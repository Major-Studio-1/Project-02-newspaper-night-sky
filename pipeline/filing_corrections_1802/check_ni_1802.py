"""The evidence for release v0.11.13: eight National Intelligencer issues of 1802 filed under the wrong dates (2026-11-23).

The review of 1802 (outputs/story_discovery_1802/README.md, "Data issues"; register X-1802-08) read the first page of each
issue on its scan. This script records, from the year's page dump, what the transcriptions say on those pages and how the
dates fall in the week, and compares the four pages filed under 24 November with the issue filed under 24 December:

- mastheads_1802.json: for each issue, the filed and printed dates with their weekdays, the pages the collection holds,
  and the masthead line of page 1 in the RevX text (the CA texts of these mastheads are unreadable). The paper appeared on
  Mondays, Wednesdays and Fridays. RevX reads two mastheads as the 16th where the scans print the 1st ("SEPTEMBER 1st",
  "OCTOBER 1st"): 16 September 1802 was a Thursday and 16 October a Saturday, days the paper did not appear.
- second_scan_1802.json: the share of word 4-grams each page filed under 24 November shares with each page filed under
  24 December, in both transcriptions (pages 1 to 4 match pages 1 to 4: CA 100%, RevX 92% to 100%; other pairs 1% or less).

Input: outputs/story_discovery_1802/search_pages.json (git-ignored; work/year_search_pages.py 1802 makes it again).
Usage (project root, Python 3.12):  python outputs/filing_corrections_1802/check_ni_1802.py
"""
from pathlib import Path
import datetime
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NI = 'sn83045242'
ISSUES = [('1802-08-21', '1802-08-02'), ('1802-09-11', '1802-09-01'), ('1802-10-10', '1802-10-01'), ('1802-11-06', '1802-12-06'),
          ('1802-11-08', '1802-12-08'), ('1802-11-29', '1802-12-29'), ('1802-12-30', '1802-12-31')]
SECOND = ('1802-11-24', '1802-12-24')   # filed under, and the issue it is another scan of
weekday = lambda d: datetime.date.fromisoformat(d).strftime('%A')


def grams(text):
    w = re.findall(r'[a-z]+', (text or '').lower())
    return {tuple(w[i:i + 4]) for i in range(len(w) - 3)}


def main():
    pages = json.loads((ROOT/'outputs/story_discovery_1802/search_pages.json').read_text(encoding='utf8'))
    by_date = {}
    for p in pages:
        if p['lccn'] == NI:
            by_date.setdefault(p['date'], {})[p['page']] = p
    rows = []
    for filed, printed in ISSUES + [SECOND]:
        held = by_date.get(filed, {})
        revx = re.sub(r'\s+', ' ', held[1]['texts']['RevX_OCR_text'] or '')
        m = re.search(r'PER ANN[A-Z]*\.\s*([A-Z]+,\s*[^.]*?\d{4})\.', revx)
        rows.append({'issue_id': f'issue:{NI}:{filed}:1', 'filed_date': filed, 'filed_weekday': weekday(filed),
                     'printed_date': printed, 'printed_weekday': weekday(printed), 'pages_held': sorted(held),
                     'issue_at_printed_date': sorted(by_date.get(printed, {})), 'revx_masthead': m.group(1) if m else None,
                     'second_scan': (filed, printed) == SECOND})
    (HERE/'mastheads_1802.json').write_text(json.dumps({'made': datetime.date.today().isoformat(), 'newspaper': NI,
        'note': 'The paper appeared on Mondays, Wednesdays and Fridays. The printed dates were read on the scans by the 1802 review; '
                'revx_masthead is the RevX text of the masthead line, which misreads "1st" as "16" twice.', 'issues': rows},
        ensure_ascii=False, indent=1) + '\n', encoding='utf8', newline='\n')
    filed, of = SECOND
    shares = {}
    for src in ('RevX_OCR_text', 'ca_ocr_text'):
        for i, a in sorted(by_date[filed].items()):
            ga = grams(a['texts'][src])
            for j, b in sorted(by_date[of].items()):
                gb = grams(b['texts'][src])
                shares[f'{src}|{i}|{j}'] = round(len(ga & gb) / max(1, min(len(ga), len(gb))), 3)
    (HERE/'second_scan_1802.json').write_text(json.dumps({'made': datetime.date.today().isoformat(), 'filed_under': filed, 'scan_of': of,
        'measure': 'shared word 4-grams / the smaller set, per transcription, page of 24 November | page of 24 December', 'shares': shares},
        indent=1) + '\n', encoding='utf8', newline='\n')
    for r in rows:
        print(r['filed_date'], r['filed_weekday'][:3], '->', r['printed_date'], r['printed_weekday'][:3], r['pages_held'], r['revx_masthead'])
    print({k: v for k, v in shares.items() if k.split('|')[1] == k.split('|')[2]})


if __name__ == '__main__':
    main()
