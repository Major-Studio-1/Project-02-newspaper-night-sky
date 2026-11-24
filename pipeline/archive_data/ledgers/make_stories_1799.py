"""Write ledgers/stories_1799.json: reviewed stories of 1799, round one.

1799 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN, as amended on 23 November 2026, the owner's
choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the newspapers that
survive for its weeks (those with a surviving issue between its first and last printing, and at least in the three weeks
from its first printing), and by at least 4; items printed by every newspaper that survives for their weeks are admitted;
the other eligible items are chosen to cover the months and the kinds of news; digests are not admitted. 1799 has ten
catalogue series, which are nine papers: the Gazette of the United States (Philadelphia, a daily, to 20 December), the
Providence Journal, the New Hampshire Gazette and the Portland Gazette (under two numbers) all year, the Kentucky Gazette to
May, the Mirror (Concord), the Virginia Argus (Richmond) and the Eagle (Hanover) in a few issues, and the Republican Ledger
(Portsmouth) from September. Four papers survive from July to the end of August, so an item printed by all four of them
is admitted; in the other weeks five to seven survive. Single paragraphs from runs of news are counted by their own words
(C-09).
The automatic families first printed in 1799 that reach 3 or more papers, and those of 1798 over the 1799 pages,
long-running ones included, were split into single printed items with work/story_items.py --long-running (items.json,
items_from_1798.json); every item in 3 or more papers was counted again by the first 40 words of its opening against
every page of the year (papers the comparison missed were looked for again, by their words and by their names, and the
strong candidates read), and a sweep of word-for-word passages shared by 4 or more papers found items the families miss;
the sweep's passages that no counted item explains were read, and the runs of news that every surviving paper printed were
counted paragraph by paragraph, each by its own opening (textcount.py in the session notes' tools). See
outputs/story_discovery_1799/README.md.

The 1799 pages are those whose issue the data release dates to 1799 (work/year_search_pages.py 1799 ... --printed-dates).

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 25-70 words), starting with its dateline or heading when one
stands directly before it. A paragraph printed in a run of news is counted, and its excerpt cut, by its own opening
sentence. Scan findings, crops and hand-drawn boxes are merged from stories_1799_review.json after the scan check. A
printing on a page whose RevX transcription is filed under another scan page (derived/revx_page_map.parquet), or empty,
takes its excerpt from the CA transcription of its scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied; other years are reviewed at the same time, and the main
session renumbers at release:
    python work/archive_data/ledgers/make_stories_1799.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1799/search_pages.json). The excerpts are cut from
the 1799 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1799'
D = PROJECT/'outputs/story_discovery_1799'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1799_review.json'
OUT = HERE/'stories_1799.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83025881': 'The Gazette of the United States', 'sn83021629': 'The Providence Journal',
         'sn83025588': 'The New Hampshire Gazette', 'sn83045634': 'The Gazette (Portland)', 'sn83016063': "Jenks's Portland Gazette",
         'sn82014782': 'The Kentucky Gazette', 'sn83025525': 'The Mirror', 'sn84023378': 'The Republican Ledger',
         'sn84024710': 'The Virginia Argus', 'sn90062451': 'The Eagle'}
ONE = {'GUS': 'sn83025881', 'PJ': 'sn83021629', 'NHG': 'sn83025588', 'KG': 'sn82014782', 'MIR': 'sn83025525', 'RL': 'sn84023378',
       'VA': 'sn84024710', 'EAG': 'sn90062451'}
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
    """Page key of a printing: paper code, date (MM-DD in 1799), page and edition. The Portland Gazette is filed under two
    numbers: 'The Gazette' to 22 April and 'Jenks's Portland Gazette' from 29 April."""
    lccn = ('sn83045634' if date <= '04-22' else 'sn83016063') if paper == 'PG' else ONE[paper]
    return f'{lccn}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()


def S(id, label, definition, core, first, what, printings, role='report', words=40, dateline=True, back=True, **kw):
    """One story group (a message_group), written compactly. The excerpt starts at the beginning of the sentence that holds
    the core (back=True), then takes the dateline standing directly before it."""
    return dict(id=id, kind='message_group', label=label, definition=definition, role=role, words=words, dateline=dateline,
                back=back, core=core, first=first, what=what, printings=printings, **kw)


RUN0722 = [k('PG', '07-22', 2), k('GUS', '07-22', 3), k('NHG', '07-23', 2), k('PJ', '07-24', 2)]
RUN0826A = [k('PG', '08-26', 2), k('GUS', '08-26', 2), k('NHG', '08-27', 1), k('PJ', '08-28', 1)]
RUN1209 = [k('PG', '12-09', 2), k('GUS', '12-10', 2), k('PJ', '12-11', 1), k('NHG', '12-11', 2), k('RL', '12-11', 2), k('VA', '12-20', 1)]

