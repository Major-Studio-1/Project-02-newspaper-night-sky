"""Write ledgers/stories_1805.json: reviewed stories of 1805, round one.

The stories were chosen as for 1776, 1807 and 1808 (make_stories_1807.py, make_stories_1808.py): the automatic families
were split into single printed items with work/story_items.py, run with --long-running, every item printed in 7 or more
newspapers was read, and the chosen items were confirmed with phrase searches over all 3,811 pages of 1805 in both
transcriptions (work/story_phrase_search.py). story_items.py takes the families first printed in its year, so it was also
run with year 1804 over the 1805 pages (items_from_1804.json), for documents and news first printed in late 1804. See
outputs/story_discovery_1805/README.md.

The 1805 pages are those whose issue the base release dates to 1805 (work/year_search_pages.py --printed-dates): release
v0.10.2 dates the Kentucky Gazette and General Advertiser issue that the collection files under 28 May 1807 to its printed
date, 28 May 1805. Its page keys and ids keep the filed date, so k() turns a printed date into the filed key, and the
observations are numbered in order of printed date.

The Portland Gazette (Maine) runs under three titles and catalogue numbers in 1805 (Jenks' Portland Gazette to 11 March, the
Portland Gazette from 18 March to 16 July, the Portland Gazette, and Maine Advertiser from 23 July). They are never in print
at the same time; the README counts them as one newspaper.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1805_review.json after the scan
check.

Seven 1805 issues have their RevX transcriptions filed one page off from the scans, or repeating another page
(derived/revx_page_map.parquet in the base release, from outputs/revx_page_shift_check/). A printing on a page whose RevX
slot holds another page's text names the scan page and takes its excerpt from the CA transcription of that page, which is
numbered as the scans are.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (the 1806 review owns release v0.11.0; the ledgers of the
stories once held back for framing follow it). The defaults assume this ledger comes after those four:
    python work/archive_data/ledgers/make_stories_1805.py [--table] [--base 0.11.4 --target 0.11.5]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1805/search_pages.json, made by
work/year_search_pages.py 1805 … --printed-dates). The excerpts are cut from the 1805 pages, which no release changes, so
the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1805'
PAGES = PROJECT/'outputs/story_discovery_1805/search_pages.json'
REVIEW = HERE/'stories_1805_review.json'
OUT = HERE/'stories_1805.json'
BASE, TARGET = '0.11.4', '0.11.5'
DATA_RELEASE = '0.10.2'   # the release whose issue dates, misfiled-page map and families were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

ADA, NI, NG, VA, EN, NHG, BJ = 'sn84024012', 'sn83045242', 'sn85025815', 'sn84024710', 'sn84024736', 'sn83025588', 'sn85059525'
HUS, OP, JPG, PG, PGZ, RIR, KG = 'sn83021527', 'sn84023351', 'sn83016081', 'sn83045636', 'sn83016082', 'sn83021188', 'sn84038147'
PAPER = {ADA: 'The Alexandria Daily Advertiser', NI: 'The National Intelligencer', NG: 'The Norfolk Gazette and Publick Ledger',
         VA: 'The Virginia Argus', EN: 'The Enquirer', NHG: 'The New Hampshire Gazette', BJ: 'The Berkeley and Jefferson Intelligencer',
         HUS: 'The Herald of the United States', OP: 'The Oracle Post', JPG: "Jenks' Portland Gazette", PG: 'The Portland Gazette',
         PGZ: 'The Portland Gazette, and Maine Advertiser', RIR: 'The Rhode-Island Republican', KG: 'The Kentucky Gazette'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def issue_dates():
    """(lccn, filed date, edition) -> printed date, from the data release's issues table."""
    out = {}
    with (RELEASE/'tables/issues.jsonl').open(encoding='utf8') as stream:
        for line in stream:
            row = json.loads(line)
            _, lccn, filed, ed = row['id'].split(':')
            out[(lccn, filed, int(ed))] = row['publication_date']
    return out


PRINTED = issue_dates()
FILED = {}
for (_lccn, _filed, _ed), _printed in PRINTED.items():
    if _printed != _filed:
        assert (_lccn, _printed, _ed) not in FILED, ('two issues printed on one day', _lccn, _printed)
        FILED[(_lccn, _printed, _ed)] = _filed


def k(paper, date, page, ed=1):
    """Page key of a printing, from its printed date (MM-DD in 1805): the key keeps the date the collection files the issue under."""
    printed = f'{YEAR}-{date}'
    return f'{paper}|{FILED.get((paper, printed, ed), printed)}|{ed}|{page}'


def printed_date(key):
    lccn, filed, ed, _ = key.split('|')
    return PRINTED.get((lccn, filed, int(ed)), filed)


