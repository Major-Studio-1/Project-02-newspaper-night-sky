"""Find issues whose RevX transcriptions are filed one page off from the scans (2026-11-10).

The RevX transcriptions of the Herald of the United States of 4 July 1807 (sn83021527) are shifted by one page:
RevX page 1 holds the text of scan page 2 (outputs/story_discovery_1807/README.md, "A data issue"). This script
checks every issue of the dataset for the same fault.

Every page has two machine transcriptions: the Library of Congress OCR ("CA") and the newer AI transcription
("RevX"). The CA text is made from the page's own scan: its file (ca_ocr_url) sits next to the page's PDF in the same
LoC folder, under the same file number. So the CA text is the reference for which scan a page is. For each issue
(newspaper, date, edition), every page's RevX text is compared with the CA text of every page of the same issue:

- share4: the share of the RevX page's distinct word 4-grams that also occur in that CA page. This is page_agree of
  work/transcription_check.py: the matcher's tokenizer, with f and s counted as one letter (old OCR reads the long s
  as f);
- share_w: the same share for distinct words of 6 or more letters, a coarser second measure for pages where the old
  OCR is too noisy for 4-grams.

A RevX page is filed at the CA page it matches clearly best: share4 of at least MIN_SHARE, and at least RATIO times
every other page of the issue. If that page is n+1 or n-1 rather than n, the page is shifted. Two safeguards:
- share_w only ever confirms a page's own number (where 4-grams are too few); it never moves a page;
- when a page's best match is a scan page whose own RevX page already matches it, the two RevX texts are compared:
  if they share at least MIN_SHARE * RATIO of their 4-grams, RevX transcribed that scan twice ("duplicate");
  otherwise the match is rejected ("conflict"; shared formulaic text such as stray-horse notices can outweigh a
  badly read own page).
Pages the measures cannot place are counted as undetermined, not as aligned.

Usage (project root, Python 3.12 with work/python_packages):
    python outputs/revx_page_shift_check/check_page_shift.py            # measure (reads the six shards once, ~11 min
                                                                        # with 4 workers), classify, impact
    python outputs/revx_page_shift_check/check_page_shift.py classify   # classification and summary only
    python outputs/revx_page_shift_check/check_page_shift.py impact     # what the misfiled pages touch in the release
    python outputs/revx_page_shift_check/check_page_shift.py scans      # confirm a sample against the pinned scan PDFs

Writes, next to this script: measures/pages.parquet and measures/pairs.parquet (the measures); page_status.csv (every
RevX page that is not plainly aligned, with its shares); shifted_issues.csv (one row per issue with a misfiled RevX
page); summary.json; impact.json (read-only counts in the current release); scan_confirmation.json (the scans stage;
downloads go to scans/, which is git-ignored).
"""
from pathlib import Path
import collections
import csv
import json
import multiprocessing as mp
import random
import sys
import time
import urllib.request
import zlib

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
WORK = PROJECT/'work'
sys.path.insert(0, str(WORK/'python_packages'))
sys.path.insert(0, str(WORK))
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from reuse_all import tokenize  # the matcher's own tokenizer

K = 4            # word n-gram length
LONG = 6         # letters in a "long word" for share_w
MIN_WORDS = 50   # a transcription with fewer words is treated as empty (as MIN_OTHER in transcription_check.py)
MIN_SHARE = 0.05  # share4 needed to place a page by 4-grams
RATIO = 3.0      # ... and it must be this many times the next best CA page of the issue
W_MIN, W_RATIO = 0.15, 2.0   # the same for share_w, used only where 4-grams cannot place the page
MEASURES = HERE/'measures'
MIX = np.uint64(0x9E3779B97F4A7C15)
EMPTY = np.empty(0, dtype=np.uint64)
REV = '0b97906ad32e269376872934820357fc333151d8'   # pinned dataset revision, as in work/scan_ledger.py
DATASET = 'RevolutionCrossroads/loc_chronicling_america_1770-1810'
KNOWN = 'sn83021527|1807-07-04|1'


# ---------------------------------------------------------------------------------------------- measure

