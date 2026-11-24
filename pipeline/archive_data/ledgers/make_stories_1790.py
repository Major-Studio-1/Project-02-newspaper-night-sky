"""Write ledgers/stories_1790.json: reviewed stories of 1790, round one.

1790 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN, as amended on 23 November 2026, the owner's
choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the newspapers that
survive for its weeks (those with a surviving issue between its first and last printing, and at least in the three weeks
from its first printing), and by at least 4; items printed by every newspaper that survives for their weeks are admitted;
the other eligible items are chosen to cover the months and the kinds of news; digests are not admitted. 1790 has four
papers all year and a fifth from 15 November, so an item reaches the bar when four print it; three items printed by every
paper that survives for their weeks are admitted, and the two other eligible items are chosen. The automatic families first printed in 1790 that reach 3 or more papers, long-running ones included,
were split into single printed items with work/story_items.py --long-running (items.json), and again with year 1789 over
the 1790 pages (items_from_1789.json); every item in 3 or more papers was counted again by the first 40 words of its
opening against every page of the year (papers the comparison missed were looked for again, and read), and a sweep of
word-for-word passages shared by 4 or more papers (as for 1803, X-1803-09) found items the families miss. Every admitted
and chosen item was counted by its own opening with phrase searches over all 950 pages of 1790 in both transcriptions
(work/story_phrase_search.py's patterns). See outputs/story_discovery_1790/README.md.

The 1790 pages are those whose issue the data release dates to 1790 (work/year_search_pages.py 1790 ... --printed-dates).
1790 has 5 catalogue series, which are 5 papers. Most of the Kentucky Gazette's issues are scanned twice (edition 2, C-05):
each printing is listed once, on the first scan; five of its issues survive only as edition 2.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. A report that stands inside a longer dated paragraph is counted, and its excerpt cut, by its
own opening sentence (as 1782 and 1789 counted reports inside longer paragraphs). Scan findings, crops and
hand-drawn boxes are merged from stories_1790_review.json after the scan check. A printing on a page whose RevX
transcription is filed under another scan page (derived/revx_page_map.parquet) takes its excerpt from the CA
transcription of its scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied; other years are reviewed at the same time, and the main
session renumbers at release:
    python work/archive_data/ledgers/make_stories_1790.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1790/search_pages.json). The excerpts are cut from
the 1790 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1790'
D = PROJECT/'outputs/story_discovery_1790'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1790_review.json'
OUT = HERE/'stories_1790.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn82014782': 'The Kentucky Gazette', 'sn83025587': 'The New-Hampshire Gazette', 'sn83030483': 'The Gazette of the United-States',
         'sn84023133': 'The New-Hampshire Gazetteer', 'sn84038410': 'The Patowmac Guardian'}
ONE = {'KG': 'sn82014782', 'NHG': 'sn83025587', 'GUS': 'sn83030483', 'NHGZ': 'sn84023133', 'PG': 'sn84038410'}
# Scan pages that hold another issue's sheet a second time, found by the scan check. A printing listed on such a page keeps
# its number (so the ids of the scan check stay as they were) but is not an observation: it is not a printing of its own.
SECOND_SCANS = {}
# Printings found by the scan check not to be the item: they keep their number but are not observations.
NOT_PRINTINGS = {}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1790), page and edition (2 for the Kentucky Gazette's issues
    that survive only as a second scan)."""
    return f'{ONE[paper]}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()

