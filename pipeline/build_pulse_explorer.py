"""Build the local multi-group pulse page from the immutable research release."""
from pathlib import Path
import json, re, sqlite3, shutil, hashlib, datetime
from archive_data.consumer import release_path, verified_file
import time


# On this Windows machine another process (a scanner or an indexer) sometimes holds a file for a moment, and writing it
# fails with EINVAL or EACCES. Writes are tried again a few times instead of failing the whole build.
def _again(write):
    def go(self, *a, **k):
        for attempt in range(6):
            try:
                return write(self, *a, **k)
            except OSError as e:
                if attempt == 5 or e.errno not in (13, 22):
                    raise
                time.sleep(.5)
    return go


Path.write_text = _again(Path.write_text)
Path.write_bytes = _again(Path.write_bytes)


def copy_if_changed(src, dst):
    """Copy src to dst unless dst already holds the same bytes. Rewriting every unchanged scan crop on each build sometimes
    failed on Windows (EINVAL while another process held the file for a moment), and it was never needed."""
    src, dst = Path(src), Path(dst)
    if dst.exists() and dst.stat().st_size == src.stat().st_size and dst.read_bytes() == src.read_bytes():
        return
    for attempt in range(5):
        try:
            shutil.copyfile(src, dst); return
        except OSError:
            if attempt == 4: raise
            time.sleep(.5)

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'outputs/newspaper_pulses_space'
release=release_path()
manifest=json.loads((release/'manifest.json').read_text(encoding='utf8'))
# The reviewed years. Each has display categories for its overview (an editorial grouping for colour, not part of the
# data release), named for that year, in the same three colour slots: the first is war in both years and the third
# American public life and government. Three colours are the most that stay distinguishable when any two can be on screen
# together. Every top-level story of a reviewed year needs exactly one category, or the build fails. 'children' lists the
# sub-stories shown under a story; 'expect' is the year's newspapers and surviving pages, checked against the release.
REVIEWED={
  # Round two (release v0.7.2) added nine stories; the user agreed the categories on 2026-11-09, with the Howe declarations
  # under Britain and Europe. Each category lists its stories in the order of their first printing.
  1776:{'categories':[
          ('war','War and the armies',['quebec-siege-1776','boston-evacuation-letter','barry-takes-edward','sloop-liberty-gunpowder','hopkins-nassau-letter',
                                       'campbell-captured-letter','hudson-warships-1776','washington-patterson-interview','eighty-eight-battalions',
                                       'congress-intelligence-october-1776','gates-carleton-retreat']),
          ('britain','Britain and Europe',['king-speech-october-1775','wilkes-speech-commons','penn-before-the-lords','prohibitory-bill-commons',
                                           'dublin-paper-naval-force','ethan-allen-cork','london-address-to-king-1776','king-speech-may-1776','howe-declarations-1776']),
          ('government','Independence and American government',['congress-bills-of-credit','congress-fast-day-1776','congress-opens-ports','rhode-island-renunciation',
                                       'congress-may-15-resolution','virginia-independence-resolution','pennsylvania-new-instructions','declaration-of-independence',
                                       'cedars-cartel-report','prize-resolutions-extended','staten-island-conference'])],
        'children':{'quebec-siege-1776':['montgomery-letter-to-carleton','quebec-assault-report','quebec-camp-letter'],
                    'hudson-warships-1776':['haverstraw-bay-report','tappan-meadows-report','gondolas-attack-report','fire-ships-attack-report'],
                    'staten-island-conference':['conference-committee-departs','conference-committee-report'],
                    'penn-before-the-lords':['penn-examined-report','penn-examination-lords'],
                    'prohibitory-bill-commons':['prohibitory-bill-committee','prohibitory-clause-settled'],
                    'howe-declarations-1776':['howe-declaration-published-by-congress','howe-declaration-september']},
        'expect':(16,2319)},
  1797:{'categories':[
          ('war','War, revolution and foreign news',['boyd-bantry-coverage','tenerife-defeat-report','camperdown-dispatches','algerine-sicilian-battle',
                                                     'hermione-mutiny','barney-escapes-blockade','sonthonax-departure','quito-earthquake']),
          ('ships','Ships, privateers and wrecks',['peace-cayenne-context','peace-and-plenty-boarding','brothers-privateer-boarding','two-sisters-wreck','havana-french-captures']),
          ('public','American public life',['adams-senate-farewell','special-session-1797','blount-affair','brown-house-fire','congress-opening-nov-1797',
                                            'kosciuszko-land-warrant','jefferson-madison-letter','nh-governor-address-1797'])],
        'children':{'boyd-bantry-coverage':['boyd-core-report','fleet-return-account'],'peace-cayenne-context':['peace-seizure-report','cayenne-decree-commentary'],
                    'peace-and-plenty-boarding':['peace-and-plenty-report'],'hermione-mutiny':['hermione-particulars'],
                    'special-session-1797':['adams-special-session-speech','special-session-proclamation','special-session-house-answer'],
                    'blount-affair':['blount-letter','blount-knoxville-welcome','blount-committee-report']},
        'expect':(8,1587),
        'order':['sn84038410','sn83025588','sn82014782','sn83025881','sn83025525','sn84023150','sn83025527','sn84024710']},   # the pilot papers first
  # The third reviewed year (release v0.8.0, page shifts corrected in v0.8.1): 14 stories. The user agreed the proposed
  # categories on 2026-11-10 ("可以，上线 1807"); the Chesapeake affair is with the ships, as a top-level story takes one category.
  1807:{'categories':[
          ('war','War in Europe',['lubeck-stormed','harford-jones-russian-army','bennigsen-pultusk-account','bulletin-66','bulletin-78','armistice-france-russia']),
          ('ships','Britain, France and American ships',['monroe-pinkney-treaty-letter','driver-at-charleston','chesapeake-affair-1807','douglas-and-the-mayor-of-norfolk',
                                                         'antwerp-letter-capture-order','britain-answer-peace-or-war']),
          ('government','American public life and government',['burr-conspiracy-1807','special-session-1807'])],
        'children':{'burr-conspiracy-1807':['burr-conspiracy-message','burr-in-arms-new-orleans','marshall-commitment-opinion','burr-treason-verdict','marshall-october-opinion'],
                    'driver-at-charleston':['kalteisen-letter-driver','driver-answer-charleston'],
                    'chesapeake-affair-1807':['chesapeake-attack-account','july-2-proclamation','berkeley-order','chesapeake-court-of-inquiry','house-report-chesapeake'],
                    'douglas-and-the-mayor-of-norfolk':['douglas-letter-3-july','mayor-answer-4-july','tazewell-report','douglas-letter-6-july'],
                    'special-session-1807':['proclamation-convening-congress','president-message-october-27']},
        'expect':(11,4162)},   # v0.10.2 dated one Kentucky Gazette issue filed under 1807 to 1805
  # The fourth reviewed year (release v0.9.0): 20 stories. Categories as proposed by the review; the owner agreed on
  # 2026-11-10 ("Follow your recommendations on the data review. And then publish all").
  1808:{'categories':[
          ('war','War in Spain and Portugal',['latest-from-portugal-dec-1807','alicante-letters-1808','charles-iv-appoints-murat','order-in-council-4-july',
                                              'arcturus-news-from-spain','reding-dispatch-baylen','conventions-in-portugal']),
          ('ships','Britain, France and American ships',['decrees-on-neutral-trade','algiers-1808','papers-before-congress-march-1808','canning-on-america-24-june']),
          ('government','The embargo and American government',['embargo-laws','wilkinson-accused','president-message-25-feb-military-force','embargo-in-force-spring-1808',
                                              'adams-resigns-senate','jefferson-answers-new-hampshire','jefferson-answer-embargo-petitions','message-8-november',
                                              'foreign-relations-report-22-november'])],
        'children':{'embargo-laws':['embargo-act-22-dec-1807','embargo-supplementary-act-9-jan','embargo-additional-act-12-march','embargo-suspension-act-22-april','embargo-act-25-april'],
                    'wilkinson-accused':['wilkinson-randolph-letters','clark-statement-on-wilkinson','president-message-20-jan-wilkinson','wilkinson-court-of-inquiry'],
                    'decrees-on-neutral-trade':['orders-in-council-11-nov-1807','amsterdam-letter-milan-decree','british-instructions-11-april'],
                    'algiers-1808':['algiers-war-report','lear-circular-peace-with-algiers','dey-of-algiers-june'],
                    'papers-before-congress-march-1808':['president-message-22-march','canning-monroe-chesapeake-correspondence','rose-madison-letters','champagny-letter-15-jan'],
                    'embargo-in-force-spring-1808':['georgia-letter-mobile-pensacola','proclamation-lake-champlain','president-circular-governors-6-may'],
                    'alicante-letters-1808':['alicante-letter-aranjuez-rumour','alicante-letter-guards-ordered'],
                    'conventions-in-portugal':['russian-fleet-tagus-convention','cintra-convention'],
                    'message-8-november':['message-8-november-text','canning-to-pinkney-23-september','armstrong-letter-28-august','madison-to-erskine-25-march']},
        'expect':(10,4060)},   # v0.10.2 dated the 98 Kentucky Gazette issues filed under 1808 to 1806
  # The fifth reviewed year (releases v0.10.0 and v0.10.1): 12 stories. The owner agreed a 6-paper threshold for 1793 (fewer
  # papers survive) and the proposed categories on 2026-11-10 ("Follow your recommendations on the data review").
  1793:{'categories':[
          ('war','The war in Europe',['emigrant-armies-disbanded','dumouriez-letter-brussels','powers-at-war-with-france-list','dumouriez-defection-1793',
                                      'tournai-bulletin-3-may','death-of-general-dampierre','convention-president-declaration-plot','cadiz-letter-24-june',
                                      'madeira-report-battle-near-lisle']),
          ('ships','Ships and the sea',['sea-serpent-captain-crabtree','treasury-circular-rules-on-neutrality']),
          ('public','American public life',['genet-appeal-to-the-people-1793'])],
        'children':{'dumouriez-defection-1793':['clairfayt-letter-tournay','sun-rumour-dumouriez-left-army','dumouriez-address-french-nation','cobourg-proclamation-5-april'],
                    'genet-appeal-to-the-people-1793':['jay-king-statement-on-genet','genet-letter-to-the-president-13-august','jefferson-answer-to-genet-16-august']},
        'expect':(12,1751)}}
