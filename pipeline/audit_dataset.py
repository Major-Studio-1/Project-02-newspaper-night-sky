import collections
import datetime as dt
import hashlib
import json
import pathlib
import random
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'python_packages'))
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

OUT = ROOT.parent / 'outputs'
OUT.mkdir(exist_ok=True)
manifest = json.loads((ROOT / 'source_manifest.json').read_text())
COLS = ['Web_URL', 'newspaper_title', 'place_of_publication', 'lccn', 'issue_date',
        'edition_order', 'Page', 'thumbnail_url', 'pdf_url', 'jpeg2000_url',
        'ca_ocr_text', 'RevX_OCR_text']
WORD_PATTERN = r"[A-Za-z]+(?:['-][A-Za-z]+)*"
rows = []
seen_keys = set()
same_issue_text = set()
global_text_counts = collections.Counter()
start = time.time()

for entry in manifest['files']:
    path = ROOT / 'data' / pathlib.Path(entry['path']).name
    pf = pq.ParquetFile(path)
    file_row = 0
    for batch in pf.iter_batches(batch_size=256, columns=COLS):
        table = pa.Table.from_batches([batch])
        ca = table['ca_ocr_text']
        rev = table['RevX_OCR_text']
        ca_counts = pc.fill_null(pc.count_substring_regex(ca, WORD_PATTERN), 0).to_pylist()
        rev_counts = pc.fill_null(pc.count_substring_regex(rev, WORD_PATTERN), 0).to_pylist()
        values = table.to_pylist()
        for i, record in enumerate(values):
            date = record['issue_date']
            day = date.date().isoformat() if hasattr(date, 'date') else str(date)[:10]
            year = int(day[:4])
            key = f"{record['lccn']}|{day}|{record['edition_order']}|{record['Page']}"
            source = 'RevX' if rev_counts[i] >= 200 else ('CA' if ca_counts[i] >= 200 else 'none')
            text = record['RevX_OCR_text'] if source == 'RevX' else record['ca_ocr_text'] if source == 'CA' else ''
            text_hash = hashlib.sha256(' '.join((text or '').lower().split()).encode()).hexdigest() if text else None
            duplicate_key = key in seen_keys
            seen_keys.add(key)
            issue_text_key = (record['lccn'], day, record['Page'], text_hash)
            duplicate_scan = bool(text_hash and issue_text_key in same_issue_text)
            if text_hash:
                same_issue_text.add(issue_text_key)
                global_text_counts[text_hash] += 1
            row = {k: record[k] for k in COLS if k not in ['ca_ocr_text', 'RevX_OCR_text', 'issue_date']}
            row.update(key=key, issue_date=day, year=year, file=path.name, file_row=file_row+i,
                       ca_words=ca_counts[i], revx_words=rev_counts[i],
                       ca_nonempty=bool((record['ca_ocr_text'] or '').strip()),
                       revx_nonempty=bool((record['RevX_OCR_text'] or '').strip()),
                       selected_source=source,
                       selected_words=rev_counts[i] if source == 'RevX' else ca_counts[i] if source == 'CA' else 0,
                       text_hash=text_hash, duplicate_key=duplicate_key, duplicate_scan=duplicate_scan,
                       eligible=source != 'none' and not duplicate_key and not duplicate_scan and 1770 <= year <= 1810)
            rows.append(row)
        file_row += len(values)
    print(f"Audited {path.name}: {file_row:,} pages; total {len(rows):,}; {time.time()-start:.1f}s", flush=True)

pq.write_table(pa.Table.from_pylist(rows), ROOT / 'page_audit.parquet')

def aggregate(items):
    n = len(items)
    titles = collections.Counter(r['lccn'] for r in items)
    words = sum(r['selected_words'] for r in items if r['eligible'])
    return dict(pages=n, unique_issues=len({(r['lccn'],r['issue_date'],r['edition_order']) for r in items}),
                newspaper_series=len(titles), title_labels=len({r['newspaper_title'] for r in items}),
                publication_locations=len({r['place_of_publication'] for r in items}),
                ca_nonempty=sum(r['ca_nonempty'] for r in items),
                revx_nonempty=sum(r['revx_nonempty'] for r in items),
                ca_at_least_200_words=sum(r['ca_words'] >= 200 for r in items),
                revx_at_least_200_words=sum(r['revx_words'] >= 200 for r in items),
                selected_revx=sum(r['selected_source']=='RevX' for r in items),
                selected_ca=sum(r['selected_source']=='CA' for r in items),
                eligible_pages=sum(r['eligible'] for r in items),
                eligible_wordlike_tokens=words,
                duplicate_keys=sum(r['duplicate_key'] for r in items),
                duplicate_same_issue_page_text=sum(r['duplicate_scan'] for r in items),
                largest_series_page_share=max(titles.values()) / n if n else None)

