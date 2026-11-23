"""Match the pages that release v0.11.13 dates differently in the windows of their printed dates (2026-11-23).

corrections.json (beside this script) dates 26 pages differently from the date they are filed under: the pages of seven
National Intelligencer issues of 1802 filed under the wrong dates (the review of 1802, register X-1802-08). The all-years
matcher (work/reuse_all.py, run:reuse-all-v1) read them under their filed dates, so it compared them with the pages of the
wrong days. It also read the four pages filed under 24 November 1802, a second scan of the issue of 24 December, which
v0.11.13 leaves out of the analysis.

This script is outputs/filing_corrections/match_moved_pages.py (release v0.11.7) with this release's pages and base. It
applies the matcher's rules (the window function of outputs/kentucky_gazette_dates/rematch.py, which is
reuse_all.match_year restricted to pairs with a page in focus; every page of the window still counts for the
common-fingerprint rule) to the windows that hold these pages:
1. as filed: the pairs found must equal, field by field, the matches release v0.11.12 holds for these pages. Every one of
   them comes from the matcher's own run: no page that v0.10.2 or v0.11.7 dated differently falls in these windows (the
   script checks this), so the windows run in one state, every page as the matcher read it.
2. as printed: these pages at their printed dates, and the four second-scan pages out of every window.
Matches between other pages are not re-evaluated. Re-running a window in full could change a few of them through the
common-fingerprint counts, which this correction leaves as released.

Writes matches_filed.json (step 1), matches_printed.json (step 2) and rematch_summary.json next to this script.
Usage (project root, Python 3.12; a few minutes):  python outputs/filing_corrections_1802/match_moved_pages.py
"""
from pathlib import Path
import collections
import datetime
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'work/python_packages'))
sys.path.insert(0, str(ROOT/'work'))
import pyarrow.parquet as pq
import reuse_all as R   # the matcher: its token cache, fingerprints and constants

_spec = importlib.util.spec_from_file_location('kg_rematch', ROOT/'outputs/kentucky_gazette_dates/rematch.py')
KG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(KG)   # match_window(), corrections(), LCCN

BASE = ROOT/'outputs/data_foundation/v0.11.12'
EARLIER = ROOT/'outputs/filing_corrections/corrections.json'   # the pages v0.11.7 dated differently
key_of = lambda pid: pid.split(':', 1)[1].replace(':', '|')   # page:lccn:date:ed:page -> lccn|date|ed|page
page_of = lambda key: 'page:'+key.replace('|', ':')
year_of = lambda d: int(d[:4])


def corrections():
    """Focus pages (key -> filed date, printed date) and the second-scan pages (keys)."""
    c = json.loads((HERE/'corrections.json').read_text(encoding='utf8'))
    focus = {}
    for i in c['issue_dates']:
        lccn, filed, ed = i['issue_id'].split(':')[1:]
        for y in {year_of(filed), year_of(i['printed_date'])}:
            for p in R.load_year(y):
                if p['lccn'] == lccn and p['date'] == filed and p['key'].split('|')[2] == ed:
                    focus[p['key']] = (filed, i['printed_date'])
    issue_date = {i['issue_id']: i['printed_date'] for i in c['issue_dates']}
    for p in c['page_issues']:
        printed = issue_date.get(p['printed_issue'], p['printed_issue'].split(':')[2])
        focus[key_of(p['page_id'])] = (p['filed_issue'].split(':')[2], printed)
    drop = {key_of(s['page_id']) for s in c['second_scans']}
    return focus, drop


def kentucky_moves():
    """Token pages of the Kentucky Gazette issues dated by v0.10.2: key -> printed date."""
    fix = KG.corrections()
    moves = {}
    for y in sorted({year_of(d) for d in fix}):
        for p in R.load_year(y):
            if p['lccn'] == KG.LCCN and p['date'] in fix:
                moves[p['key']] = fix[p['date']]
    return moves


_cache = {}
def load(y):
    if y not in _cache:
        _cache[y] = R.load_year(y)
    return _cache[y]


def state(moves, drop=frozenset()):
    """pages_of(y) for KG.match_window: the token pages of year y with the given pages moved to new dates, some left out."""
    moved = collections.defaultdict(list)
    for y in sorted({year_of(k.split('|')[1]) for k in moves}):
        for p in load(y):
            if p['key'] in moves:
                moved[year_of(moves[p['key']])].append(dict(p, date=moves[p['key']]))
    def pages_of(y):
        return [p for p in load(y) if p['key'] not in moves and p['key'] not in drop] + moved.get(y, [])
    return pages_of


def windows(dates):
    """The window years that hold a page of any of these dates (its year, and the next while within the lookback)."""
    out = set()
    for d in dates:
        out.add(year_of(d))
        if datetime.date.fromisoformat(d).toordinal() >= datetime.date(year_of(d)+1, 1, 1).toordinal() - R.LOOKBACK:
            out.add(year_of(d)+1)
    return sorted(out)


def signature(m):
    return json.dumps({k: m[k] for k in ('a', 'b', 'a_date', 'b_date', 'a_span', 'b_span', 'matched_words', 'similarity', 'seeds', 'main', 'strict')}, sort_keys=True)


