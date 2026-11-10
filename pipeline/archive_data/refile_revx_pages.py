"""Make a correction release that files matched printings under the scan pages their RevX text transcribes (v0.8.1).

The RevX transcriptions of some issues are filed under the wrong page: the text stored with page n transcribes the scan
of another page of the same issue. outputs/revx_page_shift_check/ (check_page_shift.py, 2026-11-10) compared every
RevX page with the CA text of every page of its issue (the CA text is made from the page's own scan) and found 260 such
RevX pages in 133 issues:
- shifted (238 pages, 121 issues): one page off. In 120 of the issues one scan page has no RevX text, every later
  page's RevX text is filed one page early, and the issue's last RevX page is empty;
- other_page (7 pages): two or more pages off, in the New Hampshire Gazette of 4 April and 1 May 1798 and in the
  scrambled Kentucky Gazette of 22 May 1800;
- duplicate (15 pages, 11 issues): the RevX text repeats another page's, whose own RevX text is filed correctly.
A sample of 16 issues was confirmed against the pinned scans. The matcher read all 260 from RevX, so the automatic layer
filed their matched passages under the wrong page. This step (run:revx-page-refile-v1) applies the map:

1. derived/revx_page_map.parquet (run:revx-page-shift-check-v1): one row per misfiled RevX page: the page it is filed
   under (page_id), the scan page it transcribes (revx_text_of), status, offset and evidence (the share of its word
   4-grams found in the CA text of that scan page, and in its own page's).
2. derived/reuse_family_appearances.parquet: every printing read from such a text moves to the scan page the text
   transcribes (page_id, page_number). New column text_page_id: the page the matched text is filed under, which
   span_start, span_end and blocks_json index into. It equals page_id for every other printing.
   A moved printing can land on a page where its story already has a printing: the same printed passage read twice,
   from the RevX text filed one page early and from the CA text of the page whose RevX is empty, or from a repeated
   RevX page. One printing per story and page still holds, so the reads become one printing. The read kept follows the
   matcher's own rule (RevX when it has enough words, else CA), then a RevX text filed under its own page comes before
   one filed elsewhere, then the smallest seq. It keeps its seq, blocks, excerpt and merged seqs. New column
   other_texts_json lists the other reads (seq, merged_seqs, segments, transcription, text_page_id, blocks, excerpt);
   it is null for every other printing.
3. derived/reuse_families.parquet: appearances and pages recounted. Newspapers and dates cannot change, because a
   printing only moves within its issue.
4. derived/transcription_checks.parquet: the check of every moved printing, and of every CA printing on a scan page
   whose RevX text is filed under another page, is redone by the rule of run:transcription-check-v1 against the page's
   true other transcription (the measures of work/transcription_check.py, combined per printing as
   add_checks_layer.printing_checks does). Those rows carry run:revx-page-refile-v1. The checks of the reads merged
   into another printing are dropped. Before redoing them, the script computes each of these checks again with the
   old pairing and stops unless that reproduces the stored values exactly.
5. derived/reuse_matches.parquet: a match end read from a misfiled RevX text names the scan page (a_page_id,
   b_page_id). New columns a_text_page_id and b_text_page_id name the pages the matched texts are filed under.

Not changed: page_topic_census (the 260 rows of these pages still hold the topic weights of the text filed there;
correcting it needs the 143 scan pages that no RevX text transcribes to be scored), titles, story topics, the audit
(sample n 40 was scan-checked on a page whose RevX text is the next scan page; see metadata revx_page_map), and every
reviewed table (no reviewed printing uses the RevX text of a misfiled page; the script checks this).

Usage (project root, Python 3.12):
    python work/archive_data/refile_revx_pages.py 0.8.0 0.8.1 --keep-current
    python work/archive_data/refile_revx_pages.py 0.8.0 0.8.1 --dry-run       # counts only; writes nothing
Inputs: outputs/revx_page_shift_check/ (page_status.csv, shifted_issues.csv, summary.json, impact.json,
scan_confirmation.json, README.md, check_page_shift.py, measures/); the six pinned shards in work/data/ (hashes checked
against the release) for the texts; release v0.5.2 for the span of every merged segment.
"""
from pathlib import Path
import collections
import csv
import datetime
import hashlib
import json
import shutil
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
WORK = PROJECT/'work'
FOUNDATION = PROJECT/'outputs/data_foundation'
CHECK = PROJECT/'outputs/revx_page_shift_check'
SEGMENTS = FOUNDATION/'v0.5.2/derived/reuse_family_appearances.parquet'   # the matched segments before the v0.6.0 merge
sys.path.insert(0, str(WORK/'python_packages'))
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(HERE))
import pyarrow as pa
import pyarrow.parquet as pq
from reuse_all import tokenize                            # the matcher's own tokenizer, so span offsets line up
from transcription_check import fold, grams, status, K    # the check's own measures and status rule

