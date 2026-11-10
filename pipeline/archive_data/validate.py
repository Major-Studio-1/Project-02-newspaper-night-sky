"""Integrity and counting checks for a generated data release."""
from pathlib import Path
import json
import sqlite3
import datetime
import hashlib
import sys

# Release 0.1.0 had no expected_counts metadata; these are its declared counts.
V010_EXPECTED={'observations':24,'claims':15,'relations':22,'groups':7,'memberships':16,'group_hierarchy':4,
               'distinct_current_members':9,'boyd_coverage_selections':4,'boyd_core_selections':3}

def validate(release):
    release=Path(release).resolve()
    db=sqlite3.connect((release/'research.sqlite').as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    checks=[]
    def check(name,condition):
        if not condition: raise AssertionError(name)
        checks.append(name)
    check('SQLite structural integrity',db.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
    check('All foreign-key references resolve',not db.execute('PRAGMA foreign_key_check').fetchall())
    row=db.execute("SELECT value_json FROM metadata WHERE key='expected_counts'").fetchone()
    expected=json.loads(row[0]) if row else V010_EXPECTED
    counts={t:db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['newspapers','issues','pages','observations','groups','memberships','group_hierarchy','claims','relations','topics','date_assertions']}
    counts['eligible_pages']=db.execute('SELECT SUM(eligible) FROM page_assessments').fetchone()[0]
    check('Full source inventory reconciles',counts['pages']==77793 and counts['issues']==19445 and counts['newspapers']==110)
    check('Eligibility remains analysis-specific',counts['eligible_pages']==77749)
    check('Reviewed selections, claims and links match the declared counts',all(counts[k]==expected[k] for k in ['observations','claims','relations']))
    check('Only reviewed selections populate the explicitly typed groups',all(counts[k]==expected[k] for k in ['groups','memberships','group_hierarchy']))
    check('Every group has at least one admitted selection',db.execute("SELECT COUNT(*) FROM groups g WHERE NOT EXISTS(SELECT 1 FROM group_publications p WHERE p.group_id=g.id)").fetchone()[0]==0)
    check('Every relation has attached evidence',db.execute('SELECT COUNT(*) FROM relations r WHERE NOT EXISTS(SELECT 1 FROM relation_evidence e WHERE e.relation_id=r.id)').fetchone()[0]==0)
    check('No independent review invented',db.execute('SELECT SUM(independent_review) FROM runs').fetchone()[0]==0)
    check('Membership annotations target the correct observation and group',db.execute("SELECT COUNT(*) FROM memberships m JOIN annotations a ON a.id=m.annotation_id WHERE a.object_id<>m.observation_id OR a.annotation_type<>'membership:'||m.group_id OR json_extract(a.value_json,'$.decision')<>m.decision").fetchone()[0]==0)
    for row in db.execute('SELECT publication_date FROM issues'):
        datetime.date.fromisoformat(row[0])
    check('All publication dates are valid ISO calendar dates',True)
    source_map={r['id']:r for r in db.execute('SELECT * FROM sources')}
    anchor_statuses={}
    for obs in db.execute('SELECT * FROM observations'):
        segments=json.loads(obs['excerpts_json']);loc=json.loads(obs['locator_json'])
        check_digest=hashlib.sha256(json.dumps(segments,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if check_digest!=obs['excerpt_sha256']: raise AssertionError('Excerpt hash differs: '+obs['id'])
        if len(segments)!=len(loc['segments']): raise AssertionError('Missing segment locator')
        for anchor in loc['segments']:
            status=anchor['status'];anchor_statuses[status]=anchor_statuses.get(status,0)+1
            if status=='unique_normalized_match':
                if not (anchor['start']>=0 and anchor['end']>anchor['start'] and anchor['matches']==1): raise AssertionError('Invalid anchor')
            elif anchor['start'] is not None or anchor['end'] is not None: raise AssertionError('Uncertain offsets must remain null')
    check('Excerpt hashes and explicit locator states are valid',True)
    for row in db.execute('SELECT * FROM assets'):
        path=(release/row['path']).resolve()
        check('Asset present with preserved bytes: '+row['id'],path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'])
    seed=json.loads((release/source_map[next(r['id'] for r in source_map.values() if r['kind']=='prototype_seed')]['path']).read_text(encoding='utf8'))
    pulse=json.loads((release/'views/pulse_boyd.json').read_text(encoding='utf8'))
    projected={r['id']:r for r in pulse['observations']}
    check('Pulse projection keeps every prototype observation',all(r['id'] in projected for r in seed['observations']))
    for old in seed['observations']:
        new=projected[old['id']]
        for key in ['id','node','publication_date','page','roles','phase','excerpt','source_url']:
            if old[key]!=new[key]: raise AssertionError('Pulse source data changed: '+old['id']+' '+key)
    check('Pulse projection exactly preserves dates, pages, roles, excerpts and source URLs',True)
    admitted={r[0] for r in db.execute("SELECT legacy_id FROM group_publications WHERE group_id='group:boyd-bantry-coverage'")}
    check('Pulse projection matches the admitted Boyd/Bantry coverage group',set(projected)==admitted)
    check('Pulse projection contains no edges',pulse['relations']==[])
    group_counts={r['group_id']:dict(r) for r in db.execute('SELECT * FROM observed_group_summary')}
    check('Overlapping group memberships do not inflate union counts',db.execute('SELECT COUNT(DISTINCT observation_id) FROM current_memberships').fetchone()[0]==expected['distinct_current_members'])
    check('Boyd parent and child groups keep distinct identities',group_counts['group:boyd-bantry-coverage']['passage_selections']==expected['boyd_coverage_selections'] and group_counts['group:boyd-core-report']['passage_selections']==expected['boyd_core_selections'])

    # Destructive probes run only in an in-memory clone, never the release.
    sandbox=sqlite3.connect(':memory:');db.backup(sandbox);sandbox.execute('PRAGMA foreign_keys=ON')
    def rejected(name,sql,args=()):
        sandbox.execute('SAVEPOINT probe')
        try:
            sandbox.execute(sql,args)
        except sqlite3.IntegrityError:
            sandbox.execute('ROLLBACK TO probe');sandbox.execute('RELEASE probe');checks.append(name)
        else:
            sandbox.execute('ROLLBACK TO probe');sandbox.execute('RELEASE probe');raise AssertionError(name)
    rejected('Dangling provenance is rejected',"INSERT INTO runs VALUES ('bad','bad','{}','missing','2026-11-04','automated',0)")
    rejected('Silent annotation edits are rejected',"UPDATE annotations SET value_json='{}'")
    rejected('Deleting review history is rejected','DELETE FROM annotations')
    h=sandbox.execute('SELECT * FROM group_hierarchy LIMIT 1').fetchone()
    rejected('Hierarchy cycles are rejected','INSERT INTO group_hierarchy VALUES (?,?,?)',(h[0],h[2],h[1]))
    row=sandbox.execute("SELECT * FROM annotations WHERE id='membership:boyd-core-report:H001:1'").fetchone()
    sandbox.execute('INSERT INTO annotations VALUES (?,?,?,?,?,?,?,?,?)',('test:withdraw',row[1],row[2],'{"decision":"withdrawn","roles":[]}',row[4],row[5],row[6],row[0],row[8]))
    sandbox.execute('INSERT INTO memberships VALUES (?,?,?,?,?)',('test:withdraw',row[1],'group:boyd-core-report','withdrawn','[]'))
    check('A superseding decision changes the projection while preserving the old annotation',sandbox.execute("SELECT COUNT(*) FROM group_publications WHERE group_id='group:boyd-core-report'").fetchone()[0]==2 and sandbox.execute('SELECT COUNT(*) FROM annotations WHERE id=?',(row[0],)).fetchone()[0]==1)
    sandbox.close()

    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python_packages'))
    import pyarrow.parquet as pq
    import numpy as np
    scores=pq.read_table(release/'derived/page_topic_census.parquet')
    check('Every topic vector joins to an eligible source page',len(scores)==77749 and set(scores['page_id'].to_pylist())=={r[0] for r in db.execute('SELECT v.page_id FROM page_versions v JOIN page_assessments a ON a.page_version_id=v.id WHERE a.eligible=1')})
    matrix=np.column_stack([scores[f'T{i:02}'].to_numpy() for i in range(1,25)])
    check('Topic allocations are finite and nonnegative',bool(np.isfinite(matrix).all() and (matrix>=0).all()))
    check('Topic allocations plus unassigned mass recover page word totals',bool(np.allclose(matrix.sum(axis=1)+scores['unassigned_words'].to_numpy(),scores['words'].to_numpy(),rtol=1e-7,atol=1e-5)))
    # Optional automatic reuse layer (v0.5.0 on): it must join to known pages and stay apart from reviewed tables.
    if (release/'derived/reuse_families.parquet').exists():
        fams = pq.read_table(release/'derived/reuse_families.parquet').to_pylist()
        apps = pq.read_table(release/'derived/reuse_family_appearances.parquet', columns=['family_id', 'page_id', 'lccn']).to_pylist()
        page_ids = {r[0] for r in db.execute('SELECT id FROM pages')}
        check('Reuse family ids are unique', len({f['family_id'] for f in fams}) == len(fams))
        check('Every reuse appearance joins to a known page', all(a['page_id'] in page_ids for a in apps))
        by_family = {}
        for a in apps:
            by_family.setdefault(a['family_id'], set()).add(a['lccn'])
        check('Every reuse family spans at least two newspaper series', all(len(by_family.get(f['family_id'], ())) >= 2 for f in fams))
        check('Reuse layer is recorded as automatic with no review', tuple(db.execute("SELECT reviewer_kind, independent_review FROM runs WHERE id='run:reuse-all-v1'").fetchone() or ()) == ('automated', 0))
    # Optional automatic titles (v0.5.1 on): exactly one non-empty title per matched story, recorded as automatic.
    if (release/'derived/reuse_family_titles.parquet').exists():
        titles = pq.read_table(release/'derived/reuse_family_titles.parquet', columns=['family_id', 'title']).to_pylist()
        fam_ids = [f['family_id'] for f in pq.read_table(release/'derived/reuse_families.parquet', columns=['family_id']).to_pylist()]
        check('Every matched story has exactly one title', sorted(t['family_id'] for t in titles) == sorted(fam_ids))
        check('Titles are non-empty', all(t['title'].strip(' …') for t in titles))
        check('Titles are recorded as automatic with no review', tuple(db.execute("SELECT reviewer_kind, independent_review FROM runs WHERE id='run:reuse-titles-v1'").fetchone() or ()) == ('automated', 0))
    # Optional story topics (v0.5.2 on): one row per matched story, reviewed rows name real groups, topics are T01-T24.
    if (release/'derived/story_topics.parquet').exists():
        st = pq.read_table(release/'derived/story_topics.parquet', columns=['story_id', 'kind', 'top_topic', 'second_topic', 'run_id']).to_pylist()
        fam_ids = {f['family_id'] for f in pq.read_table(release/'derived/reuse_families.parquet', columns=['family_id']).to_pylist()}
        group_ids = {r[0] for r in db.execute('SELECT id FROM groups')}
        check('Every matched story has exactly one topic row', sorted(r['story_id'] for r in st if r['kind'] == 'matched') == sorted(fam_ids))
        check('Reviewed topic rows name released groups', all(r['story_id'] in group_ids for r in st if r['kind'] == 'reviewed'))
        check('Story topics are model topics T01-T24', all(r['top_topic'] in {f'T{i:02}' for i in range(1, 25)} and r['second_topic'] in {f'T{i:02}' for i in range(1, 25)} for r in st))
        check('Story topics are recorded as automatic with no review', tuple(db.execute("SELECT reviewer_kind, independent_review FROM runs WHERE id='run:story-topics-v1'").fetchone() or ()) == ('automated', 0))
        # Topic rows for reviewed groups added later (v0.7.1 on): every reviewed group with printings has exactly one.
        if db.execute("SELECT 1 FROM runs WHERE id='run:story-topics-reviewed-v1'").fetchone():
            printed = sorted(r[0] for r in db.execute('SELECT DISTINCT group_id FROM group_publications'))
            check('Every reviewed group with printings has exactly one topic row', sorted(r['story_id'] for r in st if r['kind'] == 'reviewed') == printed)
            # Each later batch of rows has a run of its own (v0.7.2 on: one per ledger); every one must be recorded as automatic.
            later = {r['run_id'] for r in st if r['kind'] == 'reviewed'} - {'run:story-topics-v1'}
            check('Topics of later reviewed groups are recorded as automatic with no review',
                  'run:story-topics-reviewed-v1' in later and all(tuple(db.execute('SELECT reviewer_kind, independent_review FROM runs WHERE id=?', (r,)).fetchone() or ()) == ('automated', 0) for r in later))
    run_kind = lambda run: tuple(db.execute('SELECT reviewer_kind, independent_review FROM runs WHERE id=?', (run,)).fetchone() or ())
    # One printing per story and page (v0.6.0 on): merged appearances, recounted families.
    if (release/'derived/reuse_family_appearances.parquet').exists() and 'blocks_json' in pq.read_schema(release/'derived/reuse_family_appearances.parquet').names:
        app_cols = pq.read_schema(release/'derived/reuse_family_appearances.parquet').names
        prints = pq.read_table(release/'derived/reuse_family_appearances.parquet', columns=['family_id', 'page_id', 'seq', 'segments', 'blocks_json'] + [c for c in ('text_page_id',) if c in app_cols]).to_pylist()
        fams = pq.read_table(release/'derived/reuse_families.parquet', columns=['family_id', 'appearances', 'pages']).to_pylist()
        per_story = {}
        for p in prints:
            per_story[p['family_id']] = per_story.get(p['family_id'], 0) + 1
        check('No matched story lists a page twice', len({(p['family_id'], p['page_id']) for p in prints}) == len(prints))
        check('Story printing counts match their printings and pages', all(f['appearances'] == per_story.get(f['family_id']) == f['pages'] for f in fams))
        check('Printing ids are unique within each story', len({(p['family_id'], p['seq']) for p in prints}) == len(prints))
        check('Every printing keeps at least one matched block', all(p['segments'] >= 1 and json.loads(p['blocks_json']) for p in prints))
        check('The printing merge is recorded as automatic with no review', run_kind('run:printings-merge-v1') == ('automated', 0))
    # Transcription checks (v0.6.0 on): exactly one per printing, with a known status.
    if (release/'derived/transcription_checks.parquet').exists():
        tc = pq.read_table(release/'derived/transcription_checks.parquet', columns=['family_id', 'seq', 'page_id', 'status']).to_pylist()
        check('Exactly one transcription check per printing', sorted((c['family_id'], c['seq'], c['page_id']) for c in tc) == sorted((p['family_id'], p['seq'], p['page_id']) for p in prints))
        check('Transcription checks use the documented statuses', {c['status'] for c in tc} <= {'confirmed', 'partly', 'missing_in_other', 'other_unreadable', 'no_second_transcription'})
        # Checks redone later (v0.8.1 on: under the RevX page map) carry the run that redid them; every run must be automatic.
        tc_runs = {r['run_id'] for r in pq.read_table(release/'derived/transcription_checks.parquet', columns=['run_id']).to_pylist()} | {'run:transcription-check-v1'}
        check('Transcription checks are recorded as automatic with no review', all(run_kind(r) == ('automated', 0) for r in tc_runs))
    # Audit of matched stories (v0.6.0 on): released stories, protocol values, an AI review that is not independent.
    if (release/'derived/matched_audit.parquet').exists():
        au = pq.read_table(release/'derived/matched_audit.parquet').to_pylist()
        fam_ids = {f['family_id'] for f in pq.read_table(release/'derived/reuse_families.parquet', columns=['family_id']).to_pylist()}
        check('Audit rows name distinct released matched stories', len({a['family_id'] for a in au}) == len(au) and all(a['family_id'] in fam_ids for a in au))
        check('Audit verdicts use the protocol values', all(a['one_item'] in ('yes', 'no', 'unsure') and a['on_page'] in ('yes', 'partly', 'no', 'not_located')
                                                             and a['transcription'] in ('faithful', 'minor_errors', 'major_problem', 'not_checked') for a in au))
        # v0.8.1 on: a printing moved to the scan page its RevX text transcribes was scan-checked, if at all, on the page its text is filed under.
        printing_pages = {(p['family_id'], p['page_id']) for p in prints} | {(p['family_id'], p['text_page_id']) for p in prints if p.get('text_page_id')}
        check('Every scan-checked printing is a printing of its story', all((a['family_id'], a['scan_check_page_id']) in printing_pages for a in au))
        check('The audit is recorded as an AI review, not an independent one', run_kind('run:matched-audit-v1') == ('ai_assistant', 0))
    # RevX page map (v0.8.1 on): RevX transcriptions filed under another page than the scan they transcribe. Matched
    # printings and match ends read from such a text are filed under the scan page it transcribes; text_page_id keeps
    # the page the text is filed under, which their spans index into.
    if (release/'derived/revx_page_map.parquet').exists():
        pm = pq.read_table(release/'derived/revx_page_map.parquet').to_pylist()
        to = {m['page_id']: m['revx_text_of'] for m in pm}
        page_ids = {r[0] for r in db.execute('SELECT id FROM pages')}
        check('The RevX page map names known pages, each filed under another page of its issue',
              len(to) == len(pm) and all(m['page_id'] in page_ids and m['revx_text_of'] in page_ids and m['page_id'] != m['revx_text_of']
                                         and m['page_id'].rsplit(':', 1)[0] == m['revx_text_of'].rsplit(':', 1)[0]
                                         and m['status'] in ('shifted', 'other_page', 'duplicate') for m in pm))
        filed = lambda transcription, text_page: to.get(text_page, text_page) if transcription == 'RevX' else text_page
        full = pq.read_table(release/'derived/reuse_family_appearances.parquet', columns=['page_id', 'transcription', 'text_page_id', 'other_texts_json']).to_pylist()
        check('Every printing is filed under the scan page its text transcribes', all(p['page_id'] == filed(p['transcription'], p['text_page_id']) for p in full))
        check('Merged reads of a printing are texts of the same scan page',
              all(p['page_id'] == filed(o['transcription'], o['text_page_id']) for p in full if p['other_texts_json'] for o in json.loads(p['other_texts_json'])))
        ends = pq.read_table(release/'derived/reuse_matches.parquet', columns=['a_page_id', 'b_page_id', 'a_text_page_id', 'b_text_page_id']).to_pylist()
        check('Every reuse match end is filed under the scan page its text transcribes',
              all(m[s+'_page_id'] == to.get(m[s+'_text_page_id'], m[s+'_text_page_id']) for m in ends for s in 'ab'))
        check('The page map and the refiling are recorded as automatic with no review',
              run_kind('run:revx-page-shift-check-v1') == ('automated', 0) and run_kind('run:revx-page-refile-v1') == ('automated', 0))
    # English notes (v0.6.1 on): once table corrections exist, no current annotation or date role is left untranslated.
    if db.execute("SELECT 1 FROM metadata WHERE key='table_corrections'").fetchone():
        import re
        han = re.compile('[㐀-鿿]')
        texts = [r[0] for r in db.execute('SELECT value_json FROM current_annotations')] + [r[0] for r in db.execute('SELECT date_role FROM date_assertions')]
        check('Current annotations and date roles carry no untranslated Chinese', not any(han.search(t) for t in texts))
        log = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='table_corrections'").fetchone()[0])
        check('Every table correction keeps its old value and reason', all(c['from'] and c['to'] and c['reason'] for c in log))
    for line in (release/'examples.sql').read_text().split('-- QUERY\n')[1:]:
        db.execute(line.strip()).fetchall()
    check('All supplied example queries execute',True)
    db.close()
    return {'passed':True,'counts':counts,'normalized_segment_locator_statuses':anchor_statuses,'checks':checks,'limitations':['No new event census or independent human review.','A curated selection is not an article; selections on the same page may overlap.','Raw full-corpus transcriptions remain in the six pinned source shards.','Non-exact excerpt locations remain explicitly unresolved.']}

if __name__=='__main__':
    release=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[2]/'outputs/data_foundation/v0.1.0'
    print(json.dumps(validate(release),indent=2))
