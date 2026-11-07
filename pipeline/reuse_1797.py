"""Bounded local text-reuse diagnostic, with inspectable matches and sensitivity.
No article counts, copying directions, or public-attention estimates are inferred.
"""
import pathlib, sys, json, re, unicodedata, hashlib, collections, itertools, datetime, difflib, time
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python_packages'))
import numpy as np
import pyarrow.parquet as pq
OUT=ROOT.parent/'outputs/reading_evidence_2026-11-03';OUT.mkdir(exist_ok=True)
CACHE=ROOT/'reuse_1797';CACHE.mkdir(exist_ok=True)
TOKEN=re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")
T=[f'T{i:02}' for i in range(1,25)]
started=time.time()
def tokenize(text):
 text=unicodedata.normalize('NFKC',text or '').replace('ſ','s')
 text=re.sub(r'(\w)-\s*\n\s*(\w)',r'\1\2',text)
 return [m.group().lower() for m in TOKEN.finditer(text)]
def fingerprints(tokens):
 # Winnow 5-word shingles in 8-shingle windows, keeping the rightmost minimum.
 hashes=[int.from_bytes(hashlib.blake2b(' '.join(tokens[i:i+5]).encode(),digest_size=8).digest(),'little') for i in range(len(tokens)-4)]
 keep={}
 for i in range(max(0,len(hashes)-7)):
  j=min(range(i,i+8),key=lambda j:(hashes[j],-j));keep[j]=hashes[j]
 return [(h,p) for p,h in keep.items()]
pages_file=CACHE/'pages.json'
if pages_file.exists():pages=json.loads(pages_file.read_text(encoding='utf8'))
else:
 audit=[r for r in pq.read_table(ROOT/'page_audit.parquet').to_pylist() if r['eligible'] and r['year']==1797]
 loc={(r['file'],r['file_row']):r for r in audit};pages=[]
 for file in sorted((ROOT/'data').glob('*.parquet')):
  offset=0
  for batch in pq.ParquetFile(file).iter_batches(batch_size=256,columns=['RevX_OCR_text','ca_ocr_text']):
   for j,r in enumerate(batch.to_pylist()):
    m=loc.get((file.name,offset+j))
    if m:
     text=r['RevX_OCR_text'] if m['selected_source']=='RevX' else r['ca_ocr_text']
     pages.append(dict(key=m['key'],date=m['issue_date'],paper=m['newspaper_title'],lccn=m['lccn'],edition=str(m['edition_order']),page=str(m['Page']),url=m['Web_URL'],pdf_url=m['pdf_url'],source=m['selected_source'],tokens=tokenize(text)))
   offset+=batch.num_rows
  print('LOADED',file.name,len(pages),flush=True)
 pages.sort(key=lambda r:(r['date'],r['key']));pages_file.write_text(json.dumps(pages,ensure_ascii=False),encoding='utf8')
