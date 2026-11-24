"""Write ledgers/stories_1788.json: reviewed stories of 1788, round one.

1788 is read by the thin-year rule the owner chose on 23 November 2026 (docs/rules-and-exceptions.md, Y-THIN), as amended the
same night (the owner's choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the
newspapers that survive for its weeks, and by at least 4 newspapers; digests are not. The newspapers that survive for an item's
weeks are those with an eligible issue between its first and last printing, and at least in the three weeks from its first
printing. As in R-01, the eligible items printed by every newspaper that survives for their weeks are admitted, and the other
eligible items are chosen to cover the months and the kinds of news (a target, not a quota); one affair's items are handled as
in X-1800-01. Sub-stories (C-01), private persons (R-04) and the list of items read and not admitted (R-03) apply as in every
year (outputs/story_discovery_1788/README.md).

The automatic families first printed in 1788 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1787 over the 1788 pages
(items_from_1787.json); every item in 3 or more papers was counted by machine, by about 100 words of its text from the finder's
position, over every page, and the counts were joined into documents; the news among them was counted again by about 70 words
from its own opening (counts_1788.json). The 1788 pages are those whose issue the data release dates to 1788
(work/year_search_pages.py 1788 ... --printed-dates). 1788 has 7 catalogue series, which are 6 papers (C-04): the New-York
Journal under two catalogue numbers (sn83030566, daily, to 26 July; sn83030567, weekly, from 31 July). The New-York Packet
(5 issues) and the Independent Journal (2 issues) survive only in a few weeks, so most items need all 4 of the other papers.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1788_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1788.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1788/search_pages.json).
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1788'
D = PROJECT/'outputs/story_discovery_1788'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1788_review.json'
OUT = HERE/'stories_1788.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83030007': 'The Daily Advertiser', 'sn83030566': 'The New-York Journal', 'sn83030567': 'The New-York Journal',
         'sn83025587': 'The New-Hampshire Gazette', 'sn82014784': 'The Kentucke Gazette', 'sn83030137': 'The New-York Packet',
         'sn83030586': 'The Independent Journal'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, filed date (MM-DD in 1788), page and edition. The New-York Journal has two catalogue
    numbers in 1788 (C-04); the date picks it. The Kentucke Gazette's pages are filed as edition 2."""
    if paper == 'NYJ':
        lccn = 'sn83030566' if date <= '07-26' else 'sn83030567'
    else:
        lccn = {'DA': 'sn83030007', 'NHG': 'sn83025587', 'KG': 'sn82014784', 'NYP': 'sn83030137', 'IJ': 'sn83030586'}[paper]
    if paper == 'KG':
        ed = 2
    return f'{lccn}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()
