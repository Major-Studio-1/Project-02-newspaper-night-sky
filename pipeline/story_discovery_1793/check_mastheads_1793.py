"""Compare the filed date of every issue filed under 1793 with the date printed in its masthead, for all 12 series.

The reviewed stories of 1808 found that the Kentucky Gazette and General Advertiser (sn84038147) issues filed under
1806-1808 print a masthead two years earlier (outputs/story_discovery_1808/kentucky_gazette_dates.csv). This script runs
the same check on 1793, for every series, not only the Kentucky Gazette of 1793 (sn82014782, an earlier series of
John Bradford's paper). For each issue and edition, the start of page 1 in both transcriptions (RevX and CA) is searched
for a masthead date line ("WEDNESDAY, January 2, 1793"); the weekday it names is checked against the calendar for both
the filed date and the masthead date. Writes masthead_dates.csv next to this script. Run from the project root with
Python 3.12 (needs search_pages.json from work/year_search_pages.py):

    python outputs/story_discovery_1793/check_mastheads_1793.py
"""
from pathlib import Path
import collections
import csv
import datetime
import json
import re

HERE = Path(__file__).resolve().parent
MONTHS = {m: i for i, m in enumerate(['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER',
                                      'OCTOBER', 'NOVEMBER', 'DECEMBER'], 1)}
DAYS = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
MAST = re.compile(r'(' + '|'.join(DAYS) + r')\W{0,4}(' + '|'.join(MONTHS) + r')\W{0,3}(\d{1,2})\W{0,3}(17\d\d)')
HEAD = 2500   # characters of page 1 searched for the masthead


def squeeze(text):
    """Upper-case, long s folded, and spaced capitals joined: 'S A T U R D A Y' -> 'SATURDAY', 'MARC H' -> 'MARCH'."""
    t = (text or '').upper().replace('ſ', 'S')
    t = re.sub(r'\b([A-Z]) (?=[A-Z]\b)', r'\1', t)
    t = re.sub(r'(?<=[A-Z]) (?=[A-Z]{1,3}\b)', '', t)
    return t


def main():
    pages = json.loads((HERE/'search_pages.json').read_text(encoding='utf8'))
    rows = []
    for p in pages:
        if p['page'] != 1:
            continue
        found = None
        for field in ('RevX_OCR_text', 'ca_ocr_text'):
            m = MAST.search(squeeze(p['texts'].get(field))[:HEAD])
            if m:
                found = (field, m)
                break
        filed = datetime.date.fromisoformat(p['date'])
        row = {'key': p['key'], 'paper': p['paper'], 'filed_date': p['date'], 'filed_weekday': filed.strftime('%A'),
               'masthead': '', 'from': '', 'masthead_date': '', 'masthead_weekday_fits': '', 'day_offset': ''}
        if found:
            field, m = found
            row.update(masthead=m.group(0), **{'from': 'RevX' if field.startswith('RevX') else 'CA'})
            try:
                md = datetime.date(int(m.group(4)), MONTHS[m.group(2)], int(m.group(3)))
                row.update(masthead_date=md.isoformat(), masthead_weekday_fits=md.strftime('%A').upper() == m.group(1),
                           day_offset=(filed - md).days)
            except ValueError:
                pass
        rows.append(row)
    rows.sort(key=lambda r: (r['paper'], r['filed_date'], r['key']))
    out = HERE/'masthead_dates.csv'
    with out.open('w', encoding='utf8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    by = collections.defaultdict(collections.Counter)
    for r in rows:
        by[r['paper']]['issues'] += 1
        if r['masthead_date']:
            by[r['paper']]['read'] += 1
            by[r['paper']]['same date' if r['day_offset'] == 0 else 'differs'] += 1
            by[r['paper']]['weekday fits masthead' if r['masthead_weekday_fits'] else 'weekday does not fit'] += 1
    for paper, c in sorted(by.items()):
        print(f'{paper[:48]:48}', dict(c))
    print('differing:', [(r['key'], r['masthead'], r['day_offset']) for r in rows if r['masthead_date'] and r['day_offset'] != 0])


if __name__ == '__main__':
    main()
