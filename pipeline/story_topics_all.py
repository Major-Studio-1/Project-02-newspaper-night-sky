"""Topics for stories: the project's frozen 24-topic model applied to each printed excerpt of a story.

For every matched story (reuse family) and every reviewed group, each printing's excerpt is scored with the frozen
model in work/topic_model.joblib (TF-IDF + NMF, 24 components). A story's topic weights are the sum over its
printings, normalised. Also recorded: how many of its printings have the same top topic (agreement).
Topics get a display order in which similar topics sit next to each other (cosine similarity of the NMF components).

Automatic and provisional: the topic labels are the model's top words, not reviewed names, and three topics were
unstable in the original sensitivity checks. Excerpts are up to 70 words, shorter than the 220-word passages the
model was trained on; agreement between printings of the same story is the check on that (0.76 on a sample).

Usage (project root, Python 3.12):  python work/story_topics_all.py  -> outputs/story_discovery_all/story_topics.json
"""
from pathlib import Path
import collections
import hashlib
import json
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
import joblib
import numpy as np
import pyarrow.parquet as pq


def main():
    rel = ROOT.parent/'outputs/data_foundation'/json.loads((ROOT.parent/'outputs/data_foundation/CURRENT.json').read_text())['path']
    model_path = ROOT/'topic_model.joblib'
    tm = joblib.load(model_path)
    vec, nmf = tm['vectorizer'], tm['model']
    topics_meta = json.loads((ROOT.parent/'outputs/topic_pilot.json').read_text(encoding='utf8'))['topics']
    assert len(topics_meta) == nmf.n_components

    texts = collections.defaultdict(list)   # story id -> printed excerpts
    kinds = {}
    for a in pq.read_table(rel/'derived/reuse_family_appearances.parquet', columns=['family_id', 'excerpt']).to_pylist():
        texts[a['family_id']].append(a['excerpt'] or ''); kinds[a['family_id']] = 'matched'
    db = sqlite3.connect((rel/'research.sqlite').as_uri() + '?mode=ro', uri=True)
    for gid, ex in db.execute('SELECT group_id, excerpts_json FROM group_publications ORDER BY group_id, publication_date'):
        texts[gid].append(' '.join(json.loads(ex))); kinds[gid] = 'reviewed'

    ids = sorted(texts)
    flat, owner = [], []
    for i, sid in enumerate(ids):
        for t in texts[sid]:
            flat.append(t); owner.append(i)
    owner = np.array(owner)
    W = np.zeros((len(flat), nmf.n_components))
    for s in range(0, len(flat), 20000):  # in chunks, to keep memory low
        W[s:s+20000] = nmf.transform(vec.transform(flat[s:s+20000]))
        print('scored', min(s+20000, len(flat)), 'of', len(flat), flush=True)
    sums = np.zeros((len(ids), nmf.n_components))
    np.add.at(sums, owner, W)
    tops_p = W.argmax(axis=1)

    stories = {}
    for i, sid in enumerate(ids):
        w = sums[i]; total = w.sum()
        share = w / total if total > 0 else np.zeros_like(w)
        order = np.argsort(-share)
        mine = tops_p[owner == i]
        stories[sid] = {'kind': kinds[sid], 'top': int(order[0]), 'top_share': round(float(share[order[0]]), 3), 'second': int(order[1]),
                        'printings': int(len(mine)), 'agreement': round(float((mine == order[0]).mean()), 3) if total > 0 else 0.0,
                        'no_signal': bool(total == 0), 'weights': [round(float(x), 4) for x in share]}

    # Display order: start from the most distinct topic, then always step to the most similar remaining one.
    C = nmf.components_ / np.linalg.norm(nmf.components_, axis=1, keepdims=True)
    S = C @ C.T
    np.fill_diagonal(S, -1)
    start = int(np.argmin(S.max(axis=1)))
    order, left = [start], set(range(len(S))) - {start}
    while left:
        nxt = max(left, key=lambda k: S[order[-1], k]); order.append(nxt); left.remove(nxt)
    topics = [{'index': k, 'id': topics_meta[k]['topic_id'], 'terms': topics_meta[k]['top_terms'][:6], 'display_order': order.index(k)} for k in range(len(topics_meta))]
    agree = np.mean([s['agreement'] for s in stories.values() if s['printings'] >= 2 and not s['no_signal']])
    out = {'model_file': 'work/topic_model.joblib', 'model_sha256': hashlib.sha256(model_path.read_bytes()).hexdigest(),
           'topics': topics, 'mean_agreement_multi_printing': round(float(agree), 3), 'stories': stories}
    dest = ROOT.parent/'outputs/story_discovery_all/story_topics.json'
    dest.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    print(json.dumps({'stories': len(stories), 'reviewed': sum(s['kind'] == 'reviewed' for s in stories.values()),
                      'mean_agreement': out['mean_agreement_multi_printing'], 'no_signal': sum(s['no_signal'] for s in stories.values()),
                      'order': [topics_meta[k]['topic_id'] for k in order]}), flush=True)


if __name__ == '__main__':
    main()