RUN_MAP, RUN_REFILE = 'run:revx-page-shift-check-v1', 'run:revx-page-refile-v1'
MISFILED = ('shifted', 'other_page', 'duplicate')
STATUSES = ['confirmed', 'partly', 'missing_in_other', 'other_unreadable', 'no_second_transcription']
J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()
load = lambda path: json.loads(path.read_text(encoding='utf8'))
key_of = lambda pid: pid.split(':', 1)[1].replace(':', '|')   # page:lccn:date:ed:page -> lccn|date|ed|page


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def page_map():
    """The misfiled RevX pages of outputs/revx_page_shift_check/page_status.csv, one row each."""
    rows = []
    for r in csv.DictReader((CHECK/'page_status.csv').open(encoding='utf8')):
        if r['status'] in MISFILED:
            issue = 'page:'+r['issue'].replace('|', ':')
            rows.append({'page_id': f"{issue}:{r['revx_page']}", 'revx_text_of': f"{issue}:{r['filed_at']}", 'status': r['status'],
                         'offset': int(r['offset']), 'share4_at': float(r['share4_at']), 'share4_own': float(r['share4_own']),
                         'revx_same_as_own_revx': float(r['revx_same_as_own_revx']) if r['revx_same_as_own_revx'] else None,
                         'evidence': r['basis'], 'run_id': RUN_MAP})
    return sorted(rows, key=lambda m: m['page_id'])


def pinned_shards(db):
    """Check the six pinned shards against the release's source records; return their file names."""
    names = set()
    for path, digest in db.execute("SELECT path, sha256 FROM sources WHERE kind='raw_parquet'"):
        name = Path(path).name
        if file_sha(WORK/'data'/name) != digest:
            raise ValueError('Pinned shard changed: '+name)
        names.add(name)
    assert len(names) == 6, names
    return names


def texts(page_ids, shards):
    """Tokens of both transcriptions of the given pages, read from the pinned shards."""
    want = {key_of(p): p for p in page_ids}
    where = {r['key']: (r['file'], r['file_row']) for r in pq.read_table(WORK/'page_audit.parquet', columns=['key', 'file', 'file_row']).to_pylist()
             if r['key'] in want}
    assert len(where) == len(want), 'pages missing from page_audit'
    by_file = collections.defaultdict(dict)
    for k, (f, row) in where.items():
        by_file[f][row] = want[k]
    out = {}
    for f, rows in sorted(by_file.items()):
        assert f in shards, f
        pf, offset = pq.ParquetFile(WORK/'data'/f), 0
        for g in range(pf.num_row_groups):
            n = pf.metadata.row_group(g).num_rows
            hit = [rw for rw in rows if offset <= rw < offset + n]
            if hit:
                t = pf.read_row_group(g, columns=['RevX_OCR_text', 'ca_ocr_text'])
                for rw in hit:
                    out[rows[rw]] = {'RevX': tokenize(t['RevX_OCR_text'][rw - offset].as_py() or ''), 'CA': tokenize(t['ca_ocr_text'][rw - offset].as_py() or '')}
            offset += n
    assert len(out) == len(want)
    return out


