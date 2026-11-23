"""Make a correction release for the National Intelligencer issues of 1802 filed under the wrong dates (v0.11.13).

The review of 1802 (outputs/story_discovery_1802/README.md, "Data issues"; register X-1802-08) found eight issues of the
National Intelligencer filed under dates their first pages do not print. The evidence is in outputs/filing_corrections_1802/:
corrections.json names each correction and the checks and scans it rests on (mastheads_1802.json, second_scan_1802.json,
made by check_ni_1802.py). This script is work/archive_data/correct_filing.py (release v0.11.7) with this release's
corrections, and without that release's one-off census rescoring of the misfiled RevX pages. This step:

1. Issue dates (run:filing-corrections-1802-v1). Seven issues take the dates they print: filed 21 August = 2 August,
   11 September = 1 September, 10 October = 1 October, 6 November = 6 December, 8 November = 8 December,
   29 November = 29 December, 30 December = 31 December 1802. issues.publication_date becomes the printed date; ids keep
   the filed date, as since v0.10.2.
2. A second scan. The four pages filed under 24 November 1802 are another image of the four pages of the issue filed under
   24 December, which the archive holds (the CA texts are the same word for word). They leave the analysis:
   page_assessments.eligible 1 -> 0. Their census rows, matched printings and matches go. No issue of 24 November is in
   the collection.
   Every change to issues and page_assessments is in metadata table_corrections with its old value and reason.
3. Matched stories (run:filing-corrections-1802-rematch-v1). The 26 pages whose date changes are matched again in the
   windows of their printed dates (outputs/filing_corrections_1802/match_moved_pages.py, which first reproduces their
   stored matches exactly). Then, as v0.11.7 did:
   - derived/reuse_matches.parquet: the matches of these 26 pages and of the 4 second-scan pages are replaced by the new
     ones (dates are printed dates). Matches between other pages are kept as released.
   - the printings on these 30 pages leave their stories. The new main matches join stories by the family rule (matched
     spans that overlap on a page are one passage), or make new stories, whose ids continue their first year's
     numbering. Existing printings keep their spans and excerpts; a passage that links two stories joins the one it
     shares the most matched words with; stories are not merged. New printings follow the rules of v0.6.0 and v0.8.1,
     with excerpts cut as work/reuse_families_all.py cuts them, and seq continues each story's numbering.
   - only then is a story left with one newspaper dropped, and a printing that no longer matches the rest of its story by
     the main matches the release now holds removed from it (a story may not fall into two stories).
   - derived/reuse_families.parquet: dates, counts, long_running and keywords recounted for the stories that changed;
     label and title made again only where the first printing is on another page than before.
   - derived/reuse_family_titles.parquet, derived/story_topics.parquet, derived/transcription_checks.parquet: rows for
     new stories and printings by the rules of reuse-titles-v1, story-topics-v1 and transcription-check-v1; the topics of
     every story that changed are scored again together (run:story-topics-filing-corrections-1802); rows of dropped
     stories and printings removed.
4. derived/page_topic_census.parquet. Date, year and month of the 26 pages follow their issues; the 4 second-scan rows go.
   The scores do not change.
Not changed: every reviewed table. One reviewed printing stands on a corrected page: S02-090, the French Senate's address
to the First Consul in the National Intelligencer, on page 3 of the issue filed under 10 October 1802. Its row does not
change; its date, which the issue gives, becomes 1 October, the date its note records. The script stops if any other
reviewed printing stands on these pages. Also not changed: the audit (no sample story has a printing on these pages; the
script checks this) and the RevX page map (none of these pages is in it).

Usage (project root, Python 3.12):
    python work/archive_data/correct_filing_1802.py 0.11.12 0.11.13 --keep-current
    python work/archive_data/correct_filing_1802.py 0.11.12 0.11.13 --dry-run        # counts only; writes nothing
Inputs: outputs/filing_corrections_1802/ (corrections.json, check_ni_1802.py and its mastheads_1802.json and
second_scan_1802.json, match_moved_pages.py and its matches_filed.json, matches_printed.json and rematch_summary.json,
README.md); work/reuse_all/matches_*.json and outputs/kentucky_gazette_dates/matches_printed.json (match texts, for
keywords); the six pinned shards in work/data/
"""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import shutil
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
WORK = PROJECT/'work'
FOUNDATION = PROJECT/'outputs/data_foundation'
CHECK = PROJECT/'outputs/filing_corrections_1802'
SEGMENTS = FOUNDATION/'v0.5.2/derived/reuse_family_appearances.parquet'   # the excerpts story-topics-v1 scored
sys.path.insert(0, str(WORK/'python_packages'))
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(HERE))
import joblib
import pyarrow as pa
import pyarrow.parquet as pq
from merge_printings import TOUCH
from refile_revx_pages import check, file_sha, pinned_shards
from redate_issues import read_pages, excerpt_of, keywords, overlap
from reuse_families_all import TOKEN
from reuse_titles_all import analyse, clean, title_for
from add_reviewed_topics import score

RUN_FIX, RUN_MATCH = 'run:filing-corrections-1802-v1', 'run:filing-corrections-1802-rematch-v1'
RUN_TOPICS = 'run:story-topics-filing-corrections-1802'
REVIEWED_ON_CORRECTED = {'obs:expansion-1802:S02-090'}   # reviewed printings known to stand on a corrected page
POINTER = 'outputs/filing_corrections_1802/corrections.json#'
STATUSES = ['confirmed', 'partly', 'missing_in_other', 'other_unreadable', 'no_second_transcription']
TOPICS = [f'T{i:02}' for i in range(1, 25)]
J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()
load = lambda path: json.loads(path.read_text(encoding='utf8'))
page_of_key = lambda key: 'page:'+key.replace('|', ':')
key_of = lambda pid: pid.split(':', 1)[1].replace(':', '|')
issue_key = lambda iid: iid.split(':', 1)[1].replace(':', '|')
day = lambda d: datetime.date.fromisoformat(d).toordinal()


