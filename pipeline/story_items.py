"""Split one year's matched stories into single printed items and count where each item was printed.

The automatic families in the release (derived/reuse_*.parquet) join printings whose matched text
overlaps on a page. A news digest or a run of proceedings that papers printed in different pieces
therefore chains several items into one family, and the family's newspaper count belongs to the chain.

This script treats the opening words of every printing in the year's larger families (the release
excerpt: about 70 words from the start of the matched span) as a candidate item. Candidates whose
openings share most of their word 4-grams are one item. Each item's opening is then looked for on
every page of the year, in both transcriptions (RevX and CA). Long s, f and s are folded together,
because older OCR reads the long s as f. A page prints the item when it holds at least CONTAIN of
the opening's 4-grams.

The output lists candidate items for reading; nothing here admits anything. Run from the project root
with Python 3.12:

    python work/story_items.py 1776 outputs/story_discovery_1776/search_pages.json outputs/story_discovery_1776/items.json

Families flagged long_running are left out by default, as for 1776. --long-running takes their printings
as candidates too (used for 1807, where the President's message of 27 October and other widely printed
documents sit in long-running chains); the output then records "long_running_families": true.
"""
from pathlib import Path
import collections
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
sys.path.insert(0, str(ROOT))
import pyarrow.parquet as pq
from archive_data.consumer import release_path

MIN_PAPERS = 4      # families reaching at least this many newspapers supply the candidates
JOIN = 0.5          # two openings are one item when they share this share of the smaller one's 4-grams
CONTAIN = 0.4       # a page prints the item when it holds this share of the opening's 4-grams
WEAK = 0.2          # pages between WEAK and CONTAIN are listed separately, for reading
FIELDS = ('RevX_OCR_text', 'ca_ocr_text')


def words(text):
    return re.findall(r'[a-z]+', (text or '').lower().replace('ſ', 's').replace('f', 's'))


def grams(ws, n=4):
    return {hash(tuple(ws[i:i+n])) for i in range(len(ws)-n+1)}


def first_position(ws, query, n=4):
    # Start of the densest run of the opening's 4-grams: common phrases ("under the crown of")
    # can also occur earlier on the page, so the first single hit is not enough.
    hits = [i for i in range(len(ws)-n+1) if hash(tuple(ws[i:i+n])) in query]
    if not hits:
        return None
    span, best, lo = len(query)+10, (0, hits[0]), 0
    for hi, pos in enumerate(hits):
        while pos-hits[lo] > span:
            lo += 1
        if hi-lo+1 > best[0]:
            best = (hi-lo+1, hits[lo])
    return best[1]


