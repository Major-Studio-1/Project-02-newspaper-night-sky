import collections
import hashlib
import json
import pathlib
import re
import sys
import time
import unicodedata
import warnings

ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python_packages'))
import joblib
import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS,TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from threadpoolctl import threadpool_limits

OUT=ROOT.parent/'outputs'
pages=[json.loads(line) for line in (ROOT/'pilot_pages.jsonl').read_text(encoding='utf-8').splitlines()]
word_re=re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")
extra_stops='''said say says shall may mr mrs messrs esq viz aforesaid thereof hereby whereas therein hereof whereof therein thereof fuch faid fhall alfo thefe thofe fubfcriber fubfcribers hath doth th day days monday tuesday wednesday thursday friday saturday sunday january february march april june july august september october november december jan feb mar apr jun jul aug sep sept oct nov dec yesterday tomorrow instant inst ultimo ult ditto anon newspaper newspapers gazette advertiser printed printing published publisher publishers vol volume page pages number no www http https loc gov jpeg jpg com ocr image'''.split()
stops=sorted(set(ENGLISH_STOP_WORDS).union(extra_stops))
def clean(text):
    text=unicodedata.normalize('NFKC',text).replace('\u017f','s')
    text=re.sub(r'(\w)-\s*\n\s*(\w)',r'\1\2',text)
    return text

passages=[]
for pi,page in enumerate(pages):
    text=clean(page['text'])
    matches=list(word_re.finditer(text))
    starts=list(range(0,len(matches),220))
    if len(starts)>1 and len(matches)-starts[-1]<80:
        starts.pop()
    for si,start in enumerate(starts):
        end=starts[si+1] if si+1<len(starts) else len(matches)
        raw=text[matches[start].start():matches[end-1].end()]
        normalized=' '.join(raw.lower().split())
        passages.append(dict(page_index=pi,passage_index=si,word_count=end-start,
                             text=raw,exact_hash=hashlib.sha256(normalized.encode()).hexdigest(),
                             train=int(hashlib.sha256(('holdout|'+page['key']).encode()).hexdigest()[:8],16)%5!=0))
print(f"Built {len(passages):,} nonoverlapping passages from {len(pages):,} pages",flush=True)
unique_train={}
for passage in passages:
    if passage['train'] and passage['exact_hash'] not in unique_train:
        unique_train[passage['exact_hash']]=passage['text']
vectorizer=TfidfVectorizer(stop_words=stops,strip_accents='unicode',lowercase=True,
    token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z\u017f]{2,23}\b',ngram_range=(1,2),
    min_df=12,max_df=.65,max_features=35000,sublinear_tf=True,dtype=np.float32)
X=vectorizer.fit_transform(list(unique_train.values()))
print(f"Discovery training: {X.shape[0]:,} unique passages, {X.shape[1]:,} features, {X.nnz:,} nonzeros",flush=True)
k=24
start=time.time()
with threadpool_limits(limits=4):
    model=NMF(n_components=k,init='nndsvda',random_state=27,max_iter=450,tol=0.0002)
    W_train=model.fit_transform(X)
    print(f"Primary NMF fitted in {time.time()-start:.1f}s, {model.n_iter_} iterations",flush=True)
    alt=NMF(n_components=k,init='random',random_state=83,max_iter=450,tol=0.0002)
    alt.fit(X)
    similarities=cosine_similarity(model.components_,alt.components_)
    ar,ac=linear_sum_assignment(-similarities)
    stability={int(a):float(similarities[a,c]) for a,c in zip(ar,ac)}
    print(f"Restart agreement median cosine {np.median(list(stability.values())):.3f}; {time.time()-start:.1f}s",flush=True)
    all_X=vectorizer.transform([p['text'] for p in passages])
    W=model.transform(all_X)
terms=vectorizer.get_feature_names_out()
# Normalize each topic's term weights to sum to one and absorb its scale
# into document weights. These are model weights, not calibrated probabilities.
weights=W*model.components_.sum(axis=1)[None,:]
sums=weights.sum(axis=1)
Q=np.divide(weights,sums[:,None],out=np.zeros_like(weights),where=sums[:,None]>0)
dominant=Q.argmax(axis=1)
concentration=Q.max(axis=1)
word_counts=np.array([p['word_count'] for p in passages])
page_indices=np.array([p['page_index'] for p in passages])
page_topic=np.zeros((len(pages),k),dtype=float)
page_words=np.zeros(len(pages),dtype=float)
for j,p in enumerate(passages):
    pi=p['page_index']
    page_topic[pi]+=Q[j]*p['word_count']
    page_words[pi]+=p['word_count']
