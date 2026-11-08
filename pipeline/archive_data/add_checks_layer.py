"""Make a release that counts each printing once and adds the checks of the matched stories.

v0.6.0 = v0.5.2 plus:
1. One printing per matched story and page (merge_printings.py). The matcher listed some pages more than once for a
   story; v0.5.2 has 179,966 appearance rows for 163,926 distinct pages. reuse_families.appearances is recounted and
   now equals pages for every story.
2. derived/transcription_checks.parquet: for every printing, whether its passage also appears in the page's other
   transcription. work/transcription_check.py measured every matched segment of v0.5.2; here the segments of a page
   are combined, weighting each by its number of word 4-grams, and scored with the same thresholds.
3. derived/matched_audit.parquet: the random-sample audit of 200 matched stories against scan crops
   (work/audit_matched.py, outputs/matched_audit/): the reviewers' verdicts, the harmonised verdicts under PROTOCOL
   version 2, and the blind second reading of 30 stories.
Titles (reuse_family_titles) and topics (story_topics) are unchanged; story_topics.printings still counts the matched
segments of v0.5.2.

Usage (project root, Python 3.12):
    python work/archive_data/add_checks_layer.py 0.5.2 0.6.0
Inputs: outputs/transcription_check/ (measures.parquet, summary.json, README.md) and outputs/matched_audit/
(sample.json, verdicts/, adjustments.json, summary.json, second_reader/, PROTOCOL.md, README.md, crop_manifest.json).
"""
from pathlib import Path
import collections
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
CHECKS = PROJECT/'outputs/transcription_check'
AUDIT = PROJECT/'outputs/matched_audit'
sys.path.insert(0, str(WORK/'python_packages'))
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(HERE))
import pyarrow as pa
import pyarrow.parquet as pq
from merge_printings import merge, TOUCH
from transcription_check import status, K, CONFIRMED, PARTLY, READABLE, MIN_OTHER

RUN_MERGE, RUN_CHECK, RUN_AUDIT = 'run:printings-merge-v1', 'run:transcription-check-v1', 'run:matched-audit-v1'
STATUSES = ['confirmed', 'partly', 'missing_in_other', 'other_unreadable', 'no_second_transcription']
J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()
load = lambda path: json.loads(path.read_text(encoding='utf8'))


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def printing_checks(merged, measures):
    """One check per printing, from the measures of its matched segments (each weighted by its word 4-grams)."""
    by_seq = {(m['family_id'], m['seq']): m for m in measures}
    rows = []
    for p in merged:
        ms = [by_seq[p['family_id'], s] for s in json.loads(p['merged_seqs_json'])]
        assert all(m['page_id'] == p['page_id'] and m['transcription'] == p['transcription'] for m in ms), p
        assert len({(m['other_words'], m['page_agree']) for m in ms}) == 1, 'page-level measures differ within a page'
        w = [max(0, m['span_words'] - K + 1) for m in ms]
        contain = sum(m['contain'] * x for m, x in zip(ms, w)) / sum(w) if sum(w) else sum(m['contain'] for m in ms) / len(ms)
        r = {'family_id': p['family_id'], 'seq': p['seq'], 'page_id': p['page_id'], 'transcription': p['transcription'], 'segments': len(ms),
             'span_words': sum(e - s for s, e in json.loads(p['blocks_json'])), 'other_words': ms[0]['other_words'],
             'contain': round(contain, 3), 'page_agree': ms[0]['page_agree']}
        r['status'] = status(r)
        r['run_id'] = RUN_CHECK
        rows.append(r)
    return rows


