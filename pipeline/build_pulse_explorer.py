"""Build the local multi-group pulse page from the immutable research release."""
from pathlib import Path
import json, re, sqlite3, shutil, hashlib, datetime
from archive_data.consumer import release_path, verified_file

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'outputs/newspaper_pulses_space'
release=release_path()
manifest=json.loads((release/'manifest.json').read_text(encoding='utf8'))
# Display categories for the overview (an editorial grouping for colour, not part of the data release).
# Three colours are the most that stay distinguishable when any two can be on screen together.
CATEGORIES=[
    ('war','War, revolution and foreign news',['boyd-bantry-coverage','tenerife-defeat-report','camperdown-dispatches','algerine-sicilian-battle',
                                               'hermione-mutiny','barney-escapes-blockade','sonthonax-departure','quito-earthquake']),
    ('ships','Ships, privateers and wrecks',['peace-cayenne-context','peace-and-plenty-boarding','brothers-privateer-boarding','two-sisters-wreck','havana-french-captures']),
    ('public','American public life',['adams-senate-farewell','special-session-1797','blount-affair','brown-house-fire','congress-opening-nov-1797',
                                      'kosciuszko-land-warrant','jefferson-madison-letter','nh-governor-address-1797'])]
CHILDREN={'boyd-bantry-coverage':['boyd-core-report','fleet-return-account'],'peace-cayenne-context':['peace-seizure-report','cayenne-decree-commentary'],
          'peace-and-plenty-boarding':['peace-and-plenty-report'],'hermione-mutiny':['hermione-particulars'],
          'special-session-1797':['adams-special-session-speech','special-session-proclamation','special-session-house-answer'],
          'blount-affair':['blount-letter','blount-knoxville-welcome','blount-committee-report']}
# Focus-menu order: by category, each top-level story followed by its child groups.
group_ids=[g for _,_,tops in CATEGORIES for top in tops for g in [top]+CHILDREN.get(top,[])]
category_of={g:c for c,_,tops in CATEGORIES for top in tops for g in [top]+CHILDREN.get(top,[])}
short_names={'sn82014782':'Kentucky Gazette','sn83025525':'The Mirror','sn83025527':'Republican Gazetteer','sn83025588':'New Hampshire Gazette','sn83025881':'Gazette of the United States','sn84023150':'The Eagle','sn84024710':'Virginia Argus','sn84038410':'Patowmac Guardian'}
# Map layout: each series is placed at its town of publication (from the catalogue's places_json).
# Coordinates are present-day town centres (latitude, longitude), used only for display.
TOWNS=[('Portland, Me.',r'portland',43.661,-70.255),('Portsmouth, N.H.',r'portsmouth',43.071,-70.763),('Concord, N.H.',r'concord',43.208,-71.538),
       ('Exeter, N.H.',r'exeter',42.981,-70.948),('Dover, N.H.',r'dover,? n\.? ?h',43.198,-70.874),('Hanover, N.H.',r'hanover',43.702,-72.290),
       ('Keene, N.H.',r'keene',42.934,-72.278),('Newburyport, Mass.',r'newbury-?port',42.812,-70.877),('Salem, Mass.',r'salem',42.519,-70.897),
       ('Boston, Mass.',r'boston',42.360,-71.058),('Providence, R.I.',r'providence',41.824,-71.413),('Warren, R.I.',r'warren',41.730,-71.282),
       ('Newport, R.I.',r'newport',41.490,-71.313),('Hartford, Conn.',r'hartford',41.764,-72.685),('Kingston, N.Y.',r'kingston',41.927,-73.997),
       ('New York, N.Y.',r'new[- ]york',40.713,-74.006),('Chatham, N.J.',r'chatham',40.741,-74.383),('Burlington, N.J.',r'burlington',40.071,-74.865),
       # Pennsylvania Packet: "Lancaster, Pa.;Philadelphia, Pa." -- Lancaster only during the British occupation (1777-78).
       ('Philadelphia, Pa.',r'philadelphia',39.952,-75.165),('Wilmington, Del.',r'wilmington',39.746,-75.547),('Dover, Del.',r'dover,? del',39.158,-75.524),
       ('Washington, D.C.',r'washington',38.895,-77.036),('Alexandria, Va.',r'alexandria',38.805,-77.047),('Shepherdstown, W. Va.',r'shepherdstown',39.430,-77.804),
       ('Martinsburg, W. Va.',r'martinsburg',39.456,-77.964),('Wheeling, W. Va.',r'wheeling',40.064,-80.721),('Richmond, Va.',r'richmond',37.541,-77.436),
       ('Williamsburg, Va.',r'williamsburg',37.271,-76.707),('Norfolk, Va.',r'norfolk',36.851,-76.286),('Lynchburg, Va.',r'lynchburg',37.414,-79.142),
       ('Lexington, Ky.',r'lexington',38.040,-84.503),('Charleston, S.C.',r'charles-?town|charleston',32.777,-79.931)]