def stored(focus):
    """The matches release v0.11.12 holds for these pages, in the matcher's form."""
    pages = {page_of(k) for k in focus}
    out = []
    for m in pq.read_table(BASE/'derived/reuse_matches.parquet').to_pylist():
        if m['a_text_page_id'] in pages or m['b_text_page_id'] in pages:
            out.append({'a': key_of(m['a_text_page_id']), 'b': key_of(m['b_text_page_id']), 'a_date': m['a_date'], 'b_date': m['b_date'],
                        'a_span': [m['a_span_start'], m['a_span_end']], 'b_span': [m['b_span_start'], m['b_span_end']], 'matched_words': m['matched_words'],
                        'similarity': m['similarity'], 'seeds': m['seeds'], 'main': m['main'], 'strict': m['strict'], 'run_id': m['run_id']})
    return out


def main():
    focus, drop = corrections()
    assert len(focus) == 26 and len(drop) == 4, (len(focus), len(drop))
    kg = kentucky_moves()
    assert not set(focus) & set(kg) and not drop & set(kg)
    filed_windows = windows({f for f, _ in focus.values()})
    printed_windows = windows({p for _, p in focus.values()})
    # No page that an earlier release dated differently is in these windows: the Kentucky Gazette pages of v0.10.2 and the
    # pages of v0.11.7, at their filed or their printed dates. So every stored match of these pages is the matcher's own.
    earlier = json.loads(EARLIER.read_text(encoding='utf8'))
    years_of_earlier = {year_of(k.split('|')[1]) for k in kg} | {year_of(d) for d in kg.values()} |         {year_of(d) for c in earlier['issue_dates'] for d in (c['filed_date'], c['printed_date'])} |         {year_of(c[f].split(':')[2]) for c in earlier['page_issues'] for f in ('filed_issue', 'printed_issue')} |         {year_of(c[f].split(':')[2]) for c in earlier['second_scans'] for f in ('page_id', 'scan_of')}
    span = set(filed_windows) | set(printed_windows)
    assert not {y + d for y in years_of_earlier for d in (0, 1)} & span, (sorted(years_of_earlier), span)
    summary = {'focus_pages': sorted(focus), 'second_scans_left_out': sorted(drop), 'kentucky_gazette_pages_at_printed_dates': len(kg),
               'rules': {'lookback_days': R.LOOKBACK, 'max_pages': R.MAX_PAGES, 'max_occurrences': R.MAX_OCC, 'min_seeds': R.MIN_SEEDS,
                         'broad': R.BROAD, 'main': [80, 0.7], 'strict': [120, 0.8]}}

    # 1. As filed: reproduce the stored matches of these pages.
    keep = stored(focus)
    by_state = {'matcher': state({})}
    found, metas = collections.defaultdict(list), []
    for name, pages_of in by_state.items():
        for y in filed_windows:
            meta, ms = KG.match_window(y, pages_of, set(focus))
            on_kg = lambda m: m['a'] in kg or m['b'] in kg
            assert not any(on_kg(m) for m in ms)
            meta.update(state=name, kept=len(ms))
            found[str(y)] += ms
            metas.append(meta)
    canon = lambda ms: sorted(signature(m) for m in ms)
    reproduced = canon([m for v in found.values() for m in v]) == canon(keep)
    summary['filed_dates'] = {'windows': metas, 'stored': len(keep), 'stored_by_run': dict(collections.Counter(m['run_id'] for m in keep)),
                              'found': sum(len(v) for v in found.values()), 'reproduced': reproduced}
    assert reproduced, f'not reproduced: {len(keep)} stored, {sum(len(v) for v in found.values())} found'
    (HERE/'matches_filed.json').write_text(json.dumps(dict(found), ensure_ascii=False), encoding='utf8')

    # 2. As printed.
    moves = {k: p for k, (_, p) in focus.items()}
    pages_of = state(moves, frozenset(drop))
    printed, metas = {}, []
    for y in printed_windows:
        meta, ms = KG.match_window(y, pages_of, set(focus))
        meta['state'] = 'printed'
        assert not any(m['a'] in drop or m['b'] in drop for m in ms)
        printed[str(y)] = ms
        metas.append(meta)
    ordinal = lambda d: datetime.date.fromisoformat(d).toordinal()
    gaps = [abs(ordinal(m['a_date']) - ordinal(m['b_date'])) for v in printed.values() for m in v]
    summary['printed_dates'] = {'windows': metas, 'matches_broad': sum(len(v) for v in printed.values()),
                                'matches_main': sum(m['main'] for v in printed.values() for m in v), 'max_days_apart': max(gaps) if gaps else None}
    (HERE/'matches_printed.json').write_text(json.dumps(printed, ensure_ascii=False), encoding='utf8')
    (HERE/'rematch_summary.json').write_text(json.dumps(summary, indent=1), encoding='utf8')
    print(json.dumps({'filed': {k: v for k, v in summary['filed_dates'].items() if k != 'windows'},
                      'printed': {k: v for k, v in summary['printed_dates'].items() if k != 'windows'}}, indent=1), flush=True)


if __name__ == '__main__':
    main()
