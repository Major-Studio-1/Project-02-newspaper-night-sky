"""Group the 1797 cross-newspaper text-reuse matches into candidate story families.

Input: outputs/reading_evidence_2026-11-03/passage_matches.json (Codex's reuse run; main profile).
Two matched passages join one family when their spans on the same page overlap.
Output is a ranked candidate list for reading. A family is not yet a reviewed story:
one family can mix several items set next to each other, and one story can split
into several families when OCR damage breaks the match.

Run from the project root (any Python 3).
"""
from pathlib import Path
import collections
import json
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
MATCHES = ROOT/'outputs/reading_evidence_2026-11-03/passage_matches.json'
OUT = ROOT/'outputs/story_discovery_1797'
STOP = set('the of and to in a that is was for on by with as be his it at from have this are which their they or not been but were has had an all will we our by her its who would there may any these them upon more than so if no one into same said other such some most made being can should those very only great been when what also about two three'.split())


def main():
    matches = [m for m in json.loads(MATCHES.read_text(encoding='utf8')) if 'main' in m['profiles']]
    # Nodes are (page key, span); union-find over overlapping spans on the same page.
    nodes, parent = [], []
    by_page = collections.defaultdict(list)
    meta = {}

    def add(side, span):
        key = side['key']
        for i in by_page[key]:
            s = nodes[i][1]
            if span[0] < s[1] and s[0] < span[1]:
                return i, True
        nodes.append((key, list(span)))
        parent.append(len(parent))
        by_page[key].append(len(nodes)-1)
        meta[key] = {k: side[k] for k in ('date', 'paper', 'lccn', 'page', 'url', 'pdf_url', 'source')}
        return len(nodes)-1, False

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        parent[find(i)] = find(j)

    excerpts = collections.defaultdict(list)
    for m in matches:
        a, _ = add(m['a'], m['a_span'])
        b, _ = add(m['b'], m['b_span'])
        # Widen the stored span so later overlaps on this page are caught.
        for idx, span in ((a, m['a_span']), (b, m['b_span'])):
            s = nodes[idx][1]
            s[0], s[1] = min(s[0], span[0]), max(s[1], span[1])
        union(a, b)
        excerpts[a].append(m['a']['normalized_excerpt'])
        excerpts[b].append(m['b']['normalized_excerpt'])

    # Merge nodes that ended up overlapping after widening.
    for key, idxs in by_page.items():
        for x in idxs:
            for y in idxs:
                if x < y and nodes[x][1][0] < nodes[y][1][1] and nodes[y][1][0] < nodes[x][1][1]:
                    union(x, y)

    families = collections.defaultdict(list)
    for i in range(len(nodes)):
        families[find(i)].append(i)
    match_count = collections.Counter()
    words = collections.Counter()
    for m in matches:
        root = find(next(i for i in by_page[m['a']['key']] if nodes[i][1][0] <= m['a_span'][0] < nodes[i][1][1] or nodes[i][1][0] < m['a_span'][1] <= nodes[i][1][1]))
        match_count[root] += 1
        words[root] += m['matched_words']

    rows = []
    for root, idxs in families.items():
        pages = sorted({nodes[i][0] for i in idxs}, key=lambda k: (meta[k]['date'], k))
        papers = sorted({meta[k]['lccn'] for k in pages})
        texts = [t for i in idxs for t in excerpts[i]]
        rep = max(texts, key=len)
        tokens = collections.Counter(w for t in texts for w in re.findall(r"[a-z]{4,}", t) if w not in STOP)
        rows.append({
            'newspapers': len(papers), 'pages': len(pages), 'passages': len(idxs), 'matches': match_count[root],
            'matched_words': words[root], 'first': meta[pages[0]]['date'], 'last': meta[pages[-1]]['date'],
            'keywords': [w for w, _ in tokens.most_common(12)],
            'appearances': [{'key': k, **meta[k], 'spans': [nodes[i][1] for i in idxs if nodes[i][0] == k]} for k in pages],
            'representative_excerpt': rep[:900],
        })
    rows.sort(key=lambda r: (-r['newspapers'], -r['pages'], -r['matched_words']))
    for n, r in enumerate(rows, 1):
        r['family_id'] = f'F97-{n:03}'
    OUT.mkdir(exist_ok=True)
    summary = {
        'source': MATCHES.relative_to(ROOT).as_posix(), 'profile': 'main (>=80 matched words, similarity >=0.7, different series, <=120 days apart)',
        'matches_used': len(matches), 'families': len(rows),
        'by_newspaper_count': dict(sorted(collections.Counter(r['newspapers'] for r in rows).items())),
        'caveat': 'Candidate families from algorithmic shared wording. Not reviewed stories: a family may join adjacent items, and same-newspaper repeats are not in the input.',
    }
    (OUT/'families.json').write_text(json.dumps({'summary': summary, 'families': rows}, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
