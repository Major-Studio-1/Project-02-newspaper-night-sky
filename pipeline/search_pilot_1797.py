"""Versioned retrieval for the two existing 1797 message dossiers; not admissions."""
from pathlib import Path
import sys, json, re, hashlib, collections
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
import pyarrow.parquet as pq
OUT = ROOT.parent/'outputs/pilot_expansion_2026-11-05'
OUT.mkdir(exist_ok=True)
norm = lambda t: re.sub(r'\s+', ' ', re.sub(r'(?<=\w)-\s+(?=\w)', '', t or '').replace('ſ', 's')).strip()
patterns = {
    'bantry_name': r'\bbantr[ey]y?\b',
    'boyd_fleet': r'\bbo[vy][de]\b.{0,850}\b(?:fleet|french|ireland|liverpool)\b',
    'fleet_boyd': r'\b(?:fleet|french|ireland|liverpool)\b.{0,850}\bbo[vy][de]\b',
    'capture_prediction': r'\b(?:whole|all)\b.{0,100}\binevitably\b.{0,50}\bcaptured\b',
    'peace_allen': r'\bpeace\b.{0,180}\ball[ea]n\b|\ball[ea]n\b.{0,180}\bpeace\b',
    'peace_vessel': r'\b(?:brig|br[iy]gantine)\b.{0,25}\bpeace\b',
    'peace_cayenne': r'\bpeace\b.{0,450}\bcayen\w*|\bcayen\w*.{0,450}\bpeace\b',
}
rx={k:re.compile(v,re.I) for k,v in patterns.items()}
audit=[r for r in pq.read_table(ROOT/'page_audit.parquet').to_pylist() if r['year']==1797]
byfile=collections.defaultdict(dict)
for row in audit: byfile[row['file']][row['file_row']]=row
pages=[];candidates=[]
for name, lookup in sorted(byfile.items()):
    pf=pq.ParquetFile(ROOT/'data'/name);offset=0
    for rg in range(pf.num_row_groups):
        n=pf.metadata.row_group(rg).num_rows
        wanted={i:r for i,r in lookup.items() if offset<=i<offset+n}
        if wanted:
            rows=pf.read_row_group(rg,columns=['RevX_OCR_text','ca_ocr_text']).to_pylist()
            for index, meta in wanted.items():
                texts={field:norm(rows[index-offset][field]) for field in ['RevX_OCR_text','ca_ocr_text']}
                hitlist=[]
                for field,text in texts.items():
                    for label,rule in rx.items():
                        for match in rule.finditer(text):
                            lo=max(0,match.start()-250);hi=min(len(text),match.end()+650)
                            hitlist.append({'field':field,'rule':label,'match':[match.start(),match.end()],'context':[lo,hi],'text':text[lo:hi]})
                pages.append({'key':meta['key'],'date':meta['issue_date'],'paper':meta['newspaper_title'],'lccn':meta['lccn'],'edition':meta['edition_order'],'page':meta['Page'],'eligible':meta['eligible'],'source_file':name,'source_row':index,'texts':texts})
                if hitlist:candidates.append({'key':meta['key'],'date':meta['issue_date'],'paper':meta['newspaper_title'],'page':meta['Page'],'eligible':meta['eligible'],'hits':hitlist})
        offset+=n
    print(name, 'pages',len(pages),'candidate pages',len(candidates),flush=True)
pages.sort(key=lambda x:(x['date'],x['key']));candidates.sort(key=lambda x:(x['date'],x['key']))
for c in candidates:c['id']='candidate:1797:'+hashlib.sha256(c['key'].encode()).hexdigest()[:16]
(OUT/'search_pages.json').write_text(json.dumps(pages,ensure_ascii=False),encoding='utf8')
result={'scope':'All source pages dated 1797, including model-ineligible pages, both OCR fields; targeted retrieval, not exhaustive recall.','normalization':'Remove hyphen plus whitespace between word characters; replace long s; collapse whitespace; strip.','patterns':patterns,'pages_searched':len(pages),'eligible_pages':sum(p['eligible'] for p in pages),'candidate_pages':len(candidates),'candidates':candidates}
(OUT/'search_candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
for c in candidates:
    labels=sorted(set(h['rule'] for h in c['hits']))
    snippets=[]
    for h in c['hits']:
        if h['field']=='RevX_OCR_text' and (not snippets or not any(h['text'] in s for s in snippets)):snippets.append(h['text'])
    print(c['key'],','.join(labels),'\n', '\n'.join(snippets)[:1400],'\n',flush=True)
print('DONE',len(pages),len(candidates))