expanded=np.array([p['sample_weight'] for p in pages])
rng=np.random.default_rng(20261027)
B=250
annual=[]
for year in sorted({p['year'] for p in pages}):
    inds=np.array([i for i,p in enumerate(pages) if p['year']==year])
    numerator=(page_topic[inds]*expanded[inds,None]).sum(axis=0)
    denominator=(page_words[inds]*expanded[inds]).sum()
    share=numerator/denominator
    series=list(sorted({pages[i]['lccn'] for i in inds}))
    title_proportions=[]
    boot_num=np.zeros((B,k))
    boot_den=np.zeros(B)
    for lccn in series:
        ix=np.array([i for i in inds if pages[i]['lccn']==lccn])
        title_proportions.append(page_topic[ix].sum(axis=0)/page_words[ix].sum())
        # Sampling variability only; no model or archive-selection uncertainty.
        counts=rng.multinomial(len(ix),np.full(len(ix),1/len(ix)),size=B)
        pop=len(ix)*expanded[ix[0]]
        if pop<=len(ix)+1e-8:
            boot_num+=page_topic[ix].sum(axis=0)*expanded[ix[0]]
            boot_den+=page_words[ix].sum()*expanded[ix[0]]
        else:
            boot_num+=(counts@page_topic[ix])*expanded[ix[0]]
            boot_den+=(counts@page_words[ix])*expanded[ix[0]]
    boot_share=boot_num/boot_den[:,None]
    rev_ix=np.array([i for i in inds if pages[i]['selected_source']=='RevX'])
    rev_share=(page_topic[rev_ix]*expanded[rev_ix,None]).sum(axis=0)/(page_words[rev_ix]*expanded[rev_ix]).sum() if len(rev_ix) else np.full(k,np.nan)
    equal=np.mean(title_proportions,axis=0)
    for t in range(k):
        annual.append(dict(year=year,topic_id=f'T{t+1:02}',model_share=float(share[t]),
            sampling_interval_low=float(np.quantile(boot_share[:,t],.025)),
            sampling_interval_high=float(np.quantile(boot_share[:,t],.975)),
            equal_series_model_share=float(equal[t]),revx_only_model_share=float(rev_share[t]) if len(rev_ix) else None,
            sampled_pages=len(inds),sampled_series=len(series),sampled_words=int(page_words[inds].sum()),
            expanded_sample_words=float(denominator)))

periods=[(1770,1774),(1775,1779),(1780,1784),(1785,1789),(1790,1794),(1795,1799),(1800,1804),(1805,1810)]
period_rows=[]
for lo,hi in periods:
    ix=np.array([i for i,p in enumerate(pages) if lo<=p['year']<=hi])
    share=(page_topic[ix]*expanded[ix,None]).sum(axis=0)/(page_words[ix]*expanded[ix]).sum()
    for t in range(k):
        period_rows.append(dict(period=f'{lo}-{hi}',topic_id=f'T{t+1:02}',model_share=float(share[t]),
                                sampled_pages=len(ix),sampled_series=len({pages[i]['lccn'] for i in ix})))

topics=[]
heldout=~np.array([p['train'] for p in passages])
for t in range(k):
    top=model.components_[t].argsort()[::-1][:25]
    candidates=np.argsort(weights[:,t])[::-1]
    examples=[]
    used_pages=set()
    title_count=collections.Counter()
    # Reserve two high-weight heldout examples, then four further diverse examples.
    for require_heldout,limit in [(True,2),(False,6)]:
        for j in candidates:
            pi=passages[j]['page_index']
            page=pages[pi]
            if pi in used_pages or title_count[page['lccn']]>=2:
                continue
            if require_heldout and not heldout[j]:
                continue
            if dominant[j]!=t:
                continue
            examples.append(dict(year=page['year'],date=page['issue_date'],newspaper=page['newspaper_title'],
                lccn=page['lccn'],place=page['place_of_publication'],page=page['Page'],edition=page['edition_order'],
                issue_url=page['Web_URL'],pdf_url=page['pdf_url'],thumbnail_url=page['thumbnail_url'],
                jpeg2000_url=page['jpeg2000_url'],ocr_source=page['selected_source'],
                passage_index=passages[j]['passage_index'],heldout=bool(heldout[j]),
                model_concentration=float(concentration[j]),text=passages[j]['text']))
            used_pages.add(pi)
            title_count[page['lccn']]+=1
            if len(examples)>=limit:
                break
    ay=[r for r in annual if r['topic_id']==f'T{t+1:02}']
    topics.append(dict(topic_id=f'T{t+1:02}',top_terms=terms[top].tolist(),
        restart_cosine_agreement=stability[t],
        sample_dominant_passages=int((dominant==t).sum()),
        peak_year=max(ay,key=lambda r:r['model_share'])['year'],
        peak_year_model_share=max(r['model_share'] for r in ay),
        examples=examples))