print('PAGES',len(pages),'TOKENS',sum(len(r['tokens']) for r in pages),flush=True)
dates=[datetime.date.fromisoformat(p['date']).toordinal() for p in pages]
matches_file=CACHE/'matches.json'
if matches_file.exists():matches=json.loads(matches_file.read_text())
else:
 inv=collections.defaultdict(list)
 for i,p in enumerate(pages):
  for h,pos in fingerprints(p['tokens']):inv[h].append((i,pos))
 print('INDEX',len(inv),'fingerprints',flush=True)
 candidates=collections.defaultdict(list);ignored=0
 for occur in inv.values():
  pids={p for p,pos in occur}
  if len(pids)>10 or len(occur)>20:ignored+=1;continue
  if len(pids)<2:continue
  for (a,x),(b,y) in itertools.combinations(occur,2):
   if a==b or pages[a]['lccn']==pages[b]['lccn'] or abs(dates[a]-dates[b])>120:continue
   if a>b:a,b,x,y=b,a,y,x
   candidates[a,b].append((x,y))
 del inv
 candidates={k:sorted(set(v)) for k,v in candidates.items() if len(set(v))>=6}
 print('CANDIDATE_PAIRS',len(candidates),'COMMON_FINGERPRINTS_SKIPPED',ignored,flush=True)
 matches=[]
 for ci,((a,b),seeds) in enumerate(sorted(candidates.items())):
  # Monotone local chains allow modest insertions/deletions and broken alignment.
  chains=[]
  for x,y in seeds:
   choices=[(max(x-ch[-1][0],y-ch[-1][1]),i) for i,ch in enumerate(chains) if 0<x-ch[-1][0]<=100 and 0<y-ch[-1][1]<=100 and abs((x-ch[-1][0])-(y-ch[-1][1]))<=60]
   if choices:chains[min(choices)[1]].append((x,y))
   else:chains.append([(x,y)])
  for ch in chains:
   if len(ch)<6:continue
   x0,y0=ch[0];x1,y1=ch[-1][0]+5,ch[-1][1]+5
   if min(x1-x0,y1-y0)<60:continue
   aa=pages[a]['tokens'][x0:x1];bb=pages[b]['tokens'][y0:y1]
   sm=difflib.SequenceMatcher(None,aa,bb,autojunk=False)
   blocks=[(x0+m.a,y0+m.b,m.size) for m in sm.get_matching_blocks() if m.size]
   n=sum(z[2] for z in blocks);ratio=2*n/(len(aa)+len(bb))
   if n<60 or ratio<.6:continue
   matches.append(dict(a=a,b=b,a_span=[x0,x1],b_span=[y0,y1],matched_words=n,similarity=ratio,seeds=len(ch),blocks=blocks))
  if ci%250==0:print('ALIGNED',ci,'/',len(candidates),'PASSAGES',len(matches),flush=True)
 for i,m in enumerate(matches,1):m['id']=f'M{i:05}'
 matches_file.write_text(json.dumps(matches),encoding='utf8')
 (CACHE/'retrieval.json').write_text(json.dumps(dict(candidate_page_pairs=len(candidates),common_fingerprints_skipped=ignored)),encoding='utf8')
print('MATCHES',len(matches),round(time.time()-started,1),'seconds',flush=True)
profiles={'broad':(60,.6),'main':(80,.7),'strict':(120,.8)}
counts={}
masks={name:[np.zeros(len(p['tokens']),dtype=bool) for p in pages] for name in profiles}
for name,(minimum,ratio) in profiles.items():
 accepted=[m for m in matches if m['matched_words']>=minimum and m['similarity']>=ratio]
 # Same-date matches remain visible but have no temporal representative selected.
 for m in accepted:
  a,b=m['a'],m['b']
  if dates[a]==dates[b]:continue
  assert dates[a]<dates[b]
  for x,y,n in m['blocks']:masks[name][b][y:y+n]=True
 counts[name]=dict(passages=len(accepted),page_pairs=len({(m['a'],m['b']) for m in accepted}),pages_in_matches=len({i for m in accepted for i in [m['a'],m['b']]}),discounted_words=sum(int(a.sum()) for a in masks[name]),same_date_passages=sum(dates[m['a']]==dates[m['b']] for m in accepted))
passages=[]
for f in sorted((ROOT/'review_census').glob('*_passages.parquet')):
 passages.extend(pq.read_table(f,filters=[('year','=',1797)]).to_pylist())
bykey=collections.defaultdict(list)
for row in passages:bykey[row['key']].append(row)
stats=collections.defaultdict(lambda:dict(words=0.,signal=np.zeros(24)))
page_scores=[];checked=0
for i,p in enumerate(pages):
 blocks=bykey[p['key']];assert sum(b['words'] for b in blocks)==len(p['tokens']),p['key'];checked+=1
 start=0
 for block in blocks:
  n=block['words'];q=np.array([block[t] for t in T]);month=p['date'][:7]
  for name in ['all_publications']+list(profiles):
   weight=n if name=='all_publications' else n-int(masks[name][i][start:start+n].sum())
   for period in [month,'1797']:
    s=stats[period,name];s['words']+=weight;s['signal']+=q*weight
  start+=n
 page_scores.append(dict(**{k:v for k,v in p.items() if k!='tokens'},words=len(p['tokens']),**{f'{k}_matched_later_words':int(masks[k][i].sum()) for k in profiles}))