def town(places_json):
    raw='; '.join(json.loads(places_json)); low=raw.lower().replace('[','').replace(']','')
    hits=[t for t in TOWNS if re.search(t[1],low)]
    assert hits, 'No town coordinates for place: '+raw
    name,_,lat,lon=hits[0] if len(hits)==1 else next(t for t in hits if t[0].startswith('Philadelphia'))
    return {'place':name,'place_raw':raw,'lat':lat,'lon':lon}
boyd=json.loads(verified_file('views/pulse_boyd.json',release).read_text(encoding='utf8'))
old={o['observation_id']:o for o in boyd['observations']}
summaries={'H012':'A report of the seizure of Peace, attributed to Captain Whitney.','X016':'The Peace seizure report with additional Mercury-attributed commentary.','H013':'A translated Cayenne decree with an attached editorial allegation.'}
notes={'H012':'Publication date differs from the internal Providence dateline of May 13. The seizure date is not supplied.','X016':'The shared report and appended commentary are distinct textual elements. The commentary is not independently corroborated.','H013':'A contextual document, not an established legal cause of the Peace seizure. The original decree and itemized allegations remain unresolved.'}
OUT.mkdir(exist_ok=True);(OUT/'assets').mkdir(exist_ok=True)
observations={};groups=[]
with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    newspapers=[]
    for r in db.execute("SELECT n.*,COUNT(DISTINCT i.id) AS issues FROM newspapers n JOIN issues i ON i.newspaper_id=n.id WHERE i.publication_date LIKE '1797%' GROUP BY n.id ORDER BY n.lccn"):
        newspapers.append({'id':r['id'],'lccn':r['lccn'],'name':short_names[r['lccn']],'title':json.loads(r['titles_json'])[0],'issues_1797':r['issues'],**town(r['places_json'])})
    coverage=[dict(r) for r in db.execute("SELECT * FROM newspaper_date_coverage WHERE publication_date LIKE '1797%' ORDER BY publication_date,newspaper_id")]
    # Keep the same positions across groups; pilot papers occupy the first row.
    order=['sn84038410','sn83025588','sn82014782','sn83025881','sn83025525','sn84023150','sn83025527','sn84024710']
    newspapers.sort(key=lambda p:order.index(p['lccn']))
    for short in group_ids:
        g=dict(db.execute('SELECT * FROM groups WHERE id=?',('group:'+short,)).fetchone())
        rows=list(db.execute('SELECT * FROM group_publications WHERE group_id=? ORDER BY publication_date,newspaper_id,observation_id',(g['id'],)))
        g['members']=[]
        for r in rows:
            oid=r['observation_id'];g['members'].append({'id':oid,'roles':json.loads(r['roles_json'])})
            if oid in observations:continue
            assets=[]
            for a in db.execute('SELECT path FROM assets WHERE object_id=? ORDER BY path',(oid,)):
                path=verified_file(a['path'],release);shutil.copyfile(path,OUT/a['path']);assets.append(a['path'])
            o=dict(r);legacy=o['legacy_id'];prior=old.get(oid,{})
            # Selections added after v0.1.0 carry their summary and note in an observation_review annotation.
            review=db.execute("SELECT value_json FROM current_annotations WHERE object_id=? AND annotation_type='observation_review'",(oid,)).fetchone()
            review=json.loads(review[0]) if review else {}
            field=db.execute('SELECT transcription_field FROM observations WHERE id=?',(oid,)).fetchone()[0]
            observations[oid]={'id':oid,'legacy_id':legacy,'node':o['lccn'],'page_id':o['page_id'],'issue_id':o['issue_id'],'date':o['publication_date'],'page':o['page_number'],'excerpt':'\n\n'.join(json.loads(o['excerpts_json'])),'source_url':o['pinned_scan_url'],'scans':assets,'transcription':{'RevX_OCR_text':'RevX','ca_ocr_text':'CA'}[field],'summary':prior.get('summary',summaries.get(legacy,review.get('summary',''))),'note':prior.get('note',notes.get(legacy,review.get('note','')))}
        groups.append({**{k:g[k] for k in ['id','kind','label','definition','members']},'category':category_of[short],'child':short not in [t for _,_,tops in CATEGORIES for t in tops]})
    # Stories for the all-stories view: the top-level groups (no parent among the shown groups).
    children={r[0] for r in db.execute('SELECT child_id FROM group_hierarchy')}
    stories=[{'id':g['id'],'label':g['label'],'category':g['category'],'members':[m['id'] for m in g['members']]} for g in groups if g['id'] not in children]