def sketch(text):
    """Word count, distinct 4-gram hashes and distinct long-word hashes of one transcription."""
    toks = [t.replace('f', 's') for t in tokenize(text)]
    if not toks:
        return 0, EMPTY, EMPTY
    h = np.fromiter((zlib.crc32(t.encode()) for t in toks), dtype=np.uint64, count=len(toks))
    grams = EMPTY
    if len(toks) >= K:
        g = h[:1-K].copy()
        for k in range(1, K):
            g = g * MIX + h[k:len(h)-K+1+k]
        grams = np.unique(g)
    longs = np.fromiter((len(t) >= LONG for t in toks), dtype=bool, count=len(toks))
    return len(toks), grams, np.unique(h[longs])


def compare(issue, pages):
    """All RevX page x CA page pairs of one issue: shared 4-grams and shared long words."""
    rows = []
    for i, (ri, _) in sorted(pages.items()):
        if ri[0] < MIN_WORDS:
            continue
        for j, (_, cj) in sorted(pages.items()):
            if cj[0] < MIN_WORDS:
                continue
            rows.append((issue, i, j, int(np.intersect1d(ri[1], cj[1], assume_unique=True).size),
                         int(np.intersect1d(ri[2], cj[2], assume_unique=True).size)))
    return rows


def work_shard(args):
    shard, expected, cross = args
    pf = pq.ParquetFile(WORK/'data'/shard)
    buf, pages, pairs, t0 = collections.defaultdict(dict), [], [], time.time()
    for g in range(pf.num_row_groups):
        t = pf.read_row_group(g, columns=['lccn', 'issue_date', 'edition_order', 'Page', 'RevX_OCR_text', 'ca_ocr_text'])
        lccn, ed, page = t['lccn'].to_pylist(), t['edition_order'].to_pylist(), t['Page'].to_pylist()
        date = pc.strftime(t['issue_date'], format='%Y-%m-%d').to_pylist()
        revx, ca = t['RevX_OCR_text'], t['ca_ocr_text']
        for r in range(t.num_rows):
            issue = f'{lccn[r]}|{date[r]}|{ed[r]}'
            sr, sc = sketch(revx[r].as_py()), sketch(ca[r].as_py())
            buf[issue][page[r]] = (sr, sc)
            pages.append((issue, page[r], sr[0], sc[0], len(sr[1]), len(sc[1]), len(sr[2]), len(sc[2])))
            if issue not in cross and len(buf[issue]) == expected[issue]:
                pairs.extend(compare(issue, buf.pop(issue)))
        del t, revx, ca
    print(f'  {shard}: {len(pages):,} pages, {len(pairs):,} pairs, {time.time()-t0:.0f} s', flush=True)
    return pages, pairs, dict(buf)   # what is left in buf: the issues that continue in another shard


def measure(workers=4):
    audit = pq.read_table(WORK/'page_audit.parquet', columns=['file', 'lccn', 'issue_date', 'edition_order']).to_pylist()
    expected, files = collections.defaultdict(collections.Counter), collections.defaultdict(set)
    for r in audit:
        issue = f"{r['lccn']}|{r['issue_date']}|{r['edition_order']}"
        expected[r['file']][issue] += 1
        files[issue].add(r['file'])
    cross = {i for i, f in files.items() if len(f) > 1}
    jobs = [(s, dict(expected[s]), cross) for s in sorted(expected)]
    pages, pairs, rest = [], [], collections.defaultdict(dict)
    with mp.Pool(workers) as pool:
        for p, q, left in pool.imap_unordered(work_shard, jobs):
            pages += p
            pairs += q
            for issue, pg in left.items():
                rest[issue].update(pg)
    for issue, pg in rest.items():   # the few issues split between two shards
        pairs += compare(issue, pg)
    assert len(pages) == len(audit), (len(pages), len(audit))
    MEASURES.mkdir(exist_ok=True)
    names = ['issue', 'page', 'revx_words', 'ca_words', 'revx_grams', 'ca_grams', 'revx_long', 'ca_long']
    pq.write_table(pa.table({n: [p[k] for p in sorted(pages)] for k, n in enumerate(names)}), MEASURES/'pages.parquet')
    names = ['issue', 'revx_page', 'ca_page', 'shared_grams', 'shared_long']
    pq.write_table(pa.table({n: [p[k] for p in sorted(pairs)] for k, n in enumerate(names)}), MEASURES/'pairs.parquet')
    print(f'measured {len(pages):,} pages, {len(pairs):,} page pairs in {len(files):,} issues', flush=True)


# ---------------------------------------------------------------------------------------------- classify