print('CANDIDATE TOPICS',flush=True)
for topic in topics:
    print(topic['topic_id'],','.join(topic['top_terms'][:14]),'restart',round(topic['restart_cosine_agreement'],3),
          'examples',[(e['date'],e['newspaper']) for e in topic['examples'][:2]],flush=True)

for field,key in [('annual','year'),('periods','period')]:
    grouped={}
    for row in (annual if field=='annual' else period_rows):
        grouped.setdefault(row[key],[]).append(row)
    for records in grouped.values():
        residual=max(0.,1-sum(r['model_share'] for r in records))
        for row in records:
            row['unassigned_model_share']=residual
result=dict(status='Exploratory topic-discovery pilot; labels and grouping require review.',
    method='TF-IDF (unigrams and bigrams) plus 24-topic non-negative matrix factorization; no predefined historical categories.',
    sample_pages=len(pages),sample_passages=len(passages),training_pages=sum(int(hashlib.sha256(('holdout|'+p['key']).encode()).hexdigest()[:8],16)%5!=0 for p in pages),
    heldout_pages=sum(int(hashlib.sha256(('holdout|'+p['key']).encode()).hexdigest()[:8],16)%5==0 for p in pages),
    training_unique_passages=X.shape[0],features=X.shape[1],
    exact_repeated_sample_passage_extras=len(passages)-len({p['exact_hash'] for p in passages}),
    primary_iterations=model.n_iter_,restart_iterations=alt.n_iter_,median_restart_cosine=float(np.median(list(stability.values()))),
    zero_signal_passages=int((sums==0).sum()),median_largest_model_weight=float(np.median(concentration)),
    annual_definition='Within each passage, non-negative topic weights are scaled by topic term-weight sums and normalized. Annual shares are weighted by passage word count and the inverse page inclusion probability in each newspaper-series/year stratum. They are model signal shares, not calibrated probabilities or measured column space.',
    bootstrap_definition='250 page resamples within sampled newspaper-series/year strata. Intervals capture sampling variation only, omit model/OCR/archive bias, and understate variation in strata with one sampled page.',
    sensitivity_definition='Equal-series shares weight the observed newspaper series equally within each year; RevX-only shares exclude original-OCR fallback pages. Neither removes changes in which series are available.',
    limitations=['Topic number 24 is exploratory, not an established count of historical topics.',
                 'Passages are fixed-length text spans, not verified article boundaries; mixed subjects remain.',
                 'OCR is not manually validated. Modern tokenization and stopword choices affect results.',
                 'Exact duplicate passages are collapsed for fitting and retained when estimating attention; near-duplicate reprints are not identified.',
                 'Topic proportions are compositional: falling share alone does not establish displacement.',
                 'A subject/topic and a content genre are separate; discovered clusters may mix both.',
                 'Nothing in this pilot measures historical resolution or establishes a causal effect of attention.'],
    vectorizer_params=dict(min_df=12,max_df=.65,max_features=35000,ngram_range=[1,2],sublinear_tf=True),
    topics=topics,annual=annual,periods=period_rows)
(OUT/'topic_pilot.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
joblib.dump(dict(vectorizer=vectorizer,model=model,stops=stops),ROOT/'topic_model.joblib')
np.savez_compressed(ROOT/'pilot_arrays.npz',Q=Q,weights=weights,page_topic=page_topic,page_words=page_words,word_counts=word_counts,page_indices=page_indices,dominant=dominant)
with (ROOT/'passages.jsonl').open('w',encoding='utf-8') as f:
    for p in passages:
        f.write(json.dumps(p,ensure_ascii=False)+'\n')
print(f"Saved pilot; modeling and scoring {time.time()-start:.1f}s",flush=True)

