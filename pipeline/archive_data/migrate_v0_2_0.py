"""Migrate release 0.1.0 to 0.2.0 by applying the reviewed 1797 expansion ledger.

Release 0.1.0 is read-only input: its files are hash-checked, copied, and its database is
copied with SQLite's backup API. Every new row cites the ledger. Run from the project root:

    <python 3.12> work/archive_data/migrate_v0_2_0.py
"""
from pathlib import Path
import collections
import hashlib
import json
import re
import shutil
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
WORK = PROJECT/'work'
OUT = PROJECT/'outputs'
sys.path.insert(0, str(WORK/'python_packages'))
import pyarrow.parquet as pq

BASE_VERSION = '0.1.0'
VERSION = '0.2.0'
DATE = '2026-11-06'
FOUNDATION = OUT/'data_foundation'
BASE = FOUNDATION/('v'+BASE_VERSION)
RELEASE = FOUNDATION/('v'+VERSION)
LEDGER_PATH = HERE/'ledgers/expansion_1797.json'
EVIDENCE = OUT/'pilot_expansion_2026-11-05/evidence'
RUN = 'run:expansion-1797-v1'
NAMESPACE = 'expansion-1797'

J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def normalized(text):
    # Same locator normalization as release 0.1.0 (build.py).
    return re.sub(r'\s+', ' ', re.sub(r'(?<=\w)-\s+(?=\w)', '', text or '').replace('ſ', 's')).strip()


def verify_base():
    manifest = json.loads((BASE/'manifest.json').read_text(encoding='utf8'))
    assert manifest['status'] == 'released' and manifest['version'] == BASE_VERSION
    for entry in manifest['files']:
        path = BASE/entry['path']
        if path.stat().st_size != entry['bytes'] or file_sha(path) != entry['sha256']:
            raise ValueError('Base release file changed: '+entry['path'])
    return manifest


def check_ledger(ledger):
    candidates = json.loads((OUT/'pilot_expansion_2026-11-05/search_candidates.json').read_text(encoding='utf8'))['candidates']
    seen = collections.Counter(i for d in ledger['candidate_dispositions'] for i in d['candidates'])
    missing = [i for i in range(len(candidates)) if seen[i] == 0]
    doubled = [i for i, n in seen.items() if n > 1]
    if missing or doubled or max(seen) >= len(candidates):
        raise ValueError(f'Ledger must decide every candidate exactly once: missing {missing}, doubled {doubled}')
    admitted_keys = {candidates[i]['key'] for d in ledger['candidate_dispositions'] if d['decision'] == 'admitted' for i in d['candidates']}
    admitted_keys |= {d['page_key'] for d in ledger['supplementary_dispositions'] if d['decision'] == 'admitted'}
    obs_keys = {o['page_key'] for o in ledger['observations']}
    if admitted_keys != obs_keys:
        raise ValueError(f'Admitted pages and observations disagree: {admitted_keys ^ obs_keys}')
    return len(candidates)


def revx_texts(keys):
    audit = {r['key']: r for r in pq.read_table(WORK/'page_audit.parquet', columns=['key', 'file', 'file_row']).to_pylist() if r['key'] in keys}
    locations = collections.defaultdict(dict)
    for key, r in audit.items():
        locations[r['file']][r['file_row']] = key
    raw = {}
    for name, lookup in locations.items():
        pf = pq.ParquetFile(WORK/'data'/name)
        offset = 0
        for n in range(pf.num_row_groups):
            count = pf.metadata.row_group(n).num_rows
            rows = [i for i in lookup if offset <= i < offset+count]
            if rows:
                table = pf.read_row_group(n, columns=['RevX_OCR_text'])
                for i in rows:
                    raw[lookup[i]] = table['RevX_OCR_text'][i-offset].as_py() or ''
            offset += count
    assert set(raw) == set(keys), set(keys) - set(raw)
    return raw