def check(p, sel, other, spans):
    """A printing's transcription check by the rule of run:transcription-check-v1: transcription_check.measure() for each
    matched segment (sel: the matched text's tokens; other: the page's other transcription), combined as
    add_checks_layer.printing_checks() does, each segment weighted by its word 4-grams."""
    fs = fold(sel)
    g_other, g_sel = grams(fold(other)), grams(fs)
    page_agree = round(len(g_sel & g_other) / len(g_sel), 3) if g_sel else 0.0
    contains, weights = [], []
    for s, e in spans:
        assert e <= len(sel), (p['family_id'], p['seq'], e, len(sel))
        g_span = grams(fs[s:e])
        contains.append(round(len(g_span & g_other) / len(g_span), 3) if g_span else 0.0)
        weights.append(max(0, e - s - K + 1))
    contain = sum(c * w for c, w in zip(contains, weights)) / sum(weights) if sum(weights) else sum(contains) / len(contains)
    r = {'family_id': p['family_id'], 'seq': p['seq'], 'page_id': p['page_id'], 'transcription': p['transcription'], 'segments': len(spans),
         'span_words': sum(e - s for s, e in json.loads(p['blocks_json'])), 'other_words': len(other), 'contain': round(contain, 3), 'page_agree': page_agree}
    r['status'] = status(r)
    return r