def main(year, pages_path, out_path, min_papers=MIN_PAPERS, long_running=False):
    year, min_papers = str(year), int(min_papers)
    release = release_path()
    fams = {f['family_id']: f for f in pq.read_table(release/'derived/reuse_families.parquet').to_pylist()
            if f['first_date'][:4] == year and (long_running or not f['long_running']) and f['newspapers'] >= min_papers}
    titles = {t['family_id']: t['title'] for t in pq.read_table(release/'derived/reuse_family_titles.parquet', columns=['family_id', 'title']).to_pylist()}
    apps = [a for a in pq.read_table(release/'derived/reuse_family_appearances.parquet',
                                     columns=['family_id', 'page_id', 'publication_date', 'lccn', 'page_number', 'excerpt', 'transcription']).to_pylist()
            if a['family_id'] in fams]
    print(release.name, 'families', len(fams), 'printings', len(apps), flush=True)

    # 1. Candidate openings, joined into items by shared 4-grams.
    cands = []
    for a in apps:
        g = grams(words(a['excerpt']))
        if len(g) >= 20:
            key = a['page_id'].split(':', 1)[1].replace(':', '|')
            cands.append({'family': a['family_id'], 'key': key, 'date': a['publication_date'], 'lccn': a['lccn'], 'excerpt': a['excerpt'], 'g': g})
    index = collections.defaultdict(list)
    for i, c in enumerate(cands):
        for h in c['g']:
            index[h].append(i)
    parent = list(range(len(cands)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, c in enumerate(cands):
        shared = collections.Counter(j for h in c['g'] for j in index[h] if j > i)
        for j, n in shared.items():
            if n >= JOIN*min(len(c['g']), len(cands[j]['g'])):
                parent[find(i)] = find(j)
    clusters = collections.defaultdict(list)
    for i in range(len(cands)):
        clusters[find(i)].append(i)
    items = []
    for members in clusters.values():
        # Representative: the opening that shares most with the others (ties: the earliest printing).
        def centrality(i):
            return (sum(len(cands[i]['g'] & cands[j]['g'])/len(cands[i]['g']) for j in members if j != i), -int(cands[i]['date'].replace('-', '')))
        rep = max(members, key=centrality)
        items.append({'members': members, 'rep': rep, 'g': cands[rep]['g']})
    print('candidates', len(cands), 'items', len(items), flush=True)

    # 2. Look for every item's opening on every page of the year.
    lookup = collections.defaultdict(list)
    for k, it in enumerate(items):
        for h in it['g']:
            lookup[h].append(k)
    pages = json.loads(Path(pages_path).read_text(encoding='utf8'))
    meta = {p['key']: p for p in pages}
    hits = collections.defaultdict(dict)  # item -> page key -> best (share, field, word position)
    for p in pages:
        for field in FIELDS:
            ws = words(p['texts'].get(field))
            counts = collections.Counter(k for h in grams(ws) for k in lookup.get(h, ()))
            for k, n in counts.items():
                share = n/len(items[k]['g'])
                if share >= WEAK and share > hits[k].get(p['key'], (0,))[0]:
                    hits[k][p['key']] = (round(share, 3), field, None)
    for k, it in enumerate(items):
        for key, (share, field, _) in list(hits[k].items()):
            hits[k][key] = (share, field, first_position(words(meta[key]['texts'][field]), it['g']))

    # 3. Report.
    rows = []
    for k, it in enumerate(items):
        printed = sorted((key for key, v in hits[k].items() if v[0] >= CONTAIN), key=lambda key: (meta[key]['date'], key))
        weak = sorted((key for key, v in hits[k].items() if v[0] < CONTAIN), key=lambda key: (meta[key]['date'], key))
        if not printed:
            continue
        in_family = {cands[i]['key'] for i in it['members']}
        rep = cands[it['rep']]
        rows.append({'families': sorted({cands[i]['family'] for i in it['members']}),
                     'family_titles': {f: titles.get(f) for f in sorted({cands[i]['family'] for i in it['members']})},
                     'opening': ' '.join(rep['excerpt'].split()[:45]), 'opening_from': rep['key'],
                     'newspapers': len({meta[key]['lccn'] for key in printed}), 'printings': len(printed),
                     'first': meta[printed[0]]['date'], 'last': meta[printed[-1]]['date'],
                     'found_outside_families': sum(key not in in_family for key in printed),
                     'pages': [{'key': key, 'date': meta[key]['date'], 'lccn': meta[key]['lccn'], 'share': hits[k][key][0],
                                'field': hits[k][key][1], 'word': hits[k][key][2], 'in_family': key in in_family} for key in printed],
                     'weak_pages': [{'key': key, 'date': meta[key]['date'], 'lccn': meta[key]['lccn'], 'share': hits[k][key][0],
                                     'field': hits[k][key][1]} for key in weak]})
    rows.sort(key=lambda r: (-r['newspapers'], -r['printings'], r['first']))
    for n, r in enumerate(rows, 1):
        r['item'] = f'I{year[2:]}-{n:04}'
    head = {'year': int(year), 'release': release.name, 'min_family_papers': min_papers}
    if long_running:
        head['long_running_families'] = True
    Path(out_path).write_text(json.dumps({**head, 'join': JOIN, 'contain': CONTAIN, 'weak': WEAK, 'pages_searched': len(pages),
                                          'families': len(fams), 'candidate_openings': len(cands), 'items': rows},
                                         ensure_ascii=False, indent=1), encoding='utf8')
    print('items printed somewhere', len(rows), '| 10+ papers', sum(r['newspapers'] >= 10 for r in rows), '6+', sum(r['newspapers'] >= 6 for r in rows),
          '4+', sum(r['newspapers'] >= 4 for r in rows), flush=True)


if __name__ == '__main__':
    main(*[a for a in sys.argv[1:] if not a.startswith('--')][:4], long_running='--long-running' in sys.argv[1:])
