"""Topic census rows for the pages whose RevX text is filed under another page (2026-11-22).

derived/page_topic_census.parquet (run:topic-census-frozen24, made by work/recheck_full_corpus.py) scores each eligible
page from its selected transcription: the RevX text when it has 200 or more wordlike tokens, else the CA text. Release
v0.8.1 found 260 RevX texts filed under another page than the scan they transcribe (derived/revx_page_map.parquet), and
the census rows of those 260 pages hold the scores of the text filed there, which is another page's. This script makes
their rows by the census's own rule, applied to the page each text transcribes:
- 117 of the 260 are scan pages that another misfiled RevX text transcribes (the best match by share4_at where two do).
  Their row takes the scores the census computed for that text, unchanged (run:topic-census-frozen24).
- 143 are scan pages that no RevX text transcribes. Their CA text, the Library's OCR of their own scan, is scored by the
  frozen model with the census code: 220-word passages (a last passage under 80 words joins the one before), TF-IDF and
  the 24-component NMF of work/topic_model.joblib, weights scaled by each component's total and allocated by words; in
  batches of up to 128 pages in shard order (the census's batch size), under four BLAS threads, as the census ran.
Safeguard: before scoring, the script runs the census code again on every original batch (128 shard rows) that holds
one of the 260 pages, and stops unless it reproduces the stored rows of every eligible page in those batches exactly.
The model solves each batch together (coordinate descent from zero, one stopping rule for the batch), so a page's scores
depend slightly on the pages scored with it; the reproduction shows the code, packages and batches are the census's.
Not changed: the rows of the 140 pages that a misfiled text transcribes outside the 260. 125 of them have an empty or
too short RevX slot and are scored from their own CA text; 15 hold their own RevX text, which another page repeats.
Either way they already score their own page.

Writes census_rows.json and census_summary.json next to this script.
Usage (project root, Python 3.12; a few minutes):  python outputs/filing_corrections/census_rescore.py
"""
from pathlib import Path
import collections
import hashlib
import json
import re
import sqlite3
import sys
import time
import unicodedata
import warnings

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORK = ROOT/'work'
sys.path.insert(0, str(WORK/'python_packages'))
import joblib
import numpy as np
import pyarrow
import pyarrow.parquet as pq
import scipy
import sklearn
from threadpoolctl import threadpool_limits

BASE = ROOT/'outputs/data_foundation/v0.11.6'
TOPICS = [f'T{t+1:02}' for t in range(24)]
BATCH = 128
page_of = lambda key: 'page:'+key.replace('|', ':')

# The census code of work/recheck_full_corpus.py, copied unchanged (that script runs when imported).
word_re = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")


def split(text):
    text = unicodedata.normalize('NFKC', text or '').replace('ſ', 's')
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
    matches = list(word_re.finditer(text)); starts = list(range(0, len(matches), 220))
    if len(starts) > 1 and len(matches)-starts[-1] < 80: starts.pop()
    result = []
    for j, s in enumerate(starts):
        e = starts[j+1] if j+1 < len(starts) else len(matches)
        result.append((text[matches[s].start():matches[e-1].end()], e-s))
    return result


