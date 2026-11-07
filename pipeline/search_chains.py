import pathlib,json,re,sys,collections,time
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python_packages'))
import pyarrow.parquet as pq
start=time.time()
families={
 'F1':dict(title='French fleet off Ireland: the report and its challenge',start='1797-01-01',end='1797-06-30',pattern=r'bantry|(?:boyd.{0,1300}ireland)|(?:ireland.{0,1300}boyd)',terms=['bantry','boyd','liverpool','chronicle','29th','26th','twenty thousand','20,000']),
 'F2':dict(title='Cayenne seizure decree and the American papers it cites',start='1797-02-01',end='1797-09-30',pattern=r'jeannet|jeannct|(?:cayenne.{0,1800}decree)|(?:decree.{0,1800}cayenne)|american jacobin newspaper',terms=['jeannet','cayenne','american papers','germinal','vague destination','jacobin','english port']),
 'F3':dict(title='Cape of Good Hope clearance resolution: reprinted document compared',start='1794-05-01',end='1794-06-30',pattern=r'(?:cape.{0,30}good hope.{0,1100}clearance)|(?:clearance.{0,1100}cape.{0,30}good hope)',terms=['cape','good hope','clearances','unlade','security','may 7','washington'])}
coverage={k:dict(pages=0,issues=set(),series=set()) for k in families}
cols=['Web_URL','newspaper_title','place_of_publication','lccn','issue_date','edition_order','Page','pdf_url','ca_ocr_text','RevX_OCR_text']
results=[]
def norm(t):return re.sub(r'\s+',' ',re.sub(r'(?<=\w)-\s+(?=\w)','',t or '').replace('ſ','s')).strip()
for file in sorted((ROOT/'data').glob('*.parquet')):
 offset=0
 for batch in pq.ParquetFile(file).iter_batches(batch_size=256,columns=cols):
  for j,row in enumerate(batch.to_pylist()):
   dt=row['issue_date'];date=dt.date().isoformat() if hasattr(dt,'date') else str(dt)[:10]
   fs=[k for k,f in families.items() if f['start']<=date<=f['end']]
   if not fs:continue
   text=norm(row['RevX_OCR_text']);ca=norm(row['ca_ocr_text'])
   for k in fs:
    f=families[k];cv=coverage[k];cv['pages']+=1;cv['issues'].add((row['lccn'],date,row['edition_order']));cv['series'].add(row['lccn'])
    m=list(re.finditer(f['pattern'],text.lower()));cam=list(re.finditer(f['pattern'],ca.lower()))
    if not m and not cam:continue
    source='RevX' if m else 'CA';use=text if m else ca;ms=m or cam
    matches=[]
    for mt in ms:
     a=max(0,mt.start()-500);b=min(len(use),mt.end()+1700);segment=use[a:b]
     score=sum(term in segment.lower() for term in f['terms'])
     matches.append(dict(start=a,end=b,text=segment,score=score))
    best=max(matches,key=lambda x:x['score'])
    meta={kk:row[kk] for kk in cols if kk not in ['ca_ocr_text','RevX_OCR_text','issue_date']}
    meta.update(family_id=k,date=date,key=f"{row['lccn']}|{date}|{row['edition_order']}|{row['Page']}",file=file.name,file_row=offset+j,selected_source=source,RevX_text=text,CA_text=ca,hit_count=len(ms),best=best,matched_sources=[s for s,mm in [('RevX',m),('CA',cam)] if mm])
    results.append(meta)
  offset+=len(batch)
 print(file.name,'hits',len(results),'elapsed',round(time.time()-start,1),flush=True)
for k,c in coverage.items():c['issues']=len(c['issues']);c['series']=len(c['series'])
results.sort(key=lambda c:(c['family_id'],c['date'],c['lccn'],int(c['Page'])))
for i,c in enumerate(results,1):c['hit_id']=f'H{i:03}'
out=dict(search_families=families,coverage=coverage,hits=results,search_scope='All six pinned source shards; both OCR fields searched within each declared date window. Regex candidates, not verified articles or transmission links.',counts=dict(collections.Counter(r['family_id'] for r in results)))
(ROOT/'chain_search.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'coverage':coverage,'counts':out['counts'],'elapsed':round(time.time()-start,1)},ensure_ascii=False))