def place(scores, floor, ratio):
    """The CA page a RevX page matches clearly best, or None. scores: {ca_page: share}."""
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    best, a1 = ranked[0]
    a2 = ranked[1][1] if len(ranked) > 1 else 0.0
    return (best if a1 >= floor and a1 >= ratio * a2 else None), a1, a2


def load():
    pages = pq.read_table(MEASURES/'pages.parquet').to_pylist()
    pairs = pq.read_table(MEASURES/'pairs.parquet').to_pylist()
    audit = pq.read_table(WORK/'page_audit.parquet', columns=['lccn', 'issue_date', 'edition_order', 'newspaper_title',
                                                              'place_of_publication']).to_pylist()
    titles = {r['lccn']: (r['newspaper_title'], r['place_of_publication']) for r in audit}
    return pages, pairs, titles


def decide(i, s4, sw):
    """Status, scan page and evidence of RevX page i, from its shares against the issue's CA pages."""
    if s4:
        ranked = sorted(s4.items(), key=lambda kv: (-kv[1], kv[0] != i))
        (best, a1), a2, own = ranked[0], (ranked[1][1] if len(ranked) > 1 else 0.0), s4.get(i, 0.0)
        if a1 >= MIN_SHARE:
            if best == i:
                return ('aligned' if a1 >= RATIO * a2 else 'own_page_shared'), i, '4-grams'
            if a1 >= RATIO * a2:
                return 'moved', best, '4-grams'
            if own >= MIN_SHARE and a1 < RATIO * own:
                return 'own_page_shared', i, '4-grams'   # its own page matches nearly as well as another one
            return 'undetermined', None, None            # two other pages compete
    # Too few shared 4-grams (noisy old OCR): long words may confirm the page's own number, never move it.
    if sw and i in sw and place(sw, W_MIN, W_RATIO)[0] == i:
        return 'aligned', i, 'long words'
    return 'undetermined', None, None


def mechanism(moved, pgs, empty):
    """'one/two scan page(s) without RevX, the later pages filed early' when the moved pages fit that pattern."""
    offs = {s['offset'] for s in moved}
    run = sorted(s['revx_page'] for s in moved)
    if len(offs) == 1 and min(offs) > 0 and run == list(range(run[0], run[-1] + 1)) \
            and all(j in empty for j in pgs if j > run[-1]) and run[-1] < max(pgs):
        d = min(offs)
        return f"{'one' if d == 1 else d} scan page{'s' if d > 1 else ''} without RevX; later pages filed {d} early"
    return 'irregular'