AGAIN = {'note': 'Printed again.'}
# Story groups ('printings' lists each printing's page; a tuple adds overrides for that printing: core, role, field, note,
# words, dateline, head, back, stop), as in make_stories_1778.py.
STORIES = [
 dict(id='letter-of-the-president-of-the-federal-convention-to-a-friend-in-fredericksburg-january-1788', kind='document_group',
      label="A letter of the President of the late Federal Convention to a friend in Fredericksburg, Virginia, on his return from the Convention",
      definition="Printings of an extract of a letter 'of a late date, from the illustrious President of the late Federal Convention, to his friend in Frederickburgh, Virginia', taken from Mr. Green's Virginia Herald: 'I thank you for your kind congratulation on my safe return from the Convention'; the writer gives his view of the Constitution the Convention proposed. The letter-writer's own words, as the papers printed them.",
      role='published_document', words=50, dateline=False,
      core=[r'Extract\s+of\s+a\s+letter,?\s+of\s+a\s+late\s+date,?\s+from\s+the\s+illustrious\s+President', r'letter\s+of\s+a\s+late\s+date,?\s+from\s+the\s+illustrious\s+President\s+of\s+the\s+late\s+Federal\s+Convention'],
      first="A letter of the President of the late Federal Convention to a friend in Fredericksburg, Virginia.",
      what="the letter of the President of the late Federal Convention to a friend in Fredericksburg",
      printings=[k('DA', '01-17', 2), k('NYP', '01-18', 3), k('NYJ', '01-19', 3), k('NHG', '01-30', 3)]),
 dict(id='french-council-of-state-act-on-commerce-with-the-united-states-december-1787', kind='document_group',
      label="The King of France's Council of State, 29 December 1787: an act for the encouragement of the commerce of France with the United States",
      definition="Printings of the act 'of King's Council of State, for the Encouragement of the Commerce of France with the United States of America. December 29, 1787. Extract from the Records of the Council of State. The King, desirous of encouraging the commerce of his subjects with the United States of America'; it sets the duties and privileges on American goods in France. An act of the French government, printed after the letter with which a French official sent it.",
      role='published_document', words=50, dateline=False,
      core=[r'(?:An\s+)?ACT\s+of\s+(?:the\s+)?King\W?s\s+Council\s+of\s+State,?\s+for\s+the\s+Encouragement\s+of\s+the\s+Commerce'],
      first="The King of France's Council of State, 29 December 1787: an act for the encouragement of the commerce of France with the United States.",
      what="the act of the King of France's Council of State on commerce with the United States",
      printings=[k('DA', '04-10', 2), k('NHG', '04-30', 1), (k('DA', '05-21', 2), AGAIN), k('KG', '05-24', 2), k('NYJ', '06-11', 2)]),
 dict(id='congress-on-the-district-of-kentucky-june-1788', kind='document_group',
      label="Congress, 2 and 3 June 1788: the report that the district of Kentucky be erected into an independent State, and its committee to prepare an act",
      definition="Printings of the Journal of Congress of 2 and 3 June 1788: 'According to order the House was resolved into a Committee of the whole ... and Mr. Otis reported ... That in their opinion it is expedient that the district of Kentucky be erected into an Independent State'; on 3 June Congress agreed to the report and chose a committee of a member from each State to prepare an act. The Journal of Congress.",
      role='published_document', words=50, dateline=False,
      core=[r'According\s+to\s+order,?\s+the\s+House\s+was\s+resolved\s+into\s+a\s+Committee\s+of\s+the\s+whole[,;]?\s+and\s+after\s+some\s+time\s+the\s+President\s+resumed\s+the\s+Chair'],
      first="Congress, 2 and 3 June 1788: the report that the district of Kentucky be erected into an independent State.",
      what="the Journal of Congress of 2 and 3 June 1788 on the district of Kentucky",
      printings=[k('DA', '06-19', 2), k('NYJ', '06-21', 3), (k('NHG', '07-03', 3), {'head': 'Extract\\s+from\\s+the\\s+JOURNALS\\s+of\\s+CONGRESS,?\\s+June\\s+2,?\\s+1788\\.\\s*'}), (k('DA', '07-19', 2), dict(AGAIN, head=r'Monday,?\s+June\s+2,?\s+1788\.\s*')), (k('KG', '08-30', 1), {'head': 'June\\s+2,?\\s+1788\\.\\s*'})]),
 dict(id='virginia-convention-ratifies-the-constitution-june-1788', kind='document_group',
      label="The Virginia convention's act ratifying the Constitution, June 1788",
      definition="Printings of the Virginia convention's ratification: 'We the delegates of the people of Virginia, duly elected, in pursuance of a recommendation of the General Assembly, and now met in Convention, having fully and fairly investigated and discussed the proceedings of the Federal Convention'. The convention's own act.",
      role='published_document', words=50, dateline=False,
      core=[r'W\s?E,?\s+the\s+[Dd]elegates\s+of\s+the\s+[Pp]eople\s+of\s+Virginia'],
      first="The Virginia convention's act ratifying the Constitution, June 1788.",
      what="the Virginia convention's ratification",
      printings=[k('IJ', '07-02', 1), k('DA', '07-03', 2), k('NYJ', '07-03', 2), k('KG', '07-26', 2)]),
 dict(id='congress-on-putting-the-constitution-into-operation-13-september-1788', kind='document_group',
      label="Congress, 13 September 1788: the days for appointing electors, for choosing the President and for beginning proceedings under the Constitution",
      definition="Printings of the resolution of Congress of 13 September 1788: 'Whereas the Convention assembled in Philadelphia, pursuant to the Resolution of Congress of the 21st February, 1787, did, on the 17th of September in the same year, report to the United States in Congress assembled a Constitution'; it resolves the days for appointing electors and for their votes, and the time and place for commencing proceedings under the Constitution. The resolution of Congress; the drafts read in Congress in August are not counted.",
      role='published_document', words=50, dateline=False,
      core=[r'By\s+the\s+United\s+States\s+in\s+Congress\s+[Aa]ssembled,?\s+Sept\w*\.?\s+13,?\s*1788', r'WHEREAS\s+the\s+Convention\s+assembled\s+in\s+Philadelphia,?\s+pursuant\s+to\s+the\s+[Rr]esolution\s+of\s+Congress'],
      first="Congress, 13 September 1788: the days for appointing electors, choosing the President and beginning proceedings under the Constitution.",
      what="the resolution of Congress of 13 September 1788",
      printings=[k('DA', '09-15', 2), k('NYJ', '09-18', 3), k('NHG', '09-25', 3), k('KG', '11-01', 1)]),
 dict(id='letter-from-lorient-on-troubles-in-france-july-1788', kind='document_group',
      label="A letter from L'Orient of 17 July 1788 on troubles in France",
      definition="Printings of an extract of a letter from L'Orient, 'received by the Brig Lively ... dated July 17': 'In this unfortunate and unhappy country we cannot depend upon any thing. The King is now at WAR with his subjects, & there are many regiments of infantry that have refused'. A letter-writer's account; the New-Hampshire Gazette heads it 'SERIOUS and ACTUAL TROUBLES in FRANCE.'",
      role='report', words=50, dateline=True,
      head=r'(?:SERIOUS\s+and\s+)?ACTUAL\s+TROUBLES\s+in\s+FRANCE\.\s*',
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+L\W?Orient,?\s+received\s+by\s+the\s+Brig\s+Lively'],
      first="A letter from L'Orient of 17 July 1788 on troubles in France.",
      what="the letter from L'Orient of 17 July",
      printings=[k('NHG', '09-11', 3), (k('DA', '09-16', 2), {'head': 'BOSTON,?\\s+September\\s+9\\.\\s*'}), k('NYJ', '09-18', 3), k('KG', '11-01', 1)]),
 dict(id='nova-scotia-report-that-benedict-arnold-is-suspected-of-setting-fire-to-his-house-1788', kind='document_group',
      label="From Nova Scotia, September 1788: a report that Benedict Arnold is suspected of setting fire to his own house or store",
      definition="Printings of a paragraph: 'We learn from Nova-Scotia, that the highest suspicion prevails there, that the infamous Traitor BENEDICT ARNOLD, set fire to his own house, having previously effected an insurance in London upon it to a much larger amount than the real value of his property' (the New-York Packet and the Daily Advertiser print 'We hear' and 'his own store'). A report of a suspicion, in the papers' own words (an allegation).",
      role='report', words=50, dateline=True,
      core=[r'We\s+(?:learn|hear)\s+from\s+Nova\W?Scotia,?\s+that\s+the\s+highest\s+suspicion\s+prevails'],
      first="From Nova Scotia: a report that Benedict Arnold is suspected of setting fire to his own house or store.",
      what="the report from Nova Scotia on Benedict Arnold",
      printings=[k('NHG', '09-18', 3), k('NYP', '09-19', 3), k('DA', '09-20', 2), k('NYJ', '09-25', 2)]),
]


MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797 and 1800): "BOSTON, Nov. 30th, 1802."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False, head=None):
    for core in cores:
        m = re.search(core, text, re.I | re.S)
        if m:
            start = m.start()
            if head:   # a heading that ends directly before the core: the excerpt starts with it
                window = text[max(0, start-260):start]
                h = re.search('(?:' + head + r')[\W]*$', window, re.I | re.S)
                if h and re.sub(r'[\W_]+', '', h.group()):
                    start -= len(window) - h.start()
            if back:   # start at the beginning of the sentence that introduces the item
                cuts = [(text.rfind(b, 0, start), len(b)) for b in ('. ', '.] ', '] ', '." ', '.” ', '? ', '— ', '—')]
                cut, width = max(cuts)
                if cut >= 0 and start-cut < 250:
                    start = cut + width
            if dateline:
                d = DATELINE.search(text[max(0, start-90):start])
                if d:
                    start -= len(d.group(1))
            return start
    return None


def cut_excerpt(text, start, words, stop=None):
    """1776's cut: the opening of the item, ended at a clause boundary; the start anchor may run to 45 words.
    stop: a regex; the excerpt ends before its first match."""
    tokens = list(re.finditer(r'\S+', text[start:]))
    n = min(words, len(tokens))
    stopped = False
    if stop:
        m = re.search(stop, text[start:])
        if m and sum(1 for t in tokens if t.end() <= m.start()) < n:
            n, stopped = max(1, sum(1 for t in tokens if t.end() <= m.start())), True
    for j in range(15, n):   # RevX sometimes abridges with an ellipsis; end before it.
        if '...' in tokens[j].group() or '…' in tokens[j].group():
            n = j if tokens[j].group().startswith(('...', '…')) else j+1
            break
    else:
        j = None
    limit = n if (j is not None or stopped) else min(n+15, len(tokens))
    for j in range(n-1, limit):   # extend to the end of the clause, if one ends within 15 more words
        if re.search(r'[.;:]["”’)]*$', tokens[j].group()):
            n = j+1
            break
    end = start + tokens[n-1].end()
    excerpt = text[start:end]
    first = None
    for w in range(6, 45):
        candidate = text[start:start+tokens[min(w, n)-1].end()]
        if text.count(candidate) == 1:
            first = candidate
            break
    last = text[start+tokens[max(0, n-7)].start():end]
    return excerpt, first, last