assert {s['id'][6:] for s in stories}=={t for _,_,tops in CATEGORIES for t in tops}, 'Every top-level story needs exactly one display category'
stories.sort(key=lambda s:min(observations[m]['date'] for m in s['members']))
# Each passage must belong to exactly one story, so the overview never pulses a passage twice.
story_members=[m for s in stories for m in s['members']]
assert len(story_members)==len(set(story_members))==len(observations), 'Top-level stories must partition the passages'
categories=[{'id':c,'label':label,'stories':['group:'+t for t in tops]} for c,label,tops in CATEGORIES]
data={'release_version':manifest['version'],'year':1797,'newspapers':newspapers,'coverage':coverage,'groups':groups,'categories':categories,'stories':stories,'observations':list(observations.values()),'edges':[]}
assert len(newspapers)==8 and sum(c['observed_pages'] for c in coverage)==1587
assert len(observations)==len({m['id'] for g in groups for m in g['members']})
for o in observations.values():
    assert o['scans'] and o['excerpt'] and o['summary'] and o['date'].startswith('1797')
    paper_id=next(p['id'] for p in newspapers if p['lccn']==o['node'])
    assert any(c['newspaper_id']==paper_id and c['publication_date']==o['date'] for c in coverage)
for g in groups:assert len({m['id'] for m in g['members']})==len(g['members'])
# ---- All years: automatic reuse families (not checked against scans), one data file per year ----
import re, collections, sys
sys.path.insert(0,str(ROOT/'python_packages'))
import pyarrow.parquet as pq
REV='0b97906ad32e269376872934820357fc333151d8';DATASET='RevolutionCrossroads/loc_chronicling_america_1770-1810'
SMALL={'and','or','of','the','in','at','for','to','a'}
def short_name(lccn,title):
    if lccn in short_names: return short_names[lccn]
    t=re.sub(r'^\s*the\s+','',title.strip(),flags=re.I)
    t=re.split(r'[,;:(\[]|\. | and the | & the ',t)[0].strip(' .')
    head=re.split(r' and | & ',t)[0]
    if len(t)>32 and len(head.split())>=2: t=head  # "Kentucky gazette and general advertiser" -> "Kentucky gazette"
    words=[w if (i and w.lower() in SMALL) else w[:1].upper()+w[1:] for i,w in enumerate(t.split())]
    while len(' '.join(words))>32 and len(words)>1: words.pop()  # cut at a word boundary
    while len(words)>1 and words[-1].lower() in SMALL|{'&'}: words.pop()
    return ' '.join(words) or lccn
years_dir=OUT/'years';years_dir.mkdir(exist_ok=True)
fam_path=release/'derived/reuse_families.parquet'
families=pq.read_table(verified_file('derived/reuse_families.parquet',release)).to_pylist() if fam_path.exists() else []
# Automatic titles (v0.5.1 on): the item's opening words, plus a dateline place when printings agree.
story_titles={}
if (release/'derived/reuse_family_titles.parquet').exists():
    story_titles={t['family_id']:t['title'] for t in pq.read_table(verified_file('derived/reuse_family_titles.parquet',release),columns=['family_id','title']).to_pylist()}
apps_by=collections.defaultdict(list)
if families:
    for a in pq.read_table(verified_file('derived/reuse_family_appearances.parquet',release)).to_pylist(): apps_by[a['family_id']].append(a)
