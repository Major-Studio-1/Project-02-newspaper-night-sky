"""Make a correction release that dates the misfiled Kentucky Gazette issues by their printed dates (v0.10.2).

The collection files the 106 issues of the Kentucky Gazette and General Advertiser (sn84038147) printed from 13 November
1804 to 29 December 1806 under dates two years late: the 7 printed in November and December 1804 under 1806, the one of
28 May 1805 under 1807, and the 98 printed in 1806 under 1808 (one of them, of Saturday 5 July 1806, under 3 July 1808).
outputs/kentucky_gazette_dates/ (check_dates.py, 2026-11-10) reads every masthead of the series and gives each of these
issues its printed date: 91 by a masthead with the right weekday, 13 by the two-year rule where the masthead cannot be
read or reads wrong (the weekday is one of the paper's publication days at the time), 2 on the scans. This step
(run:kentucky-gazette-rematch-v1) applies them:

1. issues.publication_date: the printed date. Issue and page ids keep the date under which the collection files the
   issue, because they are the keys of the source rows and of the scan files (pinned_scan_url, legacy_page_key). Each
   change is in metadata table_corrections with its old value and evidence; metadata issue_date_corrections sums them up.
2. derived/page_topic_census.parquet: date, year and month of the 439 pages follow their issues (key, issue and page_id
   keep the filed date, as ids).
3. Matched stories. The matcher compared these pages with the pages of the wrong years. outputs/kentucky_gazette_dates/
   rematch.py applies its rules again to these pages only, in the windows of their printed dates (and reproduces their
   stored matches exactly with the filed dates first). Here:
   - derived/reuse_matches.parquet: the matches that include one of these pages are replaced by the new ones (dates are
     printed dates; ends on a misfiled RevX page are filed under the scan page their text transcribes, as since v0.8.1).
     Matches between other papers are kept as released.
   - the printings on these pages leave their stories. A story left with one newspaper is dropped; a printing that no
     longer matches the rest of its story without them leaves it too (a story may not fall into two stories; none does).
   - the new matches (main profile) join stories by the family rule (matched spans that overlap on a page are one
     passage): a passage of these pages joins the story whose printing its partner's span overlaps; passages whose
     partners belong to no story make new stories. Existing printings keep their spans and excerpts. A passage that
     links two stories joins the one it shares the most matched words with, and the stories are not merged.
   - new printings follow the rules of v0.6.0 (one printing per story and page, blocks, merged seqs) and v0.8.1 (text
     page and scan page), with excerpts cut as work/reuse_families_all.py cuts them; seq continues each story's numbering.
   - derived/reuse_families.parquet: dates, counts, long_running, keywords recounted for the stories that changed; their
     label (and title) are made again only where their first printing changed. New stories get ids that continue their
     first year's numbering. Rows that changed carry run:kentucky-gazette-rematch-v1.
   - derived/reuse_family_titles.parquet, derived/story_topics.parquet, derived/transcription_checks.parquet: rows for the
     new stories and printings by the rules of runs reuse-titles-v1, story-topics-v1 and transcription-check-v1 (topics
     of every story that changed are scored again together, run:story-topics-kentucky-gazette); rows of dropped stories
     and printings removed.
Not changed: every reviewed table (no reviewed printing stands on these pages; the script checks this), the audit (no
sample story has a printing on them), the RevX page map (it names pages by id).

Usage (project root, Python 3.12):
    python work/archive_data/redate_issues.py 0.10.1 0.10.2 --keep-current
    python work/archive_data/redate_issues.py 0.10.1 0.10.2 --dry-run        # counts only; writes nothing
Inputs: outputs/kentucky_gazette_dates/ (issues.csv, summary.json, matches_filed.json, matches_printed.json,
rematch_summary.json, check_dates.py, rematch.py, mastheads/, README.md); work/reuse_all/matches_*.json (match texts, for
keywords); the six pinned shards in work/data/ (hashes checked against the release); release v0.5.2 (the excerpts the
topic model first scored).
"""
from pathlib import Path
import collections
import csv
import datetime
import hashlib
import json
import re
import shutil
import sqlite3
import sys
import unicodedata

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
WORK = PROJECT/'work'
FOUNDATION = PROJECT/'outputs/data_foundation'
CHECK = PROJECT/'outputs/kentucky_gazette_dates'
SEGMENTS = FOUNDATION/'v0.5.2/derived/reuse_family_appearances.parquet'   # the excerpts story-topics-v1 scored
sys.path.insert(0, str(WORK/'python_packages'))
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(HERE))
import joblib
import pyarrow as pa
import pyarrow.parquet as pq
from merge_printings import TOUCH
from refile_revx_pages import check, file_sha, pinned_shards
from reuse_families_all import STOP, TOKEN, EXCERPT_WORDS
from reuse_titles_all import analyse, clean, title_for
from add_reviewed_topics import score
from transcription_check import status as check_status

