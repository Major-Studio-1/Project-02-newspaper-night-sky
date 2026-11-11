"""Find pages filed under 1793 whose own datelines are later than the issue they are filed under.

The masthead check (check_mastheads_1793.py) reads only page 1. While choosing the stories, the reviewer of July to
December found that pages 3 and 4 filed under the American Herald of Liberty of 2 July 1793 hold the text of the 9 July
issue's pages 3 and 4 (page 3 prints "BOSTON, JULY 3"). A page cannot print a dateline later than its own issue, so
this script reads every page's RevX transcription for datelines ("BOSTON, July 3.") that fall 1 to 60 days after the
filed date (larger gaps are almost always 1792 datelines of foreign news, which crossed the Atlantic in two or three
months). For each flagged page it names the page of a later issue of the same series that shares most of its word
4-grams (long s, f and s folded), with that share. Standing advertisements repeat from week to week, so a high share
alone does not show a misfiled page; a late dateline together with a near-identical later page does. Writes
page_date_flags.csv next to this script. Run from the project root with Python 3.12:

    python outputs/story_discovery_1793/check_duplicate_pages_1793.py
"""
from pathlib import Path
import csv
import datetime
import json
import re

HERE = Path(__file__).resolve().parent
MON = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)([A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2}),?\s+"
                      r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-zA-Z]*\.?,?\s*(\d{1,2})(?:st|d|th|nd|rd)?\.\s")


def grams(text, n=4):
    ws = re.findall(r'[a-z]+', (text or '').lower().replace('ſ', 's').replace('f', 's'))
    return {hash(tuple(ws[i:i+n])) for i in range(len(ws)-n+1)}


def main():
    pages = json.loads((HERE/'search_pages.json').read_text(encoding='utf8'))
    rows = []
    for p in pages:
        filed = datetime.date.fromisoformat(p['date'])
        late = []
        for m in DATELINE.finditer(p['texts']['RevX_OCR_text'] or ''):
            try:
                d = datetime.date(1793, MON.index(m.group(2)[:3].lower())+1, int(m.group(3)))
            except ValueError:
                continue
            if 1 <= (d - filed).days <= 60:
                late.append(f'{m.group(1)}, {m.group(2)} {m.group(3)}')
        if not late:
            continue
        mine = grams(p['texts']['RevX_OCR_text'])
        best, twin = 0.0, ''
        for q in pages:
            if q['lccn'] == p['lccn'] and q['date'] > p['date']:
                other = grams(q['texts']['RevX_OCR_text'])
                if mine and other:
                    share = len(mine & other) / min(len(mine), len(other))
                    if share > best:
                        best, twin = share, q['key']
        rows.append({'page': p['key'], 'paper': p['paper'], 'late_datelines': '; '.join(late), 'closest_later_page': twin,
                     'share4': round(best, 3)})
    out = HERE/'page_date_flags.csv'
    with out.open('w', encoding='utf8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['page', 'paper', 'late_datelines', 'closest_later_page', 'share4'])
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)


if __name__ == '__main__':
    main()
