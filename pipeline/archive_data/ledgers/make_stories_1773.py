"""Write ledgers/stories_1773.json: reviewed stories of 1773, round one.

1773 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN, as amended on 23 November 2026, the owner's
choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the newspapers that
survive for its weeks (those with a surviving issue between its first and last printing, and at least in the three weeks
from its first printing), and by at least 4; items printed by every newspaper that survives for their weeks are admitted;
the other eligible items are chosen to cover the months and the kinds of news; digests are not admitted. 1773 has six
papers: the Massachusetts Spy, the New-Hampshire Gazette and both Virginia Gazettes almost all year, Dunlap's Pennsylvania
Packet from 25 October and one issue of the Connecticut Courant (28 December); four papers survive in most weeks, so an
item is admitted when all four print it, and from October an item printed by four of five or six is eligible. Single
paragraphs from runs of news are counted by their own words (C-09).
The automatic families first printed in 1773 that reach 3 or more papers, and those of 1772 over the 1773 pages,
long-running ones included, were split into single printed items with work/story_items.py --long-running (items.json,
items_from_1772.json); every item in 3 or more papers was counted again by the first 40 words of its opening against
every page of the year (papers the comparison missed were looked for again, by their words and by their names, and read),
and a sweep of word-for-word passages shared by 4 or more papers (as for 1803, X-1803-09) found items the families miss;
the sweep's passages that no counted item explains were read one by one. Every item read at the bar, or one paper short
of it, was counted by its own words with phrase searches over all 846 pages of 1773 in both transcriptions
(work/story_phrase_search.py's patterns). See outputs/story_discovery_1773/README.md.

The 1773 pages are those whose issue the data release dates to 1773 (work/year_search_pages.py 1773 ... --printed-dates).
1773 has 6 catalogue series, which are 6 papers: the Massachusetts Spy, or Thomas's Boston Journal (sn83021194), the
New-Hampshire Gazette (Portsmouth), two Virginia Gazettes of Williamsburg with different printers (Purdie and Dixon,
sn84024739; Rind, sn84024741), Dunlap's Pennsylvania Packet (Philadelphia, sn83021126) and the Connecticut Courant
(Hartford, sn82016376).

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 25-70 words), starting with its dateline or heading when one
stands directly before it (a place and date, a bare date such as 'Nov. 10.', a letter-spaced or bracketed place name). A
paragraph printed in a run of news is counted, and its excerpt cut, by its own opening sentence. Scan findings, crops and
hand-drawn boxes are merged from stories_1773_review.json after the scan check. A printing on a page whose RevX
transcription is filed under another scan page (derived/revx_page_map.parquet), or empty, takes its excerpt from the CA
transcription of its scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied; other years are reviewed at the same time, and the main
session renumbers at release:
    python work/archive_data/ledgers/make_stories_1773.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1773/search_pages.json). The excerpts are cut from
the 1773 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1773'
D = PROJECT/'outputs/story_discovery_1773'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1773_review.json'
OUT = HERE/'stories_1773.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83025582': 'The New-Hampshire Gazette', 'sn84024739': 'The Virginia Gazette (Purdie and Dixon)',
         'sn84024741': 'The Virginia Gazette (Rind)', 'sn83021194': 'The Massachusetts Spy',
         'sn83021126': "Dunlap's Pennsylvania Packet", 'sn82016376': 'The Connecticut Courant'}
ONE = {'MS': 'sn83021194', 'NHG': 'sn83025582', 'VG1': 'sn84024739', 'VG2': 'sn84024741', 'PP': 'sn83021126', 'CC': 'sn82016376'}
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
    """Page key of a printing: paper code, date (MM-DD in 1773), page and edition."""
    return f'{ONE[paper]}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()


def S(id, label, definition, core, first, what, printings, role='report', words=40, dateline=True, **kw):
    """One story group (a message_group), written compactly."""
    return dict(id=id, kind='message_group', label=label, definition=definition, role=role, words=words, dateline=dateline,
                core=core, first=first, what=what, printings=printings, **kw)


CA_NOTE = 'RevX has no transcription of this item on this page, so the excerpt comes from the older CA transcription.'

# Story groups. 'printings' lists each printing's page; a tuple adds overrides for that printing: core (regexes for the
# item's first words), role, field, note, words, dateline (include a dateline directly before), back (start at the
# beginning of the sentence that holds the core), stop (a regex: the excerpt ends before it).
STORIES = [
 # ---- admitted: printed by every paper that survives for their weeks ----
 S('boston-custom-house-notice-on-registers-december-1772',
   "Custom-House, Boston, 15 December 1772: 'WHEREAS there has been great neglect on the part of the owners of sundry vessels in the plantations in not complying with the act of the 7th and 8th William 3d. C. 22'",
   ("Printings of a notice of the Custom-House at Boston dated 15 December 1772: 'WHEREAS there has been great neglect on the part of the "
    "owners of sundry vessels in the plantations in not complying with the act of the 7th and 8th William 3d. C. 22, and more particularly "
    "the 21st sect. ...' (on the registers of vessels). An official notice, printed among the advertisements and repeated in three issues "
    "of each paper."),
   [r'Cust\w*.?House,?\W+Boston,?\W+(?:15th\W+Decem|December\W+15)', r'WHEREAS\W+there\W+has\W+been\W+great\W+neglect'],
   "Boston, December 1772: a notice of the Custom-House on the registers of vessels.", "the Custom-House notice on registers",
   [k('MS', '01-07', 1), (k('NHG', '01-08', 1), {'core': [r'WHEREAS\W+there\W+has\W+been\W+great\W+neglect']}), k('MS', '01-14', 4), (k('NHG', '01-15', 4), {'core': [r'WHEREAS\W+there\W+has\W+been\W+great\W+neglect']}),
    k('MS', '01-21', 4), (k('NHG', '01-22', 4), {'core': [r'WHEREAS\W+there\W+has\W+been\W+great\W+neglect']}),
    k('VG1', '02-25', 3), k('VG2', '02-25', 3), k('VG1', '03-04', 3), k('VG2', '03-04', 4),
    (k('VG1', '03-11', 4), {'field': CA, 'core': [r"c.Us.rOMHousn"], 'note': ('The RevX transcriptions of this issue are filed one page off '
     '(this page has none), so the excerpt comes from the older CA transcription of this scan page.')}),
    k('VG2', '03-11', 4)],
   role='published_document', dateline=False),
 S('london-report-a-frigate-fired-upon-at-carthagena-1772',
   "London, November 1772: 'It is reported that a frigate is arrived at Portsmouth, express from the Mediterranean, with an account that one of his Majesty's ships, attempting to go into the harbour of Carthagena, was fired upon from the fort'",
   ("Printings of a London paragraph of 9 and 10 November 1772: 'It is reported that a frigate is arrived at Portsmouth, express from the "
    "Mediterranean, with an account that one of his Majesty's ships, attempting to go into the harbour of Carthagena, was fired upon from "
    "the fort ...'. A London report of what 'is reported', as the papers reprinted it."),
   [r'It\W+is\W+reported\W+that\W+a\W+frigate\W+is\W+arrived\W+at\W+Portsmouth'],
   "London, November 1772: a report that a British ship was fired upon at Carthagena.", "the London report of a ship fired upon at Carthagena",
   [k('VG1', '01-07', 2), k('VG2', '01-07', 2), k('MS', '02-11', 2), k('NHG', '02-12', 3)], words=38),
 S('chester-letter-on-a-gunpowder-explosion-november-1772',
   "Chester, 10 November 1772: a letter: 'On Thursday night last, the 5th instant, the inhabitants of this city were thrown into the utmost consternation by an instantaneous shock, supposed at first to have been occasioned by the violence of an earthquake'",
   ("Printings of an extract of a letter from Chester of 10 November 1772, under Liverpool and London datelines: 'On Thursday night last, "
    "the 5th instant, the inhabitants of this city were thrown into the utmost consternation by an instantaneous shock, supposed at first "
    "to have been occasioned by the violence of an earthquake ...' (gunpowder deposited in a warehouse in Water-Gate-Street). A letter at "
    "second hand, as the papers reprinted it."),
   [r'Extract\W+of\W+a\W+letter\W+from\W+Chester'],
   "Chester, November 1772: a letter on an explosion of gunpowder in the city.", "the letter from Chester",
   [k('VG1', '01-07', 2), k('VG2', '01-07', 3), k('MS', '02-11', 2), k('NHG', '02-12', 4)], words=42),
 S('london-report-amherst-sworn-of-the-privy-council-1772',
   "London, 7 November 1772: 'Yesterday Sir Jeffery Amherst was sworn in one of his Majesty's most honourable Privy Council'",
   ("Printings of a London paragraph of November 1772 in two wordings: 'Yesterday Sir Jeffery Amherst was sworn in one of his Majesty's "
    "most honourable Privy Council, and took his seat at the board' (the Virginia papers: 'Yesterday, at the Cabinet Council held at St. "
    "James's, Sir Jeffery Amherst was sworn ...'). A London report, as the papers reprinted it."),
   [r'Yesterday,?\W+(?:at\W+the\W+Cabinet\W+Council\W+held\W+at\W+St\.?\W+James.s,?\W+)?Sir\W+Jeff\w+\W+Amherst'],
   "London, November 1772: a report that Sir Jeffery Amherst was sworn of the Privy Council.", "the London report on Sir Jeffery Amherst",
   [k('VG1', '01-07', 2), k('VG2', '01-07', 2), k('MS', '01-14', 3), k('NHG', '01-15', 3)], words=20),
 S('new-york-report-the-ministry-to-repeal-the-tea-duty-january-1773',
   "New York, 4 January 1773: 'Several letters from London by the Packet, say, \"that the ministry are determined to use their influence in parliament for a repeal of the act imposing a duty on all teas exported to the colonies from Great-Britain\"'",
   ("Printings of a New York paragraph of 4 January 1773: 'Several letters from London by the Packet, say, \"that the ministry are "
    "determined to use their influence in parliament for a repeal of the act imposing a duty on all teas exported to the colonies from "
    "Great-Britain.\"' A New York report of what letters say, as the papers reprinted it."),
   [r'Several\W+letters\W+from\W+London'],
   "New York, January 1773: a report that letters say the ministry will seek the repeal of the tea duty.", "the New York report on the tea duty",
   [k('MS', '01-14', 1), k('NHG', '01-15', 3), k('VG1', '01-28', 2), k('VG2', '01-28', 2)], words=36,
   stop=r'General\W+Monckton|Extract\W+of\W+a\W+letter'),
 S('letter-from-a-gentleman-on-fortifying-the-town-1773',
   "A letter 'per the last Packet', January 1773: 'I hear your militia are put on a good footing, and that you are marching and counter-marching: It is well; but I am most desirous you should fortify'",
   ("Printings of an extract of a letter from 'a gentleman of character in London', 'per the last "
    "Packet' ('by the last Packet' in the Virginia papers), printed with New York news of 4 January 1773: 'I hear your militia are put on a good footing, and that you are "
    "marching and counter-marching: It is well; but I am most desirous you should fortify; as sure as you live if you do not, the town will "
    "be burnt about your ears in the next war ...'. A letter at second hand, as the papers reprinted it."),
   [r'Extract\W+of\W+a\W+letter\W+from\W+a\W+gentleman\W+(?:of\W+character\W+)?in\W+(?:London|Boston)'],
   "January 1773: a letter from a gentleman urging the town to fortify.", "the letter on fortifying the town",
   [k('MS', '01-14', 1), k('NHG', '01-15', 3), k('VG1', '01-28', 2), k('VG2', '01-28', 2)], words=40),
 S('london-letter-on-the-orphan-house-in-georgia-1772',
   "London, late 1772: a letter: 'We have the pleasure to inform the public, that the Countess of Huntington has purchased of the heirs of the late Rev. Mr. Whitefield, their rights in the Orphan House in Georgia'",
   ("Printings of an extract of a letter from London, printed with New York news of 4 January 1773: 'We have the pleasure to inform the "
    "public, that the Countess of Huntington has purchased of the heirs of the late Rev. Mr. Whitefield, their rights in the Orphan House in "
    "Georgia, in order more effectually to secure to the British Colonies the advantages of that seminary, and render it a public "
    "blessing ...'. A letter at second hand, as the papers reprinted it; later paragraphs on the Orphan House are other texts."),
   [r'Extract\W+of\W+a\W+letter\W+from\W+London\.?\W+.?\W*We\W+have\W+the\W+pleasure'],
   "London, late 1772: a letter on the Countess of Huntingdon and the Orphan House in Georgia.", "the London letter on the Orphan House in Georgia",
   [k('NHG', '01-15', 3), k('MS', '01-21', 1), k('VG1', '01-28', 2), k('VG2', '01-28', 2)], words=42),
 S('king-speech-opening-parliament-26-november-1772',
   "Westminster, 26 November 1772: the King's speech opening the session: 'My Lords and Gentlemen, I should most willingly have consulted your private convenience, by allowing you a longer recess from business'",
   ("Printings of the King's speech to both Houses of Parliament at the opening of the session, 26 November 1772: 'My Lords and Gentlemen, "
    "I should most willingly have consulted your private convenience, by allowing you a longer recess from business, if I had not thought, "
    "that some very important parts of the public service required the immediate attention of Parliament ...' (the affairs of the East "
    "India Company, the dearth of corn, the war in the east of Europe). A published speech, as the papers reprinted it; the two Houses' "
    "addresses in reply and paragraphs that quote it are other texts."),
   [r'His\W+Majesty.s\W+most\W+gracious\W+SPEECH\W+to\W+both'],
   "Westminster, November 1772: the King's speech at the opening of the session of Parliament.", "the King's speech of 26 November 1772",
   [k('MS', '02-18', 1), (k('NHG', '02-19', 2), {'core': [r'The\W+KING.S\W+SPEECH']}),
    (k('VG1', '03-04', 2), {'core': [r'His\W+Majesty\W+was\W+attended\W+yesterday\W+to\W+the\W+House\W+of\W+Peers'], 'words': 62}),
    (k('VG2', '03-04', 3), {'core': [r'L\W*O\W*N\W*D\W*O\W*N\W+Nov\.?\W+26\.?\W+His\W+Majesty\W+was\W+attended'], 'dateline': False, 'words': 62})],
   role='published_document', words=45),
 S('london-report-dispatches-for-the-governors-in-america-1772',
   "London, 17 December 1772: 'Dispatches are now preparing in order to be sent off with all speed to the governors in America'",
   ("Printings of a London paragraph of 17 December 1772: 'Dispatches are now preparing in order to be sent off with all speed to the "
    "governors in America.' A London report, as the papers reprinted it."),
   [r'D[ie]s?patches,?\W+are\W+now\W+preparing'],
   "London, December 1772: a report that dispatches were preparing for the governors in America.", "the London report of dispatches for the governors",
   [k('MS', '02-18', 1), k('NHG', '02-19', 2), k('VG1', '03-04', 3), k('VG2', '03-04', 3)], words=18),
 S('london-report-the-recorder-s-charge-to-the-grand-jury-1772',
   "London, December 1772: 'Yesterday Serjeant Glynn sat for the first time as Recorder of London. His charge to the grand jury was exceedingly pathetic, elegant and instructive'",
   ("Printings of a London paragraph of 8 December 1772: 'Yesterday Serjeant Glynn sat for the first time as Recorder of London. His "
    "charge to the grand jury was exceedingly pathetic, elegant and instructive, accompanied with copious eulogiums on the blessings this "
    "country enjoys over all others, in having the freedom of trial by a jury of their peers.' A London report, as the papers reprinted it."),
   [r'Yesterday,?\W+(?:Mr\.?\W+)?Ser\w+\W+\w+\W+sat\W+for\W+the\W+first\W+time\W+as\W+Recorder'],
   "London, December 1772: a report of the new Recorder's charge to the grand jury.", "the London report of the Recorder's charge",
   [k('MS', '02-18', 1), k('NHG', '02-19', 2), k('VG2', '03-18', 1), k('VG1', '03-25', 2)], words=40),
 S('report-captain-henshaw-from-st-vincent-february-1773',
   "New York, 4 February, and Philadelphia, 8 February 1773: 'By Captain Henshaw, from St. Vincents, we are informed that General Leybourne was gone to Grenada, and the command of the troops devolved on Col. Dalrymple, who had entirely surrounded the Indians'",
   ("Printings of a shipmaster's report from St. Vincent in two wordings, a New York paragraph of 4 February 1773 ('Wednesday the 27th ult. "
    "Capt. Henshaw arrived here from St. Vincents ...') and a Philadelphia paragraph of 8 February ('By Captain Henshaw, from St. Vincents, "
    "we are informed ...'): 'General Leybourne was gone to Grenada, and the command of the troops devolved on Col. Dalrymple, who had "
    "entirely surrounded the Indians, and it was imagined the greatest part of them would be made prisoners ...' (the Caribs of St. "
    "Vincent). A shipmaster's report at second hand, as the papers reprinted it."),
   [r'\w+day\W+the\W+\d+\w*\W+ult\.?\W+Capt\w*\.?\W+Henshaw', r'(?:By\W+)?Capt\w*\.?\W+Henshaw'],
   "St. Vincent, early 1773: a shipmaster's report of the troops and the Caribs.", "Captain Henshaw's report from St. Vincent",
   [(k('NHG', '02-19', 3), {'core': [r'N\W*E\W*W\W*-?\W*Y\W*O\W*R\W*K,?\W+Feb\.?\W+4\.?\W+Wednesday'], 'dateline': False}),
    k('MS', '02-25', 3), k('VG1', '02-25', 2), k('VG2', '02-25', 2)], words=40),
 S('virginia-burgesses-resolutions-of-12-march-1773',
   "Williamsburg, 12 March 1773: the House of Burgesses' resolutions: 'Whereas the minds of his Majesty's faithful subjects in this colony have been much disturbed by various rumours and reports of proceedings tending to deprive them of their ancient, legal, and constitutional rights'",
   ("Printings of the resolutions of the Virginia House of Burgesses of 12 March 1773 appointing a standing committee of correspondence and "
    "enquiry: 'Whereas the minds of his Majesty's faithful subjects in this colony have been much disturbed by various rumours and reports "
    "of proceedings tending to deprive them of their ancient, legal, and constitutional rights ...'. A published document, as the papers "
    "printed it; other houses' resolutions answering it are other texts."),
   [r'On\W+Friday\W+the\W+HONOURABLE\W+the\W+HOUSE\W+OF\W+BURGESSES', r'Mr\.?\W+Bland\W+reported\W+from\W+the\W+committee',
    r'In\W+the\W+House\W+of\W+Burge\w*,?\W+in\W+Virginia'],
   "Williamsburg, March 1773: the House of Burgesses' resolutions for a committee of correspondence.", "the Virginia resolutions of 12 March",
   [k('VG1', '03-18', 2), k('VG2', '03-18', 3), k('MS', '04-08', 3), (k('NHG', '04-23', 1), {'field': CA, 'note': CA_NOTE})],
   role='published_document', words=45, dateline=False),
 S('london-report-a-sudden-fog-1773',
   "London, early 1773: 'The most sudden and close fog came on yesterday that ever was known in the memory of man. Considerable mischief has been done by coaches running foul of each other'",
   ("Printings of a London paragraph of early 1773: 'The most sudden and close fog came on yesterday that ever was known in the memory of "
    "man. Considerable mischief has been done by coaches running foul of each other, &c. the drivers not being able to distinguish any "
    "object at a yard distance.' A London report, as the papers reprinted it."),
   [r'The\W+most\W+sudden\W+and\W+close\W+\w+\W+came\W+on'],
   "London, early 1773: a report of a sudden fog.", "the London report of a sudden fog",
   [k('MS', '03-25', 2), k('VG1', '03-25', 2), k('VG2', '03-25', 3), k('NHG', '03-26', 2)], words=35),
 S('london-report-the-hotel-dieu-burnt-at-paris-1773',
   "London, early 1773: 'The Hotel Dieu, (one of the finest hospitals in the world) was burnt down at Paris the beginning of January last, and between seven and eight hundred sick persons perished in the flames'",
   ("Printings of a London paragraph of early 1773 in two wordings: 'The Hotel Dieu, (one of the finest hospitals in the world) was burnt "
    "down at Paris the beginning of January last, and between seven and eight hundred sick persons perished in the flames ...' (the "
    "Virginia papers: 'The Hotel Dieu at Paris is burnt down, with twelve houses ...'). A London report, as the papers reprinted it; letters "
    "from Paris on the same fire are other texts."),
   [r'The\W+Hotel\W+Dieu'],
   "London, early 1773: a report that the Hotel Dieu at Paris was burnt.", "the London report of the Hotel Dieu",
   [k('MS', '03-25', 2), k('NHG', '03-26', 2), k('VG1', '04-01', 2), k('VG2', '04-08', 3)], words=34),
 S('boston-report-fire-in-the-custom-house-march-1773',
   "Boston, 29 March 1773: 'Last Friday, about three o'clock in the afternoon, a fire broke out in the custom-house; but by the timely assistance of the inhabitants of the town a stop was put to its progress before it had done much damage'",
   ("Printings of a Boston paragraph of 29 March 1773: 'Last Friday, about three o'clock in the afternoon, a fire broke out in the "
    "custom-house; but by the timely assistance of the inhabitants of the town a stop was put to its progress before it had done much "
    "damage ...'. A Boston report, as the papers reprinted it."),
   [r'Last\W+Friday,?\W+about\W+(?:three|3)\W+o\W*.?\W*clock\W+in\W+the\W+afternoon'],
   "Boston, March 1773: a report of a fire in the custom-house.", "the Boston report of the fire in the custom-house",
   [k('MS', '04-01', 2), k('NHG', '04-02', 3), k('VG1', '04-15', 2), k('VG2', '04-15', 2)], words=40),
 S('st-vincent-report-a-treaty-with-the-caribs-february-1773',
   "St. Vincent, 27 February 1773: 'On Wednesday the 17th instant a number of Charibs came into the Grand Camp at Macarican, and a TREATY of PEACE and FRIENDSHIP was then concluded by his Excellency General Dalrymple'",
   ("Printings of a St. Vincent paragraph of 27 February 1773, from the Royal Grenada Gazette: 'On Wednesday the 17th instant a number of "
    "Charibs came into the Grand Camp at Macarican, and a TREATY of PEACE and FRIENDSHIP was then concluded by his Excellency General "
    "Dalrymple ...'. A report from the island, as the papers reprinted it; the papers spell the Caribs and the camp in several ways."),
   [r'O\W*N\W+Wednesday\W+the\W+17th\W+inst'],
   "St. Vincent, February 1773: a report of a treaty with the Caribs.", "the St. Vincent report of the treaty",
   [(k('NHG', '04-09', 2), {'core': [r'S\W*T\.?\W+VINCENT,?\W+FEBRUARY\W+27'], 'dateline': False}),
    k('VG1', '04-15', 2), k('VG2', '04-15', 2), k('MS', '04-16', 1)], words=40),
 S('massachusetts-house-resolutions-answering-virginia-may-1773',
   "Boston, 28 May 1773: the House of Representatives' resolutions: 'Whereas the Speaker hath communicated to this House a letter from the truly respectable House of Burgesses in his Majesty's ancient colony of Virginia'",
   ("Printings of the resolutions of the Massachusetts House of Representatives of 28 May 1773 answering the Virginia resolutions of 12 "
    "March: 'Whereas the Speaker hath communicated to this House a letter from the truly respectable House of Burgesses in his Majesty's "
    "ancient colony of Virginia, enclosing a copy of the resolves entered into by them on the 12th of March last ...'. A published "
    "document, as the papers printed it."),
   [r'In\W+the\W+House\W+of\W+REPRESENTATIVES,?\W+May\W+28', r'W\W*HEREAS,?\W+the\W+Speaker\W+hath\W+communicated'],
   "Boston, May 1773: the House of Representatives' resolutions answering Virginia's.", "the Massachusetts resolutions of 28 May",
   [k('MS', '06-03', 2), k('NHG', '06-04', 1), k('VG1', '06-24', 3), k('VG2', '07-01', 2)], role='published_document', words=45, dateline=False),
 S('paris-report-rumours-of-war-april-1773',
   "Paris, 5 April 1773: 'The rumours of a war are now renewed with more force than ever, and have greatly influenced our public funds'",
   ("Printings of a Paris paragraph of 5 April 1773: 'The rumours of a war are now renewed with more force than ever, and have greatly "
    "influenced our public funds, which have fallen considerably within these few days ...'. A report from Paris, as the London papers "
    "gave it and the papers reprinted it."),
   [r'T\W*HE\W+rumours\W+of\W+a\W+war\W+are\W+now\W+renewed'],
   "Paris, April 1773: a report of rumours of war.", "the Paris report of rumours of war",
   [k('MS', '06-10', 2), k('NHG', '06-11', 1), k('VG1', '06-17', 1), k('VG2', '06-17', 1)], words=30),
 S('wilkes-letter-to-the-speaker-20-april-1773',
   "Prince's Court, 20 April 1773: Mr. Wilkes's letter to Sir Fletcher Norton, Speaker of the House of Commons: 'In pursuance of your orders to the Sheriff of Middlesex, on the 7th of this month, to summon the Representatives of this County, I have received a letter from Richard Oliver, Esq; and Sir Watkin Lewes'",
   ("Printings of a letter of John Wilkes to Sir Fletcher Norton, Speaker of the House of Commons, dated Prince's Court, 20 April 1773: "
    "'In pursuance of your orders to the Sheriff of Middlesex, on the 7th of this month, to summon the Representatives of this County, I "
    "have received a letter from Richard Oliver, Esq; and Sir Watkin Lewes ...'. A letter in its writer's words, as the papers reprinted "
    "it (an 'attested copy' in two papers)."),
   [r'An\W+ATTESTED\W+COPY\W+of\W+a\W+LETTER\W+from\W+JOHN\W+WILKES', r'Copy\W+of\W+Mr\.?\W+WILKES.s\W+Letter'],
   "London, April 1773: Mr. Wilkes's letter to the Speaker on the summons to the members for Middlesex.", "Mr. Wilkes's letter to the Speaker",
   [k('MS', '06-10', 3), k('VG1', '06-17', 3), (k('VG2', '06-17', 6), {'field': CA, 'core': [r'copsy\W+Arm\W+w\W+I\W+Lsix'], 'dateline': False, 'note': CA_NOTE}),
    k('NHG', '06-18', 1)], role='published_document', words=45),
 S('london-report-the-speaker-reads-the-sheriffs-letter-april-1773',
   "London, 22 April 1773: 'Lord North did not come yesterday from St. James's to the House of Commons till near four o'clock. As soon as his Lordship arrived, the Speaker rose, and acquainted the House that he had received a letter from the Sheriffs of Middlesex'",
   ("Printings of a London paragraph of 22 April 1773, one of them without its first sentence: 'Lord North did not come yesterday from St. "
    "James's to the House of Commons till near four o'clock. As soon as his Lordship arrived, the Speaker rose, and acquainted the House "
    "that he had received a letter from the Sheriffs of Middlesex, signed \"Richard Oliver\" and \"Watkin Lewes\", in answer to a circular "
    "letter he had written to them by order of the House ...'. A London report of proceedings in the House of Commons, as the papers "
    "reprinted it."),
   [r'Lord\W+North\W+did\W+not\W+come\W+yesterday', r'As\W+soon\W+as\W+Lord\W+North\W+came\W+to\W+the\W+House'],
   "London, April 1773: a report of the Speaker reading the Sheriffs of Middlesex's answer in the House of Commons.", "the London report of the Sheriffs' answer",
   [k('MS', '06-10', 2), k('VG1', '06-17', 3), k('VG2', '06-17', 3), k('NHG', '06-18', 1)], words=45),
 S('london-report-burke-on-the-door-keepers-april-1773',
   "London, 16 April 1773: 'If the door-keepers of the House of Commons should refuse to admit Mr. Wilkes on the 26th inst. Mr. E. Burke declares that he will move in the house, not only to dismiss them from their employments, but also to commit them to Newgate'",
   ("Printings of a London paragraph of 16 April 1773 ('a certain House' in the Virginia papers): 'If the door-keepers of the House of "
    "Commons should refuse to admit Mr. Wilkes on the 26th inst. Mr. E. Burke declares that he will move in the house, not only to dismiss "
    "them from their employments, but also to commit them to Newgate for offering so gross an insult to the member of that house.' A "
    "London report, as the papers reprinted it."),
   [r'If\W+the\W+door.?keepers\W+of'],
   "London, April 1773: a report of what Mr. Burke would move if Mr. Wilkes were refused admittance.", "the London report on Mr. Burke and the door-keepers",
   [k('MS', '06-10', 2), k('VG1', '06-17', 2), k('VG2', '06-17', 2), k('NHG', '06-18', 4)], words=45),
 S('london-report-ships-for-the-north-pole-1773',
   "London, May 1773: 'The Racehorse and Carcass are fitting out for an expedition to the North Pole, under the command of the Honourable Captain Phipps'",
   ("Printings of a London paragraph of May 1773: 'The Racehorse and Carcass are fitting out for an expedition to the North Pole, under "
    "the command of the Honourable Captain Phipps. Mr. Lyons is appointed by the Board of Longitude to make observations ...'. A London "
    "report, as the papers reprinted it."),
   [r'The\W+Racehorse\W+and\W+\w+\W+are\W+fitting\W+out'],
   "London, May 1773: a report of ships fitting out for the North Pole.", "the London report of the expedition to the North Pole",
   [k('VG1', '07-15', 3), k('VG2', '07-15', 3), k('MS', '07-22', 2), k('NHG', '07-23', 1)], words=30),
 S('annapolis-letter-on-the-maryland-bank-stock-july-1773',
   "Annapolis, July 1773: a letter: 'Our Assembly is passing an act, to sell out 40,000l. bank stock, and lend it to the people in Maryland, to keep up their credit'",
   ("Printings of an extract of a letter from Annapolis of 2 July 1773 (5 July in the New-Hampshire Gazette) in two wordings: 'Our Assembly "
    "is passing an act, to sell out 40,000l. bank stock, and lend it to the people in Maryland, to keep up their credit, which will be of "
    "great service at this time ...' (the others: 'Our assembly are passing an act for selling forty thousand pounds sterling bank stock "
    "...'). A letter at second hand, as the papers reprinted it."),
   [r'Extra\w*\W+of\W+a\W+letter\W+from\W+Annapolis'],
   "Annapolis, July 1773: a letter on the Maryland Assembly's act to lend money to the people.", "the letter from Annapolis",
   [k('MS', '07-22', 2), k('NHG', '07-23', 2), k('VG1', '07-29', 2), k('VG2', '07-29', 2)], words=40),
 S('london-report-a-loss-on-the-river-canton-1773',
   "London, 1773: 'The report that upwards of 200,000 people had been lost in the river Canton, in China, in a hurricane in August last, may seem extravagantly great'",
   ("Printings of a London paragraph of 1773 (the New England papers print '30,000' or 'thirty thousand' where the Virginia papers print "
    "'200,000'): 'The report that upwards of 200,000 people had been lost in the river Canton, in China, in a hurricane in August last, may "
    "seem extravagantly great; but when it is considered that the fishermen on that river, and all others that carry manure for the cultivation of "
    "rice, live with their families at all times in their boats, it may not appear so enormous ...'. A London report, as the papers "
    "reprinted it."),
   [r'The\W+report\W+that\W+upwards\W+of'],
   "London, 1773: a report on the numbers lost in a hurricane on the river at Canton.", "the London report on the river Canton",
   [k('VG1', '07-22', 1), k('MS', '08-05', 1), k('NHG', '08-06', 2), k('VG2', '09-02', 5)], words=40),
 S('london-report-emigration-from-the-north-of-ireland-1773',
   "London, July 1773: 'great numbers of vessels from Dublin, Londonderry, Belfast, Learn, Cork, and other ports, have lately sailed or are soon expected to sail, full of passengers, for different parts of America'",
   ("Printings of a London paragraph of July 1773 (in the Virginia papers dated 15 July: 'Numbers of vessels, we hear, from Dublin ... are "
    "daily expected to sail'): '... great numbers of vessels from Dublin, Londonderry, Belfast, Learn, Cork, and other ports, have lately "
    "sailed or are soon expected to sail, full of passengers, for different parts of America. These emigrations, it is thought, have "
    "already drained the northern parts of Ireland of near a third part of its most useful and industrious inhabitants ...'. A London "
    "report, as the papers reprinted it; in the New England papers it follows a paragraph on settlers for the Mississippi."),
   [r'We\W+hear\W+also,?\W+that\W+great\W+numbers\W+of\W+vessels', r'Numbers\W+of\W+vessels,?\W+we\W+hear,?\W+from\W+Dublin'],
   "London, July 1773: a report of ships full of emigrants from the north of Ireland.", "the London report on emigration from Ireland",
   [k('MS', '07-22', 3), k('NHG', '07-30', 1), k('VG1', '08-05', 2), k('VG2', '08-05', 2)], words=40),
 S('new-york-report-the-mississippi-packet-sails-july-1773',
   "New York, 19 July 1773: 'On Sunday last sailed from Elizabeth Town, the New-Jersey and Mississippi Packet, Brig, Capt. Thomas Davison, with whom went upwards of 70 passengers, bound to the Mississippi'",
   ("Printings of a New York paragraph of 19 July 1773: 'On Sunday last sailed from Elizabeth Town, the New-Jersey and Mississippi Packet, "
    "Brig, Capt. Thomas Davison, with whom went upwards of 70 passengers, bound to the Mississippi, where they intend to settle ...'. A New "
    "York report, as the papers reprinted it."),
   [r'On\W+Sunday\W+last\W+[sf]ailed\W+from\W+Elizabeth'],
   "New York, July 1773: a report of a brig sailing with settlers for the Mississippi.", "the New York report of the Mississippi packet",
   [k('MS', '07-29', 2), k('VG1', '08-05', 2), k('VG2', '08-05', 2), k('NHG', '08-06', 1)], words=38),
 S('london-common-council-on-the-east-india-bill-28-may-1773',
   "London, 28 May 1773: the Common Council's resolution sent to Mr. Wilkes: 'This court doth unanimously desire such Members of parliament as are members of this court to oppose the bill now depending in Parliament respecting the East-India Company'",
   ("Printings of a London paragraph of May 1773 with a copy of a resolution of the Common Council of London of 28 May 1773: 'Mr. Wilkes "
    "received the following on Saturday last: (COPY) A Common-Council holden in the Chamber of the Guildhall of the city of London on "
    "Friday the 28th of May, 1773. This court doth unanimously desire such Members of parliament as are members of this court to oppose "
    "the bill now depending in Parliament respecting the East-India Company.' A London report with a published resolution, as the papers "
    "reprinted it."),
   [r'Mr\.?\W+Wilkes\W+received\W+the\W+following', r'\(?COPY\)?\W+A\W+common\W+council\W+h[eo]ld'],
   "London, May 1773: the Common Council's resolution against the East India bill.", "the Common Council's resolution",
   [k('MS', '08-05', 1), (k('NHG', '08-06', 2), {'core': [r'\(?COPY\)?\W+A\W+common\W+council\W+h[eo]ld'], 'dateline': False}),
    k('VG1', '08-26', 1), k('VG2', '08-26', 5)], words=45),
 S('portsmouth-letter-on-the-king-s-visit-to-the-fleet-may-1773',
   "Portsmouth, 30 May 1773: a letter: 'This town is all alive on the certainty of their Majesties coming to see the fleet'",
   ("Printings of an extract of a letter from Portsmouth of 30 May 1773: 'This town is all alive on the certainty of their Majesties coming "
    "to see the fleet, where many officers of the navy and others are arriving every day. They have now a certainty of a great naval "
    "promotion, and six Admirals are to be made, and six Post Captains, six masters and commanders and twelve Lieutenants ...'. A letter at "
    "second hand, as the papers reprinted it."),
   [r'Extract\W+of\W+a\W+letter\W+from\W+Portsmouth,?\W+May\W+30'],
   "Portsmouth, May 1773: a letter on the expected royal visit to the fleet.", "the letter from Portsmouth",
   [k('MS', '08-05', 2), k('NHG', '08-06', 2), k('VG1', '08-26', 1), k('VG2', '08-26', 5)], words=40),
 S('london-gazette-governors-of-south-carolina-and-nova-scotia-june-1773',
   "Whitehall, 5 June 1773: 'The King has been pleased to appoint William Campbell, Esq; (commonly called Lord William Campbell) to be Captain General and Governor in chief of his Majesty's province of South Carolina'",
   ("Printings of a notice from the London Gazette, Whitehall, 5 June 1773 (in Rind's paper, with the "
    "appointment of a chief justice of Dominica before it): 'The King has been pleased to appoint William Campbell, Esq; (commonly called "
    "Lord William Campbell) to be Captain General and Governor in chief of his Majesty's province of South Carolina, in America, in the room "
    "of Lord Charles Greville Montague. The King has been also pleased to appoint Francis Legge, Esq; ...'. An official notice of "
    "appointments, as the papers reprinted it; a later paragraph on Lord William Campbell's patent is another text."),
   [r'The\W+King\W+has\W+been\W+pleased\W+to\W+appoint\W+(?:William\W+Campbell|Thomas\W+Wilson)'],
   "Whitehall, June 1773: a notice of the appointment of governors of South Carolina and Nova Scotia.", "the Whitehall notice of the governors' appointments",
   [k('MS', '08-05', 2), k('NHG', '08-06', 2), k('VG1', '08-26', 2), k('VG2', '08-26', 6)], role='published_document', words=40),
 S('london-report-lord-north-moves-a-mark-of-favour-for-general-monckton-1773',
   "London, 1773: 'Lord North moved an address to his Majesty, that he would be graciously pleased to confer some mark of royal favour upon General Robert Monckton, for his signal services'",
   ("Printings of a London paragraph of 1773 on the House of Commons: '[Yesterday in the House of Commons] Lord North moved an address to "
    "his Majesty, that he would be graciously pleased to confer some mark of royal favour upon General Robert Monckton, for his signal "
    "services, by granting to him a quantity of land in the ceded islands ...'. A London report of proceedings in Parliament, as the papers "
    "reprinted it."),
   [r'Yesterday\W+in\W+the\W+House\W+of\W+Commons,?\W+Lord\W+North\W+moved', r'Lord\W+North\W+moved\W+an\W+address\W+to\W+his\W+Majesty'],
   "London, 1773: a report of Lord North's motion on General Monckton.", "the London report of Lord North's motion",
   [k('MS', '08-05', 5), k('NHG', '08-20', 3), k('VG1', '09-02', 2), k('VG2', '09-02', 2)], words=40),
 S('dresden-report-a-storm-at-reichenbach-june-1773',
   "Dresden, 2 June 1773: 'We have received a very disagreeable account of great damage having been done by a storm of thunder and lightning in the circle of Voigtland in this electorate'",
   ("Printings of a Dresden paragraph of 2 June 1773: 'We have received a very disagreeable account of great damage having been done by a "
    "storm of thunder and lightning in the circle of Voigtland in this electorate: The whole town of Reichenbach is entirely ...'. A "
    "report from Dresden, as the London papers gave it and the papers reprinted it."),
   [r'W\W*E\W+have\W+received\W+a\W+very\W+disagreeable\W+account'],
   "Dresden, June 1773: a report of a storm at Reichenbach.", "the Dresden report of the storm",
   [k('MS', '08-05', 5), k('NHG', '08-20', 1), k('VG1', '09-02', 1), k('VG2', '09-02', 5)], words=40),
 S('vienna-report-advices-from-constantinople-may-1773',
   "Vienna, May 1773: 'The freshest advices from Constantinople say, that they intend to push on the war with the utmost vigour against the Russians'",
   ("Printings of a Vienna paragraph of May 1773 (dated 25 May in the New England papers, 15 May in the Virginia papers): 'The freshest "
    "advices from Constantinople say, that they intend to push on the war with the utmost vigour against the Russians; that several "
    "couriers had been dispatched with orders ...'. A report from Vienna, as the London papers gave it and the papers reprinted it."),
   [r'The\W+freshest\W+advices\W+from\W+Constantinople'],
   "Vienna, May 1773: a report of advices from Constantinople on the war.", "the Vienna report",
   [k('MS', '08-05', 1), k('NHG', '08-06', 2), k('VG1', '08-26', 1), k('VG2', '08-26', 1)], words=36),
 S('temeswar-letter-on-the-turks-and-russians-may-1773',
   "Temeswar, 23 May 1773: a letter: 'Since hostilities have recommenced between the Turks and Russians, they have had several skirmishes and severe conflicts'",
   ("Printings of an extract of a letter from Temeswar of 23 May 1773: 'Since hostilities have recommenced between the Turks and Russians, "
    "they have had several skirmishes and severe conflicts, in which victory has indifferently declared herself for either party ...'. A "
    "letter at second hand, as the papers reprinted it."),
   [r'Extract\W+of\W+a\W+letter\W+from\W+T[ae]m\w*', r'Since\W+hostilities\W+have\W+recommenced'],
   "Temeswar, May 1773: a letter on the fighting between the Turks and Russians.", "the letter from Temeswar",
   [k('MS', '08-05', 5), k('NHG', '08-20', 1), k('VG1', '09-02', 1), k('VG2', '09-02', 6)], words=36),
 S('philadelphia-report-french-and-spanish-navy-laid-up-july-1773',
   "Philadelphia, 21 July 1773: 'Yesterday Capt. Stewart arrived here from Gibraltar, and acquaints us, that the Pallas Frigate put in there the day before he sailed'",
   ("Printings of a Philadelphia paragraph of 21 July 1773: 'Yesterday Capt. Stewart arrived here from Gibraltar, and acquaints us, that the "
    "Pallas Frigate put in there the day before he sailed, the Captain of which reported, that he had been at Toulon and Carthagena, where "
    "there was not the least signs of any hostile preparations, the French and Spanish navy at both places being laid up ...'. A "
    "shipmaster's report at second hand, as the papers reprinted it."),
   [r'Yesterday\W+(?:arrived\W+here\W+)?Capt\w*\.?\W+Stewart'],
   "Philadelphia, July 1773: a shipmaster's report that the French and Spanish navies were laid up.", "the Philadelphia report from Gibraltar",
   [k('NHG', '08-06', 2), k('MS', '08-12', 1), k('VG1', '08-12', 2), k('VG2', '08-19', 2)], words=42),
 S('south-carolina-commons-house-on-the-virginia-letter-july-1773',
   "Charlestown (South Carolina), 13 July 1773: 'On Thursday last, before his honour the Lieutenant Governor prorogued the Commons House of Assembly, the hon. Rawlins Lowndes, Esq; their Speaker, laid before them a letter by him received, from the Speaker of the House of Burgesses in Virginia'",
   ("Printings of a Charlestown report of 13 July 1773 (in Rind's Virginia Gazette, another Charlestown report, of 16 July) with the "
    "resolutions of the South Carolina Commons House of Assembly answering the Virginia resolutions of 12 March: 'RESOLVED, That Mr. "
    "Speaker, and eight of the other members of the standing committee of correspondence, be a committee to enquire for, and obtain "
    "intelligence ...'. Reports with a published document, as the papers reprinted them; the two reports introduce the same resolutions "
    "(C-02)."),
   [r'On\W+Thursday\W+last,?\W+(?:before\W+his\W+hono\w*|the\W+Hono\w*\W+Rawlins)'],
   "Charlestown, July 1773: the South Carolina Commons House's resolutions answering Virginia's.", "the Charlestown report of the Commons House's resolutions",
   [k('MS', '08-12', 1), k('VG2', '08-12', 2),
    (k('NHG', '08-13', 2), {'core': [r'CHARLESTOWN,?\W+S\.?\W+Carolina,?\W+July\W+13'], 'dateline': False}), k('VG1', '09-02', 2)], words=42),
 S('honduras-letter-on-a-species-of-tigers-june-1773',
   "St. George's Key, Bay of Honduras, 4 June 1773: a letter: 'This day they bring us from Sherboon the following account: That a few days ago came into that river a species of tigers, not like any ever known in this country'",
   ("Printings of an extract of a letter from St. George's Key, Bay of Honduras, of 4 June 1773 ('another letter from the same place' in "
    "two papers, 'a letter from the same place' in the Massachusetts Spy), printed with New York news of 5 August: 'This day they bring us from Sherboon the following account: That a few days "
    "ago came into that river a species of tigers, not like any ever known in this country ...'. A letter at second hand, as the papers "
    "reprinted it."),
   [r'Extract\W+of\W+a\W+letter\W+from\W+St\.?\W+George.s\W+Key,?\W+Bay\W+of\W+Honduras,?\W+June\W+4',
    r'Extra\S*\W+of\W+(?:a|another)\W+letter\W+from\W+the\W+[sf]ame\W+place'],
   "Bay of Honduras, June 1773: a letter on a kind of tiger come into the river.", "the letter from the Bay of Honduras",
   [(k('MS', '08-19', 1), {'core': [r'Extra\S*\W+of\W+(?:a|another)\W+letter\W+from\W+the\W+[sf]ame\W+place']}),
    (k('NHG', '08-20', 2), {'field': CA, 'note': CA_NOTE}),
    (k('VG1', '08-26', 2), {'core': [r'Extra\S*\W+of\W+(?:a|another)\W+letter\W+from\W+the\W+[sf]ame\W+place']}), k('VG2', '08-26', 2)], words=40),
 S('london-report-the-midsummer-day-common-hall-june-1773',
   "London, 25 June 1773: 'Yesterday being midsummer day, there was a very numerous and respectable appearance of the livery of London, in Common-Hall assembled, for the annual purpose of electing Sheriffs for the city of London, and county of Middlesex'",
   ("Printings of a London paragraph of 24 and 25 June 1773: 'Yesterday being midsummer day, there was a very numerous and respectable "
    "appearance of the livery of London, in Common-Hall assembled, for the annual purpose of electing Sheriffs for the city of London, and "
    "county of Middlesex, for the year ensuing ...'. A London report, as the papers reprinted it."),
   [r'(?:Yesterday|This\W+Day|The\W+24th\W+of\W+this\W+instant),?\W+being\W+midsummer'],
   "London, June 1773: a report of the Common Hall for the election of sheriffs.", "the London report of the Common Hall",
   [k('MS', '08-19', 2), k('NHG', '08-27', 1), k('VG1', '09-09', 1), k('VG2', '09-09', 2)], words=42),
 S('london-report-the-king-s-gifts-at-portsmouth-june-1773',
   "London, 26 June 1773: 'His Majesty set out from the Commissioner's house, on his return to Kew, at three quarters after six o'clock, having been graciously pleased to order the following sums to be distributed'",
   ("Printings of a London paragraph of 26 June 1773 (another wording in the New-Hampshire Gazette): 'His Majesty set out from the "
    "Commissioner's house, on his return to Kew, at three quarters after six o'clock, having been graciously pleased to order the following "
    "sums to be distributed, viz. To the artificers, workmen, and labourers of the Dock-yard ...' (after the King's visit to the fleet at "
    "Portsmouth). A London report, as the papers reprinted it."),
   [r'H?IS\W+Majesty\W+(?:before\W+he\W+)?set\W+out\W+from'],
   "London, June 1773: a report of the King's gifts at Portsmouth.", "the London report of the King's gifts",
   [k('MS', '09-02', 2), k('NHG', '09-03', 2), k('VG1', '09-09', 2), k('VG2', '09-09', 2)], words=40),
 S('london-report-the-french-ambassador-at-portsmouth-1773',
   "London, June 1773: 'The French Ambassador observed at Portsmouth, that he had now seen two of the finest sights in the world, \"The King of Prussia, at the head of his army, and the King of England at the head of his fleet\"'",
   ("Printings of a London paragraph of June 1773: 'The French Ambassador observed at Portsmouth that he had now seen two of the finest "
    "sights in the world, \"The King of Prussia, at the head of his army, and the King of England at the head of his fleet.\" ...'. A London "
    "report, as the papers reprinted it."),
   [r'The\W+French\W+Ambassador\W+observed,?\W+at\W+Portsmouth'],
   "London, June 1773: a report of what the French Ambassador said at Portsmouth.", "the London report on the French Ambassador",
   [k('MS', '09-02', 2), k('NHG', '09-03', 2), k('VG1', '09-09', 2), k('VG2', '09-09', 2)], words=36),
 S('king-speech-closing-the-session-1-july-1773',
   "London, 1 July 1773: 'This day his Majesty went to the House of Peers, made a speech to both houses, and put an end to the present session of parliament'",
   ("Printings of a London paragraph of 1 July 1773 with the King's speech closing the session of Parliament: 'This day his Majesty went "
    "to the House of Peers, made a speech to both houses, and put an end to the present session of parliament. His Majesty's speech was "
    "substantially as follows: \"My Lords and Gentlemen, ...\"'. A London report with a published speech, as the papers reprinted it."),
   [r'T\W*HIS\W+day\W+his\W+Majesty\W+went\W+to\W+the\W+House\W+of\W+Peers'],
   "London, July 1773: the King's speech closing the session of Parliament.", "the London report of the King's closing speech",
   [k('MS', '09-02', 2), k('NHG', '09-03', 2), k('VG1', '09-09', 2), k('VG2', '09-09', 2)], role='published_document', words=40),
 S('constantinople-letter-on-the-turkish-fleet-may-1773',
   "Constantinople, 29 May 1773: a letter: 'A Ragusan sloop of war, in the service of the Porte, is just arrived here from the Palus Maeotis, or the sea of Asoph, and brings the following account of the success which the Turkish fleet met with'",
   ("Printings of an extract of a letter from Constantinople of 29 May 1773 (19 May in the New-Hampshire Gazette): 'A Ragusan sloop of war, "
    "in the service of the Porte, is just arrived here from the Palus Maeotis, or the sea of Asoph, and brings the following account of the "
    "success which the Turkish fleet met with ...'. A letter at second hand, as the papers reprinted it."),
   [r'Extract\W+of\W+a\W+letter\W+from\W+Constantinople,?\W+May\W+[12]9'],
   "Constantinople, May 1773: a letter on the Turkish fleet in the sea of Azov.", "the letter from Constantinople",
   [k('MS', '09-02', 2), k('NHG', '09-03', 2), k('VG1', '09-09', 2), k('VG2', '09-09', 2)], words=42),
 S('london-report-a-governor-for-the-ohio-colony-july-1773',
   "London, 9 July 1773: 'We are informed, that Lord Dartmouth has nominated Col. George Mercer to be Governor of the new colony on the Ohio, which should be called Pittsylvania'",
   ("Printings of a London paragraph of 9 July 1773: 'We are informed, that Lord Dartmouth has nominated Col. George Mercer to be Governor of "
    "the new colony on the Ohio, which should be called Pittsylvania. Our correspondent observes, that this act is a strong proof of his "
    "Lordship's strict justice, as well as of his good judgment.' A London report, as the papers reprinted it."),
   [r'We\W+are\W+informed,?\W+that\W+Lord\W+Dartmouth\W+has\W+nominated'],
   "London, July 1773: a report of a governor named for the new colony on the Ohio.", "the London report on the Ohio colony",
   [k('MS', '09-16', 3), k('NHG', '09-17', 2), k('VG1', '09-23', 1), k('VG2', '09-23', 2)], words=42),
 S('london-report-french-refugees-for-new-york-july-1773',
   "London, July 1773: 'It is said that a considerable number of French Refugees, well skilled in the management of silk-worms, and making of wines, have within these few days engaged themselves on very advantageous terms to go to New-York'",
   ("Printings of a London paragraph of 20 and 24 July 1773: 'It is said that a considerable number of French Refugees, well skilled in the "
    "management of silk-worms, and making of wines, have within these few days engaged themselves on very advantageous terms to go to "
    "New-York ...'. A London report of what 'is said', as the papers reprinted it."),
   [r'It\W+is\W+said\W+(?:that\W+)?a\W+considerable\W+number\W+of\W+French'],
   "London, July 1773: a report of French refugees engaged to go to New York.", "the London report on French refugees",
   [k('MS', '09-23', 3), k('VG1', '09-23', 2), k('VG2', '09-23', 3), k('NHG', '09-24', 2)], words=40),
 S('london-paragraph-a-scotch-peruke-maker-july-1773',
   "London, July 1773: 'A Scotch Peruke-maker was employed to make a Great Personage's Spanish fly, so that now both the out, as well as the inside of his head, is entirely furnished by Scotchmen'",
   ("Printings of a London paragraph of July 1773: 'A Scotch Peruke-maker was employed to make a Great Personage's Spanish fly, so that now "
    "both the out, as well as the inside of his head, is entirely furnished by Scotchmen.' A London paper's jest, as the papers reprinted "
    "it."),
   [r'A\W+Scotch\W+\w+.?maker\W+was\W+employed'],
   "London, July 1773: a London paper's jest about 'a Great Personage' and the Scots.", "the London jest about a Great Personage",
   [k('MS', '09-23', 3), k('VG1', '09-23', 6), k('VG2', '09-23', 3), k('NHG', '09-24', 2)], words=30),
 S('new-york-report-three-tea-ships-october-1773',
   "New York, October 1773: 'By letters from London, and from good authority, we are assured that the East-India Company have determined upon sending three vessels with tea, one of them for Boston, another for Philadelphia, and the third for this port'",
   ("Printings of a New York paragraph of October 1773: 'By letters from London, and from good authority, we are assured that the "
    "East-India Company have determined upon sending three vessels with tea, one of them for Boston, another for Philadelphia, and the "
    "third for this port, and it is most confidently asserted, that no duty will be paid upon those teas in America.' A New York report of "
    "what letters say, as the papers reprinted it."),
   [r'By\W+letters?\W+from\W+London,?\W+(?:and\W+)?from\W+good\W+authority'],
   "New York, October 1773: a report that the East India Company would send three ships with tea.", "the New York report of the tea ships",
   [k('PP', '10-25', 3), k('MS', '10-28', 3), k('VG1', '11-11', 6), k('VG2', '11-11', 6), k('NHG', '11-12', 2)], words=45),
 S('london-report-colony-agents-warned-on-the-bounties-august-1773',
   "London, 24 August 1773: 'It is said the Colony agents have been given to understand, that if any further opposition is made to the measures of government, the several bounties paid for the encouragement of American produce'",
   ("Printings of a London paragraph of 24 August 1773: 'It is said the Colony agents have been given to understand, that if any further "
    "opposition is made to the measures of government, the several bounties paid for the encouragement of American produce, on their "
    "importation ...'. A London report of what 'is said', as the papers reprinted it."),
   [r'It\W+is\W+said\W+the\W+Colony\W+agents\W+have\W+been\W+given'],
   "London, August 1773: a report of a warning to the colony agents on the bounties.", "the London report on the colony agents",
   [k('MS', '10-28', 2), k('PP', '11-01', 2), k('NHG', '11-05', 2), k('VG1', '11-11', 5), k('VG2', '11-11', 5)], words=40),
 S('paris-letter-the-charge-d-affaires-to-leave-london-august-1773',
   "Paris, 17 August 1773: a letter: 'Our Charge d'Affaires is positively ordered to leave London, and to give directions for the sale of every thing belonging to our Ambassador'",
   ("Printings of an extract of a letter from Paris of 17 August 1773: 'Our Charge d'Affaires is positively ordered to leave London, and to "
    "give directions for the sale of every thing belonging to our Ambassador ...'. A letter at second hand, as the London papers gave it "
    "and the papers reprinted it."),
   [r'Extract\W+of\W+a\W+letter\W+from\W+Paris,?\W+(?:dated\W+)?August\W+17'],
   "Paris, August 1773: a letter that the French Charge d'Affaires was ordered to leave London.", "the letter from Paris of 17 August",
   [k('PP', '10-25', 3), k('MS', '11-04', 2), k('VG1', '11-11', 6), k('VG2', '11-11', 6), k('NHG', '11-12', 2)], words=36),
 S('amsterdam-letter-a-courier-from-paris-august-1773',
   "Amsterdam (the Hague, or Paris), 20 August 1773: a letter: 'By a Scheveling boat I have an opportunity of sending you this important information, that by a courier arrived last night at the Hague, from Paris, Madame Barre is disgraced'",
   ("Printings of an extract of a letter of 20 August 1773, headed from Amsterdam in three papers, from the Hague and from Paris in the "
    "others: 'By a Scheveling boat I have an opportunity of sending you this important information, that by a courier arrived last night at "
    "the Hague, from Paris, Madame Barre is disgraced. The Choiseul party are triumphant; and war will be declared against England in less "
    "than ten days ...'. A letter at second hand, as the London papers gave it and the papers reprinted it."),
   [r'Extract\W+of\W+a\W+letter\W+from\W+(?:Amsterdam|Paris|the\W+Hague),?\W+August\W+20'],
   "August 1773: a letter that war would be declared against England.", "the letter of 20 August",
   [k('PP', '10-25', 3), k('MS', '11-04', 2), k('VG1', '11-11', 6), k('VG2', '11-11', 6), k('NHG', '11-12', 2)], words=40),
 # ---- chosen: eligible, printed by four of the five papers of its weeks (December) ----
 S('new-york-report-tea-agents-appointed-december-1773',
   "New York, 2 December 1773: 'Letters were received by the Packet appointing the Honourable Henry White, Esq; Abraham Lott, Esq; and Mr. Benjamin Booth, Merchant of this City, to be Agents for the Sale of the Tea shipped for this Province'",
   ("Printings of a New York paragraph of 2 December 1773: 'Letters were received by the Packet appointing the Honourable Henry White, Esq; "
    "Abraham Lott, Esq; and Mr. Benjamin Booth, Merchant of this City, to be Agents for the Sale of the Tea shipped for this Province, by the "
    "Honourable East India Company ...'. A New York report, as the papers reprinted it."),
   [r'L\W*ETTERS\W+were\W+received\W+by\W+the\W+Packet\W+appointing'],
   "New York, December 1773: a report of the agents appointed for the East India Company's tea.", "the New York report of the tea agents",
   [k('PP', '12-06', 3), k('NHG', '12-17', 2), k('VG1', '12-23', 6), k('VG2', '12-23', 3)], words=42),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797, 1800, 1801 and 1803): "BOSTON, August 12."
# 1773 takes, as 1772 does after the cross-year check of openings (24 November 2026), a bare date ('Nov. 10.'), a place with
# 'St.' ("ST. JAMES'S, Sept. 1."), a bracketed state or island ('VIENNA, [Germany] May 25.') and a space before the comma.
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|(?:S[Tt]\.\s*)?[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*[\(\[][A-Za-z ,.\-]+[\)\]])?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)((?:" + PLACE + r"\s*,?\s+)?" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


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
            problems.append((s['id'], key, 'page not in the 1773 pages'))
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
        r['id'] = f'S73-{n:03}'
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
               'admission_rule': 'Reviewed 1773 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1773/'
    return {
        'ledger_id': 'ledger:stories-1773', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1773', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1773, and of 1772 where they reach the 1773 pages (long-running ones '
                   'included), every item in 3 or more papers counted again by the first 40 words of its opening against every page, papers that '
                   'comparison missed looked for again by their words and their names, and read, a sweep of word-for-word passages shared by 4 or '
                   'more papers for items the families miss (its passages that no counted item explains read one by one), phrase searches on all '
                   '846 pages of 1773 in both transcriptions for every item read at the bar or one paper short of it, and scan checks of each '
                   'admitted and chosen passage, by the thin-year rule (Y-THIN as amended on 23 November 2026: an item '
                   'printed by more than half of the newspapers that survive for its weeks, and by at least 4, is eligible; items printed by every '
                   'surviving paper are admitted, the others chosen to cover the months and the kinds of news; single paragraphs from runs of news '
                   'counted by their own words, C-09)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1772.json': 'retrieval_candidates',
                             d+'counted_items.json': 'retrieval_candidates', d+'phrase_patterns.json': 'retrieval_patterns',
                             d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1773.py': 'ledger_code', 'work/archive_data/ledgers/stories_1773_review.json': 'scan_review',
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
