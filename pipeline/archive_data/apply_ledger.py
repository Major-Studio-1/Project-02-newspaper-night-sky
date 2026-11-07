"""Make a new release by applying a reviewed expansion ledger to the previous release.

Generic form of migrate_v0_2_0.py. The ledger names its base and target versions, its
observation namespace and the folder holding the scan crops. Run from the project root
with Python 3.12:

    python work/archive_data/apply_ledger.py work/archive_data/ledgers/<ledger>.json

The base release is hash-checked and left untouched. Every new row cites the ledger.
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
FOUNDATION = PROJECT/'outputs/data_foundation'
sys.path.insert(0, str(WORK/'python_packages'))
import pyarrow.parquet as pq

J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()
REQUIRED = ('id', 'page_key', 'excerpt_start', 'excerpt_end', 'crops', 'roles', 'groups', 'summary', 'note', 'scan_findings')


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def normalized(text):
    # Same locator normalization as every earlier release.
    return re.sub(r'\s+', ' ', re.sub(r'(?<=\w)-\s+(?=\w)', '', text or '').replace('ſ', 's')).strip()


def page_texts(keys, field='RevX_OCR_text'):
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
                table = pf.read_row_group(n, columns=[field])
                for i in rows:
                    raw[lookup[i]] = table[field][i-offset].as_py() or ''
            offset += count
    missing = set(keys) - set(raw)
    if missing:
        raise ValueError(f'Pages not found in the audit: {sorted(missing)}')
    return raw


def main(ledger_path):
    ledger_path = Path(ledger_path).resolve()
    ledger = json.loads(ledger_path.read_text(encoding='utf8'))
    base, release = FOUNDATION/('v'+ledger['base_release']), FOUNDATION/('v'+ledger['target_release'])
    version, date, namespace = ledger['target_release'], ledger['recorded_date'], ledger['namespace']
    evidence = PROJECT/ledger['evidence_dir']
    run = 'run:'+ledger['ledger_id'].split(':', 1)[1]
    if (release/'manifest.json').exists() and json.loads((release/'manifest.json').read_text())['status'] == 'released':
        raise SystemExit('Release '+version+' is immutable.')

    # Ledger completeness checks before touching anything.
    ids = [o['id'] for o in ledger['observations']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate observation ids in ledger')
    group_ids = {g['id'] for g in ledger['new_groups']}
    for o in ledger['observations']:
        missing = [k for k in REQUIRED if k not in o]
        if missing:
            raise ValueError(f"{o.get('id')}: missing {missing}")
        for crop in o['crops']:
            if not (evidence/crop).is_file():
                raise ValueError(f"{o['id']}: missing scan crop {crop}")
    for g in ledger['new_groups']:
        if not any(g['id'] in o['groups'] for o in ledger['observations']) and not any(a['group'] == g['id'] for a in ledger.get('added_memberships', [])):
            raise ValueError('New group has no admitted passage: '+g['id'])

    manifest = json.loads((base/'manifest.json').read_text(encoding='utf8'))
    assert manifest['status'] == 'released' and manifest['version'] == ledger['base_release']
    for entry in manifest['files']:
        path = base/entry['path']
        if path.stat().st_size != entry['bytes'] or file_sha(path) != entry['sha256']:
            raise ValueError('Base release file changed: '+entry['path'])
    print('Verified base release', ledger['base_release'], flush=True)

    if release.exists():
        shutil.rmtree(release)  # Only an unreleased draft of this version.
    shutil.copytree(base, release, ignore=shutil.ignore_patterns('research.sqlite', 'manifest.json', 'validation.json', 'tables'))
    (release/'manifest.json').write_text(J({'status': 'draft', 'version': version}), encoding='utf8')
    (release/'tables').mkdir()
    src = sqlite3.connect((base/'research.sqlite').as_uri()+'?mode=ro', uri=True)
    db = sqlite3.connect(release/'research.sqlite')
    src.backup(db)
    src.close()
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
        target = f'sources/v{version}__'+relative.replace('/', '__')
        shutil.copyfile(path, release/target)
        insert('sources', id=sid, path=target, sha256=digest, bytes=path.stat().st_size, kind=kind, url=None, verification='sha256_verified_at_build')
        return sid

    def obj(oid, kind, label):
        db.execute('INSERT OR IGNORE INTO objects VALUES (?,?,?)', (oid, kind, label))

    def annotation(aid, oid, kind, value, sid, pointer):
        insert('annotations', id=aid, object_id=oid, annotation_type=kind, value_json=J(value), run_id=run,
               source_id=sid, source_pointer=pointer, supersedes_id=None, recorded_date=date)

    ledger_source = source(ledger_path, 'review_ledger')
    source(HERE/'apply_ledger.py', 'migration_code')
    source(HERE/'validate.py', 'validation_code')
    source(HERE/'README.md', 'documentation')
    for path, kind in ledger.get('supporting_files', {}).items():
        source(path, kind)
    crop_source = source(evidence/'crop_manifest.json', 'scan_crop_manifest')
    insert('runs', id=run, method=ledger['method'], parameters_json=J({'release': version, 'reviewer': ledger['reviewer'],
           'observations': len(ids), 'new_groups': sorted(group_ids)}), source_id=ledger_source, recorded_date=date,
           reviewer_kind='ai_assistant', independent_review=0)

    # Excerpts come from RevX unless an observation names another transcription (e.g. RevX empty).
    fields = {o.get('transcription_field', 'RevX_OCR_text') for o in ledger['observations']}
    raw = {f: page_texts({o['page_key'] for o in ledger['observations'] if o.get('transcription_field', 'RevX_OCR_text') == f}, f) for f in fields}
    for i, o in enumerate(ledger['observations']):
        key = o['page_key']
        field = o.get('transcription_field', 'RevX_OCR_text')
        page_version = db.execute('SELECT v.id FROM page_versions v JOIN pages p ON p.id=v.page_id WHERE p.legacy_page_key=?', (key,)).fetchone()[0]
        text = normalized(raw[field][key])
        if text.count(o['excerpt_start']) != 1:
            raise ValueError(f"{o['id']}: excerpt start occurs {text.count(o['excerpt_start'])} times, need exactly 1")
        start = text.find(o['excerpt_start'])
        end = text.find(o['excerpt_end'], start)
        if end < 0:
            raise ValueError(f"{o['id']}: excerpt end not found after start")
        excerpt = text[start:end+len(o['excerpt_end'])]
        unique = text.count(excerpt) == 1
        locator = {'coordinate_system': f'Unicode character offsets in normalized {field} text', 'normalization_id': 'chain-search-v1',
                   'normalized_page_sha256': sha(text), 'segments': [{'status': 'unique_normalized_match' if unique else 'ambiguous_match',
                   'start': start if unique else None, 'end': start+len(excerpt) if unique else None, 'matches': text.count(excerpt)}]}
        oid = f'obs:{namespace}:{o["id"]}'
        obj(oid, 'observation', o['id']+' · '+key.split('|')[1])
        insert('observations', id=oid, legacy_namespace=namespace, legacy_id=o['id'], page_version_id=page_version,
               transcription_field=field, excerpts_json=J([excerpt]), excerpt_sha256=sha(J([excerpt])),
               normalization=f'Excerpt cut from {field} between ledger anchors; source spellings and OCR errors retained. Locator normalization: join whitespace hyphenation, long-s to s, collapse whitespace.',
               locator_json=J(locator), scan_review_status='scan_inspected_ai_assistant', scan_review_run_id=run,
               source_id=ledger_source, source_pointer=f'/observations/{i}')
        for crop in o['crops']:
            asset_path = 'assets/'+ledger['evidence_dir'].split('outputs/', 1)[-1].replace('/', '__')+'__'+crop
            shutil.copyfile(evidence/crop, release/asset_path)
            insert('assets', id='asset:'+sha(oid+'|'+asset_path)[:24], object_id=oid, path=asset_path,
                   sha256=file_sha(evidence/crop), kind='inspected_scan_crop', original_source_id=crop_source)
        review = {k: o[k] for k in ('summary', 'note', 'scan_findings')}
        review['independent_review'] = False
        if o.get('family'):
            review['family'] = o['family']
        annotation(f'review:{namespace}:{o["id"]}:1', oid, 'observation_review', review, ledger_source, f'/observations/{i}')

    for g in ledger['new_groups']:
        gid = 'group:'+g['id']
        obj(gid, 'group', g['label'])
        insert('groups', id=gid, kind=g['kind'], label=g['label'], definition=g['definition'], admission_rule=g['admission_rule'], run_id=run)
    for i, h in enumerate(ledger.get('new_hierarchy', [])):
        aid = f'hierarchy:{h["parent"]}:{h["child"]}'
        annotation(aid, 'group:'+h['child'], 'parent_group', {'parent': 'group:'+h['parent'], 'meaning': 'Organizational containment; not historical causation'},
                   ledger_source, f'/new_hierarchy/{i}')
        insert('group_hierarchy', annotation_id=aid, parent_id='group:'+h['parent'], child_id='group:'+h['child'])
    for i, o in enumerate(ledger['observations']):
        oid = f'obs:{namespace}:{o["id"]}'
        for short in o['groups']:
            gid = 'group:'+short
            if not db.execute('SELECT 1 FROM groups WHERE id=?', (gid,)).fetchone():
                raise ValueError(f"{o['id']}: unknown group {gid}")
            aid = f'membership:{short}:{o["id"]}:1'
            annotation(aid, oid, 'membership:'+gid, {'decision': 'admitted', 'roles': o['roles'],
                       'basis': 'Reviewed passage checked against its scan; observed publication, not an adjudicated historical event.'},
                       ledger_source, f'/observations/{i}')
            insert('memberships', annotation_id=aid, observation_id=oid, group_id=gid, decision='admitted', roles_json=J(o['roles']))

    # Passages admitted in earlier releases that also join a group from this ledger (e.g. a new parent story).
    for i, a in enumerate(ledger.get('added_memberships', [])):
        oid = a['observation'] if a['observation'].startswith('obs:') else f'obs:{namespace}:{a["observation"]}'
        if not db.execute('SELECT 1 FROM observations WHERE id=?', (oid,)).fetchone():
            raise ValueError('Unknown observation in added_memberships: '+a['observation'])
        gid = 'group:'+a['group']
        legacy = oid.rsplit(':', 1)[1]
        aid = f'membership:{a["group"]}:{legacy}:1'
        annotation(aid, oid, 'membership:'+gid, {'decision': 'admitted', 'roles': a['roles'],
                   'basis': a.get('basis', 'Already-admitted passage joined to a group from this ledger.')}, ledger_source, f'/added_memberships/{i}')
        insert('memberships', annotation_id=aid, observation_id=oid, group_id=gid, decision='admitted', roles_json=J(a['roles']))

    # Typed links between passages (e.g. two items printed side by side). Endpoints are existing
    # observation ids or this ledger's ids; each link cites both passages as its evidence.
    def resolve(ref):
        oid = ref if ref.startswith('obs:') else f'obs:{namespace}:{ref}'
        if not db.execute('SELECT 1 FROM observations WHERE id=?', (oid,)).fetchone():
            raise ValueError('Relation endpoint is not an observation: '+ref)
        return oid
    for i, r in enumerate(ledger.get('new_relations', [])):
        rid = 'relation:'+r['id']
        subject, target = resolve(r['subject']), resolve(r['object'])
        obj(rid, 'relation', r['predicate'])
        aid = f'review:{rid}:1'
        annotation(aid, rid, 'relation_review', {'note': r['note'], 'historical_causality_established': False, 'independent_review': False},
                   ledger_source, f'/new_relations/{i}')
        insert('relations', id=rid, subject_id=subject, predicate=r['predicate'], object_id=target, directed=int(r['directed']),
               evidence_level=r['evidence_level'], imported_review_annotation_id=aid)
        for oid in (subject, target):
            insert('relation_evidence', relation_id=rid, evidence_object_id=oid, locator='Printed selection named in the ledger')

    meta = lambda key: json.loads(db.execute('SELECT value_json FROM metadata WHERE key=?', (key,)).fetchone()[0])
    release_meta = dict(meta('release'), version=version, date=date, previous_release=ledger['base_release'])
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    history = meta('migration_history') + [{'from': ledger['base_release'], 'to': version, 'date': date, 'ledger': ledger['ledger_id'],
                                             'ledger_version': ledger['ledger_version'], 'run_id': run}]
    db.execute("UPDATE metadata SET value_json=? WHERE key='migration_history'", (J(history),))
    if 'dispositions_summary' in ledger:
        insert('metadata', key=ledger['ledger_id'].split(':', 1)[1]+'_dispositions', value_json=J(ledger['dispositions_summary']))
    expected = meta('expected_counts')
    n_members = sum(len(o['groups']) for o in ledger['observations']) + len(ledger.get('added_memberships', []))
    expected.update(observations=expected['observations']+len(ids), groups=expected['groups']+len(ledger['new_groups']),
                    memberships=expected['memberships']+n_members, group_hierarchy=expected['group_hierarchy']+len(ledger.get('new_hierarchy', [])),
                    relations=expected['relations']+len(ledger.get('new_relations', [])),
                    distinct_current_members=expected['distinct_current_members']+sum(1 for o in ledger['observations'] if o['groups']),
                    boyd_coverage_selections=expected['boyd_coverage_selections']+sum('boyd-bantry-coverage' in o['groups'] for o in ledger['observations']),
                    boyd_core_selections=expected['boyd_core_selections']+sum('boyd-core-report' in o['groups'] for o in ledger['observations']))
    db.execute("UPDATE metadata SET value_json=? WHERE key='expected_counts'", (J(expected),))
    db.commit()

    # Boyd/Bantry consumer view: unchanged records kept as they are; schema version follows the release.
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
    shutil.copyfile(HERE/'schema.sql', release/'schemas/schema.sql')
    shutil.copyfile(HERE/'README.md', release/'README.md')
    shutil.copyfile(HERE/'examples.sql', release/'examples.sql')

    sys.path.insert(0, str(HERE))
    from validate import validate
    results = validate(release)
    (release/'validation.json').write_text(json.dumps(results, indent=2), encoding='utf8')
    files = [{'path': p.relative_to(release).as_posix(), 'bytes': p.stat().st_size, 'sha256': file_sha(p)}
             for p in sorted(release.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    out = {'version': version, 'status': 'released', 'created_date': date, 'previous_release': ledger['base_release'],
           'dataset_revision': release_meta['revision'], 'build_command': 'python work/archive_data/apply_ledger.py '+ledger_path.relative_to(PROJECT).as_posix(),
           'counts': results['counts'], 'files': files, 'raw_archive_included': False, 'raw_archive_location': '../../../work/data/',
           'historical_findings_added': False, 'observed_publications_added': len(ids)}
    (release/'manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': version, 'path': 'v'+version, 'manifest_sha256': file_sha(release/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(release), 'counts': results['counts'], 'checks': len(results['checks'])}, indent=2), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