def main(base_version, version, keep_current=False, dry_run=False):
    base, release = FOUNDATION/('v'+base_version), FOUNDATION/('v'+version)
    date = datetime.date.today().isoformat()
    if (release/'manifest.json').exists() and json.loads((release/'manifest.json').read_text())['status'] == 'released':
        raise SystemExit('Release '+version+' is immutable.')
    manifest = load(base/'manifest.json')
    assert manifest['status'] == 'released'
    for entry in manifest['files']:
        if file_sha(base/entry['path']) != entry['sha256']:
            raise ValueError('Base release file changed: '+entry['path'])
    src = sqlite3.connect((base/'research.sqlite').as_uri()+'?mode=ro', uri=True)
    src.row_factory = sqlite3.Row
    shards = pinned_shards(src)

    # 0. The corrections, and what they touch.
    C = load(CHECK/'corrections.json')
    issue_date = {r['id']: r['publication_date'] for r in src.execute('SELECT id, publication_date FROM issues')}
    issue_paper = {r['id']: (r['newspaper_id'], r['edition']) for r in src.execute('SELECT id, newspaper_id, edition FROM issues')}
    page_issue = {r['id']: r['issue_id'] for r in src.execute('SELECT id, issue_id FROM pages')}
    page_no = {r['id']: r['page_number'] for r in src.execute('SELECT id, page_number FROM pages')}
    to_date = {}
    for c in C['issue_dates']:
        assert issue_date[c['issue_id']] == c['filed_date'] == c['issue_id'].split(':')[2], c['issue_id']
        to_date[c['issue_id']] = c['printed_date']
    to_issue = {}
    for c in C['page_issues']:
        assert page_issue[c['page_id']] == c['filed_issue'] == 'issue:'+c['page_id'].split(':', 1)[1].rsplit(':', 1)[0], c['page_id']
        assert issue_paper[c['printed_issue']] == issue_paper[c['filed_issue']] and c['printed_issue'] not in to_date, c['page_id']
        to_issue[c['page_id']] = c['printed_issue']
    issue_after = dict(issue_date, **to_date)
    taken = collections.Counter((issue_paper[i][0], d, issue_paper[i][1]) for i, d in issue_after.items())
    assert max(taken.values()) == 1, 'two issues of one paper and edition on one date'
    page_issue_after = dict(page_issue, **to_issue)
    assert max(collections.Counter((i, page_no[p]) for p, i in page_issue_after.items()).values()) == 1, 'two pages of one number in an issue'
    pdate = lambda pid: issue_after[page_issue_after[pid]]   # the printed date of any page
    moved = {p: pdate(p) for p in page_issue if pdate(p) != issue_date[page_issue[p]]}   # pages whose date changes
    assert len(moved) == 26 and set(to_issue) <= set(moved)
    second = {c['page_id']: c['scan_of'] for c in C['second_scans']}
    assess = {r['page_id']: dict(r) for r in src.execute("SELECT v.page_id, a.* FROM page_assessments a JOIN page_versions v ON v.id=a.page_version_id WHERE a.run_id='run:eligibility-v1'")}
    for p, q in second.items():
        assert assess[p]['eligible'] == 1 and assess[q]['eligible'] == 1 and page_no[p] == page_no[q] and issue_paper[page_issue[p]] == issue_paper[page_issue[q]], p
        assert p not in moved and q not in moved
    pages = set(moved) | set(second)   # the pages whose printings and matches are made again, or go
    pm_rows = pq.read_table(base/'derived/revx_page_map.parquet').to_pylist()
    pmap = {r['page_id']: r['revx_text_of'] for r in pm_rows}
    assert not pages & (set(pmap) | set(pmap.values())), 'a corrected page is in the RevX page map'
    sources_of = collections.defaultdict(list)
    for m in pm_rows:
        sources_of[m['revx_text_of']].append(m)
    filed_page = lambda transcription, text_page: pmap.get(text_page, text_page) if transcription == 'RevX' else text_page
    marks = ','.join('?'*len(pages))
    reviewed = {r[0]: r[1] for r in src.execute(f'SELECT o.id, v.page_id FROM observations o JOIN page_versions v ON v.id=o.page_version_id WHERE v.page_id IN ({marks})', sorted(pages))}
    assert set(reviewed) == REVIEWED_ON_CORRECTED and set(reviewed.values()) <= set(moved), reviewed
    reviewed_dates = {o: {'page_id': p, 'from': issue_date[page_issue[p]], 'to': pdate(p)} for o, p in reviewed.items()}
    audit_pages = {r['scan_check_page_id'] for r in pq.read_table(base/'derived/matched_audit.parquet', columns=['scan_check_page_id']).to_pylist()}
    assert not audit_pages & pages, 'an audited printing stands on a corrected page'

    # 1. Matches: those of these pages, replaced by the matches made in the windows of their printed dates.
    mt = pq.read_table(base/'derived/reuse_matches.parquet')
    mrows = mt.to_pylist()
    hit = lambda m: m['a_text_page_id'] in pages or m['b_text_page_id'] in pages
    old_m = [m for m in mrows if hit(m)]
    on_moved = [m for m in old_m if m['a_text_page_id'] in moved or m['b_text_page_id'] in moved]
    filed = [m for ms in load(CHECK/'matches_filed.json').values() for m in ms]
    sig = lambda pa_, pb, sa, sb: (pa_, pb, sa[0], sa[1], sb[0], sb[1])
    assert sorted(sig(m['a_text_page_id'], m['b_text_page_id'], (m['a_span_start'], m['a_span_end']), (m['b_span_start'], m['b_span_end'])) for m in on_moved) == \
        sorted(sig(page_of_key(m['a']), page_of_key(m['b']), m['a_span'], m['b_span']) for m in filed), 'the stored matches of these pages are the ones match_moved_pages.py reproduced'
    printed = [m for ms in load(CHECK/'matches_printed.json').values() for m in ms]
    new_m = []
    for m in printed:
        ta, tb = page_of_key(m['a']), page_of_key(m['b'])
        assert ta not in second and tb not in second and (ta in moved or tb in moved)
        assert m['a_date'] == pdate(ta) and m['b_date'] == pdate(tb), 'match dates are the printed dates'
        new_m.append({'a_page_id': pmap.get(ta, ta), 'b_page_id': pmap.get(tb, tb), 'a_date': m['a_date'], 'b_date': m['b_date'],
                      'a_span_start': m['a_span'][0], 'a_span_end': m['a_span'][1], 'b_span_start': m['b_span'][0], 'b_span_end': m['b_span'][1],
                      'matched_words': m['matched_words'], 'similarity': m['similarity'], 'seeds': m['seeds'], 'main': m['main'], 'strict': m['strict'],
                      'run_id': RUN_MATCH, 'a_text_page_id': ta, 'b_text_page_id': tb})
    kept_m = [m for m in mrows if not hit(m)]
    match_rows = kept_m + new_m

    # 2. Stories: the printings on these pages leave; the new matches join stories or make new ones.
    apps = pq.read_table(base/'derived/reuse_family_appearances.parquet')
    app_schema = apps.schema
    prints = apps.to_pylist()
    fams = {f['family_id']: f for f in pq.read_table(base/'derived/reuse_families.parquet').to_pylist()}
    fam_schema = pq.read_schema(base/'derived/reuse_families.parquet')
    gone = [p for p in prints if p['page_id'] in pages or p['text_page_id'] in pages]
    assert all(p['page_id'] in pages and p['text_page_id'] in pages for p in gone)
    left = [p for p in prints if not (p['page_id'] in pages or p['text_page_id'] in pages)]
    by_fam = collections.defaultdict(list)
    for p in left:
        by_fam[p['family_id']].append(p)
    touched = sorted({p['family_id'] for p in gone})
    # Unlike v0.10.2, whose moved pages lay two years from their filed dates, these move by days or weeks, and the new
    # matches re-find most of their pairs. So the passages join first, and only then does a story that keeps one
    # newspaper drop, or a printing that no longer matches the rest of its story leave it: a story whose pairs are
    # found again keeps its id and its printings.

    # New passages: union-find over the new main matches; overlapping spans on one page are one passage.
    nodes, parent, on_page = [], [], collections.defaultdict(list)
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    def node(page, span):
        for i in on_page[page]:
            s = nodes[i]['span']
            if span[0] < s[1] and s[0] < span[1]:
                s[0], s[1] = min(s[0], span[0]), max(s[1], span[1])
                return i
        nodes.append({'page': page, 'span': list(span), 'words': collections.Counter()})
        parent.append(len(parent)); on_page[page].append(len(nodes)-1)
        return len(nodes)-1
    main_pairs = []
    for m in printed:
        if not m['main']:
            continue
        a, b = node(page_of_key(m['a']), m['a_span']), node(page_of_key(m['b']), m['b_span'])
        parent[find(a)] = find(b)
        main_pairs.append((a, b, m))
        nodes[a]['words'][b] += m['matched_words']; nodes[b]['words'][a] += m['matched_words']
    for page, idx in on_page.items():   # spans widened after insertion can now overlap
        for x in idx:
            for y in idx:
                if x < y and overlap(nodes[x]['span'], nodes[y]['span']):
                    parent[find(x)] = find(y)
    left_on_page = collections.defaultdict(list)
    for fid, ps in by_fam.items():
        for p in ps:
            left_on_page[p['text_page_id']].append(p)
    for i, n in enumerate(nodes):
        n['in'] = collections.Counter()
        if n['page'] not in pages:
            for p in left_on_page.get(n['page'], []):
                o = sum(overlap(b, n['span']) for b in json.loads(p['blocks_json']))
                if o:
                    n['in'][p['family_id']] += o
    comps = collections.defaultdict(list)
    for i in range(len(nodes)):
        comps[find(i)].append(i)
    joins, new_groups, bridges, skipped_same_page = collections.defaultdict(list), [], [], []
    story_of = {}
    for root, idx in comps.items():
        linked = collections.Counter()
        for i in idx:
            if nodes[i]['in']:
                for fid in nodes[i]['in']:   # the words this story shares with the component's passages on the corrected pages
                    linked[fid] += sum(w for j, w in nodes[i]['words'].items() if nodes[j]['page'] in pages)
        if not linked:
            new_groups.append(idx)
            continue
        fid = max(linked, key=lambda f: (linked[f], f))
        if len(linked) > 1:
            bridges.append({'joined': fid, 'not_joined': sorted(f for f in linked if f != fid)})
        have = {p['text_page_id'] for p in by_fam[fid]}
        for i in idx:
            n = nodes[i]
            if fid in n['in']:
                story_of[i] = fid
                continue
            if n['in'] or n['page'] in have:
                skipped_same_page.append((fid, n['page']))
                continue
            joins[fid].append(i); story_of[i] = fid

    # New printings: one per story and scan page; seq continues the story's numbering.
    text = read_pages({key_of(n['page']) for n in nodes}, shards)
    def printing_rows(fid, idx, next_seq):
        idx = sorted(idx, key=lambda i: (pdate(nodes[i]['page']), nodes[i]['page'], nodes[i]['span'][0]))
        seqs = {i: next_seq + k for k, i in enumerate(idx)}
        groups = collections.defaultdict(list)
        for i in idx:
            groups[filed_page(text[key_of(nodes[i]['page'])]['source'], nodes[i]['page'])].append(i)
        out = []
        for scan_page, members in groups.items():
            reads = collections.defaultdict(list)
            for i in members:
                reads[(text[key_of(nodes[i]['page'])]['source'], nodes[i]['page'])].append(i)
            order = sorted(reads, key=lambda r: (r[0] != 'RevX', r[1] != scan_page, min(seqs[i] for i in reads[r])))
            rows_ = []
            for transcription, text_page in order:
                ms = reads[(transcription, text_page)]
                blocks = []
                for s, e in sorted(nodes[i]['span'] for i in ms):
                    if blocks and s <= blocks[-1][1] + TOUCH:
                        blocks[-1][1] = max(blocks[-1][1], e)
                    else:
                        blocks.append([s, e])
                first = min(ms, key=lambda i: (nodes[i]['span'][0], seqs[i]))
                rows_.append({'family_id': fid, 'seq': min(seqs[i] for i in ms), 'page_id': scan_page,
                              'publication_date': pdate(scan_page), 'lccn': scan_page.split(':')[1],
                              'page_number': int(scan_page.rsplit(':', 1)[1]), 'span_start': blocks[0][0], 'span_end': blocks[0][1],
                              'transcription': transcription, 'excerpt': excerpt_of(text[key_of(text_page)]['raw'], nodes[first]['span']),
                              'segments': len(ms), 'merged_seqs_json': json.dumps(sorted(seqs[i] for i in ms)), 'blocks_json': json.dumps(blocks),
                              'text_page_id': text_page, 'other_texts_json': None})
            keep = rows_[0]
            if len(rows_) > 1:
                keep['other_texts_json'] = json.dumps([{'seq': x['seq'], 'merged_seqs': json.loads(x['merged_seqs_json']), 'segments': x['segments'],
                                                        'transcription': x['transcription'], 'text_page_id': x['text_page_id'],
                                                        'blocks': json.loads(x['blocks_json']), 'excerpt': x['excerpt']} for x in rows_[1:]], ensure_ascii=False)
            out.append(keep)
        return out, next_seq + len(idx)
    added = []
    for fid, idx in sorted(joins.items()):
        top = max(max(json.loads(p['merged_seqs_json']) + [p['seq']] + [o['seq'] for o in json.loads(p['other_texts_json'] or '[]')]) for p in by_fam[fid])
        rows_, _ = printing_rows(fid, idx, top + 1)
        assert not {p['page_id'] for p in rows_} & {p['page_id'] for p in by_fam[fid]}
        by_fam[fid] += rows_; added += rows_

    # Stories that lost or gained a printing: a story left with one newspaper drops; a printing that no longer matches
    # the rest of its story by the main matches the release now holds leaves it (a story may not fall into two stories).
    main_by_page = collections.defaultdict(list)
    for i, m in enumerate(match_rows):
        if m['main']:
            main_by_page[m['a_text_page_id']].append(i); main_by_page[m['b_text_page_id']].append(i)
    dropped, splits, leave = [], [], set()   # leave: (story, scan page) of printings that no longer match the rest of their story
    for fid in sorted(set(touched) | set(joins)):
        ps = by_fam.get(fid, [])
        if len({p['lccn'] for p in ps}) < 2:
            dropped.append(fid)
            continue
        parent_s = list(range(len(ps)))
        def find_s(i):
            while parent_s[i] != i:
                parent_s[i] = parent_s[parent_s[i]]; i = parent_s[i]
            return i
        where_s = collections.defaultdict(list)
        for i, p in enumerate(ps):
            where_s[p['text_page_id']].append(i)
        def owner(page, span):
            for i in where_s.get(page, []):
                if any(overlap(b, span) for b in json.loads(ps[i]['blocks_json'])):
                    return i
            return None
        for page in where_s:
            for mi in main_by_page.get(page, []):
                m = match_rows[mi]
                a = owner(m['a_text_page_id'], (m['a_span_start'], m['a_span_end']))
                b = owner(m['b_text_page_id'], (m['b_span_start'], m['b_span_end']))
                if a is not None and b is not None:
                    parent_s[find_s(a)] = find_s(b)
        parts = collections.defaultdict(list)
        for i in range(len(ps)):
            parts[find_s(i)].append(i)
        if len(parts) > 1:   # the corrected pages joined parts of the story that do not match each other
            parts = sorted(parts.values(), key=lambda c: (-len({ps[i]['lccn'] for i in c}), -len(c), min(ps[i]['publication_date'] for i in c)))
            assert len({ps[i]['lccn'] for i in parts[0]}) >= 2 and all(len({ps[i]['lccn'] for i in c}) == 1 for c in parts[1:]), \
                'a story falls into two stories without these printings: '+fid
            by_fam[fid] = [ps[i] for i in parts[0]]
            alone = [ps[i] for c in parts[1:] for i in c]
            splits.append({'story': fid, 'printings_left': [p['page_id'] for p in alone]})
            for p in alone:
                leave.add((fid, p['page_id']))
    added_keys = {(p['family_id'], p['seq']) for p in added}
    left_in_dropped = sum((fid, p['seq']) not in added_keys for fid in dropped for p in by_fam.get(fid, []))   # the other paper's printing of a story that kept one
    for fid in dropped:
        by_fam.pop(fid, None)
    added = [p for p in added if p['family_id'] in by_fam and (p['family_id'], p['page_id']) not in leave]
    leavers_added = len(added_keys) - len(added)
    kept_prints = {fid: [p for p in by_fam[fid] if (fid, p['seq']) not in added_keys] for fid in set(touched) | set(joins) if fid in by_fam}

    made = []
    for idx in new_groups:
        rows_, _ = printing_rows(None, idx, 0)
        if len({p['lccn'] for p in rows_}) >= 2:
            made.append((idx, rows_))
    top_n = collections.Counter()
    for fid in fams:
        y, n = fid[1:].split('-')
        top_n[y] = max(top_n[y], int(n))
    made.sort(key=lambda x: (min(p['publication_date'] for p in x[1])[:4], -len({p['lccn'] for p in x[1]}), -len(x[1]), min(p['publication_date'] for p in x[1])))
    new_ids = []
    for idx, rows_ in made:
        y = min(p['publication_date'] for p in rows_)[:4]
        top_n[y] += 1
        fid = f'R{y}-{top_n[y]:04d}'
        for p in rows_:
            p['family_id'] = fid
        by_fam[fid] = rows_; added += rows_; new_ids.append(fid)
        fams[fid] = {'family_id': fid}
        for i in idx:
            story_of[i] = fid

    # Story rows. Keywords: the texts of the main matches the release holds between the story's printings.
    changed = sorted((set(touched) | set(joins)) - set(dropped))
    where = collections.defaultdict(list)   # text page -> (story, blocks)
    for fid in changed + new_ids:
        for p in by_fam[fid]:
            where[p['text_page_id']].append((fid, json.loads(p['blocks_json'])))
    owners = lambda page, span: {fid for fid, blocks in where.get(page, []) if any(overlap(b, span) for b in blocks)}
    wanted = {}
    for m in match_rows:
        if m['main'] and m['a_text_page_id'] in where and m['b_text_page_id'] in where:
            fids = owners(m['a_text_page_id'], (m['a_span_start'], m['a_span_end'])) & owners(m['b_text_page_id'], (m['b_span_start'], m['b_span_end']))
            if fids:
                wanted[sig(m['a_text_page_id'], m['b_text_page_id'], (m['a_span_start'], m['a_span_end']), (m['b_span_start'], m['b_span_end']))] = fids
    found = {}
    years = sorted({int(p['publication_date'][:4]) for fid in changed + new_ids for p in by_fam[fid]})
    files = [WORK/'reuse_all'/f'matches_{y}.json' for y in range(min(years), min(max(years) + 2, 1811))]
    files += [PROJECT/'outputs/kentucky_gazette_dates/matches_printed.json', CHECK/'matches_printed.json']
    for path in files:
        doc = load(path)
        for m in (doc['matches'] if 'matches' in doc else [x for v in doc.values() for x in v]):
            k = sig(page_of_key(m['a']), page_of_key(m['b']), m['a_span'], m['b_span'])
            if k in wanted:
                found[k] = (m['a_text'], m['b_text'])
    assert set(found) == set(wanted), f'{len(set(wanted) - set(found))} match texts not found'
    texts_all = {fid: [] for fid in changed + new_ids}
    for k, fids in wanted.items():
        for fid in fids:
            texts_all[fid] += list(found[k])
    orig_by_fam = collections.defaultdict(list)
    for p in prints:
        orig_by_fam[p['family_id']].append(p)
    first_changed = []
    for fid in changed + new_ids:
        ps = sorted(by_fam[fid], key=lambda p: (p['publication_date'], p['page_id'], p['span_start']))
        f = dict(fams[fid])
        f.update(first_date=ps[0]['publication_date'], last_date=ps[-1]['publication_date'], newspapers=len({p['lccn'] for p in ps}),
                 pages=len(ps), appearances=len(ps), run_id=RUN_MATCH,
                 long_running=day(ps[-1]['publication_date']) - day(ps[0]['publication_date']) > 120 or len(ps) > 40)
        f['keywords_json'] = json.dumps(keywords(texts_all[fid]))
        if fid in new_ids:
            f['label'] = ' '.join(ps[0]['excerpt'].split()[:12]).rstrip(',;:') + ' …'
        else:
            was_first = min(orig_by_fam[fid], key=lambda p: (p['publication_date'], p['page_id'], p['span_start']))
            if was_first['page_id'] != ps[0]['page_id']:   # a printing found again on the same page keeps the label
                first_changed.append(fid)
                f['label'] = ' '.join(ps[0]['excerpt'].split()[:12]).rstrip(',;:') + ' …'
        fams[fid] = f
    for fid in dropped:
        del fams[fid]
    printings = sorted([p for ps in by_fam.values() for p in ps], key=lambda r: (r['family_id'], r['seq']))
    assert len({(p['family_id'], p['page_id']) for p in printings}) == len(printings)
    assert len({(p['family_id'], p['seq']) for p in printings}) == len(printings)
    assert all(p['publication_date'] == pdate(p['page_id']) for p in printings), 'every printing carries its page date'
    family_rows = [fams[k] for k in sorted(fams)]

    # Titles: new stories, and stories whose first printing changed.
    t_table = pq.read_table(base/'derived/reuse_family_titles.parquet')
    titles = {t['family_id']: t for t in t_table.to_pylist() if t['family_id'] not in dropped}
    retitle = new_ids + first_changed
    need_t = {key_of(p['text_page_id']) for fid in retitle for p in by_fam[fid]} - set(text)
    text.update(read_pages(need_t, shards))
    for fid in retitle:
        ps = sorted(by_fam[fid], key=lambda p: (p['publication_date'], p['page_id'], p['span_start']))
        found_t = []
        for p in ps:
            raw = clean(text[key_of(p['text_page_id'])]['raw'])
            starts = [m.start() for m in TOKEN.finditer(raw)]
            found_t.append(analyse(raw, starts[p['span_start']] if p['span_start'] < len(starts) else len(raw)))
        t = title_for(fams[fid], found_t)
        titles[fid] = {'family_id': fid, 'title': t['title'], 'title_source': t['title_source'], 'dateline_place': t['place'],
                       'dateline_place_support': t['title_support'], 'starts_at_item': t['starts_at_item'], 'run_id': RUN_MATCH}
    title_rows = [titles[k] for k in sorted(titles)]
    assert sorted(titles) == sorted(fams)

    # Transcription checks of the new printings, by the rule of run:transcription-check-v1 (and of v0.8.1 for text filed elsewhere).
    old_checks = {(c['family_id'], c['seq']): c for c in pq.read_table(base/'derived/transcription_checks.parquet').to_pylist()}
    best_source = {page: max(ms, key=lambda m: m['share4_at'])['page_id'] for page, ms in sources_of.items()}
    more = {key_of(p['page_id']) for p in added if p['text_page_id'] != p['page_id']} | \
           {key_of(best_source[p['page_id']]) for p in added if p['transcription'] == 'CA' and p['page_id'] in best_source}
    text.update(read_pages(more - set(text), shards))
    new_checks = {}
    for p in added:
        own = text[key_of(p['text_page_id'])]
        spans = [tuple(b) for b in json.loads(p['blocks_json'])]
        if p['text_page_id'] != p['page_id']:
            c = check(p, own['RevX'], text[key_of(p['page_id'])]['CA'], spans)
        elif p['transcription'] == 'CA' and p['page_id'] in best_source:
            c = check(p, own['CA'], text[key_of(best_source[p['page_id']])]['RevX'], spans)
        else:
            c = check(p, own[p['transcription']], own['RevX' if p['transcription'] == 'CA' else 'CA'], spans)
        c['run_id'] = RUN_MATCH
        new_checks[(p['family_id'], p['seq'])] = c
    checks = [new_checks.get((p['family_id'], p['seq'])) or old_checks[(p['family_id'], p['seq'])] for p in printings]
    assert all(c['page_id'] == p['page_id'] for c, p in zip(checks, printings))
    gone_check = {(p['family_id'], p['page_id']): old_checks[(p['family_id'], p['seq'])] for p in gone}
    measures = ('status', 'contain', 'page_agree', 'span_words', 'other_words', 'segments', 'transcription')
    checks_as_before = sum(all(gone_check[(p['family_id'], p['page_id'])][k] == new_checks[(p['family_id'], p['seq'])][k] for k in measures)
                           for p in added if (p['family_id'], p['page_id']) in gone_check)

    # Topics: every story that changed, and every new one, scored again together from its excerpts: the segments
    # story-topics-v1 scored (release v0.5.2, by story and seq) for the printings that stay, the passages' excerpts for
    # the printings added now. A printing added after v0.5.2 (by v0.10.2) is represented by its stored excerpts.
    segs = collections.defaultdict(dict)
    restore = set(changed)
    for r in pq.read_table(SEGMENTS, columns=['family_id', 'seq', 'page_id', 'excerpt']).to_pylist():
        if r['family_id'] in restore:
            segs[r['family_id']][r['seq']] = (r['page_id'], r['excerpt'] or '')
    seg_ex, fallback = collections.defaultdict(list), 0
    for fid in changed:
        for p in kept_prints.get(fid, []):
            reads = [(p['text_page_id'], json.loads(p['merged_seqs_json']), p['excerpt'])] + \
                    [(o['text_page_id'], o['merged_seqs'], o['excerpt']) for o in json.loads(p['other_texts_json'] or '[]')]
            for text_page, seqs, excerpt in reads:
                if all(segs[fid].get(s, (None,))[0] == text_page for s in seqs):
                    seg_ex[fid] += [segs[fid][s][1] for s in seqs]
                else:
                    seg_ex[fid].append(excerpt or ''); fallback += 1
    node_excerpt = lambda i: excerpt_of(text[key_of(nodes[i]['page'])]['raw'], nodes[i]['span'])
    scan_page_of = lambda i: filed_page(text[key_of(nodes[i]['page'])]['source'], nodes[i]['page'])
    for fid in joins:
        if fid in by_fam:
            seg_ex[fid] += [node_excerpt(i) for i in joins[fid] if (fid, scan_page_of(i)) not in leave]
    for i, fid in story_of.items():
        if fid in new_ids:
            seg_ex[fid].append(node_excerpt(i))
    st_table = pq.read_table(base/'derived/story_topics.parquet')
    st_rows = {r['story_id']: r for r in st_table.to_pylist() if r['story_id'] not in dropped}
    tm_params = json.loads(src.execute("SELECT parameters_json FROM runs WHERE id='run:story-topics-v1'").fetchone()[0])
    model_path = PROJECT/tm_params['model_file']
    assert file_sha(model_path) == tm_params['model_sha256']
    tm = joblib.load(model_path)
    tmeta = json.loads(src.execute("SELECT value_json FROM metadata WHERE key='story_topics'").fetchone()[0])
    tid = [t['id'] for t in tmeta['topics']]
    ids = sorted(seg_ex)
    assert set(ids) == set(changed) | set(new_ids)
    got = score(seg_ex, ids, tm['vectorizer'], tm['model'])
    for sid in ids:
        s = got[sid]
        st_rows[sid] = {'story_id': sid, 'kind': 'matched', 'top_topic': tid[s['top']], 'top_share': s['top_share'], 'second_topic': tid[s['second']],
                        'printings': s['printings'], 'printing_agreement': s['agreement'], 'no_signal': s['no_signal'],
                        'weights_json': json.dumps(s['weights']), 'run_id': RUN_TOPICS}
    topic_rows = [st_rows[k] for k in sorted(st_rows)]

    # 3. Topic census: dates follow the pages' issues; second scans go. The scores do not change.
    census = pq.read_table(base/'derived/page_topic_census.parquet')
    crows = census.to_pylist()
    assert 'text_page_id' in census.schema.names   # since v0.11.7
    census_rows = []
    for r in crows:
        p = r['page_id']
        if p in second:
            continue
        if p in moved:
            d = moved[p]
            r = dict(r, date=d, year=int(d[:4]), month=d[5:7], issue=issue_key(page_issue_after[p]))
        census_rows.append(r)
    assert len(census_rows) == len(crows) - len(second) and sum(r['page_id'] in moved for r in census_rows) == len(moved)
    census_schema = census.schema

    eligible_after = sum(r['eligible'] for r in assess.values()) - len(second)
    was_on_moved = {(p['family_id'], p['page_id']): p for p in gone if p['page_id'] in moved}
    now_on_moved = {(p['family_id'], p['page_id']): p for p in added if p['page_id'] in moved}
    again = set(was_on_moved) & set(now_on_moved)
    found_again = {'same_story_and_page': len(again), 'same_blocks': sum(was_on_moved[k]['blocks_json'] == now_on_moved[k]['blocks_json'] for k in again),
                   'same_excerpt': sum(was_on_moved[k]['excerpt'] == now_on_moved[k]['excerpt'] for k in again),
                   'not_found_again': sorted('|'.join(k) for k in set(was_on_moved) - again), 'new': sorted('|'.join(k) for k in set(now_on_moved) - again),
                   'added_elsewhere': sum(p['page_id'] not in moved for p in added)}
    summary = {
        'issues_redated': len(to_date), 'pages_moved_to_another_issue': len(to_issue), 'second_scan_pages': len(second),
        'pages_with_a_new_date': len(moved), 'eligible_pages': {'before': sum(r['eligible'] for r in assess.values()), 'after': eligible_after},
        'reviewed_printings_on_corrected_pages': reviewed_dates,
        'matches': {'removed': len(old_m), 'removed_main': sum(m['main'] for m in old_m), 'removed_with_second_scans_only': len(old_m) - len(on_moved),
                    'added': len(new_m), 'added_main': sum(m['main'] for m in new_m), 'before': len(mrows), 'after': len(match_rows)},
        'printings': {'removed': len(gone), 'removed_on_second_scans': sum(p['page_id'] in second for p in gone),
                      'removed_with_dropped_stories': left_in_dropped, 'removed_as_no_longer_matched': len(leave) - leavers_added, 'added': len(added),
                      'added_but_left_again': leavers_added,
                      'added_to_stories': len(added) - sum(len(by_fam[f]) for f in new_ids), 'passages_joined': sum(len(v) for f, v in joins.items() if f in by_fam),
                      'in_new_stories': sum(len(by_fam[f]) for f in new_ids), 'before': len(prints), 'after': len(printings),
                      'passages_not_added': len(skipped_same_page), 'printings_of_the_moved_pages_found_again': found_again},
        'stories': {'dropped': dropped, 'lost_a_printing': sorted(set(touched) - set(dropped)), 'split': splits, 'joined': len(joins), 'new': new_ids,
                    'bridges_not_merged': bridges, 'first_printing_changed': first_changed, 'before': len({p['family_id'] for p in prints}), 'after': len(family_rows)},
        'checks_added': dict(collections.Counter(c['status'] for c in new_checks.values())), 'checks_as_before_for_printings_found_again': checks_as_before,
        'topics_scored': len(ids), 'topic_excerpt_fallbacks': fallback,
        'census': {'rows_before': len(crows), 'rows_after': len(census_rows), 'second_scan_rows_removed': len(second), 'rows_redated': len(moved)},
    }
    print(json.dumps(summary, indent=1, ensure_ascii=False), flush=True)
    if dry_run:
        return summary

    # 4. Write the release.
    if release.exists():
        shutil.rmtree(release)   # only an unreleased draft
    shutil.copytree(base, release, ignore=shutil.ignore_patterns('research.sqlite', 'manifest.json', 'validation.json', 'tables'))
    (release/'manifest.json').write_text(J({'status': 'draft', 'version': version}), encoding='utf8')
    (release/'tables').mkdir()
    db = sqlite3.connect(release/'research.sqlite')
    src.backup(db)
    src.close()
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')

    def source(path, kind):
        path = PROJECT/path
        rel = path.relative_to(PROJECT).as_posix()
        digest = file_sha(path)
        sid = 'source:'+sha(rel+'@'+digest)[:24]
        if not db.execute('SELECT 1 FROM sources WHERE id=?', (sid,)).fetchone():
            target = f'sources/v{version}__'+rel.replace('/', '__')
            shutil.copyfile(path, release/target)
            db.execute('INSERT INTO sources VALUES (?,?,?,?,?,?,?)', (sid, target, digest, path.stat().st_size, kind, None, 'sha256_verified_at_build'))
        return sid

    corrections_src = source('outputs/filing_corrections_1802/corrections.json', 'correction_ledger')
    for rel, kind in [('outputs/filing_corrections_1802/README.md', 'documentation'),
                      ('outputs/filing_corrections_1802/mastheads_1802.json', 'model_output'), ('outputs/filing_corrections_1802/second_scan_1802.json', 'model_output'),
                      ('outputs/filing_corrections_1802/check_ni_1802.py', 'analysis_code'), ('outputs/story_discovery_1802/README.md', 'documentation')]:
        source(rel, kind)
    rematch_code = source('outputs/filing_corrections_1802/match_moved_pages.py', 'analysis_code')
    for rel, kind in [('matches_filed.json', 'model_output'), ('matches_printed.json', 'model_output'), ('rematch_summary.json', 'model_output_summary')]:
        source('outputs/filing_corrections_1802/'+rel, kind)
    fix_code = source('work/archive_data/correct_filing_1802.py', 'migration_code')
    for rel in ('work/reuse_all.py', 'work/reuse_families_all.py', 'work/reuse_titles_all.py', 'work/transcription_check.py',
                'work/recheck_full_corpus.py', 'outputs/kentucky_gazette_dates/rematch.py'):
        source(rel, 'analysis_code')
    source('work/archive_data/validate.py', 'validation_code')
    rs = load(CHECK/'rematch_summary.json')
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_FIX, 'Filing faults of the National Intelligencer of 1802 corrected: seven issues dated as printed, the four pages of a second scan left out of the analysis',
               J({'issues_redated': len(to_date), 'pages_moved_to_another_issue': len(to_issue), 'second_scan_pages': len(second),
                  'evidence': 'the first pages read on their scans by the 1802 review (AI reviewers); the mastheads in the RevX text, the weekdays and the shared text of the second scan recorded by check_ni_1802.py',
                  'ids': 'issue and page ids keep the filed date and issue'}), corrections_src, date, 'automated', 0))
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_MATCH, 'The pages whose date changed matched again in the windows of their printed dates; the second-scan pages\' matches removed; stories, printings, titles and checks updated',
               J({'fix_run_id': RUN_FIX, 'matcher_rules': rs['rules'], 'reproduced_with_filed_dates': rs['filed_dates']['reproduced'],
                  'windows': sorted({w['year'] for w in rs['printed_dates']['windows']}), 'matches_removed': len(old_m), 'matches_added': len(new_m),
                  'family_rule': 'main profile; a passage joins the story whose printing its partner overlaps; existing printings keep their spans; stories are not merged',
                  'keywords': 'texts of the main matches the release holds between the story\'s printings', 'checked_against_scans': False}), rematch_code, date, 'automated', 0))
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_TOPICS, 'Frozen 24-topic model applied to the printed excerpts of the matched stories the filing correction changed',
               J({**tm_params, 'batches': 'the stories that changed and the new ones, together', 'stories': len(ids),
                  'excerpts': 'v0.5.2 segments by story and seq for printings that stay; the passages\' excerpts for printings added now; stored excerpts for printings added after v0.5.2',
                  'stored_excerpt_fallbacks': fallback}), fix_code, date, 'automated', 0))

    log = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='table_corrections'").fetchone()[0])
    entry = lambda pointer, table, id_, column, old, new, reason: {'release': version, 'ledger': None, 'source_id': corrections_src, 'run_id': RUN_FIX,
                                                                    'pointer': POINTER+pointer, 'table': table, 'id': id_,
                                                                    'column': column, 'from': old, 'to': new, 'reason': reason}
    for i, c in enumerate(C['issue_dates']):
        db.execute('UPDATE issues SET publication_date=? WHERE id=?', (c['printed_date'], c['issue_id']))
        log.append(entry(f'/issue_dates/{i}', 'issues', c['issue_id'], 'publication_date', c['filed_date'], c['printed_date'],
                         'The collection files this issue under another date than it prints: ' + c['evidence']))
    db.commit()
    db.execute('PRAGMA defer_foreign_keys=ON')   # pages trade places between two issues; the issue numbers stay unique throughout
    for c in C['page_issues']:
        db.execute('UPDATE pages SET issue_id=? WHERE id=?', ('issue:in-transit:'+c['page_id'], c['page_id']))
    for i, c in enumerate(C['page_issues']):
        db.execute('UPDATE pages SET issue_id=? WHERE id=?', (c['printed_issue'], c['page_id']))
        log.append(entry(f'/page_issues/{i}', 'pages', c['page_id'], 'issue_id', c['filed_issue'], c['printed_issue'],
                         'The collection files this page in another issue than it belongs to: ' + c['evidence']))
    db.commit()
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
    for i, c in enumerate(C['second_scans']):
        pv = assess[c['page_id']]['page_version_id']
        db.execute("UPDATE page_assessments SET eligible=0 WHERE page_version_id=? AND run_id='run:eligibility-v1'", (pv,))
        e = entry(f'/second_scans/{i}', 'page_assessments', pv, 'eligible', 1, 0,
                  'A second scan of ' + c['scan_of'] + ', filed under another date; left out of the analysis like an exact duplicate: ' + c['evidence'])
        e['row_run_id'] = 'run:eligibility-v1'
        log.append(e)
    db.execute("UPDATE metadata SET value_json=? WHERE key='table_corrections'", (J(log),))
    fc_meta = {
        'status': 'from the scan check of the 1802 review; scans read by AI reviewers; not an independent review',
        'release': version, 'run_ids': [RUN_FIX, RUN_MATCH, RUN_TOPICS], 'evidence_source_id': corrections_src,
        'ids': 'issue and page ids keep the filed date and issue: they are the keys of the source rows and scan files; issues.publication_date is the printed date and pages.issue_id the issue a page belongs to',
        'issue_dates': [{k: c[k] for k in ('issue_id', 'filed_date', 'printed_date')} for c in C['issue_dates']],
        'page_issues': [{k: c[k] for k in ('page_id', 'filed_issue', 'printed_issue')} for c in C['page_issues']],
        'second_scans': [{'page_id': c['page_id'], 'scan_of': c['scan_of'], 'eligible': {'from': 1, 'to': 0}} for c in C['second_scans']],
        'eligible_pages': summary['eligible_pages'], 'reviewed_printings_on_corrected_pages': reviewed_dates,
        'matched_layer': {k: summary[k] for k in ('matches', 'printings', 'stories')},
        'topic_census': dict(summary['census'], rule='dates follow the issues; the rows of the second-scan pages go; scores unchanged'),
        'not_changed': {'reviewed': 'every reviewed table; the one reviewed printing on a corrected page keeps its row and takes the printed date of its issue',
                        'matched_audit': 'no sample story has a printing on these pages', 'revx_page_map': 'unchanged; none of these pages is in it',
                        'other_matches': 'matches between other pages are kept as released; re-running these windows in full could change a few through the common-fingerprint counts'}}
    db.execute('INSERT INTO metadata VALUES (?,?)', ('filing_corrections_1802', J(fc_meta)))
    fc_before = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='filing_corrections'").fetchone()[0])
    fc_before['later_releases'] = fc_before.get('later_releases', []) + [{'release': version, 'metadata_key': 'filing_corrections_1802', 'run_id': RUN_FIX}]
    db.execute("UPDATE metadata SET value_json=? WHERE key='filing_corrections'", (J(fc_before),))
    idc = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='issue_date_corrections'").fetchone()[0])
    idc['later_releases'] = idc.get('later_releases', []) + [{'release': version, 'issues': len(to_date), 'metadata_key': 'filing_corrections', 'run_id': RUN_FIX}]
    db.execute("UPDATE metadata SET value_json=? WHERE key='issue_date_corrections'", (J(idc),))
    reuse = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='reuse_layer'").fetchone()[0])
    reuse.update(families=len(family_rows), family_appearances=len(printings), matches_broad=len(match_rows), matches_main=sum(m['main'] for m in match_rows),
                 families_by_newspapers={str(k): v for k, v in sorted(collections.Counter(f['newspapers'] for f in family_rows).items())},
                 filing_corrections_1802_rematch={'run_id': RUN_MATCH, 'windows': rs['printed_dates']['windows'], **summary['matches']})
    db.execute("UPDATE metadata SET value_json=? WHERE key='reuse_layer'", (J(reuse),))
    pmeta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='printings'").fetchone()[0])
    pmeta.update(printings=len(printings), filing_corrections_1802={'run_id': RUN_MATCH, **summary['printings']})
    db.execute("UPDATE metadata SET value_json=? WHERE key='printings'", (J(pmeta),))
    by_story = collections.defaultdict(list)
    for c in checks:
        by_story[c['family_id']].append(c['status'])
    cmeta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='transcription_check'").fetchone()[0])
    cmeta.update(printings=len(checks), status_counts={s: sum(c['status'] == s for c in checks) for s in STATUSES},
                 status_by_matched_transcription={t: {s: sum(c['status'] == s and c['transcription'] == t for c in checks) for s in STATUSES} for t in ('RevX', 'CA')},
                 stories_by_status=dict(collections.Counter('all printings confirmed' if all(s == 'confirmed' for s in v) else
                                                            'at least one confirmed' if 'confirmed' in v else 'none confirmed' for v in by_story.values())),
                 filing_corrections_1802={'run_id': RUN_MATCH, 'added': len(new_checks), 'removed_with_printings': len(gone)})
    db.execute("UPDATE metadata SET value_json=? WHERE key='transcription_check'", (J(cmeta),))
    tmeta_t = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='reuse_titles'").fetchone()[0])
    tmeta_t.update(families=len(title_rows), by_source=dict(sorted(collections.Counter(t['title_source'] for t in title_rows).items())),
                   starts_at_item=sum(t['starts_at_item'] for t in title_rows), filing_corrections_1802={'run_id': RUN_MATCH, 'made': len(retitle)})
    db.execute("UPDATE metadata SET value_json=? WHERE key='reuse_titles'", (J(tmeta_t),))
    tmeta.update(stories=dict(sorted(collections.Counter(r['kind'] for r in topic_rows).items())), runs=list(dict.fromkeys(tmeta.get('runs', []) + [RUN_TOPICS])))
    db.execute("UPDATE metadata SET value_json=? WHERE key='story_topics'", (J(tmeta),))
    release_meta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='release'").fetchone()[0])
    release_meta.update(version=version, date=date, previous_release=base_version)
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    history = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='migration_history'").fetchone()[0])
    history.append({'from': base_version, 'to': version, 'date': date, 'ledger': None, 'run_id': [RUN_FIX, RUN_MATCH, RUN_TOPICS],
                    'note': 'seven National Intelligencer issues of 1802 dated as printed; the four pages of a second scan left out; their matches made again'})
    db.execute("UPDATE metadata SET value_json=? WHERE key='migration_history'", (J(history),))
    db.commit()

    pq.write_table(pa.Table.from_pylist(census_rows, schema=census_schema), release/'derived/page_topic_census.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist(match_rows, schema=mt.schema), release/'derived/reuse_matches.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist(printings, schema=app_schema), release/'derived/reuse_family_appearances.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist(family_rows, schema=fam_schema), release/'derived/reuse_families.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist(title_rows, schema=t_table.schema), release/'derived/reuse_family_titles.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist(topic_rows, schema=st_table.schema), release/'derived/story_topics.parquet', compression='zstd')
    tc_schema = pq.read_schema(base/'derived/transcription_checks.parquet')
    pq.write_table(pa.Table.from_pylist(checks, schema=tc_schema), release/'derived/transcription_checks.parquet', compression='zstd')

    view = load(release/'views/pulse_boyd.json')
    view.update(schema_version=version, release_id='newspapers-v'+version)
    (release/'views/pulse_boyd.json').write_text(json.dumps(view, ensure_ascii=False, indent=2), encoding='utf8')
    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        with (release/'tables'/f'{table}.jsonl').open('w', encoding='utf8', newline='\n') as f:
            for row in db.execute(f'SELECT * FROM {table} ORDER BY 1'):
                values = dict(row)
                for k in list(values):
                    if k.endswith('_json') and values[k] is not None:
                        values[k[:-5]] = json.loads(values.pop(k))
                f.write(J(values)+'\n')
    db.close()
    shutil.copyfile(HERE/'README.md', release/'README.md')
    from validate import validate
    results = validate(release)
    (release/'validation.json').write_text(json.dumps(results, indent=2), encoding='utf8')
    files = [{'path': p.relative_to(release).as_posix(), 'bytes': p.stat().st_size, 'sha256': file_sha(p)}
             for p in sorted(release.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    out = dict(manifest, version=version, status='released', created_date=date, previous_release=base_version, observed_publications_added=0,
               build_command=f'python work/archive_data/correct_filing_1802.py {base_version} {version}'+(' --keep-current' if keep_current else ''),
               counts=results['counts'], files=files,
               filing_corrections={'issues_redated': len(to_date), 'pages_moved_to_another_issue': len(to_issue), 'second_scan_pages': len(second),
                                   'matches_removed': len(old_m), 'matches_added': len(new_m), 'printings': len(printings), 'stories': len(family_rows)})
    for k in ('issue_date_corrections', 'observed_publications_added'):
        out.setdefault(k, manifest.get(k)) if k in manifest else None
    (release/'manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    if not keep_current:
        (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': version, 'path': 'v'+version, 'manifest_sha256': file_sha(release/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(release), 'checks': len(results['checks']), 'files': len(files), 'current_moved': not keep_current}), flush=True)
    return summary


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0], args[1], keep_current='--keep-current' in sys.argv, dry_run='--dry-run' in sys.argv)
