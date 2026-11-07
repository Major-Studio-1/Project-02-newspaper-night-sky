"""Frozen-model corpus census and phrase-led evidence search; no model refit."""
import pathlib, sys, json, re, unicodedata, hashlib, time, argparse, warnings
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python_packages'))
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import joblib
from threadpoolctl import threadpool_limits

OUT=ROOT.parent/'outputs'/'research_review_2026-11-02'
OUT.mkdir(exist_ok=True)
CACHE=ROOT/'review_census'; CACHE.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=0);args=parser.parse_args()
audit=pq.read_table(ROOT/'page_audit.parquet').to_pylist()
lookup={(r['file'],r['file_row']):r for r in audit if r['eligible']}
pilot={json.loads(s)['key'] for s in (ROOT/'pilot_pages.jsonl').open(encoding='utf8')}
bundle=joblib.load(ROOT/'topic_model.joblib');vectorizer=bundle['vectorizer'];model=bundle['model']
scale=model.components_.sum(axis=1)
word_re=re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")

def split(text):
    text=unicodedata.normalize('NFKC',text or '').replace('\u017f','s')
    text=re.sub(r'(\w)-\s*\n\s*(\w)',r'\1\2',text)
    matches=list(word_re.finditer(text)); starts=list(range(0,len(matches),220))
    if len(starts)>1 and len(matches)-starts[-1]<80:starts.pop()
    result=[]
    for j,s in enumerate(starts):
        e=starts[j+1] if j+1<len(starts) else len(matches)
        result.append((text[matches[s].start():matches[e-1].end()],e-s))
    return result

def norm(text):
    return re.sub(r'\s+',' ',re.sub(r'(?<=\w)-\s+(?=\w)','',text or '').replace('ſ','s')).lower()