def main():
    if (RELEASE/'manifest.json').exists() and json.loads((RELEASE/'manifest.json').read_text())['status'] == 'released':
        raise SystemExit('Release '+VERSION+' is immutable. Make a new version for further changes.')
    ledger = json.loads(LEDGER_PATH.read_text(encoding='utf8'))
    assert ledger['base_release'] == BASE_VERSION and ledger['target_release'] == VERSION
    n_candidates = check_ledger(ledger)
    verify_base()
    print('Verified base release', BASE_VERSION, 'and ledger covering', n_candidates, 'candidates', flush=True)

    if RELEASE.exists():
        shutil.rmtree(RELEASE)  # Only an unreleased draft of this version.
    shutil.copytree(BASE, RELEASE, ignore=shutil.ignore_patterns('research.sqlite', 'manifest.json', 'validation.json', 'tables', 'views'))
    (RELEASE/'manifest.json').write_text(J({'status': 'draft', 'version': VERSION}), encoding='utf8')
    for folder in ['tables', 'views']:
        (RELEASE/folder).mkdir()
    src_db = sqlite3.connect((BASE/'research.sqlite').as_uri()+'?mode=ro', uri=True)
    db = sqlite3.connect(RELEASE/'research.sqlite')
    src_db.backup(db)
    src_db.close()
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')

    def insert(table, **values):
        db.execute(f'INSERT INTO {table} ({",".join(values)}) VALUES ({",".join("?" for _ in values)})', tuple(values.values()))

    def source(path, kind):
        path = Path(path)
        if not path.is_absolute():
            path = PROJECT/path
        relative = path.relative_to(PROJECT).as_posix()
        digest = file_sha(path)
        sid = 'source:'+sha(relative+'@'+digest)[:24]
        if db.execute('SELECT 1 FROM sources WHERE id=?', (sid,)).fetchone():
            return sid
        # Prefix with the version so a changed file never overwrites the base release's snapshot.
        target = f'sources/v{VERSION}__'+relative.replace('/', '__')
        shutil.copyfile(path, RELEASE/target)
        insert('sources', id=sid, path=target, sha256=digest, bytes=path.stat().st_size, kind=kind, url=None, verification='sha256_verified_at_build')
        return sid

    def obj(oid, kind, label):
        db.execute('INSERT OR IGNORE INTO objects VALUES (?,?,?)', (oid, kind, label))

    def annotation(aid, oid, kind, value, sid, pointer):
        insert('annotations', id=aid, object_id=oid, annotation_type=kind, value_json=J(value), run_id=RUN,
               source_id=sid, source_pointer=pointer, supersedes_id=None, recorded_date=DATE)
        return aid

    ledger_source = source(LEDGER_PATH, 'review_ledger')
    source(HERE/'migrate_v0_2_0.py', 'migration_code')
    source(HERE/'validate.py', 'validation_code')
    source(HERE/'README.md', 'documentation')
    source(WORK/'search_pilot_1797.py', 'retrieval_code')
    source(WORK/'scan_expansion_1797.py', 'scan_check_code')
    source(OUT/'pilot_expansion_2026-11-05/search_candidates.json', 'retrieval_candidates')
    crop_source = source(EVIDENCE/'crop_manifest.json', 'scan_crop_manifest')

    insert('runs', id=RUN, method='Review of the targeted 1797 retrieval, supplementary phrase sweeps and scan checks',
           parameters_json=J({'release': VERSION, 'pages_searched': 1587, 'candidates_reviewed': n_candidates,
                              'supplementary_patterns': sorted(ledger['retrieval']['supplementary_patterns']),
                              'reviewer': ledger['reviewer'], 'new_historical_findings': 'Observed publications only; no events adjudicated'}),
           source_id=ledger_source, recorded_date=DATE, reviewer_kind='ai_assistant', independent_review=0)

    keys = {o['page_key'] for o in ledger['observations']}
    raw = revx_texts(keys)
    observation_ids = {}
    for i, o in enumerate(ledger['observations']):
        key = o['page_key']
        page_version = db.execute('SELECT v.id FROM page_versions v JOIN pages p ON p.id=v.page_id WHERE p.legacy_page_key=?', (key,)).fetchone()[0]
        text = normalized(raw[key])
        start = text.find(o['excerpt_start'])
        if start < 0 or text.count(o['excerpt_start']) != 1:
            raise ValueError(f"{o['id']}: excerpt start must occur exactly once")
        end = text.find(o['excerpt_end'], start)
        if end < 0:
            raise ValueError(f"{o['id']}: excerpt end not found")
        excerpt = text[start:end+len(o['excerpt_end'])]
        excerpts = [excerpt]
        anchors = [{'status': 'unique_normalized_match' if text.count(excerpt) == 1 else 'ambiguous_match', 'start': start if text.count(excerpt) == 1 else None,
                    'end': start+len(excerpt) if text.count(excerpt) == 1 else None, 'matches': text.count(excerpt)}]
        locator = {'coordinate_system': 'Unicode character offsets in normalized RevX text', 'normalization_id': 'chain-search-v1',
                   'normalized_page_sha256': sha(text), 'segments': anchors}
        oid = f'obs:{NAMESPACE}:{o["id"]}'
        observation_ids[o['id']] = oid
        obj(oid, 'observation', o['id']+' · '+key.split('|')[1])
        insert('observations', id=oid, legacy_namespace=NAMESPACE, legacy_id=o['id'], page_version_id=page_version,
               transcription_field='RevX_OCR_text', excerpts_json=J(excerpts), excerpt_sha256=sha(J(excerpts)),
               normalization='Excerpt cut from RevX between ledger anchors; source spellings and OCR errors retained. Locator normalization: join whitespace hyphenation, long-s to s, collapse whitespace.',
               locator_json=J(locator), scan_review_status='scan_inspected_ai_assistant', scan_review_run_id=RUN,
               source_id=ledger_source, source_pointer=f'/observations/{i}')
        for crop in o['crops']:
            original = EVIDENCE/crop
            asset_path = 'assets/pilot_expansion_2026-11-05__evidence__'+crop
            shutil.copyfile(original, RELEASE/asset_path)
            insert('assets', id='asset:'+sha(oid+'|'+asset_path)[:24], object_id=oid, path=asset_path,
                   sha256=file_sha(original), kind='inspected_scan_crop', original_source_id=crop_source)
        annotation(f'review:{NAMESPACE}:{o["id"]}:1', oid, 'observation_review',
                   {'summary': o['summary'], 'note': o['note'], 'scan_findings': o['scan_findings'], 'independent_review': False},
                   ledger_source, f'/observations/{i}')

    for i, g in enumerate(ledger['new_groups']):
        gid = 'group:'+g['id']
        obj(gid, 'group', g['label'])
        insert('groups', id=gid, kind=g['kind'], label=g['label'], definition=g['definition'], admission_rule=g['admission_rule'], run_id=RUN)
    for i, h in enumerate(ledger['new_hierarchy']):
        aid = f'hierarchy:{h["parent"]}:{h["child"]}'
        annotation(aid, 'group:'+h['child'], 'parent_group', {'parent': 'group:'+h['parent'], 'meaning': 'Organizational containment; not historical causation'},
                   ledger_source, f'/new_hierarchy/{i}')
        insert('group_hierarchy', annotation_id=aid, parent_id='group:'+h['parent'], child_id='group:'+h['child'])
    for i, o in enumerate(ledger['observations']):
        oid = observation_ids[o['id']]
        for short in o['groups']:
            gid = 'group:'+short
            assert db.execute('SELECT 1 FROM groups WHERE id=?', (gid,)).fetchone(), gid
            aid = f'membership:{short}:{o["id"]}:1'
            annotation(aid, oid, 'membership:'+gid, {'decision': 'admitted', 'roles': o['roles'],
                       'basis': 'Reviewed 1797 expansion passage checked against its scan; observed publication, not an adjudicated historical event.'},
                       ledger_source, f'/observations/{i}')
            insert('memberships', annotation_id=aid, observation_id=oid, group_id=gid, decision='admitted', roles_json=J(o['roles']))

    old_release = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='release'").fetchone()[0])
    release_meta = dict(old_release, version=VERSION, date=DATE, previous_release=BASE_VERSION)
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    insert('metadata', key='migration_history', value_json=J([{'from': BASE_VERSION, 'to': VERSION, 'date': DATE, 'ledger': ledger['ledger_id'],
                                                                 'ledger_version': ledger['ledger_version'], 'run_id': RUN}]))
    dispositions = collections.Counter()
    for d in ledger['candidate_dispositions']:
        dispositions[d['decision']] += len(d['candidates'])
    insert('metadata', key='expansion_1797_dispositions', value_json=J({'candidate_pages': n_candidates, 'by_decision': dict(dispositions),
                                                                         'supplementary': [{k: d[k] for k in ('page_key', 'decision')} for d in ledger['supplementary_dispositions']],
                                                                         'ledger_source_id': ledger_source}))
    new_members = sum(len(o['groups']) for o in ledger['observations'])
    boyd = lambda gid: db.execute('SELECT COUNT(DISTINCT observation_id) FROM group_publications WHERE group_id=?', (gid,)).fetchone()[0]
    expected = {'observations': 24+len(ledger['observations']), 'claims': 15, 'relations': 22,
                'groups': 7+len(ledger['new_groups']), 'memberships': 16+new_members, 'group_hierarchy': 4+len(ledger['new_hierarchy']),
                'distinct_current_members': 9+len(ledger['observations']),
                'boyd_coverage_selections': 4+sum('boyd-bantry-coverage' in o['groups'] for o in ledger['observations']),
                'boyd_core_selections': 3+sum('boyd-core-report' in o['groups'] for o in ledger['observations'])}
    assert boyd('group:boyd-bantry-coverage') == expected['boyd_coverage_selections']
    insert('metadata', key='expected_counts', value_json=J(expected))
    db.commit()

    # Regenerate the Boyd/Bantry consumer projection: prototype records stay byte-for-byte equal.
    base_pulse = json.loads((BASE/'views/pulse_boyd.json').read_text(encoding='utf8'))
    prior = {r['observation_id']: r for r in base_pulse['observations']}
    records = []
    for r in db.execute("SELECT * FROM group_publications WHERE group_id='group:boyd-bantry-coverage' ORDER BY publication_date,newspaper_id"):
        if r['observation_id'] in prior:
            records.append(prior[r['observation_id']])
            continue
        asset = db.execute('SELECT path FROM assets WHERE object_id=? ORDER BY path', (r['observation_id'],)).fetchone()
        review = json.loads(db.execute("SELECT value_json FROM current_annotations WHERE object_id=? AND annotation_type='observation_review'", (r['observation_id'],)).fetchone()[0])
        records.append({'id': r['legacy_id'], 'observation_id': r['observation_id'], 'page_id': r['page_id'], 'node': r['lccn'],
                        'publication_date': r['publication_date'], 'page': r['page_number'], 'roles': json.loads(r['roles_json']), 'phase': None,
                        'excerpt': '\n\n'.join(json.loads(r['excerpts_json'])), 'source_url': r['pinned_scan_url'], 'scan_asset': asset['path'],
                        'note': review['note'], 'summary': review['summary']})
    pulse = dict(base_pulse, schema_version=VERSION, release_id='newspapers-v'+VERSION, observations=records)
    (RELEASE/'views/pulse_boyd.json').write_text(json.dumps(pulse, ensure_ascii=False, indent=2), encoding='utf8')

    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        with (RELEASE/'tables'/f'{table}.jsonl').open('w', encoding='utf8', newline='\n') as f:
            for row in db.execute(f'SELECT * FROM {table} ORDER BY 1'):
                values = dict(row)
                for k in list(values):
                    if k.endswith('_json') and values[k] is not None:
                        values[k[:-5]] = json.loads(values.pop(k))
                f.write(J(values)+'\n')
    db.close()
    shutil.copyfile(HERE/'schema.sql', RELEASE/'schemas/schema.sql')
    shutil.copyfile(HERE/'README.md', RELEASE/'README.md')
    shutil.copyfile(HERE/'examples.sql', RELEASE/'examples.sql')

    from validate import validate
    results = validate(RELEASE)
    (RELEASE/'validation.json').write_text(json.dumps(results, indent=2), encoding='utf8')
    files = [{'path': p.relative_to(RELEASE).as_posix(), 'bytes': p.stat().st_size, 'sha256': file_sha(p)}
             for p in sorted(RELEASE.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    manifest = {'version': VERSION, 'status': 'released', 'created_date': DATE, 'previous_release': BASE_VERSION,
                'dataset_revision': release_meta['revision'], 'build_command': 'python work/archive_data/migrate_v0_2_0.py',
                'counts': results['counts'], 'files': files, 'raw_archive_included': False, 'raw_archive_location': '../../../work/data/',
                'historical_findings_added': False, 'observed_publications_added': len(ledger['observations'])}
    (RELEASE/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': VERSION, 'path': 'v'+VERSION, 'manifest_sha256': file_sha(RELEASE/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(RELEASE), 'counts': results['counts'], 'checks': len(results['checks'])}, indent=2), flush=True)


if __name__ == '__main__':
    main()
