"""Write ledgers/stories_1772.json: reviewed stories of 1772, round one.

1772 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN, as amended on 23 November 2026, the owner's
choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the newspapers that
survive for its weeks (those with a surviving issue between its first and last printing, and at least in the three weeks
from its first printing), and by at least 4; items printed by every newspaper that survives for their weeks are admitted;
the other eligible items are chosen to cover the months and the kinds of news; digests are not admitted. 1772 has five
papers, three of them all year; Rind's Virginia Gazette survives in 18 issues and the South-Carolina and American General
Gazette in one, so an item reaches the bar only where four papers survive and all four print it, or four of the five in
the weeks of 5 October. Single paragraphs from runs of news are counted by their own words (C-09).
The automatic families first printed in 1772 that reach 3 or more papers, and those of 1771 over the 1772 pages,
long-running ones included, were split into single printed items with work/story_items.py --long-running (items.json,
items_from_1771.json); every item in 3 or more papers was counted again by the first 40 words of its opening against
every page of the year (papers the comparison missed were looked for again, by their words and by their names, and read),
and a sweep of word-for-word passages shared by 4 or more papers (as for 1803, X-1803-09) found items the families miss.
Every admitted and chosen item was counted by its own opening with phrase searches over all 675 pages of 1772 in both
transcriptions (work/story_phrase_search.py's patterns). See outputs/story_discovery_1772/README.md.

The 1772 pages are those whose issue the data release dates to 1772 (work/year_search_pages.py 1772 ... --printed-dates).
1772 has 6 catalogue series, which are 5 papers: the Massachusetts Spy (Boston) under two numbers (sn83021193 to 1 October;
sn83021194, 'or, Thomas's Boston Journal', from 8 October), the New-Hampshire Gazette, two Virginia Gazettes of Williamsburg
with different printers (Purdie and Dixon, sn84024739; Rind, sn84024741), and one issue of the South-Carolina and American
General Gazette (Charlestown, 5 October).

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 25-70 words), starting with its dateline or heading when one
stands directly before it (a place and date, a bare date such as 'Sept. 25.', a letter-spaced or bracketed place name). A
paragraph printed in a run of news is counted, and its excerpt cut, by its own opening sentence. Scan findings, crops and
hand-drawn boxes are merged from stories_1772_review.json after the scan check. A printing on a page whose RevX
transcription is filed under another scan page (derived/revx_page_map.parquet) takes its excerpt from the CA
transcription of its scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied; other years are reviewed at the same time, and the main
session renumbers at release:
    python work/archive_data/ledgers/make_stories_1772.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1772/search_pages.json). The excerpts are cut from
the 1772 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1772'
D = PROJECT/'outputs/story_discovery_1772'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1772_review.json'
OUT = HERE/'stories_1772.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83025582': 'The New-Hampshire Gazette', 'sn84024739': 'The Virginia Gazette (Purdie and Dixon)',
         'sn84024741': 'The Virginia Gazette (Rind)', 'sn83021193': 'The Massachusetts Spy', 'sn83021194': 'The Massachusetts Spy',
         'sn83025790': 'The South-Carolina and American General Gazette'}
ONE = {'NHG': 'sn83025582', 'VG1': 'sn84024739', 'VG2': 'sn84024741', 'SCG': 'sn83025790'}
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
    """Page key of a printing: paper code, date (MM-DD in 1772), page and edition. The Massachusetts Spy has two catalogue
    numbers: sn83021193 to 1 October, sn83021194 from 8 October."""
    lccn = ('sn83021194' if date >= '10-08' else 'sn83021193') if paper == 'MS' else ONE[paper]
    return f'{lccn}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()

PHILA = 'philadelphia-report-of-11-november-1772-on-the-frontier'

# Story groups. 'printings' lists each printing's page; a tuple adds overrides for that printing: core (regexes for the
# item's first words), role, field, note, words, dateline (include a dateline directly before), back (start at the
# beginning of the sentence that holds the core), stop (a regex: the excerpt ends before it).
STORIES = [
 # ---- admitted: printed by every paper that survives for their weeks ----
 dict(id='london-report-the-king-in-council-on-the-duke-of-cumberland-1771', kind='message_group',
      label="London, November 1771: 'A very great Personage last Thursday, in Council, after expressing the most tender concern for the Duke of Gloucester, thought proper to take notice, that the late act of the Duke of Cumberland would cause an eternal separation between himself and the Duke'",
      definition=("Printings of a London paragraph of November 1771 (dated 11 and 13 November in the Virginia papers): 'A very great Personage last "
                  "Thursday, in Council, after expressing the most tender concern for the Duke of Gloucester, thought proper to take notice, that the "
                  "late act of the Duke of Cumberland would cause an eternal separation between himself and the Duke. Upon which tears being seen to "
                  "gush, a motion was made to adjourn the Council; but the great Personage, resuming his wonted firmness, told the Council, that no "
                  "private concerns respecting himself should ever retard the public business of the kingdom ...'. A London paper's report, as the "
                  "papers reprinted it."),
      role='report', words=43, dateline=True, stop=r'The\W+account\W+in\W+some|The\W+following\W+are\W+the\W+further|No\W+less\W+than\W+four',
      core=[r'(?:L\W*A\W*S\W*T\W+Thursday\W+)?a\W+very\W+great\W+Pe\w+,?\W+(?:last\W+Thursday,?\W+)?in\W+Council'],
      first="London, November 1771: a report of the King's words in Council on the 'late act' of his brother the Duke of Cumberland.",
      what="the London report of the King in Council",
      printings=[k('MS', '01-23', 2), k('NHG', '01-31', 2), (k('VG2', '02-06', 2), {'words': 46}), k('VG1', '02-13', 2)]),
 dict(id='new-york-report-captain-prince-fire-at-grenada-1772', kind='message_group',
      label="New York, February 1772: 'Captain Prince, from Cayenne, on his passage, touched at the Windward Islands, where he was informed, that on the 27th of December last, a most terrible fire broke out in the Island of Grenada, which burnt down no less than 600 houses'",
      definition=("Printings of a New York paragraph of February 1772: 'Captain Prince, from Cayenne, on his passage, touched at the Windward Islands, "
                  "where he was informed, that on the 27th of December last, a most terrible fire broke out in the Island of Grenada, which burnt down no "
                  "less than 600 houses; and that not more than 40 were left standing in the whole town of Grenada.' A shipmaster's report at second "
                  "hand. Letters from the islands on the same fire, in other words, are other texts."),
      role='report', words=55, dateline=True, stop=r'Captain\W+Prince\W+acquaints|M\W*E\W*W\W*-?\W*H\W*A\W*V\W*E\W*N|Extract\W+of\W+a\W+letter\W+from\W+Mr',
      core=[r'Capt\w*\.?\W+Prince,?\W+(?:from\W+Cayenne,?\W+)?on\W+his\W+passage'],
      first="New York, February 1772: a shipmaster's report of a fire in Grenada.",
      what="the New York report of the fire in Grenada",
      printings=[k('MS', '03-05', 3), k('NHG', '03-06', 2), k('VG1', '03-12', 3), k('VG2', '03-12', 2)]),
 dict(id='london-report-proclamation-for-emigrants-to-america-1772', kind='message_group',
      label="London, August 1772: 'It is said that a proclamation will shortly be issued, offering great advantages to those people who embark for America, in order to cultivate the country, and facilitate the Mississippi scheme'",
      definition=("Printings of a London paragraph of August 1772 (dated 24 August in Rind's Virginia Gazette): 'It is said that a proclamation will "
                  "shortly be issued, offering great advantages to those people who embark for America, in order to cultivate the country, and "
                  "facilitate the Mississippi scheme.' A London report of what 'is said'."),
      role='report', words=35, dateline=True, stop=r'August\W+21\W+One|The\W+last\W+ships|Sunday\W+Morning|A\W+correspondent\W+informs',
      core=[r'It\W+is\W+said\W+that\W+a\W+(?:P|p)roclamation\W+will\W+shortly'],
      first="London, August 1772: a report that a proclamation would offer advantages to people embarking for America.",
      what="the London report of a proclamation for people embarking for America",
      printings=[k('NHG', '10-23', 2), k('MS', '10-29', 2), k('VG1', '11-05', 2), k('VG2', '11-05', 1)]),
 dict(id='st-james-receiver-general-of-virginia-1772', kind='message_group',
      label="St. James's, 1 September 1772: 'The King has been pleased to grant unto George James Williams and Francis North, Esqrs. the office of Receiver General of all his Majesty's revenues within his colony and dominion of Virginia'",
      definition=("Printings of a notice from St. James's of 1 September 1772: 'The King has been pleased to grant unto George James Williams and Francis "
                  "North, Esqrs. the office of Receiver General of all his Majesty's revenues within his colony and dominion of Virginia.' An official "
                  "notice of an appointment, as the London papers gave it."),
      role='report', words=40, dateline=True, stop=r'NORTHAMPTON|Also\W+passed|They\W+write\W+from\W+Paris|WILLIAMSBURG',
      core=[r'The\W+King\W+has\W+been\W+pleased\W+to\W+grant\W+unto\W+George'],
      first="St. James's, September 1772: a notice that the King granted the office of Receiver General of his revenues in Virginia.",
      what="the notice of the Receiver General of Virginia",
      printings=[k('MS', '10-29', 2), k('NHG', '10-30', 1), k('VG1', '11-05', 2), k('VG2', '11-05', 2)]),
 dict(id='hamburg-letter-on-the-revolution-in-sweden-1772', kind='message_group',
      label="Hamburg, 25 August 1772: 'The day before yesterday two express were dispatched from Stockholm ... The four great cities ... have declared his Majesty, the King of Sweden, as their absolute sovereign'",
      definition=("Printings of an extract of a letter from Hamburg of 25 August 1772: 'The day before yesterday two express were dispatched from "
                  "Stockholm, and passed through this city ... it is no longer a secret here. The following is the intelligence they brought: \"The four "
                  "great cities, namely, Christianstadt, Joenkjoeping, Landscrona, and Gothenburgh, have declared his Majesty, the King of Sweden, as "
                  "their absolute sovereign ...\"'. A letter at second hand. Rind's Virginia Gazette prints the same letter in other words ('A letter "
                  "from Hambourg, dated August 25, says ... two couriers, dispatched from Stockholm ...'), counted with it (C-02)."),
      role='report', words=55, dateline=False,
      core=[r'Extract\W+of\W+a\W+(?:L|l)etter\W+from\W+Hamburg', r'A\W+letter\W+from\W+Hambourg'],
      first="Hamburg, August 1772: a letter on the news from Sweden that the King had been declared absolute.",
      what="the letter from Hamburg on Sweden",
      printings=[(k('MS', '10-29', 1), {'words': 57}), k('VG1', '11-05', 3), (k('VG2', '11-05', 1), {'words': 48}), k('NHG', '11-20', 2)]),
 dict(id='london-war-office-orders-for-officers-in-america-1772', kind='message_group',
      label="London, September 1772: 'Orders are stuck up at the War-Office for all persons (commissioned and private) absent from regiments on duty in the West Indies and America to join them without delay'",
      definition=("Printings of a London paragraph of September 1772: 'Orders are stuck up at the War-Office for all persons (commissioned and "
                  "private) absent from regiments on duty in the West Indies and America to join them without delay.' A London report of an order."),
      role='report', words=35, dateline=True, stop=r'Sept\W+25|Extract\W+of\W+a\W+(?:L|l)etter|The\W+(?:W|w)hale\W+(?:F|f)ishery',
      core=[r'Orders\W+are\W+stuck\W+up\W+at\W+the\W+(?:W|w)ar'],
      first="London, September 1772: a report of orders at the War-Office for soldiers absent from regiments in the West Indies and America.",
      what="the London report of the War-Office orders",
      printings=[k('MS', '11-19', 3), k('NHG', '11-20', 1), k('VG1', '12-10', 1), k('VG2', '12-10', 5)]),
 dict(id='london-report-dartmouth-lenient-measures-1772', kind='message_group',
      label="London, 25 September 1772: 'A correspondent informs us that Lord Dartmouth has signified his determined resolution that the most lenient measures shall be adopted towards the Americans'",
      definition=("Printings of a London paragraph of 25 September 1772: 'A correspondent informs us that Lord Dartmouth has signified his "
                  "determined resolution that the most lenient measures shall be adopted towards the Americans.' A London paper's report from a "
                  "correspondent."),
      role='report', words=30, dateline=True, stop=r'Mr\.?\W+Fordyce|Interest\W+is\W+making|DIED',
      core=[r'A\W+(?:C|c)orrespondent\W+informs\W+us,?\W+that\W+Lord\W+Dartmouth'],
      first="London, September 1772: a report that Lord Dartmouth had resolved on 'the most lenient measures' towards the Americans.",
      what="the London report on Lord Dartmouth",
      printings=[k('MS', '11-19', 3), k('NHG', '11-20', 1), k('VG1', '12-10', 1), k('VG2', '12-10', 5)]),
 dict(id='boston-report-bernard-expected-governor-of-barbados-1772', kind='message_group',
      label="Boston, November 1772: 'By letters from Barbados, we learn that it was expected that Sir Francis Bernard would be appointed to that government'",
      definition=("Printings of a Boston paragraph of November 1772: 'By letters from Barbados, we learn that it was expected that Sir Francis "
                  "Bernard would be appointed to that government.' A report of an expectation, from letters."),
      role='report', words=25, dateline=True, stop=r'We\W+have\W+(?:A|a)dvice|Tuesday\W+last',
      core=[r'By\W+(?:L|l)etters\W+from\W+Barbad'],
      first="Boston, November 1772: a report that Sir Francis Bernard was expected to be appointed governor of Barbados.",
      what="the Boston report on Sir Francis Bernard and Barbados",
      printings=[k('MS', '11-19', 1), k('NHG', '11-20', 1), k('VG1', '12-10', 2), k('VG2', '12-10', 5)]),
 dict(id='boston-report-dudingston-promoted-captain-1772', kind='message_group',
      label="Boston, November 1772: 'We have advice from England, that Lieutenant Dudingston, who commanded the Gaspee armed schooner that was burnt at Rhode-Island, is promoted to the rank of Captain, by his Majesty's express command'",
      definition=("Printings of a Boston paragraph of November 1772 (dated 12 November in Purdie and Dixon's Virginia Gazette): 'We have advice "
                  "from England, that Lieutenant Dudingston, who commanded the Gaspee armed schooner that was burnt at Rhode-Island, is promoted to "
                  "the rank of Captain, by his Majesty's express command.'"),
      role='report', words=35, dateline=True, stop=r'We\W+hear\W+from\W+Taunton|Tuesday\W+last|Extract',
      core=[r'W\W*E\W+have\W+(?:A|a)dvice\W+from\W+England,?\W+that\W+Lieu'],
      first="Boston, November 1772: a report that the commander of the Gaspee schooner had been promoted to captain.",
      what="the Boston report on the commander of the Gaspee",
      printings=[k('MS', '11-19', 1), k('NHG', '11-20', 1), k('VG1', '12-10', 2), k('VG2', '12-10', 5)]),
 dict(id=PHILA, kind='context_group',
      label="Philadelphia, 11 November 1772: three paragraphs on the frontier, as the papers printed them in November and December",
      definition=("Three paragraphs of a Philadelphia report of 11 November 1772, each printed by every newspaper that survives for its weeks "
                  "and each counted by its own words (C-09): the great Seneca chief's return from a visit to Sir William Johnson; the forts Chartres "
                  "and Pitt destroyed by orders from England; and the frontier inhabitants' petition to the Governor on that subject."),
      children=['philadelphia-report-seneca-chief-from-johnson-hall-1772', 'philadelphia-report-forts-chartres-and-pitt-1772',
                'philadelphia-report-frontier-petition-1772']),
 dict(id='philadelphia-report-seneca-chief-from-johnson-hall-1772', parent=PHILA, kind='message_group',
      label="Philadelphia, 11 November 1772: 'On Saturday last Kayashuta, the great Seneca Chief, returned to this city from Johnson's Hall, where he has been on a visit to Sir William Johnson, of the greatest importance to the colonies'",
      definition=("Printings of a Philadelphia paragraph of 11 November 1772: 'On Saturday last Kayashuta, the great Seneca Chief, returned to "
                  "this city from Johnson's Hall, where he has been on a visit to Sir William Johnson, of the greatest importance to the colonies ...'. "
                  "The papers spell the chief's name in several ways."),
      role='report', words=40, dateline=True, stop=r'The\W+(?:E|e)ntertainment|The\W+(?:F|f)orts?\W+Chartres',
      core=[r'O\W*N\W+Saturday\W+(?:last\W+)?K\w+,?\W+the\W+great\W+Seneca'],
      first="Philadelphia, November 1772: a report that the great Seneca chief had returned from a visit to Sir William Johnson.",
      what="the Philadelphia report of the Seneca chief",
      printings=[k('NHG', '11-27', 2), k('VG1', '12-03', 1), k('VG2', '12-03', 2), k('MS', '12-04', 1)]),
 dict(id='philadelphia-report-forts-chartres-and-pitt-1772', parent=PHILA, kind='message_group',
      label="Philadelphia, 11 November 1772: 'The forts Chartres and Pitt are, by orders from England, destroyed, the barracks levelled to the ground, and abandoned by the garrisons'",
      definition=("Printings of a Philadelphia paragraph of 11 November 1772: 'The forts Chartres and Pitt are, by orders from England, destroyed, "
                  "the barracks levelled to the ground, and abandoned by the garrisons, who are soon expected, as they are on their way for this city.'"),
      role='report', words=35, dateline=True, stop=r'We\W+are\W+assured',
      core=[r'The\W+(?:F|f)orts?\W+Chartres\W+and\W+Pi'],
      first="Philadelphia, November 1772: a report that the forts Chartres and Pitt were destroyed by orders from England.",
      what="the Philadelphia report of the forts",
      printings=[k('NHG', '11-27', 2), k('VG1', '12-03', 1), k('VG2', '12-03', 2), k('MS', '12-04', 1)]),
 dict(id='philadelphia-report-frontier-petition-1772', parent=PHILA, kind='message_group',
      label="Philadelphia, 11 November 1772: 'We are assured the frontier inhabitants of this province have presented the Governor with a petition on that subject'",
      definition=("Printings of a Philadelphia paragraph of 11 November 1772: 'We are assured the frontier inhabitants of this province have "
                  "presented the Governor with a petition on that subject, who has referred them to General Gage, at New-York, but we fear the "
                  "application is without success.' The subject is the forts' abandonment, in the paragraph before."),
      role='report', words=40, dateline=True, stop=r'On\W+Saturday|To\W+Mess|WILLIAMSBURG|FOR\W+THE\W+MASSACHUSETTS',
      core=[r'We\W+are\W+assured\W+the\W+(?:F|f)rontier'],
      first="Philadelphia, November 1772: a report that the frontier inhabitants had petitioned the Governor.",
      what="the Philadelphia report of the frontier petition",
      printings=[k('NHG', '11-27', 2), k('VG1', '12-03', 1), k('VG2', '12-03', 2), k('MS', '12-04', 1)]),
 # ---- chosen: eligible, printed by four of the five papers that survive for its weeks ----
 dict(id='christiansted-report-hurricane-september-1772', kind='message_group',
      label="Christiansted (St. Croix), 4 September 1772: 'On Monday night last blew the most violent hurricane that has ever been known here, or perhaps on any island, in the memory of man'",
      definition=("Printings of a Christiansted (St. Croix) paragraph of 4 September 1772: 'On Monday night last blew the most violent hurricane "
                  "that has ever been known here, or perhaps on any island, in the memory of man. Words are wanting to describe the horrors of the "
                  "night ...'. A report from the island, as the papers reprinted it. Accounts of the same storm from other islands are other texts."),
      role='report', words=38, dateline=True,
      core=[r'O\W*N\W+Monday\W+(?:N|n)ight\W+last,?\W+blew'],
      first="St. Croix, September 1772: a report from Christiansted of a hurricane.",
      what="the Christiansted report of the hurricane",
      printings=[k('SCG', '10-05', 6), k('MS', '10-15', 2), k('VG1', '10-29', 1), k('VG2', '10-29', 1)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797, 1800, 1801 and 1803): "BOSTON, August 12."
# 1772 also takes, after the cross-year check of openings (24 November 2026), a bare date ('Sept. 25.'), a place with 'St.'
# ("ST. JAMES'S, Sept. 1."), a bracketed state or island ('CHRISTIANSTED, [St. Croix] Sept. 4.') and a space before the comma.
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
            problems.append((s['id'], key, 'page not in the 1772 pages'))
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
        r['id'] = f'S72-{n:03}'
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
               'admission_rule': 'Reviewed 1772 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1772/'
    return {
        'ledger_id': 'ledger:stories-1772', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1772', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1772, and of 1771 where they reach the 1772 pages (long-running ones '
                   'included), every item in 3 or more papers counted again by the first 40 words of its opening against every page, papers that '
                   'comparison missed looked for again by their words and their names, and read, a sweep of word-for-word passages shared by 4 or '
                   'more papers for items the families miss, phrase searches on all 675 pages of 1772 in both transcriptions for every admitted and '
                   'chosen item, and scan checks of each admitted passage, by the thin-year rule (Y-THIN as amended on 23 November 2026: an item '
                   'printed by more than half of the newspapers that survive for its weeks, and by at least 4, is eligible; items printed by every '
                   'surviving paper are admitted, the others chosen to cover the months and the kinds of news; single paragraphs from runs of news '
                   'counted by their own words, C-09)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1771.json': 'retrieval_candidates',
                             d+'counted_items.json': 'retrieval_candidates', d+'phrase_patterns.json': 'retrieval_patterns',
                             d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1772.py': 'ledger_code', 'work/archive_data/ledgers/stories_1772_review.json': 'scan_review',
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