patterns={
 'F1': [r'bantr[yi]|bant[rv]y',r'boy[de].{0,1500}(?:ireland|liverpool)|(?:ireland|liverpool).{0,1500}boy[de]',r'inevitably.{0,50}captur',r'londonderry.{0,350}(?:fleet|land|troop)',r'seventeen.{0,60}(?:sail|ship).{0,500}(?:ireland|dismast|bantr)',r'dismast.{0,700}dublin'],
 'F2': [r'jeann[ec]t',r'(?:brig|ship|schooner).{0,25}peace.{0,900}(?:cayen|confiscat|whitney)',r'whitney.{0,1100}cayen',r'seven.{0,50}eight.{0,60}false',r'cayen.{0,2500}(?:american papers|germinal|vague destination)'],
 'F3': [r'good\s*hope.{0,1500}(?:clearance|unlad|security|embargo)',r'(?:clearance|unlad|security|embargo).{0,1500}good\s*hope']
}
compiled={f:[re.compile(p) for p in ps] for f,ps in patterns.items()}
start=time.time();total=0;total_pass=0
for file in sorted((ROOT/'data').glob('*.parquet')):
    tag=file.stem;dest=CACHE/(tag+'.parquet');p_dest=CACHE/(tag+'_passages.parquet');done=CACHE/(tag+'_done.json')
    if not args.limit and done.exists():
        print('CACHED',tag,flush=True);continue
    rows=[];pass_blocks=[];ca_rows=[];hits=[];offset=0
    for batch in pq.ParquetFile(file).iter_batches(batch_size=128,columns=['RevX_OCR_text','ca_ocr_text']):
        texts=[];counts=[];metas=[];indices=[];hashes=[]
        ca_texts=[];ca_counts=[];ca_indices=[];ca_metas=[]
        for j,r in enumerate(batch.to_pylist()):
            meta=lookup.get((file.name,offset+j))
            if meta is None:continue
            if args.limit and total>=args.limit:break
            pi=len(metas);metas.append(meta);total+=1
            text=r['RevX_OCR_text'] if meta['selected_source']=='RevX' else r['ca_ocr_text']
            for raw,n in split(text):
                texts.append(raw);counts.append(n);indices.append(pi)
                hashes.append(hashlib.sha256(' '.join(raw.lower().split()).encode()).hexdigest())
            if meta['key'] in pilot and meta['ca_words']>=200:
                ci=len(ca_metas);ca_metas.append(meta)
                for raw,n in split(r['ca_ocr_text']):ca_texts.append(raw);ca_counts.append(n);ca_indices.append(ci)
            fs=[]
            if meta['year']==1797:fs=['F1','F2']
            if '1794-04-01'<=meta['issue_date']<='1794-07-31':fs=['F3']
            for family in fs:
                matches={};snippets=[]
                for source,col in [('RevX','RevX_OCR_text'),('CA','ca_ocr_text')]:
                    t=norm(r[col]);ms=[(k,mt) for k,rx in enumerate(compiled[family]) for mt in rx.finditer(t)]
                    if ms:
                        matches[source]=sorted(set(k for k,m in ms))
                        snippets.extend(dict(source=source,pattern=k,text=t[max(0,m.start()-400):min(len(t),m.end()+1400)]) for k,m in ms[:12])
                if matches:
                    hits.append(dict(family=family,key=meta['key'],date=meta['issue_date'],lccn=meta['lccn'],paper=meta['newspaper_title'],page=meta['Page'],file=file.name,file_row=offset+j,url=meta['Web_URL'],pdf_url=meta['pdf_url'],matches=matches,snippets=snippets,RevX_text=r['RevX_OCR_text'],CA_text=r['ca_ocr_text']))
        if texts:
            with threadpool_limits(limits=4):
                with warnings.catch_warnings(record=True) as caught:
                    W=model.transform(vectorizer.transform(texts))
                if caught:print('MODEL WARNINGS',list(set(str(w.message) for w in caught)),flush=True)
            weights=W*scale;den=weights.sum(axis=1);Q=np.divide(weights,den[:,None],out=np.zeros_like(weights),where=den[:,None]>0)
            ix=np.array(indices);wc=np.array(counts);pt=np.zeros((len(metas),24));pw=np.zeros(len(metas));zero=np.zeros(len(metas))
            np.add.at(pt,ix,Q*wc[:,None]);np.add.at(pw,ix,wc);np.add.at(zero,ix,wc*(den==0))
            for k,m in enumerate(metas):
                rows.append(dict(key=m['key'],year=m['year'],date=m['issue_date'],lccn=m['lccn'],paper=m['newspaper_title'],source=m['selected_source'],edition=str(m['edition_order']),page=str(m['Page']),words=int(pw[k]),unassigned_words=int(zero[k]),**{f'T{t+1:02}':float(pt[k,t]) for t in range(24)}))
            pass_blocks.append(pa.table(dict(hash=hashes,year=[metas[k]['year'] for k in indices],lccn=[metas[k]['lccn'] for k in indices],date=[metas[k]['issue_date'] for k in indices],key=[metas[k]['key'] for k in indices],words=counts,**{f'T{t+1:02}':Q[:,t] for t in range(24)})))
            total_pass+=len(texts)
        if ca_texts:
            with threadpool_limits(limits=4):W=model.transform(vectorizer.transform(ca_texts))
            weights=W*scale;den=weights.sum(axis=1);Q=np.divide(weights,den[:,None],out=np.zeros_like(weights),where=den[:,None]>0)
            ix=np.array(ca_indices);wc=np.array(ca_counts);pt=np.zeros((len(ca_metas),24));pw=np.zeros(len(ca_metas))
            np.add.at(pt,ix,Q*wc[:,None]);np.add.at(pw,ix,wc)
            for k,m in enumerate(ca_metas):ca_rows.append(dict(key=m['key'],year=m['year'],lccn=m['lccn'],words=int(pw[k]),**{f'T{t+1:02}':float(pt[k,t]) for t in range(24)}))
        offset+=batch.num_rows
        if total and total%2048<128:print('PROGRESS',total,'pages',total_pass,'passages',round(time.time()-start,1),'sec',flush=True)
        if args.limit and total>=args.limit:break
    if args.limit:
        print(json.dumps(dict(benchmark_pages=total,passages=total_pass,seconds=time.time()-start,rate_pages_sec=total/(time.time()-start))),flush=True);break
    pq.write_table(pa.Table.from_pylist(rows),dest,compression='zstd')
    pq.write_table(pa.concat_tables(pass_blocks),p_dest,compression='zstd')
    pq.write_table(pa.Table.from_pylist(ca_rows),CACHE/(tag+'_ca.parquet'),compression='zstd')
    (CACHE/(tag+'_hits.json')).write_text(json.dumps(hits,ensure_ascii=False),encoding='utf8')
    done.write_text(json.dumps(dict(pages=len(rows),passages=sum(len(p) for p in pass_blocks),ca_pages=len(ca_rows),hits=len(hits),seconds=time.time()-start)),encoding='utf8')
    print('SAVED',tag,len(rows),'pages',len(hits),'candidates',round(time.time()-start,1),'sec',flush=True)
