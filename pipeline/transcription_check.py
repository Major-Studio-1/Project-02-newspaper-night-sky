"""Check every printing of a matched story against the page's other transcription (2026-11-08).

Every page of the dataset has two machine transcriptions: the Library of Congress OCR ("CA") and a newer AI
transcription ("RevX"). The text-reuse matcher read one of them per page (RevX when it had enough words, else CA).
This script asks, for each of the 179,966 printings of matched stories: does the same passage also appear in the
page's other transcription? Two independent readings that agree make it very likely the words are on the page.

Measures, per printing:
- contain:    the share of the passage's word 4-grams that also occur in the other transcription of the page;
- page_agree: the same share for the whole page, a baseline for how well the two transcriptions agree there.
Old OCR often reads the long s as f, so f and s count as the same letter on both sides.

The old OCR is noisy, so even whole pages share only 30-50% of their 4-grams between the two transcriptions. The
status therefore compares each passage with its own page (contain / page_agree): a passage that agrees about as well
as the rest of its page is confirmed; one that is almost absent from a page the other transcription otherwise reads
is flagged.

Usage (project root, Python 3.12):
    python work/transcription_check.py          # measure (reads the six dataset shards once, about 10-20 minutes)
    python work/transcription_check.py classify # re-run only the classification and summary on the stored measures
Writes outputs/transcription_check/measures.parquet, checks.parquet (with a status per printing) and summary.json.
"""
from pathlib import Path
import collections
import json
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
sys.path.insert(0, str(ROOT))
import pyarrow as pa
import pyarrow.parquet as pq
from reuse_all import tokenize  # the matcher's own tokenizer, so span offsets line up exactly

PROJECT = ROOT.parent
CURRENT = json.loads((PROJECT/'outputs/data_foundation/CURRENT.json').read_text(encoding='utf8'))
RELEASE = PROJECT/'outputs/data_foundation'/CURRENT['path']
OUT = PROJECT/'outputs/transcription_check'
K = 4
# Status thresholds, on the passage-to-page ratio (see summary.json for the distributions they were chosen from).
CONFIRMED, PARTLY, READABLE, MIN_OTHER = 0.6, 0.3, 0.15, 50


def fold(tokens):
    return [t.replace('f', 's') for t in tokens]


def grams(tokens):
    return {' '.join(tokens[i:i+K]) for i in range(len(tokens) - K + 1)}


def measure():
    apps = pq.read_table(RELEASE/'derived/reuse_family_appearances.parquet',
                         columns=['family_id', 'seq', 'page_id', 'span_start', 'span_end', 'transcription']).to_pylist()
    key_of = lambda pid: '|'.join(pid.split(':')[1:])   # page:lccn:date:ed:page -> lccn|date|ed|page
    by_key = collections.defaultdict(list)
    for i, a in enumerate(apps):
        by_key[key_of(a['page_id'])].append(i)
    audit = {r['key']: r for r in pq.read_table(ROOT/'page_audit.parquet', columns=['key', 'file', 'file_row', 'selected_source']).to_pylist()
             if r['key'] in by_key}
    assert len(audit) == len(by_key), 'pages missing from page_audit'
    want = collections.defaultdict(dict)
    for k, r in audit.items():
        want[r['file']][r['file_row']] = k
    rows, t0 = [None] * len(apps), time.time()
    for shard in sorted(want):
        pf, offset, wanted = pq.ParquetFile(ROOT/'data'/shard), 0, want[shard]
        for g in range(pf.num_row_groups):
            n = pf.metadata.row_group(g).num_rows
            hit = [rw for rw in wanted if offset <= rw < offset + n]
            if hit:
                table = pf.read_row_group(g, columns=['RevX_OCR_text', 'ca_ocr_text'])
                for rw in hit:
                    key = wanted[rw]
                    source = audit[key]['selected_source']
                    revx, ca = tokenize(table['RevX_OCR_text'][rw - offset].as_py()), tokenize(table['ca_ocr_text'][rw - offset].as_py())
                    sel, other = (revx, ca) if source == 'RevX' else (ca, revx)
                    fs = fold(sel)
                    g_other, g_sel = grams(fold(other)), grams(fs)
                    page_agree = len(g_sel & g_other) / len(g_sel) if g_sel else 0.0
                    for i in by_key[key]:
                        a = apps[i]
                        assert a['transcription'] == source, (key, a['transcription'], source)
                        s, e = a['span_start'], a['span_end']
                        assert e <= len(sel), (key, e, len(sel))
                        g_span = grams(fs[s:e])
                        contain = len(g_span & g_other) / len(g_span) if g_span else 0.0
                        rows[i] = {'family_id': a['family_id'], 'seq': a['seq'], 'page_id': a['page_id'], 'transcription': source,
                                   'span_words': e - s, 'other_words': len(other), 'contain': round(contain, 3), 'page_agree': round(page_agree, 3)}
            offset += n
        print(f'{shard}: {sum(r is not None for r in rows):,} printings measured, {time.time() - t0:.0f} s', flush=True)
    assert all(r is not None for r in rows), 'some printings were not measured'
    OUT.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), OUT/'measures.parquet')