def printings():
    for s in STORIES:
        for p in s.get('printings', []):
            key, over = (p, {}) if isinstance(p, str) else p
            yield s, key, over


def page_families():
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    out = {}
    for a in pq.read_table(RELEASE/'derived/reuse_family_appearances.parquet', columns=['family_id', 'page_id', 'publication_date']).to_pylist():
        if a['publication_date'].startswith(YEAR):
            key = a['page_id'].split(':', 1)[1].replace(':', '|')
            out.setdefault(key, []).append(a['family_id'])
    return {key: sorted(set(v)) for key, v in out.items()}


def build_rows(pages):
    rows, problems = [], []
    families = page_families()
    seen = {}
    for s, key, over in printings():
        if key not in pages:
            problems.append((s['id'], key, 'page not in the 1788 pages'))
            continue
        text_fields = pages[key]['texts']
        cores = over.get('core', s['core'])
        if key in MISFILED:     # this page's RevX slot holds another scan page's text: read the CA text of the scan page
            fields = [CA]
        else:
            fields = [over['field']] if 'field' in over else [REVX, CA]
        for field in fields:
            text = text_fields.get(field) or ''
            start = item_start(text, cores, over.get('dateline', s.get('dateline', True)), over.get('back', s.get('back', False)), over.get('head', s.get('head')))
            if start is not None:
                break
        if start is None:
            problems.append((s['id'], key, 'item start not found'))
            continue
        excerpt, first, last = cut_excerpt(text, start, over.get('words', s['words']), over.get('stop', s.get('stop')))
        if not first or text.find(last, start) < 0:
            problems.append((s['id'], key, 'anchors not unique'))
            continue
        lccn = key.split('|')[0]
        story = s['id']
        groups = [story] if 'parent' not in s else [s['parent'], story]
        earlier = seen.get(story, 0)
        seen[story] = earlier + 1
        summary = s['first'] if earlier == 0 else f"{PAPER[lccn]} prints {s['what']}."
        note = over.get('note', '')
        if key in MISFILED:
            note = (note+' ' if note else '') + ('The RevX transcription of this page is filed under another page, so the excerpt '
                                                 'comes from the older CA transcription of this scan page.')
        elif field == CA and 'field' not in over:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'printed': pages[key]['date'], 'field': field, 'excerpt_start': first, 'excerpt_end': last,
                     'excerpt': excerpt, 'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['printed'], r['page_key'], r['story']))
    for n, r in enumerate(rows, 1):   # numbered in order of printed date
        r['id'] = f'S88-{n:03}'
    return rows, problems


