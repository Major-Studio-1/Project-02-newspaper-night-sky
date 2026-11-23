"""Find 1806 pages filed under the wrong issue: pages whose text matches a distant issue of their paper better than the
issues around their own date.

Found while checking datelines (check_duplicate_pages_1806.py): pages 3 and 4 filed under the National Intelligencer of
9 July 1806 print news of early September and the standing advertisements of September, while pages 3 and 4 filed
under 8 September print July's. A paper's standing advertisements and continued items change slowly, so a page shares
most of its text with the same paper's pages of the weeks around it. For every 1806 page this script takes the best
share of word 5-grams (long s, f and s folded; RevX, or CA where RevX is empty) with any page of the same series within
14 days ('near'), and with any page more than 30 days away ('far'), and flags pages where far exceeds near by 0.15 and
reaches 0.3. Pages are compared with pages of their own year only. Writes page_neighbour_flags.csv next to this
script. Run from the project root with Python 3.12:

    python outputs/story_discovery_1806/check_page_neighbours_1806.py
"""
from pathlib import Path
import collections
import csv
import datetime
import json
import re

HERE = Path(__file__).resolve().parent


def grams(text, n=5):
    ws = re.findall(r'[a-z]+', (text or '').lower().replace('ſ', 's').replace('f', 's'))
    return frozenset(hash(tuple(ws[i:i+n])) for i in range(len(ws)-n+1))


def main():
    pages = json.loads((HERE/'search_pages.json').read_text(encoding='utf8'))
    by_series = collections.defaultdict(list)
    for p in pages:
        g = grams(p['texts']['RevX_OCR_text']) or grams(p['texts']['ca_ocr_text'])
        if len(g) >= 200:
            p['_g'] = g
            p['_d'] = datetime.date.fromisoformat(p['date'])
            by_series[p['lccn']].append(p)
    rows = []
    for lccn, ps in by_series.items():
        for p in ps:
            near = far = (0.0, None)
            for q in ps:
                if q is p or q['key'].rsplit('|', 2)[0] == p['key'].rsplit('|', 2)[0]:
                    continue   # the same issue
                gap = abs((q['_d'] - p['_d']).days)
                if gap > 30 or gap <= 14:
                    share = len(p['_g'] & q['_g']) / min(len(p['_g']), len(q['_g']))
                    if gap <= 14 and share > near[0]:
                        near = (share, q['key'])
                    elif gap > 30 and share > far[0]:
                        far = (share, q['key'])
            if far[0] >= 0.3 and far[0] - near[0] >= 0.15:
                rows.append({'page': p['key'], 'date': p['date'], 'paper': p['paper'], 'near_share': round(near[0], 3), 'near_page': near[1],
                             'far_share': round(far[0], 3), 'far_page': far[1]})
    rows.sort(key=lambda r: (r['paper'], r['date'], r['page']))
    with (HERE/'page_neighbour_flags.csv').open('w', encoding='utf8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['page', 'date', 'paper', 'near_share', 'near_page', 'far_share', 'far_page'])
        w.writeheader()
        w.writerows(rows)
    print(len(rows), 'flagged pages')
    for r in rows:
        print(f"{r['page']} ({r['date']}) near {r['near_share']} {r['near_page']} | far {r['far_share']} {r['far_page']}")


if __name__ == '__main__':
    main()
