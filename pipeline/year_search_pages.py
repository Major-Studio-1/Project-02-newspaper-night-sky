"""Dump every source page of one year, with both transcriptions, for phrase searches and item finding.

Same page records and normalization as outputs/pilot_expansion_2026-11-05/search_pages.json (1797):
join hyphen-plus-whitespace between word characters, long s to s, collapse whitespace.
Model-ineligible pages are included. Run from the project root with Python 3.12:

    python work/year_search_pages.py 1776 outputs/story_discovery_1776/search_pages.json
"""
from pathlib import Path
import collections
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
import pyarrow.parquet as pq

FIELDS = ('RevX_OCR_text', 'ca_ocr_text')
norm = lambda t: re.sub(r'\s+', ' ', re.sub(r'(?<=\w)-\s+(?=\w)', '', t or '').replace('ſ', 's')).strip()


def main(year, out):
    year, out = int(year), Path(out)
    audit = [r for r in pq.read_table(ROOT/'page_audit.parquet').to_pylist() if r['year'] == year]
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
                    pages.append({'key': meta['key'], 'date': meta['issue_date'], 'paper': meta['newspaper_title'], 'lccn': meta['lccn'],
                                  'edition': meta['edition_order'], 'page': meta['Page'], 'eligible': meta['eligible'],
                                  'source_file': name, 'source_row': index,
                                  'texts': {f: norm(rows[index-offset][f]) for f in FIELDS}})
            offset += n
    pages.sort(key=lambda p: (p['date'], p['key']))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pages, ensure_ascii=False), encoding='utf8')
    print(year, 'pages', len(pages), 'series', len({p['lccn'] for p in pages}), 'eligible', sum(p['eligible'] for p in pages),
          'empty RevX', sum(not p['texts']['RevX_OCR_text'] for p in pages), 'empty CA', sum(not p['texts']['ca_ocr_text'] for p in pages))


if __name__ == '__main__':
    main(*sys.argv[1:3])