by_year=collections.defaultdict(list)
for f in families: by_year[int(f['first_date'][:4])].append(f)
years_index=[]
with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    titles={r['lccn']:(r['id'],json.loads(r['titles_json'])[0]) for r in db.execute('SELECT * FROM newspapers')}
    towns={r['lccn']:town(r['places_json']) for r in db.execute('SELECT lccn,places_json FROM newspapers')}
    for year in range(1770,1811):
        fams=sorted(by_year.get(year,[]),key=lambda f:(f['first_date'],-f['newspapers']))
        last=max([f['last_date'] for f in fams]+[f'{year}-12-31'])
        lccns=[r[0] for r in db.execute("SELECT DISTINCT n.lccn FROM newspapers n JOIN issues i ON i.newspaper_id=n.id WHERE i.publication_date LIKE ? ORDER BY n.lccn",(f'{year}%',))]
        if year==1797: lccns=[p['lccn'] for p in newspapers]+[l for l in lccns if l not in {p['lccn'] for p in newspapers}]
        extra_l=sorted({a['lccn'] for f in fams for a in apps_by[f['family_id']]}-set(lccns))
        papers=[{'id':titles[l][0],'lccn':l,'name':short_name(l,titles[l][1]),'title':titles[l][1],**towns[l]} for l in lccns+extra_l]
        # Some years hold several series with the same short name (title changes, rival printers): tell them apart.
        names=collections.Counter(p['name'] for p in papers)
        for p in papers:
            if names[p['name']]>1 and p['lccn'] not in short_names:
                full=' '.join(w[:1].upper()+w[1:] if w.lower().strip(',;') not in SMALL else w.lower() for w in re.sub(r'^\s*the\s+','',p['title'],flags=re.I).strip(' .').split())
                p['name']=full if len(full)<=60 and sum(q['title'].lower()==p['title'].lower() for q in papers)==1 else p['name']+' · '+p['lccn']
        names=collections.Counter(p['name'] for p in papers)
        for p in papers:
            if names[p['name']]>1 and p['lccn'] not in short_names: p['name']+=' · '+p['lccn']
        assert len({p['name'] for p in papers})==len(papers), f'{year}: newspaper names must be distinct'
        cov=[dict(r) for r in db.execute("SELECT * FROM newspaper_date_coverage WHERE publication_date BETWEEN ? AND ? ORDER BY publication_date,newspaper_id",(f'{year}-01-01',last))]
        # Compact rows: the page expands them (page and issue ids, scan URL, labels and notes are derived, not repeated).
        obs=[];grps=[];days={(c['newspaper_id'],c['publication_date']) for c in cov}
        for f in fams:
            members=[]
            for a in apps_by[f['family_id']]:
                _,lccn,date,ed,page=a['page_id'].split(':')
                assert (titles[lccn][0],date) in days, 'Every matched appearance joins to observed date coverage'
                oid=f"auto:{f['family_id']}:{a['seq']}"
                obs.append({'id':oid,'node':lccn,'date':date,'ed':int(ed),'page':int(page),'excerpt':a['excerpt'],'tr':a['transcription']})
                members.append(oid)
            grps.append({'id':'auto:'+f['family_id'],'label':story_titles.get(f['family_id'],f['label']),'newspapers':f['newspapers'],'first':f['first_date'],'last':f['last_date'],
                         'long_running':bool(f['long_running']),'members':members})
        (years_dir/f'{year}.json').write_text(json.dumps({'year':year,'scan_base':f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/',
                                                          'newspapers':papers,'coverage':cov,'groups':grps,'observations':obs},ensure_ascii=False,separators=(',',':')),encoding='utf8')
        years_index.append({'year':year,'reviewed':len(stories) if year==1797 else 0,'matched':len(fams),'matched3':sum(f['newspapers']>=3 for f in fams)})