CATEGORY_COLORS=['#3987e5','#d95926','#199e70']   # dataviz slots 1-3, validated all-pairs on #050711
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
# Regions colour the telescope's stars by the town where each story was first printed in this archive, grouped as the
# early republic grouped its states. Three hues at most: the stars form a scatter, where any two colours can meet, and only
# three categorical hues stay distinguishable there for colour-blind readers (dataviz check, all pairs, on #050711).
REGIONS=[('New England','Maine, New Hampshire, Massachusetts, Rhode Island and Connecticut','#9085e9',{'Me.','N.H.','Mass.','R.I.','Conn.','Vt.'}),
         ('Middle States','New York, New Jersey, Pennsylvania and Delaware','#199e70',{'N.Y.','N.J.','Pa.','Del.'}),
         ('South and West','Washington, Virginia (with today\'s West Virginia), Kentucky and South Carolina','#d95926',{'D.C.','Va.','W. Va.','Ky.','S.C.'})]
def region_of(place):
    state_abbr=place.split(', ',1)[1]
    found=[i for i,r in enumerate(REGIONS) if state_abbr in r[3]]
    assert len(found)==1, 'Give this town a region in REGIONS: '+place
    return found[0]
for t in TOWNS: region_of(t[0])
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
import collections, sys
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
def name_papers(papers):
    """Make newspaper names distinct within one set (a year, or all years): some years hold several series with the same
    short name (title changes, rival printers)."""
    names=collections.Counter(p['name'] for p in papers)
    for p in papers:
        if names[p['name']]>1 and p['lccn'] not in short_names:
            full=' '.join(w[:1].upper()+w[1:] if w.lower().strip(',;') not in SMALL else w.lower() for w in re.sub(r'^\s*the\s+','',p['title'],flags=re.I).strip(' .').split())
            p['name']=full if len(full)<=60 and sum(q['title'].lower()==p['title'].lower() for q in papers)==1 else p['name']+' · '+p['lccn']
    names=collections.Counter(p['name'] for p in papers)
    for p in papers:
        if names[p['name']]>1 and p['lccn'] not in short_names: p['name']+=' · '+p['lccn']
    assert len({p['name'] for p in papers})==len(papers), 'newspaper names must be distinct'
    return papers
