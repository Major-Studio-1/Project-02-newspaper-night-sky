"""Find 1806 pages whose own datelines are later than the issue they belong to (the 1793 check, for 1806).

As outputs/story_discovery_1793/check_duplicate_pages_1793.py: a page cannot print a dateline later than its own issue, so
every page's RevX transcription is read for datelines ("BOSTON, July 3.") that fall 2 to 60 days after the page's date
(the printed date, from search_pages.json made with work/year_search_pages.py --printed-dates). A dateline one day
later is left out: datelines of the evening before, and dailies dated for the next morning, are common. For each flagged
page it names the page of a later issue of the same series that shares most of its word 4-grams (long s, f and s
folded), with that share. Standing advertisements repeat from issue to issue, so a high share alone does not show a
misfiled page; a late dateline together with a near-identical later page does. Misread figures ("July 8" read as
"July 28") also raise flags, so every flag needs reading. Writes page_date_flags.csv next to this script. Run from the
project root with Python 3.12:

    python outputs/story_discovery_1806/check_duplicate_pages_1806.py
"""
from pathlib import Path
import collections
import csv
import datetime
import json
import re

HERE = Path(__file__).resolve().parent
YEAR = 1806
MON = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)([A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2}),?\s+"
                      r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-zA-Z]*\.?,?\s*(\d{1,2})(?:st|d|th|nd|rd)?\.\s")


def grams(text, n=4):
    ws = re.findall(r'[a-z]+', (text or '').lower().replace('ſ', 's').replace('f', 's'))
    return {hash(tuple(ws[i:i+n])) for i in range(len(ws)-n+1)}


def main():
    pages = json.loads((HERE/'search_pages.json').read_text(encoding='utf8'))
    by_series = collections.defaultdict(list)
    for p in pages:
        by_series[p['lccn']].append(p)
    rows = []
    for p in pages:
        dated = datetime.date.fromisoformat(p['date'])
        late = []
        for m in DATELINE.finditer(p['texts']['RevX_OCR_text'] or ''):
            try:
                d = datetime.date(YEAR, MON.index(m.group(2)[:3].lower())+1, int(m.group(3)))
            except ValueError:
                continue
            if 2 <= (d - dated).days <= 60:
                late.append(f'{m.group(1)}, {m.group(2)} {m.group(3)}')
        if not late:
            continue
        mine = grams(p['texts']['RevX_OCR_text'])
        best, twin = 0.0, ''
        for q in by_series[p['lccn']]:
            if q['date'] > p['date']:
                other = grams(q['texts']['RevX_OCR_text'])
                if mine and other:
                    share = len(mine & other) / min(len(mine), len(other))
                    if share > best:
                        best, twin = share, q['key']
        rows.append({'page': p['key'], 'date': p['date'], 'paper': p['paper'], 'late_datelines': '; '.join(late), 'closest_later_page': twin,
                     'share4': round(best, 3)})
    out = HERE/'page_date_flags.csv'
    with out.open('w', encoding='utf8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['page', 'date', 'paper', 'late_datelines', 'closest_later_page', 'share4'])
        w.writeheader()
        w.writerows(rows)
    print(len(rows), 'pages with a late dateline;', sum(r['share4'] >= 0.5 for r in rows), 'of them share half their 4-grams with a later page')
    for r in sorted(rows, key=lambda r: -r['share4'])[:40]:
        print(f"{r['share4']:.3f} {r['page']} ({r['date']}) late: {r['late_datelines'][:90]} | closest: {r['closest_later_page']}")


if __name__ == '__main__':
    main()