# ---- Story telescope: every story as a star, placed by real values ----
# day = first printing (days since 1 Jan 1770); lat = mean latitude of the towns of the papers that printed it.
EPOCH=datetime.date(1770,1,1).toordinal()
dnum=lambda s:datetime.date.fromisoformat(s).toordinal()-EPOCH
stars=[]
cat_index={c['id']:i for i,c in enumerate(categories)}
for s in stories:
    obs_s=[observations[m] for m in s['members']]
    ls=sorted({o['node'] for o in obs_s})
    stars.append({'id':s['id'],'year':1797,'kind':1,'cat':cat_index[s['category']],'first':min(dnum(o['date']) for o in obs_s),'last':max(dnum(o['date']) for o in obs_s),
                  'papers':len(ls),'prints':len(obs_s),'lat':round(sum(towns[l]['lat'] for l in ls)/len(ls),3),'long':0,'title':s['label']})
for f in families:
    ls=sorted({a['lccn'] for a in apps_by[f['family_id']]})
    title=story_titles.get(f['family_id'],f['label'])
    stars.append({'id':f['family_id'],'year':int(f['first_date'][:4]),'kind':0,'cat':-1,'first':dnum(f['first_date']),'last':dnum(f['last_date']),
                  'papers':f['newspapers'],'prints':f['appearances'],'lat':round(sum(towns[l]['lat'] for l in ls)/len(ls),3),'long':int(bool(f['long_running'])),
                  'title':title if len(title)<=110 else title[:108].rstrip()+' …'})
# Story topics (release v0.5.2 on): the frozen 24-topic model applied to every printing; lanes in display order.
topic_rows,topic_list={},[]
if (release/'derived/story_topics.parquet').exists():
    topic_rows={r['story_id']:r for r in pq.read_table(verified_file('derived/story_topics.parquet',release),columns=['story_id','top_topic','top_share']).to_pylist()}
    with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db2:
        topic_meta=json.loads(db2.execute("SELECT value_json FROM metadata WHERE key='story_topics'").fetchone()[0])
    topic_list=sorted(topic_meta['topics'],key=lambda x:x['display_order'])
lane_of={x['id']:x['display_order'] for x in topic_list}
# Search text: the title plus the opening words of the first printing (lower case), loaded by the page only when searching.
first_excerpt={fid:min(apps,key=lambda a:a['seq'])['excerpt'] for fid,apps in apps_by.items()}
for s in stories:
    first_excerpt[s['id']]=min((observations[m] for m in s['members']),key=lambda o:o['date'])['excerpt']
first_town={fid:towns[min(apps,key=lambda a:(a['publication_date'],a['seq']))['lccn']] for fid,apps in apps_by.items()}
for s in stories:
    first_town[s['id']]=towns[min((observations[m] for m in s['members']),key=lambda o:o['date'])['node']]
town_count=collections.Counter()
for s in stars:
    ft=first_town[s['id']]; s['flat']=ft['lat']; s['flon']=ft['lon']; town_count[ft['place']]+=1
for s in stars:
    r=topic_rows.get(s['id'])
    s['topic']=lane_of[r['top_topic']] if r else -1; s['tconf']=round(r['top_share'],2) if r else 0
    s['text']=re.sub(r'\s+',' ',(s['title']+' '+(first_excerpt.get(s['id']) or '')).replace('ſ','s')).lower().strip()
stars.sort(key=lambda s:(s['first'],-s['papers'],s['id']))
tele={'epoch':'1770-01-01','count':len(stars),**{k:[s[k] for s in stars] for k in ['id','year','kind','cat','first','last','papers','prints','lat','long','title','topic','tconf','flat','flon']},
      'topics':[{'id':x['id'],'label':' · '.join(x['terms'][:3])} for x in topic_list]}
(OUT/'telescope.json').write_text(json.dumps(tele,ensure_ascii=False,separators=(',',':')),encoding='utf8')
(OUT/'telescope-text.json').write_text(json.dumps({'count':len(stars),'text':[s['text'] for s in stars]},ensure_ascii=False,separators=(',',':')),encoding='utf8')
tele_stamp=hashlib.sha256((OUT/'telescope.json').read_bytes()+(OUT/'telescope-text.json').read_bytes()).hexdigest()[:12]
tele_boot={'release_version':manifest['version'],'stamp':tele_stamp,'stories':len(stars),
           # Sizes as served, so the loading bar can measure progress even when the server compresses the files.
           'bytes':{'data':(OUT/'telescope.json').stat().st_size,'text':(OUT/'telescope-text.json').stat().st_size},
           'towns':[{'name':n.split(',')[0],'lat':la,'lon':lo,'stories':town_count[n]} for n,_,la,lo in TOWNS if town_count[n]],'categories':[{'label':c['label'],'color':col} for c,col in zip(categories,['#3987e5','#d95926','#199e70'])]}