# Story groups. 'printings' lists each printing's page; a tuple adds overrides for that printing: core (regexes for the
# item's first words), role, field, note, words, dateline (include a dateline directly before), back (start at the
# beginning of the sentence that holds the core), stop (a regex: the excerpt ends before it).
STORIES = [
 # ---- admitted: printed by every paper that survives for their weeks ----
 dict(id='president-speech-to-both-houses-8-january-1790', kind='document_group',
      label="The President's speech to both Houses of Congress, 8 January 1790: 'I embrace with great satisfaction the opportunity, which now presents itself, of congratulating you on the present favorable prospects of our public affairs'",
      definition=("Printings of the speech the President made to the Senate and the House of Representatives in the Senate Chamber at New-York on "
                  "8 January 1790, at the opening of the session, as the papers print it from the proceedings: 'Fellow-Citizens of the Senate, and "
                  "House of Representatives. I embrace with great satisfaction the opportunity, which now presents itself, of congratulating you on "
                  "the present favorable prospects of our public affairs. The recent accession of the important State of North-Carolina to the "
                  "Constitution of the United States ...'. A correspondent's letter that quotes the speech is not counted (C-07)."),
      role='published_document', words=40, dateline=False, stop=r'The\W+recent\W+accession',
      core=[r'F\W*ELLOW\W*-?\W*CITIZENS,?\W+of\W+the\W+SENATE', r'E\W*MBRACE\W+with\W+great\W+satisfaction\W+the\W+opportunity'],
      first="New-York, January 1790: the President's speech to both Houses at the opening of the session.",
      what="the President's speech of 8 January 1790",
      printings=[k('GUS', '01-09', 3), k('NHG', '01-20', 3), k('NHGZ', '01-23', 2), k('KG', '04-05', 2)]),
 dict(id='treasury-report-of-4-march-1790-on-further-revenue', kind='document_group',
      label="Treasury Department, 4 March 1790: the Secretary of the Treasury reports 'that in his opinion, the funds in the first instance requisite towards the payment of interest on the debts of the individual States ... may be obtained from the following objects'",
      definition=("Printings of the Secretary of the Treasury's report to the House of Representatives, 'Treasury Department, March 4, 1790. In "
                  "obedience to the Order of the House of Representatives, of the second inst. The Secretary of the Treasury respectfully reports, "
                  "THAT in his opinion, the funds in the first instance requisite towards the payment of interest on the debts of the individual "
                  "States, according to the modifications proposed by him in his report of the ninth of January past, may be obtained from the "
                  "following objects: An increase of the general product of the duties on goods imported ...'. The New-Hampshire papers print it "
                  "inside their reports of the House's proceedings; the Kentucky Gazette prints it in three parts (17, 24 and 31 May), each under the "
                  "report's heading, counted once, where its opening stands."),
      role='published_document', words=75, dateline=False, stop=r'A\W*n\W+increase\W+of\W+the\W+general',
      core=[r'T\W*REASURY\W*-?\W*DEPARTMENT,?\W+March\W+4'],
      first="New-York, March 1790: the Secretary of the Treasury's report on the funds for paying interest on the states' debts.",
      what="the Secretary of the Treasury's report of 4 March 1790",
      printings=[k('GUS', '03-06', 2), k('NHG', '03-24', 1), k('NHGZ', '03-27', 1), k('KG', '05-17', 2)]),
 dict(id='anecdote-of-a-french-gentleman-1790', kind='message_group',
      label="Autumn 1790: 'The following incident lately occurred in one of the eastern States. A French Gentleman, totally unacquainted with our language ...'",
      definition=("Printings of an anecdote, headed 'Anecdote' in the New-Hampshire Gazetteer: 'The following incident lately occurred in one of the "
                  "eastern States. A French Gentleman, totally unacquainted with our language, being introduced to a circle of young ladies and "
                  "gentlemen in a country town, after the usual compliments had passed, he seated himself beside a beautiful young lady ...'. No "
                  "one is named. A story told for amusement, as the papers print it (C-10)."),
      role='report', words=45, dateline=False,
      core=[r'T\W*HE\W+following\W+incident\W+late(?:ly)?\W+oc\W*curred'],
      first="Autumn 1790: an anecdote of a French gentleman in a country town of the eastern States.",
      what="the anecdote of a French gentleman",
      printings=[k('GUS', '09-22', 1), k('NHG', '10-14', 3), k('NHGZ', '10-16', 4), k('PG', '11-15', 4)]),
 # ---- chosen ----
 dict(id='essay-on-the-idea-that-wars-are-necessary-1790', kind='message_group',
      label="Autumn 1790: 'There is a strange idea that prevails in the world, that wars are necessary at the return of different periods in the age of a nation'",
      definition=("Printings of a paragraph of comment: 'There is a strange idea that prevails in the world, that wars are necessary at the return of "
                  "different periods in the age of a nation; and on this principle there are those who justify a pleasing anticipation of this most "
                  "capital of all misfortunes: It will however be generally found on examination, that this insensibility to the misery of our "
                  "species, arises from an unprincipled love of gain ...'. A writer's opinion, as the papers print it."),
      role='report', words=55, dateline=False, stop=r'It\W+will\W+however',
      core=[r'T\W*HERE\W+is\W+a\W+strange\W+idea\W+that\W+prevails'],
      first="Autumn 1790: a paragraph against the idea that wars are necessary.",
      what="the paragraph on the idea that wars are necessary",
      printings=[k('GUS', '09-25', 3), k('NHG', '10-07', 3), k('PG', '11-22', 3), k('KG', '12-04', 3, ed=2)]),
 dict(id='boston-paragraph-the-western-posts-still-retained-november-1790', kind='message_group',
      label="Boston, November 1790: 'The Western Posts—Those barriers of the United States—are still retained by the British'",
      definition=("Printings of a Boston paragraph, dated 3 November in the New-Hampshire Gazetteer and 10 November in the Patowmac Guardian (the "
                  "New-Hampshire Gazette and the Gazette of the United States print it inside a longer review of public affairs): 'The Western "
                  "Posts—Those barriers of the United States—are still retained by the British; and we are told, have lately been strengthened by "
                  "additional fortifications and troops.—That at Niagara, in particular ...'. A paper's report and comment, in its own words."),
      role='report', words=50, dateline=True, stop=r'[Tt]he\W+half\W*-?\W*pay',
      core=[r'The\W+WESTERN\W+POSTS\W*[,—\-]*\W*[Tt]hose\W+barriers', r'[Tt]hose\W+barriers\W+of\W+the\W+United\W+States'],
      first="Boston, November 1790: a paragraph on the western posts that the British still hold.",
      what="the Boston paragraph on the Western Posts",
      printings=[k('NHG', '11-06', 2), k('NHGZ', '11-13', 2), k('GUS', '11-17', 2), k('PG', '12-06', 2)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797, 1800, 1801 and 1803): "BOSTON, August 12."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.\-]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False):
    for core in cores:
        m = re.search(core, text, re.I | re.S)
        if m:
            start = m.start()
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
            problems.append((s['id'], key, 'page not in the 1790 pages'))
            continue
        text_fields = pages[key]['texts']
        cores = over.get('core', s['core'])
        if key in MISFILED:     # this page's RevX slot holds another scan page's text: read the CA text of the scan page
            fields = [CA]
        else:
            fields = [over['field']] if 'field' in over else [REVX, CA]
        for field in fields:
            text = text_fields.get(field) or ''
            start = item_start(text, cores, over.get('dateline', s.get('dateline', True)), over.get('back', s.get('back', False)))
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
        r['id'] = f'S90-{n:03}'
    rows = [r for r in rows if r['page_key'] not in SECOND_SCANS and (r['page_key'], r['story']) not in NOT_PRINTINGS]   # keep their number, not a row
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
               'admission_rule': 'Reviewed 1790 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1790/'
    return {
        'ledger_id': 'ledger:stories-1790', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1790', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1790, and of 1789 where they reach the 1790 pages (long-running ones '
                   'included), every item in 3 or more papers counted again by the first 40 words of its opening against every page, papers that '
                   'comparison missed looked for again and read, a sweep of word-for-word passages shared by 4 or more papers for items the '
                   'families miss, phrase searches on all 950 pages of 1790 in both transcriptions for every admitted and chosen item, and scan '
                   'checks of each admitted passage, by the thin-year rule (Y-THIN as amended on 23 November 2026: an item printed by more than '
                   'half of the newspapers that survive for its weeks, and by at least 4, is eligible; items printed by every surviving paper are '
                   'admitted, the others chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1789.json': 'retrieval_candidates',
                             d+'counted_items.json': 'retrieval_candidates', d+'phrase_patterns.json': 'retrieval_patterns',
                             d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1790.py': 'ledger_code', 'work/archive_data/ledgers/stories_1790_review.json': 'scan_review',
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