def main(base_version, version, keep_current=False, dry_run=False):
    base, release = FOUNDATION/('v'+base_version), FOUNDATION/('v'+version)
    date = datetime.date.today().isoformat()
    if (release/'manifest.json').exists() and json.loads((release/'manifest.json').read_text())['status'] == 'released':
        raise SystemExit('Release '+version+' is immutable.')
    manifest = load(base/'manifest.json')
    assert manifest['status'] == 'released'
    for entry in manifest['files']:
        if file_sha(base/entry['path']) != entry['sha256']:
            raise ValueError('Base release file changed: '+entry['path'])
    src = sqlite3.connect((base/'research.sqlite').as_uri()+'?mode=ro', uri=True)
    shards = pinned_shards(src)
    summary = load(CHECK/'summary.json')

    # 0. The map, and what may use it.
    pmap = page_map()
    to = {m['page_id']: m['revx_text_of'] for m in pmap}
    sources_of = collections.defaultdict(list)   # scan page -> the misfiled RevX pages that transcribe it
    for m in pmap:
        sources_of[m['revx_text_of']].append(m)
    counts = collections.Counter(m['status'] for m in pmap)
    assert len(to) == len(pmap) == sum(summary['revx_pages_by_status'][s] for s in MISFILED), counts
    selected = {'page:'+r['key'].replace('|', ':'): r['selected_source'] for r in pq.read_table(WORK/'page_audit.parquet', columns=['key', 'selected_source']).to_pylist()}
    assert all(selected[p] == 'RevX' for p in to), 'the matcher read every misfiled page from RevX'
    orphans = sorted(p for p in to if p not in sources_of)   # scan pages whose text no RevX page carries
    assert len(orphans) == summary['scan_pages_with_no_revx_text']['pages'], len(orphans)
    for pv, field in src.execute('SELECT page_version_id, transcription_field FROM observations'):
        assert pv.split('@')[0] not in to or field != 'RevX_OCR_text', 'a reviewed printing uses the RevX text of a misfiled page: '+pv

    # 1. Printings: move, then merge the reads of one page.
    app_table = pq.read_table(base/'derived/reuse_family_appearances.parquet')
    rows = app_table.to_pylist()
    lccns_before = collections.defaultdict(set)
    for r in rows:
        lccns_before[r['family_id']].add(r['lccn'])
        r['text_page_id'], r['other_texts_json'] = r['page_id'], None
        if r['transcription'] == 'RevX' and r['page_id'] in to:
            r['page_id'] = to[r['page_id']]
            r['page_number'] = int(r['page_id'].rsplit(':', 1)[1])
    moved = [r for r in rows if r['text_page_id'] != r['page_id']]
    by_page = collections.defaultdict(list)
    for r in rows:
        by_page[(r['family_id'], r['page_id'])].append(r)
    printings, folded, merged_kinds = [], [], collections.Counter()
    for rs in by_page.values():
        rs.sort(key=lambda r: (r['transcription'] != 'RevX', r['text_page_id'] != r['page_id'], r['seq']))
        keep = rs[0]
        if len(rs) > 1:
            keep['other_texts_json'] = json.dumps([{'seq': x['seq'], 'merged_seqs': json.loads(x['merged_seqs_json']), 'segments': x['segments'],
                                                    'transcription': x['transcription'], 'text_page_id': x['text_page_id'],
                                                    'blocks': json.loads(x['blocks_json']), 'excerpt': x['excerpt']} for x in rs[1:]], ensure_ascii=False)
            folded += rs[1:]
            merged_kinds[' + '.join(('moved ' if x['text_page_id'] != x['page_id'] else 'own ') + x['transcription'] for x in rs)] += 1
        printings.append(keep)
    printings.sort(key=lambda r: (r['family_id'], r['seq']))
    lccns_after = collections.defaultdict(set)
    for p in printings:
        lccns_after[p['family_id']].add(p['lccn'])
    assert lccns_after == lccns_before, 'a story lost or gained a newspaper'
    schema = app_table.schema.append(pa.field('text_page_id', pa.string())).append(pa.field('other_texts_json', pa.string()))
    printings_meta = {'moved': len(moved), 'moved_by_status': dict(collections.Counter(next(m['status'] for m in pmap if m['page_id'] == r['text_page_id']) for r in moved)),
                      'stories_moved': len({r['family_id'] for r in moved}), 'reads_merged_into_another': len(folded),
                      'stories_merged': len({r['family_id'] for r in folded}), 'merged_pages_by_reads': dict(merged_kinds.most_common()),
                      'printings_before': len(rows), 'printings_after': len(printings)}

    # 2. Stories: recount.
    fam_table = pq.read_table(base/'derived/reuse_families.parquet')
    fams = fam_table.to_pylist()
    count = collections.Counter(p['family_id'] for p in printings)
    printings_meta['stories_recounted'] = sum(f['appearances'] != count[f['family_id']] for f in fams)
    for f in fams:
        f['appearances'] = f['pages'] = count[f['family_id']]

    # 3. Transcription checks: redo those whose pairing the map changes; first reproduce them as they are.
    old_checks = {(c['family_id'], c['seq']): c for c in pq.read_table(base/'derived/transcription_checks.parquet').to_pylist()}
    redo = [p for p in printings if p['text_page_id'] != p['page_id'] or (p['transcription'] == 'CA' and p['page_id'] in sources_of)]
    want = {(p['family_id'], s) for p in redo for s in json.loads(p['merged_seqs_json'])}
    segs = {(r['family_id'], r['seq']): r for r in pq.read_table(SEGMENTS, columns=['family_id', 'seq', 'page_id', 'span_start', 'span_end', 'transcription']).to_pylist()
            if (r['family_id'], r['seq']) in want}
    best_source = {page: max(ms, key=lambda m: m['share4_at'])['page_id'] for page, ms in sources_of.items()}
    tokens = texts({p['text_page_id'] for p in redo} | {p['page_id'] for p in redo} | {best_source[p['page_id']] for p in redo if p['page_id'] in best_source}, shards)
    new_checks, redone = {}, collections.Counter()
    for p in redo:
        spans = []
        for s in json.loads(p['merged_seqs_json']):
            g = segs[(p['family_id'], s)]
            assert g['page_id'] == p['text_page_id'] and g['transcription'] == p['transcription'], (p['family_id'], s)
            spans.append((g['span_start'], g['span_end']))
        own = tokens[p['text_page_id']]
        old = old_checks[(p['family_id'], p['seq'])]
        again = check(dict(p, page_id=p['text_page_id']), own[p['transcription']], own['RevX' if p['transcription'] == 'CA' else 'CA'], spans)
        assert old['page_id'] == p['text_page_id'] and all(again[k] == old[k] for k in again), ('old check not reproduced', old, again)
        if p['text_page_id'] != p['page_id']:   # moved: its RevX text against the CA text of the scan page it transcribes
            r, why = check(p, own['RevX'], tokens[p['page_id']]['CA'], spans), 'moved'
        else:                                   # CA on a scan page whose RevX text is filed under another page
            r, why = check(p, own['CA'], tokens[best_source[p['page_id']]]['RevX'], spans), 'CA on a page whose RevX is filed elsewhere'
        r['run_id'] = RUN_REFILE
        new_checks[(p['family_id'], p['seq'])] = r
        redone[(why, old['status'], r['status'])] += 1
    checks = []
    for p in printings:
        c = new_checks.get((p['family_id'], p['seq'])) or old_checks[(p['family_id'], p['seq'])]
        assert c['page_id'] == p['page_id']
        checks.append(c)
    by_story = collections.defaultdict(list)
    for c in checks:
        by_story[c['family_id']].append(c['status'])
    check_meta_update = {'printings': len(checks), 'status_counts': {s: sum(c['status'] == s for c in checks) for s in STATUSES},
                         'status_by_matched_transcription': {t: {s: sum(c['status'] == s and c['transcription'] == t for c in checks) for s in STATUSES} for t in ('RevX', 'CA')},
                         'stories_by_status': dict(collections.Counter('all printings confirmed' if all(s == 'confirmed' for s in v) else
                                                                       'at least one confirmed' if 'confirmed' in v else 'none confirmed' for v in by_story.values()))}
    redo_meta = {'run_id': RUN_REFILE, 'redone': len(new_checks), 'dropped_with_merged_reads': len(folded),
                 'redone_by_reason': {why: dict(collections.Counter({k[2]: n for k, n in redone.items() if k[0] == why})) for why in {k[0] for k in redone}},
                 'status_before_redone': dict(collections.Counter(old_checks[k]['status'] for k in new_checks)),
                 'rule': 'run:transcription-check-v1, against the page\'s true other transcription: a moved RevX text against the CA text of the scan '
                         'page it transcribes; a CA text against the RevX text filed under another page that transcribes its scan (the best match '
                         'where two do)'}

    # 4. Matches: the scan page of each end, and the page its text is filed under.
    mt = pq.read_table(base/'derived/reuse_matches.parquet')
    text_a, text_b = mt['a_page_id'].to_pylist(), mt['b_page_id'].to_pylist()
    mt = mt.set_column(mt.schema.get_field_index('a_page_id'), 'a_page_id', pa.array([to.get(x, x) for x in text_a], pa.string()))
    mt = mt.set_column(mt.schema.get_field_index('b_page_id'), 'b_page_id', pa.array([to.get(x, x) for x in text_b], pa.string()))
    mt = mt.append_column('a_text_page_id', pa.array(text_a, pa.string())).append_column('b_text_page_id', pa.array(text_b, pa.string()))
    match_meta = {'matches_with_a_moved_end': sum(1 for a, b in zip(text_a, text_b) if a in to or b in to), 'ends_moved': sum(x in to for x in text_a + text_b)}

    census = pq.read_table(base/'derived/page_topic_census.parquet', columns=['page_id']).to_pylist()
    audit_rows = [r for r in pq.read_table(base/'derived/matched_audit.parquet', columns=['n', 'family_id', 'scan_check_page_id', 'on_page']).to_pylist() if r['scan_check_page_id'] in to]
    shifted = list(csv.DictReader((CHECK/'shifted_issues.csv').open(encoding='utf8')))
    map_meta = {
        'status': 'automatic; checked against the pinned scans for a sample of 16 issues; not an independent review',
        'run_id': RUN_MAP, 'refile_run_id': RUN_REFILE,
        'misfiled_revx_pages': dict(counts),
        'issues': {'with_misfiled_revx_pages': len(shifted), 'by_check_label': dict(collections.Counter(r['kind'] for r in shifted)),
                   'with_pages_of_status': {s: len({m['page_id'].rsplit(':', 1)[0] for m in pmap if m['status'] == s}) for s in MISFILED}},
        'rule': summary['thresholds'],
        'scan_pages_without_revx_text': orphans,
        'printings': printings_meta, 'transcription_checks': redo_meta, 'reuse_matches': match_meta,
        'not_changed': {
            'page_topic_census': f"{sum(1 for c in census if c['page_id'] in to)} rows of misfiled RevX pages still hold the topic weights of the text filed "
                                 f"there; correcting them needs the {len(orphans)} scan pages that no RevX text transcribes to be scored",
            'matched_audit': [f"sample n {r['n']} ({r['family_id']}) was scan-checked on {r['scan_check_page_id']}, whose RevX text transcribes "
                              f"{to[r['scan_check_page_id']]}; the verdict on_page='{r['on_page']}' is left as recorded for the page shown" for r in audit_rows],
            'reviewed': 'no reviewed printing uses the RevX text of a misfiled page',
            'titles_and_story_topics': 'computed from the matched texts, which do not change'},
        'not_read': f"the text of the {len(orphans)} scan pages that no RevX text transcribes was never read by the matcher (their CA text could be)"}
    print(json.dumps({'map': dict(counts), 'orphans': len(orphans), 'printings': printings_meta, 'stories_recounted': printings_meta['stories_recounted'],
                      'checks_redone': {f'{k[0]}: {k[1]} -> {k[2]}': n for k, n in sorted(redone.items())}, 'check_status_counts': check_meta_update['status_counts'],
                      'stories_by_status': check_meta_update['stories_by_status'], 'matches': match_meta, 'audit_rows': audit_rows}, indent=1), flush=True)
    if dry_run:
        return

    # 5. Write the release.
    if release.exists():
        shutil.rmtree(release)   # only an unreleased draft
    shutil.copytree(base, release, ignore=shutil.ignore_patterns('research.sqlite', 'manifest.json', 'validation.json', 'tables'))
    (release/'manifest.json').write_text(J({'status': 'draft', 'version': version}), encoding='utf8')
    (release/'tables').mkdir()
    db = sqlite3.connect(release/'research.sqlite')
    src.backup(db)
    src.close()
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')

    def source(path, kind):
        path = PROJECT/path
        rel = path.relative_to(PROJECT).as_posix()
        digest = file_sha(path)
        sid = 'source:'+sha(rel+'@'+digest)[:24]
        if not db.execute('SELECT 1 FROM sources WHERE id=?', (sid,)).fetchone():
            target = f'sources/v{version}__'+rel.replace('/', '__')
            shutil.copyfile(path, release/target)
            db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?)', (sid, target, digest, path.stat().st_size, kind, None, 'sha256_verified_at_build'))
        return sid

    check_code = source('outputs/revx_page_shift_check/check_page_shift.py', 'analysis_code')
    for rel, kind in [('page_status.csv', 'model_output'), ('shifted_issues.csv', 'model_output'), ('measures/pages.parquet', 'model_output'),
                      ('measures/pairs.parquet', 'model_output'), ('impact.json', 'model_output_summary'), ('scan_confirmation.json', 'scan_review'),
                      ('README.md', 'documentation')]:
        source('outputs/revx_page_shift_check/'+rel, kind)
    map_meta['summary_source_id'] = source('outputs/revx_page_shift_check/summary.json', 'model_output_summary')
    refile_code = source('work/archive_data/refile_revx_pages.py', 'migration_code')
    source('work/transcription_check.py', 'analysis_code')
    source('work/archive_data/validate.py', 'validation_code')
    scans = load(CHECK/'scan_confirmation.json')
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_MAP, 'Each RevX page compared with the CA text of every page of its issue, to find RevX texts filed under another page than the scan they transcribe',
               J({'unit': 'distinct word 4-grams, f and s folded (the matcher\'s tokenizer)', 'thresholds': summary['thresholds'], 'pages': summary['pages'],
                  'revx_pages_tested': summary['revx_pages_tested'], 'checked_against_scans': {'issues': scans['issues_sampled'], 'seed': scans['seed'], 'tally': scans['tally']}}),
               check_code, summary['date'], 'automated', 0))
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_REFILE, 'Matched printings and match ends read from a misfiled RevX text filed under the scan page it transcribes; reads of one page merged; their transcription checks redone',
               J({'map_run_id': RUN_MAP, 'moved': len(moved), 'reads_merged_into_another': len(folded), 'printings_after': len(printings), 'checks_redone': len(new_checks),
                  'match_ends_moved': match_meta['ends_moved'], 'kept_read': 'RevX before CA, then a RevX text filed under its own page, then the smallest seq',
                  'checked_against_scans': False}), refile_code, date, 'automated', 0))
    reuse = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='reuse_layer'").fetchone()[0])
    reuse.update(family_appearances=len(printings))
    db.execute("UPDATE metadata SET value_json=? WHERE key='reuse_layer'", (J(reuse),))
    pmeta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='printings'").fetchone()[0])
    pmeta.update(printings=len(printings), revx_refile={'run_id': RUN_REFILE, 'moved': len(moved), 'reads_merged_into_another': len(folded), 'printings_before': len(rows)})
    db.execute("UPDATE metadata SET value_json=? WHERE key='printings'", (J(pmeta),))
    cmeta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='transcription_check'").fetchone()[0])
    cmeta.update(check_meta_update, revx_refile={k: redo_meta[k] for k in ('run_id', 'redone', 'dropped_with_merged_reads')})
    db.execute("UPDATE metadata SET value_json=? WHERE key='transcription_check'", (J(cmeta),))
    db.execute('INSERT INTO metadata VALUES (?,?)', ('revx_page_map', J(map_meta)))
    release_meta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='release'").fetchone()[0])
    release_meta.update(version=version, date=date, previous_release=base_version)
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    history = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='migration_history'").fetchone()[0])
    history.append({'from': base_version, 'to': version, 'date': date, 'ledger': None, 'run_id': [RUN_MAP, RUN_REFILE],
                    'note': 'matched printings and match ends filed under the scan pages their RevX texts transcribe (RevX page map); reads of one page merged; their transcription checks redone'})
    db.execute("UPDATE metadata SET value_json=? WHERE key='migration_history'", (J(history),))
    db.commit()

    pq.write_table(pa.Table.from_pylist(pmap), release/'derived/revx_page_map.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist(printings, schema=schema), release/'derived/reuse_family_appearances.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist(fams, schema=fam_table.schema), release/'derived/reuse_families.parquet', compression='zstd')
    tc_schema = pq.read_schema(base/'derived/transcription_checks.parquet')
    pq.write_table(pa.Table.from_pylist(checks, schema=tc_schema), release/'derived/transcription_checks.parquet', compression='zstd')
    pq.write_table(mt, release/'derived/reuse_matches.parquet', compression='zstd')

    view = load(release/'views/pulse_boyd.json')
    view.update(schema_version=version, release_id='newspapers-v'+version)
    (release/'views/pulse_boyd.json').write_text(json.dumps(view, ensure_ascii=False, indent=2), encoding='utf8')
    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        with (release/'tables'/f'{table}.jsonl').open('w', encoding='utf8', newline='\n') as f:
            for row in db.execute(f'SELECT * FROM {table} ORDER BY 1'):
                values = dict(row)
                for k in list(values):
                    if k.endswith('_json') and values[k] is not None:
                        values[k[:-5]] = json.loads(values.pop(k))
                f.write(J(values)+'\n')
    db.close()
    shutil.copyfile(HERE/'README.md', release/'README.md')
    from validate import validate
    results = validate(release)
    (release/'validation.json').write_text(json.dumps(results, indent=2), encoding='utf8')
    files = [{'path': p.relative_to(release).as_posix(), 'bytes': p.stat().st_size, 'sha256': file_sha(p)}
             for p in sorted(release.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    out = dict(manifest, version=version, status='released', created_date=date, previous_release=base_version, observed_publications_added=0,
               build_command=f'python work/archive_data/refile_revx_pages.py {base_version} {version}'+(' --keep-current' if keep_current else ''),
               counts=results['counts'], files=files,
               revx_page_map={'misfiled_revx_pages': dict(counts), 'printings_moved': len(moved), 'reads_merged_into_another': len(folded),
                              'printings': len(printings), 'transcription_checks_redone': len(new_checks), 'match_ends_moved': match_meta['ends_moved']})
    (release/'manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    if not keep_current:
        (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': version, 'path': 'v'+version, 'manifest_sha256': file_sha(release/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(release), 'checks': len(results['checks']), 'files': len(files), 'current_moved': not keep_current}), flush=True)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0], args[1], keep_current='--keep-current' in sys.argv, dry_run='--dry-run' in sys.argv)
