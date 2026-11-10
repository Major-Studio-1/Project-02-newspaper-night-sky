"""The printed date of every Kentucky Gazette and General Advertiser issue (sn84038147) in the collection (2026-11-10).

Found while choosing the reviewed stories of 1808: the issues filed under 1808 print 1806 in their mastheads
(outputs/story_discovery_1808/check_kentucky_gazette_dates.py checked 1806-1809). This script checks all 214 issues of
the series, 1803-1809, and decides a printed date for each one filed under 1806, 1807 or 1808:

- masthead: page 1's RevX and CA transcriptions are searched for the masthead line ("THURSDAY, AUGUST 21, 1806") and the
  issue number ("No 1068"). A masthead date whose weekday is right, two years before the filed date, is taken.
- the two-year rule: where the masthead cannot be read (or reads wrong), the filed date less two years is taken when its
  weekday is one of the paper's publication days at the time (the weekdays of the issues with a readable masthead within
  two weeks on either side). The issue numbers read on either side are checked too (a check only: some are misread).
- scans: two issues were checked against the pinned page scans by eye (mastheads/): the issue filed under 3 July 1808
  is No. 1054 of Saturday 5 July 1806 (its masthead, not the two-year rule, gives the day), and the issue filed under 25
  August 1808 repeats the printed masthead of No. 1068 (Thursday 21 August), corrected by hand on the page to 1069 and
  25: Monday 25 August 1806, as the two-year rule gives.

Issues filed under 1803, 1804 and 1809 keep their filed dates (their mastheads agree, apart from misread figures).
Writes issues.csv (one row per issue) and summary.json next to this script. Run from the project root (Python 3.12):

    python outputs/kentucky_gazette_dates/check_dates.py
"""
from pathlib import Path
import collections
import csv
import datetime
import json
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'work/python_packages'))
import pyarrow.parquet as pq

LCCN = 'sn84038147'
REDATE_YEARS = ('1806', '1807', '1808')
WEEKS = 2   # publication days: the weekdays of the readable issues within two weeks on either side
MONTHS = {m: i for i, m in enumerate(['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER',
                                      'OCTOBER', 'NOVEMBER', 'DECEMBER'], 1)}
MAST = re.compile(r'(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\W{0,4}(' + '|'.join(MONTHS) + r')\W{0,3}(\d{1,2})\W{0,3}(1[78]\d\d)')
NUMBER = re.compile(r'\b(?:N[UO]MB?|NO)\W{0,3}(\d{3,4})\b')
# Read by eye on the pinned scans (mastheads/*.jpg): filed date -> (printed date, issue number, what the page shows).
SCANS = {
    '1808-07-03': ('1806-07-05', 1054, 'masthead "VOL. XIX.—No 1054. ... SATURDAY, JULY 5, 1806."'),
    '1808-08-25': ('1806-08-25', 1069, 'printed masthead repeats No 1068, "THURSDAY, AUGUST 21, 1806."; corrected by hand on the page to 1069 and 25'),
}


def two_years_back(d):
    return d.replace(year=d.year - 2)   # no 29 February among these dates


def read_mastheads():
    audit = [r for r in pq.read_table(ROOT/'work/page_audit.parquet').to_pylist() if r['lccn'] == LCCN]
    pages = collections.Counter(r['issue_date'] for r in audit)
    first = {r['issue_date']: r for r in audit if r['Page'] == 1}
    assert set(first) == set(pages), 'every issue has a page 1'
    wanted = collections.defaultdict(dict)
    for r in first.values():
        wanted[r['file']][r['file_row']] = r
    rows = {}
    for name, lookup in sorted(wanted.items()):
        pf, offset = pq.ParquetFile(ROOT/'work/data'/name), 0
        for g in range(pf.num_row_groups):
            n = pf.metadata.row_group(g).num_rows
            hit = [i for i in lookup if offset <= i < offset + n]
            if hit:
                table = pf.read_row_group(g, columns=['RevX_OCR_text', 'ca_ocr_text']).to_pylist()
                for i in hit:
                    meta = lookup[i]
                    text = ' '.join((table[i - offset][f] or '') for f in ('RevX_OCR_text', 'ca_ocr_text'))
                    text = re.sub(r'(?<=[A-Z]) (?=[A-Z]{1,3}\b)', '', text.upper())   # "MARC H" -> "MARCH"
                    m, number = MAST.search(text), NUMBER.search(text[:3000])
                    row = {'issue_id': f"issue:{LCCN}:{meta['issue_date']}:1", 'filed_date': meta['issue_date'], 'pages': pages[meta['issue_date']],
                           'masthead': m.group(0) if m else '', 'masthead_date': '', 'masthead_weekday_fits': '', 'issue_number': int(number.group(1)) if number else ''}
                    if m:
                        try:
                            md = datetime.date(int(m.group(4)), MONTHS[m.group(2)], int(m.group(3)))
                            row.update(masthead_date=md.isoformat(), masthead_weekday_fits=md.strftime('%A').upper() == m.group(1))
                        except ValueError:
                            pass
                    rows[meta['issue_date']] = row
            offset += n
    return [rows[d] for d in sorted(rows)]


