"""Make a release that adds the all-years text-reuse layer as derived tables.

The layer is automatic: matched passages and the families built from them, NOT reviewed.
It is stored apart from the reviewed tables (observations, groups, memberships), as
derived/reuse_*.parquet with its own run, so nothing reviewed is mixed with it.

Usage (project root, Python 3.12):
    python work/archive_data/add_reuse_layer.py 0.4.0 0.5.0
Inputs: work/reuse_all/matches_*.json, outputs/story_discovery_all/families.json.
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

RUN = 'run:reuse-all-v1'
J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()
page_id = lambda key: 'page:'+key.replace('|', ':')


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

    code = source('work/reuse_all.py', 'analysis_code')
    source('work/reuse_families_all.py', 'analysis_code')
    source('work/archive_data/add_reuse_layer.py', 'migration_code')
    source('work/archive_data/validate.py', 'validation_code')
    summary_src = source('outputs/story_discovery_all/summary.json', 'model_output_summary')

    # Matches (all years, broad profile, with main/strict flags). Texts stay in the pinned shards.
    metas, cols = [], {k: [] for k in ['a_page_id', 'b_page_id', 'a_date', 'b_date', 'a_span_start', 'a_span_end', 'b_span_start', 'b_span_end',
                                       'matched_words', 'similarity', 'seeds', 'main', 'strict']}
    for f in sorted((WORK/'reuse_all').glob('matches_*.json')):
        d = json.loads(f.read_text(encoding='utf8')); metas.append(d['meta'])
        for m in d['matches']:
            cols['a_page_id'].append(page_id(m['a'])); cols['b_page_id'].append(page_id(m['b']))
            cols['a_date'].append(m['a_date']); cols['b_date'].append(m['b_date'])
            cols['a_span_start'].append(m['a_span'][0]); cols['a_span_end'].append(m['a_span'][1])
            cols['b_span_start'].append(m['b_span'][0]); cols['b_span_end'].append(m['b_span'][1])
            for k in ['matched_words', 'similarity', 'seeds', 'main', 'strict']:
                cols[k].append(m[k])
    matches = pa.table(cols).append_column('run_id', pa.array([RUN]*len(cols['seeds'])))
    pq.write_table(matches, release/'derived/reuse_matches.parquet', compression='zstd')

    fam = json.loads((PROJECT/'outputs/story_discovery_all/families.json').read_text(encoding='utf8'))
    f_rows, a_rows = [], []
    for f in fam['families']:
        f_rows.append({'family_id': f['family_id'], 'first_date': f['first'], 'last_date': f['last'], 'newspapers': f['newspapers'], 'pages': f['pages'],
                       'appearances': len(f['appearances']), 'label': f['label'], 'keywords_json': json.dumps(f['keywords']),
                       'long_running': f['long_running'], 'run_id': RUN})
        for i, a in enumerate(f['appearances']):
            a_rows.append({'family_id': f['family_id'], 'seq': i, 'page_id': page_id(a['key']), 'publication_date': a['date'], 'lccn': a['lccn'],
                           'page_number': int(a['page']), 'span_start': a['span'][0], 'span_end': a['span'][1], 'transcription': a['source'], 'excerpt': a['excerpt']})
    pq.write_table(pa.Table.from_pylist(f_rows), release/'derived/reuse_families.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist(a_rows), release/'derived/reuse_family_appearances.parquet', compression='zstd')

    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN, 'Automatic text reuse across all years and families of matched passages',
               J({'years': [1770, 1810], 'shingle_words': 5, 'winnow_window': 8, 'min_shared_fingerprints': 6, 'max_days_apart': 120,
                  'different_series_only': True, 'common_fingerprint_rule': 'ignored if on more than 40 pages or 80 times in a year window',
                  'profiles': {'broad': [60, 0.6], 'main': [80, 0.7], 'strict': [120, 0.8]}, 'families_from': 'main profile, overlapping spans on a page',
                  'checked_against_scans': False}), code, date, 'automated', 0))
    layer = {'status': 'automatic; not reviewed; not checked against scans', 'run_id': RUN, 'matches_broad': len(cols['seeds']),
             'matches_main': sum(cols['main']), 'families': len(f_rows), 'family_appearances': len(a_rows),
             'families_by_newspapers': fam['summary']['families_by_newspapers'], 'per_year': metas, 'summary_source_id': summary_src}
    db.execute('INSERT INTO metadata VALUES (?,?)', ('reuse_layer', J(layer)))
    release_meta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='release'").fetchone()[0])
    release_meta.update(version=version, date=date, previous_release=base_version)
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    history = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='migration_history'").fetchone()[0])
    history.append({'from': base_version, 'to': version, 'date': date, 'ledger': None, 'run_id': RUN, 'note': 'automatic reuse layer added as derived tables'})
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
               build_command=f'python work/archive_data/add_reuse_layer.py {base_version} {version}', counts=results['counts'], files=files,
               reuse_layer={k: layer[k] for k in ('matches_main', 'families', 'family_appearances')})
    (release/'manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': version, 'path': 'v'+version, 'manifest_sha256': file_sha(release/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(release), 'checks': len(results['checks']), 'reuse_layer': out['reuse_layer']}), flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
