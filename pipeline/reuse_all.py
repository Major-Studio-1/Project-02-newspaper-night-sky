"""Text reuse across the whole archive (1770-1810), one year at a time.

Generalizes work/reuse_1797.py to all 77,749 eligible pages:
- the same matching rules (5-word shingles, winnowing window 8, >=6 shared fingerprints,
  monotone chains, token SequenceMatcher, different newspaper series, <=120 days apart);
- each year is a window of its own pages plus the previous 120 days, and a pair belongs to
  the year of its later page, so every pair is found exactly once;
- fingerprints are CRC32 hashes in numpy arrays (fast, low memory);
- the boilerplate rule is scaled for big years: a fingerprint is ignored when it occurs on
  more than 40 pages or more than 80 times in the window (1797 used 10/20, which would drop
  stories reprinted in many papers in years with up to 17 series).

Stages are resumable: tokens are cached per year, matches are written per year.
Usage (project root, Python 3.12):
    python work/reuse_all.py tokens          # cache tokens per year (once)
    python work/reuse_all.py match [years]   # e.g. "match 1808" or "match" for all, 2 workers
"""
from pathlib import Path
import collections
import datetime
import difflib
import itertools
import json
import re
import sys
import time
import unicodedata
import zlib

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
import numpy as np
import pyarrow.parquet as pq

CACHE = ROOT/'reuse_all'
TOKEN = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")
LOOKBACK, MAX_PAGES, MAX_OCC, MIN_SEEDS = 120, 40, 80, 6
BROAD = (60, 0.6)  # stored; 'main' (80, 0.7) and 'strict' (120, 0.8) are flags


def tokenize(text):
    text = unicodedata.normalize('NFKC', text or '').replace('ſ', 's')
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
    return [m.group().lower() for m in TOKEN.finditer(text)]


def stage_tokens():
    CACHE.mkdir(exist_ok=True)
    audit = [r for r in pq.read_table(ROOT/'page_audit.parquet').to_pylist() if r['eligible']]
    loc = {(r['file'], r['file_row']): r for r in audit}
    years = sorted({r['year'] for r in audit})
    if all((CACHE/f'tokens_{y}.jsonl').exists() for y in years):
        print('tokens already cached'); return
    files = {y: (CACHE/f'tokens_{y}.jsonl').open('w', encoding='utf8') for y in years}
    n = 0
    for shard in sorted((ROOT/'data').glob('*.parquet')):
        offset = 0
        for batch in pq.ParquetFile(shard).iter_batches(batch_size=256, columns=['RevX_OCR_text', 'ca_ocr_text']):
            for j, r in enumerate(batch.to_pylist()):
                m = loc.get((shard.name, offset+j))
                if m:
                    text = r['RevX_OCR_text'] if m['selected_source'] == 'RevX' else r['ca_ocr_text']
                    row = {'key': m['key'], 'date': m['issue_date'], 'lccn': m['lccn'], 'paper': m['newspaper_title'],
                           'page': str(m['Page']), 'source': m['selected_source'], 'text': ' '.join(tokenize(text))}
                    files[m['year']].write(json.dumps(row, ensure_ascii=False)+'\n'); n += 1
            offset += batch.num_rows
        print('tokenized', shard.name, n, 'pages', flush=True)
    for f in files.values():
        f.close()


def load_year(y):
    path = CACHE/f'tokens_{y}.jsonl'
    if not path.exists():
        return []
    with path.open(encoding='utf8') as f:
        return [json.loads(line) for line in f]


def fingerprints(tokens):
    n = len(tokens) - 4
    if n < 8:
        return np.empty(0, np.uint32), np.empty(0, np.uint32)
    h = np.fromiter((zlib.crc32(' '.join(tokens[i:i+5]).encode()) for i in range(n)), dtype=np.uint32, count=n)
    w = np.lib.stride_tricks.sliding_window_view(h, 8)
    pos = np.unique(np.arange(n-7) + 7 - np.argmin(w[:, ::-1], axis=1))  # rightmost minimum per window
    return h[pos], pos.astype(np.uint32)


