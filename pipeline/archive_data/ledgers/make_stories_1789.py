"""Write ledgers/stories_1789.json: reviewed stories of 1789, round one.

1789 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN, as amended on 23 November 2026, the owner's
choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the newspapers that
survive for its weeks (those with a surviving issue between its first and last printing, and at least in the three weeks
from its first printing), and by at least 4; items printed by every newspaper that survives for their weeks are admitted;
the other eligible items are chosen to cover the months and the kinds of news; digests are not admitted. 1789 has four
papers, so an item reaches the bar only when all four print it, and every eligible item is admitted by the first part;
nothing is chosen. The automatic families first printed in 1789 that reach 3 or more papers, long-running ones included,
were split into single printed items with work/story_items.py --long-running (items.json), and again with year 1788 over
the 1789 pages (items_from_1788.json); every item in 3 or more papers was counted again by the first 40 words of its
opening against every page of the year (papers the comparison missed were looked for again, and read), and a sweep of
word-for-word passages shared by 4 or more papers (as for 1803, X-1803-09) found items the families miss. Every admitted
item was counted by its own opening with phrase searches over all 742 pages of 1789 in both transcriptions
(work/story_phrase_search.py's patterns). See outputs/story_discovery_1789/README.md.

The 1789 pages are those whose issue the data release dates to 1789 (work/year_search_pages.py 1789 ... --printed-dates).
1789 has 5 catalogue series, which are 4 papers: the Kentucky Gazette is under two numbers (sn82014784 to 7 March,
sn82014782 from 14 March; C-04). Most of its issues are scanned twice (edition 2, C-05): each printing is listed once,
on the first scan.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. A report that stands inside a longer dated paragraph is counted, and its excerpt cut, by its
own opening sentence (as 1782 counted the Charlestown report of Savannah's evacuation). Scan findings, crops and
hand-drawn boxes are merged from stories_1789_review.json after the scan check. A printing on a page whose RevX
transcription is filed under another scan page (derived/revx_page_map.parquet) takes its excerpt from the CA
transcription of its scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied; other years are reviewed at the same time, and the main
session renumbers at release:
    python work/archive_data/ledgers/make_stories_1789.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1789/search_pages.json). The excerpts are cut from
the 1789 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1789'
D = PROJECT/'outputs/story_discovery_1789'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1789_review.json'
OUT = HERE/'stories_1789.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn82014784': 'The Kentucky Gazette', 'sn82014782': 'The Kentucky Gazette', 'sn83025587': 'The New-Hampshire Gazette',
         'sn83030483': 'The Gazette of the United-States', 'sn84023133': 'The New-Hampshire Gazetteer'}
ONE = {'NHG': 'sn83025587', 'GUS': 'sn83030483', 'NHGZ': 'sn84023133'}
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
    """Page key of a printing: paper code, date (MM-DD in 1789), page and edition. The Kentucky Gazette is under two
    catalogue numbers (C-04): sn82014784 to 7 March, sn82014782 from 14 March."""
    if paper == 'KG':
        lccn = 'sn82014784' if date <= '03-07' else 'sn82014782'
    else:
        lccn = ONE[paper]
    return f'{lccn}|{YEAR}-{date}|{ed}|{page}'


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
 # ---- admitted: printed by all four papers (every paper that survives for their weeks) ----
 dict(id='london-report-of-a-tumult-at-barcelona-1789', kind='message_group',
      label="London, 9 April 1789: 'A most outrageous tumult has happened at Barcelona, in Spain, in consequence of the high price of bread'",
      definition=("Printings of a report among the London news of 9 April 1789 (the New-Hampshire papers introduce it with 'says a late European "
                  "paper'): 'A most outrageous tumult has happened at Barcelona, in Spain, in consequence of the high price of bread. On the 1st ult. "
                  "a very numerous mob began to set fire to the town magazines, where the corn is deposited. Having finished here, they burnt two "
                  "houses belonging to principal corn dealers, besides some others.' The papers give the day as 'the 1st ult.', 'the first of "
                  "April' and 'the first instant'; the Kentucky Gazette prints a longer text. Counted by its own words."),
      role='report', words=50, dateline=True,
      core=[r'A\W*L?MOST\W+outrageous\W+tumult', r'outrageous\W+tumult'],
      first="London, April 1789: a report from a European paper of a tumult at Barcelona over the price of bread.",
      what="the London report of a tumult at Barcelona",
      printings=[k('GUS', '07-25', 3), k('NHGZ', '08-18', 3), (k('NHG', '08-20', 2), {'words': 72}), k('KG', '12-05', 2)]),
 dict(id='act-establishing-the-department-of-foreign-affairs-1789', kind='document_group',
      label="An Act for establishing an Executive Department, to be denominated the Department of Foreign Affairs, approved 27 July 1789",
      definition=("Printings of the act of Congress approved on 27 July 1789, as the papers print it from the laws of the first session ('Congress "
                  "of the United States. Begun and held at the City of New-York, on Wednesday the Fourth of March, One Thousand Seven Hundred and "
                  "Eighty-Nine'): 'An ACT for establishing an Executive Department, to be denominated the Department of Foreign Affairs. BE it "
                  "enacted by the Senate and House of Representatives of the United States of America in Congress assembled, That there shall be an "
                  "executive department, to be denominated the department of foreign affairs, and that there shall be a principal officer therein, "
                  "to be called the Secretary for the department of foreign affairs ...'. Lists of the session's acts that give only its title, and "
                  "the Senate's journal naming the bill, are not counted (C-07)."),
      role='published_document', words=75, dateline=False, stop=r'who\W+shall\W+perform',
      core=[r'A\W*N\W+ACT\W+for\W+establishing\W+an\W+EXECUTIVE\W+DEPARTMENT', r'executive\W+department,?\W+to\W+be\W+denominated\W+the\W+department\W+of\W+foreign\W+affairs'],
      first="New-York, July 1789: the act of Congress establishing the Department of Foreign Affairs.",
      what="the act establishing the Department of Foreign Affairs",
      printings=[k('GUS', '07-29', 3), k('NHG', '08-06', 2), k('NHGZ', '08-18', 1), k('KG', '10-17', 2)]),
 dict(id='boston-paragraph-on-american-genius-abroad-july-1789', kind='message_group',
      label="Boston, July 1789: 'While the soil of America is propitious to the production of genius, Europe appears no less propitious to its growth and maturity'",
      definition=("Printings of a Boston paragraph, dated 25 July 1789 in the Gazette of the United States and 27 July in the Kentucky Gazette (the "
                  "New-Hampshire papers print it without a dateline): 'While the soil of America is propitious to the production of genius, Europe "
                  "appears no less propitious to its growth and maturity. Poets, Painters and Mechanics seek in the old world those rewards which "
                  "cannot be bestowed on them in the new. Our West, Copley, Brown, Trumbull, &c. seem to have taken up their abode in those climes "
                  "...'. A paper's comment."),
      role='report', words=42, dateline=True,
      core=[r'W\W*HILE\W+the\W+soil\W+of\W+America\W+is\W+propitious'],
      first="Boston, July 1789: a paragraph on American painters, poets and mechanics who seek their rewards in Europe.",
      what="the Boston paragraph on American genius abroad",
      printings=[k('NHG', '07-30', 3), k('GUS', '08-01', 3), k('NHGZ', '08-18', 3), k('KG', '10-24', 2)]),
 dict(id='revenue-officers-appointed-by-the-president-august-1789', kind='document_group',
      label="Revenue Department, August 1789: 'The President of the United States has been pleased to nominate, and by and with the advice and consent of the Senate, to appoint the following persons to the offices in the Revenue'",
      definition=("Printings of the list of the collectors, naval officers and surveyors of the ports, state by state, headed 'Revenue Department' "
                  "in the Gazette of the United States of 5 August 1789 ('New-York, August 5' in the New-Hampshire Gazetteer; without the heading "
                  "in the New-Hampshire Gazette): 'The President of the United States has been pleased to nominate, and by and with the advice and "
                  "consent of the Senate, to appoint the following persons to the offices in the Revenue, affixed to their respective names—To hold "
                  "their commissions during the pleasure of the President: For the State of New-Hampshire. Portsmouth. Joseph Whipple, collector "
                  "...'. A list of public officers."),
      role='published_document', words=60, dateline=True, stop=r'For\W+the\W+State\W+of',
      core=[r'REVENUE\W+DEPARTMENT', r'T\W*HE\W+PRESIDENT\W+of\W+the\W+United\W+States\W+has\W+been\W+pleased\W+to\W+nominate'],
      first="New-York, August 1789: the list of officers of the revenue whom the President appointed with the Senate's consent.",
      what="the list of the officers of the revenue",
      printings=[k('GUS', '08-05', 3), k('NHG', '08-13', 1), k('NHGZ', '08-22', 1), k('KG', '10-10', 2)]),
 dict(id='vienna-13-may-1789-report-from-croatia', kind='message_group',
      label="Vienna, 13 May 1789: 'They write from Croatia, that on the 12th of April, 1000 Turkish cavalry attacked a post of the Bannat'",
      definition=("Printings of a report from Croatia in a Vienna paragraph dated 13 May 1789: 'They write from Croatia, that on the 12th of April, "
                  "1000 Turkish cavalry attacked a post of the Bannat—five villages belonging to the Bosnians, which were under the imperial "
                  "protection, experienced the fury of the enemy ...'. Three papers print it after a report that the Emperor is ill ('Our august "
                  "Sovereign is again ill ...'); the Kentucky Gazette prints it alone under the dateline. Counted by its own opening sentence."),
      role='report', words=55, dateline=True,
      core=[r'T\W*HEY\W+write\W+from\W+Cro\W*a?\W*tia', r'write\W+from\W+Cro'],
      first="Vienna, May 1789: a report from Croatia of an attack by Turkish cavalry on a post of the Bannat.",
      what="the Vienna report from Croatia",
      printings=[k('GUS', '08-05', 2), k('NHGZ', '08-18', 2), k('NHG', '08-20', 2), k('KG', '10-31', 1)]),
 dict(id='london-report-of-a-letter-from-ancona-on-the-fleets-1789', kind='message_group',
      label="London, June 1789: 'A letter from Ancona mentions, that the Russian fleet has destroyed the first division of the Turkish fleet, near the port of Warna'",
      definition=("Printings of a one-sentence report among the London news of June 1789 (dated 10 June in the Gazette of the United States and "
                  "the Kentucky Gazette, 15 June in the New-Hampshire papers): 'A letter from Ancona mentions, that the Russian fleet has destroyed "
                  "the first division of the Turkish fleet, near the port of Warna.' Counted by its own words, inside different paragraphs."),
      role='report', words=23, dateline=True,
      core=[r'A\W+letter\W+from\W+A\W*c?n?c?ona\W+mentions'],
      first="London, June 1789: a report of a letter from Ancona on the Russian and Turkish fleets.",
      what="the London report of a letter from Ancona",
      printings=[k('GUS', '08-26', 3), k('NHGZ', '09-05', 2), k('NHG', '09-10', 3), k('KG', '12-12', 2)]),
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
            problems.append((s['id'], key, 'page not in the 1789 pages'))
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
        r['id'] = f'S89-{n:03}'
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
               'admission_rule': 'Reviewed 1789 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1789/'
    return {
        'ledger_id': 'ledger:stories-1789', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1789', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1789, and of 1788 where they reach the 1789 pages (long-running ones '
                   'included), every item in 3 or more papers counted again by the first 40 words of its opening against every page, papers that '
                   'comparison missed looked for again and read, a sweep of word-for-word passages shared by 4 or more papers for items the '
                   'families miss, phrase searches on all 742 pages of 1789 in both transcriptions for every admitted item, and scan checks of '
                   'each admitted passage, by the thin-year rule (Y-THIN as amended on 23 November 2026: an item printed by more than half of '
                   'the newspapers that survive for its weeks, and by at least 4, is eligible; items printed by every surviving paper are '
                   'admitted, the others chosen to cover the months and the kinds of news; in 1789, with four papers, every eligible item is '
                   'printed by all four and admitted)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1788.json': 'retrieval_candidates',
                             d+'counted_items.json': 'retrieval_candidates', d+'phrase_patterns.json': 'retrieval_patterns',
                             d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1789.py': 'ledger_code', 'work/archive_data/ledgers/stories_1789_review.json': 'scan_review',
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