# ---- The site: five pages sharing one header and footer (work/site_parts.py, work/site.css) ----
from site_parts import fill, REPO
from urllib.parse import quote
VER=manifest['version']; N_STARS=len(stars)
shutil.copyfile(ROOT/'site.css',OUT/'site.css')
tele_html=(ROOT/'telescope.html').read_text(encoding='utf8').replace('__TELESCOPE_BOOT__',json.dumps(tele_boot,ensure_ascii=False).replace('</','<\\/'))
assert '__TELESCOPE_BOOT__' not in tele_html
(OUT/'telescope.html').write_text(fill(tele_html,'telescope',VER,N_STARS),encoding='utf8')
# A stamp of the year files' contents, so browsers fetch fresh copies after a rebuild.
year_stamp=hashlib.sha256(b''.join(hashlib.sha256((years_dir/f'{y}.json').read_bytes()).digest() for y in range(1770,1811))).hexdigest()[:12]
boot={'release_version':VER,'reviewed':data,'years':years_index,'year_stamp':year_stamp}
payload=json.dumps(boot,ensure_ascii=False).replace('</','<\\/')
html=(ROOT/'pulse_explorer.html').read_text(encoding='utf8').replace('__PULSE_DATA__',payload)
assert '__PULSE_DATA__' not in html
(OUT/'pulses.html').write_text(fill(html,'pulses',VER,N_STARS),encoding='utf8')
(OUT/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')

# Home: featured stories, the archive in numbers, and a small sample of stars for the hero sky.
by_id={s['id']:s for s in stars}
when=lambda s:datetime.date.fromordinal(EPOCH+s['first']).strftime('%B %Y')
peace=by_id['group:peace-and-plenty-boarding']
decl=max((s for s in stars if s['kind']==0 and s['year']==1776 and 'declaration by the representatives' in s['title'].lower()),key=lambda s:s['papers'])
pulse_link=lambda s:f"pulses.html?year={s['year']}&focus={quote(s['id'] if s['kind'] else 'auto:'+s['id'])}"
sky_link=lambda s:f"telescope.html?story={quote(s['id'])}"
search_link=lambda q:f"telescope.html?view=orbit&q={quote(q)}"
featured=[
  {'title':'A privateer boards the Peace and Plenty','meta':f"{when(peace)} · {peace['papers']} newspapers · {peace['prints']} printings",'reviewed':True,
   'text':"Captain Dunbar's account of a French privateer boarding his brig, printed in three papers and retold in a fourth. Every printing was checked against its scan.",
   'links':[['Follow the story',pulse_link(peace)],['See it in the sky',sky_link(peace)]]},
  {'title':'The Declaration of Independence','meta':f"{when(decl)} · {decl['papers']} newspapers · {decl['prints']} printings",'reviewed':False,
   'text':'Found automatically by its shared wording in the papers that survive, like every matched story. Not yet checked against the scans.',
   'links':[['Follow the story',pulse_link(decl)],['See it in the sky',sky_link(decl)]]},
  {'title':'Fever comes back in summer','meta':'41 years · a search','reviewed':False,
   'text':'Reports of yellow and malignant fever cluster in July to September in most years. The Orbit view shows the season.',
   'links':[['See the rhythm',search_link('yellow fever, malignant fever, prevailing fever')]]},
  {'title':'Independence Day, every July','meta':'41 years · a search','reviewed':False,
   'text':'Accounts of the Fourth of July come back each summer, in most years of the archive. The Orbit view shows the season.',
   'links':[['See the rhythm',search_link('anniversary of independence, fourth of july, 4th of july')]]}]
numbers=[[f"{manifest['counts']['eligible_pages']:,}",'pages read'],[str(manifest['counts']['newspapers']),'newspaper series'],['41','years'],
         [f"{len(families):,}",'matched stories'],[str(len(stories)),'reviewed stories (1797)'],[f"{sum(f['appearances'] for f in families):,}",'printings found']]
sample=sorted((s for s in stars if not s['long']),key=lambda s:(-s['papers'],-s['prints'],s['first']))[:4500]
sample.sort(key=lambda s:s['first'])
palette=['rgba(170,182,207,A)','rgba(57,135,229,A)','rgba(217,89,38,A)','rgba(25,158,112,A)']
home_data={'featured':featured,'numbers':numbers,'towns':tele_boot['towns'],'palette':palette,
           'sky':{'day':[s['first'] for s in sample],'lat':[s['flat'] for s in sample],'lon':[s['flon'] for s in sample],'papers':[s['papers'] for s in sample],
                  'color':[s['cat']+1 if s['kind'] else 0 for s in sample]}}
home=(ROOT/'home.html').read_text(encoding='utf8').replace('__HOME_DATA__',json.dumps(home_data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
home=home.replace('__N_STORIES__',f'{N_STARS:,}').replace('__FEATURED_PULSE__',pulse_link(peace))
(OUT/'index.html').write_text(fill(home,'home',VER,N_STARS),encoding='utf8')

# How it works and Research notes.
fill_text=lambda s:(s.replace('__N_STORIES__',f'{N_STARS:,}').replace('__N_MATCHED__',f'{len(families):,}')
                     .replace('__N_PRINTINGS__',f"{sum(f['appearances'] for f in families):,}").replace('__RELEASE__',VER).replace('__REPO__',REPO))
(OUT/'method.html').write_text(fill(fill_text((ROOT/'method.html').read_text(encoding='utf8')),'method',VER,N_STARS),encoding='utf8')
(OUT/'notes.html').write_text(fill(fill_text((ROOT/'notes.html').read_text(encoding='utf8')),'notes',VER,N_STARS),encoding='utf8')
def copy_with_assets(src,dest):
    """Copy a report and the local files it links to (images, data), keeping their relative paths.
    The site is English only, so links to Chinese quick-read files are dropped from the copy."""
    dest.mkdir(parents=True,exist_ok=True)
    page=re.sub(r'\s*·\s*<a href="[^"]*\.zh-CN\.md">[^<]*</a>','',src.read_text(encoding='utf8'))
    (dest/src.name).write_text(page,encoding='utf8')
    for ref in set(re.findall(r'(?:src|href)="([^"#?]+)"',page)):
        if re.match(r'^(?:[a-z]+:|//)',ref) or '.zh-CN.' in ref: continue
        f=src.parent/ref
        if f.is_file(): (dest/ref).parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(f,dest/ref)
shutil.rmtree(OUT/'notes',ignore_errors=True)   # notes/ is generated: start clean, so no stale file lingers
copy_with_assets(ROOT.parent/'outputs/attention_pilot_report.html',OUT/'notes/attention')
copy_with_assets(ROOT.parent/'outputs/reading_evidence_2026-11-03/reading_notebook.html',OUT/'notes/reading')
for leftover in [m for m in ['__N_STORIES__','__N_MATCHED__','__N_PRINTINGS__','__RELEASE__','__REPO__','__HOME_DATA__','__FEATURED_PULSE__']
                 for page in ['index.html','method.html','notes.html'] if m in (OUT/page).read_text(encoding='utf8')]:
    raise AssertionError('Unfilled placeholder '+leftover)

pages={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['index.html','telescope.html','pulses.html','method.html','notes.html','site.css']}
receipt={'passed':True,'release_version':VER,'newspapers':len(newspapers),'curated_passages':len(observations),'group_views':len(groups),'stories_in_overview':len(stories),'overview_categories':len(categories),
         'years':len(years_index),'matched_families':len(families),'year_files_mb':round(sum(p.stat().st_size for p in years_dir.glob('*.json'))/1e6,1),'telescope_stars':len(stars),'telescope_mb':round((OUT/'telescope.json').stat().st_size/1e6,1),'telescope_text_mb':round((OUT/'telescope-text.json').stat().st_size/1e6,1),'story_topic_lanes':len(topic_list),'edges':0,
         'checks':['All displayed sources have scan assets and excerpts','All displayed publications join to observed date coverage','No duplicate observation within a group','Read-only release with verified input hashes','Matched families are labelled as not checked against scans','Every page carries the shared header and footer'],
         'pages_sha256':pages}
(OUT/'build_validation.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(receipt,indent=2))
