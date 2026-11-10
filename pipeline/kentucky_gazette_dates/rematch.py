"""Match the re-dated Kentucky Gazette pages in the windows of their printed dates (2026-11-10).

The all-years matcher (work/reuse_all.py, run:reuse-all-v1) compares each year's pages with each other and with the
pages of the previous 120 days; a pair belongs to the year of its later page. It read the pages of the 106 Kentucky
Gazette issues (sn84038147) re-dated in issues.csv under their filed dates: 1806 is really 1804, 1807 is 1805 and 1808
is 1806. So their pages were matched against the wrong years' pages, and never against their own years'.

This script applies the matcher's own rules (reuse_all.fingerprints, LOOKBACK, MAX_PAGES, MAX_OCC, MIN_SEEDS, the chain
rule, the broad, main and strict profiles) to a year window, with every page of the window counted for the common-
fingerprint rule, but it evaluates only page pairs that include a page of these issues:
1. filed dates (the token cache as it is), windows 1806-1809: the pairs found must equal, field by field, the stored
   matches (work/reuse_all/matches_*.json) that include one of these pages. This shows the code is the matcher's.
2. printed dates (these issues' pages moved to their printed dates), windows 1804-1809.
Matches between other papers are not re-evaluated. Re-running a window in full could change a few of them through
the common-fingerprint counts, which this correction leaves as released.

Writes matches_filed.json (step 1), matches_printed.json (step 2) and rematch_summary.json next to this script.
Usage (project root, Python 3.12; about ten minutes):  python outputs/kentucky_gazette_dates/rematch.py
"""
from pathlib import Path
import collections
import csv
import datetime
import difflib
import itertools
import json
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'work/python_packages'))
sys.path.insert(0, str(ROOT/'work'))
import numpy as np
import reuse_all as R   # the matcher: its tokens cache, fingerprints and constants

LCCN = 'sn84038147'
ordinal = lambda d: datetime.date.fromisoformat(d).toordinal()


def corrections():
    rows = list(csv.DictReader((HERE/'issues.csv').open(encoding='utf8')))
    return {r['filed_date']: r['printed_date'] for r in rows if r['printed_date'] != r['filed_date']}


def year_pages(fix):
    """The token pages of a year as the matcher's window takes them: by filed date, or with these issues moved."""
    moved = collections.defaultdict(list)
    if fix:
        for y in sorted({int(d[:4]) for d in fix}):
            for p in R.load_year(y):
                if p['lccn'] == LCCN and p['date'] in fix:
                    moved[int(fix[p['date']][:4])].append(dict(p, date=fix[p['date']]))

    def pages(y):
        own = [p for p in R.load_year(y) if not (fix and p['lccn'] == LCCN and p['date'] in fix)]
        return own + moved.get(y, [])
    return pages


def match_window(y, pages_of, focus):
    """reuse_all.match_year for the window of year y, keeping only pairs with a page in focus (page keys)."""
    t0 = time.time()
    start = datetime.date(y, 1, 1).toordinal()
    pages = pages_of(y) + [p for p in pages_of(y-1) if ordinal(p['date']) >= start - R.LOOKBACK]
    pages.sort(key=lambda p: (p['date'], p['key']))
    tokens = [p['text'].split() for p in pages]
    ords = [ordinal(p['date']) for p in pages]
    lccn = [p['lccn'] for p in pages]
    in_focus = np.array([p['key'] in focus for p in pages])
    H, P, X = [], [], []
    for i, t in enumerate(tokens):
        h, pos = R.fingerprints(t)
        H.append(h); P.append(np.full(len(h), i, np.uint32)); X.append(pos)
    H, P, X = np.concatenate(H), np.concatenate(P), np.concatenate(X)
    order = np.argsort(H, kind='stable')
    H, P, X = H[order], P[order], X[order]
    cut = np.flatnonzero(np.diff(H)) + 1
    starts, ends = np.r_[0, cut], np.r_[cut, len(H)]
    sizes = ends - starts
    keep = (sizes >= 2) & (sizes <= R.MAX_OCC)
    keep &= np.add.reduceat(in_focus[P].astype(np.int64), starts) > 0   # only fingerprints on a focus page can seed a focus pair
    cand = collections.defaultdict(list)
    for s, e in zip(starts[keep].tolist(), ends[keep].tolist()):
        pids = P[s:e].tolist()
        if len(set(pids)) > R.MAX_PAGES:
            continue
        occ = list(zip(pids, X[s:e].tolist()))
        for (a, xa), (b, xb) in itertools.combinations(occ, 2):
            if a == b or lccn[a] == lccn[b] or abs(ords[a]-ords[b]) > R.LOOKBACK:
                continue
            if not (in_focus[a] or in_focus[b]):
                continue
            if a > b:
                a, b, xa, xb = b, a, xb, xa
            if ords[b] < start:  # the later page is in the previous year: that window owns the pair
                continue
            cand[a, b].append((xa, xb))
    del H, P, X
    cand = {k: sorted(set(v)) for k, v in cand.items() if len(set(v)) >= R.MIN_SEEDS}
    matches = []
    for (a, b), seeds in cand.items():   # from here on, reuse_all.match_year unchanged
        chains = []
        for x, yy in seeds:
            choices = [(max(x-ch[-1][0], yy-ch[-1][1]), i) for i, ch in enumerate(chains)
                       if 0 < x-ch[-1][0] <= 100 and 0 < yy-ch[-1][1] <= 100 and abs((x-ch[-1][0])-(yy-ch[-1][1])) <= 60]
            if choices:
                chains[min(choices)[1]].append((x, yy))
            else:
                chains.append([(x, yy)])
        for ch in chains:
            if len(ch) < R.MIN_SEEDS:
                continue
            x0, y0 = ch[0]; x1, y1 = ch[-1][0]+5, ch[-1][1]+5
            if min(x1-x0, y1-y0) < R.BROAD[0]:
                continue
            aa, bb = tokens[a][x0:x1], tokens[b][y0:y1]
            sm = difflib.SequenceMatcher(None, aa, bb, autojunk=False)
            n = sum(m.size for m in sm.get_matching_blocks())
            ratio = 2*n/(len(aa)+len(bb))
            if n < R.BROAD[0] or ratio < R.BROAD[1]:
                continue
            pa, pb = pages[a], pages[b]
            matches.append({'a': pa['key'], 'b': pb['key'], 'a_date': pa['date'], 'b_date': pb['date'], 'a_lccn': pa['lccn'], 'b_lccn': pb['lccn'],
                            'a_span': [x0, x1], 'b_span': [y0, y1], 'matched_words': n, 'similarity': round(ratio, 4), 'seeds': len(ch),
                            'main': n >= 80 and ratio >= 0.7, 'strict': n >= 120 and ratio >= 0.8,
                            'a_text': ' '.join(aa[:90]), 'b_text': ' '.join(bb[:90])})
    meta = {'year': y, 'pages_in_window': len(pages), 'focus_pages_in_window': int(in_focus.sum()),
            'focus_pages_in_year': int(sum(1 for i, o in enumerate(ords) if o >= start and in_focus[i])), 'candidate_page_pairs': len(cand),
            'matches_broad': len(matches), 'matches_main': sum(m['main'] for m in matches), 'matches_strict': sum(m['strict'] for m in matches),
            'seconds': round(time.time()-t0, 1)}
    print(json.dumps(meta), flush=True)
    return meta, matches