def status(r):
    if r['other_words'] < MIN_OTHER:
        return 'no_second_transcription'
    if r['page_agree'] < READABLE:
        return 'other_unreadable'   # the other transcription shares too little of this page to tell
    ratio = r['contain'] / r['page_agree']
    if ratio >= CONFIRMED:
        return 'confirmed'
    if ratio >= PARTLY:
        return 'partly'
    # Telling: the other transcription reads the rest of this page, yet lacks this passage.
    return 'missing_in_other'


def classify():
    rows = pq.read_table(OUT/'measures.parquet').to_pylist()
    for r in rows:
        r['status'] = status(r)
    pq.write_table(pa.Table.from_pylist(rows), OUT/'checks.parquet')
    counts = collections.Counter(r['status'] for r in rows)
    by_source = {s: dict(collections.Counter(r['status'] for r in rows if r['transcription'] == s)) for s in ('RevX', 'CA')}
    hist = lambda vals: [sum(1 for v in vals if lo <= v < lo + .1 or (lo >= .9 and v == 1.0)) for lo in [x / 10 for x in range(10)]]
    readable = [r for r in rows if r['page_agree'] >= READABLE and r['other_words'] >= MIN_OTHER and r['page_agree'] > 0]
    stories = collections.defaultdict(list)
    for r in rows:
        stories[r['family_id']].append(r['status'])
    story_counts = collections.Counter('all printings confirmed' if all(s == 'confirmed' for s in v)
                                       else 'at least one confirmed' if any(s == 'confirmed' for s in v)
                                       else 'none confirmed' for v in stories.values())
    by_year = collections.defaultdict(collections.Counter)
    for r in rows:
        by_year[r['page_id'].split(':')[2][:4]][r['status']] += 1
    summary = {'run': 'transcription-check-v1', 'release': CURRENT['version'], 'printings': len(rows), 'stories': len(stories),
               'k': K, 'thresholds': {'confirmed': CONFIRMED, 'partly': PARTLY, 'other_readable_page_agree': READABLE, 'min_other_words': MIN_OTHER},
               'status': dict(counts), 'status_by_matched_transcription': by_source, 'stories_by_status': dict(story_counts),
               'histogram_contain_all': hist([r['contain'] for r in rows]),
               'histogram_contain_where_other_reads_page': hist([r['contain'] for r in readable]),
               'histogram_page_agree': hist([r['page_agree'] for r in rows if r['other_words'] >= MIN_OTHER]),
               'histogram_ratio_where_readable_0_to_1_2plus': [sum(1 for r in readable if min(12, int(r['contain'] / r['page_agree'] * 10)) == k) for k in range(13)],
               'by_year': {y: dict(c) for y, c in sorted(by_year.items())}}
    (OUT/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    print(json.dumps({k: summary[k] for k in ['printings', 'stories', 'status', 'status_by_matched_transcription', 'stories_by_status',
                                              'histogram_contain_all', 'histogram_contain_where_other_reads_page', 'histogram_page_agree']}, indent=1))


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'classify':
        measure()
    classify()
