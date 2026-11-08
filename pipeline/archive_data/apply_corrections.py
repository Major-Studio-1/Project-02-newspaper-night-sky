"""Make a correction release: copy a frozen release and append superseding annotations from a ledger.

Usage (from the project root, Python 3.12):
    python work/archive_data/apply_corrections.py work/archive_data/ledgers/corrections_2026-11-06.json

The base release stays untouched. Old annotations remain in the database; the new rows
point to them with supersedes_id, so current_annotations shows only the corrected values.

A ledger may also carry "table_corrections" for text fields of plain tables that have no annotation history (only
those listed in TABLE_FIELDS). Each names the current value ("from") and the new one ("to"); the release changes the
field, and the metadata key table_corrections keeps every old value with its ledger and reason. With
"update_readme": true the release gets the current work/archive_data/README.md.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
FOUNDATION = PROJECT/'outputs/data_foundation'
J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()
TABLE_FIELDS = {'date_assertions': {'date_role'}}   # plain-table text fields a correction ledger may change


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main(ledger_path):
    ledger_path = Path(ledger_path).resolve()
    ledger = json.loads(ledger_path.read_text(encoding='utf8'))
    base, target = FOUNDATION/('v'+ledger['base_release']), FOUNDATION/('v'+ledger['target_release'])
    if (target/'manifest.json').exists() and json.loads((target/'manifest.json').read_text())['status'] == 'released':
        raise SystemExit('Release '+ledger['target_release']+' is immutable.')
    manifest = json.loads((base/'manifest.json').read_text(encoding='utf8'))
    assert manifest['status'] == 'released'
    for entry in manifest['files']:
        if file_sha(base/entry['path']) != entry['sha256']:
            raise ValueError('Base release file changed: '+entry['path'])

    if target.exists():
        shutil.rmtree(target)  # Only an unreleased draft.
    shutil.copytree(base, target, ignore=shutil.ignore_patterns('research.sqlite', 'manifest.json', 'validation.json', 'tables'))
    (target/'manifest.json').write_text(J({'status': 'draft', 'version': ledger['target_release']}), encoding='utf8')
    (target/'tables').mkdir()
    src = sqlite3.connect((base/'research.sqlite').as_uri()+'?mode=ro', uri=True)
    db = sqlite3.connect(target/'research.sqlite')
    src.backup(db)
    src.close()
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')

    relative = ledger_path.relative_to(PROJECT).as_posix()
    digest = file_sha(ledger_path)
    sid = 'source:'+sha(relative+'@'+digest)[:24]
    path = f'sources/v{ledger["target_release"]}__'+relative.replace('/', '__')
    shutil.copyfile(ledger_path, target/path)
    db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?)', (sid, path, digest, ledger_path.stat().st_size, 'correction_ledger', None, 'sha256_verified_at_build'))
    for code, kind in [(HERE/'apply_corrections.py', 'migration_code'), (HERE/'validate.py', 'validation_code')]:
        code_rel = code.relative_to(PROJECT).as_posix()
        code_digest = file_sha(code)
        code_sid = 'source:'+sha(code_rel+'@'+code_digest)[:24]
        if not db.execute('SELECT 1 FROM sources WHERE id=?', (code_sid,)).fetchone():
            code_path = f'sources/v{ledger["target_release"]}__'+code_rel.replace('/', '__')
            shutil.copyfile(code, target/code_path)
            db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?)', (code_sid, code_path, code_digest, code.stat().st_size, kind, None, 'sha256_verified_at_build'))
    run = 'run:'+ledger['ledger_id'].split(':', 1)[1]
    table_fixes = ledger.get('table_corrections', [])
    params = {'release': ledger['target_release'], 'corrections': len(ledger['corrections'])}
    if table_fixes:
        params['table_corrections'] = len(table_fixes)
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (run, 'Correction of recorded annotations', J(params),
                                                          sid, ledger['recorded_date'], 'ai_assistant', 0))
    for i, c in enumerate(ledger['corrections']):
        old = db.execute('SELECT * FROM current_annotations WHERE id=?', (c['supersedes'],)).fetchone()
        if old is None or old['object_id'] != c['object_id'] or old['annotation_type'] != c['annotation_type']:
            raise ValueError('Correction must supersede the current annotation of the same object and type: '+c['supersedes'])
        value = dict(c['value'], correction_reason=c['reason'])
        db.execute('INSERT INTO annotations VALUES (?,?,?,?,?,?,?,?,?)', (c['new_annotation_id'], c['object_id'], c['annotation_type'], J(value), run, sid,
                                                                         f'/corrections/{i}', c['supersedes'], ledger['recorded_date']))
    log = []
    for i, c in enumerate(table_fixes):
        if c['column'] not in TABLE_FIELDS.get(c['table'], ()):
            raise ValueError('Table corrections may change only '+json.dumps({k: sorted(v) for k, v in TABLE_FIELDS.items()}))
        row = db.execute(f"SELECT {c['column']} FROM {c['table']} WHERE id=?", (c['id'],)).fetchone()
        if row is None or row[0] != c['from']:
            raise ValueError('A table correction must start from the current value: '+c['id'])
        db.execute(f"UPDATE {c['table']} SET {c['column']}=? WHERE id=?", (c['to'], c['id']))
        log.append({'release': ledger['target_release'], 'ledger': ledger['ledger_id'], 'pointer': f'/table_corrections/{i}', 'run_id': run,
                    **{k: c[k] for k in ('table', 'id', 'column', 'from', 'to', 'reason')}})
    if log:
        old = db.execute("SELECT value_json FROM metadata WHERE key='table_corrections'").fetchone()
        db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', ('table_corrections', J((json.loads(old[0]) if old else []) + log)))
    release_meta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='release'").fetchone()[0])
    release_meta.update(version=ledger['target_release'], date=ledger['recorded_date'], previous_release=ledger['base_release'])
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    history = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='migration_history'").fetchone()[0])
    history.append({'from': ledger['base_release'], 'to': ledger['target_release'], 'date': ledger['recorded_date'], 'ledger': ledger['ledger_id'], 'ledger_version': ledger['ledger_version'], 'run_id': run})
    db.execute("UPDATE metadata SET value_json=? WHERE key='migration_history'", (J(history),))
    db.commit()

    view = json.loads((target/'views/pulse_boyd.json').read_text(encoding='utf8'))
    view.update(schema_version=ledger['target_release'], release_id='newspapers-v'+ledger['target_release'])
    for record in view['observations']:
        if record['id'].startswith('E'):
            review = json.loads(db.execute("SELECT value_json FROM current_annotations WHERE object_id=? AND annotation_type='observation_review'", (record['observation_id'],)).fetchone()[0])
            record.update(summary=review['summary'], note=review['note'])
    (target/'views/pulse_boyd.json').write_text(json.dumps(view, ensure_ascii=False, indent=2), encoding='utf8')
    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        with (target/'tables'/f'{table}.jsonl').open('w', encoding='utf8', newline='\n') as f:
            for row in db.execute(f'SELECT * FROM {table} ORDER BY 1'):
                values = dict(row)
                for k in list(values):
                    if k.endswith('_json') and values[k] is not None:
                        values[k[:-5]] = json.loads(values.pop(k))
                f.write(J(values)+'\n')
    db.close()
    if ledger.get('update_readme'):
        shutil.copyfile(HERE/'README.md', target/'README.md')

    sys.path.insert(0, str(HERE))
    from validate import validate
    results = validate(target)
    (target/'validation.json').write_text(json.dumps(results, indent=2), encoding='utf8')
    files = [{'path': p.relative_to(target).as_posix(), 'bytes': p.stat().st_size, 'sha256': file_sha(p)}
             for p in sorted(target.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    out = dict(manifest, version=ledger['target_release'], status='released', created_date=ledger['recorded_date'], previous_release=ledger['base_release'],
               build_command='python work/archive_data/apply_corrections.py '+relative, counts=results['counts'], files=files,
               corrections_applied=len(ledger['corrections']), **({'table_corrections_applied': len(table_fixes)} if table_fixes else {}))
    (target/'manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': ledger['target_release'], 'path': 'v'+ledger['target_release'], 'manifest_sha256': file_sha(target/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(target), 'checks': len(results['checks']), 'corrections': len(ledger['corrections'])}), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
