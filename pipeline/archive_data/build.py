"""Build a versioned research data release from existing, pinned project inputs.

This is a migration, not new historical research or an event census.
"""
from pathlib import Path
import collections
import datetime as dt
import hashlib
import json
import re
import shutil
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
WORK = PROJECT/'work'
OUT = PROJECT/'outputs'
sys.path.insert(0, str(WORK/'python_packages'))
import pyarrow as pa
import pyarrow.parquet as pq

VERSION = '0.1.0'
RELEASE = OUT/'data_foundation'/('v'+VERSION)
DATE = '2026-11-05'
REV = '0b97906ad32e269376872934820357fc333151d8'
DATASET = 'RevolutionCrossroads/loc_chronicling_america_1770-1810'
DB = RELEASE/'research.sqlite'
J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
read = lambda path: json.loads((PROJECT/path).read_text(encoding='utf8'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()

def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def normalized(text):
    return re.sub(r'\s+', ' ', re.sub(r'(?<=\w)-\s+(?=\w)', '', text or '').replace('ſ','s')).strip()

def page_id(key): return 'page:'+key.replace('|', ':')
def page_version(key): return page_id(key)+'@'+REV
def observation_id(namespace, legacy): return 'obs:'+namespace+':'+legacy

def main():
    manifest_path = RELEASE/'manifest.json'
    if manifest_path.exists() and json.loads(manifest_path.read_text())['status']=='released':
        raise SystemExit('This release is immutable. Increment VERSION for changed inputs or annotations.')
    RELEASE.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(J({'status':'draft','version':VERSION}), encoding='utf8')
    for folder in ['sources','assets','derived','tables','views','schemas']:
        (RELEASE/folder).mkdir(exist_ok=True)
    if DB.exists(): DB.unlink()  # Only this unreleased, generated database.
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.executescript((HERE/'schema.sql').read_text())
    source_ids = {}

    def insert(table, **values):
        db.execute(f'INSERT INTO {table} ({",".join(values)}) VALUES ({",".join("?" for _ in values)})', tuple(values.values()))

    def source(path, kind='project_input', copy=True, url=None, expected=None):
        path = Path(path)
        if not path.is_absolute(): path = PROJECT/path
        relative = path.relative_to(PROJECT).as_posix()
        if relative in source_ids: return source_ids[relative]
        digest = file_sha(path)
        if expected and digest!=expected: raise ValueError('Input hash mismatch: '+relative)
        sid = 'source:'+sha(relative+'@'+digest)[:24]
        target = 'sources/'+relative.replace('/', '__') if copy else '../../../'+relative
        if copy: shutil.copyfile(path, RELEASE/target)
        insert('sources',id=sid,path=target,sha256=digest,bytes=path.stat().st_size,kind=kind,url=url,verification='sha256_verified_at_build')
        source_ids[relative] = sid
        return sid

    def obj(oid, kind, label):
        db.execute('INSERT OR IGNORE INTO objects VALUES (?,?,?)',(oid,kind,label))

    def annotation(aid, oid, kind, value, run, sid, pointer):
        insert('annotations',id=aid,object_id=oid,annotation_type=kind,value_json=J(value),run_id=run,
               source_id=sid,source_pointer=pointer,supersedes_id=None,recorded_date=DATE)
        return aid

    src_manifest = read('work/source_manifest.json')
    assert src_manifest['revision']==REV
    source('work/source_manifest.json')
    source('work/archive_data/build.py','build_code')
    source('work/archive_data/validate.py','validation_code')
    source('work/archive_data/examples.sql','query_examples')
    source('work/archive_data/README.md','documentation')
    schema_source = source('work/archive_data/schema.sql','schema')
    audit_source = source('work/page_audit.parquet','page_audit')
    audit_code = source('work/audit_dataset.py','analysis_code')
    chain_source = source('outputs/chain_pilot.json','legacy_evidence_ledger')
    rel_source = source('outputs/relations_1793_1800.json','legacy_relation_ledger')
    review_source = source('outputs/research_review_2026-11-02/evidence_review.json','review_ledger')
    pulse_source = source('outputs/reading_evidence_2026-11-03/pulse_seed.json','prototype_seed')
    source('outputs/reading_evidence_2026-11-03/peace_case.json','case_record')
    source('outputs/reading_evidence_2026-11-03/peace_search_review.json','candidate_dispositions')
    source('outputs/reading_evidence_2026-11-03/passage_matches.json','reuse_candidates')
    source('outputs/reading_evidence_2026-11-03/reuse_results.json','reuse_sensitivity')
    source('outputs/research_review_2026-11-02/trend_review.json','trend_sensitivity')
    for entry in src_manifest['files']:
        path=WORK/'data'/Path(entry['path']).name
        source(path,'raw_parquet',copy=False,expected=entry['lfs']['oid'],url=f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/{entry["path"]}')
        print('Verified raw shard',path.name,flush=True)

    for rid,method,params,sid,reviewer in [
      ('run:eligibility-v1','Existing page eligibility audit',{'word_pattern':r"[A-Za-z]+(?:['-][A-Za-z]+)*",'minimum_words':200,'priority':['RevX','CA'],'duplicate_pages_excluded':True,'years':[1770,1810]},audit_code,'automated'),
      ('run:import-review','Import of the existing same-assistant scan/evidence review',{'review_completed':'2026-11-03','new_scan_review':False},review_source,'same_ai_assistant'),
      ('run:foundation-v1','Structural migration and explicit group refinement',{'release':VERSION,'new_historical_findings':False,'retains_all_repeated_publications':True},schema_source,'same_ai_assistant')]:
        insert('runs',id=rid,method=method,parameters_json=J(params),source_id=sid,recorded_date=DATE,reviewer_kind=reviewer,independent_review=0)

    audit=pq.read_table(WORK/'page_audit.parquet').to_pylist()
    by_key={r['key']:r for r in audit}
    assert len(by_key)==len(audit)==77793
    papers=collections.defaultdict(list)
    for r in audit: papers[r['lccn']].append(r)
    for lccn,rows in sorted(papers.items()):
        insert('newspapers',id='paper:'+lccn,lccn=lccn,titles_json=J(sorted(set(r['newspaper_title'] for r in rows))),places_json=J(sorted(set(r['place_of_publication'] for r in rows))))
    issue_ids=set()
    for r in audit:
        iid='issue:'+':'.join([r['lccn'],r['issue_date'],str(r['edition_order'])])
        if iid not in issue_ids:
            insert('issues',id=iid,newspaper_id='paper:'+r['lccn'],publication_date=r['issue_date'],edition=r['edition_order']);issue_ids.add(iid)
        scan=f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/{r["lccn"]}/{r["issue_date"]}_{r["edition_order"]}_{r["Page"]}.pdf?download=true'
        insert('pages',id=page_id(r['key']),issue_id=iid,page_number=r['Page'],legacy_page_key=r['key'],issue_url=r['Web_URL'],pinned_scan_url=scan,original_scan_url=r['pdf_url'])
        insert('page_versions',id=page_version(r['key']),page_id=page_id(r['key']),dataset_revision=REV,shard_source_id=source_ids['work/data/'+r['file']],shard_row=r['file_row'])
        insert('page_assessments',page_version_id=page_version(r['key']),run_id='run:eligibility-v1',eligible=int(r['eligible']),selected_text_field={'RevX':'RevX_OCR_text','CA':'ca_ocr_text','none':None}[r['selected_source']],selected_words=r['selected_words'],revx_words=r['revx_words'],ca_words=r['ca_words'],duplicate_key=int(r['duplicate_key']),duplicate_scan=int(r['duplicate_scan']),selected_normalized_text_sha256=r['text_hash'])
    print('Indexed',len(audit),'pages and',len(issue_ids),'issues/editions',flush=True)

    chain=read('outputs/chain_pilot.json');rels=read('outputs/relations_1793_1800.json');review=read('outputs/research_review_2026-11-02/evidence_review.json')
    wanted={v['key'] for v in chain['versions']}|{r['source']['page_key'] for r in rels['records']}
    raw={}
    locations=collections.defaultdict(dict)
    for key in wanted:
        r=by_key[key];locations[r['file']][r['file_row']]=key
    for name,lookup in locations.items():
        pf=pq.ParquetFile(WORK/'data'/name);offset=0
        for n in range(pf.num_row_groups):
            count=pf.metadata.row_group(n).num_rows
            wanted_rows=[i for i in lookup if offset<=i<offset+count]
            if wanted_rows:
                table=pf.read_row_group(n,columns=['RevX_OCR_text'])
                for i in wanted_rows: raw[lookup[i]]=table['RevX_OCR_text'][i-offset].as_py() or ''
            offset+=count

    def observe(namespace, legacy, key, excerpts, sid, pointer, crops):
        oid=observation_id(namespace,legacy);obj(oid,'observation',legacy+' · '+by_key[key]['issue_date'])
        text=normalized(raw[key]);anchors=[]
        for excerpt in excerpts:
            target=normalized(excerpt);count=text.count(target)
            anchors.append({'status':'unique_normalized_match' if count==1 else 'ambiguous_match' if count>1 else 'not_exactly_located',
              'start':text.find(target) if count==1 else None,'end':text.find(target)+len(target) if count==1 else None,'matches':count})
        locator={'coordinate_system':'Unicode character offsets in normalized RevX text','normalization_id':'chain-search-v1','normalized_page_sha256':sha(text),'segments':anchors}
        insert('observations',id=oid,legacy_namespace=namespace,legacy_id=legacy,page_version_id=page_version(key),transcription_field='RevX_OCR_text',excerpts_json=J(excerpts),excerpt_sha256=sha(J(excerpts)),normalization='Imported excerpts; source spellings retained. Locator normalization: join whitespace hyphenation, long-s to s, collapse whitespace.',locator_json=J(locator),scan_review_status='previously_inspected_same_assistant',scan_review_run_id='run:import-review',source_id=sid,source_pointer=pointer)
        for crop in crops:
            original=OUT/crop['path']
            if not original.exists(): raise ValueError('Missing inspected scan crop: '+str(original))
            asset_path='assets/'+crop['path'].replace('/','__')
            shutil.copyfile(original,RELEASE/asset_path)
            aid='asset:'+sha(oid+'|'+asset_path)[:24]
            insert('assets',id=aid,object_id=oid,path=asset_path,sha256=file_sha(original),kind='inspected_scan_crop',original_source_id=sid)
        return oid

    for i,v in enumerate(chain['versions']):
        observe('chain-20261030',v['id'],v['key'],[v['excerpt']],chain_source,f'/versions/{i}',v['crops'])
    for i,r in enumerate(rels['records']):
        observe('relations-20261029',r['id'],r['source']['page_key'],r['excerpts'],rel_source,f'/records/{i}',r['scan_crops'])

    group_specs=[
      ('boyd-bantry-coverage','context_group','Boyd / Bantry coverage','Reports, printed challenge and later related account concerning the expedition; not a single verified event.',['H001','H002','H006','H007']),
      ('boyd-core-report','message_group','Boyd fleet report','Corresponding core fleet report; includes the edition with an appended challenge.',['H001','H002','H006']),
      ('fleet-return-account','message_group','Later fleet-return account','Later related account concerning the main body returning to Brest; no explicit retraction assigned.',['H007']),
      ('peace-cayenne-context','context_group','Peace / Cayenne context','Research collection of a seizure report and decree/commentary. Membership does not assert a legal or causal link.',['H012','X016','H013']),
      ('peace-seizure-report','message_group','Peace seizure report','Corresponding reports about the named Peace account attributed to Whitney; excludes unresolved later same-name leads.',['H012','X016']),
      ('cayenne-decree-commentary','document_group','Cayenne decree and commentary','Printed translated decree and attached allegation; original decree and itemized allegations remain unresolved.',['H013']),
      ('clearance-resolution-1794','document_group','1794 clearance resolution','Two observed versions of the same clearance provisions; content verification does not establish implementation.',['H017','H019'])]
    roles={'H001':['report'],'H002':['report','challenge'],'H006':['report'],'H007':['later_related_account'],'H012':['report'],'X016':['report','commentary'],'H013':['translated_document','accusation'],'H017':['document_excerpt'],'H019':['published_document']}
    for short,kind,label,definition,ids in group_specs:
        gid='group:'+short;obj(gid,'group',label)
        insert('groups',id=gid,kind=kind,label=label,definition=definition,admission_rule='Existing inspected selections only; additional candidates require an explicit documented admission.',run_id='run:foundation-v1')
        for legacy in ids:
            oid=observation_id('chain-20261030',legacy)
            aid='membership:'+short+':'+legacy+':1'
            annotation(aid,oid,'membership:'+gid,{'decision':'admitted','roles':roles[legacy],'basis':'Existing inspected selection; structural membership, not an independently adjudicated historical event.'},'run:foundation-v1',chain_source,'/versions/'+str(next(i for i,v in enumerate(chain['versions']) if v['id']==legacy)))
            insert('memberships',annotation_id=aid,observation_id=oid,group_id=gid,decision='admitted',roles_json=J(roles[legacy]))
    for parent,child in [('boyd-bantry-coverage','boyd-core-report'),('boyd-bantry-coverage','fleet-return-account'),('peace-cayenne-context','peace-seizure-report'),('peace-cayenne-context','cayenne-decree-commentary')]:
        aid='hierarchy:'+parent+':'+child
        annotation(aid,'group:'+child,'parent_group',{'parent':'group:'+parent,'meaning':'Organizational containment; not historical causation'},'run:foundation-v1',chain_source,'/families')
        insert('group_hierarchy',annotation_id=aid,parent_id='group:'+parent,child_id='group:'+child)

    old_claims={x['id']:x for x in chain['claims']}
    for i,c in enumerate(review['claims']):
        cid='claim:'+c['id'];obj(cid,'claim',c['statement'])
        aid=annotation('review:'+c['id']+':1',cid,'evidence_review',{'status':c['status'],'note':c['note'],'independent_review':False},'run:import-review',review_source,f'/claims/{i}')
        insert('claims',id=cid,statement=c['statement'],kind=old_claims[c['id']]['kind'],imported_review_annotation_id=aid)
        for legacy in c['versions']: insert('claim_evidence',claim_id=cid,observation_id=observation_id('chain-20261030',legacy))

    def relation(rid,subject,predicate,target,directed,level,note,sid,pointer,evidence):
        obj(rid,'relation',predicate)
        aid=annotation('review:'+rid+':1',rid,'relation_review',{'note':note,'historical_causality_established':False,'independent_review':False},'run:import-review',sid,pointer)
        insert('relations',id=rid,subject_id=subject,predicate=predicate,object_id=target,directed=int(directed),evidence_level=level,imported_review_annotation_id=aid)
        for oid,loc in evidence: insert('relation_evidence',relation_id=rid,evidence_object_id=oid,locator=loc)

    coded={r['id']:r for r in review['relations']}
    for i,r in enumerate(rels['records']):
        for name in [r['from_id'],r['to_id']]: obj('concept:'+name,'concept',name.replace('_',' '))
        rr=coded[r['id']];oid=observation_id('relations-20261029',r['id'])
        relation('relation:'+r['id'],'concept:'+r['from_id'],rr['coding'],'concept:'+r['to_id'],True,'printed_assertion',rr['review_note'],review_source,f'/relations/{i}',[(oid,'Imported supporting excerpt selection')])
        for j,d in enumerate(r['event_dates']):
            iso=d.get('iso');valid=bool(iso and re.fullmatch(r'\d{4}-\d{2}-\d{2}',iso))
            insert('date_assertions',id=f'date:{r["id"]}:{j}',object_id=oid,date_role=d['meaning'],as_printed=d['as_printed'],earliest_date=iso if valid else None,latest_date=iso if valid else None,precision='day' if valid else 'unresolved',source_id=rel_source,source_pointer=f'/records/{i}/event_dates/{j}')
    for i,r in enumerate(chain['relations']):
        level='context_only' if r['type'] in ['context_only','later_account'] else 'textual_correspondence'
        relation('relation:chain:'+r['id'],observation_id('chain-20261030',r['a']),r['type'],observation_id('chain-20261030',r['b']),r['directed'],level,r['note'],chain_source,f'/relations/{i}',[(observation_id('chain-20261030',r['a']),'Corresponding printed selection'),(observation_id('chain-20261030',r['b']),'Corresponding printed selection')])
    doc='document:asp2:p62:item19';obj(doc,'document_fragment','American State Papers, Foreign Relations, vol. 2, p. 62, item 19')
    annotation('document:asp2:source',doc,'source_locator',review['external_sources'][1],'run:import-review',review_source,'/external_sources/1')
    relation('relation:peace-explicit-citation',observation_id('chain-20261030','H012'),'cited_by',doc,True,'explicit_citation','The later compilation explicitly cites Gazette of the United States, May 18. Source dependence, not independent corroboration; intermediate route unknown.',review_source,'/source_edges/0',[(doc,'Printed page 62, item 19; source citation inspected in the existing review')])

    topic_input=read('outputs/topic_pilot.json');labels=read('work/topic_labels.json')
    model_source=source('work/topic_model.joblib','frozen_model',copy=False)
    source('work/topic_labels.json','topic_labels')
    source('outputs/topic_pilot.json','pilot_model_metadata')
    model_code=source('work/recheck_full_corpus.py','model_scoring_code')
    source('work/discover_topics.py','model_training_code')
    run='run:topic-census-frozen24'
    insert('runs',id=run,method=topic_input['method'],parameters_json=J({'model_source_id':model_source,'vectorizer_params':topic_input['vectorizer_params'],'score_unit':'allocated wordlike tokens','status':'frozen pilot model applied to eligible census; labels provisional'}),source_id=model_code,recorded_date=DATE,reviewer_kind='automated',independent_review=0)
    for t in topic_input['topics']:
        tid=t['topic_id'];oid='topic:frozen24:'+tid;label=labels[tid]
        obj(oid,'model_topic',label['label'])
        insert('topics',id=oid,model_run_id=run,component_id=tid,label=label['label'],definition=label['description'],terms_json=J(t['top_terms']),restart_agreement=t['restart_cosine_agreement'],review_note=label.get('review_note','Provisional model topic; not an event.'))
    source('outputs/research_review_2026-11-02/page_topic_census.parquet','model_output',copy=False)
    census=pq.read_table(OUT/'research_review_2026-11-02/page_topic_census.parquet')
    census=census.append_column('page_id',pa.array([page_id(k) for k in census['key'].to_pylist()]))
    census=census.append_column('model_run_id',pa.array([run]*len(census)))
    pq.write_table(census,RELEASE/'derived/page_topic_census.parquet')

    insert('metadata',key='release',value_json=J({'version':VERSION,'dataset':DATASET,'revision':REV,'date':DATE,'language':'English schema and documentation; source annotations preserved verbatim'}))
    insert('metadata',key='counting_units',value_json=J({'observation':'curated passage selection, not automatically a full article','issue':'newspaper + publication date + edition','page':'issue + page number','publication_dates':'not historical event dates','group_totals':'overlap; use DISTINCT observation/page/issue IDs for unions'}))
    db.commit()

    # Consumer projection: no layout positions, colors, brightness, or inferred edges.
    notes={
      'H001':'Scan: dismasted; RevX: distressed. The capture statement is a prediction.',
      'H002':'Printed CHRONICLE challenge; objections are not independently adjudicated. Some failed forms read sailed in the scan.',
      'H006':'Corresponding report without the appended CHRONICLE challenge. Direct copying route unassigned.',
      'H007':'Later account concerning the main body returning to Brest; no explicit retraction.'}
    summaries={'H001':"Boyd's account of the French fleet at Bantry Bay.",'H002':'The report appears with an appended challenge.','H006':'The core report appears in the Kentucky Gazette.','H007':"A later account describes the main body's return to Brest."}
    records=[]
    for r in db.execute("SELECT * FROM group_publications WHERE group_id='group:boyd-bantry-coverage' ORDER BY publication_date"):
        asset=db.execute('SELECT path FROM assets WHERE object_id=? ORDER BY path',(r['observation_id'],)).fetchone()
        records.append({'id':r['legacy_id'],'observation_id':r['observation_id'],'page_id':r['page_id'],'node':r['lccn'],'publication_date':r['publication_date'],'page':r['page_number'],'roles':json.loads(r['roles_json']),'phase':None,'excerpt':'\n\n'.join(json.loads(r['excerpts_json'])),'source_url':r['pinned_scan_url'],'scan_asset':asset['path'],'note':notes[r['legacy_id']],'summary':summaries[r['legacy_id']]})
    pulse={'schema_version':VERSION,'release_id':'newspapers-v'+VERSION,'group_id':'group:boyd-bantry-coverage','observations':records,'relations':[]}
    (RELEASE/'views/pulse_boyd.json').write_text(json.dumps(pulse,ensure_ascii=False,indent=2),encoding='utf8')
    tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for table in tables:
        with (RELEASE/'tables'/f'{table}.jsonl').open('w',encoding='utf8',newline='\n') as f:
            for row in db.execute(f'SELECT * FROM {table} ORDER BY 1'):
                values=dict(row)
                for k in list(values):
                    if k.endswith('_json') and values[k] is not None: values[k[:-5]]=json.loads(values.pop(k))
                f.write(J(values)+'\n')
    shutil.copyfile(HERE/'schema.sql',RELEASE/'schemas/schema.sql')
    shutil.copyfile(HERE/'README.md',RELEASE/'README.md')
    shutil.copyfile(HERE/'examples.sql',RELEASE/'examples.sql')
    db.close()
    from validate import validate
    results=validate(RELEASE)
    (RELEASE/'validation.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    files=[]
    for path in sorted(RELEASE.rglob('*')):
        if path.is_file() and path.name!='manifest.json': files.append({'path':path.relative_to(RELEASE).as_posix(),'bytes':path.stat().st_size,'sha256':file_sha(path)})
    manifest={'version':VERSION,'status':'released','created_date':DATE,'dataset_revision':REV,'build_command':'python work/archive_data/build.py','counts':results['counts'],'files':files,'raw_archive_included':False,'raw_archive_location':'../../../work/data/','historical_findings_added':False}
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf8')
    (RELEASE.parent/'CURRENT.json').write_text(json.dumps({'version':VERSION,'path':'v'+VERSION,'manifest_sha256':file_sha(manifest_path)},indent=2),encoding='utf8')
    print(json.dumps({'release':str(RELEASE),'validation':results}),flush=True)

if __name__=='__main__': main()