def score(pages, vectorizer, model, scale, caught_all):
    """pages: [(page_id, text)] scored as one batch -> {page_id: census values}."""
    texts, counts, indices = [], [], []
    for pi, (_, text) in enumerate(pages):
        for raw, n in split(text):
            texts.append(raw); counts.append(n); indices.append(pi)
    with threadpool_limits(limits=4):
        with warnings.catch_warnings(record=True) as caught:
            W = model.transform(vectorizer.transform(texts))
    caught_all.update(str(w.message) for w in caught)
    weights = W*scale; den = weights.sum(axis=1); Q = np.divide(weights, den[:, None], out=np.zeros_like(weights), where=den[:, None] > 0)
    ix = np.array(indices); wc = np.array(counts); pt = np.zeros((len(pages), 24)); pw = np.zeros(len(pages)); zero = np.zeros(len(pages))
    np.add.at(pt, ix, Q*wc[:, None]); np.add.at(pw, ix, wc); np.add.at(zero, ix, wc*(den == 0))
    return {pid: dict(words=int(pw[k]), unassigned_words=int(zero[k]), **{TOPICS[t]: float(pt[k, t]) for t in range(24)})
            for k, (pid, _) in enumerate(pages)}


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    t0 = time.time()
    db = sqlite3.connect((BASE/'research.sqlite').as_uri()+'?mode=ro', uri=True)
    model_source = json.loads(db.execute("SELECT parameters_json FROM runs WHERE id='run:topic-census-frozen24'").fetchone()[0])['model_source_id']
    model_sha = db.execute('SELECT sha256 FROM sources WHERE id=?', (model_source,)).fetchone()[0]
    assert file_sha(WORK/'topic_model.joblib') == model_sha, 'the frozen model changed'
    shards = {Path(p).name: s for p, s in db.execute("SELECT path, sha256 FROM sources WHERE kind='raw_parquet'")}
    assert len(shards) == 6 and all(file_sha(WORK/'data'/n) == s for n, s in shards.items()), 'a pinned shard changed'
    bundle = joblib.load(WORK/'topic_model.joblib'); vectorizer, model = bundle['vectorizer'], bundle['model']
    scale = model.components_.sum(axis=1)

    pm = pq.read_table(BASE/'derived/revx_page_map.parquet').to_pylist()
    misfiled = {m['page_id'] for m in pm}
    sources_of = collections.defaultdict(list)
    for m in pm:
        sources_of[m['revx_text_of']].append(m)
    orphans = {p for p in misfiled if p not in sources_of}
    moved_from = {p: max(sources_of[p], key=lambda m: m['share4_at'])['page_id'] for p in misfiled if p in sources_of}
    assert (len(misfiled), len(orphans), len(moved_from)) == (260, 143, 117), (len(misfiled), len(orphans), len(moved_from))
    census = {r['page_id']: r for r in pq.read_table(BASE/'derived/page_topic_census.parquet').to_pylist()}
    assert all(census[p]['source'] == 'RevX' for p in misfiled)

    audit = pq.read_table(WORK/'page_audit.parquet').to_pylist()
    lookup = {(r['file'], r['file_row']): r for r in audit if r['eligible']}
    caught = set()
    batches, compared, worst, orphan_ca = [], 0, 0.0, []
    for file in sorted((WORK/'data').glob('*.parquet')):
        assert file.name in shards
        offset = 0
        for batch in pq.ParquetFile(file).iter_batches(batch_size=BATCH, columns=['RevX_OCR_text', 'ca_ocr_text']):
            metas = [(j, lookup.get((file.name, offset+j))) for j in range(batch.num_rows)]
            metas = [(j, m) for j, m in metas if m is not None]
            ids = [page_of(m['key']) for _, m in metas]
            if misfiled & set(ids):
                rows = batch.to_pylist()
                pages = [(page_of(m['key']), rows[j]['RevX_OCR_text'] if m['selected_source'] == 'RevX' else rows[j]['ca_ocr_text']) for j, m in metas]
                again = score(pages, vectorizer, model, scale, caught)
                for pid, v in again.items():
                    old = census[pid]
                    diff = max(abs(v[t] - old[t]) for t in TOPICS)
                    worst = max(worst, diff)
                    assert v['words'] == old['words'] and v['unassigned_words'] == old['unassigned_words'] and diff == 0.0, ('not reproduced', pid, diff)
                compared += len(again)
                batches.append({'file': file.name, 'first_row': offset, 'rows': batch.num_rows, 'pages': len(pages),
                                'misfiled_pages': sorted(set(ids) & misfiled)})
                orphan_ca += [(file.name, offset+j, page_of(m['key']), rows[j]['ca_ocr_text']) for j, m in metas if page_of(m['key']) in orphans]
            offset += batch.num_rows
        print('read', file.name, round(time.time()-t0, 1), 's', flush=True)
    assert {p for _, _, p, _ in orphan_ca} == orphans, 'every orphan page is in a batch with a misfiled page (its own)'

    # The 143 pages no RevX text transcribes: their CA text, in shard order, batches of up to 128 pages.
    orphan_ca.sort(key=lambda x: (x[0], x[1]))
    scored = {}
    for i in range(0, len(orphan_ca), BATCH):
        part = orphan_ca[i:i+BATCH]
        scored.update(score([(p, text) for _, _, p, text in part], vectorizer, model, scale, caught))
    rows = {}
    for p in sorted(misfiled):
        if p in orphans:
            rows[p] = dict(scored[p], source='CA', text_page_id=p, how='scored')
        else:
            q = moved_from[p]
            rows[p] = dict({k: census[q][k] for k in ['words', 'unassigned_words'] + TOPICS}, source='RevX', text_page_id=q, how='moved')
    for p, r in rows.items():
        assert abs(sum(r[t] for t in TOPICS) + r['unassigned_words'] - r['words']) <= 1e-5 * max(1, r['words']), p
    (HERE/'census_rows.json').write_text(json.dumps(rows, indent=0, sort_keys=True), encoding='utf8')
    summary = {
        'made': '2026-11-22', 'base_release': '0.11.6', 'census_run': 'run:topic-census-frozen24', 'model_sha256': model_sha,
        'packages': {'numpy': np.__version__, 'scipy': scipy.__version__, 'scikit-learn': sklearn.__version__, 'pyarrow': pyarrow.__version__},
        'rows': len(rows), 'moved': sum(r['how'] == 'moved' for r in rows.values()), 'scored_from_ca': sum(r['how'] == 'scored' for r in rows.values()),
        'reproduction': {'original_batches_rerun': len(batches), 'eligible_pages_compared': compared, 'reproduced_exactly': True, 'max_abs_difference': worst},
        'ca_batches': (len(orphan_ca) + BATCH - 1) // BATCH, 'model_warnings': sorted(caught),
        'words': {'before': sum(census[p]['words'] for p in misfiled), 'after': sum(r['words'] for r in rows.values())},
        'batches': batches, 'seconds': round(time.time()-t0, 1)}
    (HERE/'census_summary.json').write_text(json.dumps(summary, indent=1), encoding='utf8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'batches'}, indent=1), flush=True)


if __name__ == '__main__':
    main()
