"""Dump every source page of one year, with both transcriptions, for phrase searches and item finding.

Same page records and normalization as outputs/pilot_expansion_2026-11-05/search_pages.json (1797):
join hyphen-plus-whitespace between word characters, long s to s, collapse whitespace.
Model-ineligible pages are included. Run from the project root with Python 3.12:

    python work/year_search_pages.py 1776 outputs/story_discovery_1776/search_pages.json

--printed-dates takes the year and each page's date from the current release's issues.publication_date (the printed
date) instead of the date the collection files the issue under. Used from 1806 on: release v0.10.2 dates 106 Kentucky
Gazette issues two years before their filed dates (outputs/kentucky_gazette_dates/), so 98 issues filed under 1808 are
pages of 1806, and 7 filed under 1806 are pages of 1804. Page keys keep the filed date, as page ids do; a page whose
printed date differs also records 'filed_date'. Without the option the output is as before.
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

FIELDS = ('RevX_OCR_text', 'ca_ocr_text')
norm = lambda t: re.sub(r'\s+', ' ', re.sub(r'(?<=\w)-\s+(?=\w)', '', t or '').replace('ſ', 's')).strip()


def printed_dates():
    """Issue id -> printed date, from the current release (the filed date unless a release corrected it)."""
    from archive_data.consumer import release_path
    out = {}
    with (release_path()/'tables/issues.jsonl').open(encoding='utf8') as stream:
        for line in stream:
            row = json.loads(line)
            out[row['id']] = row['publication_date']
    return out


def main(year, out, printed=False):
    year, out = int(year), Path(out)
    audit = pq.read_table(ROOT/'page_audit.parquet').to_pylist()
    if printed:
        dates = printed_dates()
        for r in audit:
            r['printed_date'] = dates.get(f"issue:{r['lccn']}:{r['issue_date']}:{r['edition_order']}", r['issue_date'])
        audit = [r for r in audit if int(r['printed_date'][:4]) == year]
    else:
        audit = [r for r in audit if r['year'] == year]
    by_file = collections.defaultdict(dict)
    for row in audit:
        by_file[row['file']][row['file_row']] = row
    pages = []
    for name, lookup in sorted(by_file.items()):
        pf = pq.ParquetFile(ROOT/'data'/name)
        offset = 0
        for rg in range(pf.num_row_groups):
            n = pf.metadata.row_group(rg).num_rows
            wanted = {i: r for i, r in lookup.items() if offset <= i < offset+n}
            if wanted:
                rows = pf.read_row_group(rg, columns=list(FIELDS)).to_pylist()
                for index, meta in wanted.items():
                    date = meta.get('printed_date', meta['issue_date'])
                    pages.append({'key': meta['key'], 'date': date, 'paper': meta['newspaper_title'], 'lccn': meta['lccn'],
                                  'edition': meta['edition_order'], 'page': meta['Page'], 'eligible': meta['eligible'],
                                  'source_file': name, 'source_row': index,
                                  **({'filed_date': meta['issue_date']} if date != meta['issue_date'] else {}),
                                  'texts': {f: norm(rows[index-offset][f]) for f in FIELDS}})
            offset += n
    pages.sort(key=lambda p: (p['date'], p['key']))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pages, ensure_ascii=False), encoding='utf8')
    print(year, 'pages', len(pages), 'series', len({p['lccn'] for p in pages}), 'eligible', sum(p['eligible'] for p in pages),
          'empty RevX', sum(not p['texts']['RevX_OCR_text'] for p in pages), 'empty CA', sum(not p['texts']['ca_ocr_text'] for p in pages),
          'redated', sum('filed_date' in p for p in pages))


if __name__ == '__main__':
    main(*[a for a in sys.argv[1:] if not a.startswith('--')][:2], printed='--printed-dates' in sys.argv[1:])