def audit_rows(families):
    """The 200 audited stories: reviewers' verdicts, harmonised verdicts (PROTOCOL v2) and the blind second reading."""
    sample, adj = load(AUDIT/'sample.json'), load(AUDIT/'adjustments.json')
    raw, batch = {}, {}
    for f in sorted((AUDIT/'verdicts').glob('batch_*.json')):
        for v in load(f):
            raw[v['n']], batch[v['n']] = v, f.stem
    second = {v['n']: v for v in load(AUDIT/'second_reader/verdicts.json')}
    rows = []
    for s in sample['stories']:
        v = raw[s['n']]
        assert v['family_id'] == s['family_id'] and s['family_id'] in families, s['n']
        one, tr = adj['one_item'].get(str(s['n'])), adj['transcription'].get(str(s['n']))
        p = s['printings'][s['scan_check']]
        b = second.get(s['n'], {})
        assert not b or b['family_id'] == s['family_id']
        rows.append({'n': s['n'], 'family_id': s['family_id'], 'newspapers': s['newspapers'],
                     'scan_check_page_id': 'page:'+p['page_key'].replace('|', ':'), 'scan_check_date': p['date'], 'scan_check_transcription': p['transcription'],
                     # Harmonised (PROTOCOL.md version 2): written adjustments applied; every 'partly' was a crop that stopped short.
                     'one_item': one['to'] if one else v['one_item'], 'joined': 'none' if one and one['to'] == 'yes' else v['joined'],
                     'on_page': 'yes' if v['on_page'] == 'partly' else v['on_page'], 'transcription': tr['to'] if tr else v['transcription'],
                     'harmonisation_note': '; '.join(x['reason'] for x in (one, tr) if x) or None,
                     'reviewer_one_item': v['one_item'], 'reviewer_joined': v['joined'], 'reviewer_on_page': v['on_page'],
                     'reviewer_transcription': v['transcription'], 'confidence': v['confidence'], 'notes': v['notes'], 'review_batch': batch[s['n']],
                     'second_one_item': b.get('one_item'), 'second_joined': b.get('joined'), 'second_on_page': b.get('on_page'),
                     'second_transcription': b.get('transcription'), 'second_confidence': b.get('confidence'), 'second_notes': b.get('notes'),
                     'run_id': RUN_AUDIT})
    return rows, sample['meta']


