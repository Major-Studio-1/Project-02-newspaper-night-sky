"""Write ledgers/stories_1797_round3.json: reviewed stories of 1797, round three (read again by the one rule).

1797 was first read on 6 November 2026 (stories_1797.json, stories_1797_round2.json), before the admission rule the other
reviewed years follow existed: candidate families of 3 to 5 papers were read and some chosen, and its stories reach 2 to 5
papers. This round reads the year again by that rule (make_stories_1809.py, outputs/story_discovery_1809/README.md):
the automatic families first printed in 1797 that reach 3 or more papers, long-running ones included, were split into
single printed items with work/story_items.py --long-running (items.json), and again with year 1796 over the 1797 pages
(items_from_1796.json); every item in 4 or more papers was read, the counts were checked item by item with phrase searches
over all 1,587 pages of 1797 in both transcriptions (work/story_phrase_search.py), and every hit was read.

No 1797 item reaches 7 papers, or 6: the collection holds 8 series for 1797, of which only three (the Gazette of the
United States, the Kentucky Gazette and the New Hampshire Gazette) run all year, and 2 to 6 are in print in any three
weeks. The README (outputs/story_discovery_1797/round3/README.md) therefore proposes a 4-paper threshold for 1797, as 1793
uses 6 because fewer papers survive, and puts it to the owner. This ledger is built at that proposed threshold: every
single item in 5 or more papers, and items in 4 papers chosen to cover the months and the kinds of news. It is not
applied: the owner decides the threshold first.

The 21 stories of rounds one and two stay as they are; this ledger adds groups and adds nothing to theirs.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1797_round3_review.json after
the scan check. Three 1797 pages have their RevX transcriptions filed one page off from the scans (derived/revx_page_map
.parquet); no printing here stands on one of them, but a printing that did would take its excerpt from the CA
transcription of its scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied; the defaults assume it follows v0.11.7, the correction release
cut on 22 November 2026 (correct_filing.py), which changes no 1797 page:
    python work/archive_data/ledgers/make_stories_1797_round3.py [--table] [--base 0.11.7 --target 0.11.8]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1797/round3/search_pages.json, made by
work/year_search_pages.py 1797 ... --printed-dates). The excerpts are cut from the 1797 pages, which no release changes, so
the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1797'
ROUND3 = PROJECT/'outputs/story_discovery_1797/round3'
PAGES = ROUND3/'search_pages.json'
REVIEW = HERE/'stories_1797_round3_review.json'
OUT = HERE/'stories_1797_round3.json'
BASE, TARGET = '0.11.7', '0.11.8'   # defaults; see the docstring
DATA_RELEASE = '0.11.6'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-22'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

GUS, KY, NH, PG, EAG, MIR, RG, VA = ('sn83025881', 'sn82014782', 'sn83025588', 'sn84038410', 'sn84023150', 'sn83025525',
                                     'sn83025527', 'sn84024710')
PAPER = {GUS: 'The Gazette of the United States', KY: 'The Kentucky Gazette', NH: 'The New Hampshire Gazette',
         PG: 'The Patowmac Guardian', EAG: 'The Eagle', MIR: 'The Mirror', RG: "Russel & Davis' Republican Gazetteer",
         VA: 'The Virginia Argus'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper, date (MM-DD in 1797), page and edition."""
    return f'{paper}|{YEAR}-{date}|{ed}|{page}'


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
# The Vienna report's two printed forms (counted together, as 1809 counted two translations of one bulletin): the short form
# ends before 'On the part of the French'; the longer form's excerpt runs to its sentence on the peace negotiations.
SHORT_FORM = {'note': 'The short form.', 'stop': r'On\s+the\s+part\s+of\s+the\s+French'}
LONG_FORM = {'note': 'The longer form of the report.', 'words': 95, 'stop': r'The\s+French\s+require'}