STORIES = [
 # ---- admitted: printed by every paper that survives for their weeks ----
 S('london-report-paris-papers-to-the-5th-april-1799',
   "London, 9 April 1799: 'Yesterday afternoon we received Paris papers to the 5th inst. which were brought to Dover in a neutral vessel from Calais'",
   ("Printings of a London paragraph of 9 April 1799: 'Yesterday afternoon we received Paris papers to the 5th inst. which were brought to "
    "Dover in a neutral vessel from Calais. On the 26th ult. General Jourdan wrote from his head-quarters ...' (the French army's retreat "
    "in Germany, as the Paris papers gave it). A London report, as the papers reprinted it."),
   [r'Yesterday\W+afternoon\W+we\W+received\W+Paris\W+papers'],
   "London, April 1799: a report of the Paris papers on the French army's retreat in Germany.", "the London report of the Paris papers to 5 April",
   [k('PG', '05-27', 3), k('NHG', '05-28', 2), k('PJ', '05-29', 2), k('GUS', '05-31', 3), k('VA', '06-07', 2)], words=40),
 S('vienna-report-the-surrender-of-peschiera-may-1799',
   "Vienna, May 1799: 'The first Lieutenant of artillery, Wopaterney, sent as courier from General Baron Kray ... brought the agreeable intelligence'",
   ("Printings of a report from a supplement to the Vienna Court Gazette of 11 May 1799, headed 'Surrender of Peschiera': 'The first "
    "Lieutenant of artillery, Wopaterney, sent as courier from General Baron Kray, who was left behind by Fieldmarshal Count Suwarrow, "
    "brought the agreeable intelligence, that, on the 5th ...'. A report from the Vienna Court Gazette, as the papers reprinted it."),
   [r'Surrender\W+of\W+Peschiera', r'sent\W+as\W+courier\W+from\W+General\W+Baron\W+Kray'],
   "Vienna, May 1799: a report of the surrender of Peschiera.", "the Vienna report of the surrender of Peschiera",
   [k('PG', '07-22', 2), k('GUS', '07-22', 2), k('NHG', '07-23', 2), k('PJ', '07-24', 1)], words=40),
 S('verona-report-suwarow-summons-the-citadel-of-milan-may-1799',
   "Verona, 5 May 1799: 'Suwarow has summoned the citadel of Milan to surrender in 24 hours'",
   ("Printings of a paragraph dated Verona, 5 May 1799: 'Suwarow has summoned the citadel of Milan to surrender in 24 hours. The Commandant "
    "answered that he would surrender that place, which has a garrison of 2500 men, on condition of his being permitted to march out with "
    "his troops ...'. A report from Verona, as the London papers gave it and the papers reprinted it."),
   [r'summoned\W+the\W+citadel\W+of\W+Milan'],
   "Verona, May 1799: a report that Suwarow had summoned the citadel of Milan.", "the Verona report on the citadel of Milan",
   RUN0722, words=40),
 S('trent-report-the-russians-in-tortona-may-1799',
   "Trent, 7 May 1799: 'This instant the Imperial Royal Major Marshall has arrived, assuring us that the Russians are in Tortona'",
   ("Printings of a paragraph dated Trent, 7 May 1799: 'This instant the Imperial Royal Major Marshall has arrived, assuring us that the "
    "Russians are in Tortona, and the Austrians in Vercelli—the head quarters are at Pavia. Part of our troops are marching against Genoa, "
    "to facilitate the landing of the allies ...' (the Portland Gazette prints it from 'Part of our troops'). A report from Trent, as the "
    "London papers gave it and the papers reprinted it."),
   [r'This\W+instant\W+the\W+Imperial\W+Royal'],
   "Trent, May 1799: a report that the Russians were in Tortona.", "the Trent report",
   [(k('PG', '07-22', 2), {'core': [r'Part\W+of\W+our\W+troops\W+are\W+marching\W+against\W+Genoa']}), k('GUS', '07-22', 3),
    k('NHG', '07-23', 2), k('PJ', '07-24', 2)], words=40),
 S('vienna-report-naples-taken-by-the-english-may-1799',
   "Vienna, 3 May 1799: 'This moment it is reported here, that the English, in concert with the Neapolitan insurgents, have taken the city of Naples'",
   ("Printings of a paragraph dated Vienna, 3 May 1799: 'This moment it is reported here, that the English, in concert with the Neapolitan "
    "insurgents, have taken the city of Naples after an obstinate action, in which many republican patriots lost their lives ...'. A report "
    "of what was 'reported' at Vienna, as the London papers gave it and the papers reprinted it."),
   [r'This\W+moment\W+it\W+is\W+reported\W+here'],
   "Vienna, May 1799: a report that the English and the Neapolitan insurgents had taken Naples.", "the Vienna report on Naples",
   RUN0722, words=40),
 S('hamburg-report-the-murder-of-the-french-ministers-at-rastadt-may-1799',
   "Hamburg, 22 May 1799: 'Some Continental papers insinuate, the murder of Bonnier, &c. had been contrived by personal enemies, high in office of the Great Republic'",
   ("Printings of a paragraph dated Hamburg, 22 May 1799: 'Some Continental papers insinuate, the murder of Bonnier, &c. had been contrived "
    "by personal enemies, high in office of the Great Republic. By others it is stated ...' (on the killing of the French ministers leaving "
    "Rastadt). A report of what papers said, as the London papers gave it and the papers reprinted it."),
   [r'murder\W+of\W+Bonnier'],
   "Hamburg, May 1799: a report of what papers said of the murder of the French ministers at Rastadt.", "the Hamburg report on the murder at Rastadt",
   RUN0722, words=40),
 S('constantinople-report-buonaparte-s-defeat-near-acre-april-1799',
   "Constantinople, 19 April 1799: 'The intelligence sent under date of the 16th inst. respecting General Buonaparte's defeat ... near St. John d'Acre, is fully confirmed'",
   ("Printings of a paragraph dated Constantinople, 19 April 1799: 'The intelligence sent under date of the 16th inst. respecting General "
    "Buonaparte's defeat by Djezzar Pacha near St. John d'Acre, is fully confirmed. The French General is now retreating with the rest of "
    "his army towards Cairo ...' (the pacha's name as each paper prints it). A report from Constantinople, as the London papers gave it and "
    "the papers reprinted it."),
   [r'intelligence\W+sent\W+under,?\W+date\W+of\W+the\W+16th'],
   "Constantinople, April 1799: a report of Buonaparte's defeat near Acre.", "the Constantinople report on Acre",
   [k('GUS', '07-19', 2), k('PG', '07-22', 2), k('NHG', '07-23', 2), k('PJ', '07-24', 2)], words=40),
 S('boston-report-captain-freeman-s-news-of-the-fleets-july-1799',
   "Boston, July 1799: Captain Freeman, from Malaga: 'the French fleet passed Gibraltar' ... 'Off Gibraltar was boarded from an English sloop of war, commanded by Capt. Moore'",
   ("Printings of a Boston report of mid-July 1799 in two wordings, of the news Captain Freeman brought from Malaga ('Yesterday arrived "
    "Capt. James Freeman, in 53 days from Malaga. He communicates to us the following sketch of intelligence: May 6. The French fleet passed "
    "Gibraltar ...' in the Providence Journal and the Gazette of the United States; 'On Monday Capt. Freeman arrived ... in 35 days from "
    "Malaga ... He informs that the French fleet passed Gibraltar into the Mediterranean, the 6th May ...' in the Portland Gazette and the "
    "New Hampshire Gazette), both with Capt. Moore's word that 'the French and English fleets had engaged'. A shipmaster's report at second "
    "hand, as the papers reprinted it."),
   [r'Yesterday\W+arrived\W+Capt\.?\W+James\W+Freeman', r'Capt\.?\W+Freeman\W+arrived'],
   "Boston, July 1799: a shipmaster's news of the French, English and Spanish fleets.", "the Boston report of Captain Freeman's news",
   [k('PJ', '07-17', 2), k('GUS', '07-20', 3), k('PG', '07-22', 2), k('NHG', '07-23', 2)], words=40),
 S('lisbon-letter-from-mr-leigh-june-1799',
   "Lisbon, 1 June 1799: a letter from Mr. Leigh: 'The Cadiz fleet is said to be put into Carthagena, with damage'",
   ("Printings of an extract of a letter from Mr. Leigh, dated Lisbon, 1 June 1799: 'The Cadiz fleet is said to be put into Carthagena, with "
    "damage; and the French fleet to have anchored in a bay of Majorca, with Earl St. Vincent near at hand ...'. A letter at second hand, "
    "as the papers reprinted it."),
   [r'letter\W+from\W+Mr\.?\W+Leigh', r'Cadiz\W+fleet\W+is\W+said\W+to\W+be\W+put\W+into'],
   "Lisbon, June 1799: a letter on the Cadiz and French fleets.", "the letter from Mr. Leigh",
   [k('NHG', '07-23', 3), k('PJ', '07-24', 2), k('GUS', '07-25', 2), k('PG', '07-29', 2)], words=40),
 S('london-report-the-hamburg-mail-and-the-defeat-of-the-french-in-italy-june-1799',
   "London, 9 June 1799: 'The Hamburg mail of the 31st arrived in town last night by express, and has brought the important intelligence of the total defeat of the French armies in Italy'",
   ("Printings of a London paragraph of 9 June 1799: 'The Hamburg mail of the 31st arrived in town last night by express, and has brought "
    "the important intelligence of the total defeat of the French armies in Italy, the junction of the imperial armies in Switzerland, &c. "
    "...', with 'the official account of the action, published at Milan, by General Suwarow'. A London report, as the papers reprinted it."),
   [r'Hamburgh?\W+Mail\W+of\W+the\W+31st', r'Hamburgh?\W+mail\W+of\W+the\W+3\w*\W+arrived\W+in\W+town'],
   "London, June 1799: a report of the Hamburg mail on the defeat of the French in Italy.", "the London report of the Hamburg mail",
   [k('GUS', '08-06', 2), k('PG', '08-12', 1), k('NHG', '08-13', 3), k('PJ', '08-14', 1)], words=40),
 S('london-report-sweden-joins-the-coalition-june-1799',
   "London, June 1799: 'The King of Sweden, in quality of Duke of Pomerania, has, by his Minister, Baron Bildt, delivered to the Congress of Ratisbon a note'",
   ("Printings of a London paragraph of June 1799: 'The King of Sweden, in quality of Duke of Pomerania, has, by his Minister, Baron Bildt, "
    "delivered to the Congress of Ratisbon a note, informing the co-estates that he had joined the coalition against France ...'. A London "
    "report, as the papers reprinted it."),
   [r'King\W+of\W+Sweden,?\W+in\W+quality\W+of\W+Duke'],
   "London, June 1799: a report that the King of Sweden had joined the coalition.", "the London report on Sweden",
   [k('GUS', '08-06', 2), k('PG', '08-12', 2), k('NHG', '08-13', 3), k('PJ', '08-14', 1)], words=40),
 S('london-report-the-capture-of-genoa-june-1799',
   "London, 10 June 1799: 'The capture of Genoa, by the combined English, Turks, and Russians, has been officially announced by Baron D'Aspres to the Regency of Modena'",
   ("Printings of a London paragraph of 10 June 1799: 'The capture of Genoa, by the combined English, Turks, and Russians, has been officially "
    "announced by Baron D'Aspres to the Regency of Modena. The French have wholly evacuated Rome ...'. A London report, as the papers "
    "reprinted it."),
   [r'capture\W+of\W+Genoa,?\W+by\W+the\W+combined'],
   "London, June 1799: a report that Genoa had been taken.", "the London report on Genoa",
   [k('GUS', '08-06', 2), k('PG', '08-12', 2), k('NHG', '08-13', 3), k('PJ', '08-14', 2)], words=40),
 S('paris-papers-a-rupture-between-the-british-and-tippoo-1799',
   "London, June 1799: 'An article from Bombay, March 21, inserted in the Paris papers, states the probability of an immediate rupture between the British and Tippoo'",
   ("Printings of a London paragraph of June 1799: 'An article from Bombay, March 21, inserted in the Paris papers, states the probability of "
    "an immediate rupture between the British and Tippoo; who, they say, has 100,000 well disciplined troops ...'. A report of what the Paris "
    "papers said, as the London papers gave it and the papers reprinted it."),
   [r'article\W+from\W+Bombay,?\W+March\W+21'],
   "London, June 1799: a report of the Paris papers on the British and Tippoo in India.", "the report on Tippoo",
   [k('GUS', '08-06', 2), k('PG', '08-12', 2), k('NHG', '08-13', 3), k('PJ', '08-14', 1)], words=40),
 S('london-report-a-letter-from-milan-on-the-fate-of-italy-1799',
   "London, June 1799: 'A letter from Milan, of the 15th, states this action to have decided the fate of Italy'",
   ("Printings of a London paragraph of June 1799: 'A letter from Milan, of the 15th, states this action to have decided the fate of Italy. "
    "The Russians on the 14th took Valenza by assault ...'. A report of a letter, as the London papers gave it and the papers reprinted it."),
   [r'letter\W+from\W+Milan,?\W+of\W+the\W+1[45]'],
   "London, June 1799: a report of a letter from Milan on the battle in Italy.", "the report of the letter from Milan",
   [k('GUS', '08-06', 2), k('PG', '08-12', 1), k('NHG', '08-13', 3), k('PJ', '08-14', 1)], words=40),
 S('new-york-report-commercial-news-by-the-boyne-august-1799',
   "New York, August 1799: 'Commercially Important. A gentleman who came passenger in the Boyne, from London, has favoured us with the following'",
   ("Printings of a New York paragraph of 5 August 1799, headed 'Commercially Important': 'A gentleman who came passenger in the Boyne, from "
    "London, has favoured us with the following: All vessels leaving any port in Holland, as well as those bound there, are taken and "
    "carried into England ...'. A passenger's report at second hand, as the papers reprinted it."),
   [r'came\W+passenger\W+in\W+the\W+Boyne'],
   "New York, August 1799: a passenger's report on vessels bound to or from Holland.", "the New York report by the Boyne",
   [k('GUS', '08-06', 3), k('PG', '08-12', 2), k('NHG', '08-13', 3), k('PJ', '08-14', 2)], words=40),
 S('philadelphia-report-news-by-the-dominick-terry-august-1799',
   "Philadelphia, 9 August 1799: 'A gentleman who came passenger in the ship Dominick Terry, from Lisbon, brings the following articles'",
   ("Printings of a Philadelphia paragraph of 9 August 1799: 'A gentleman who came passenger in the ship Dominick Terry, from Lisbon, brings "
    "the following articles, which he says were received at Lisbon by a Portuguese brig of war from Falmouth: Falmouth, June 18 ...'. A "
    "passenger's report at second hand, as the papers reprinted it."),
   [r'passenger\W+in\W+the\W+(?:ship\W+)?Dominick\W+Terry'],
   "Philadelphia, August 1799: a passenger's report of news received at Lisbon.", "the Philadelphia report by the Dominick Terry",
   [k('GUS', '08-09', 3), k('PG', '08-19', 2), k('NHG', '08-20', 2), k('PJ', '08-21', 2)], words=40),
 S('boston-report-the-president-names-fort-independent-august-1799',
   "Boston, August 1799: 'On Wednesday last, the President of the United States visited the fortress in our harbour ... Fort Independent on Castle-Island'",
   ("Printings of a Boston paragraph of early August 1799: 'On Wednesday last, the President of the United States visited the fortress in "
    "our harbour; and under a discharge of 15 guns, pronounced the name it is in future to bear, to be Fort Independent on Castle-Island ...' "
    "(the Providence Journal in its own words). A Boston report, as the papers reprinted it."),
   [r'President\W+of\W+the\W+United\W+States\W+visited\W+the\W+fort'],
   "Boston, August 1799: a report of the President's visit to the fort on Castle Island.", "the Boston report on Fort Independent",
   [k('NHG', '08-06', 3), k('PJ', '08-07', 2), k('GUS', '08-09', 3), k('PG', '08-12', 2)], words=40),
 S('lower-elbe-report-the-vienna-court-gazette-of-19-june-1799',
   "Lower Elbe, 29 June 1799: 'By the Vienna Court Gazette, of June 19th, we learn, That the Archduke Charles was at Klattern, the 9th June'",
   ("Printings of a paragraph dated Lower Elbe, 29 June 1799: 'By the Vienna Court Gazette, of June 19th, we learn, That the Archduke Charles "
    "was at Klattern, the 9th June. He took at Zurich, from which the French had precipitately retreated 94 cannons ...'. A report of the "
    "Vienna Court Gazette, as the London papers gave it and the papers reprinted it."),
   [r'By\W+the\W+Vienna\W+Court\W+Gazette,?\W+of\W+June\W+19'],
   "Lower Elbe, June 1799: a report of the Vienna Court Gazette on the Archduke in Switzerland.", "the Lower Elbe report of 29 June",
   RUN0826A, words=40),
 S('frontiers-of-swabia-report-the-archduke-at-kloten-june-1799',
   "Frontiers of Swabia, 16 June 1799: 'The Archduke's head quarters were at Kloten, the 13th'",
   ("Printings of a paragraph dated Frontiers of Swabia, 16 June 1799: 'The Archduke's head quarters were at Kloten, the 13th.—He intends "
    "giving a few days rest to his brave army ...'. A report from the frontiers of Swabia, as the London papers gave it and the papers "
    "reprinted it."),
   [r'Archduke.s\W+head\W*-?\W*quarters\W+were\W+at\W+Kloten'],
   "Frontiers of Swabia, June 1799: a report on the Archduke's army.", "the report from the frontiers of Swabia",
   RUN0826A, words=40),
 S('vienna-report-the-archduke-before-zurich-june-1799',
   "Vienna, 12 June 1799: 'On the 4th, 5th and 6th inst. the Archduke attacked the French in front of their strong intrenched camp in the van of Zurich'",
   ("Printings of a paragraph dated Vienna, 12 June 1799: 'On the 4th, 5th and 6th inst. the Archduke attacked the French in front of their "
    "strong intrenched camp in the van of Zurich. The combat was long, obstinate, and bloody ...'. A report from Vienna, as the London papers "
    "gave it and the papers reprinted it."),
   [r'On\W+the\W+4th,?\W+5th,?\W+and\W+6th', r'Archduke\W+attacked\W+the\W+French\W+in\W+front'],
   "Vienna, June 1799: a report of the Archduke's attack before Zurich.", "the Vienna report of 12 June",
   RUN0826A, words=40),
 S('milan-report-bellegarde-gone-to-piedmont-june-1799',
   "Milan, 10 June 1799: 'Gen. Bellegarde is gone to Piedmont, from whence he will march against Acqui'",
   ("Printings of a paragraph dated Milan, 10 June 1799: 'Gen. Bellegarde is gone to Piedmont, from whence he will march against Acqui, with "
    "12,000, and penetrate the Genoese country on that side ...'. A report from Milan, as the London papers gave it and the papers "
    "reprinted it."),
   [r'Gen\.?\W+Bellegarde\W+(?:is|has)\W+gone\W+to\W+Piedmont', r'Bellegarde\W+(?:is|has)\W+gone\W+to\W+Piedmont'],
   "Milan, June 1799: a report on the Austrian generals' marches.", "the Milan report of 10 June",
   RUN0826A, words=40),
 S('report-hohenzollern-near-modena-june-1799',
   "June 1799: 'The 11th Gen. Hohenzollern succeeded in repulsing a French corps of 8000 French, who approached Modena'",
   ("Printings of a paragraph dated 15 June 1799, in the run from Milan: 'The 11th Gen. Hohenzollern succeeded in repulsing a French corps of "
    "8000 French, who approached Modena, and took 800 prisoners. But Gen. Macdonald's army of 30,000 appearing, the Austrian Gen. retired to "
    "the Po ...'. A report from Italy, as the London papers gave it and the papers reprinted it."),
   [r'The\W+\w+\W+Gen\.?\W+Hohen\W*zoll'],
   "Italy, June 1799: a report of a fight near Modena.", "the report on Hohenzollern near Modena",
   RUN0826A, words=40),
 S('roveredo-report-macdonald-marches-to-join-moreau-june-1799',
   "Roveredo, 14 June 1799: 'General Macdonald has marched from Pontremoli and Sarzana towards Genoa to join Moreau'",
   ("Printings of a paragraph dated Roveredo, 14 June 1799: 'General Macdonald has marched from Pontremoli and Sarzana towards Genoa to join "
    "Moreau. Gen. Suwarrow will break out in forced marches ... and another battle will be decisive of the fate of Italy ...' (the Portland "
    "Gazette dates it 18 June and prints it from 'Gen. Suwarrow will break out'). A report from Roveredo, as the London papers gave it and "
    "the papers reprinted it."),
   [r'Gen(?:eral|\.)?\W+Macdonald\W+has\W+marched\W+from\W+Pontremoli', r'Macdonald\W+has\W+marched\W+from\W+Pontremoli'],
   "Roveredo, June 1799: a report on the marches of Macdonald and Suwarow.", "the Roveredo report",
   [(k('PG', '08-26', 2), {'core': [r'Gen\.?\W+Suwar\W*row\W+will\W+break', r'Suwar\W*row\W+will\W+break\W*-?\W*out']}), k('GUS', '08-26', 2), k('NHG', '08-27', 1), k('PJ', '08-28', 1)], words=40),
 S('vienna-report-count-melas-writes-june-1799',
   "Vienna, 19 June 1799: 'Count Melas writes, that General Moreau had retreated, and taken a position near Savona'",
   ("Printings of a paragraph dated Vienna, 19 June 1799: 'Count Melas writes, that General Moreau had retreated, and taken a position near "
    "Savona, in the Gulf of Genoa, which enabled him to wait his reinforcement ...'. "
    "A report from Vienna, as the London papers gave it and the papers reprinted it."),
   [r'Count\W+Melas\W+writes'],
   "Vienna, June 1799: a report of what Count Melas wrote on Moreau's retreat.", "the Vienna report of Count Melas's letter",
   RUN0826A, words=40),
 S('vienna-report-the-junction-of-macdonald-with-moreau-june-1799',
   "Vienna, 19 June 1799: 'Gen. Macdonald having entered the defiles of the mountains on the sea-coast, ... the accounts of his junction with Moreau are no longer doubted'",
   ("Printings of a paragraph dated Vienna, 19 June 1799, headed 'Junction of Macdonald with Moreau': 'Gen. Macdonald having entered the "
    "defiles of the mountains on the sea-coast, his march through upper Italy, the accounts of his junction with Moreau are no longer "
    "doubted ...'. A report from Vienna, as the London papers gave it and the papers reprinted it."),
   [r'Gen\.?\W+Macdo\W*nald\W+having\W+entered', r'Macdo\W*nald\W+having\W+entered\W+the\W+defile'],
   "Vienna, June 1799: a report on the junction of Macdonald with Moreau.", "the Vienna report on Macdonald's junction",
   [k('PG', '08-26', 2), k('GUS', '08-26', 2), k('NHG', '08-27', 1), k('PJ', '08-28', 2)], words=40),
 S('paris-report-the-councils-and-the-directory-june-1799',
   "Paris, 18 June 1799: 'In the Councils of 500 and Ancients, Briot and Savery expressed their astonishment at the neglect of the Directory'",
   ("Printings of a paragraph dated Paris, 18 June 1799: 'In the Councils of 500 and Ancients, Briot and Savery expressed their astonishment "
    "at the neglect of the Directory to reply to the message of the legislative assemblies ...' (the change of Directors in June). A report "
    "from Paris, as the London papers gave it and the papers reprinted it."),
   [r'Briot\W+and\W+Sa\W*v[ae]ry\W+expre(?:ss|fl)ed'],
   "Paris, June 1799: a report of the Councils and the Directory.", "the Paris report of 18 June",
   [k('PG', '08-26', 1), k('GUS', '08-26', 2), k('NHG', '08-27', 1), k('PJ', '08-28', 2)], words=40),
 S('milan-report-what-the-french-left-in-a-vault-june-1799',
   "Milan, 3 June 1799: 'In a magazine in this city, the Austrians have found in a vault, the following effects, which the French were not able to carry away with them'",
   ("Printings of a paragraph dated Milan, 3 June 1799: 'In a magazine in this city, the Austrians have found in a vault, the following "
    "effects, which the French were not able to carry away with them: 1. A great many chests with valuable paintings, from Rome ...'. A "
    "report from Milan, as the London papers gave it and the papers reprinted it."),
   [r'In\W+a\W+magazine\W+in\W+this\W+city'],
   "Milan, June 1799: a report of goods found in a vault.", "the Milan report of 3 June",
   [k('PG', '08-26', 1), k('GUS', '08-26', 3), k('NHG', '08-27', 1), k('PJ', '08-28', 2)], words=40),
 S('milan-report-general-vukassovich-s-letter-from-ceva-june-1799',
   "Milan, 7 June 1799: 'The following letter has been received here from General Vukassovich: Ceva, June 4. I have this day entered Ceva'",
   ("Printings of a paragraph dated Milan, 7 June 1799: 'The following letter has been received here from General Vukassovich: Ceva, June 4. "
    "I have this day entered Ceva, where I made prisoners 1800 Frenchmen, and the wives of Generals Moreau and Fiorella ...'. A general's "
    "letter at second hand, as the London papers gave it and the papers reprinted it."),
   [r'following\W+let\W*ter\W+has\W+been\W+received\W+here\W+from\W+Gen'],
   "Milan, June 1799: a general's letter from Ceva.", "the Milan report of the letter from Ceva",
   [k('PG', '08-26', 2), k('GUS', '08-26', 3), k('NHG', '08-27', 1), k('PJ', '08-28', 2)], words=40),
 S('hamburgh-report-the-british-force-in-the-mediterranean-june-1799',
   "Hamburgh, June 1799: 'The British force now in the Mediterranean, consists of fifty-eight sail of the line'",
   ("Printings of a paragraph of June 1799: 'The British force now in the Mediterranean, consists of FIFTY-EIGHT sail of the line.—The Turks, "
    "Russians and Neapolitans make the combined forces 73.—The French and Spaniards have SIXTY-THREE sail of the line ...'. A report, as "
    "the London papers gave it and the papers reprinted it."),
   [r'British\W+force\W+no\W*w\W+in\W+the\W+M\w*d\w*t'],
   "June 1799: a report of the fleets in the Mediterranean.", "the report of the fleets in the Mediterranean",
   [k('PG', '08-26', 1), k('GUS', '08-26', 3), k('NHG', '08-27', 2), k('PJ', '08-28', 2)], words=40),
 S('hamburg-report-the-english-blockade-the-north-sea-ports-june-1799',
   "Hamburg, 29 June 1799: 'The English have closely blockaded all the ports of the North Seas'",
   ("Printings of a paragraph dated Hamburg, 29 June 1799: 'The English have closely blockaded all the ports of the North Seas. The Court of "
    "Prussia is said to have refused the French Republic a passage for 10,000 horses through the line of demarcation ...'. A report from "
    "Hamburg, as the London papers gave it and the papers reprinted it."),
   [r'English\W+have\W+closely\W+blockaded'],
   "Hamburg, June 1799: a report of the blockade of the North Sea ports.", "the Hamburg report of 29 June",
   [k('PG', '08-26', 1), k('GUS', '08-26', 3), k('NHG', '08-27', 2), k('PJ', '08-28', 2)], words=40),
 S('modena-report-an-imperial-mandate-to-the-jews-june-1799',
   "Modena, 2 June 1799: 'A severe Imperial mandate has been addressed to the Jews, with injunction to restore within the space of three days all the church plate'",
   ("Printings of a paragraph dated Modena, 2 June 1799: 'A severe Imperial mandate has been addressed to the Jews, with injunction to "
    "restore within the space of three days all the church plate, relics, statues of saints, &c. which they bought of the French, while the "
    "latter were masters of this country ...'. A report from Modena of an Imperial order, as the London papers gave it and the papers "
    "reprinted it."),
   [r'Imperial\W+mandate\W+has\W+been', r'impe\W*rial\W+mandate'],
   "Modena, June 1799: a report of an Imperial order to the Jews of the city to restore church property bought from the French.", "the Modena report",
   [k('PG', '08-26', 2), k('GUS', '08-26', 3), k('NHG', '08-27', 2), k('PJ', '08-28', 2)], words=40),
 S('report-buonaparte-wounded-and-egypt-lost-to-france-1799',
   "1799: 'General Buonaparte we learn to have been wounded, though not mortally. He is said to have left only 1000 Frenchmen in Egypt'",
   ("Printings of a paragraph of the summer of 1799: 'General Buonaparte we learn to have been wounded, though not mortally. He is said to "
    "have left only 1000 Frenchmen in Egypt, exclusive of the Copts and the Algerines; so that this country may now be considered lost to "
    "France. The entire loss of the French before Acre ...' (in the Portland Gazette and the New Hampshire Gazette, after a handbill dated "
    "Piacenza, 23 June). A report of what was learned, as the papers reprinted it."),
   [r'Gen(?:eral|\.)?\W+Buonaparte,?\W+we\W+learn', r'Buonaparte,?\W+we\W+learn,?\W+(?:to\W+have\W+been|has\W+been)\W+wounded'],
   "Summer 1799: a report that Buonaparte had been wounded and had left few Frenchmen in Egypt.", "the report on Buonaparte and Egypt",
   [k('PG', '09-09', 2), k('NHG', '09-10', 2), k('PJ', '09-11', 2), k('GUS', '09-13', 2), k('RL', '09-26', 2)], words=40),
 S('report-the-evacuation-of-leghorn-1799',
   "1799: 'This mail has brought us the particulars of the evacuation of Leghorn by the French'",
   ("Printings of a short London paragraph of 1799: 'This mail has brought us the particulars of the evacuation of Leghorn by the French. "
    "The French Minister who fled by sea in an American vessel, was taken by one of our cruisers.' A London report, as the papers reprinted "
    "it."),
   [r'particulars\W+of\W+the\W+evacuation\W+of\W+Le\W*g?\W*horn'],
   "1799: a report of the French evacuation of Leghorn.", "the report on Leghorn",
   [k('PG', '09-30', 2), k('NHG', '10-01', 2), k('PJ', '10-02', 4), k('GUS', '10-02', 3)], words=25, stop=r'Secretary\W+PICKERING'),
 S('zurich-dispatch-the-two-armies-totally-destroyed-september-1799',
   "Zurich, 28 September 1799: a dispatch: 'The two armies, Russian and Austrian, are totally destroyed'",
   ("Printings of a dispatch dated head-quarters, Zurich, 28 September 1799: 'The two armies, Russian and Austrian, are totally destroyed. "
    "The Russians have passed the Thur. We are in pursuit of the remains of the Austrian and Bavarian corps ...' (a French general's "
    "report to the Executive Directory). A dispatch at second hand, as the papers reprinted it."),
   [r'two\W+armies,?\W+Russian\W+and\W+Austrian,?\W+are\W+totally\W+destroyed'],
   "Zurich, September 1799: a French dispatch on the battle at Zurich.", "the dispatch from Zurich",
   [k('PG', '12-02', 3), k('PJ', '12-11', 3), k('NHG', '12-11', 3), k('RL', '12-11', 2), k('GUS', '12-12', 2), k('VA', '12-20', 3)], words=40),
 S('lindau-report-the-bridge-over-the-rhine-september-1799',
   "Lindau, 29 September 1799: 'The bridge over the Rhine, which was taken up yesterday morning, will be thrown over to night'",
   ("Printings of a paragraph dated Lindau, on Lake Constance, 29 September 1799: 'The bridge over the Rhine, which was taken up yesterday "
    "morning, will be thrown over to night, and the corps of Gen. Petrarsch ...' (so the papers print the name). A report from Lindau, as the papers reprinted it."),
   [r'bridge\W+over\W+the\W+Rhine,?\W+which\W+was\W+taken\W+up'],
   "Lindau, September 1799: a report on the Austrian corps on the Rhine.", "the Lindau report",
   RUN1209, words=40),
 S('donaueschingen-report-the-austrians-advancing-october-1799',
   "Donaueschingen, 1 October 1799: 'The Austrians are advancing from Feldkirch'",
   ("Printings of a paragraph dated Donaueschingen, Swabia, 1 October 1799: 'The Austrians are advancing from Feldkirch. The Austrian Col. "
    "Lauser, has attacked the French in Glaris, beaten them, and taken 1500 prisoners, and two standards ...'. A report from "
    "Donaueschingen, as the papers reprinted it."),
   [r'Austrians\W+are\W+advancing\W+from\W+Feldkirch'],
   "Donaueschingen, October 1799: a report of the Austrians advancing in Switzerland.", "the Donaueschingen report",
   RUN1209, words=40),
 # ---- chosen: eligible, to cover the months and the kinds of news ----
 S('secretary-of-state-s-report-on-france-january-1799',
   "Philadelphia, January 1799: the Secretary of State's report: 'The Secretary of State respectfully submits the following report on the transactions relating to the United States and France'",
   ("Printings of the report of the Secretary of State, Timothy Pickering, to the President, laid before Congress on 21 January 1799: 'The "
    "Secretary of State respectfully submits the following report on the transactions relating to the United States and France, since the "
    "last communications to Congress on that subject ...'. A published state paper, as the papers printed it, most of them in parts over "
    "several issues."),
   [r'Secretary\W+of\W+State\W+respectfully\W+submits'],
   "Philadelphia, January 1799: the Secretary of State's report on relations with France.", "the Secretary of State's report on France",
   [k('GUS', '01-23', 2), k('PJ', '02-06', 1), k('NHG', '02-13', 2), k('PG', '02-18', 1), k('MIR', '03-11', 1)], role='published_document', words=40),
 S('report-the-president-nominates-a-minister-to-france-february-1799',
   "Philadelphia, 19 February 1799: 'The President yesterday sent a message to the Senate' ... on sending another minister to France",
   ("Printings of a Philadelphia paragraph of 19 February 1799 in two wordings: 'The President yesterday sent a message to the Senate, in "
    "which he informed them, that he continued faithful to his declaration never to send another Minister to France, unless he had "
    "assurances of his being received ...' and 'We have it in our power to state that the President yesterday sent a message to the Senate, "
    "in which he informed that body, that it had been and still was his determination ...' (on his nomination of a minister to France). "
    "A report of a message to the Senate, as the papers reprinted it."),
   [r'We\W+have\W+it\W+in\W+our\W+power\W+to\W+state\W+that\W+the\W+President', r'The\W+President\W+yesterday\W+sent\W+a\W+message\W+to\W+the\W+Senate'],
   "Philadelphia, February 1799: a report of the President's message nominating a minister to France.", "the report of the President's nomination",
   [(k('PJ', '02-27', 3), {'core': [r'happy\W+to\W+have\W+it\W+in\W+ou\w\W+power\W+to']}), k('VA', '03-01', 3), k('MIR', '03-04', 3), k('PG', '03-04', 3), k('NHG', '03-06', 2), k('KG', '03-28', 2)], words=40),
 S('president-s-proclamation-on-the-insurrection-in-pennsylvania-march-1799',
   "Philadelphia, 12 March 1799: the President's proclamation: 'Whereas combinations to defeat the execution of the laws for the valuation of lands and dwelling houses within the United States, have existed'",
   ("Printings of the President's proclamation of 12 March 1799: 'Whereas combinations to defeat the execution of the laws for the "
    "valuation of lands and dwelling houses within the United States, have existed in the counties of Northampton, Montgomery and Bucks, in "
    "the State of Pennsylvania ...', commanding the insurgents to disperse. A published proclamation, as the papers printed it; the Gazette "
    "of the United States printed it in two issues."),
   [r'combinations\W+to\W+defeat\W+the\W+execution\W+of\W+the\W+laws'],
   "Philadelphia, March 1799: the President's proclamation on the insurrection in three counties of Pennsylvania.", "the President's proclamation of 12 March",
   [k('GUS', '03-13', 3), k('GUS', '03-14', 3), k('PG', '03-25', 2), k('PJ', '03-27', 1), k('NHG', '03-27', 2)],
   role='published_document', words=40),
 S('captain-truxtun-s-letter-on-the-capture-of-the-insurgente-february-1799',
   "February 1799: an extract of a letter from Captain Thomas Truxtun to the Secretary of the Navy, on board the Constellation",
   ("Printings of an extract of a letter from Captain Thomas Truxtun to the Secretary of the Navy, dated on board the United States ship "
    "Constellation, February 1799, published in March as 'the official account of the capture of L'Insurgente French frigate' (the name as "
    "each paper prints it). A naval officer's letter, as the papers printed it."),
   [r'letter\W+from\W+Capt(?:ain|\.)?\W+THOMAS\W+TRUXT'],
   "February 1799: a naval captain's letter on the capture of a French frigate.", "Captain Truxtun's letter",
   [k('GUS', '03-14', 3), k('PJ', '03-20', 3), k('PG', '03-25', 2), k('NHG', '03-27', 2), k('MIR', '04-01', 2)], words=40),
 S('captain-murray-s-letter-from-the-montezuma-march-1799',
   "March 1799: an extract of a letter from Captain Alexander Murray, on board the ship of war Montezuma, to the Secretary of the Navy",
   ("Printings of an extract of a letter from Captain Alexander Murray to the Secretary of the Navy, dated on board the ship of war "
    "Montezuma, 9 March 1799, on a French brig he had taken ('Capt. Mallet, pierced for 16 guns'). A naval officer's letter, as the "
    "papers printed it."),
   [r'letter\W+from\W+Capt\.?\W+(?:A\.|ALEXANDER)\W+MURRAY'],
   "March 1799: a naval captain's letter on the capture of a French brig.", "Captain Murray's letter",
   [k('GUS', '04-08', 2), k('MIR', '04-22', 3), k('PG', '04-22', 3), k('NHG', '04-23', 2)], words=40),
 S('fort-washington-report-from-detroit-may-1799',
   "Fort Washington, 15 May 1799: '[Official.] By a letter dated the 4th of May, '99, I am informed from Col. David Strong, commanding at Detroit'",
   ("Printings of a paragraph dated Fort Washington, 15 May 1799, marked official: 'By a letter dated the 4th of May, '99, I am informed from "
    "Col. David Strong, commanding at Detroit, that there is a report of a body of Indians ...'. An officer's report at second hand, as the "
    "papers printed it."),
   [r'BY\W+a\W+letter\W+dated\W+(?:the\W+)?4th\W+of\W+May'],
   "Fort Washington, May 1799: an official report of a rumour from Detroit.", "the report from Fort Washington",
   [k('GUS', '06-24', 2), k('NHG', '07-02', 3), k('PG', '07-08', 1), k('MIR', '07-08', 3)], words=40),
 S('havana-circular-on-the-admission-of-neutrals-october-1799',
   "New York, 9 November 1799: a circular letter from the American consul at Havana: 'I hasten to inform you, that a decree was yesterday passed ... for the admission of neutrals'",
   ("Printings of a circular letter of the American consulate at Havana of 18 October 1799: 'I hasten to inform you, that a decree was "
    "yesterday passed by the government of this island, for the admission of neutrals ...', under the heading of the Custom-House at New "
    "York (9 November) in three papers and of New York news in the Portland Gazette. A published notice, as the papers printed it."),
   [r'Copy\W+of\W+a\W+circular\W+letter\W+received', r'Consulate\W+of\W+the\W+Havann'],
   "Havana, October 1799: the American consul's circular on the admission of neutral vessels.", "the Havana circular",
   [k('GUS', '11-12', 3), k('PJ', '11-20', 2), k('RL', '11-20', 3), k('PG', '11-25', 2)], role='published_document', words=40),
 S('president-s-speech-to-congress-december-1799',
   "Philadelphia, 3 December 1799: the President's speech: 'It is with peculiar satisfaction, that I meet the Sixth Congress of the United States of America'",
   ("Printings of the President's speech to both Houses of Congress of 3 December 1799: 'Gentlemen of the Senate, and Gentlemen of the House of "
    "Representatives, It is with peculiar satisfaction, that I meet the Sixth Congress of the United States of America ...'. A published "
    "speech, as the papers printed it."),
   [r'IT\W+is\W+with\W+peculiar\W+satisfaction', r'peculiar\W+satisfaction,?\W+that\W+I\W+meet\W+the\W+Sixth\W+Congress'],
   "Philadelphia, December 1799: the President's speech opening the Sixth Congress.", "the President's speech of 3 December",
   [k('PJ', '12-11', 3), k('PG', '12-16', 1), k('NHG', '12-18', 2), k('RL', '12-18', 2)], role='published_document', words=40),
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
            problems.append((s['id'], key, 'page not in the 1799 pages'))
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
        r['id'] = f'S99-{n:03}'
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
               'admission_rule': 'Reviewed 1799 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1799/'
    return {
        'ledger_id': 'ledger:stories-1799', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1799', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1799, and of 1798 where they reach the 1799 pages (long-running ones '
                   'included), every item in 3 or more papers counted again by the first 40 words of its opening against every page in both '
                   'transcriptions, papers that comparison missed looked for again by their words and their names and the strong candidates read, '
                   'a sweep of word-for-word passages shared by 4 or more papers for items the families miss (its passages that no counted item '
                   'explains read), the runs of news printed by every surviving paper counted paragraph by paragraph, each by its own opening, '
                   'and scan checks of each admitted and chosen passage, by the thin-year rule (Y-THIN as amended on 23 November 2026: an item '
                   'printed by more than half of the newspapers that survive for its weeks, and by at least 4, is eligible; items printed by every '
                   'surviving paper are admitted, the others chosen to cover the months and the kinds of news; single paragraphs from runs of news '
                   'counted by their own words, C-09)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1798.json': 'retrieval_candidates',
                             d+'counted_items.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1799.py': 'ledger_code', 'work/archive_data/ledgers/stories_1799_review.json': 'scan_review',
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
