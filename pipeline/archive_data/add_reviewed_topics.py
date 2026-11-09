"""Make a release that adds topic rows for reviewed groups that have none yet (such as the 1776 stories of v0.7.0).

The topics come from the project's frozen 24-topic model (the model file and hash recorded in run:story-topics-v1),
applied as in work/story_topics_all.py: each printing's excerpt is scored, and a group's topic weights are the sum over
its printings, normalised. The model's solver stops on a whole batch, so a weight can move in the fourth decimal with
other company in the batch. So the reviewed groups that already have rows are scored together, as they were, and the
script stops unless that reproduces every one of them exactly; then the groups without rows are scored together and
added. Existing rows are kept as they are; the new rows carry their own run. Automatic and provisional, like the rest.

Usage (project root, Python 3.12):
    python work/archive_data/add_reviewed_topics.py 0.7.0 0.7.1
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
sys.path.insert(0, str(WORK/'python_packages'))
import joblib
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

BASE_RUN = 'run:story-topics-v1'
RUN = 'run:story-topics-reviewed-v1'
J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def score(texts, ids, vec, nmf):
    """Topic weights of the given stories in one batch, as work/story_topics_all.py computes them."""
    flat, owner = [], []
    for i, sid in enumerate(ids):
        for t in texts[sid]:
            flat.append(t); owner.append(i)
    owner = np.array(owner)
    W = nmf.transform(vec.transform(flat))
    sums = np.zeros((len(ids), nmf.n_components))
    np.add.at(sums, owner, W)
    tops = W.argmax(axis=1)
    out = {}
    for i, sid in enumerate(ids):
        w = sums[i]; total = w.sum()
        share = w/total if total > 0 else np.zeros_like(w)
        order = np.argsort(-share)
        mine = tops[owner == i]
        out[sid] = {'top': int(order[0]), 'top_share': round(float(share[order[0]]), 3), 'second': int(order[1]), 'printings': int(len(mine)),
                    'agreement': round(float((mine == order[0]).mean()), 3) if total > 0 else 0.0, 'no_signal': bool(total == 0),
                    'weights': [round(float(x), 4) for x in share]}
    return out


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

    code = source('work/archive_data/add_reviewed_topics.py', 'analysis_code')
    source('work/archive_data/validate.py', 'validation_code')

    # The same frozen model as the layer's first run.
    params = json.loads(db.execute('SELECT parameters_json FROM runs WHERE id=?', (BASE_RUN,)).fetchone()[0])
    model_path = PROJECT/params['model_file']
    assert file_sha(model_path) == params['model_sha256'], 'The topic model is not the one the story topics were made with'
    tm = joblib.load(model_path)
    vec, nmf = tm['vectorizer'], tm['model']
    meta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='story_topics'").fetchone()[0])
    tid = [t['id'] for t in meta['topics']]   # stored in model order
    assert len(tid) == nmf.n_components

    texts = collections.defaultdict(list)   # reviewed group -> its printed excerpts
    for gid, ex in db.execute('SELECT group_id, excerpts_json FROM group_publications ORDER BY group_id, publication_date'):
        texts[gid].append(' '.join(json.loads(ex)))
    table = pq.read_table(release/'derived/story_topics.parquet')
    rows = table.to_pylist()
    have = {r['story_id']: r for r in rows}
    reviewed = sorted(texts)
    kept, new = [sid for sid in reviewed if sid in have], [sid for sid in reviewed if sid not in have]
    if not new:
        raise SystemExit('Every reviewed group already has a topic row.')

    def as_row(sid, s, run):
        return {'story_id': sid, 'kind': 'reviewed', 'top_topic': tid[s['top']], 'top_share': s['top_share'], 'second_topic': tid[s['second']],
                'printings': s['printings'], 'printing_agreement': s['agreement'], 'no_signal': s['no_signal'],
                'weights_json': json.dumps(s['weights']), 'run_id': run}

    again = score(texts, kept, vec, nmf)
    for sid in kept:
        if as_row(sid, again[sid], have[sid]['run_id']) != have[sid]:
            raise SystemExit('Scoring the reviewed groups that have rows does not reproduce the topic row of '+sid)
    got = score(texts, new, vec, nmf)
    added = [as_row(sid, got[sid], RUN) for sid in new]
    pq.write_table(pa.Table.from_pylist(sorted(rows+added, key=lambda r: r['story_id']), schema=table.schema),
                   release/'derived/story_topics.parquet', compression='zstd')

    agree = [r['printing_agreement'] for r in added if r['printings'] >= 2 and not r['no_signal']]
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN, 'Frozen 24-topic model applied to the printed excerpts of reviewed groups added after run:story-topics-v1',
               J({**params, 'batches': 'the reviewed groups that had rows, together (reproduced exactly); then the added groups, together',
                  'groups_added': len(added), 'reproduced_rows': len(kept),
                  'mean_agreement_multi_printing': round(float(np.mean(agree)), 3) if agree else None}), code, date, 'automated', 0))
    counts = collections.Counter(r['kind'] for r in rows+added)
    meta.update(stories=dict(sorted(counts.items())), runs=[BASE_RUN, RUN])
    db.execute("UPDATE metadata SET value_json=? WHERE key='story_topics'", (J(meta),))
    release_meta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='release'").fetchone()[0])
    release_meta.update(version=version, date=date, previous_release=base_version)
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    history = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='migration_history'").fetchone()[0])
    history.append({'from': base_version, 'to': version, 'date': date, 'ledger': None, 'run_id': RUN,
                    'note': f'automatic topic rows added for {len(added)} reviewed groups that had none'})
    db.execute("UPDATE metadata SET value_json=? WHERE key='migration_history'", (J(history),))
    db.commit()

    view = json.loads((release/'views/pulse_boyd.json').read_text(encoding='utf8'))
    view.update(schema_version=version, release_id='newspapers-v'+version)
    (release/'views/pulse_boyd.json').write_text(json.dumps(view, ensure_ascii=False, indent=2), encoding='utf8')
    for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        with (release/'tables'/f'{name}.jsonl').open('w', encoding='utf8', newline='\n') as f:
            for row in db.execute(f'SELECT * FROM {name} ORDER BY 1'):
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
               build_command=f'python work/archive_data/add_reviewed_topics.py {base_version} {version}', counts=results['counts'], files=files,
               observed_publications_added=0, story_topics={'stories': dict(sorted(counts.items())), 'added': len(added)})
    (release/'manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': version, 'path': 'v'+version, 'manifest_sha256': file_sha(release/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(release), 'checks': len(results['checks']), 'story_topics': out['story_topics'],
                      'added': {r['story_id']: (r['top_topic'], r['top_share'], r['second_topic']) for r in added}}, indent=1), flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
