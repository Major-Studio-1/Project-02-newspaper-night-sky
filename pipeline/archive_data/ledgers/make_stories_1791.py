"""Write ledgers/stories_1791.json: reviewed stories of 1791, round one.

1791 is a thin year: no item of 1791 reaches 7 papers, so it is read by the thin-year rule (docs/rules-and-exceptions.md,
Y-THIN, as amended on 23 November 2026, the owner's choice B1): an item, counted by its own words, is eligible when it was
printed by more than half of the newspapers that survive for its weeks (those with a surviving issue between its first and
its last printing, and at least in the three weeks from its first printing), and by at least 4; as in R-01, the items
printed by every newspaper that survives for their weeks are admitted, and the other eligible items are chosen to cover the
months and the kinds of news, about as many stories as a standard year; one affair's items are treated as in X-1800-01;
digests are not admitted. In 1791 4 to 6 papers survive for an item's weeks: the Gazette of the United States, the
New-Hampshire Gazette, the New Hampshire Gazetteer and the Patowmac Guardian through the year, the Kentucky Gazette except
from 23 July to 8 October, and the National Gazette from 31 October; so every eligible item is in 4 or more papers.
The automatic families first printed in 1791 that reach 3 or more papers, long-running ones included, were split into
single printed items with work/story_items.py --long-running (items.json), and again with year 1790 over the 1791 pages
(items_from_1790.json); every item in 3 or more papers was compared by machine with every page and counted again by its
opening, a sweep of word-for-word passages shared by 4 or more papers found short items the families miss, and the
admitted and chosen items were counted by their own words over all 1,242 pages of 1791 in both transcriptions. See
outputs/story_discovery_1791/README.md and count_1791.md.

The 1791 pages are those whose issue the data release dates to 1791 (work/year_search_pages.py 1791 ... --printed-dates);
no 1791 issue has a corrected date. 1791 has 6 catalogue series, which are 6 papers: the Gazette of the United States
(Philadelphia, 107 issues), the New-Hampshire Gazette (Portsmouth, 53), the New Hampshire Gazetteer (Exeter, 49), the
Patowmac Guardian (Shepherdstown, Virginia, 49), the Kentucky Gazette (Lexington, 41) and the National Gazette (Philadelphia,
18, from 31 October).
The release's map of misfiled RevX pages (derived/revx_page_map.parquet) lists 3 pages of 1791, of the New-Hampshire Gazette
of 12 February and 1 September; no printing of this ledger is on them.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-85 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1791_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (reviews of other years run at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1791.py [--table] [--base 0.11.30 --target 0.11.31]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1791/search_pages.json). The excerpts are cut from
the 1791 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1791'
D = PROJECT/'outputs/story_discovery_1791'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1791_review.json'
OUT = HERE/'stories_1791.json'
BASE, TARGET = '0.11.30', '0.11.31'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83030483': 'The Gazette of the United States', 'sn83025587': 'The New-Hampshire Gazette', 'sn82014782': 'The Kentucky Gazette',
         'sn84023133': 'The New Hampshire Gazetteer', 'sn84038410': 'The Patowmac Guardian', 'sn83025887': 'The National Gazette'}
ONE = {'GUS': 'sn83030483', 'NHG': 'sn83025587', 'KG': 'sn82014782', 'NHGR': 'sn84023133', 'PG': 'sn84038410', 'NG': 'sn83025887'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1791), page and edition."""
    return f'{ONE[paper]}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release (3 pages of 1791)."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()