# ---- The reviewed years: stories read and grouped by hand, every printing checked against its scan ----
observations={};stories=[];reviewed_data={}
with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    titles={r['lccn']:(r['id'],json.loads(r['titles_json'])[0]) for r in db.execute('SELECT * FROM newspapers')}
    towns={r['lccn']:town(r['places_json']) for r in db.execute('SELECT lccn,places_json FROM newspapers')}
    # Newspaper names, distinct over all years: the same names as in the all-years index below.
    paper_name={p['lccn']:p['name'] for p in name_papers([{'lccn':l,'name':short_name(l,t),'title':t} for l,(_,t) in sorted(titles.items())])}
    children={r[0] for r in db.execute('SELECT child_id FROM group_hierarchy')}
    for year,spec in sorted(REVIEWED.items()):
        tops=[t for _,_,ts in spec['categories'] for t in ts]
        shown=[g for t in tops for g in [t]+spec['children'].get(t,[])]   # by category: each top-level story, then its sub-stories
        cat_of={g:f'{year}-{c}' for c,_,ts in spec['categories'] for t in ts for g in [t]+spec['children'].get(t,[])}
        released={r[0][6:] for r in db.execute('SELECT DISTINCT group_id FROM group_publications WHERE publication_date LIKE ?',(f'{year}%',))}
        assert released==set(shown) and len(shown)==len(set(shown)), \
            f'{year}: list every reviewed group of the year once (not listed: {sorted(released-set(shown))}; not in the release: {sorted(set(shown)-released)})'
        papers=[{'id':r['id'],'lccn':r['lccn'],'name':paper_name[r['lccn']],'title':titles[r['lccn']][1],'issues':r['issues'],**towns[r['lccn']]}
                for r in db.execute('SELECT n.id,n.lccn,COUNT(DISTINCT i.id) AS issues FROM newspapers n JOIN issues i ON i.newspaper_id=n.id WHERE i.publication_date LIKE ? GROUP BY n.id ORDER BY n.lccn',(f'{year}%',))]
        if 'order' in spec: papers.sort(key=lambda p:spec['order'].index(p['lccn']))
        coverage=[dict(r) for r in db.execute('SELECT * FROM newspaper_date_coverage WHERE publication_date LIKE ? ORDER BY publication_date,newspaper_id',(f'{year}%',))]
        assert (len(papers),sum(c['observed_pages'] for c in coverage))==spec['expect'], f"{year}: newspapers and surviving pages differ from {spec['expect']}"
        groups=[];year_obs={}
        for short in shown:
            g=dict(db.execute('SELECT * FROM groups WHERE id=?',('group:'+short,)).fetchone())
            rows=list(db.execute('SELECT * FROM group_publications WHERE group_id=? ORDER BY publication_date,newspaper_id,observation_id',(g['id'],)))
            g['members']=[]
            for r in rows:
                oid=r['observation_id'];g['members'].append({'id':oid,'roles':json.loads(r['roles_json'])})
                if oid in year_obs:continue
                assets=[]
                for a in db.execute('SELECT path FROM assets WHERE object_id=? ORDER BY path',(oid,)):
                    path=verified_file(a['path'],release);copy_if_changed(path,OUT/a['path']);assets.append(a['path'])
                o=dict(r);legacy=o['legacy_id'];prior=old.get(oid,{})
                # Selections added after v0.1.0 carry their summary and note in an observation_review annotation.
                review=db.execute("SELECT value_json FROM current_annotations WHERE object_id=? AND annotation_type='observation_review'",(oid,)).fetchone()
                review=json.loads(review[0]) if review else {}
                field=db.execute('SELECT transcription_field FROM observations WHERE id=?',(oid,)).fetchone()[0]
                year_obs[oid]={'id':oid,'legacy_id':legacy,'node':o['lccn'],'page_id':o['page_id'],'issue_id':o['issue_id'],'date':o['publication_date'],'page':o['page_number'],'excerpt':'\n\n'.join(json.loads(o['excerpts_json'])),'source_url':o['pinned_scan_url'],'scans':assets,'transcription':{'RevX_OCR_text':'RevX','ca_ocr_text':'CA'}[field],'summary':prior.get('summary',summaries.get(legacy,review.get('summary',''))),'note':prior.get('note',notes.get(legacy,review.get('note','')))}
            groups.append({**{k:g[k] for k in ['id','kind','label','definition','members']},'category':cat_of[short],'child':short not in tops})
        # The year's overview plays its top-level stories (groups with no parent).
        year_stories=[{'id':g['id'],'label':g['label'],'category':g['category'],'members':[m['id'] for m in g['members']]} for g in groups if g['id'] not in children]
        assert {s['id'][6:] for s in year_stories}==set(tops), f'{year}: every top-level story needs exactly one display category'
        year_stories.sort(key=lambda s:min(year_obs[m]['date'] for m in s['members']))
        # Each passage must belong to exactly one story, so the overview never pulses a passage twice.
        members=[m for s in year_stories for m in s['members']]
        assert len(members)==len(set(members))==len(year_obs), f'{year}: top-level stories must partition the passages'
        for o in year_obs.values():
            assert o['scans'] and o['excerpt'] and o['summary'] and o['date'].startswith(str(year))
            paper_id=next(p['id'] for p in papers if p['lccn']==o['node'])
            assert any(c['newspaper_id']==paper_id and c['publication_date']==o['date'] for c in coverage)
        for g in groups: assert len({m['id'] for m in g['members']})==len(g['members'])
        assert not set(year_obs)&set(observations), 'a passage belongs to one reviewed year'
        observations.update(year_obs); stories+=[{**s,'year':year} for s in year_stories]
        reviewed_data[year]={'year':year,'newspapers':papers,'coverage':coverage,'groups':groups,
                             'categories':[{'id':f'{year}-{c}','label':label,'stories':['group:'+t for t in ts]} for c,label,ts in spec['categories']],
                             'stories':year_stories,'observations':list(year_obs.values())}
reviewed_list=[reviewed_data[y] for y in sorted(reviewed_data)]
# ---- All years: automatic reuse families (not checked against scans), one data file per year ----
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
# Transcription checks (v0.6.0 on): whether each printing's passage is also in the page's other machine transcription.
# Stored per observation in the year files as one letter; the pulse page says it in words.
CHECK_CODE={'confirmed':'c','partly':'p','missing_in_other':'m','other_unreadable':'u','no_second_transcription':'n'}
printing_checks={}
if (release/'derived/transcription_checks.parquet').exists():
    printing_checks={(r['family_id'],r['seq']):CHECK_CODE[r['status']] for r in pq.read_table(verified_file('derived/transcription_checks.parquet',release),columns=['family_id','seq','status']).to_pylist()}
    assert len(printing_checks)==sum(len(v) for v in apps_by.values()), 'every printing needs exactly one transcription check'
    assert all(len({a['page_id'] for a in v})==len(v) for v in apps_by.values()), 'one printing per story and page'