def classify():
    pages, pairs, titles = load()
    info = {(p['issue'], p['page']): p for p in pages}
    by_page = collections.defaultdict(dict)
    for r in pairs:
        by_page[(r['issue'], r['revx_page'])][r['ca_page']] = r
    issues = collections.defaultdict(list)
    for p in pages:
        issues[p['issue']].append(p['page'])
    status = {}   # (issue, revx page) -> dict
    for (issue, i), row in by_page.items():
        p = info[(issue, i)]
        s4 = {j: r['shared_grams'] / p['revx_grams'] for j, r in row.items()} if p['revx_grams'] else {}
        sw = {j: r['shared_long'] / p['revx_long'] for j, r in row.items()} if p['revx_long'] else {}
        st, at, basis = decide(i, s4, sw)
        ranked = sorted(s4.values(), reverse=True) + [0.0, 0.0]
        status[(issue, i)] = {'issue': issue, 'revx_page': i, 'status': st, 'filed_at': at, 'basis': basis,
                              'offset': None if at is None else at - i,
                              'share4_own': round(s4.get(i, 0.0), 4), 'share4_at': round(s4[at], 4) if at in s4 else None,
                              'share4_best': round(ranked[0], 4), 'share4_next': round(ranked[1], 4),
                              'share_w_own': round(sw.get(i, 0.0), 4), 'share_w_at': round(sw[at], 4) if at in sw else None,
                              'share4_all': {j: round(v, 4) for j, v in sorted(s4.items())}}
    # A moved page whose scan page is already the clear match of that page's own RevX text is not taken as moved:
    # either RevX transcribed that scan twice (a duplicate), or shared formulaic text (stray-horse notices, say)
    # outweighs a badly read own page. The RevX texts of the two pages tell which.
    suspects = [s for s in status.values() if s['status'] == 'moved'
                and status.get((s['issue'], s['filed_at']), {}).get('status') in ('aligned', 'own_page_shared')]
    if suspects:
        texts = texts_of({f"{s['issue']}|{p}" for s in suspects for p in (s['revx_page'], s['filed_at'])})
        for s in suspects:
            a, b = (sketch(texts[f"{s['issue']}|{p}"][0])[1] for p in (s['revx_page'], s['filed_at']))
            s['revx_same_as_own_revx'] = round(np.intersect1d(a, b, assume_unique=True).size / len(a), 4)
            s['status'] = 'duplicate' if s['revx_same_as_own_revx'] >= MIN_SHARE * RATIO else 'conflict'

    def kind(s):
        if s['status'] == 'moved':
            return 'shifted' if abs(s['offset']) == 1 else 'other_page'
        return s['status']

    page_counts = collections.Counter(kind(s) for s in status.values())
    untested = collections.Counter()
    for p in pages:
        if (p['issue'], p['page']) not in status:
            untested['no RevX text' if p['revx_words'] < MIN_WORDS else 'no other page with CA text'] += 1
    out_issues, issue_counts = [], collections.Counter()
    for issue, pgs in sorted(issues.items()):
        st = [status[(issue, i)] for i in sorted(pgs) if (issue, i) in status]
        kinds = collections.Counter(kind(s) for s in st)
        if not st:
            issue_counts['not testable'] += 1
            continue
        label = next((k for k in ('shifted', 'other_page', 'duplicate') if kinds[k]), None)
        if label is None:
            settled = kinds['aligned'] + kinds['own_page_shared']
            label = 'undetermined' if not settled else 'aligned' if settled == len(st) else 'aligned_where_determined'
        issue_counts[label] += 1
        if label in ('shifted', 'other_page', 'duplicate'):
            lccn, date, ed = issue.split('|')
            empty = [j for j in sorted(pgs) if info[(issue, j)]['revx_words'] < MIN_WORDS]
            moved = [s for s in st if s['status'] in ('moved', 'duplicate')]
            filed = {s['filed_at'] for s in st if s['status'] in ('aligned', 'own_page_shared', 'moved', 'duplicate')}
            out_issues.append({
                'issue': issue, 'lccn': lccn, 'newspaper': titles[lccn][0], 'place': titles[lccn][1], 'date': date,
                'edition': int(ed), 'year': int(date[:4]), 'pages': len(pgs), 'kind': label,
                'mechanism': mechanism(moved, pgs, empty) if label != 'duplicate' else 'RevX page repeats another page',
                'offsets': ' '.join(sorted({f"{s['offset']:+d}" for s in moved})),
                'pages_moved': len(moved), 'pages_aligned': kinds['aligned'] + kinds['own_page_shared'],
                'pages_undetermined': kinds['undetermined'] + kinds['conflict'],
                'revx_empty_pages': ' '.join(map(str, empty)),
                # scan pages whose text no RevX page carries (once the moved pages are refiled)
                'scan_pages_without_revx': ' '.join(str(j) for j in sorted(pgs) if j not in filed and info[(issue, j)]['ca_words'] >= MIN_WORDS),
                'min_share4_at': min(s['share4_at'] for s in moved),
                'max_share4_own': max(s['share4_own'] for s in moved),
                'pattern': '; '.join(f"RevX {s['revx_page']} = scan {s['filed_at']} ({s['share4_at']:.3f} vs {s['share4_own']:.3f} own)"
                                     for s in moved)})
    with (HERE/'shifted_issues.csv').open('w', newline='', encoding='utf8') as f:
        w = csv.DictWriter(f, fieldnames=list(out_issues[0]))
        w.writeheader()
        w.writerows(out_issues)
    with (HERE/'page_status.csv').open('w', newline='', encoding='utf8') as f:
        cols = ['issue', 'revx_page', 'status', 'filed_at', 'offset', 'basis', 'share4_own', 'share4_at', 'share4_best',
                'share4_next', 'share_w_own', 'share_w_at', 'revx_same_as_own_revx', 'share4_all']
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in sorted(status.values(), key=lambda s: (s['issue'], s['revx_page'])):
            if kind(s) != 'aligned':
                w.writerow({**{c: s.get(c) for c in cols}, 'status': kind(s), 'share4_all': json.dumps(s['share4_all'])})
    aligned = [s for s in status.values() if kind(s) == 'aligned' and s['basis'] == '4-grams']
    shifted = [r for r in out_issues if r['kind'] == 'shifted']
    # Scan pages whose text is in no RevX page: their own RevX page holds another page, and no RevX page holds them.
    claimed = {(s['issue'], s['filed_at']) for s in status.values() if s['status'] in ('aligned', 'own_page_shared', 'moved', 'duplicate')}
    orphans = [s for s in status.values() if s['status'] in ('moved', 'duplicate') and (s['issue'], s['revx_page']) not in claimed]
    hist = lambda vals, edges: [sum(1 for v in vals if lo <= v < hi) for lo, hi in zip(edges, edges[1:])]
    edges = [0, .01, .02, .05, .1, .2, .3, .4, .5, .6, .8, 1.01]
    undetermined_by_year = collections.Counter(int(s['issue'].split('|')[1][:4]) for s in status.values() if kind(s) == 'undetermined')
    tested_by_year = collections.Counter(int(s['issue'].split('|')[1][:4]) for s in status.values())
    summary = {
        'run': 'revx-page-shift-check-v1', 'date': '2026-11-10',
        'thresholds': {'k': K, 'long_word_letters': LONG, 'min_words': MIN_WORDS, 'min_share4': MIN_SHARE, 'ratio': RATIO,
                       'long_words_min_share': W_MIN, 'long_words_ratio': W_RATIO, 'duplicate_min_share': MIN_SHARE * RATIO},
        'pages': len(pages), 'revx_pages_tested': len(status), 'pages_not_tested': dict(untested),
        'revx_pages_by_status': dict(page_counts),
        'revx_pages_by_status_and_evidence': dict(collections.Counter(f"{kind(s)} by {s['basis']}" for s in status.values() if s['basis'])),
        'issues': len(issues), 'issues_by_status': dict(issue_counts),
        'shifted_issues': len(shifted), 'shifted_pages': sum(r['pages_moved'] for r in shifted),
        'shifted_issues_by_mechanism': dict(collections.Counter(r['mechanism'] for r in shifted)),
        'shifted_issues_by_paper': dict(collections.Counter(f"{r['lccn']} {r['newspaper']}" for r in shifted).most_common()),
        'shifted_issues_by_year': dict(sorted(collections.Counter(r['year'] for r in shifted).items())),
        'other_misfiled_issues': {r['issue']: f"{r['kind']}: {r['pattern']}" for r in out_issues if r['kind'] != 'shifted'},
        'scan_pages_with_no_revx_text': {'pages': len(orphans), 'by_status_of_their_own_revx_page': dict(collections.Counter(kind(s) for s in orphans))},
        'known_case': next((r for r in out_issues if r['issue'] == KNOWN), None),
        'undetermined_share_by_year': {y: round(undetermined_by_year[y] / tested_by_year[y], 3) for y in sorted(tested_by_year)},
        'share4_edges': edges,
        'histogram_share4_aligned_pages': hist([s['share4_at'] for s in aligned], edges),
        'histogram_share4_next_best_aligned_pages': hist([s['share4_next'] for s in aligned], edges),
        'histogram_share4_own_moved_pages': hist([s['share4_own'] for s in status.values() if s['status'] == 'moved'], edges),
        'histogram_share4_at_moved_pages': hist([s['share4_at'] for s in status.values() if s['status'] == 'moved'], edges),
        'histogram_share4_best_undetermined_pages': hist([s['share4_best'] for s in status.values() if kind(s) == 'undetermined'], edges),
    }
    (HERE/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    print(json.dumps({k: summary[k] for k in ['revx_pages_tested', 'pages_not_tested', 'revx_pages_by_status', 'revx_pages_by_status_and_evidence',
                                              'issues_by_status', 'shifted_issues', 'shifted_pages', 'shifted_issues_by_mechanism',
                                              'other_misfiled_issues']}, indent=1))
    return status, out_issues


# ---------------------------------------------------------------------------------------------- scans

def texts_of(keys):
    """RevX and CA text of the given page keys (lccn|date|ed|page), read by shard row."""
    audit = pq.read_table(WORK/'page_audit.parquet', columns=['key', 'file', 'file_row']).to_pylist()
    where = {r['key']: (r['file'], r['file_row']) for r in audit if r['key'] in keys}
    out, by_file = {}, collections.defaultdict(dict)
    for k, (f, row) in where.items():
        by_file[f][row] = k
    for f, rows in by_file.items():
        pf, offset = pq.ParquetFile(WORK/'data'/f), 0
        for g in range(pf.num_row_groups):
            n = pf.metadata.row_group(g).num_rows
            hit = [rw for rw in rows if offset <= rw < offset + n]
            if hit:
                t = pf.read_row_group(g, columns=['RevX_OCR_text', 'ca_ocr_text'])
                for rw in hit:
                    out[rows[rw]] = (t['RevX_OCR_text'][rw - offset].as_py() or '', t['ca_ocr_text'][rw - offset].as_py() or '')
            offset += n
    return out


def pinned_pdf(key):
    """The pinned scan PDF of a page: work/scans/ if a review already fetched it, else downloaded to scans/ here."""
    lccn, date, ed, page = key.split('|')
    stem = f'{lccn}_{date}_{ed}_{page}'
    for p in (WORK/'scans'/f'{stem}.pdf', HERE/'scans'/f'{stem}.pdf'):
        if p.exists():
            return p
    url = f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/{lccn}/{date}_{ed}_{page}.pdf?download=true'
    p = HERE/'scans'/f'{stem}.pdf'
    p.parent.mkdir(exist_ok=True)
    with urllib.request.urlopen(url, timeout=180) as r:
        data = r.read()
    p.write_bytes(data)
    return p


def text_layer(pdf):
    from pypdf import PdfReader
    return '\n'.join(pg.extract_text() or '' for pg in PdfReader(pdf).pages)


def scans(n_random=8, n_weakest=2, n_control=3, seed=20261110):
    """Confirm a sample against the pinned scans.

    The sample: the known issue; the n_weakest one-page shifts with the least evidence; n_random other one-page
    shifts; one issue shifted by two pages; one issue with a repeated RevX page (8 pages or fewer); n_control issues
    with every page aligned. Each scan PDF carries a text layer over the page image. For every page of a sampled
    issue, the RevX text is placed among the issue's scan text layers by the same rule as above, and the CA text is
    compared with its own scan's text layer (does the pinned PDF of page n carry the CA text of page n?)."""
    pages, _, titles = load()
    rows = list(csv.DictReader((HERE/'shifted_issues.csv').open(encoding='utf8')))
    by_issue = collections.defaultdict(list)
    for p in pages:
        by_issue[p['issue']].append(p)
    rng = random.Random(seed)
    one = sorted((r for r in rows if r['kind'] == 'shifted' and r['issue'] != KNOWN), key=lambda r: float(r['min_share4_at']))
    weakest = [r['issue'] for r in one[:n_weakest]]
    sample = {KNOWN: 'known'} | {i: 'shifted, weakest evidence' for i in weakest}
    sample |= {i: 'shifted, random' for i in rng.sample([r['issue'] for r in one[n_weakest:]], n_random)}
    sample |= {rng.choice([r['issue'] for r in rows if r['kind'] == 'other_page']): 'shifted by two pages'}
    sample |= {rng.choice([r['issue'] for r in rows if r['kind'] == 'duplicate' and int(r['pages']) <= 8]): 'repeated RevX page'}
    aligned = [i for i in sorted(by_issue) if i not in {r['issue'] for r in rows}
               and sum(p['revx_words'] >= MIN_WORDS for p in by_issue[i]) >= 2]
    sample |= {i: 'control (aligned)' for i in rng.sample(aligned, n_control)}
    keys = {f"{i}|{p['page']}" for i in sample for p in by_issue[i]}
    texts = texts_of(keys)
    # Where the CA comparison filed each RevX page (aligned pages are not listed in page_status.csv)
    by_ca = {(r['issue'], int(r['revx_page'])): (int(r['filed_at']) if r['filed_at'] and r['status'] != 'conflict' else None)
             for r in csv.DictReader((HERE/'page_status.csv').open(encoding='utf8'))}
    report, tally = [], collections.Counter()
    for issue, role in sample.items():
        pg = sorted(p['page'] for p in by_issue[issue])
        sk = {j: (sketch(texts[f'{issue}|{j}'][0]), sketch(texts[f'{issue}|{j}'][1]), sketch(text_layer(pinned_pdf(f'{issue}|{j}'))))
              for j in pg}
        res = {'issue': issue, 'newspaper': titles[issue.split('|')[0]][0], 'role': role, 'pages': []}
        for i in pg:
            r, c, s = sk[i]
            entry = {'page': i, 'revx_words': r[0], 'ca_words': c[0], 'scan_text_words': s[0],
                     # does this page's scan carry this page's CA text? (share of CA 4-grams found in the scan's text layer)
                     'ca_in_own_scan': round(np.intersect1d(c[1], s[1], assume_unique=True).size / len(c[1]), 3) if len(c[1]) else None}
            if r[0] >= MIN_WORDS and len(r[1]):
                shares = {j: np.intersect1d(r[1], sk[j][2][1], assume_unique=True).size / len(r[1]) for j in pg if sk[j][2][0] >= MIN_WORDS}
                if shares:
                    at = place(shares, MIN_SHARE, RATIO)[0]
                    ca_at = by_ca.get((issue, i), i)
                    entry.update({'revx_in_scan': {j: round(v, 3) for j, v in shares.items()}, 'revx_matches_scan': at,
                                  'revx_filed_at_by_ca': ca_at})
                    tally['pages compared'] += 1
                    tally['scan agrees with the CA comparison' if at == ca_at else
                          'scan cannot place the page' if at is None else 'scan disagrees'] += 1
                    if ca_at is not None and ca_at != i:
                        tally['moved pages confirmed by the scan' if at == ca_at else 'moved pages not confirmed by the scan'] += 1
            res['pages'].append(entry)
        report.append(res)
        print(issue, role, [(e['page'], e.get('revx_matches_scan'), e['ca_in_own_scan']) for e in res['pages']], flush=True)
    ca_own = [e['ca_in_own_scan'] for r in report for e in r['pages'] if e['ca_in_own_scan'] is not None and e['ca_words'] >= MIN_WORDS]
    summary = {'seed': seed, 'dataset_revision': REV, 'issues_sampled': len(report), 'tally': dict(tally),
               'ca_in_own_scan_min': min(ca_own), 'ca_in_own_scan_median': sorted(ca_own)[len(ca_own) // 2]}
    print(json.dumps(summary, indent=1))
    (HERE/'scan_confirmation.json').write_text(json.dumps({**summary, 'issues': report}, indent=1), encoding='utf8')


# ---------------------------------------------------------------------------------------------- impact

def recheck(release, wrong, moved):
    """The transcription check of each printing on a misfiled page, redone against the CA text of the scan page its
    RevX text belongs to (work/transcription_check.py's own measures and status rule)."""
    from transcription_check import fold, grams, status as check_status
    apps = [a for a in pq.read_table(release/'derived/reuse_family_appearances.parquet',
                                     columns=['page_id', 'span_start', 'span_end']).to_pylist() if a['page_id'] in wrong]
    key = lambda pid: '|'.join(pid.split(':')[1:])
    texts = texts_of({key(p) for p in wrong} | {key(moved[p][0]) for p in wrong})
    result = collections.Counter()
    for a in apps:
        sel = fold(tokenize(texts[key(a['page_id'])][0]))           # the RevX text the matcher read
        other = tokenize(texts[key(moved[a['page_id']][0])][1])     # CA text of the scan page it belongs to
        g_other, g_sel, g_span = grams(fold(other)), grams(sel), grams(sel[a['span_start']:a['span_end']])
        r = {'other_words': len(other), 'page_agree': len(g_sel & g_other) / len(g_sel) if g_sel else 0.0,
             'contain': len(g_span & g_other) / len(g_span) if g_span else 0.0}
        result[check_status(r)] += 1
    return dict(result)


def impact():
    """What the moved pages touch in the current data release (read only)."""
    current = json.loads((PROJECT/'outputs/data_foundation/CURRENT.json').read_text(encoding='utf8'))
    release = PROJECT/'outputs/data_foundation'/current['path']
    moved = {}   # page id of a RevX page filed elsewhere -> (page id of the scan it holds, status)
    for r in csv.DictReader((HERE/'page_status.csv').open(encoding='utf8')):
        if r['status'] in ('shifted', 'other_page', 'duplicate'):
            lccn, date, ed = r['issue'].split('|')
            moved[f"page:{lccn}:{date}:{ed}:{r['revx_page']}"] = (f"page:{lccn}:{date}:{ed}:{r['filed_at']}", r['status'])
    audit = pq.read_table(WORK/'page_audit.parquet', columns=['key', 'selected_source', 'eligible']).to_pylist()
    source = {'page:' + r['key'].replace('|', ':'): r['selected_source'] for r in audit}
    eligible = {'page:' + r['key'].replace('|', ':'): r['eligible'] for r in audit}
    wrong = {p for p in moved if source[p] == 'RevX' and eligible[p]}   # pages the automatic layer read from RevX
    out = {'release': current['version'],
           'revx_pages_filed_elsewhere': dict(collections.Counter(s for _, s in moved.values())),
           'of_which_read_from_revx_by_the_matcher': dict(collections.Counter(moved[p][1] for p in wrong))}
    apps = pq.read_table(release/'derived/reuse_family_appearances.parquet',
                         columns=['family_id', 'seq', 'page_id', 'transcription', 'publication_date']).to_pylist()
    hit = [a for a in apps if a['page_id'] in wrong]
    assert all(a['transcription'] == 'RevX' for a in hit)
    # Refiled, a printing can land on a page where its story already has a printing: a page read twice (as RevX one
    # page early and as the CA text of the page whose RevX is empty, usually the issue's last), or a repeated page.
    # Those would merge.
    refiled = collections.Counter((a['family_id'], moved[a['page_id']][0] if a['page_id'] in wrong else a['page_id']) for a in apps)
    out['appearances'] = {
        'printings_on_a_wrong_page': dict(collections.Counter(moved[a['page_id']][1] for a in hit)),
        'stories': len({a['family_id'] for a in hit}),
        'printings_sharing_a_page_with_their_story_once_refiled': dict(collections.Counter(
            moved[a['page_id']][1] for a in hit if refiled[(a['family_id'], moved[a['page_id']][0])] > 1)),
        'printings_fewer_after_merging': sum(c - 1 for c in refiled.values() if c > 1),
        'by_year': dict(sorted(collections.Counter(a['publication_date'][:4] for a in hit).items()))}
    checks = pq.read_table(release/'derived/transcription_checks.parquet', columns=['page_id', 'status']).to_pylist()
    out['transcription_checks'] = {'rows': sum(1 for c in checks if c['page_id'] in wrong),
                                   'status_now': dict(collections.Counter(c['status'] for c in checks if c['page_id'] in wrong)),
                                   'status_against_the_true_page': recheck(release, wrong, moved)}
    matches = pq.read_table(release/'derived/reuse_matches.parquet', columns=['a_page_id', 'b_page_id']).to_pylist()
    out['reuse_matches_with_a_wrong_page'] = sum(1 for m in matches if m['a_page_id'] in wrong or m['b_page_id'] in wrong)
    census = pq.read_table(release/'derived/page_topic_census.parquet', columns=['page_id', 'source']).to_pylist()
    out['page_topic_census_rows'] = sum(1 for c in census if c['page_id'] in wrong)
    audit_rows = pq.read_table(release/'derived/matched_audit.parquet', columns=['family_id', 'scan_check_page_id']).to_pylist()
    out['matched_audit_rows_on_a_moved_page'] = [r for r in audit_rows if r['scan_check_page_id'] in moved]
    reviewed = []
    for rel in sorted({release.name} | {p.name for p in (PROJECT/'outputs/data_foundation').glob('v*') if p.is_dir()}):
        f = PROJECT/'outputs/data_foundation'/rel/'tables/observations.jsonl'
        if f.exists():
            for line in f.open(encoding='utf8'):
                o = json.loads(line)
                pid = o['page_version_id'].split('@')[0]
                if pid in moved:
                    reviewed.append({'release': rel, 'id': o['id'], 'page_id': pid, 'field': o['transcription_field'],
                                     'scan_holds_revx_of': moved[pid][0]})
    out['reviewed_observations_on_a_moved_page'] = reviewed
    (HERE/'impact.json').write_text(json.dumps(out, indent=1), encoding='utf8')
    print(json.dumps({k: v for k, v in out.items() if k != 'reviewed_observations_on_a_moved_page'}, indent=1))
    print('reviewed observations on a moved page:', len(reviewed), sorted({(r['release'], r['page_id'], r['field']) for r in reviewed})[:20])


if __name__ == '__main__':
    stage = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if stage in ('all', 'measure'):
        t0 = time.time()
        measure()
        print(f'{time.time()-t0:.0f} s')
    if stage in ('all', 'classify'):
        classify()
    if stage in ('all', 'impact'):
        impact()
    if stage == 'scans':
        scans()