STORIES = [
 dict(id='crauford-letter-27-october-1796-moreau-retreats', kind='document_group',
      label="From the Archduke Charles's headquarters, 27 October 1796: Moreau's army retreats across the Rhine",
      definition="Printings of a letter dated at the headquarters of the Archduke Charles of Austria, 27 October 1796, which the London Gazette of 13 November published with others from Captain Anstruther and R. Crauford: 'My Lord, I have the honour to inform your Lordship, that in the course of the last night Gen. Moreau's army retreated across the Rhine at Huningen' (the Patowmac Guardian's words); it is signed Robert Crauford. Three papers print it after a London paragraph of 14 November that introduces it as 'the last of the letters alluded to'; the New Hampshire Gazette prints the letter alone, from New York. The writer's report from the Austrian headquarters, as the London Gazette published it.",
      role='published_document', words=60, dateline=False, back=True, stop=r'The\s+l(?:eft|ast)\s+of\s+his\s+rear',
      core=[r'Head[\s-]*(?:Q|q)uarters\s+of\s+his\s+(?:R|r)oyal\s+(?:H|h)ighness,?\s+the\s+(?:A|a)rchduke\s+Charles'],
      first="A letter from the Archduke Charles's headquarters, 27 October 1796, from the London Gazette: Moreau's army has retreated across the Rhine.",
      what='the letter from the Archduke Charles\'s headquarters',
      printings=[k(GUS, '01-14', 3),
                 k(PG, '01-26', 2),
                 k(NH, '01-28', 2),
                 k(KY, '03-08', 2)]),
 dict(id='truguet-letter-6-november-1796-ireland', kind='document_group',
      label="Truguet to the Directory, 6 November 1796: letters from Brest 'announce that a general revolution has just taken place in Ireland'",
      definition="Printings of a letter to the French Executive Directory dated 6 November 1796 and signed Truguet: 'I hasten to communicate to the Executive Directory the reception of letters from Brest, of the 3d instant (November) brought by an extraordinary courier, which announce that a general revolution has just taken place in Ireland.' It gives the report of the captains of two ships brought in from Liverpool by French privateers, that the Irish had taken 30,000 stand of arms in Dublin and defeated 10,000 English troops. Printed from the Paris papers, in the same column of French news as General Bournonville's letter (a group of its own). A report at second hand: the writer passes on what letters from Brest and two ship captains said.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:Nov(?:ember|\.)\s+6\.\s+)?Citizens?\s+Direct\w*[.,]?\s+I\s+hasten\s+to\s+communicate'],
      first="Truguet's letter to the Directory of 6 November 1796: letters from Brest announce 'a general revolution' in Ireland.",
      what="Truguet's letter",
      printings=[k(GUS, '01-09', 3),
                 k(PG, '01-19', 2),
                 k(RG, '01-24', 3),
                 k(KY, '03-08', 2)]),
 dict(id='bournonville-letter-3-brumaire-neuwied', kind='document_group',
      label='General Bournonville to the Directory, Mulheim, 3 Brumaire: the attack on the bridgehead at Neuwied',
      definition="Printings of General Bournonville's letter to the French Executive Directory from Mulheim, dated 3 Brumaire (two papers add 'Oct. 28'): 'I had the honor to give you an account yesterday of the attack of the army made by the enemy in the night between the 29th and 30th Vendemiaire ... upon the head of the bridge and the isle of Neuwied'; he writes that the enemy meant to make the garrison prisoners of war, and that 'This affair cost the enemy more than four thousand men'. Printed from the Paris papers, in the same column as Truguet's letter of 6 November (a group of its own). A commander's own report.",
      role='published_document', words=60, dateline=False, stop=r'he\s+ha[sd]\s+projected',
      core=[r'(?:General\s+)?BOURNONVILLE\s+to\s+the\s+Ex(?:ecutive|\.)\s+Directory'],
      first="General Bournonville's letter to the Directory from Mulheim, 3 Brumaire, on the attack at the bridgehead of Neuwied.",
      what="General Bournonville's letter",
      printings=[k(GUS, '01-09', 3),
                 k(PG, '01-19', 2),
                 k(RG, '01-24', 3),
                 k(KY, '03-08', 2)]),
 dict(id='berthier-letter-milan-28-november-1796', kind='document_group',
      label="General Berthier's letter from Milan, 28 November 1796: the army of Italy after Arcola",
      definition="Printings of a letter from General Berthier, chief of the staff of the army of Italy, to General Baraguey d'Hilliers (each paper spells the name differently), dated at Milan, 8 Frimaire, 28 November 1796: 'I informed you, general, by the last bulletin which I sent you, that, after having beaten the troops commanded by general Alvinzy in person, at Arcola, the commander in chief made his dispositions to attack the column commanded by general Davidovich'; it reports that the enemy was driven from the heights of Rivoli with 1,100 prisoners taken. A staff officer's own report for the French side.",
      role='published_document', words=70, dateline=False,
      core=[r'(?:(?:FRANCE\.\s+)?ARMY\s+OF\s+ITALY\.\s+)?Letter\s+from\s+Gen(?:eral|\.)\s+Berthier'],
      first="General Berthier's letter from Milan of 28 November 1796 reports the army of Italy's attack after Arcola.",
      what="General Berthier's letter",
      printings=[k(GUS, '02-13', 3),
                 k(NH, '02-25', 2),
                 (k(RG, '02-28', 3), {'note': "The Republican Gazetteer introduces it: 'The French continue victorious in Italy—See this Letter'."}),
                 k(KY, '03-15', 2)]),
 dict(id='delarue-report-march-of-the-troops-august-1797', kind='document_group',
      label="Delarue's report to the Council of Five Hundred on the march of the troops, August 1797",
      definition="Printings of the report made in the French Council of Five Hundred (sitting of 4 August 1797; 3 August in the Mirror) by Delarue ('Delarne' in the Mirror and the Kentucky Gazette) for its committee of inspectors, 'on the march of the troops': 'It results from the information we have procured, 1. That from 26 to 27,000 men have been detached from the army of the Sambre and Meuse, instead of 9000, as was stated by Gen. Hoche. 2. That this force directed its march towards Paris' (the Gazette of the United States prints 6000, 'as was said'). It goes on to say that the soldiers had been 'misled and seduced' against the Legislative Body and that troops kept marching on Paris 'by order of Gen. Hoche'. A committee's report and charges in the legislature, as the Paris papers gave them.",
      role='published_document', words=80, dateline=True, stop=r'3\.\s+That\s+a\s+formidable',
      core=[r'(?:Sitting\s+of\s+August\s+4\.?\s+|COUNCIL\s+OF\s+FIVE\s+HUNDRED,\s+AUGUST\s+3\.\s+)?DELAR[UN]E\.?\s*[-—–]*\s*["“]?I\s+come\s+in\s+the\s+name'],
      first="Delarue's report to the Council of Five Hundred, 4 August 1797: 26 to 27,000 men detached from the army of the Sambre and Meuse marched towards Paris.",
      what="Delarue's report",
      printings=[k(GUS, '09-20', 3),
                 k(NH, '09-26', 3),
                 k(MIR, '10-10', 1),
                 k(KY, '10-14', 2)]),
 dict(id='vienna-report-26-july-1797-peace-talks', kind='message_group',
      label="Vienna, 26 July 1797: the peace talks in Italy 'meet with great difficulties'",
      definition="Printings of a report from Vienna dated 26 July 1797, printed from the London papers in two forms. Three papers print a short form: 'The Marquis DE GALLO, has this moment arrived here from Udina. The negotiations for peace in Italy, meet with great difficulties. The French require that Mantua shall be united with the Cisalpine Republic' (the Mirror's words). The Gazette of the United States and the Kentucky Gazette print a longer form that opens with the Marquis de Gallo's conferences with the Emperor and Baron Thugut, and adds that 'neither the marquis nor the persons about the court had very pleasant countenances'. Both forms then give the same account of the French demand for Mantua, the Emperor's indemnification in Istria and Dalmatia, and 'our fears that hostilities may again commence'. A correspondent's report, at second hand through the London papers.",
      role='report', words=55, dateline=False,
      core=[r'VIENNA,?\s+JULY\s+26\.\s+(?:THE|The)\s+Marquis', r'VIENNA,?\s+July\s+26\.\s+On\s+the\s+24th'],
      first="A report from Vienna of 26 July 1797, in the longer form: the Marquis de Gallo's conferences, and difficulties in the peace talks in Italy.",
      what='the Vienna report',
      printings=[(k(GUS, '10-04', 2), LONG_FORM),
                 (k(NH, '10-10', 2), dict(SHORT_FORM, field=CA, core=[r'V\w{3,5}a,?\s+July\s+26\.\s+THE\s+Marquis'],
                                          note='The short form. This page has no RevX transcription, so the excerpt comes from the older CA transcription.')),
                 (k(EAG, '10-23', 2), SHORT_FORM),
                 (k(MIR, '10-24', 1), SHORT_FORM),
                 (k(KY, '10-28', 2), LONG_FORM)]),
 dict(id='wilmington-report-12-october-1797-spanish-posts', kind='message_group',
      label='Wilmington, 12 October 1797: a traveller from Pensacola reports orders to deliver up the Spanish posts',
      definition="Printings of a report from Wilmington, North Carolina, of 12 October 1797: 'A gentleman who arrived in town on Sunday last from New-Providence, via the Havannah, has favored the Printer with the following information—on the authenticity of which he places the greatest confidence': on 20 August, the day he left Pensacola, he saw an official letter from the Baron de Carondelet saying that orders had come from his court 'to put into full execution, the treaty between Spain and the United States of America', and that the commandants of the forts on the Mississippi were to deliver up the posts; Governor Gayoso had been appointed governor-general of the Floridas and Louisiana. A traveller's report at second hand.",
      role='report', words=70, dateline=True, stop=r'acquaint\W*ing\s+him',
      core=[r'(?:WILMINGTON,?\s+(?:\(N\.\s*C\.\)\s+)?Oct(?:ober|\.)\s+12\.\s+)?A\s+gentleman\s+who\s+arrived\s+in\s+town\s+on\s+Sunday\s+last'],
      first="A Wilmington report of 12 October 1797: a traveller from Pensacola saw the Spanish governor's letter ordering the posts on the Mississippi delivered up.",
      what='the Wilmington report',
      printings=[k(GUS, '10-27', 3),
                 k(KY, '11-15', 3),
                 (k(NH, '11-15', 2), {'field': CA, 'core': [r'W\w+,?\s*\(N\.\s*C\.\)\s+O\S+\s+12\.\s+A\s+gentleman\s+who\s+arrived\s+in\s+town\s+on'],
                                      'note': 'RevX gives this report three times on the page; the CA transcription has it once, so the excerpt comes from the CA text.'}),
                 k(MIR, '11-21', 2)]),
 dict(id='nassau-letter-26-september-1797', kind='message_group',
      label="A letter from Nassau, New Providence, 26 September 1797: the writer's account of a 'plot'",
      definition="Printings of a letter from a gentleman at Nassau, New Providence, dated 26 September 1797, as a Columbia (South Carolina) paper printed it on 3 November: 'We have lately very providentially escaped a most hellish plot.—A parcel of French negroes who had been captured and sold here, and who had ran away from their owners, entered into a conspiracy (about thirty in number) to burn the town and make a general massacre of the whites.' By his account one of them told his master a few hours before, five were taken and condemned and three executed. One correspondent's account, written from the side of those who held the accused; the accused are heard only through it, and it names no one.",
      role='report', words=75, dateline=True, stop=r'They\s+had\s+the\s+promise',
      core=[r'(?:Extract\s+of\s+a\s+letter|A\s+letter)\s+from\s+a\s+gentleman\s+at\s+Nassau'],
      first="A letter from Nassau of 26 September 1797, printed at Columbia: the writer's account of a 'plot' and of the executions that followed.",
      what='the Nassau letter',
      printings=[k(GUS, '11-20', 3),
                 k(NH, '12-06', 2),
                 k(MIR, '12-12', 2),
                 k(EAG, '12-25', 3)]),
 # A printing of a story of round two that round two's searches missed (the issue's RevX pages are filed one page off).
 # Decided 23 November 2026 to add it, then DEFERRED the same day: adding a printing to an existing group changes that group's
 # topic row, which apply_ledger.py's topic step (add_reviewed_topics.py) must reproduce exactly. It goes in with a correction
 # release that also updates that row; its check and crop are in outputs/story_discovery_1797/round3/deferred/. 'deferred' keeps
 # it out of this ledger; 'existing' marks a group this ledger does not redefine; its id is fixed.
 dict(id='congress-opening-nov-1797', existing=True, deferred=True, role='reply', words=30, dateline=False,
      core=[r'Reply\s+of\s+the\s+President\s+to\s+the\s+answer\s+of\s+the'],
      first="The New Hampshire Gazette prints Adams's reply of 29 November 1797 to the House of Representatives.",
      what="Adams's reply to the House",
      printings=[(k(NH, '12-13', 2), {'id': 'S97-034', 'note': "Added in round three: round two's searches missed this printing."})]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808 and 1809): "COLUMBIA, (S. C.) Nov. 3."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*17(?:96|97))?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False):
    for core in cores:
        m = re.search(core, text, re.I)
        if m:
            start = m.start()
            if back:   # a quoted document: start at the beginning of the sentence that introduces it
                cuts = [(text.rfind(b, 0, start), len(b)) for b in ('. ', '.] ', '] ', '." ', '.” ', '? ')]
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
        if s.get('deferred'):
            continue
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
            problems.append((s['id'], key, 'page not in the 1797 pages'))
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
        earlier = seen.get(story, 0) if not s.get('existing') else 1   # an added printing is never the story's earliest
        seen[story] = seen.get(story, 0) + 1
        summary = s['first'] if earlier == 0 else f"{PAPER[lccn]} prints {s['what']}."
        note = over.get('note', '')
        if key in MISFILED:
            note = (note+' ' if note else '') + ('The RevX transcriptions of this issue are filed one page off from the scans, so the excerpt '
                                                 'comes from the older CA transcription of this scan page.')
        elif field == CA and 'field' not in over:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'printed': pages[key]['date'], 'field': field, 'excerpt_start': first, 'excerpt_end': last,
                     'excerpt': excerpt, 'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0, 'fixed_id': over.get('id')})
    rows.sort(key=lambda r: (r['printed'], r['page_key'], r['story']))
    numbers = iter(range(1, 10**4))
    for r in rows:   # the rows numbered in order of printed date; a fixed id (a printing added later) keeps its own
        r['id'] = r['fixed_id'] or f'S97-{next(numbers):03}'
    rows.sort(key=lambda r: r['id'])
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
               'admission_rule': 'Reviewed 1797 printings, checked against the scan.'} for s in STORIES if not s.get('existing')]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1797/round3/'
    return {
        'ledger_id': 'ledger:stories-1797-round3', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1797', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1797, and of 1796 where they reach the 1797 pages (long-running ones '
                   'included), phrase searches on all 1,587 pages of 1797 in both transcriptions, reading of every hit, and scan checks of each '
                   'admitted passage, at the 4-paper threshold proposed for 1797'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1796.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1797_round3.py': 'ledger_code', 'work/archive_data/ledgers/stories_1797_round3_review.json': 'scan_review',
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
            print(f"{r['id']} {r['story'][:26]:26} {r['page_key']:30} {r['field'][:4]} {r['roles'][0][:9]:9} | {r['excerpt'][:110]} … {r['excerpt'][-50:]}")
    review = json.loads(REVIEW.read_text(encoding='utf8')) if REVIEW.exists() else {}
    if problems and '--force' not in sys.argv:
        raise SystemExit(f'{len(problems)} printings without anchors')
    OUT.write_text(json.dumps(build(rows, review), ensure_ascii=False, indent=2), encoding='utf8')
    print('wrote', OUT, len(rows), 'observations,', sum(not s.get('existing') for s in STORIES), 'new groups')