by_year=collections.defaultdict(list)
for f in families: by_year[int(f['first_date'][:4])].append(f)
years_index=[]
with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    for year in range(1770,1811):
        fams=sorted(by_year.get(year,[]),key=lambda f:(f['first_date'],-f['newspapers']))
        last=max([f['last_date'] for f in fams]+[f'{year}-12-31'])
        lccns=[r[0] for r in db.execute("SELECT DISTINCT n.lccn FROM newspapers n JOIN issues i ON i.newspaper_id=n.id WHERE i.publication_date LIKE ? ORDER BY n.lccn",(f'{year}%',))]
        if year in reviewed_data:   # a reviewed year keeps its papers in the reviewed order
            first=[p['lccn'] for p in reviewed_data[year]['newspapers']]; lccns=first+[l for l in lccns if l not in first]
        extra_l=sorted({a['lccn'] for f in fams for a in apps_by[f['family_id']]}-set(lccns))
        papers=name_papers([{'id':titles[l][0],'lccn':l,'name':short_name(l,titles[l][1]),'title':titles[l][1],**towns[l]} for l in lccns+extra_l])
        cov=[dict(r) for r in db.execute("SELECT * FROM newspaper_date_coverage WHERE publication_date BETWEEN ? AND ? ORDER BY publication_date,newspaper_id",(f'{year}-01-01',last))]
        # Compact rows: the page expands them (page and issue ids, scan URL, labels and notes are derived, not repeated).
        obs=[];grps=[];days={(c['newspaper_id'],c['publication_date']) for c in cov}
        for f in fams:
            members=[]
            for a in apps_by[f['family_id']]:
                _,lccn,filed,ed,page=a['page_id'].split(':'); date=a['publication_date']   # the printed date; the id keeps the filed one
                assert (titles[lccn][0],date) in days, 'Every matched appearance joins to observed date coverage'
                oid=f"auto:{f['family_id']}:{a['seq']}"
                obs.append({'id':oid,'node':lccn,'date':date,**({'fd':filed} if filed!=date else {}),'ed':int(ed),'page':int(page),'excerpt':a['excerpt'],'tr':a['transcription'],
                            **({'ck':printing_checks[f['family_id'],a['seq']]} if printing_checks else {})})
                members.append(oid)
            grps.append({'id':'auto:'+f['family_id'],'label':story_titles.get(f['family_id'],f['label']),'newspapers':f['newspapers'],'first':f['first_date'],'last':f['last_date'],
                         'long_running':bool(f['long_running']),'members':members})
        (years_dir/f'{year}.json').write_text(json.dumps({'year':year,'scan_base':f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/',
                                                          'newspapers':papers,'coverage':cov,'groups':grps,'observations':obs},ensure_ascii=False,separators=(',',':')),encoding='utf8')
        # The year strip on the pulse page: how many newspapers and pages survive each year (the archive's shape).
        pages_y=db.execute("SELECT COUNT(*) FROM pages p JOIN issues i ON i.id=p.issue_id WHERE i.publication_date LIKE ?",(f'{year}%',)).fetchone()[0]
        years_index.append({'year':year,'reviewed':len(reviewed_data[year]['stories']) if year in reviewed_data else 0,'matched':len(fams),'matched3':sum(f['newspapers']>=3 for f in fams),
                            'papers':len(set(lccns)),'pages':pages_y})
# ---- Story telescope: every story as a star, placed by real values ----
# day = first printing (days since 1 Jan 1770); lat = mean latitude of the towns of the papers that printed it.
EPOCH=datetime.date(1770,1,1).toordinal()
dnum=lambda s:datetime.date.fromisoformat(s).toordinal()-EPOCH
# Each reviewed story's twin in the matched layer: the automatic story that holds at least half of its printings (same
# newspaper, printed date and page). They are one story found twice, so the sky draws it once (the reviewed star), links
# to the twin reach the reviewed story, and the Pulses shelf lists it once. 85 of the 98 stories had one on 2026-11-11.
page_owner=collections.defaultdict(set)
for fid,apps in apps_by.items():
    for a in apps: page_owner[(a['lccn'],a['publication_date'],int(a['page_id'].split(':')[4]))].add(fid)
twins={};paired=[]
for s in stories:
    obs_s=[observations[m] for m in s['members']]
    c=collections.Counter(f for o in obs_s for f in page_owner.get((o['node'],o['date'],int(o['page'])),()))
    if c:
        fid,k=min(c.items(),key=lambda x:(-x[1],x[0]))   # ties go to the first id, so every build pairs the same way
        if k*2>=len(obs_s): paired.append(s['id']); twins.setdefault(fid,s['id'])   # two reviewed stories can share one automatic story
print(f'twins: {len(paired)} of {len(stories)} reviewed stories have one; {len(twins)} matched stories are twins')
assert len(paired)>=80, f'only {len(paired)} reviewed stories found their matched twin'
stars=[]
# Reviewed stars carry their year's category: one list over all reviewed years, each category in its year's colour slot.
tele_cats=[{'id':c['id'],'label':c['label'],'year':y,'slot':i,'color':CATEGORY_COLORS[i]} for y in sorted(reviewed_data) for i,c in enumerate(reviewed_data[y]['categories'])]
cat_index={c['id']:i for i,c in enumerate(tele_cats)}
for s in stories:
    obs_s=[observations[m] for m in s['members']]
    ls=sorted({o['node'] for o in obs_s})
    stars.append({'id':s['id'],'year':s['year'],'kind':1,'cat':cat_index[s['category']],'first':min(dnum(o['date']) for o in obs_s),'last':max(dnum(o['date']) for o in obs_s),
                  'papers':len(ls),'prints':len(obs_s),'lat':round(sum(towns[l]['lat'] for l in ls)/len(ls),3),'long':0,'title':s['label']})
for f in families:
    if f['family_id'] in twins: continue   # drawn as its reviewed star
    ls=sorted({a['lccn'] for a in apps_by[f['family_id']]})
    title=story_titles.get(f['family_id'],f['label'])
    stars.append({'id':f['family_id'],'year':int(f['first_date'][:4]),'kind':0,'cat':-1,'first':dnum(f['first_date']),'last':dnum(f['last_date']),
                  'papers':f['newspapers'],'prints':f['appearances'],'lat':round(sum(towns[l]['lat'] for l in ls)/len(ls),3),'long':int(bool(f['long_running'])),
                  'title':title if len(title)<=110 else title[:108].rstrip()+' …'})
# Story topics (release v0.5.2 on): the frozen 24-topic model applied to every printing; lanes in display order.
topic_rows,topic_list={},[]
if (release/'derived/story_topics.parquet').exists():
    topic_rows={r['story_id']:r for r in pq.read_table(verified_file('derived/story_topics.parquet',release),columns=['story_id','top_topic','top_share','second_topic']).to_pylist()}
    with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db2:
        topic_meta=json.loads(db2.execute("SELECT value_json FROM metadata WHERE key='story_topics'").fetchone()[0])
    topic_list=sorted(topic_meta['topics'],key=lambda x:x['display_order'])