def main(base_version, version):
    base, release = FOUNDATION/('v'+base_version), FOUNDATION/('v'+version)
    date = datetime.date.today().isoformat()
    if (release/'manifest.json').exists() and json.loads((release/'manifest.json').read_text())['status'] == 'released':
        raise SystemExit('Release '+version+' is immutable.')
    manifest = json.loads((base/'manifest.json').read_text(encoding='utf8'))
    assert manifest['status'] == 'released'
    for entry in manifest['files']:
        if file_sha(base/entry['path']) != entry['sha256']:
            raise ValueError('Base release file changed: '+entry['path'])
    if release.exists():
        shutil.rmtree(release)
    shutil.copytree(base, release, ignore=shutil.ignore_patterns('research.sqlite', 'manifest.json', 'validation.json', 'tables'))
    (release/'manifest.json').write_text(J({'status': 'draft', 'version': version}), encoding='utf8')
    (release/'tables').mkdir()
    src = sqlite3.connect((base/'research.sqlite').as_uri()+'?mode=ro', uri=True)
    db = sqlite3.connect(release/'research.sqlite')
    src.backup(db); src.close()
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')

    def source(path, kind):
        path = PROJECT/path
        rel = path.relative_to(PROJECT).as_posix(); digest = file_sha(path)
        sid = 'source:'+sha(rel+'@'+digest)[:24]
        if not db.execute('SELECT 1 FROM sources WHERE id=?', (sid,)).fetchone():
            target = f'sources/v{version}__'+rel.replace('/', '__')
            shutil.copyfile(path, release/target)
            db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?)', (sid, target, digest, path.stat().st_size, kind, None, 'sha256_verified_at_build'))
        return sid

    merge_code = source('work/archive_data/merge_printings.py', 'analysis_code')
    source('work/archive_data/add_checks_layer.py', 'migration_code')
    source('work/archive_data/validate.py', 'validation_code')
    check_code = source('work/transcription_check.py', 'analysis_code')
    source('outputs/transcription_check/measures.parquet', 'model_output')
    check_summary_src = source('outputs/transcription_check/summary.json', 'model_output_summary')
    source('outputs/transcription_check/README.md', 'documentation')
    audit_code = source('work/audit_matched.py', 'analysis_code')
    for rel, kind in [('PROTOCOL.md', 'documentation'), ('README.md', 'documentation'), ('sample.json', 'audit_sample'), ('adjustments.json', 'review_ledger'),
                      ('summary.json', 'model_output_summary'), ('crop_manifest.json', 'scan_crop_manifest'),
                      ('second_reader/verdicts.json', 'review_ledger'), ('second_reader/agreement.json', 'model_output_summary')]:
        source('outputs/matched_audit/'+rel, kind)
    for f in sorted((AUDIT/'verdicts').glob('batch_*.json')):
        source(f.relative_to(PROJECT).as_posix(), 'review_ledger')

    # 1. One printing per story and page.
    old = pq.read_table(release/'derived/reuse_family_appearances.parquet').to_pylist()
    merged = merge(old)
    assert len(merged) == len({(r['family_id'], r['page_id']) for r in old})
    pq.write_table(pa.Table.from_pylist(merged), release/'derived/reuse_family_appearances.parquet', compression='zstd')
    fam_table = pq.read_table(release/'derived/reuse_families.parquet')
    count = collections.Counter(r['family_id'] for r in merged)
    fams = fam_table.to_pylist()
    for f in fams:
        f['appearances'] = count[f['family_id']]
    assert all(f['appearances'] == f['pages'] for f in fams), 'a story has more printings than pages, or fewer'
    pq.write_table(pa.Table.from_pylist(fams, schema=fam_table.schema), release/'derived/reuse_families.parquet', compression='zstd')
    repeated = {r['family_id'] for r in merged if r['segments'] > 1}
    printings_meta = {'rule': 'one printing per matched story and page', 'run_id': RUN_MERGE, 'rows_before': len(old), 'printings': len(merged),
                      'stories_with_repeated_pages': len(repeated), 'pages_listed_more_than_once': sum(r['segments'] > 1 for r in merged),
                      'pages_with_separate_blocks': sum(len(json.loads(r['blocks_json'])) > 1 for r in merged), 'touch_words': TOUCH,
                      'kept': 'seq of the page\'s first row; first block as span; excerpt of the earliest row; all blocks in blocks_json'}

    # 2. Transcription check, one per printing.
    measures = pq.read_table(CHECKS/'measures.parquet').to_pylist()
    assert {(m['family_id'], m['seq']) for m in measures} == {(r['family_id'], r['seq']) for r in old}, 'measures must cover exactly the v0.5.2 segments'
    checks = printing_checks(merged, measures)
    pq.write_table(pa.Table.from_pylist(checks), release/'derived/transcription_checks.parquet', compression='zstd')
    by_story = collections.defaultdict(list)
    for c in checks:
        by_story[c['family_id']].append(c['status'])
    check_meta = {'status': 'automatic; says whether a passage is on the page, not whether every word was read correctly', 'run_id': RUN_CHECK,
                  'printings': len(checks), 'status_counts': {s: sum(c['status'] == s for c in checks) for s in STATUSES},
                  'status_by_matched_transcription': {t: {s: sum(c['status'] == s and c['transcription'] == t for c in checks) for s in STATUSES} for t in ('RevX', 'CA')},
                  'stories_by_status': dict(collections.Counter('all printings confirmed' if all(s == 'confirmed' for s in v) else
                                                                'at least one confirmed' if 'confirmed' in v else 'none confirmed' for v in by_story.values())),
                  'thresholds': {'confirmed': CONFIRMED, 'partly': PARTLY, 'other_readable_page_agree': READABLE, 'min_other_words': MIN_OTHER, 'k': K},
                  'segment_summary_source_id': check_summary_src,
                  'combined': 'segments of a page weighted by their word 4-grams (span_words - 3); page_agree is page-level'}

    # 3. The audit of 200 matched stories.
    audit, sample_meta = audit_rows({f['family_id'] for f in fams})
    pq.write_table(pa.Table.from_pylist(audit), release/'derived/matched_audit.parquet', compression='zstd')
    summary = load(AUDIT/'summary.json')
    summary.pop('not_yet_audited', None)
    audit_meta = {'status': 'AI reviewers against scan crops; harmonised under one written rule; not an independent human review', 'run_id': RUN_AUDIT,
                  'sample': sample_meta, 'summary': summary, 'second_reader': load(AUDIT/'second_reader/agreement.json'),
                  'fact_changing_range': {'reviewers_own_calls': summary['raw_reviewer_counts']['transcription'].get('major_problem'),
                                          'harmonised': summary['transcription']['major_problem'], 'located': summary['located_on_scan'],
                                          'reading': 'about 1 located passage in 5, up to 1 in 3, has a fact-changing misreading'}}

    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_MERGE, 'One printing per matched story and page: rows of the same page merged',
               J({'touch_words': TOUCH, 'rows_before': len(old), 'printings_after': len(merged), 'checked_against_scans': False}), merge_code, date, 'automated', 0))
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_CHECK, "Each printing's passage compared with the page's other transcription",
               J({'unit': 'word 4-grams, f and s folded', 'measure': 'contain / page_agree', 'thresholds': check_meta['thresholds'],
                  'combined_per_printing': check_meta['combined'], 'checked_against_scans': False}), check_code, date, 'automated', 0))
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_AUDIT, 'Random-sample audit of matched stories against scan crops',
               J({'seed': sample_meta['seed'], 'size': sample_meta['size'], 'population': sample_meta['population'], 'protocol': 'PROTOCOL.md version 2',
                  'reviewers': 'eight AI reviewers, harmonised under one written rule; a blind AI second reader for 30 stories',
                  'independent_human_review': False}), audit_code, date, 'ai_assistant', 0))
    reuse = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='reuse_layer'").fetchone()[0])
    reuse.update(family_appearances=len(merged), family_appearances_before_merge=len(old))
    db.execute("UPDATE metadata SET value_json=? WHERE key='reuse_layer'", (J(reuse),))
    for key, value in [('printings', printings_meta), ('transcription_check', check_meta), ('matched_audit', audit_meta)]:
        db.execute('INSERT INTO metadata VALUES (?,?)', (key, J(value)))
    release_meta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='release'").fetchone()[0])
    release_meta.update(version=version, date=date, previous_release=base_version)
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    history = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='migration_history'").fetchone()[0])
    history.append({'from': base_version, 'to': version, 'date': date, 'ledger': None, 'run_id': [RUN_MERGE, RUN_CHECK, RUN_AUDIT],
                    'note': 'one printing per story and page; transcription checks and the matched-story audit added as derived tables'})
    db.execute("UPDATE metadata SET value_json=? WHERE key='migration_history'", (J(history),))
    db.commit()

    view = json.loads((release/'views/pulse_boyd.json').read_text(encoding='utf8'))
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
    out = dict(manifest, version=version, status='released', created_date=date, previous_release=base_version,
               build_command=f'python work/archive_data/add_checks_layer.py {base_version} {version}', counts=results['counts'], files=files,
               reuse_layer=dict(manifest['reuse_layer'], family_appearances=len(merged), family_appearances_before_merge=len(old)),
               checks={'printings': len(merged), 'transcription_checks': check_meta['status_counts'], 'audited_stories': len(audit)})
    (release/'manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': version, 'path': 'v'+version, 'manifest_sha256': file_sha(release/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(release), 'checks': len(results['checks']), 'printings': printings_meta, 'transcription_checks': check_meta['status_counts'],
                      'stories_by_status': check_meta['stories_by_status'], 'audited': len(audit)}, indent=1), flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