def build(rows, review):
    base, target = releases()
    findings, crops, boxes, notes = review.get('findings', {}), review.get('crops', {}), review.get('boxes', {}), review.get('notes', {})
    obs = []
    for r in rows:
        note = notes.get(r['id'], r['note']) or ('' if r['earliest'] else 'Same item as the other printings.')
        if r['earliest'] and not note.startswith('Earliest'):
            note = ('Earliest printing found. ' + note).strip()
        o = {'id': r['id'], 'page_key': r['page_key'], 'excerpt_start': r['excerpt_start'], 'excerpt_end': r['excerpt_end'],
             'roles': r['roles'], 'groups': r['groups'], 'summary': r['summary'], 'note': note,
             'scan_findings': findings.get(r['id'], ['pending']), 'crops': crops.get(r['id'], [])}
        if r['field'] != REVX:
            o['transcription_field'] = r['field']
        if r['family']:
            o['family'] = r['family']
        if r['id'] in boxes:
            o['scan_boxes'] = boxes[r['id']]
        obs.append(o)
    groups = [{'id': s['id'], 'kind': s['kind'], 'label': s['label'], 'definition': s['definition'],
               'admission_rule': 'Reviewed 1788 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1788/'
    return {
        'ledger_id': 'ledger:stories-1788', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1788', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1788, and of 1787 where they reach the 1788 pages (long-running ones '
                   'included), counted by machine over all 2,379 pages of 1788 in both transcriptions and joined into documents; the admitted '
                   'and chosen items counted again by their own opening, and scan checks of each admitted passage, by the thin-year rule '
                   "(Y-THIN, as amended with the owner's choice B1): eligible when printed by more than half of the papers that survive for "
                   "the item's weeks and by at least 4; eligible items printed by every paper that survives for their weeks admitted; the "
                   'others chosen to cover the months and the kinds of news'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1787.json': 'retrieval_candidates',
                             d+'counts_1788.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1788.py': 'ledger_code', 'work/archive_data/ledgers/stories_1788_review.json': 'scan_review',
                             d+'SCAN_PROTOCOL.md': 'review_protocol', d+'scan_points.json': 'review_protocol'},
        'scan_scope': 'Each crop covers the excerpt, the opening of the printed item. Long documents were not proofread in full.',
        'observations': obs, 'new_groups': groups, 'new_hierarchy': hierarchy, 'added_memberships': [], 'new_relations': [],
        'dispositions_summary': review.get('dispositions', {}),
    }


if __name__ == '__main__':
    pages = {p['key']: p for p in json.loads(PAGES.read_text(encoding='utf8'))}
    rows, problems = build_rows(pages)
    for p in problems:
        print('PROBLEM', *p)
    if '--table' in sys.argv:
        for r in rows:
            print(f"{r['id']} {r['story'][:26]:26} {r['page_key']:30} {r['field'][:4]} | {' '.join(r['excerpt'].split())[:150]} … {' '.join(r['excerpt'].split())[-60:]}")
    review = json.loads(REVIEW.read_text(encoding='utf8')) if REVIEW.exists() else {}
    if problems and '--force' not in sys.argv:
        raise SystemExit(f'{len(problems)} printings without anchors')
    if '--dry' in sys.argv:
        print('dry run:', len(rows), 'observations,', len(STORIES), 'groups; nothing written')
        raise SystemExit(0)
    OUT.write_text(json.dumps(build(rows, review), ensure_ascii=False, indent=2), encoding='utf8')
    print('wrote', OUT, len(rows), 'observations,', len(STORIES), 'groups')