# The Topic view groups the 24 topics into the seven reviewed (provisional) families of the first study, with plain names.
# The families are not used for colour: a spot check (8 Nov 2026) found that among matched stories the model's notice and
# "other" families mostly hold news (fires, bridges, courts), because advertisements were rarely reprinted across papers.
# Each family: (name in the study, short name, name for phones).
FAMILIES=[('Politics and public institutions','Politics','Politics'),('War, diplomacy and shipping','War, diplomacy and shipping','War and ships'),
          ('Commerce, property and everyday transactions','Commerce and property','Commerce'),('Law, debt and taxation','Law, debt and taxes','Law and debt'),
          ('Coercion and escape','Escape and capture','Escape'),('Literature and reflection','Poetry and reflection','Poetry'),
          ('Formats and unresolved clusters','Formats and mixed','Mixed')]
SHORT={'T01':'Political argument','T02':'Laws and statutes','T03':'Shipping and ports','T04':'Cloth and dry goods','T05':'Stray horses',
       'T06':'Federal government','T07':'Land for sale','T08':'Court orders','T09':'Battles and armies','T10':'Estates and debts',
       'T11':'France and Europe','T12':'Legislatures','T13':'Places, mixed','T14':'Poetry and reflection','T15':'Lotteries and money',
       'T16':'Escape and capture notices','T17':'Food and drink for sale','T18':'Name lists','T19':'Letter extracts','T20':'Crown and Parliament',
       'T21':'Britain and America','T22':'Shops and premises','T23':'Land-tax sales','T24':'Insolvent estates'}
topic_labels=json.loads(verified_file('sources/work__topic_labels.json',release).read_text(encoding='utf8'))
topic_rel={json.loads(l)['id'].split(':')[-1]:json.loads(l) for l in verified_file('tables/topics.jsonl',release).read_text(encoding='utf8').splitlines() if l.strip()}
fam_index={f[0]:i for i,f in enumerate(FAMILIES)}
tid=lambda x:x['id'].split(':')[-1]
assert topic_list and all(tid(x) in SHORT and topic_labels[tid(x)]['category'] in fam_index for x in topic_list), 'every topic needs a short name and a family'
topic_list.sort(key=lambda x:(fam_index[topic_labels[tid(x)]['category']],x['display_order']))   # by family, then by shared vocabulary
lane_of={x['id']:i for i,x in enumerate(topic_list)}
# Search text: the title plus the opening words of the first printing (lower case), loaded by the page only when searching.
first_excerpt={fid:min(apps,key=lambda a:a['seq'])['excerpt'] for fid,apps in apps_by.items()}
for s in stories:
    first_excerpt[s['id']]=min((observations[m] for m in s['members']),key=lambda o:o['date'])['excerpt']
first_town={fid:towns[min(apps,key=lambda a:(a['publication_date'],a['seq']))['lccn']] for fid,apps in apps_by.items()}
for s in stories:
    first_town[s['id']]=towns[min((observations[m] for m in s['members']),key=lambda o:o['date'])['node']]
town_count=collections.Counter()
for s in stars:
    ft=first_town[s['id']]; s['flat']=ft['lat']; s['flon']=ft['lon']; s['reg']=region_of(ft['place']); town_count[ft['place']]+=1
for s in stars:
    r=topic_rows.get(s['id'])
    s['topic']=lane_of[r['top_topic']] if r else -1; s['tconf']=round(r['top_share'],2) if r else 0
    s['topic2']=lane_of.get(r['second_topic'],s['topic']) if r else -1   # the second-strongest topic: which way a mixed story leans
    s['text']=re.sub(r'\s+',' ',(s['title']+' '+(first_excerpt.get(s['id']) or '')).replace('ſ','s')).lower().strip()
stars.sort(key=lambda s:(s['first'],-s['papers'],s['id']))
tele={'epoch':'1770-01-01','count':len(stars),**{k:[s[k] for s in stars] for k in ['id','year','kind','cat','first','last','papers','prints','lat','long','title','topic','topic2','tconf','flat','flon','reg']},
      'topics':[{'id':x['id'],'label':SHORT[tid(x)],'name':topic_labels[tid(x)]['label'],'family':fam_index[topic_labels[tid(x)]['category']],
                 'provisional':topic_rel[tid(x)]['restart_agreement']<0.6,'terms':' · '.join(x['terms'][:3])} for x in topic_list],
      'families':[{'name':f,'short':s,'tiny':t} for f,s,t in FAMILIES]}
(OUT/'telescope.json').write_text(json.dumps(tele,ensure_ascii=False,separators=(',',':')),encoding='utf8')
(OUT/'telescope-text.json').write_text(json.dumps({'count':len(stars),'text':[s['text'] for s in stars]},ensure_ascii=False,separators=(',',':')),encoding='utf8')
tele_stamp=hashlib.sha256((OUT/'telescope.json').read_bytes()+(OUT/'telescope-text.json').read_bytes()).hexdigest()[:12]
# ---- Trace: the words of a story's title worth following through the years (the story card's "Trace a word") ----
# Counted the way the telescope's search finds them: at the start of a word, in the title and the opening words. A word
# is offered when its stories are spread over the years, or over the months, unlike the sky's stories as a whole (a
# G-test, p < .001 with 40 and 11 degrees of freedom), so that tracing it shows more than the archive's coverage. Each
# word keeps its number of stories and a score (how far its spread differs, shrunk for small numbers), which orders a
# title's words on the card. The pages split a title into words the same way (titleWords in both pages).
TRACE_STOP=set('''that with this from have been were which their there they them then than what when where will would shall
should could into upon unto your yours ours more most some such other others only also very much many each every both after
before about above below under over again further once here hers himself herself itself themselves those these being having
doing does done same just while during against between through without within along among until because since though
although whether either neither cannot made make makes making said says following extract letter letters dated date
gentleman gentlemen received receive arrived arrive informed inform learn learned hear heard yesterday today last next first
second third days week weeks month months year years time times morning evening night january february march april june july
august september october november december sept monday tuesday wednesday thursday friday saturday sunday inst instant ultimo
messrs sirs cent copy published publish printed print paper papers account accounts news intelligence advices advice late
lately former latter public publick great well good part whole number'''.split())
def title_words(t):
    return {w for w in re.findall(r'[a-z]+',re.sub(r"['’]s\b",'',t.lower().replace('ſ','s'))) if len(w)>=4 and w not in TRACE_STOP}