LCCN = 'sn84038147'
RUN_DATES, RUN_FIX, RUN_TOPICS = 'run:kentucky-gazette-dates-v1', 'run:kentucky-gazette-rematch-v1', 'run:story-topics-kentucky-gazette'
STATUSES = ['confirmed', 'partly', 'missing_in_other', 'other_unreadable', 'no_second_transcription']
J = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = lambda text: hashlib.sha256(text.encode('utf8')).hexdigest()
load = lambda path: json.loads(path.read_text(encoding='utf8'))
page_of_key = lambda key: 'page:'+key.replace('|', ':')
key_of = lambda pid: pid.split(':', 1)[1].replace(':', '|')
day = lambda d: datetime.date.fromisoformat(d).toordinal()


def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def read_pages(keys, shards):
    """Raw selected text and both token lists of the given pages (dataset keys), from the pinned shards."""
    from reuse_all import tokenize
    audit = {r['key']: r for r in pq.read_table(WORK/'page_audit.parquet', columns=['key', 'file', 'file_row', 'selected_source']).to_pylist() if r['key'] in keys}
    assert len(audit) == len(keys), 'pages missing from page_audit'
    by_file = collections.defaultdict(dict)
    for k, r in audit.items():
        by_file[r['file']][r['file_row']] = k
    out = {}
    for f, rows in sorted(by_file.items()):
        assert f in shards, f
        pf, offset = pq.ParquetFile(WORK/'data'/f), 0
        for g in range(pf.num_row_groups):
            n = pf.metadata.row_group(g).num_rows
            hit = [rw for rw in rows if offset <= rw < offset + n]
            if hit:
                t = pf.read_row_group(g, columns=['RevX_OCR_text', 'ca_ocr_text'])
                for rw in hit:
                    k = rows[rw]
                    revx, ca = t['RevX_OCR_text'][rw - offset].as_py() or '', t['ca_ocr_text'][rw - offset].as_py() or ''
                    source = audit[k]['selected_source']
                    out[k] = {'source': source, 'raw': revx if source == 'RevX' else ca, 'RevX': tokenize(revx), 'CA': tokenize(ca)}
            offset += n
    return out


def excerpt_of(raw, span):
    """The excerpt rule of work/reuse_families_all.py: up to 70 words from the span's start, capitals and punctuation kept."""
    raw = unicodedata.normalize('NFKC', raw).replace('ſ', 's')
    raw = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', raw)
    spans = [m.span() for m in TOKEN.finditer(raw)]
    x0, x1 = span
    if x0 >= len(spans):
        return ''
    end = spans[min(x1, x0 + EXCERPT_WORDS, len(spans)) - 1][1]
    return re.sub(r'\s+', ' ', raw[spans[x0][0]:end]).strip() + (' …' if x1 - x0 > EXCERPT_WORDS else '')