def main():
    rows = read_mastheads()
    for r in rows:
        assert r['issue_id'].endswith(':1'), 'one edition per issue in this series'
        filed = datetime.date.fromisoformat(r['filed_date'])
        r['two_year_date'] = two_years_back(filed).isoformat() if r['filed_date'][:4] in REDATE_YEARS else ''
    # A readable masthead: its weekday is right and it gives the filed date (1803, 1804, 1809) or the date two years before.
    def readable(r):
        return r['masthead_weekday_fits'] is True and r['masthead_date'] in (r['filed_date'], r['two_year_date'])
    # Publication days and issue numbers come from the readable mastheads, in printed-date order.
    anchors = sorted((r['masthead_date'], r['filed_date'], r) for r in rows if readable(r))
    cand = {r['filed_date']: (SCANS[r['filed_date']][0] if r['filed_date'] in SCANS else r['two_year_date'] or r['filed_date']) for r in rows}
    for r in rows:
        if r['filed_date'][:4] not in REDATE_YEARS:
            r.update(printed_date=r['filed_date'], basis='filed date (not in the misfiled run)')
            continue
        scan = SCANS.get(r['filed_date'])
        c = cand[r['filed_date']]
        d = datetime.date.fromisoformat(c)
        near = [a for a in anchors if a[0] != c and abs((datetime.date.fromisoformat(a[0]) - d).days) <= WEEKS * 7]
        days = {datetime.date.fromisoformat(a[0]).strftime('%A') for a in near}
        r['publication_days_nearby'] = ' '.join(sorted(days))
        r['weekday_fits_paper'] = d.strftime('%A') in days
        # The nearest readable issue numbers on either side must leave room for the issues between them (a check only:
        # some numbers are misread, so it does not decide a date).
        nb = [a for a in anchors if a[0] < c and a[2]['issue_number']][-1:]
        na = [a for a in anchors if a[0] > c and a[2]['issue_number']][:1]
        if nb and na:
            between = sum(1 for x in cand.values() if nb[0][0] < x < na[0][0])
            r['numbers_around'] = f"{nb[0][2]['issue_number']} ({nb[0][0]}) .. {na[0][2]['issue_number']} ({na[0][0]})"
            r['numbers_fit'] = na[0][2]['issue_number'] - nb[0][2]['issue_number'] == between + 1
        if scan:
            r.update(printed_date=scan[0], basis='scan', scan_issue_number=scan[1], scan_note=scan[2])
        elif readable(r):
            r.update(printed_date=r['masthead_date'], basis='masthead')
        elif r['weekday_fits_paper']:
            why = ('masthead not readable in either transcription' if not r['masthead'] else
                   f"masthead read as \"{r['masthead']}\", which does not fit the calendar")
            r.update(printed_date=r['two_year_date'], basis='two-year rule', note=why)
        else:
            raise SystemExit('No printed date for ' + r['filed_date'])
    redated = [r for r in rows if r['filed_date'][:4] in REDATE_YEARS]
    assert len(redated) == 106 and all(r['weekday_fits_paper'] for r in redated if r['basis'] != 'masthead')
    printed = collections.Counter(r['printed_date'] for r in rows)
    assert max(printed.values()) == 1, 'two issues with one printed date'
    fields = ['issue_id', 'filed_date', 'printed_date', 'basis', 'pages', 'masthead', 'masthead_date', 'masthead_weekday_fits', 'issue_number',
              'two_year_date', 'publication_days_nearby', 'weekday_fits_paper', 'numbers_around', 'numbers_fit', 'scan_issue_number', 'scan_note', 'note']
    with (HERE/'issues.csv').open('w', encoding='utf8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='raise')
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fields})
    summary = {
        'date': '2026-11-10', 'series': LCCN, 'issues': len(rows), 'pages': sum(r['pages'] for r in rows),
        'issues_by_filed_year': dict(sorted(collections.Counter(r['filed_date'][:4] for r in rows).items())),
        'redated': {'issues': len(redated), 'pages': sum(r['pages'] for r in redated),
                    'by_filed_to_printed_year': {f'{a} -> {b}': n for (a, b), n in sorted(collections.Counter((r['filed_date'][:4], r['printed_date'][:4]) for r in redated).items())},
                    'by_basis': dict(collections.Counter(r['basis'] for r in redated)),
                    'two_years_and_two_days': [r['filed_date'] + ' -> ' + r['printed_date'] for r in redated if r['printed_date'] != r['two_year_date']],
                    'numbers_fit_by_basis': {b: dict(collections.Counter(str(r.get('numbers_fit', 'no number on either side')) for r in redated if r['basis'] == b))
                                             for b in ('masthead', 'two-year rule', 'scan')},
                    'numbers_note': 'The issue numbers on either side are counted against the issues in the collection between them, so they also '
                                    'fail where the collection lacks issues (December 1804 to May 1805, 1805, 1807 and 1808) or a number is misread '
                                    '(1036 for 1037 on 6 May, 1073 for 1078 on 25 September 1806).'},
        'publication_days_1806': 'Thursday to 13 February; Wednesday and Saturday from 19 February; Tuesday and Saturday from 6 May; Monday and Thursday from 7 August',
        'kept': {'issues': len(rows) - len(redated), 'masthead_agrees': sum(1 for r in rows if r['filed_date'][:4] not in REDATE_YEARS and r['masthead_date'] == r['filed_date'])},
        'rule': 'A masthead date with the right weekday, two years before the filed date; else the filed date less two years when its weekday is one of the '
                'paper\'s publication days at the time (readable issues within two weeks on either side); two issues read on the scans.',
    }
    (HERE/'summary.json').write_text(json.dumps(summary, indent=1), encoding='utf8')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