import bisect, math
post=collections.defaultdict(list)
for i,s in enumerate(stars):
    for tok in set(re.findall(r'[a-z]+',s['text'])): post[tok].append(i)
toks=sorted(post)
year_of=[s['year'] for s in stars]
month_of=[(datetime.date(1770,1,1)+datetime.timedelta(days=s['first'])).month for s in stars]
year_all,month_all,n_all=collections.Counter(year_of),collections.Counter(month_of),len(stars)
def g_test(obs,base,n): return 2*sum(o*math.log(o*n_all/(n*base[k])) for k,o in obs.items() if o)
trace_words={}
for w in sorted(set().union(*(title_words(s['title']) for s in stars))):
    a,b=bisect.bisect_left(toks,w),bisect.bisect_left(toks,w+'{')
    if sum(len(post[t]) for t in toks[a:b])<3: continue
    hit_ix=set().union(*(post[t] for t in toks[a:b])); n=len(hit_ix)
    if not 3<=n<=3000: continue
    gy=g_test(collections.Counter(year_of[i] for i in hit_ix),year_all,n); gm=g_test(collections.Counter(month_of[i] for i in hit_ix),month_all,n)
    if gy<73.4 and gm<31.3: continue   # spread like the archive: its trace would show the archive's coverage
    trace_words[w]=[n,round(1000*max(gy,gm*40/11)/(2*(n+30)))]
(OUT/'trace.json').write_text(json.dumps({'words':trace_words},ensure_ascii=False,separators=(',',':')),encoding='utf8')
trace_stamp=hashlib.sha256((OUT/'trace.json').read_bytes()).hexdigest()[:12]
trace_cover=sum(1 for s in stars if title_words(s['title'])&trace_words.keys())
print(f'trace: {len(trace_words):,} words; {trace_cover:,} of {len(stars):,} stories have at least one')
assert trace_cover>=.9*len(stars), 'most stories should offer a word to trace'
reg_count=collections.Counter(s['reg'] for s in stars)
tele_boot={'release_version':manifest['version'],'stamp':tele_stamp,'trace':trace_stamp,'stories':len(stars),'twins':twins,
           # The archive under the timeline, as on the Pulses year strip: [year, newspapers with surviving pages, pages, reviewed stories].
           'years':[[y['year'],y['papers'],y['pages'],y['reviewed']] for y in years_index],
           'regions':[{'label':label,'states':states,'color':color,'stories':reg_count[i]} for i,(label,states,color,_) in enumerate(REGIONS)],
           # Sizes as served, so the loading bar can measure progress even when the server compresses the files.
           'bytes':{'data':(OUT/'telescope.json').stat().st_size,'text':(OUT/'telescope-text.json').stat().st_size},
           'towns':[{'name':n.split(',')[0],'lat':la,'lon':lo,'stories':town_count[n]} for n,_,la,lo in TOWNS if town_count[n]],'categories':[{'label':c['label'],'year':c['year'],'color':c['color']} for c in tele_cats]}
# ---- The site: five pages sharing one header and footer (work/site_parts.py, work/site.css) ----
from site_parts import fill, REPO
from urllib.parse import quote
VER=manifest['version']; N_STARS=len(stars)
shutil.copyfile(ROOT/'site.css',OUT/'site.css')
shutil.copyfile(ROOT/'glass.js',OUT/'glass.js')   # the glass controls shared by the Telescope and Pulses pages
shutil.copyfile(ROOT/'radio.js',OUT/'radio.js')   # the radio's voice and sounds, made in the browser (Radio page, Pulses, Telescope)
tele_html=(ROOT/'telescope.html').read_text(encoding='utf8').replace('__TELESCOPE_BOOT__',json.dumps(tele_boot,ensure_ascii=False).replace('</','<\\/'))
assert '__TELESCOPE_BOOT__' not in tele_html
(OUT/'telescope.html').write_text(fill(tele_html,'telescope',VER,N_STARS),encoding='utf8')
# ---- All years in one slim index, for pulse views of several years (any stretch of 1770-1810) ----
# The year files carry every passage. This index carries only what the map and the story shelf need: the newspapers,
# the stories (title, reach, dates, topic), the printings (newspaper, day, edition, page, transcription check) and the
# surviving pages. A passage loads from its year file when it is opened.
with sqlite3.connect(verified_file('research.sqlite',release).as_uri()+'?mode=ro',uri=True) as db3:
    db3.row_factory=sqlite3.Row
    cov_all=[dict(r) for r in db3.execute("SELECT newspaper_id,publication_date,observed_pages,observed_issues_editions FROM newspaper_date_coverage ORDER BY publication_date,newspaper_id")]
id_to_lccn={v[0]:k for k,v in titles.items()}
all_l=sorted({id_to_lccn[c['newspaper_id']] for c in cov_all}|{a['lccn'] for v in apps_by.values() for a in v})
idx_papers=name_papers([{'id':titles[l][0],'lccn':l,'name':short_name(l,titles[l][1]),'title':titles[l][1],**towns[l]} for l in all_l])
pix={p['lccn']:i for i,p in enumerate(idx_papers)}
assert all(p['name']==paper_name[p['lccn']] for p in idx_papers), 'a newspaper has one name in every view'
S_={k:[] for k in ['id','label','papers','first','last','long','topic','off','n']};P_={k:[] for k in ['p','d','e','g','q']};checks=[];P_fd={}   # fd: filed days that differ from the printed day
for f in sorted(families,key=lambda f:(f['first_date'],-f['newspapers'],f['family_id'])):   # stories in date order, so a stretch of years is one slice
    fid=f['family_id'];apps=[]
    for a in apps_by[fid]:
        _,lccn,filed,ed,page=a['page_id'].split(':');apps.append((dnum(a['publication_date']),lccn,int(ed),int(page),a['seq'],dnum(filed)))
    apps.sort();r=topic_rows.get(fid);title=story_titles.get(fid,f['label'])
    for k,v in (('id',fid),('label',title if len(title)<=100 else title[:98].rstrip()+' …'),('papers',f['newspapers']),('first',dnum(f['first_date'])),('last',dnum(f['last_date'])),
                ('long',int(bool(f['long_running']))),('topic',lane_of[r['top_topic']] if r else -1),('off',len(P_['p'])),('n',len(apps))): S_[k].append(v)
    for d,lccn,ed,page,seq,fd in apps:
        if fd!=d: P_fd[str(len(P_['p']))]=fd
        P_['p'].append(pix[lccn]);P_['d'].append(d);P_['e'].append(ed);P_['g'].append(page);P_['q'].append(seq)
        checks.append(printing_checks.get((fid,seq),'-') if printing_checks else '-')