def match_year(y):
    out = CACHE/f'matches_{y}.json'
    if out.exists():
        return y, 'cached'
    t0 = time.time()
    start = datetime.date(y, 1, 1).toordinal()
    pages = load_year(y) + [p for p in load_year(y-1) if datetime.date.fromisoformat(p['date']).toordinal() >= start-LOOKBACK]
    pages.sort(key=lambda p: (p['date'], p['key']))
    tokens = [p['text'].split() for p in pages]
    ords = [datetime.date.fromisoformat(p['date']).toordinal() for p in pages]
    lccn = [p['lccn'] for p in pages]
    H, P, X = [], [], []
    for i, t in enumerate(tokens):
        h, pos = fingerprints(t)
        H.append(h); P.append(np.full(len(h), i, np.uint32)); X.append(pos)
    H, P, X = np.concatenate(H), np.concatenate(P), np.concatenate(X)
    order = np.argsort(H, kind='stable')
    H, P, X = H[order], P[order], X[order]
    cut = np.flatnonzero(np.diff(H)) + 1
    starts, ends = np.r_[0, cut], np.r_[cut, len(H)]
    sizes = ends - starts
    keep = (sizes >= 2) & (sizes <= MAX_OCC)
    ignored = int((sizes > MAX_OCC).sum())
    cand = collections.defaultdict(list)
    for s, e in zip(starts[keep].tolist(), ends[keep].tolist()):
        pids = P[s:e].tolist()
        if len(set(pids)) > MAX_PAGES:
            ignored += 1; continue
        occ = list(zip(pids, X[s:e].tolist()))
        for (a, xa), (b, xb) in itertools.combinations(occ, 2):
            if a == b or lccn[a] == lccn[b] or abs(ords[a]-ords[b]) > LOOKBACK:
                continue
            if a > b:
                a, b, xa, xb = b, a, xb, xa
            if ords[b] < start:  # the later page is in the previous year: that window owns the pair
                continue
            cand[a, b].append((xa, xb))
    del H, P, X
    cand = {k: sorted(set(v)) for k, v in cand.items() if len(set(v)) >= MIN_SEEDS}
    matches = []
    for (a, b), seeds in cand.items():
        chains = []
        for x, yy in seeds:
            choices = [(max(x-ch[-1][0], yy-ch[-1][1]), i) for i, ch in enumerate(chains)
                       if 0 < x-ch[-1][0] <= 100 and 0 < yy-ch[-1][1] <= 100 and abs((x-ch[-1][0])-(yy-ch[-1][1])) <= 60]
            if choices:
                chains[min(choices)[1]].append((x, yy))
            else:
                chains.append([(x, yy)])
        for ch in chains:
            if len(ch) < MIN_SEEDS:
                continue
            x0, y0 = ch[0]; x1, y1 = ch[-1][0]+5, ch[-1][1]+5
            if min(x1-x0, y1-y0) < BROAD[0]:
                continue
            aa, bb = tokens[a][x0:x1], tokens[b][y0:y1]
            sm = difflib.SequenceMatcher(None, aa, bb, autojunk=False)
            n = sum(m.size for m in sm.get_matching_blocks())
            ratio = 2*n/(len(aa)+len(bb))
            if n < BROAD[0] or ratio < BROAD[1]:
                continue
            pa, pb = pages[a], pages[b]
            matches.append({'a': pa['key'], 'b': pb['key'], 'a_date': pa['date'], 'b_date': pb['date'], 'a_lccn': pa['lccn'], 'b_lccn': pb['lccn'],
                            'a_span': [x0, x1], 'b_span': [y0, y1], 'matched_words': n, 'similarity': round(ratio, 4), 'seeds': len(ch),
                            'main': n >= 80 and ratio >= 0.7, 'strict': n >= 120 and ratio >= 0.8,
                            'a_text': ' '.join(aa[:90]), 'b_text': ' '.join(bb[:90])})
    in_year = sum(1 for o in ords if o >= start)
    meta = {'year': y, 'pages_in_year': in_year, 'pages_in_window': len(pages), 'candidate_page_pairs': len(cand), 'ignored_common_fingerprints': ignored,
            'matches_broad': len(matches), 'matches_main': sum(m['main'] for m in matches), 'seconds': round(time.time()-t0, 1)}
    out.write_text(json.dumps({'meta': meta, 'matches': matches}, ensure_ascii=False), encoding='utf8')
    return y, meta


if __name__ == '__main__':
    stage = sys.argv[1]
    if stage == 'tokens':
        stage_tokens()
    elif stage == 'match':
        years = [int(a) for a in sys.argv[2:]] or list(range(1770, 1811))
        sizes = {y: (CACHE/f'tokens_{y}.jsonl').stat().st_size for y in years}
        years.sort(key=lambda y: -sizes[y])
        # Alternate big and small years so two big windows rarely run at once (memory).
        order, lo, hi = [], 0, len(years)-1
        while lo <= hi:
            order.append(years[lo]); lo += 1
            if lo <= hi:
                order.append(years[hi]); hi -= 1
        years = order
        if len(years) == 1:
            print(match_year(years[0]), flush=True)
        else:
            from multiprocessing import Pool
            with Pool(2) as pool:
                for y, meta in pool.imap_unordered(match_year, years):
                    print(y, meta, flush=True)