def canon(ms):
    return sorted(json.dumps(m, sort_keys=True) for m in ms)


def main():
    fix = corrections()
    focus = {p['key'] for y in sorted({int(d[:4]) for d in fix}) for p in R.load_year(y) if p['lccn'] == LCCN and p['date'] in fix}
    summary = {'focus_pages': len(focus), 'issues': len(fix), 'rules': {'lookback_days': R.LOOKBACK, 'max_pages': R.MAX_PAGES, 'max_occurrences': R.MAX_OCC,
               'min_seeds': R.MIN_SEEDS, 'broad': R.BROAD, 'main': [80, 0.7], 'strict': [120, 0.8]}}
    # 1. Filed dates: reproduce the stored matches of these pages.
    filed, metas = {}, []
    for y in (1806, 1807, 1808, 1809):
        meta, ms = match_window(y, year_pages(None), focus)
        stored = [m for m in json.loads((R.CACHE/f'matches_{y}.json').read_text(encoding='utf8'))['matches'] if m['a'] in focus or m['b'] in focus]
        meta['stored'] = len(stored)
        meta['reproduced'] = canon(ms) == canon(stored)
        assert meta['reproduced'], f'window {y}: {len(ms)} found, {len(stored)} stored'
        filed[str(y)] = ms; metas.append(meta)
    summary['filed_dates'] = {'windows': metas, 'matches_broad': sum(len(v) for v in filed.values()),
                              'matches_main': sum(m['main'] for v in filed.values() for m in v), 'reproduced': all(m['reproduced'] for m in metas)}
    (HERE/'matches_filed.json').write_text(json.dumps(filed, ensure_ascii=False), encoding='utf8')
    # 2. Printed dates.
    printed, metas = {}, []
    pages_of = year_pages(fix)
    for y in (1804, 1805, 1806, 1807, 1808, 1809):
        meta, ms = match_window(y, pages_of, focus)
        printed[str(y)] = ms; metas.append(meta)
    gaps = [abs(ordinal(m['a_date']) - ordinal(m['b_date'])) for v in printed.values() for m in v]
    summary['printed_dates'] = {'windows': metas, 'matches_broad': sum(len(v) for v in printed.values()),
                                'matches_main': sum(m['main'] for v in printed.values() for m in v), 'max_days_apart': max(gaps) if gaps else None}
    (HERE/'matches_printed.json').write_text(json.dumps(printed, ensure_ascii=False), encoding='utf8')
    (HERE/'rematch_summary.json').write_text(json.dumps(summary, indent=1), encoding='utf8')
    print(json.dumps({k: summary[k] for k in ('focus_pages', 'issues')} | {'filed': {k: v for k, v in summary['filed_dates'].items() if k != 'windows'},
                     'printed': {k: v for k, v in summary['printed_dates'].items() if k != 'windows'}}, indent=1), flush=True)


if __name__ == '__main__':
    main()