def misfiled():
    """Page keys of 1805 pages whose RevX slot holds another scan page's text (shifted, two pages off or repeated)."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if printed_date(key(r['page_id'])).startswith(YEAR)}


MISFILED = misfiled()

# Numbers not given to any printing, so that the ids of the scan check stay with their printings: S05-022 was the Alexandria
# Daily Advertiser's page of 20 February with Chase's answer, which the scan check showed to be a later instalment of the
# printing of 16 February, not a printing of its own.
RETIRED = {22}

# Story groups, as for 1776, 1807 and 1808. 'printings' lists each printing's page; a tuple adds overrides for that printing:
# core (regexes for the item's first words), role, field, note, words, dateline (include a dateline or heading directly
# before), back (start at the beginning of the sentence that holds the core, for quoted documents), stop (end the
# excerpt before the first match of this regex).
ACT = r'A\s?N\s+A\s?CT,?\s+'
TO_HOUSES = r'(?:T\s?O\s+THE\s+(?:THE\s+)?S\s?ENATE,?\s+(?:AND|&)\s+H\s?OUSE\s+OF\s+R\s?EPRESENTATIVES,?(?:\s+OF\s+THE\s+U[\w.]*\s?S\w*[.,]?)?["”]?\s+)?'
TO_CONGRESS = (r'(?:T\s?O\s+THE\s+S\s?ENATE,?\s+(?:AND|&)\s+H\s?OUSE\s+OF\s+R\s?EPRESENTATIVES,?\s+OF\s+THE\s+U[\w.]*\s?S\w*\.?,?\s*'
               r'(?:OF\s+A\s?MERICA\.?\s*)?)?')
STORIES = [
 # --- January to June (reader A's half of the year) ----------------------------------------------------------------------
 dict(id='tripoli-squadron-letters-1805', kind='context_group', label='Letters on the squadron before Tripoli, sent to Congress',
      definition=("Two letters on the American squadron's attacks on Tripoli in August and September 1804, as the 1805 papers printed them after the "
                  "President sent them to Congress: Richard O'Brien's letter from Malta of 5 September 1804 (sent on 31 December 1804) and Commodore "
                  "Preble's letter of 18 September 1804 (sent on 20 February 1805). Contains those two groups. Each is an American official's own account."),
      children=['obrien-letter-on-tripoli-5-september-1804', 'preble-letter-18-september-1804']),
 dict(id='obrien-letter-on-tripoli-5-september-1804', parent='tripoli-squadron-letters-1805', kind='document_group',
      label="O'Brien's letter from Malta on the attacks on Tripoli", role='published_document', words=55, dateline=True,
      core=[r"(?:Copy|Extract)\s+of\s+a\s+letter\s+from\s+R\s?ICHARD\s+O.?\s?B\s?RIEN"],
      definition=("Printings of the letter of Richard O'Brien, 'late Consul of the United States, at Algiers', to John Gavino, consul at Gibraltar, dated "
                  "Malta, 5 September 1804, 'giving some details of transactions before Tripoli', which the President communicated to Congress on "
                  "31 December 1804: the American gun boats and two bombards 'entered the harbour of Tripoli, and within 600 feet of the Bashaw's castle' "
                  "began their attack. An American official's own account."),
      first="Richard O'Brien's letter from Malta (5 September 1804), sent to Congress, on the squadron's attacks on Tripoli.", what="O'Brien's letter",
      printings=[k(NI, '01-02', 3), k(EN, '01-08', 2), k(VA, '01-09', 3), k(NG, '01-09', 2), k(BJ, '01-11', 2),
                 (k(JPG, '01-14', 2), dict(role='document_excerpt', note="Printed as an extract of the letter, without the President's message.")),
                 k(NHG, '01-15', 2)]),
 dict(id='preble-letter-18-september-1804', parent='tripoli-squadron-letters-1805', kind='document_group',
      label="Commodore Preble's letter of 18 September 1804", role='published_document', words=55, dateline=False,
      core=[r'(?:M\s?EDITERRANEAN\s+W\s?AR\.\s+)?Copy\s+of\s+a\s+letter\s+from\s+[Cc]ommodore\s+P\s?REBLE'],
      definition=("Printings of the letter of Commodore Edward Preble to the Secretary of the Navy, from the harbour of Malta, 18 September 1804, which the "
                  "President sent to Congress with his message of 20 February 1805: 'I had the honor to write you from Messina, under date of the 5th "
                  "of July', followed by his day-by-day account of the squadron before Tripoli. The commander's own account."),
      first="Commodore Preble's letter of 18 September 1804, sent to Congress, with his account of the squadron before Tripoli.", what="Preble's letter",
      printings=[k(NI, '02-25', 2), k(ADA, '03-01', 2), k(VA, '03-02', 2), k(EN, '03-05', 1), k(NG, '03-06', 2), k(OP, '03-26', 1), k(PG, '04-29', 1)]),
 dict(id='chase-impeachment-trial-1805', kind='context_group', label='The impeachment trial of Judge Chase, 1805',
      definition=("Four printed pieces of the trial of Samuel Chase, an associate justice of the Supreme Court, before the Senate on the articles of "
                  "impeachment exhibited by the House of Representatives, as the 1805 papers printed them: his speech of 2 January, his answer and pleas "
                  "of 4 February, the House's replication, and the declaration of 1 March that he was acquitted. Contains those four groups. Each side's "
                  "words are its own: the speech and the answer are the accused judge's, the replication the House's."),
      children=['chase-address-to-the-senate-2-january-1805', 'chase-answer-and-pleas-4-february-1805', 'house-replication-to-chase-answer-1805',
                'chase-acquittal-declared-1-march-1805']),
 dict(id='chase-address-to-the-senate-2-january-1805', parent='chase-impeachment-trial-1805', kind='document_group',
      label="Judge Chase's speech to the Senate, 2 January", role='published_document', words=55,
      core=[r"(?:J\s?UDGE\s+)?C\s?HASE.?S\s+S\s?PEECH", r"The\s+following\s+is\s+the\s+S\s?PEECH\s+of\s+M\s?r\.?\s+C\s?HASE", r"M\s?R\.?\s+P\s?RESIDENT,?\s+I\s+A\s?PPEAR"],
      definition=("Printings of the speech of Samuel Chase before the Senate sitting as a court of impeachment, 2 January 1805: 'I appear, in obedience to "
                  "a summons from this honorable court, to answer articles of impeachment exhibited against me'; he asks for time until the next session "
                  "to prepare his answer. The accused judge's own words."),
      first="Judge Chase's speech to the Senate (2 January 1805): he appears to answer the articles of impeachment and asks for time.", what="Chase's speech",
      printings=[k(NI, '01-07', 3), k(EN, '01-11', 1), k(NG, '01-11', 3), k(VA, '01-12', 2), k(BJ, '01-18', 1), k(JPG, '01-21', 2), k(OP, '01-22', 1)]),
 dict(id='chase-answer-and-pleas-4-february-1805', parent='chase-impeachment-trial-1805', kind='document_group',
      label='The answer and pleas of Samuel Chase, 4 February', role='published_document', words=55, dateline=False,
      core=[r'In\s+the\s+Senate\s+of\s+the\s+United\s+States,?\s+SITTING\s+AS\s+A\s+High\s+Court', r'J\s?UDGE\s+C\s?HASE.?S?\s+A\s?NSWER\.',
            r'T\s?HE\s+A\s?NSWER,?\s+(?:AND|&)\s+P\s?LEAS?,?\s+OF'],
      definition=("Printings of 'The answer, and pleas of Samuel Chase, one of the associate justices of the supreme court of the United States, to the "
                  "articles of impeachment exhibited against him', given in the Senate on 4 February 1805: 'This respondent, in his proper person, comes "
                  "into the said court, and protesting that there is no high crime or misdemeanor particularly alleged'. A long document printed in "
                  "parts; the accused judge's own defence."),
      first="The answer and pleas of Judge Chase to the articles of impeachment, given in the Senate on 4 February 1805.", what="Chase's answer",
      printings=[k(NI, '02-11', 1),
                 (k(ADA, '02-16', 2), dict(note="Printed in instalments: this issue's part, under the repeated title and marked '(Continued.)', is the "
                                                "earliest that survives; the answer continues in the issue of 20 February.")),
                 k(EN, '02-19', 1), k(NG, '02-20', 2), k(VA, '02-27', 1),
                 (k(OP, '03-05', 1), dict(note="Printed under the paper's own heading, 'JUDGE CHASES ANSWER.', beginning with the body of the answer.")),
                 k(BJ, '03-08', 1)]),
 dict(id='house-replication-to-chase-answer-1805', parent='chase-impeachment-trial-1805', kind='document_group',
      label="The House's replication to Judge Chase's answer", role='published_document', words=55, dateline=False,
      core=[r'(?:R\s?EPLICATION\.\s*)?[\'"“‘]?\s*T\s?he\s+[Hh]ouse\s+of\s+[Rr]epresentatives\s+of\s+the\s+United\s+States,?\s+have\s+considered'],
      definition=("Printings of the replication of the House of Representatives to the answer of Samuel Chase, reported by its managers and adopted by the "
                  "House in February 1805: 'The House of Representatives of the United States have considered the answer of Samuel Chase, one of the "
                  "associate justices of the supreme court of the United States, to the articles of impeachment'. The accusers' own reply."),
      first="The House of Representatives replies to Judge Chase's answer (February 1805), maintaining its articles of impeachment.", what='the replication',
      printings=[k(NI, '02-08', 3), k(VA, '02-13', 2), k(EN, '02-15', 2), k(NG, '02-15', 3), k(BJ, '02-22', 1),
                 (k(OP, '02-26', 1), dict(note="Printed under the paper's own comment on the replication.")),
                 (k(OP, '02-26', 2), dict(note='Printed again in the same issue, in the account of the House proceedings.')), k(NHG, '03-12', 2)]),
 dict(id='chase-acquittal-declared-1-march-1805', parent='chase-impeachment-trial-1805', kind='document_group',
      label='The declaration that Judge Chase is acquitted, 1 March', role='quoted_document', words=50, dateline=False,
      core=[r'Hence\s+it\s+appears,?\s+that\s+there\s+is\s+not\s+a\s+constitutional\s+majority', r'The\s+(?:Vice\s+)?[Pp]resident\s+then\s+said'],
      definition=("Printings of the declaration made on 1 March 1805 by the President of the Senate, after the votes on the eight articles, as the papers' "
                  "accounts of the court quote it: 'there not being a constitutional majority on any one article, it becomes my duty to pronounce that "
                  "Samuel Chase, Esq. is acquitted', or, in the National Intelligencer's account, 'Hence it appears that there is not a constitutional "
                  "majority of votes finding Samuel Chase, Esquire, guilty, on any one article'. The declaration as each account quotes it."),
      first="The President of the Senate declares Judge Chase acquitted (1 March 1805): no article has a constitutional majority.", what='the declaration',
      printings=[k(NI, '03-04', 3), k(ADA, '03-04', 3), k(EN, '03-08', 2), k(NG, '03-08', 2), (k(BJ, '03-08', 3), dict(field=CA)), k(VA, '03-09', 3),
                 k(RIR, '03-14', 3), k(NHG, '03-19', 2), k(OP, '03-19', 3)]),
 dict(id='jefferson-second-inaugural-address-1805', kind='document_group', label="President Jefferson's second inaugural address",
      role='published_document', words=55, dateline=False,
      core=[r'(?:S\s?P\s?E\s?E\s?C\s?H\.\s+)?P\s?ROCEEDING,?\s+fellow.?\s?citizens,?\s+to\s+that\s+qualification'],
      definition=("Printings of the speech President Thomas Jefferson delivered on taking the oath of office for a second term, 4 March 1805: 'Proceeding, "
                  "fellow citizens, to that qualification which the constitution requires, before my entrance on the charge again conferred on me'. He "
                  "gives his account of his first term: taxes and the debt, Louisiana, 'the aboriginal inhabitants of these countries', religion and the "
                  "press. The President's own account (a policy argument)."),
      first="President Jefferson's second inaugural address (4 March 1805): his own account of his first term.", what='the inaugural address',
      printings=[k(NI, '03-06', 1), k(EN, '03-08', 2), k(NG, '03-11', 2), k(BJ, '03-15', 2), k(PG, '03-18', 2), k(NHG, '03-19', 2), k(OP, '03-19', 3)]),
 dict(id='napoleon-peace-letter-and-british-answer-1805', kind='context_group', label="Napoleon's letter to the King of England and the British answer",
      definition=("The two letters that the French minister of foreign affairs laid before the French Senate on 4 February 1805, as the papers printed them "
                  "from April: the Emperor Napoleon's letter to the King of England of 2 January 1805, proposing peace, and Lord Mulgrave's answer to "
                  "Talleyrand. Contains those two groups; each is one government's own letter."),
      children=['napoleon-letter-to-the-king-of-england-1805', 'mulgrave-answer-to-napoleon-letter-1805']),
 dict(id='napoleon-letter-to-the-king-of-england-1805', parent='napoleon-peace-letter-and-british-answer-1805', kind='document_group',
      label="Napoleon's letter to the King of England", role='published_document', words=55, dateline=False,
      core=[r'Letter\s+from\s+the\s+[Ee]mperor\s+(?:Bonaparte\s+|of\s+France\s+)?to\s+the\s+[Kk]ing\s+of\s+England'],
      definition=("Printings of the letter of the Emperor Napoleon to the King of England, Paris, 12 Nivose year 13 (2 January 1805): 'Sir, my brother, "
                  "Called to the throne of France by Providence, by the suffrages of the senate, the people and the army, my first sentiment is the wish "
                  "of peace.' France's own letter: a proposal of peace and its argument."),
      first="The Emperor Napoleon writes to the King of England (2 January 1805) proposing peace.", what="Napoleon's letter",
      printings=[k(NI, '04-10', 2), k(VA, '04-13', 3), k(EN, '04-13', 2),
                 k(PG, '04-15', 2),
                 k(NG, '04-15', 2), k(OP, '04-16', 2), k(NHG, '04-23', 2), k(BJ, '05-03', 2)]),
 dict(id='mulgrave-answer-to-napoleon-letter-1805', parent='napoleon-peace-letter-and-british-answer-1805', kind='document_group',
      label="Lord Mulgrave's answer to Talleyrand", role='published_document', words=55, dateline=False,
      core=[r'(?:Letter\s+)?[Ff]rom\s+L\s?ord\s+M\s?ulgrave,?\s+to\s+(?:his\s+[Ee]xcellency\s+)?M\.?\s+[Dd]e\s+T\s?alleyrand'],
      definition=("Printings of the British answer, a letter from Lord Mulgrave to Talleyrand, the French minister of foreign affairs (January 1805): 'His "
                  "Majesty has received the letter which has been addressed to him by the chief of the French government'; the King cannot answer it "
                  "more particularly before communicating with the powers of the continent, in particular the Emperor of Russia. Britain's own letter."),
      first="Lord Mulgrave answers for the King of England (January 1805): no particular answer before consulting the powers of the continent.", what="Mulgrave's answer",
      printings=[k(NI, '04-10', 2), k(EN, '04-13', 3), k(NG, '04-15', 2), k(OP, '04-16', 2), k(VA, '04-17', 2), k(PG, '04-22', 3), k(NHG, '04-30', 2)]),
 dict(id='haytian-army-before-santo-domingo-1805', kind='message_group', label='Norfolk report from St. Thomas on the Haytian army before St. Domingo',
      role='report', words=55,
      core=[r'(?:S\s?T\.\s+D\s?OMINGO\.\s*[—-]*\s*)?By\s+a\s+[Gg]entleman\s+from\s+S\s?t\.?\s+Thomas'],
      definition=("Printings of a Norfolk paragraph first found in the Norfolk Gazette of 6 May 1805: 'By a Gentleman from St. Thomas we are obligingly "
                  "informed of some circumstances respecting the defeat of the Haytians before the city of St. Domingo, by the garrison under command of "
                  "the brave Ferrand'. It quotes a summons from 'Jean Jacques, the first, Emperor of Hayti, to General Ferrand' and tells of an action "
                  "of 28 March. A report at second hand ('it is said'), told from the side of the French garrison; its words are the paper's."),
      first="A Norfolk report from St. Thomas (6 May 1805) on the Haytian army before the city of St. Domingo, told from the French garrison's side.",
      what='the report from St. Thomas',
      printings=[k(NG, '05-06', 2), k(EN, '05-10', 2), k(ADA, '05-11', 3), k(NI, '05-13', 3), k(BJ, '05-17', 2), k(PG, '05-20', 2), k(NHG, '05-21', 2)]),
 dict(id='folger-report-toulon-fleet-off-cadiz-1805', kind='message_group', label="Boston report: Captain Folgier's news that the Toulon fleet is out",
      role='report', words=55,
      core=[r'T\s?OULON\s+F\s?LEET\s+O\s?UT', r'Capt\.?\s+Folger,?\s+arrived\s+at\s+Boston'],
      definition=("Printings of a Boston report of May 1805, headed in most papers 'TOULON FLEET OUT': Captain Folgier (so printed in most papers; "
                  "'Folger' in the Oracle Post and the Virginia Argus, 'Foigier' in the National Intelligencer), arrived from Lisbon, 'is the bearer of the "
                  "very interesting intelligence of the escape of the French fleet from Toulon'; a transport ship had brought Lisbon the news of the "
                  "fleet off Cadiz. A ship captain's report of news at second hand."),
      first="A Boston report (May 1805): Captain Folgier brings news from Lisbon that the French fleet has left Toulon.", what="Captain Folgier's report",
      printings=[k(NI, '06-03', 3), (k(PG, '06-03', 3), dict(note="The paper's own introduction; the captain's statement is quoted.")), k(ADA, '06-03', 2),
                 k(OP, '06-04', 2), k(EN, '06-07', 1), k(BJ, '06-07', 2), k(VA, '06-08', 2), k(NG, '06-08', 3)]),
 dict(id='strong-speech-to-massachusetts-legislature-june-1805', kind='document_group', label="Governor Strong's speech to the Massachusetts legislature",
      role='published_document', words=55, dateline=False,
      core=[r'S\s?PEECH\s+Of\s+Governor\s+\w+\s+to\s+the\s+Legislature',
            r'Gentlemen\s+of\s+the\s+[Ss]enate,?\s+and\s+Gentlemen\s+of\s+the\s+House\s+of\s+Representatives[.,]?\s+I?\s*E\s?MBRACE',
            r'Extract\s+from\s+governor\s+Strong.?s\s+Speech'],
      definition=("Printings of the speech of Caleb Strong, Governor of Massachusetts, to the two houses of the legislature, June 1805: 'I embrace with "
                  "pleasure the opportunity of congratulating you on the return of the anniversary, established by our Constitution'. He speaks of "
                  "debtors, land disputes in the eastern counties, banks, and Kentucky's proposed amendment on the federal courts. A governor's own "
                  "policy argument."),
      first="Governor Strong's speech to the Massachusetts legislature (June 1805).", what="Governor Strong's speech",
      printings=[k(PG, '06-11', 2), k(HUS, '06-15', 1), k(OP, '06-18', 1),
                 (k(ADA, '06-18', 3), dict(role='document_excerpt', note='Printed as an extract: the passage on banking.')),
                 k(NI, '06-19', 1), k(VA, '06-22', 2), k(NG, '06-25', 3)]),
 # --- July to December (reader B's half of the year) ---------------------------------------------------------------------
 dict(id='lewis-and-clark-news-from-fort-mandan-1805', kind='context_group', label="News from Lewis and Clark's party at Fort Mandan, 1805",
      definition=("Two items printed in July and August 1805 about the party of discovery on the Missouri under Captains Lewis and Clark: a Kentucky "
                  "account of the party's winter at Fort Mandan, and Captain Lewis's letter to the President of 7 April 1805. Contains those two groups."),
      children=['kentucky-account-of-the-party-of-discovery-1805', 'lewis-letter-to-the-president-7-april-1805']),
 dict(id='kentucky-account-of-the-party-of-discovery-1805', parent='lewis-and-clark-news-from-fort-mandan-1805', kind='message_group',
      label='A Kentucky account of the party of discovery at Fort Mandan', role='report', words=55,
      core=[r'(?:L\s?OUISIANA\.\s+)?T\s?HE\s+party\s+of\s+discovery,?\s+under\s+the\s+command\s+of\s+[Cc]ap'],
      definition=("Printings of an account from Lexington, Kentucky (June 1805): 'The party of discovery, under the command of captains Lewis and Clark, "
                  "left the mouth of the Missouri on the 19th of May, 1804'; it tells, from the party's dispatches and letters, of its winter quarters "
                  "at Fort Mandan, the river, the country, its animals and the Indian nations the party met. A report at second hand; its words about "
                  "the Indian nations are the party's and the paper's."),
      first="A Kentucky account (June 1805) of Lewis and Clark's party of discovery and its winter at Fort Mandan.", what='the Kentucky account',
      printings=[k(ADA, '07-10', 2), k(NI, '07-12', 1), k(NHG, '07-16', 2), k(EN, '07-16', 2), k(NG, '07-19', 2), (k(BJ, '07-26', 1), dict(field=CA)),
                 k(HUS, '07-27', 1)]),
 dict(id='lewis-letter-to-the-president-7-april-1805', parent='lewis-and-clark-news-from-fort-mandan-1805', kind='document_group',
      label="Captain Lewis's letter to the President from Fort Mandan", role='published_document', words=55,
      core=[r'A\s+letter\s+from\s+Capt(?:ain|\.)?\s+Meriwether\s+Lewis'],
      definition=("Printings of 'A letter from Captain Meriwether Lewis to the President of the United States. Fort Mandan, April 7th, 1805': 'Herewith "
                  "inclosed you will receive an invoice of certain articles, which I have forwarded to you from this place'; he describes the party and "
                  "its plans for going on. The writer's own account."),
      first="Captain Lewis writes to the President from Fort Mandan (7 April 1805), sending specimens and describing the party's plans.", what="Lewis's letter",
      printings=[k(NI, '07-17', 2), k(ADA, '07-19', 2), k(VA, '07-24', 3), k(NG, '07-24', 3), k(BJ, '07-26', 2), k(NHG, '08-06', 2)]),
 dict(id='cowdery-letter-from-tripoli-1805', kind='message_group', label="Surgeon Cowdery's letter from captivity in Tripoli", role='report', words=55,
      core=[r'(?:T\s?RIPOLITAN\s+C\s?APTIVITY\.\s+)?A\s+letter\s+from\s+Jonathan\s+\w+,?\s+[Ee]sq'],
      definition=("Printings of 'A letter from Jonathan Cowdery, Esq. Surgeon of the late frigate Philadelphia, now a captive in Tripoli, to Dr. Mitchell, "
                  "dated 24th November, 1804': the Bashaw 'has taken me from the prison where my fellow-officers are confined, and ordered me to attend "
                  "his sick slaves, who are principally Neapolitans, negroes, and our unfortunate crew'. A captive officer's own account, in a letter to "
                  "a member of Congress."),
      first="Surgeon Jonathan Cowdery writes from captivity in Tripoli (24 November 1804) to Dr. Mitchell.", what="Cowdery's letter",
      printings=[k(ADA, '08-01', 2), k(PGZ, '08-05', 2), k(NI, '08-05', 3), k(NG, '08-05', 2), k(NHG, '08-06', 3), k(EN, '08-06', 2), k(VA, '08-07', 3),
                 k(BJ, '08-09', 3)]),
 dict(id='madison-answer-to-the-charleston-insurers-10-july-1805', kind='document_group',
      label="Madison's answer to the Charleston memorial on the ship Two Friends", role='published_document', words=55, dateline=False,
      core=[r'(?:COPY\.\s+)?Department\s+of\s+State,?\s+10th\s+(?:of\s+)?July'],
      definition=("Printings of the Secretary of State's letter of 10 July 1805 to the president of the South Carolina Insurance Company at Charleston: 'I "
                  "have received your letter of the 22d ult. inclosing the memorial of the insurance company of which you are President, and of the "
                  "merchants and others, interested', on the capture of the ship Two Friends by a French privateer and on French privateers off "
                  "Charleston bar. The government's own answer; the memorial it answers is the merchants' complaint."),
      first="The Secretary of State answers the Charleston insurers (10 July 1805) on the capture of the ship Two Friends.", what="Madison's answer",
      printings=[k(EN, '08-16', 3), k(NG, '08-16', 3), k(NI, '08-19', 3), k(ADA, '08-22', 3), k(HUS, '08-24', 3), k(VA, '08-28', 3), k(BJ, '08-30', 3)]),
 dict(id='peace-with-tripoli-news-1805', kind='context_group', label='News of the peace with Tripoli, 1805',
      definition=("How the peace with Tripoli of June 1805 reached the papers from late August: the Salem Register's report of news from Naples, and the "
                  "letters released at Washington in September: Commodore Rodgers's letter on the peace, with the government's notice, Captain Hull's "
                  "letter on the attack on Derne and Commodore Barron's letter to William Eaton. Contains those four groups."),
      children=['salem-register-report-by-the-belleisle-1805', 'rodgers-letter-on-the-peace-with-tripoli-8-june-1805',
                'hull-letter-on-the-attack-on-derne-28-april-1805', 'barron-letter-to-eaton-22-march-1805']),
 dict(id='salem-register-report-by-the-belleisle-1805', parent='peace-with-tripoli-news-1805', kind='message_group',
      label='Salem report: news from Naples by the brig Belle-Isle', role='report', words=55,
      core=[r'(?:From\s+the\s+S\s?ALEM\s+R\s?EGISTER,?\s+(?:of\s+)?Aug(?:ust|\.)?\s*2\d\.\s+|I\s?MPORTANT\s+N\s?EWS\s+FROM\s+T\s?RIPOLI\.\s+)?Yesterday,?\s+the\s+brig\s+Bel'],
      definition=("Printings of a report from the Salem Register of 29 August 1805: 'Yesterday the brig Belle-Isle, Capt. Leach, arrived here in 66 days "
                  "from Naples. About eight days before he sailed, news arrived there, that Gen. Eaton, at the head of the small American force which had "
                  "been detached from our Mediterranean squadron, and the troops collected by the rival brother of the Bashaw of Tripoli, had had an "
                  "engagement'. News heard at Naples, reported at second hand."),
      first='The Salem Register reports (29 August 1805) news from Naples of a battle at Derne and a peace with Tripoli.', what='the Salem report',
      printings=[k(HUS, '08-31', 3), (k(PGZ, '09-02', 2), dict(core=[r'S\s?ALEM,?\s+A\s?UGUST\s+2\w\.\s+Ye\w+\s+the\s+brig'])), k(NI, '09-04', 2), k(ADA, '09-05', 3), k(EN, '09-06', 3), k(VA, '09-07', 3), k(NG, '09-09', 2),
                 (k(EN, '09-10', 2), dict(note='Printed again, as from the Salem Register of 29 August.')), k(BJ, '09-13', 2)]),
 dict(id='rodgers-letter-on-the-peace-with-tripoli-8-june-1805', parent='peace-with-tripoli-news-1805', kind='document_group',
      label="The official notice of peace with Tripoli and Commodore Rodgers's letter", role='document_excerpt', words=60, dateline=False,
      core=[r'(?:O\s?FFICIAL\.?\s+)?P\s?RELIMINARIES\s+of\s+peace\s+with\s+Trip',
            r'The\s+following\s+is\s+an\s+extra\w*\s+of\s+a\s+letter\s+(?:from|fpom)\W{0,3}\s*[Cc]ommodore\s+Ro'],
      definition=("Printings of the government's notice of September 1805, 'Preliminaries of peace with Tripoli were signed on the second day of June last, "
                  "and on the same day capt. Bainbridge, the officers and crew of the late frigate Philadelphia were liberated', with an extract of a "
                  "letter from Commodore Rodgers to the Secretary of the Navy, U. S. ship Constitution, 8 June 1805: 'The Bashaw, conscious, that by a "
                  "continuance of his obstinacy, his town would fall a sacrifice to our forces ... proposed to us terms of peace'. The commodore's name is "
                  "printed 'Rodgers' or 'Rogers'. The government's notice and the commander's own account."),
      first="The government's notice (September 1805) that peace with Tripoli was signed on 2 June, with an extract of Commodore Rodgers's letter.",
      what="the notice and Rodgers's letter",
      printings=[k(ADA, '09-14', 2), k(NI, '09-16', 3), k(NG, '09-16', 2), k(VA, '09-18', 2), (k(EN, '09-20', 2), dict(field=CA)), k(BJ, '09-20', 2),
                 k(HUS, '09-21', 2), k(PGZ, '09-23', 2), k(NHG, '09-24', 2)]),
 dict(id='hull-letter-on-the-attack-on-derne-28-april-1805', parent='peace-with-tripoli-news-1805', kind='document_group',
      label="Captain Hull's letter on the attack on Derne", role='published_document', words=55, dateline=False,
      core=[r'(?:The\s+following\s+is\s+a\s+)?[Cc]opy\s+of\s+a\s+letter\s+from\s+[Cc]apt(?:ain|\.)?\s+(?:Isaac\s+)?Hull'],
      definition=("Printings of 'a copy of a letter from capt. Hull, of the Argus, to commodore Barron, dated Argus, (Derne) April 28' (1805), released with "
                  "Commodore Rodgers's letter in September: 'I have the honor to inform you, that at nine o'clock in the morning of the 27th, being about "
                  "ten miles to the eastward of the town of Derne, with the Hornet in company, we discovered the Nautilus at anchor'. An officer's own "
                  "account of the attack on Derne."),
      first="Captain Hull's letter to Commodore Barron (28 April 1805) on the attack on Derne.", what="Hull's letter",
      printings=[k(ADA, '09-14', 3), k(NI, '09-16', 3), k(NG, '09-16', 2), k(EN, '09-20', 2), k(BJ, '09-20', 2), k(HUS, '09-21', 2), k(NHG, '09-24', 2)]),
 dict(id='barron-letter-to-eaton-22-march-1805', parent='peace-with-tripoli-news-1805', kind='document_group',
      label="Commodore Barron's letter to William Eaton, 22 March", role='document_excerpt', words=55, dateline=False,
      core=[r'(?:O\s?FFICIAL\.?\s+)?The\s+following\s+is\s+an?\s+extract\s+(?:of\s+)?a\s+letter\s+from\s+[Cc]om\w*\.?\s+(?:Samuel\s+)?Barron'],
      definition=("Printings of 'an extract of a letter from Commodore Barron to William Eaton, Esq. dated Malta, March 22, 1805', released at Washington in "
                  "September: 'You must be sensible that in giving their sanction to a co-operation with the Ex-Bashaw, government did not contemplate the "
                  "measure as leading necessarily and absolutely to a re-instatement of that Prince'; he withholds his sanction from any convention "
                  "binding the United States to place the Ex-Bashaw on the throne. The commodore's own instructions and reasoning."),
      first="Commodore Barron writes to William Eaton (22 March 1805) on the limits of American support for the Ex-Bashaw.", what="Barron's letter",
      printings=[k(NI, '09-16', 3), k(ADA, '09-16', 3), k(NG, '09-18', 2), k(EN, '09-20', 2), k(VA, '09-21', 3),
                 (k(PGZ, '09-23', 2), dict(core=[r'M\s?ALTA,?\s+M\s?ARCH\s+2\d,'], note="Printed with the date 'Malta, March 20, 1805' and the salutation 'Dear Sir', after the paper's own introduction.")),
                 k(NHG, '09-24', 2), (k(ADA, '09-25', 3), dict(note='Printed again, under a Norfolk Herald introduction.')),
                 (k(HUS, '09-28', 2), dict(core=[r'["“]?M\s?ALTA,?\s+M\s?ARCH\s+2\d\.?["”]?\s+["“]?D\s?EAR\s+S\s?IR'], note="Printed with the date 'Malta, March 20' and the salutation 'Dear Sir', after the paper's own comment."))]),
 dict(id='calder-dispatch-23-july-1805', kind='document_group', label="Admiral Calder's dispatch on the action of 22 July", role='published_document',
      words=55, dateline=False,
      core=[r'P\s?RINCE\s+of\s+W\s?ALES,?\s+July\s+\d+'],
      definition=("Printings of the dispatch of Vice-Admiral Sir Robert Calder to Admiral Cornwallis, 'Prince of Wales, July 23, 1805', from the London "
                  "Gazette: 'Yesterday at noon ... I was favored with a view of the combined squadrons of France and Spain, consisting of 20 sail of the "
                  "line'; he 'brought on an action which lasted upwards of four hours' and took two ships. The British commander's own account."),
      first="Admiral Calder's dispatch (23 July 1805) on his action with the combined squadrons of France and Spain.", what="Calder's dispatch",
      printings=[k(HUS, '09-14', 2), k(PGZ, '09-16', 2), k(NHG, '09-17', 2), k(ADA, '09-19', 2), k(NI, '09-20', 1), k(VA, '09-21', 3), k(NG, '09-23', 2),
                 k(EN, '09-24', 1), k(BJ, '09-27', 2)]),
 dict(id='british-orders-on-american-vessels-with-colonial-produce-1805', kind='context_group',
      label='British orders on American vessels carrying colonial produce, 1805',
      definition=("Two items on British orders concerning American vessels that carried the produce of the enemy's colonies, as the papers printed them "
                  "from September 1805: a London paragraph of 7 and 8 August reporting an order to detain such vessels, and the Privy Council's minute "
                  "of 3 August as the British consuls published it in November. Contains those two groups."),
      children=['london-paragraph-order-to-detain-american-vessels-1805', 'privy-council-minute-3-august-1805']),
 dict(id='london-paragraph-order-to-detain-american-vessels-1805', parent='british-orders-on-american-vessels-with-colonial-produce-1805',
      kind='message_group', label='London paragraph: an order to detain American vessels', role='report', words=55, dateline=False,
      core=[r'(?:From\s+a\s+London\s+paper,?\s+of\s+Aug\.?\s*7\.\s+|A\s+London\s+paper\s+of\s+the\s+7th\s+August,?\s+says\s+["“]?)?'
            r'An\s+order,?\s+(?:we\s+understand|it\s+is\s+said),?\s+was\s+sent\s+to\s+all\s+the\s+out'],
      definition=("Printings of a London newspaper paragraph of 7 or 8 August 1805: 'An order, we understand, was sent to all the out ports some days ago, "
                  "instructing our cruisers to detain all American vessels which have on board property not the produce of the United States. This "
                  "order has been already acted upon'. A report ('we understand', 'it is said'); the reason it gives is the London paper's. The paragraph "
                  "of 7 August ('we understand', 'not the produce') and of 8 August ('it is said', 'not the property') are counted together."),
      first='A London paragraph (7 August 1805) reports an order to detain American vessels carrying property not the produce of the United States.',
      what='the London paragraph',
      printings=[k(HUS, '09-14', 2), k(PGZ, '09-16', 2), k(NI, '09-20', 2), k(ADA, '09-20', 2), k(NG, '09-23', 3), k(EN, '09-24', 2), k(VA, '09-28', 2),
                 (k(ADA, '10-05', 2), dict(note='Printed again.'))]),
 dict(id='privy-council-minute-3-august-1805', parent='british-orders-on-american-vessels-with-colonial-produce-1805', kind='document_group',
      label="The Privy Council's minute of 3 August, published by the British consuls", role='published_document', words=55,
      core=[r'His\s+Britann?ic?k?\s+[Mm]ajesty.?s\s+[Cc]onsul', r'(?:OFFICIAL\.\s+)?British\s+Consul\s+General.?s\s+Office'],
      definition=("Printings of the minute of the Lords of the British Privy Council of 3 August 1805 on the trade carried on in neutral ships, as the British "
                  "consuls published it to American merchants in November: their Lordships resolved 'to allow the trade with the settlements and islands, "
                  "belonging to the enemy, in America and the West Indies, to be carried on through the medium of the British free ports in the West "
                  "Indies, and not otherwise', with an exception for ships cleared from the Havana before 1 November. Three consuls' notices are counted "
                  "together: the consul general's at Philadelphia, the consul's for Virginia and the consul general's at New York, the last two with an "
                  "'Extract of Council Minute'. Britain's own document."),
      first="The British consul general publishes (11 November 1805) the Privy Council's minute of 3 August on the colonial trade in neutral ships.",
      what="the consuls' notice of the minute",
      printings=[k(NI, '11-15', 3), k(ADA, '11-15', 3), (k(NG, '11-15', 2), dict(note="The Virginia consul's notice, with the 'Extract of Council Minute'.")),
                 k(EN, '11-19', 3), k(VA, '11-20', 2), (k(EN, '11-22', 2), dict(note="Printed again, in the Virginia consul's form.")),
                 (k(RIR, '12-05', 3), dict(note="The notice of the consul general at New York, with the 'Extract of Council Minute'."))]),
 dict(id='algiers-insurrection-and-change-of-dey-1805', kind='context_group', label='Reports from Algiers, 1805',
      definition=("Two items from Algiers printed from September to November 1805: a Salem report, by way of Leghorn, of an insurrection at Algiers, and "
                  "the letter of 9 September of the American charge d'affaires at Algiers that 'the soldiers rose in a body and murdered the Dey'. "
                  "Contains those two groups."),
      children=['shillaber-report-from-algiers-1805', 'mountford-letter-from-algiers-9-september-1805']),
 dict(id='shillaber-report-from-algiers-1805', parent='algiers-insurrection-and-change-of-dey-1805', kind='message_group',
      label="Salem report: Captain Shillaber's news of an insurrection at Algiers", role='report', words=55,
      core=[r'(?:B\s?LOODY\s+S\s?CENES?\s+(?:AT|at)\s+A\s?LGIERS\W{0,4}\s*)?Cap(?:t\.?|tain)\s+S\w*ab?er,?\s+(?:arrived|from)'],
      definition=("Printings of a Salem report of September 1805, headed in most papers 'Bloody Scenes at Algiers': 'Capt. Shillaber, from Leghorn, informs "
                  "us, that on the 7th July a brig arrived there from Algiers, and brought accounts of an insurrection at that place'; a Leghorn letter "
                  "of 8 July follows. News at third hand: a shipmaster repeats what a brig brought to Leghorn."),
      first="A Salem report (September 1805): Captain Shillaber brings news from Leghorn of an insurrection at Algiers.", what="Shillaber's report",
      printings=[k(HUS, '09-21', 3), k(PGZ, '09-23', 2), k(NHG, '09-24', 2), k(ADA, '09-24', 3), k(NI, '09-25', 3), k(VA, '09-28', 2), k(EN, '10-01', 2),
                 k(BJ, '10-04', 2)]),
 dict(id='mountford-letter-from-algiers-9-september-1805', parent='algiers-insurrection-and-change-of-dey-1805', kind='message_group',
      label="Mountford's letter from Algiers, 9 September", role='report', words=55,
      core=[r'(?:COPY\.\s+)?A\s?LGIERS,?\s+Sept(?:ember|\.)?\s*9', r'S\s?IR,?\s+I\s+have\s+only\s+a\s+few\s+moments'],
      definition=("Printings of a letter dated 'Algiers, September 9, 1805', from Mr. Mountford, 'secretary of Mr. Lear, and now our charge d'affaires at "
                  "Algiers', which General Eaton gave to the Enquirer: 'I have only a few moments to inform you, our affairs here are well. On the 30th "
                  "ult. the soldiers rose in a body and murdered the Dey and his prime minister.' An American official's own short report; the words "
                  "are his."),
      first="A letter from Algiers (9 September 1805): the American charge d'affaires writes that the soldiers rose and killed the Dey.",
      what="Mountford's letter",
      printings=[k(EN, '11-15', 3), k(VA, '11-16', 2), k(ADA, '11-19', 3), k(NI, '11-20', 3), k(NG, '11-20', 2), k(BJ, '11-29', 2), k(HUS, '11-30', 3)]),
 dict(id='paris-article-on-the-austrian-armaments-31-august-1805', kind='message_group', label='A Paris article of 31 August on the Austrian armies',
      role='report', words=55,
      core=[r'The\s+(?:frontiers|movements)\s+of\s+the\s+[Ee]mpire\s+seems?\s+to\s+be\s+menaced'],
      definition=("Printings of a Paris article dated 31 August 1805, from French and Dutch papers: 'The frontiers of the empire seem to be menaced by the "
                  "movements of the Austrian armies. Thirty thousand men are to march from the camps of Boulogne to the banks of the Rhine'; it blames "
                  "the British cabinet for the war and warns that 'there is in future more than one day of Marengo to France and Austria'. One "
                  "government's side, in a Paris paper: argument and warning."),
      first='A Paris article (31 August 1805): the Austrian armies menace the frontiers, and troops march from Boulogne to the Rhine.', what='the Paris article',
      printings=[k(NHG, '10-29', 2), k(ADA, '11-01', 2), (k(RIR, '11-02', 3), dict(note='The rest of the article follows in the issue of 14 November.')),
                 k(HUS, '11-02', 2), k(NI, '11-04', 1), k(NG, '11-04', 3), k(EN, '11-05', 2), k(VA, '11-06', 2), k(BJ, '11-08', 2)]),
 dict(id='creek-treaty-washington-paragraph-1805', kind='message_group', label='Washington paragraph on a treaty with the chiefs of the Creek Nation',
      role='report', words=55,
      core=[r'A\s+very\s+advantageous\s+T\s?REATY\s+has\s+been\s+made'],
      definition=("Printings of a paragraph of the National Intelligencer of 18 November 1805: 'A very advantageous TREATY has been made, we understand, at "
                  "this place, with the chiefs of the Creek Nation; by which a large cession of land is made to the United States, and the right given to "
                  "open a direct road to New Orleans'. The government paper's report ('we understand'); 'very advantageous' is its own judgement."),
      first='A Washington paragraph (18 November 1805) reports a treaty made with the chiefs of the Creek Nation.', what='the paragraph on the treaty',
      printings=[k(NI, '11-18', 3), k(ADA, '11-19', 3), k(EN, '11-22', 3), k(VA, '11-23', 3), k(BJ, '11-29', 3), k(HUS, '11-30', 3), k(NHG, '12-03', 2),
                 k(RIR, '12-05', 3)]),
 dict(id='napoleon-speech-to-the-senate-september-1805', kind='document_group', label="Napoleon's speech to the French Senate, September 1805",
      role='published_document', words=55, dateline=False,
      core=[r'The\s+E\s?mperor.?s\s+[Ss]peech\s+in\s+the\s+[Ss]enate', r'S\s?PEECH\s+OF\s+THE\s+E\s?MPEROR\s+OF\s+F\s?RANCE',
            r'On\s+the\s+21st\s+inst\.?,?\s+the\s+Emperor\s+met'],
      definition=("Printings of the speech of the Emperor Napoleon to the French Senate in September 1805, from Paris papers: 'Senators, In the present "
                  "circumstances of Europe, I feel the necessity of appearing in the midst of you, and of making known to you my sentiments'; he is about "
                  "to leave his capital to put himself at the head of the army. A head of state's own account. The Norfolk Gazette prints another "
                  "translation ('I come among you to communicate my sentiments'), counted with the others."),
      first="The Emperor Napoleon's speech to the French Senate (September 1805) on leaving to put himself at the head of the army.", what="Napoleon's speech",
      printings=[(k(NG, '11-20', 2), dict(note='Another translation of the speech.')), k(NI, '11-22', 3), k(NHG, '11-26', 3), k(EN, '11-26', 3), k(VA, '11-27', 1),
                 k(HUS, '11-30', 2), k(PGZ, '12-02', 2), k(RIR, '12-05', 2), k(BJ, '12-06', 2)]),
 dict(id='spanish-order-on-american-vessels-at-algeziras-5-september-1805', kind='document_group',
      label='A royal order from Madrid on American vessels carried into Algeziras', role='published_document', words=55,
      core=[r'M\s?ADRID\W{0,3}\s*Sept(?:ember|\.)?,?\s*[35]', r'M\s?OST\s+E\s?XCELLENT\s+S\s?IR'],
      definition=("Printings of a royal order dated 'Madrid, Sept. 3, 1805' (5 September in some papers), as the Spanish commander of marine at Algeziras "
                  "received it and a Gibraltar paper printed it: 'His Excellency, the Minister of the United States, has complained of new grievances and "
                  "captures of American vessels by the Spanish privateers; and that eleven Americans have been carried into Algeziras'; vessels taken "
                  "only for carrying English goods are to be released. The Spanish government's own order, at second hand."),
      first='A royal order from Madrid (September 1805) on American vessels carried into Algeziras by Spanish privateers.', what='the royal order',
      printings=[k(HUS, '11-23', 3), k(PGZ, '11-25', 2), k(NHG, '11-26', 2), k(NI, '11-27', 3), k(ADA, '11-27', 2), k(NG, '12-02', 2), k(VA, '12-04', 2),
                 k(BJ, '12-06', 2)]),
 dict(id='president-message-3-december-1805', kind='document_group', label="The President's message to Congress, 3 December 1805",
      role='published_document', words=55, dateline=False,
      core=[TO_CONGRESS + r'(?:M\s?ESSAGE[:.]?\s+)?A\s?T\s+a\s+moment\s+when\s+the\s+nations\s+of\s+Europe'],
      definition=("Printings of President Jefferson's annual message to Congress of 3 December 1805: 'At a moment when the nations of Europe are in commotion "
                  "and arming against each other, and when those with whom we have principal intercourse are engaging the resources of commerce in their "
                  "contest'. He speaks of injuries to American commerce, of Spain and the territories of Orleans and the Mississippi, of gun boats and the "
                  "militia, the peace with Tripoli, the Indian nations and the Treasury. The executive's own account and recommendations."),
      first="President Jefferson's annual message to Congress (3 December 1805).", what="the President's message",
      printings=[k(NI, '12-03', 3), k(ADA, '12-04', 2), k(EN, '12-06', 3), k(NG, '12-09', 3), k(RIR, '12-12', 1), k(BJ, '12-13', 1), k(HUS, '12-14', 1),
                 k(PGZ, '12-16', 2), k(NHG, '12-17', 1)]),
 dict(id='collingwood-dispatch-on-trafalgar-22-october-1805', kind='document_group', label="Admiral Collingwood's dispatch on the action off Cape Trafalgar",
      role='published_document', words=65, dateline=False,
      core=[r'A\s?DMIRALTY.?\s?O\s?FFICE,?\s+Nov(?:ember|\.)?\s*6,?\s*(?:1805)?\.?\s+D\s?ISPATCHES', r'D\s?ISPATCHES,?\s+of\s+which\s+the\s+following\s+are'],
      definition=("Printings of the London Gazette Extraordinary of 6 November 1805: 'Dispatches, of which the following are copies, were received at the "
                  "Admiralty this day at one o'clock A. M. from vice-admiral Collingwood', with his dispatch 'Euryalus, off Cape Trafalgar, Oct. 22': 'The "
                  "ever to be lamented death of vice-admiral lord viscount Nelson, who, in the late conflict with the enemy, fell in the hour of "
                  "victory'. The British commander's own account."),
      first="Admiral Collingwood's dispatch from off Cape Trafalgar (22 October 1805), from the London Gazette Extraordinary of 6 November.",
      what="Collingwood's dispatch",
      printings=[k(NI, '12-20', 3), k(ADA, '12-20', 2), k(HUS, '12-21', 2), k(PGZ, '12-23', 2), k(NG, '12-23', 2), k(NHG, '12-24', 2), k(VA, '12-24', 2),
                 k(EN, '12-24', 2), k(RIR, '12-26', 2)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline or heading directly before the item, after a sentence boundary (as for 1776, 1807 and 1808): "NORFOLK, July 6."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*180[45])?\.\s*(?:[—-]+\s*)?)$")


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
    stop: a regex; the excerpt ends before its first match (to end before private persons' names)."""
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
            problems.append((s['id'], key, 'page not in the 1805 pages'))
            continue
        text_fields = pages[key]['texts']
        cores = over.get('core', s['core'])
        if key in MISFILED:     # this page's RevX slot holds another scan page's text: read the CA text of the scan page
            fields = [CA]
        else:
            fields = [over['field']] if 'field' in over else [REVX, CA]
        for field in fields:
            text = text_fields.get(field) or ''
            start = item_start(text, cores, over.get('dateline', s.get('dateline', True)), over.get('back', False))
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
            note = (note+' ' if note else '') + ('The RevX transcriptions of this issue are filed one page off from the scans, so the excerpt '
                                                 'comes from the older CA transcription of this scan page.')
        elif field == CA and 'field' not in over:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'printed': pages[key]['date'], 'field': field, 'excerpt_start': first, 'excerpt_end': last,
                     'excerpt': excerpt, 'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['printed'], r['page_key'], r['story']))
    numbers = (n for n in range(1, 10**4) if n not in RETIRED)
    for r in rows:
        r['id'] = f'S05-{next(numbers):03}'
    return rows, problems


def build(rows, review):
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
               'admission_rule': 'Reviewed 1805 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    base, target = releases()
    return {
        'ledger_id': 'ledger:stories-1805', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': '2026-11-12', 'namespace': 'expansion-1805', 'evidence_dir': 'outputs/story_discovery_1805/evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1805, and of 1804 where they reach the 1805 pages (long-running ones '
                   'included), phrase searches on all 3,811 pages of 1805 in both transcriptions, reading of every hit, and scan checks of each '
                   'admitted passage'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             'outputs/story_discovery_1805/items.json': 'retrieval_candidates', 'outputs/story_discovery_1805/items_from_1804.json': 'retrieval_candidates',
                             'outputs/story_discovery_1805/phrase_patterns.json': 'retrieval_patterns', 'outputs/story_discovery_1805/phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1805.py': 'ledger_code', 'work/archive_data/ledgers/stories_1805_review.json': 'scan_review',
                             'outputs/story_discovery_1805/SCAN_PROTOCOL.md': 'review_protocol', 'outputs/story_discovery_1805/scan_points.json': 'review_protocol'},
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
    print('wrote', OUT, len(rows), 'observations,', len(STORIES), 'groups')