trends=[]
for (period,profile),s in sorted(stats.items()):
 trends.append(dict(period=period,profile=profile,words=s['words'],shares={t:float(s['signal'][j]/s['words']) if s['words'] else None for j,t in enumerate(T)}))
chain=json.loads((ROOT.parent/'outputs/chain_pilot.json').read_text(encoding='utf8'));cv={v['id']:v for v in chain['versions']};idx={p['key']:i for i,p in enumerate(pages)}
controls=[]
for aid,bid in [('H001','H002'),('H002','H006'),('H001','H006'),('H012','X016')]:
 a,b=sorted([idx[cv[aid]['key']],idx[cv[bid]['key']]])
 found=[m for m in matches if m['a']==a and m['b']==b]
 # Check overlap with the manually selected passage, not merely any shared text on the page.
 def region(vid):
  target=tokenize(cv[vid]['excerpt']);text=pages[idx[cv[vid]['key']]]['tokens'];sm=difflib.SequenceMatcher(None,target,text,autojunk=False);zs=[z for z in sm.get_matching_blocks() if z.size>=5];return [min(z.b for z in zs),max(z.b+z.size for z in zs)]
 ra,rb=region(aid),region(bid)
 if idx[cv[aid]['key']]!=a:ra,rb=rb,ra
 local=[m for m in found if max(m['a_span'][0],ra[0])<min(m['a_span'][1],ra[1]) and max(m['b_span'][0],rb[0])<min(m['b_span'][1],rb[1])]
 controls.append(dict(versions=[aid,bid],matching_ids=[m['id'] for m in local],recovered_profiles={name:any(m['matched_words']>=n and m['similarity']>=rat for m in local) for name,(n,rat) in profiles.items()}))
export=[]
for m in matches:
 row={k:v for k,v in m.items() if k not in ['a','b','blocks']}
 for side in ['a','b']:
  p=pages[m[side]];lo,hi=m[side+'_span'];row[side]={k:v for k,v in p.items() if k!='tokens'};row[side]['normalized_excerpt']=' '.join(p['tokens'][lo:hi])
 row['profiles']=[k for k,(n,rat) in profiles.items() if m['matched_words']>=n and m['similarity']>=rat]
 row['status']='algorithmic shared-wording candidate; copying route and article boundaries unverified'
 export.append(row)
result=dict(scope=dict(year=1797,eligible_pages=len(pages),issues=len({(p['lccn'],p['date'],p['edition']) for p in pages}),series=len({p['lccn'] for p in pages}),words=sum(len(p['tokens']) for p in pages),cross_series_only=True,max_publication_gap_days=120),profiles={k:dict(min_matched_words=v[0],min_similarity=v[1],**counts[k]) for k,v in profiles.items()},trends=trends,positive_controls=controls,validation=dict(page_word_totals_match=checked,independent_reviewer=False),method='5-word shingles; rightmost minimum in 8-shingle windows; ignore fingerprints on >10 pages or >20 occurrences; >=6 shared fingerprints; monotone chains with <=100-word gaps and <=60-word drift; token SequenceMatcher; approximate local alignment. Later matched token positions downweighted to zero only against an earlier date; same-day ties retained. Frozen 220-word-block topic weights apportioned to retained tokens. This is sensitivity, not validated reprint correction.')
(OUT/'reuse_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'passage_matches.json').write_text(json.dumps(export,ensure_ascii=False),encoding='utf8')
(OUT/'page_coverage.json').write_text(json.dumps(page_scores,ensure_ascii=False),encoding='utf8')
print(json.dumps(dict(scope=result['scope'],profiles=result['profiles'],controls=controls),ensure_ascii=False),flush=True)