def match_texts(fids, by_fam, skip_pages):
    """The texts of each story's main matches (both ends on its printings), from the matcher's files (work/reuse_all/)."""
    out = {fid: [] for fid in fids}
    where = collections.defaultdict(list)   # text page -> (story, blocks)
    years = set()
    for fid in fids:
        for p in by_fam[fid]:
            where[p['text_page_id']].append((fid, json.loads(p['blocks_json'])))
            years.add(int(p['publication_date'][:4]))
    owners = lambda page, span: {fid for fid, blocks in where.get(page, []) if any(overlap(b, span) for b in blocks)}
    for y in range(min(years), min(max(years) + 2, 1811)):   # a pair belongs to the window of its later page
        for m in load(WORK/'reuse_all'/f'matches_{y}.json')['matches']:
            if not m['main']:
                continue
            a, b = page_of_key(m['a']), page_of_key(m['b'])
            if a in skip_pages or b in skip_pages or a not in where or b not in where:
                continue
            for fid in owners(a, m['a_span']) & owners(b, m['b_span']):
                out[fid] += [m['a_text'], m['b_text']]
    return out


def keywords(texts):
    words = collections.Counter(w for t in texts for w in t.split() if len(w) > 3 and w not in STOP)
    return [w for w, _ in words.most_common(10)]


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

    # 0. The corrections, and what may use them.
    rows = list(csv.DictReader((CHECK/'issues.csv').open(encoding='utf8')))
    fixes = [r for r in rows if r['printed_date'] != r['filed_date']]
    issue_date = {r['id']: r['publication_date'] for r in src.execute('SELECT id, publication_date FROM issues')}
    for r in fixes:
        assert issue_date[r['issue_id']] == r['filed_date'] == r['issue_id'].split(':')[2], r['issue_id']
    to_date = {r['issue_id']: r['printed_date'] for r in fixes}
    after = dict(issue_date, **to_date)
    taken = collections.Counter((i.split(':')[1], d, i.rsplit(':', 1)[1]) for i, d in after.items())
    assert max(taken.values()) == 1, 'two issues of one paper and edition on one date'
    page_issue = {p['id']: p['issue_id'] for p in src.execute('SELECT id, issue_id FROM pages')}
    pdate = lambda pid: after[page_issue[pid]]   # the printed date of any page
    pages = {p: i for p, i in page_issue.items() if i in to_date}
    page_date = {p: to_date[i] for p, i in pages.items()}
    assert len(pages) == sum(int(r['pages']) for r in fixes), 'pages of the corrected issues'
    assert not src.execute(f"SELECT COUNT(*) FROM observations o JOIN page_versions v ON v.id=o.page_version_id WHERE v.page_id IN ({','.join('?'*len(pages))})",
                           list(pages)).fetchone()[0], 'a reviewed printing stands on a corrected page'
    keys = {key_of(p) for p in pages}
    pmap = {r['page_id']: r['revx_text_of'] for r in pq.read_table(base/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()}
    sources_of = collections.defaultdict(list)
    for m in pq.read_table(base/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of', 'share4_at']).to_pylist():
        sources_of[m['revx_text_of']].append(m)
    filed_page = lambda transcription, text_page: pmap.get(text_page, text_page) if transcription == 'RevX' else text_page

    # 1. Matches: those of these pages, replaced by the matches made in the windows of their printed dates.
    mt = pq.read_table(base/'derived/reuse_matches.parquet')
    mrows = mt.to_pylist()
    hit = lambda m: m['a_text_page_id'] in pages or m['b_text_page_id'] in pages
    old_m = [m for m in mrows if hit(m)]
    filed = [m for ms in load(CHECK/'matches_filed.json').values() for m in ms]
    sig = lambda pa_, pb, sa, sb: (pa_, pb, sa[0], sa[1], sb[0], sb[1])
    assert sorted(sig(m['a_text_page_id'], m['b_text_page_id'], (m['a_span_start'], m['a_span_end']), (m['b_span_start'], m['b_span_end'])) for m in old_m) == \
        sorted(sig(page_of_key(m['a']), page_of_key(m['b']), m['a_span'], m['b_span']) for m in filed), 'the stored matches of these pages are the ones rematch.py reproduced'
    printed = [m for ms in load(CHECK/'matches_printed.json').values() for m in ms]
    new_m = []
    for m in printed:
        ta, tb = page_of_key(m['a']), page_of_key(m['b'])
        assert m['a_date'] == pdate(ta) and m['b_date'] == pdate(tb), 'match dates are the printed dates'
        new_m.append({'a_page_id': pmap.get(ta, ta), 'b_page_id': pmap.get(tb, tb), 'a_date': m['a_date'], 'b_date': m['b_date'],
                      'a_span_start': m['a_span'][0], 'a_span_end': m['a_span'][1], 'b_span_start': m['b_span'][0], 'b_span_end': m['b_span'][1],
                      'matched_words': m['matched_words'], 'similarity': m['similarity'], 'seeds': m['seeds'], 'main': m['main'], 'strict': m['strict'],
                      'run_id': RUN_FIX, 'a_text_page_id': ta, 'b_text_page_id': tb})
    kept_m = [m for m in mrows if not hit(m)]
    match_rows = kept_m + new_m
    for m in match_rows:   # every match end now carries its issue's printed date
        for s in 'ab':
            if m[s+'_text_page_id'] in pages:
                assert m[s+'_date'] == page_date[m[s+'_text_page_id']]

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
    dropped, splits, leave = [], [], set()   # leave: (story, text page) of printings that no longer match the rest of their story
    main_by_page = collections.defaultdict(list)   # text page -> main matches kept, to test whether a story still connects
    for i, m in enumerate(kept_m):
        if m['main']:
            main_by_page[m['a_text_page_id']].append(i); main_by_page[m['b_text_page_id']].append(i)
    for fid in touched:
        ps = by_fam.get(fid, [])
        if len({p['lccn'] for p in ps}) < 2:
            dropped.append(fid)
            continue
        parent = list(range(len(ps)))
        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i
        where = collections.defaultdict(list)
        for i, p in enumerate(ps):
            where[p['text_page_id']].append(i)
        def owner(page, span):
            for i in where.get(page, []):
                if any(overlap(b, span) for b in json.loads(ps[i]['blocks_json'])):
                    return i
            return None
        for page in where:
            for mi in main_by_page.get(page, []):
                m = kept_m[mi]
                a = owner(m['a_text_page_id'], (m['a_span_start'], m['a_span_end']))
                b = owner(m['b_text_page_id'], (m['b_span_start'], m['b_span_end']))
                if a is not None and b is not None:
                    parent[find(a)] = find(b)
        parts = collections.defaultdict(list)
        for i in range(len(ps)):
            parts[find(i)].append(i)
        if len(parts) > 1:   # the corrected pages joined parts of the story that do not match each other
            parts = sorted(parts.values(), key=lambda c: (-len({ps[i]['lccn'] for i in c}), -len(c), min(ps[i]['publication_date'] for i in c)))
            assert len({ps[i]['lccn'] for i in parts[0]}) >= 2 and all(len({ps[i]['lccn'] for i in c}) == 1 for c in parts[1:]), \
                'a story falls into two stories without these printings: '+fid
            by_fam[fid] = [ps[i] for i in parts[0]]
            alone = [ps[i] for c in parts[1:] for i in c]
            splits.append({'story': fid, 'printings_left': [p['page_id'] for p in alone]})
            for p in alone:
                leave.add((fid, p['text_page_id']))
    left_in_dropped = sum(len(by_fam.get(fid, [])) for fid in dropped)   # the other paper's printing of a story that kept one paper
    for fid in dropped:
        by_fam.pop(fid, None)

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
    main_pairs = []   # (node a, node b, match) of every new main match
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
    # Which existing printing does a passage on another paper's page overlap?
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
    story_of = {}   # node -> the story it ends in (joined, or already that story's printing)
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
                story_of[i] = fid   # already this story's printing (its span is kept)
                continue
            if n['in'] or n['page'] in have:
                skipped_same_page.append((fid, n['page']))   # another story's passage, or a second block on a page the story prints
                continue
            joins[fid].append(i); story_of[i] = fid

    # New printings: one per story and scan page; seq continues the story's numbering.
    text = read_pages({key_of(n['page']) for n in nodes}, shards)
    def printing_rows(fid, idx, next_seq):
        idx = sorted(idx, key=lambda i: (pdate(nodes[i]['page']), nodes[i]['page'], nodes[i]['span'][0]))
        seqs = {i: next_seq + k for k, i in enumerate(idx)}
        groups = collections.defaultdict(list)
        for i in idx:
            t = text[key_of(nodes[i]['page'])]['source']
            groups[filed_page(t, nodes[i]['page'])].append(i)
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
    # New stories: ids continue the numbering of their first year, ordered as reuse_families_all.py orders a year.
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

    # Story rows.
    changed = sorted((set(touched) - set(dropped)) | set(joins))
    texts_all = match_texts(changed, by_fam, pages)
    for fid in new_ids:
        texts_all[fid] = []
    for a, b, m in main_pairs:
        if story_of.get(a) is not None and story_of.get(a) == story_of.get(b):
            texts_all[story_of[a]] += [m['a_text'], m['b_text']]
    orig_by_fam = collections.defaultdict(list)
    for p in prints:
        orig_by_fam[p['family_id']].append(p)
    first_changed = []
    for fid in changed + new_ids:
        ps = sorted(by_fam[fid], key=lambda p: (p['publication_date'], p['page_id'], p['span_start']))
        f = dict(fams[fid])
        f.update(first_date=ps[0]['publication_date'], last_date=ps[-1]['publication_date'], newspapers=len({p['lccn'] for p in ps}),
                 pages=len(ps), appearances=len(ps), run_id=RUN_FIX,
                 long_running=day(ps[-1]['publication_date']) - day(ps[0]['publication_date']) > 120 or len(ps) > 40)
        f['keywords_json'] = json.dumps(keywords(texts_all[fid]))
        if fid in new_ids:
            f['label'] = ' '.join(ps[0]['excerpt'].split()[:12]).rstrip(',;:') + ' …'
        else:
            was_first = min(orig_by_fam[fid], key=lambda p: (p['publication_date'], p['page_id'], p['span_start']))
            if (was_first['page_id'], was_first['seq']) != (ps[0]['page_id'], ps[0]['seq']):
                first_changed.append(fid)
                f['label'] = ' '.join(ps[0]['excerpt'].split()[:12]).rstrip(',;:') + ' …'
        fams[fid] = f
    for fid in dropped:
        del fams[fid]
    printings = sorted([p for ps in by_fam.values() for p in ps], key=lambda r: (r['family_id'], r['seq']))
    assert len({(p['family_id'], p['page_id']) for p in printings}) == len(printings)
    family_rows = [fams[k] for k in sorted(fams)]

    # Titles: new stories, and stories whose first printing changed.
    t_table = pq.read_table(base/'derived/reuse_family_titles.parquet')
    titles = {t['family_id']: t for t in t_table.to_pylist() if t['family_id'] not in dropped}
    retitle = new_ids + first_changed
    need_t = {key_of(p['text_page_id']) for fid in retitle for p in by_fam[fid]} - set(text)
    text.update(read_pages(need_t, shards))
    for fid in retitle:
        ps = sorted(by_fam[fid], key=lambda p: (p['publication_date'], p['page_id'], p['span_start']))
        found = []
        for p in ps:
            raw = clean(text[key_of(p['text_page_id'])]['raw'])
            starts = [m.start() for m in TOKEN.finditer(raw)]
            found.append(analyse(raw, starts[p['span_start']] if p['span_start'] < len(starts) else len(raw)))
        t = title_for(fams[fid], found)
        titles[fid] = {'family_id': fid, 'title': t['title'], 'title_source': t['title_source'], 'dateline_place': t['place'],
                       'dateline_place_support': t['title_support'], 'starts_at_item': t['starts_at_item'], 'run_id': RUN_FIX}
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
        c['run_id'] = RUN_FIX
        new_checks[(p['family_id'], p['seq'])] = c
    checks = [new_checks.get((p['family_id'], p['seq'])) or old_checks[(p['family_id'], p['seq'])] for p in printings]
    assert all(c['page_id'] == p['page_id'] for c, p in zip(checks, printings))

    # Topics: every story that changed, and every new one, scored again together from its excerpts.
    seg_ex = collections.defaultdict(list)
    restore = set(changed)
    for r in pq.read_table(SEGMENTS, columns=['family_id', 'page_id', 'excerpt']).to_pylist():
        if r['family_id'] in restore and r['page_id'] not in pages and (r['family_id'], r['page_id']) not in leave:
            seg_ex[r['family_id']].append(r['excerpt'] or '')
    node_excerpt = lambda i: excerpt_of(text[key_of(nodes[i]['page'])]['raw'], nodes[i]['span'])
    for fid in joins:
        seg_ex[fid] += [node_excerpt(i) for i in joins[fid]]
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
    got = score(seg_ex, ids, tm['vectorizer'], tm['model'])
    for sid in ids:
        s = got[sid]
        st_rows[sid] = {'story_id': sid, 'kind': 'matched', 'top_topic': tid[s['top']], 'top_share': s['top_share'], 'second_topic': tid[s['second']],
                        'printings': s['printings'], 'printing_agreement': s['agreement'], 'no_signal': s['no_signal'],
                        'weights_json': json.dumps(s['weights']), 'run_id': RUN_TOPICS}
    topic_rows = [st_rows[k] for k in sorted(st_rows)]

    # Topic census: the pages' dates follow their issues.
    census = pq.read_table(base/'derived/page_topic_census.parquet')
    crows = census.to_pylist()
    for r in crows:
        if r['page_id'] in pages:
            d = page_date[r['page_id']]
            r.update(date=d, year=int(d[:4]), month=d[5:7])

    summary = {
        'issues_redated': len(fixes), 'pages_redated': len(pages), 'by_basis': dict(collections.Counter(r['basis'] for r in fixes)),
        'by_year': {f'{a} -> {b}': n for (a, b), n in sorted(collections.Counter((r['filed_date'][:4], r['printed_date'][:4]) for r in fixes).items())},
        'matches': {'removed': len(old_m), 'removed_main': sum(m['main'] for m in old_m), 'added': len(new_m), 'added_main': sum(m['main'] for m in new_m),
                    'before': len(mrows), 'after': len(match_rows)},
        'printings': {'removed': len(gone), 'removed_with_dropped_stories': left_in_dropped, 'removed_as_no_longer_matched': len(leave), 'added': len(added),
                      'added_to_stories': len(added) - sum(len(by_fam[f]) for f in new_ids), 'passages_joined': sum(len(v) for v in joins.values()),
                      'in_new_stories': sum(len(by_fam[f]) for f in new_ids),
                      'before': len(prints), 'after': len(printings), 'passages_not_added': len(skipped_same_page)},
        'stories': {'dropped': dropped, 'lost_a_printing': sorted(set(touched) - set(dropped)), 'split': splits, 'joined': len(joins), 'new': len(new_ids),
                    'bridges_not_merged': bridges, 'first_printing_changed': first_changed, 'before': len({p['family_id'] for p in prints}), 'after': len(family_rows)},
        'checks_added': dict(collections.Counter(c['status'] for c in new_checks.values())), 'topics_scored': len(ids),
    }
    print(json.dumps(summary, indent=1, ensure_ascii=False), flush=True)
    if dry_run:
        return summary

    # 3. Write the release.
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

    check_code = source('outputs/kentucky_gazette_dates/check_dates.py', 'analysis_code')
    issues_src = source('outputs/kentucky_gazette_dates/issues.csv', 'model_output')
    source('outputs/kentucky_gazette_dates/summary.json', 'model_output_summary')
    for scan in sorted((CHECK/'mastheads').glob('*.jpg')):
        source(scan.relative_to(PROJECT).as_posix(), 'scan_review')
    source('outputs/kentucky_gazette_dates/README.md', 'documentation')
    rematch_code = source('outputs/kentucky_gazette_dates/rematch.py', 'analysis_code')
    for rel, kind in [('matches_filed.json', 'model_output'), ('matches_printed.json', 'model_output'), ('rematch_summary.json', 'model_output_summary')]:
        source('outputs/kentucky_gazette_dates/'+rel, kind)
    fix_code = source('work/archive_data/redate_issues.py', 'migration_code')
    for rel in ('work/reuse_all.py', 'work/reuse_families_all.py', 'work/reuse_titles_all.py', 'work/transcription_check.py'):
        source(rel, 'analysis_code')
    source('work/archive_data/validate.py', 'validation_code')
    rs = load(CHECK/'rematch_summary.json')
    cs = load(CHECK/'summary.json')
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_DATES, 'Printed dates of the Kentucky Gazette issues filed two years late, from their mastheads, the paper\'s publication days and two scans',
               J({'issues_checked': cs['issues'], 'redated': cs['redated'], 'rule': cs['rule'], 'scans_read_by_eye': 2}), check_code, '2026-11-10', 'automated', 0))
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_FIX, 'Issue dates corrected; the pages of these issues matched again in the windows of their printed dates; stories, printings, titles and checks updated',
               J({'dates_run_id': RUN_DATES, 'matcher_rules': rs['rules'], 'reproduced_with_filed_dates': rs['filed_dates']['reproduced'],
                  'windows': [w['year'] for w in rs['printed_dates']['windows']], 'matches_removed': len(old_m), 'matches_added': len(new_m),
                  'family_rule': 'main profile; a passage joins the story whose printing its partner overlaps; existing printings keep their spans; stories are not merged',
                  'checked_against_scans': False}), rematch_code, date, 'automated', 0))
    db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)', (RUN_TOPICS, 'Frozen 24-topic model applied to the printed excerpts of the matched stories the date correction changed',
               J({**tm_params, 'batches': 'the stories that changed and the new ones, together', 'stories': len(ids)}), fix_code, date, 'automated', 0))
    log = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='table_corrections'").fetchone()[0])
    for r in sorted(fixes, key=lambda r: r['issue_id']):
        why = {'masthead': 'masthead date, two years before the filed date, with the right weekday',
               'two-year rule': 'filed date less two years: ' + r['note'] + '; the weekday is a publication day of the paper at the time',
               'scan': 'read on the pinned scan: ' + r['scan_note']}[r['basis']]
        db.execute('UPDATE issues SET publication_date=? WHERE id=?', (r['printed_date'], r['issue_id']))
        log.append({'release': version, 'ledger': None, 'source_id': issues_src, 'pointer': 'outputs/kentucky_gazette_dates/issues.csv#'+r['issue_id'], 'run_id': RUN_FIX,
                    'table': 'issues', 'id': r['issue_id'], 'column': 'publication_date', 'from': r['filed_date'], 'to': r['printed_date'],
                    'reason': 'The collection files this Kentucky Gazette issue two years late; printed date: ' + why + '.'})
    db.execute("UPDATE metadata SET value_json=? WHERE key='table_corrections'", (J(log),))
    db.execute('INSERT INTO metadata VALUES (?,?)', ('issue_date_corrections', J({
        'status': 'automatic from the mastheads; two issues read on the scans; not an independent review', 'run_id': RUN_DATES, 'refile_run_id': RUN_FIX,
        'series': LCCN, 'issues': len(fixes), 'pages': len(pages), 'by_basis': summary['by_basis'], 'by_year': summary['by_year'],
        'ids': 'issue and page ids keep the filed date: they are the keys of the source rows and scan files; issues.publication_date is the printed date',
        'evidence_source_id': issues_src, 'matched_layer': {k: summary[k] for k in ('matches', 'printings', 'stories')},
        'not_changed': {'reviewed': 'no reviewed printing stands on these pages', 'matched_audit': 'no sample story has a printing on these pages',
                        'revx_page_map': 'names pages by id; 4 of its rows are pages of these issues',
                        'other_matches': 'matches between other papers are kept as released; re-running these windows in full could change a few through the common-fingerprint counts'}})))
    reuse = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='reuse_layer'").fetchone()[0])
    reuse.update(families=len(family_rows), family_appearances=len(printings), matches_broad=len(match_rows), matches_main=sum(m['main'] for m in match_rows),
                 families_by_newspapers={str(k): v for k, v in sorted(collections.Counter(f['newspapers'] for f in family_rows).items())},
                 kentucky_gazette_rematch={'run_id': RUN_FIX, 'windows': rs['printed_dates']['windows'], **summary['matches']})
    db.execute("UPDATE metadata SET value_json=? WHERE key='reuse_layer'", (J(reuse),))
    pmeta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='printings'").fetchone()[0])
    pmeta.update(printings=len(printings), kentucky_gazette_redate={'run_id': RUN_FIX, **summary['printings']})
    db.execute("UPDATE metadata SET value_json=? WHERE key='printings'", (J(pmeta),))
    by_story = collections.defaultdict(list)
    for c in checks:
        by_story[c['family_id']].append(c['status'])
    cmeta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='transcription_check'").fetchone()[0])
    cmeta.update(printings=len(checks), status_counts={s: sum(c['status'] == s for c in checks) for s in STATUSES},
                 status_by_matched_transcription={t: {s: sum(c['status'] == s and c['transcription'] == t for c in checks) for s in STATUSES} for t in ('RevX', 'CA')},
                 stories_by_status=dict(collections.Counter('all printings confirmed' if all(s == 'confirmed' for s in v) else
                                                            'at least one confirmed' if 'confirmed' in v else 'none confirmed' for v in by_story.values())),
                 kentucky_gazette_redate={'run_id': RUN_FIX, 'added': len(new_checks), 'removed_with_printings': len(gone)})
    db.execute("UPDATE metadata SET value_json=? WHERE key='transcription_check'", (J(cmeta),))
    tmeta_t = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='reuse_titles'").fetchone()[0])
    tmeta_t.update(families=len(title_rows), by_source=dict(sorted(collections.Counter(t['title_source'] for t in title_rows).items())),
                   starts_at_item=sum(t['starts_at_item'] for t in title_rows), kentucky_gazette_redate={'run_id': RUN_FIX, 'made': len(retitle)})
    db.execute("UPDATE metadata SET value_json=? WHERE key='reuse_titles'", (J(tmeta_t),))
    tmeta.update(stories=dict(sorted(collections.Counter(r['kind'] for r in topic_rows).items())), runs=list(dict.fromkeys(tmeta.get('runs', []) + [RUN_TOPICS])))
    db.execute("UPDATE metadata SET value_json=? WHERE key='story_topics'", (J(tmeta),))
    release_meta = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='release'").fetchone()[0])
    release_meta.update(version=version, date=date, previous_release=base_version)
    db.execute("UPDATE metadata SET value_json=? WHERE key='release'", (J(release_meta),))
    history = json.loads(db.execute("SELECT value_json FROM metadata WHERE key='migration_history'").fetchone()[0])
    history.append({'from': base_version, 'to': version, 'date': date, 'ledger': None, 'run_id': [RUN_DATES, RUN_FIX, RUN_TOPICS],
                    'note': 'Kentucky Gazette issues filed two years late dated by their mastheads; their pages matched again in the windows of their printed dates'})
    db.execute("UPDATE metadata SET value_json=? WHERE key='migration_history'", (J(history),))
    db.commit()

    pq.write_table(pa.Table.from_pylist(crows, schema=census.schema), release/'derived/page_topic_census.parquet', compression='zstd')
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
               build_command=f'python work/archive_data/redate_issues.py {base_version} {version}'+(' --keep-current' if keep_current else ''),
               counts=results['counts'], files=files,
               issue_date_corrections={'issues': len(fixes), 'pages': len(pages), 'matches_removed': len(old_m), 'matches_added': len(new_m),
                                       'printings': len(printings), 'stories': len(family_rows)})
    (release/'manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    if not keep_current:
        (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': version, 'path': 'v'+version, 'manifest_sha256': file_sha(release/'manifest.json')}, indent=2), encoding='utf8')
    print(json.dumps({'release': str(release), 'checks': len(results['checks']), 'files': len(files), 'current_moved': not keep_current}), flush=True)
    return summary


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0], args[1], keep_current='--keep-current' in sys.argv, dry_run='--dry-run' in sys.argv)
