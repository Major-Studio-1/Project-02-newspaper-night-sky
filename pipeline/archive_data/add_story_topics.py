"""Make a release that adds automatic topics for stories (matched stories and reviewed groups).

Topics come from work/story_topics_all.py: the project's frozen 24-topic model (work/topic_model.joblib) applied to
each printed excerpt, summed per story. Automatic and provisional; stored as derived/story_topics.parquet with
their own run. Nothing else changes.

Usage (project root, Python 3.12):
    python work/archive_data/add_story_topics.py 0.5.1 0.5.2
Input: outputs/story_discovery_all/story_topics.json
"""
from pathlib import Path
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
sys.path.insert(0, str(WORK/'python_packages'))
import pyarrow as pa
import pyarrow.parquet as pq

RUN = 'run:story-topics-v1'
J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


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

    code = source('work/story_topics_all.py', 'analysis_code')
    source('work/archive_data/add_story_topics.py', 'migration_code')
    source('work/archive_data/validate.py', 'validation_code')

    data = json.loads((PROJECT/'outputs/story_discovery_all/story_topics.json').read_text(encoding='utf8'))
    families = {f['family_id'] for f in pq.read_table(release/'derived/reuse_families.parquet', columns=['family_id']).to_pylist()}
    groups = {r[0] for r in db.execute('SELECT id FROM groups')}
    matched = {k for k, v in data['stories'].items() if v['kind'] == 'matched'}
    assert matched == families, 'Topics must cover exactly the released matched stories'
    assert {k for k, v in data['stories'].items() if v['kind'] == 'reviewed'} <= groups, 'Reviewed topics must name released groups'
    tid = [t['id'] for t in sorted(data['topics'], key=lambda t: t['index'])]
    rows = [{'story_id': sid, 'kind': s['kind'], 'top_topic': tid[s['top']], 'top_share': s['top_share'], 'second_topic': tid[s['second']],
             'printings': s['printings'], 'printing_agreement': s['agreement'], 'no_signal': s['no_signal'],
             'weights_json': json.dumps(s['weights']), 'run_id': RUN} for sid, s in sorted(data['stories'].items())]
    pq.write_table(pa.Table.from_pylist(rows), release/'derived/story_topics.parquet', compression='zstd')

    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN, 'Frozen 24-topic model applied to the printed excerpts of each story',
               J({'model_file': data['model_file'], 'model_sha256': data['model_sha256'], 'story_weights': 'sum over printings, normalised',
                  'excerpt_words_max': 70, 'labels': 'model top words; provisional', 'checked_against_scans': False}), code, date, 'automated', 0))
    counts = {}
    for r in rows:
        counts[r['kind']] = counts.get(r['kind'], 0) + 1
    db.execute('INSERT INTO metadata VALUES (?,?)', ('story_topics', J({'status': 'automatic; provisional topic labels', 'run_id': RUN, 'stories': counts,
               'mean_agreement_multi_printing': data['mean_agreement_multi_printing'],
               'topics': [{'id': t['id'], 'terms': t['terms'], 'display_order': t['display_order']} for t in sorted(data['topics'], key=lambda t: t['index'])]})))
    release_meta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='release'").fetchone()[0])
    release_meta.update(version=version, date=date, previous_release=base_version)
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    history = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='migration_history'").fetchone()[0])
    history.append({'from': base_version, 'to': version, 'date': date, 'ledger': None, 'run_id': RUN, 'note': 'automatic story topics added as a derived table'})
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
    sys.path.insert(0, str(HERE))
    from validate import validate
    results = validate(release)
    (release/'validation.json').write_text(json.dumps(results, indent=2), encoding='utf8')
    files = [{'path': p.relative_to(release).as_posix(), 'bytes': p.stat().st_size, 'sha256': file_sha(p)}
             for p in sorted(release.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    out = dict(manifest, version=version, status='released', created_date=date, previous_release=base_version,
               build_command=f'python work/archive_data/add_story_topics.py {base_version} {version}', counts=results['counts'], files=files,
               story_topics={'stories': counts})
    (release/'manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': version, 'path': 'v'+version, 'manifest_sha256': file_sha(release/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(release), 'checks': len(results['checks']), 'story_topics': out['story_topics']}), flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
