"""Group all-years reuse matches (work/reuse_all/matches_*.json, main profile) into story families.

Same rule as reuse_families_1797.py: matched passages whose spans overlap on the same page join
one family. Families are automatic and NOT checked against scans. For each appearance the
excerpt is re-read from the original transcription (capitalisation and punctuation kept).

Output: outputs/story_discovery_all/families.json and appearances.jsonl, plus a summary.
Run from the project root with Python 3.12.
"""
from pathlib import Path
import collections
import datetime
import json
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
import pyarrow.parquet as pq

CACHE = ROOT/'reuse_all'
OUT = ROOT.parent/'outputs/story_discovery_all'
TOKEN = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")
STOP = set('''the of and to in a that is was for on by with as be his it at from have this are which their they or not been but were has had an
all will we our her its who would there may any these them upon more than so if no one into same said other such some most made being can should those
very only great when what also about two three them shall your you him she out last letter take place inst have been from which'''.split())
EXCERPT_WORDS = 70


def main():
    matches = []
    for f in sorted(CACHE.glob('matches_*.json')):
        matches += [m for m in json.loads(f.read_text(encoding='utf8'))['matches'] if m['main']]
    print('main matches', len(matches), flush=True)

    # Union-find over (page, span) nodes; overlapping spans on one page are one node.
    nodes, parent, by_page = [], [], collections.defaultdict(list)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i

    def node(key, span):
        for i in by_page[key]:
            s = nodes[i][1]
            if span[0] < s[1] and s[0] < span[1]:
                s[0], s[1] = min(s[0], span[0]), max(s[1], span[1])
                return i
        nodes.append((key, list(span))); parent.append(len(parent)); by_page[key].append(len(nodes)-1)
        return len(nodes)-1

    texts = collections.defaultdict(list)
    for m in matches:
        a, b = node(m['a'], m['a_span']), node(m['b'], m['b_span'])
        parent[find(a)] = find(b)
        texts[a].append(m['a_text']); texts[b].append(m['b_text'])
    for key, idx in by_page.items():  # spans widened after insertion can now overlap
        for x in idx:
            for y in idx:
                if x < y and nodes[x][1][0] < nodes[y][1][1] and nodes[y][1][0] < nodes[x][1][1]:
                    parent[find(x)] = find(y)
    fams = collections.defaultdict(list)
    for i in range(len(nodes)):
        fams[find(i)].append(i)

    audit = {r['key']: r for r in pq.read_table(ROOT/'page_audit.parquet').to_pylist() if r['key'] in by_page}
    # Original-case excerpts: re-read the selected transcription and cut by token offsets.
    want = collections.defaultdict(dict)
    for i, (key, span) in enumerate(nodes):
        r = audit[key]
        want[r['file']].setdefault(r['file_row'], []).append(i)
    excerpt = {}
    for shard, rows in want.items():
        pf = pq.ParquetFile(ROOT/'data'/shard); offset = 0
        for g in range(pf.num_row_groups):
            count = pf.metadata.row_group(g).num_rows
            hit = [rw for rw in rows if offset <= rw < offset+count]
            if hit:
                table = pf.read_row_group(g, columns=['RevX_OCR_text', 'ca_ocr_text'])
                for rw in hit:
                    for i in rows[rw]:
                        key, (x0, x1) = nodes[i]
                        field = 'RevX_OCR_text' if audit[key]['selected_source'] == 'RevX' else 'ca_ocr_text'
                        raw = unicodedata.normalize('NFKC', table[field][rw-offset].as_py() or '').replace('ſ', 's')
                        raw = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', raw)
                        spans = [mt.span() for mt in TOKEN.finditer(raw)]
                        if x0 < len(spans):
                            end = spans[min(x1, x0+EXCERPT_WORDS, len(spans))-1][1]
                            excerpt[i] = re.sub(r'\s+', ' ', raw[spans[x0][0]:end]).strip() + (' …' if x1-x0 > EXCERPT_WORDS else '')
            offset += count
        print('excerpts from', shard, flush=True)

    rows = []
    for root, idx in fams.items():
        pages = sorted({nodes[i][0] for i in idx}, key=lambda k: (audit[k]['issue_date'], k))
        papers = sorted({audit[k]['lccn'] for k in pages})
        words = collections.Counter(w for i in idx for t in texts[i] for w in t.split() if len(w) > 3 and w not in STOP)
        first = min(idx, key=lambda i: (audit[nodes[i][0]]['issue_date'], nodes[i][0]))
        label = ' '.join(excerpt.get(first, ' '.join(texts[first][0].split()[:12])).split()[:12])
        apps = []
        for i in sorted(idx, key=lambda i: (audit[nodes[i][0]]['issue_date'], nodes[i][0], nodes[i][1][0])):
            key, span = nodes[i]; r = audit[key]
            apps.append({'key': key, 'date': r['issue_date'], 'lccn': r['lccn'], 'page': r['Page'], 'span': span,
                         'source': r['selected_source'], 'excerpt': excerpt.get(i, ''), 'web_url': r['Web_URL']})
        days = (datetime.date.fromisoformat(apps[-1]['date']) - datetime.date.fromisoformat(apps[0]['date'])).days
        rows.append({'newspapers': len(papers), 'pages': len(pages), 'appearances': apps, 'first': apps[0]['date'], 'last': apps[-1]['date'],
                     'label': label.rstrip(',;:') + ' …', 'keywords': [w for w, _ in words.most_common(10)],
                     # Overlapping matches can chain a long debate or serial document into one family.
                     'long_running': days > 120 or len(pages) > 40})
    rows.sort(key=lambda r: (r['first'][:4], -r['newspapers'], -r['pages'], r['first']))
    seq = collections.Counter()
    for r in rows:
        y = r['first'][:4]; seq[y] += 1; r['family_id'] = f'R{y}-{seq[y]:04d}'
    OUT.mkdir(parents=True, exist_ok=True)
    by_year = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        by_year[r['first'][:4]][min(r['newspapers'], 5)] += 1
    summary = {'matches_main': len(matches), 'families': len(rows), 'families_by_newspapers': dict(sorted(collections.Counter(r['newspapers'] for r in rows).items())),
               'long_running_families': sum(r['long_running'] for r in rows),
               'by_first_year': {y: dict(sorted(c.items())) for y, c in sorted(by_year.items())},
               'status': 'Automatic families from shared wording; not checked against scans. A family can join neighbouring items, and one story can split when OCR damage breaks a match.'}
    (OUT/'families.json').write_text(json.dumps({'summary': summary, 'families': rows}, ensure_ascii=False), encoding='utf8')
    (OUT/'summary.json').write_text(json.dumps(summary, indent=1), encoding='utf8')
    print(json.dumps({k: summary[k] for k in ('matches_main', 'families', 'families_by_newspapers')}), flush=True)


if __name__ == '__main__':
    main()