S = r'\s+'
# Story groups. A parent ('context_group') lists its children and has no printings. 'printings' lists each printing's page;
# a tuple adds overrides for that printing: core (regexes for the item's first words), role, field, note, words, dateline
# (include a dateline directly before), head (a regex for a heading that ends directly before the core: the excerpt starts
# with it), back (start at the beginning of the sentence that holds the core), stop (a regex: the excerpt ends before it).
ACT = r'A\s?N\s+A\s?CT,?\s+'   # an act's excerpt starts with its title, as for 1808
STORIES = [
 # ---- January to March: news from India, the acts admitting Kentucky and Vermont, the President's message on commerce with
 # Great Britain, the act raising another regiment ----
 dict(id='calcutta-paper-on-tippoo-saib-and-the-rajah-of-travancore-january-1791', kind='message_group',
      label="Boston, January 1791: 'By an arrival at Salem, from India, a Calcutta paper has been received', with accounts of Tippoo Saib's operations against the Rajah of Travancore",
      definition="Printings of a Boston paragraph of 15 January 1791, headed 'Tippo Saib' in three of the papers: 'By an arrival at Salem, from India, a Calcutta paper has been received, which gives accounts of the operations of that inveterate enemy of the English, Tipoo Saib, the successor of the famous Hyder Ali, against the Rajah of Travencore. In one battle with the Rajah, Tippo is said to have been defeated, with the loss of 1300 men—and in a second, he is said to have assaulted the Rajah lines with incredible ferocity and bravery, and after a long contest, obtained a victory.' A Boston paper's report from a Calcutta paper.",
      role='report', words=50, dateline=True,
      head=r'T\s?I\s?P\s?P?\s?O\s+S\s?A\s?I\s?B\.?\s*',
      core=[r'B\s?Y\s+an\s+arrival\s+at\s+Salem'],
      first="A Calcutta paper brought to Salem gives accounts of Tippoo Saib's operations against the Rajah of Travancore.",
      what="the Boston paragraph on Tippoo Saib",
      printings=[(k('NHG', '01-22', 3), {'words': 75}), k('NHGR', '01-22', 3), (k('GUS', '01-29', 4), {'stop': r'\sTHE\s+NATIONAL\s+ASSEMBLY'}), k('PG', '02-08', 3)]),
 dict(id='the-acts-admitting-kentucky-and-vermont-into-the-union-february-1791', kind='context_group',
      label="The acts of Congress of February 1791 on the admission of Kentucky and Vermont into the Union",
      children=['act-declaring-the-consent-of-congress-to-the-state-of-kentucky-february-1791', 'act-for-the-admission-of-the-state-of-vermont-february-1791'],
      definition="Two acts of the third session of the first Congress, as the papers printed them from February to April 1791: the act declaring the consent of Congress that a new State be formed within the jurisdiction of Virginia and admitted into the Union by the name of the State of Kentucky, and the act for the admission of the State of Vermont into the Union. Contains those two groups."),
 dict(id='act-declaring-the-consent-of-congress-to-the-state-of-kentucky-february-1791', parent='the-acts-admitting-kentucky-and-vermont-into-the-union-february-1791', kind='document_group',
      label="An Act declaring the consent of Congress that a new State be formed within the jurisdiction of the Commonwealth of Virginia, and admitted into the Union by the name of the State of Kentucky",
      definition="Printings of the act: 'An Act declaring the consent of Congress, that a new State be formed within the jurisdiction of the Commonwealth of Virginia, and admitted into this Union, by the name of the State of Kentucky. Whereas the legislature of the Commonwealth of Virginia, by an act entitled, \"An act concerning the erection of the district of Kentucky into an independent State,\" passed the eighteenth day of December, one thousand seven hundred and eighty-nine, have consented, that the district of Kentucky, within the jurisdiction of the said Commonwealth, and according to its actual boundaries at the time of passing the act aforesaid, should be formed into a new State'. The Kentucky Gazette prints it twice, the second time among the papers of the Kentucky convention (C-08); the New-Hampshire Gazette's list of the session's acts of 16 June, which names it, is not counted (C-07). The act itself, as the papers print it.",
      role='published_document', words=60, dateline=False,
      core=[ACT + r'declaring\s+the\s+[Cc]onsent\s+of\s+Congress,?\s+that\s+a\s+new\s+[Ss]tate'],
      first="Congress consents that a new State be formed from the district of Kentucky and admitted into the Union.",
      what="the act concerning Kentucky",
      printings=[k('GUS', '02-09', 3), k('PG', '02-22', 2), k('NHG', '02-26', 1), k('KG', '03-19', 2, 2),
                 (k('KG', '04-16', 2, 2), {'note': 'Printed again, among the papers of the Kentucky convention.'})]),
 dict(id='act-for-the-admission-of-the-state-of-vermont-february-1791', parent='the-acts-admitting-kentucky-and-vermont-into-the-union-february-1791', kind='document_group',
      label="An Act for the admission of the State of Vermont into this Union",
      definition="Printings of the act: 'An Act for the admission of the State of Vermont into this Union. The State of Vermont having petitioned the Congress to be admitted a Member of the United States—Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled, and it is hereby enacted and declared, That, on the Fourth day of March, one thousand seven hundred and ninety-one, the said State, by the name and style of \"The State of Vermont,\" shall be received and admitted into the Union, as a new and entire Member of the United States of America.' The Patowmac Guardian prints only the House's proceedings on the bill, and the New-Hampshire Gazette's list of the session's acts of 16 June names it; neither is counted (C-07). The act itself, as the papers print it.",
      role='published_document', words=60, dateline=False,
      core=[ACT + r'for\s+the\s+admission\s+of\s+the\s+State\s+of\s+V\s?ERMONT'],
      first="Congress admits the State of Vermont into the Union from 4 March 1791.",
      what="the act admitting Vermont",
      printings=[k('GUS', '02-26', 4), k('KG', '03-19', 2, 2), k('NHG', '03-19', 1), k('NHGR', '03-26', 4)]),
 dict(id='presidents-message-of-14-february-1791-on-commerce-with-great-britain', kind='document_group',
      label="The President's message to Congress of 14 February 1791: 'Soon after I was called to the administration of the government, I found it important to come to an understanding with the court of London'",
      definition="Printings of the President's message to the Senate and the House of Representatives of 14 February 1791: 'Soon after I was called to the administration of the government, I found it important to come to an understanding with the court of London, on several points interesting to the United States, and particularly to know whether they were disposed to enter into arrangements, by mutual consent, which might fix the commerce between the two nations on principles of reciprocal advantage. For this purpose I authorized informal conferences with their ministers; and from these I do not infer any disposition on their part, to enter into any arrangements merely commercial.' The President's own message.",
      role='published_document', words=75, dateline=False,
      head=(r'(?:M\s?ESSAGE\s+from\s+the\s+P\s?RESIDENT\s*[—\-]+\s*read\s+in\s+the\s+House\s+of\s+Representatives\s+of\s+the\s+United\s+States,?\s+on\s+Monday\s+(?:last|the\s+14th\s+inst)\.?\s*[\"“]?\s*)?'
            r'(?:United\s+States,?\s+Feb(?:ruary|\.)?\s+14[.,]?\s*1791\.?\s*[\"“]?\s*)?G\s?ENTLEMEN\s+of\s+the\s+Senate,?\s+and\s+(?:of\s+the\s+)?House\s+of\s+Representatives[,.]?\s*[\"“]?\s*'),
      core=[r'S\s?OON\s+after\s+I\s+was\s+called\s+to\s+the\s+administration'],
      first="The President tells Congress that informal conferences with the British ministers show no disposition 'to enter into any arrangements merely commercial'.",
      what="the President's message of 14 February",
      printings=[k('GUS', '02-19', 3), k('PG', '03-08', 3), k('NHG', '03-12', 2), k('NHGR', '03-19', 2)]),
 dict(id='act-for-raising-and-adding-another-regiment-march-1791', kind='document_group',
      label="An Act for raising and adding another regiment to the military establishment of the United States, and for making further provision for the protection of the frontiers",
      definition="Printings of the act: 'An Act for raising and adding another Regiment to the Military Establishment of the United States, and for making farther Provision for the Protection of the Frontiers. Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled, That there shall be raised an additional regiment of infantry, which, exclusive of the commissioned officers, shall consist of nine hundred and twelve non-commissioned officers, privates and musicians.' The New-Hampshire Gazette's list of the session's acts of 16 June, which names it, is not counted (C-07). The act itself, as the papers print it.",
      role='published_document', words=60, dateline=False,
      core=[ACT + r'for\s+raising\s+and\s+adding\s+another\s+[Rr]egiment'],
      first="Congress raises an additional regiment of infantry and makes further provision for the protection of the frontiers.",
      what="the act raising another regiment",
      printings=[k('GUS', '03-30', 4), k('PG', '04-12', 1), k('NHGR', '04-16', 1), k('NHG', '06-02', 1)]),
 # ---- April to June: the first stone of the Federal District, the French duties, General Scott's expedition ----
 dict(id='alexandria-the-first-corner-stone-of-the-federal-district-april-1791', kind='message_group',
      label="Alexandria, April 1791: the commissioners Daniel Carroll and David Stewart arrive to superintend the fixing of the first corner-stone of the Federal District",
      definition="Printings of an Alexandria paragraph of 21 April 1791: 'On Friday the 15th inst. the Hon. Daniel Carroll, and Dr. David Stewart, arrived in this town, to superintend the fixing of the first Corner-Stone of the Federal District.' The paragraph goes on to the procession of the Mayor and Commonality and the members of the town's lodges to Jones's Point. An Alexandria paper's report.",
      role='report', words=50, dateline=True, stop=r'\s(?:By\s+neglect|The\s+Mayor\s+and\s+Common)',
      core=[r'O\s?N\s+Friday,?\s+the\s+15th\s+inst'],
      first="The commissioners Daniel Carroll and David Stewart arrive at Alexandria to superintend the fixing of the first corner-stone of the Federal District.",
      what="the Alexandria paragraph on the first corner-stone",
      printings=[k('GUS', '04-30', 2), k('PG', '05-03', 3), k('NHG', '05-12', 2), k('KG', '06-18', 2, 2)]),
 dict(id='letter-from-paris-of-10-march-1791-on-the-importation-of-oil', kind='message_group',
      label="A letter from Paris of 10 March 1791: the National Assembly decrees that 'the importation of oil from any country, but the United States of America, shall be prohibited'",
      definition="Printings of a letter from Paris of 10 March 1791 on the duties the National Assembly decreed on foreign importations: 'The importation of oil from any country, but the United States of America, shall be prohibited. The oil imported from the United States of America, in French or American vessels, shall pay a duty of twelve livres per quintal.' The New-Hampshire Gazette and the New Hampshire Gazetteer print an extract of the letter ('Our Assembly has at last decreed the duties which are to be paid upon foreign importations'); the Gazette of the United States and the Patowmac Guardian report what it contains ('A letter from Paris, of March 10, ... contains the following information'), counted with it (C-02). A correspondent's report of a decree.",
      role='report', words=55, dateline=True,
      head=r'(?:Important\s+and\s+authentick?\s+F\s?RENCH\s+(?:I\s?NTELLIGENCE|N\s?EWS)\.?\s*[—\-]*\s*)?Extra(?:ct)?\s+of\s+a\s+letter\s+from\s+Paris,?\s+March\s+10\.?\s*[\"“]?\s*',
      core=[r'(?:O\s?UR|Our)\s+Assembly\s+has\s+at\s+last\s+decreed\s+the\s+duties', r'A\s+letter\s+from\s+Paris,?\s+of\s+March\s+10'],
      first="A letter from Paris reports that the National Assembly prohibits the importation of oil from any country but the United States.",
      what="the letter from Paris on the importation of oil",
      printings=[k('GUS', '06-04', 3), k('NHG', '06-16', 2), k('NHGR', '06-17', 2), k('PG', '06-20', 3)]),
 dict(id='general-scotts-account-of-the-expedition-against-the-wabash-towns-june-1791', kind='document_group',
      label="General Scott's account of the expedition against the towns on the Wabash, May and June 1791: his letter to the Secretary of War, and the Lexington 'detail of facts'",
      definition="Printings of Brigadier General Charles Scott's account of the expedition against the towns on the Wabash in May and June 1791, in two forms counted together (C-02): his letter to the Secretary for the Department of War, dated Lexington, 20 June 1791 ('In prosecution of the enterprise, I marched four miles from the banks of the Ohio on the 23d of May, and on the 24th I resumed my march, and pushed forward with the utmost industry'), and the Lexington paper's 'detail of Facts, relative to the operations of the Expedition under Brig. Gen. Scott, against the Savages of the Wabash' of 25 June, which gives the same account in the third person ('The Army marched four miles from the bank of the Ohio on the 23d of last month'). The commander's own account, and a Lexington paper's version of it.",
      role='published_document', words=85, dateline=True,
      head=(r'(?:G\s?ENERAL\s+S\s?COTT\.?\s*)?Extra(?:ct)?\s+of\s+a\s+[Ll]etter\s+from\s+Brigadier[\s\-]+General\s+C\s?HARLES\s+S\s?COTT,?\s+to\s+the\s+Secretary\s+for\s+the\s+Department\s+of\s+War,?\s+'
            r'dated\s+Lexington,?\s+the\s+20th\s+of\s+June,?\s*1791[.,]?\s*[—\-]*\s*received\s+by\s+Lieut(?:enant|\.)?\s+Belli,?\s+who\s+arrived\s+in\s+town\s+(?:on\s+Tuesday\s+last|yesterday\s+afternoon),?\s+from\s+the\s+Western\s+Country\.?\s*'),
      core=[r'I\s?N\s+prosecution\s+of\s+the\s+enterprise', r'W\s?E\s+are\s+authori[sz]ed\s+to\s+give\s+(?:to\s+)?the\s+[Pp]ublic'],
      first="Lexington, 25 June 1791: a 'detail of Facts' on the operations of General Scott's expedition against the towns on the Wabash.",
      what="General Scott's account of his expedition",
      printings=[(k('KG', '06-25', 2, 2), {'words': 60, 'head': r'L\s?EXINGTON,?\s+June\s+25\.?\s*', 'note': "The Lexington 'detail of Facts' of 25 June, which gives General Scott's account in the third person; counted with his letter (C-02)."}),
                 k('GUS', '07-30', 1),
                 (k('PG', '08-01', 3), {'words': 60, 'note': "The Lexington 'detail of facts', from the Kentucky Gazette; counted with General Scott's letter (C-02)."}),
                 k('NHGR', '08-12', 1)]),
 # ---- July to September: the English papers, the treaty at Newtown Point, the plague in Turkey, the flight of the King, Birmingham,
 # General Wilkinson ----
 dict(id='the-english-papers-on-the-battle-near-carpentras-july-1791', kind='message_group',
      label="'The English papers give an account of the first pitched battle to which the French revolution has given rise': a battle near Carpentras",
      definition="Printings of a paragraph of July 1791: 'The English papers give an account of the first pitched battle to which the French revolution has given rise; it was fought near Carpentras, between 10,000 patriots and about 7000 counter-revolutionists. The latter were completely routed, and Carpentras, in which was a garrison of 4000 men invested by the patriotic troops. On the 21st of April a capitulation was proposed by the besieged.' A report at second hand from the English papers.",
      role='report', words=50, dateline=True,
      core=[r'(?:T\s?HE\s+)?English\s+papers\s+(?:also\s+)?give\s+an\s+account\s+of\s+the\s+first\s+pitched\s+battle'],
      first="The English papers report a battle near Carpentras between 10,000 patriots and about 7,000 counter-revolutionists.",
      what="the paragraph on the battle near Carpentras",
      printings=[k('GUS', '07-16', 3), k('PG', '07-25', 2), k('NHG', '07-28', 2), k('NHGR', '08-05', 3),
                 (k('KG', '10-15', 3, 2), {'head': r'P\s?HILADELPHIA,?\s+July\s+16\.?\s*', 'dateline': False, 'words': 55})]),
 dict(id='a-correspondent-on-the-treaty-held-by-timothy-pickering-with-the-six-nations-july-1791', kind='message_group',
      label="'A correspondent informs, that the treaty, lately held under commission from the President of the United States, by Timothy Pickering': the treaty with the Six Nations at Newtown Point, July 1791",
      definition="Printings of a paragraph of 30 July 1791: 'A correspondent informs, that the treaty, lately held under commission from the President of the United States, by Timothy Pickering, Esq. of Wilkesbarre, with those Indian tribes commonly called the Six Nations, at Newtown-Point, on the north-west branch of the Susquehanna, in the state of New-York, was concluded on the 18th inst. to the satisfaction of all parties, by a recapitulatory speech from the Commissioner. The principal object of this treaty was, to confirm the peace that has subsisted between us, ever since the treaty of Fort Stanwix, in 1784, and prevent the Five Nations from joining the Western Indians, now at war.' A correspondent's account.",
      role='report', words=60, dateline=True,
      core=[r'A\s+correspondent\s+informs,?\s+(?:us,?\s+)?that\s+the\s+[Tt]reaty'],
      first="A correspondent reports that the treaty held by Timothy Pickering with the Six Nations at Newtown Point was concluded on 18 July 'to the satisfaction of all parties'.",
      what="the correspondent's account of the treaty at Newtown Point",
      printings=[k('GUS', '07-30', 3), k('PG', '08-08', 2), k('NHG', '08-11', 2), k('NHGR', '08-12', 2)]),
 dict(id='london-the-plague-rages-in-turkey-june-1791', kind='message_group',
      label="London, 3 June 1791: 'Accounts were received yesterday at the Secretary of State's office, by way of France, that the plague rages with dreadful havoc in that part of Turkey nearest to the Mediterranean'",
      definition="Printings of a London paragraph of 3 June 1791: 'Accounts were received yesterday at the Secretary of State's office, by way of France, that the plague rages with dreadful havoc in that part of Turkey nearest to the Mediterranean, inasmuch, that in a small district a thousand persons have died in a day.' The New-Hampshire Gazette prints it twice (C-08). A London report of accounts received by way of France.",
      role='report', words=40, dateline=True,
      core=[r'A\s?CCOUNTS\s+were\s+received,?\s+yesterday,?\s+at\s+the\s+Secretary\s+of\s+State'],
      first="London: accounts received by way of France say that the plague rages in the part of Turkey nearest the Mediterranean, a thousand dying in a day in a small district.",
      what="the London paragraph on the plague in Turkey",
      printings=[k('NHG', '08-04', 2), k('NHGR', '08-05', 3), k('GUS', '08-10', 2), (k('NHG', '08-18', 2), {'note': 'Printed again.'}), k('PG', '08-22', 2)]),
 dict(id='m-drouet-recital-before-the-national-assembly-on-stopping-the-king-june-1791', kind='document_group',
      label="M. Drouet's recital before the National Assembly of France: 'I am the Postmaster of Sainte Menehould', on how the King was stopped in June 1791",
      definition="Printings of the recital that M. Drouet, one of the two citizens who stopped the King, gave before the National Assembly: 'I am the Postmaster of Sainte Menehould, formerly a dragoon in the regiment of Conde. My comrade, William, was formerly a dragoon of the Queen's regiment. On the 21st of June, at half past seven o'clock in the evening, two carriages and eleven horses baited at my house—I thought I recognized the Queen; and perceiving a man at the back part of the carriage, on the left, I was struck with the resemblance of his countenance to the King's effigy on an assignat of 50 livres.' M. Drouet's own account, as the papers print it.",
      role='published_document', words=55, dateline=False,
      head=r'M\s?R\.?\s+P\s?RESIDENT,?\s*[\"“]?\s*',
      core=[r'I\s+am\s+the\s+Post[\s\-]*master\s+of\s+Saint'],
      first="M. Drouet, postmaster of Sainte Menehould, gives the National Assembly his account of how the King was recognized and stopped.",
      what="M. Drouet's recital",
      printings=[k('GUS', '08-31', 1), k('NHG', '09-01', 1), k('NHGR', '09-02', 3), k('KG', '11-05', 2, 2)]),
 dict(id='the-insurgents-of-birmingham-had-made-a-gridiron-july-1791', kind='message_group',
      label="'The Insurgents of Birmingham had made a gridiron of immense size': a paragraph of the English news on the riots at Birmingham, July 1791",
      definition="Printings of a paragraph of the English news of July 1791: 'The Insurgents of Birmingham had made a gridiron of immense size, which they brought to Dr. Priestley's house, where they said they meant to broil an Anti-constitutional Philosopher by the blaze of his own writings, and light the fire with the Rights of Man.' The Gazette of the United States and the Patowmac Guardian print it among the London reports of the riots, the New-Hampshire Gazette at the end of an account of the riot. An English paper's report.",
      role='report', words=45, dateline=False, stop=r'(?<=\b[Mm][Aa][Nn]\.)|(?<=\b[Mm][Aa][Nn]\b)(?!\.)',   # the paragraph ends with 'Rights of Man'
      core=[r'(?:T\s?HE\s+)?[Ii]nsurgents\s+of\s+Birmingham\s+had\s+made\s+a\s+grid[\s\-]*iron'],
      first="An English report says that the insurgents of Birmingham brought 'a gridiron of immense size' to Dr. Priestley's house.",
      what="the paragraph on the Birmingham gridiron",
      printings=[k('GUS', '09-17', 1), k('NHG', '09-22', 3), k('PG', '09-26', 2), k('NHGR', '09-30', 3)]),
 dict(id='danville-letter-an-express-from-general-wilkinson-august-1791', kind='message_group',
      label="Danville, Kentucky, 22 August 1791: an extract of a letter, 'An express from Gen. Wilkinson has this moment reached this place, informing of his success'",
      definition="Printings of an extract of a letter from Danville, Kentucky, dated 22 August 1791, sent by way of Richmond: 'An express from Gen. Wilkinson has this moment reached this place, informing of his success. He has destroyed a large Indian town situated on the Wabash; also a Kickapoo town, containing about 30 houses, and killed and taken 42 of the enemy. His loss, 2 men killed and one wounded.' A letter writer's report of General Wilkinson's express.",
      role='report', words=50, dateline=True,
      head=r'Extract\s+of\s+a\s+letter\s+from\s+Danville,?\s+(?:in\s+)?Kentucky,?\s+(?:via\s+Richmond,?\s+)?(?:dated\s+)?Aug(?:ust|\.)?\s+22\.?\s*[\"“]?\s*',
      core=[r'A\s?N\s+express\s+from\s+Gen(?:eral|\.)?\s+Wilkinson'],
      first="A letter from Danville reports an express from General Wilkinson: a large town on the Wabash and a Kickapoo town destroyed.",
      what="the Danville letter on General Wilkinson's express",
      printings=[k('GUS', '09-17', 3), k('PG', '09-26', 3), k('NHG', '09-29', 2), k('NHGR', '10-07', 1)]),
 # ---- October to December: Saint-Domingue, the opening of Congress, the King of France's acceptance, General St. Clair's defeat ----
 dict(id='by-the-schooner-hardy-from-cape-francois-the-insurrection-october-1791', kind='message_group',
      label="By the schooner Hardy from Cape-Francois, October 1791: intelligence of the insurrection in Saint-Domingue",
      definition="Printings of a paragraph of early October 1791, in a Philadelphia form ('arrived here on Saturday last') and a New York form of 5 October ('arrived at Philadelphia on Saturday morning'): 'By the Schooner Hardy, Capt. Green, which sailed from Cape-Francois the 12th ult. and arrived here on Saturday last, we have received intelligence, that the mulattoes and free blacks have got fire-arms, &c. out of the King's store at the Cape, and done more execution against the black insurgents than the white inhabitants had been able to effect: above 3000 of the insurgents have been killed.' A report of the intelligence a ship brought.",
      role='report', words=65, dateline=False,
      head=r'(?:Further\s+particulars\s+of\s+the\s+[Ii]nsurrection\s+in\s+the\s+West[\s\-]*Indies\s*\.?\s*)?N\s?EW[\s\-]*Y\s?ORK,?\s+Oct(?:ober|\.)?\s+5\.?\s*',
      core=[r'B\s?Y\s+the\s+Schooner\s+Hardy'],
      first="Intelligence by the schooner Hardy from Cape-Francois on the insurrection in Saint-Domingue.",
      what="the report by the schooner Hardy",
      printings=[k('GUS', '10-05', 3), k('NHG', '10-13', 3), k('NHGR', '10-14', 3), k('PG', '10-17', 2), k('KG', '11-26', 3, 2)]),
 dict(id='london-prince-john-the-african-prince-arrives-from-sierra-leone-september-1791', kind='message_group',
      label="London, September 1791: 'Prince John, the African Prince, is arrived here from Sierra Leona. His business to this country appears chiefly to be respecting the Slave Trade'",
      definition="Printings of a London paragraph of 19 September 1791: 'Prince John, the African Prince, is arrived here from Sierra Leona. His business to this country appears chiefly to be respecting the Slave Trade. He has met with a very cordial reception in this city, and particularly among the gentlemen who wish for the abolition of the Slave Trade.' The paragraph goes on to his visits and his conversation. A London paper's report.",
      role='report', words=50, dateline=True, stop=r'\sYesterday,?\s+accompanied|\sN\s?ATIONAL\s+A\s?SSEMBLY',
      core=[r'Prince\s+John,?\s+the\s+African\s+Prince'],
      first="London: Prince John, an African prince, arrives from Sierra Leone, his business 'chiefly to be respecting the Slave Trade'.",
      what="the London paragraph on Prince John",
      printings=[k('GUS', '10-03', 1), k('NG', '12-05', 1), k('NHG', '12-14', 2), k('PG', '12-20', 1)]),
 dict(id='the-presidents-speech-and-the-answers-of-the-two-houses-october-1791', kind='context_group',
      label="The opening of the session of Congress, October 1791: the President's speech and the answers of the two Houses",
      children=['presidents-speech-to-both-houses-25-october-1791', 'answer-of-the-house-of-representatives-october-1791', 'address-of-the-senate-to-the-president-october-1791'],
      definition="Three public papers of the opening of the first session of the second Congress, as the papers printed them from October to December 1791: the President's speech to both Houses of 25 October, the answer of the House of Representatives, which the Speaker delivered to the President at his house on 28 October, and the address of the Senate, which the Vice-President and the Senate presented on 31 October. Contains those three groups."),
 dict(id='presidents-speech-to-both-houses-25-october-1791', parent='the-presidents-speech-and-the-answers-of-the-two-houses-october-1791', kind='document_group',
      label="The President's speech to both Houses of Congress, 25 October 1791: 'I meet you, upon the present occasion, with the feelings which are naturally inspired by a strong impression of the prosperous situation of our common country'",
      definition="Printings of the President's speech to the Senate and the House of Representatives at the opening of the session, 25 October 1791: 'Fellow Citizens of the Senate, and of the House of Representatives, I meet you, upon the present occasion, with the feelings which are naturally inspired by a strong impression of the prosperous situation of our common country, and by a persuasion equally strong that the labors of the session, which has just commenced, will, under the guidance of a spirit no less prudent than patriotic, issue in measures, conducive to the stability and increase of national prosperity.' The President's own speech.",
      role='published_document', words=60, dateline=False,
      head=(r'(?:S\s?\s?P\s?\s?E\s?\s?E\s?\s?C\s?\s?H\s+OF\s+THE\s+P\s?RESIDENT\s+OF\s+THE\s+U\s?NITED\s+S\s?TATES,?\s+TO\s+BOTH\s+H\s?OUSES\s+OF\s+C\s?ONGRESS\.?\s*)?'
            r'F\s?ELLOW[\s\-]*C\s?ITIZENS\s+OF\s+THE\s+S\s?ENATE,?\s+(?:AND\s+OF\s+THE|AND)\s+H\s?OUSE\s+OF\s+R\s?EPRESENTATIVES[,.]?\s*'),
      core=[r'I\s+MEET\s+you,?\s+upon\s+the\s+present\s+occasion'],
      first="The President opens the session with a speech on 'the prosperous situation of our common country'.",
      what="the President's speech of 25 October",
      printings=[k('GUS', '10-26', 3), k('NG', '10-31', 1), k('PG', '11-07', 2), k('NHG', '11-10', 1), k('NHGR', '11-12', 2)]),
 dict(id='answer-of-the-house-of-representatives-october-1791', parent='the-presidents-speech-and-the-answers-of-the-two-houses-october-1791', kind='document_group',
      label="The answer of the House of Representatives to the President's speech, October 1791: 'In receiving your address at the opening of the present session, the House of Representatives have taken an ample share in the feelings inspired by the actual prosperity, and flattering prospects of our country'",
      definition="Printings of the address of the House of Representatives in answer to the President's speech, which the Speaker delivered to the President at his house on 28 October 1791: 'In receiving your address at the opening of the present session, the House of Representatives have taken an ample share in the feelings inspired by the actual prosperity, and flattering prospects of our country: And whilst, with becoming gratitude to heaven, we ascribe this happiness to the true source from which it flows, we behold with an animating pleasure'. The House's own address.",
      role='published_document', words=60, dateline=False,
      head=r'(?:A\s?NSWER\s+OF\s+THE\s+H\s?OUSE\s+OF\s+R\s?EPRESENTATIVES[,.]?\s*)?(?:To\s+G\s?EORGE\s+W\s?ASHINGTON,?\s+President\s+of\s+the\s+United\s+States\.?\s*)?(?:S\s?\s?I\s?\s?R[.,]?\s*)?',
      core=[r'I\s?N\s+receiving\s+your\s+address\s+at\s+the\s+opening\s+of\s+the'],
      first="The House of Representatives answers the President's speech.",
      what="the House's answer",
      printings=[k('GUS', '10-29', 3), k('NG', '10-31', 2), k('PG', '11-14', 1), k('NHG', '11-16', 1), k('NHGR', '12-03', 4)]),
 dict(id='address-of-the-senate-to-the-president-october-1791', parent='the-presidents-speech-and-the-answers-of-the-two-houses-october-1791', kind='document_group',
      label="The address of the Senate to the President in answer to his speech, October 1791: 'The Senate of the United States have received with the highest satisfaction, the assurances of public prosperity contained in your speech'",
      definition="Printings of the Senate's address in answer to the President's speech, which the Vice-President and the Senate presented to the President on 31 October 1791: 'The Senate of the United States have received with the highest satisfaction, the assurances of public prosperity contained in your speech to both houses: the multiplied blessings of Providence have not escaped our notice, or failed to excite our gratitude.' The Senate's own address.",
      role='published_document', words=60, dateline=False,
      head=r'(?:The\s+S\s?ENATE.?s\s+A\s?nswer\.?\s*)?(?:To\s+the\s+P\s?RESIDENT\s+of\s+the\s+U\s?NITED\s+S\s?TATES\.?\s*)?(?:S\s?\s?I\s?\s?R[.,]?\s*)?',
      core=[r'T\s?HE\s+Senate\s+of\s+the\s+United\s+States\s+have\s+received\s+with'],
      first="The Senate answers the President's speech.",
      what="the Senate's address",
      printings=[k('GUS', '11-02', 2), k('NG', '11-03', 3), k('NHG', '11-16', 2), k('NHGR', '12-03', 4)]),
 dict(id='letter-of-the-king-of-france-to-the-national-assembly-accepting-the-constitution-september-1791', kind='document_group',
      label="The King of France's letter to the National Assembly accepting the constitution, September 1791: 'I have attentively examined the Constitutional Act which you have presented to me. I do accept it'",
      definition="Printings of the letter of the King of France to the National Assembly accepting the constitution, from the Paris papers of September 1791, in three translations counted as one item (C-02): 'Gentlemen, I have attentively examined the Constitutional Act which you have presented to me. I do accept it, and will cause it to be executed. This simple declaration might at another time have been sufficient: but now I am bound to make my motives known; it is a duty which I owe to the Nation and to myself' (the National Gazette, from a Paris paper of 14 September, and the Patowmac Guardian and the Kentucky Gazette); 'I have attentively examined the Constitutional Act, which you have presented for my acceptance. I accept it, and I shall cause it to be executed' (the New-Hampshire Gazette and the New Hampshire Gazetteer); 'I have examined with attention the Constitution which you presented me for acceptance. I accept it, and shall see it executed' (the Gazette of the United States). The King's own letter, in translation.",
      role='published_document', words=55, dateline=False,
      head=r'(?:(?:Copy\s+of\s+a\s+)?Letter\s+from\s+the\s+K\s?ING(?:\s+of\s+F\s?RANCE)?\s+to\s+the\s+(?:National\s+)?A\s?SSEMBLY(?:,?\s+accepting\s+the\s+Constitution)?[.,]?\s*)?[\"“]?\s*G\s?ENTLEMEN[.,]?\s*[\"“]?\s*',
      core=[r'I\s+H\s?AVE\s+(?:attentively\s+examined|examined\s+with\s+attention)\s+the\s+[Cc]onstitution'],
      first="The King of France writes to the National Assembly that he accepts the constitution.",
      what="the King of France's letter accepting the constitution",
      printings=[k('NG', '11-17', 3), k('NHG', '11-23', 2),
                 (k('GUS', '11-26', 1), {'note': "Another translation ('I have examined with attention the Constitution which you presented me for acceptance'), counted with the others (C-02)."}),
                 k('NHGR', '12-03', 1), k('PG', '12-06', 1), k('KG', '12-17', 3, 2)]),
 dict(id='general-st-clairs-defeat-november-1791', kind='context_group',
      label="The defeat of the army under General St. Clair, November 1791: General Scott's circular from Lexington and General St. Clair's report, as the papers printed them",
      children=['general-scotts-circular-letter-to-the-county-lieutenants-november-1791', 'general-st-clairs-letter-to-the-secretary-of-war-9-november-1791'],
      definition="Two public papers on the defeat of the army under General St. Clair, as the papers printed them in November and December 1791: Brigadier General Scott's circular letter to the county lieutenants of Kentucky, dated Lexington, 11 November, and General St. Clair's letter to the Secretary of War, dated Fort Washington, 9 November, which the President sent to Congress in December. Contains those two groups."),
 dict(id='general-scotts-circular-letter-to-the-county-lieutenants-november-1791', parent='general-st-clairs-defeat-november-1791', kind='document_group',
      label="Lexington, 11 November 1791: General Scott's circular letter to the county lieutenants of Kentucky, 'We have now received certain intelligence that the army have been defeated'",
      definition="Printings of a circular letter of Brigadier General Scott to the county lieutenants in Kentucky, dated Lexington, 11 November 1791, first printed in the Kentucky Gazette: 'We have now received certain intelligence that the army have been defeated. The loss is very great. The Garrison at Fort Jefferson is intercepted and many, many have been wounded; gallant men are now left on the road, unable to travel, and without any provision but the flesh of the pack horses. This case requires immediate exertions.' He appoints a rendezvous for the 15th. The general's own circular.",
      role='published_document', words=55, dateline=False,
      head=(r'(?:Copy\s+of\s+a\s+[Cc]ircular\s+[Ll]etter\s+from\s+B\s?rig(?:adier|\.)?[\s\-]*G\s?en(?:eral|\.)?\s+S\s?COTT,?\s+to\s+the\s+different\s+[Cc]ounty[\s\-]*L\s?ieutenants,?\s+in\s+Kentucky\.?\s*)?'
            r'[\"“]?\s*(?:S\s?I\s?R[.,]\s*[\"“]?\s*)?(?:L\s?EXINGTON,?\s+Nov(?:ember|\.)?\s+11(?:th)?,?\s*1791\.?\s*[\"“]?\s*)?(?:S\s?I\s?R[.,]\s*[\"“]?\s*)?'),
      core=[r'W\s?E\s+have\s+now\s+received\s+certain\s+intelligence'],
      first="General Scott writes to the county lieutenants of Kentucky that 'the army have been defeated'.",
      what="General Scott's circular letter",
      printings=[k('KG', '11-12', 3, 2), k('PG', '12-06', 3), k('GUS', '12-10', 3), k('NG', '12-12', 3), k('NHGR', '12-24', 3)]),
 dict(id='general-st-clairs-letter-to-the-secretary-of-war-9-november-1791', parent='general-st-clairs-defeat-november-1791', kind='document_group',
      label="Fort Washington, 9 November 1791: General St. Clair's letter to the Secretary of War, 'Yesterday afternoon the remains of the army under my command got back to this place'",
      definition="Printings of the letter of Major General St. Clair to the Secretary of War, dated Fort Washington, 9 November 1791, which the President sent to Congress with a message in December: 'Yesterday afternoon the remains of the army under my command got back to this place, and I have now the painful task to give you an account of as warm and unfortunate an action as almost any that has been fought, in which every corps was engaged and worsted, except the first regiment—that had been detached upon a service I had the honor to inform you of in my last dispatch, and had not joined me.' The commander's own report.",
      role='published_document', words=60, dateline=False,
      head=(r'(?:(?:Copy\s+of\s+a\s+letter\s+from\s+Major[\s\-]*General\s+St\.?\s*Clair,?\s+to\s+the\s+Secretary\s+for\s+the\s+Department\s+of\s+War|General\s+St\.?\s*Clair.?s\s+Letter,?\s+to\s+Major[\s\-]*General\s+Knox,?\s+Secretary\s+of\s+War)\.?\s*)?'
            r'(?:Fort[\s\-]*Washington,?\s+Nov(?:ember|\.)?\s+9,?\s*1791\.?\s*)?(?:S\s?\s?I\s?\s?R[.,]?\s*)?'),
      core=[r'Y\s?ESTERDAY\s+afternoon\s+the\s+remains\s+of\s+the\s+army'],
      first="General St. Clair reports to the Secretary of War 'as warm and unfortunate an action as almost any that has been fought'.",
      what="General St. Clair's letter of 9 November",
      printings=[k('GUS', '12-14', 2), k('NG', '12-15', 2), k('NHG', '12-21', 2), k('PG', '12-27', 2), k('NHGR', '12-31', 2)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797 and 1800): "BOSTON, Nov. 30th, 1802."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}[\s\-]+){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:(?:\s|\s?-\s?)[A-Z][A-Za-z'\-]+){0,2})(?:,?\s*[\(\[][A-Za-z ,.]+[\)\]])?"
# As for 1774 (24 November): also a year after a stop ('Oct. 16. 1774.') and a date printed alone ('December 5.').
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”’)]\s+)((?:" + PLACE + r",?\s+)?" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:[,.]?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False, head=None):
    for core in cores:
        m = re.search(core, text, re.I | re.S)
        if m:
            start = m.start()
            if head:   # a heading that ends directly before the core: the excerpt starts with it
                window = text[max(0, start-420):start]
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


# Openings compared side by side on 24 November 2026 (the 1780 review's cross-year check): where one printing of a group
# carried the heading printed above the item and another did not, the heading patterns above were widened, and the printings
# below take their own start. KEEP_WORDS keeps the end of every excerpt whose start moved where the scan check read it: it is
# the number of words from the new start to the old end.
OPENING_FIXES = {
}
KEEP_WORDS = {
}


def printings():
    for s in STORIES:
        for p in s.get('printings', []):
            key, over = (p, {}) if isinstance(p, str) else p
            over = dict(over, **OPENING_FIXES.get((s['id'], key), {}))
            if (s['id'], key) in KEEP_WORDS:
                over['words'] = KEEP_WORDS[(s['id'], key)]
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
            problems.append((s['id'], key, 'page not in the 1791 pages'))
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
        r['id'] = f'S91-{n:03}'
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
               'admission_rule': 'Reviewed 1791 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1791/'
    return {
        'ledger_id': 'ledger:stories-1791', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1791', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1791, and of 1790 where they reach the 1791 pages (long-running ones '
                   'included), every item in 3 or more papers compared by machine with every page and counted again by its opening, a sweep of '
                   'word-for-word passages shared by 4 or more papers for short items the families miss, phrase searches on all 1,242 pages of '
                   '1791 in both transcriptions, reading of every hit, and scan checks of each admitted passage, by the thin-year rule (Y-THIN, '
                   'as amended on 23 November 2026: an item printed by more than half of the papers that survive for its weeks, and by at '
                   'least 4, is eligible; the items printed by every paper that survives for their weeks are admitted, and the other eligible '
                   'items are chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1790.json': 'retrieval_candidates', d+'count_1791.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1791.py': 'ledger_code', 'work/archive_data/ledgers/stories_1791_review.json': 'scan_review',
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