by_year = []
for year in range(1770,1811):
    group = [r for r in rows if r['year']==year]
    by_year.append(dict(year=year, **aggregate(group)))
by_series=[]
for lccn in sorted({r['lccn'] for r in rows}):
    group=[r for r in rows if r['lccn']==lccn]
    by_series.append(dict(lccn=lccn,
        titles=sorted({r['newspaper_title'] for r in group}),
        locations=sorted({r['place_of_publication'] for r in group}),
        first_year=min(r['year'] for r in group),last_year=max(r['year'] for r in group),
        years_present=len({r['year'] for r in group}),**aggregate(group)))
series_year=[]
for lccn in sorted({r['lccn'] for r in rows}):
    for year in range(1770,1811):
        group=[r for r in rows if r['lccn']==lccn and r['year']==year]
        if group:
            series_year.append(dict(lccn=lccn,year=year,**aggregate(group)))

# Sample at most 100 pages per year. Distribute slots round-robin across
# available newspaper series; select pages by seeded SHA-256 rank within strata.
strata=collections.defaultdict(list)
for row in rows:
    if row['eligible']:
        strata[(row['year'],row['lccn'])].append(row)
selected=[]
sample_strata=[]
for year in range(1770,1811):
    groups={lccn:sorted(group,key=lambda r:hashlib.sha256(('20261027|'+r['key']).encode()).hexdigest())
            for (y,lccn),group in strata.items() if y==year}
    allocation={k:0 for k in groups}
    order=sorted(groups,key=lambda k:hashlib.sha256(f'20261027|{year}|{k}'.encode()).hexdigest())
    slots=min(100,sum(map(len,groups.values())))
    while sum(allocation.values()) < slots:
        for lccn in order:
            if allocation[lccn] < len(groups[lccn]) and sum(allocation.values()) < slots:
                allocation[lccn]+=1
    for lccn, n in allocation.items():
        population=len(groups[lccn])
        sample_strata.append(dict(year=year,lccn=lccn,eligible_population=population,sampled_pages=n,page_expansion_weight=population/n))
        for r in groups[lccn][:n]:
            r['sample_weight']=population/n
            selected.append(r)
selected_lookup={(r['file'],r['file_row']):r for r in selected}
with (ROOT/'pilot_pages.jsonl').open('w',encoding='utf-8') as out:
    for entry in manifest['files']:
        path=ROOT/'data'/pathlib.Path(entry['path']).name
        offset=0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=256,columns=['ca_ocr_text','RevX_OCR_text']):
            for i,r in enumerate(batch.to_pylist()):
                meta=selected_lookup.get((path.name,offset+i))
                if meta:
                    text=r['RevX_OCR_text'] if meta['selected_source']=='RevX' else r['ca_ocr_text']
                    out.write(json.dumps(dict(meta,text=text),ensure_ascii=False)+'\n')
            offset+=batch.num_rows

summary=dict(dataset=manifest['dataset'],revision=manifest['revision'],retrieved_date='2026-10-27',
             source=f"https://huggingface.co/datasets/{manifest['dataset']}/tree/{manifest['revision']}",
             overall=aggregate(rows),date_min=min(r['issue_date'] for r in rows),
             date_max=max(r['issue_date'] for r in rows),
             out_of_range=sum(not 1770<=r['year']<=1810 for r in rows),
             edition_counts=dict(collections.Counter(str(r['edition_order']) for r in rows)),
             exact_repeated_selected_text_groups=sum(n>1 for n in global_text_counts.values()),
             exact_repeated_selected_text_extra_pages=sum(n-1 for n in global_text_counts.values() if n>1),
             pilot_pages=len(selected),pilot_newspaper_series=len({r['lccn'] for r in selected}),
             pilot_years=len({r['year'] for r in selected}),sample_design='At most 100 eligible pages per year; round-robin allocation across newspaper-series/year strata; seeded hash selection within each stratum.',
             eligibility='At least 200 ASCII wordlike tokens in RevX OCR, or original CA OCR as fallback. Exact duplicate page keys and identical text for the same series/date/page are excluded. This is a length screen, not verified OCR accuracy.',
             by_year=by_year,by_series=sorted(by_series,key=lambda r:r['pages'],reverse=True),
             by_series_year=series_year,sample_strata=sample_strata)
(OUT/'coverage_audit.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['by_year','by_series','by_series_year','sample_strata']},indent=2),flush=True)
print('YEAR COVERAGE',flush=True)
for r in by_year:
    print(r['year'],r['pages'],r['newspaper_series'],r['revx_nonempty'],r['eligible_pages'],round(r['largest_series_page_share'] or 0,3),flush=True)
print('TOP SERIES',flush=True)
for r in summary['by_series'][:12]:
    print(r['lccn'],r['titles'],r['pages'],r['first_year'],r['last_year'],flush=True)