assert len(P_['p'])==sum(len(v) for v in apps_by.values()), 'the index holds every printing once'
index={'epoch':'1770-01-01','scan_base':f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/','papers':idx_papers,'stories':S_,'printings':{**P_,'c':''.join(checks),'fd':P_fd},
       'coverage':{'p':[pix[id_to_lccn[c['newspaper_id']]] for c in cov_all],'d':[dnum(c['publication_date']) for c in cov_all],
                   'pages':[c['observed_pages'] for c in cov_all],'issues':[c['observed_issues_editions'] for c in cov_all]}}
(years_dir/'index.json').write_text(json.dumps(index,ensure_ascii=False,separators=(',',':')),encoding='utf8')
# A stamp of the year files' contents (and the index), so browsers fetch fresh copies after a rebuild.
year_stamp=hashlib.sha256(b''.join(hashlib.sha256((years_dir/f'{y}.json').read_bytes()).digest() for y in range(1770,1811))+hashlib.sha256((years_dir/'index.json').read_bytes()).digest()).hexdigest()[:12]
boot={'release_version':VER,'reviewed':reviewed_list,'years':years_index,'year_stamp':year_stamp,'trace':trace_stamp,'twins':twins,'index_bytes':(years_dir/'index.json').stat().st_size,
      # Topics for the story shelf's chips: each topic's plain name and family (as in the telescope).
      'topics':[{'label':SHORT[tid(x)],'family':fam_index[topic_labels[tid(x)]['category']]} for x in topic_list],
      'families':[{'name':f,'short':s,'tiny':t} for f,s,t in FAMILIES]}
payload=json.dumps(boot,ensure_ascii=False).replace('</','<\\/')
html=(ROOT/'pulse_explorer.html').read_text(encoding='utf8').replace('__PULSE_DATA__',payload)
assert '__PULSE_DATA__' not in html
(OUT/'pulses.html').write_text(fill(html,'pulses',VER,N_STARS),encoding='utf8')
(OUT/'data.json').write_text(json.dumps({'release_version':VER,'reviewed':reviewed_list},ensure_ascii=False,indent=2),encoding='utf8')
# The radio: a year dial over the surviving papers of each year. It reads the year files and data.json, read aloud in the browser.
radio_boot={'release_version':VER,'year_stamp':year_stamp,'years':[{k:y[k] for k in ('year','papers','pages','matched','reviewed')} for y in years_index],
            'reviewed_years':sorted(reviewed_data)}
radio=(ROOT/'radio.html').read_text(encoding='utf8').replace('__RADIO_DATA__',json.dumps(radio_boot,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
assert '__RADIO_DATA__' not in radio
(OUT/'radio.html').write_text(fill(radio,'radio',VER,N_STARS),encoding='utf8')

# Home: featured stories, the archive in numbers, and a small sample of stars for the hero sky.
by_id={s['id']:s for s in stars}
when=lambda s:datetime.date.fromordinal(EPOCH+s['first']).strftime('%B %Y')
peace=by_id['group:peace-and-plenty-boarding']
decl=by_id['group:declaration-of-independence']   # reviewed in data release v0.7.0
day_text=lambda d:datetime.date.fromordinal(EPOCH+d).strftime('%d %B %Y').lstrip('0')
assert day_text(decl['first'])=='6 July 1776', 'The Declaration card says its first printing came two days after it was adopted'
pulse_link=lambda s:f"pulses.html?year={s['year']}&focus={quote(s['id'] if s['kind'] else 'auto:'+s['id'])}"
sky_link=lambda s:f"telescope.html?story={quote(s['id'])}"
search_link=lambda q:f"telescope.html?view=orbit&q={quote(q)}"
featured=[
  {'title':'A privateer boards the Peace and Plenty','meta':f"{when(peace)} · {peace['papers']} newspapers · {peace['prints']} printings",'reviewed':True,
   'text':"Captain Dunbar's account of a French privateer boarding his brig, printed in three papers and retold in a fourth. Every printing was checked against its scan.",
   'links':[['Follow the story',pulse_link(peace)],['See it in the sky',sky_link(peace)]]},
  {'title':'The Declaration of Independence','meta':f"{when(decl)} · {decl['papers']} newspapers · {decl['prints']} printings",'reviewed':True,
   'text':f"First printed in this archive on {day_text(decl['first'])}, two days after Congress adopted it, and in {decl['papers']} papers by {day_text(decl['last'])[:-5]}. Every printing was checked against its scan.",
   'links':[['Follow the story',pulse_link(decl)],['See it in the sky',sky_link(decl)]]},
  {'title':'Fever comes back in summer','meta':'41 years · a search','reviewed':False,
   'text':'Reports of yellow and malignant fever cluster in July to September in most years. The Orbit view shows the season.',
   'links':[['See the rhythm',search_link('yellow fever, malignant fever, prevailing fever')]]},
  {'title':'Independence Day, every July','meta':'41 years · a search','reviewed':False,
   'text':'Accounts of the Fourth of July come back each summer, in most years of the archive. The Orbit view shows the season.',
   'links':[['See the rhythm',search_link('anniversary of independence, fourth of july, 4th of july')]]}]
numbers=[[f"{manifest['counts']['eligible_pages']:,}",'pages read'],[str(manifest['counts']['newspapers']),'newspaper series'],['41','years'],
         [f"{len(families):,}",'matched stories'],[str(len(stories)),'reviewed stories ('+', '.join(map(str,sorted(reviewed_data)))+')'],[f"{sum(f['appearances'] for f in families):,}",'printings found']]
sample=sorted((s for s in stars if not s['long']),key=lambda s:(-s['papers'],-s['prints'],s['first']))[:4500]
sample.sort(key=lambda s:s['first'])
palette=['rgba(170,182,207,A)','rgba(57,135,229,A)','rgba(217,89,38,A)','rgba(25,158,112,A)']
home_data={'featured':featured,'numbers':numbers,'towns':tele_boot['towns'],'palette':palette,
           'sky':{'day':[s['first'] for s in sample],'lat':[s['flat'] for s in sample],'lon':[s['flon'] for s in sample],'papers':[s['papers'] for s in sample],
                  'color':[tele_cats[s['cat']]['slot']+1 if s['kind'] else 0 for s in sample]}}
home=(ROOT/'home.html').read_text(encoding='utf8').replace('__HOME_DATA__',json.dumps(home_data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
home=home.replace('__N_STORIES__',f'{N_STARS:,}').replace('__FEATURED_PULSE__',pulse_link(peace))
(OUT/'index.html').write_text(fill(home,'home',VER,N_STARS),encoding='utf8')

# Exhibition: a self-running loop of scenes, each a page in its exhibition mode (?exhibit=1), for a large screen.
# The scenes follow docs/site-plan.md (phase 2); each links to the same view on the web for the QR code.
from site_parts import PAGES
fever_q,july_q='yellow fever, malignant fever, prevailing fever','anniversary of independence, fourth of july, 4th of july'
exhibit_scenes=[
  {'title':f'A sky of {N_STARS:,} stories','seconds':75,
   'text':'Every story printed in at least two newspapers of this archive, 1770–1810. Each star sits where its story was first printed. Time runs into the distance: the front is now, and the further away a star is, the earlier the story.',
   'url':'telescope.html?exhibit=1&view=place&lookback=10&year=1780&drift=on','link':'telescope.html?view=place&lookback=10&year=1780'},
  {'title':'A privateer boards the Peace and Plenty','seconds':60,
   'text':"Captain Dunbar's account of a French privateer boarding his brig, printed in three papers in 1797 and retold in a fourth. Each pulse is one newspaper printing it on its date; every printing was checked against its scan.",
   'url':pulse_link(peace)+'&exhibit=1&speed=7&radio=on','link':pulse_link(peace)},
  {'title':'The Declaration of Independence','seconds':60,
   'text':f"First printed in this archive on {day_text(decl['first'])}, two days after Congress adopted it, and in {decl['papers']} papers by {day_text(decl['last'])[:-5]}. The radio reads the first printing.",
   'url':pulse_link(decl)+'&exhibit=1&speed=7&radio=on','link':pulse_link(decl)},
  {'title':'Some news returns with the seasons','seconds':60,
   'text':'Independence Day in amber, fever in blue. Time of year runs around the ring, and each turn of the spiral is a year; the coloured lines show the months. The Fourth of July comes back every summer, and fever reports cluster in late summer.',
   'url':f"telescope.html?exhibit=1&view=orbit&lookback=all&colour=search&drift=off&q={quote(july_q+' vs '+fever_q)}",'link':f"telescope.html?view=orbit&lookback=all&q={quote(july_q+' vs '+fever_q)}"},
  {'title':'What the papers talked about','seconds':55,
   'text':"The same stars arranged by topic and seen from the side: each wedge is one of the 24 topics of the project's topic model, and time runs from the front to the back.",
   'url':'telescope.html?exhibit=1&view=topic&angle=side&lookback=10&year=1800&drift=on','link':'telescope.html?view=topic&angle=side&lookback=10&year=1800'},
  {'title':'What is missing','seconds':45,
   'text':'Only two newspaper series survive for 1785–86, against 11 to 17 a year after 1800. A thin sky is a gap in the surviving archive, not silence in the towns.',
   'url':'telescope.html?exhibit=1&view=place&lookback=5&year=1789&drift=off','link':'telescope.html?view=place&lookback=5&year=1789'},
  {'title':'The radio: a morning in 1776','seconds':120,
   'text':'Any day from 1770 to 1810, read aloud: a greeting to the town, then what its newspapers printed that morning. The voices are recorded and modern; the sounds are atmosphere, not recordings of the time.',
   'url':'radio.html?exhibit=1&year=1776&date=07-06&on=1','link':'radio.html?year=1776&date=07-06'}]
assert all(y['papers'] for y in years_index if y['year'] in (1780,1789,1800)), 'every exhibition year has surviving papers'
exhibit=(ROOT/'exhibit.html').read_text(encoding='utf8').replace('__EXHIBIT_DATA__',json.dumps({'pages':PAGES,'scenes':exhibit_scenes},ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
assert '__EXHIBIT_DATA__' not in exhibit
(OUT/'exhibit.html').write_text(fill(exhibit,'exhibit',VER,N_STARS),encoding='utf8')

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

pages={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['index.html','telescope.html','pulses.html','radio.html','exhibit.html','method.html','notes.html','site.css','glass.js','radio.js']}
# The radio's recorded voices (work/audio_render.py writes audio/ next to the pages; this build leaves it alone). Report
# how many reviewed passages have a recording; a passage without one is read by the browser's voice on the Radio page, and introduced by the announcer elsewhere.
audio_summary=None
if (OUT/'audio'/'index.json').exists():
    ai=json.loads((OUT/'audio'/'index.json').read_text(encoding='utf8')); clips=ai.get('clips',{})
    obs_ids=[o['id'] for d in reviewed_list for o in d['observations']]
    audio_summary={'clips':len(clips),'packs':len(ai.get('packs',[])),'mb':round(sum(f.stat().st_size for f in (OUT/'audio').rglob('*.mp3'))/1e6,1),
                   'reviewed_passages_recorded':sum(('p:'+i) in clips for i in obs_ids),'reviewed_passages':len(obs_ids),
                   'titles_recorded':sum(k.startswith('t:') for k in clips),'announcer_clips':sum(k.startswith('a:') for k in clips)}
receipt={'passed':True,'release_version':VER,
         'reviewed_years':[{'year':y,'newspapers':len(d['newspapers']),'passages':len(d['observations']),'group_views':len(d['groups']),'stories':len(d['stories']),'categories':len(d['categories'])} for y,d in sorted(reviewed_data.items())],
         'curated_passages':len(observations),'group_views':sum(len(d['groups']) for d in reviewed_list),'stories_in_overview':len(stories),'overview_categories':len(tele_cats),
         'years':len(years_index),'matched_families':len(families),'reviewed_twins':len(twins),'sky_stars':len(stars),'trace_words':len(trace_words),'trace_stories':trace_cover,'year_files_mb':round(sum((years_dir/f'{y}.json').stat().st_size for y in range(1770,1811))/1e6,1),'year_index_mb':round((years_dir/'index.json').stat().st_size/1e6,1),'telescope_stars':len(stars),'telescope_mb':round((OUT/'telescope.json').stat().st_size/1e6,1),'telescope_text_mb':round((OUT/'telescope-text.json').stat().st_size/1e6,1),'story_topic_lanes':len(topic_list),'edges':0,
         'checks':['All displayed sources have scan assets and excerpts','All displayed publications join to observed date coverage','No duplicate observation within a group','Read-only release with verified input hashes','Matched families are labelled as not checked against scans','Every page carries the shared header and footer',
                   'Each reviewed year lists every one of its groups once, and every top-level story has a display category']
                  +(['Every matched printing carries its transcription check, one printing per page'] if printing_checks else []),
         'matched_printings':sum(len(v) for v in apps_by.values()),
         'recorded_voices':audio_summary,
         'pages_sha256':pages}
(OUT/'build_validation.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(receipt,indent=2))
