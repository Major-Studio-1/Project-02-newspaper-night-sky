"""Write ledgers/stories_1783.json: reviewed stories of 1783, round one.

1783 is a thin year: no item of 1783 reaches 7 papers, so it is read by the thin-year rule (docs/rules-and-exceptions.md,
Y-THIN, as amended on 23 November 2026, the owner's choice B1): an item, counted by its own words, is eligible when it was
printed by more than half of the newspapers that survive for its weeks (those with a surviving issue between its first and
its last printing, and at least in the three weeks from its first printing), and by at least 4; as in R-01, the items
printed by every newspaper that survives for their weeks are admitted, and the other eligible items are chosen to cover the
months and the kinds of news, about as many stories as a standard year; one affair's items are treated as in X-1800-01;
digests are not admitted. In 1783 4 to 7 papers survive for most items' weeks (4 for most of the year: the Pennsylvania
Packet, the New-Hampshire Gazette, the Connecticut Courant and the New-Jersey Gazette), so every eligible item is in 4 or
more papers.
The automatic families first printed in 1783 that reach 3 or more papers, long-running ones included, were split into
single printed items with work/story_items.py --long-running (items.json), and again with year 1782 over the 1783 pages
(items_from_1782.json); every item in 3 or more papers was compared by machine with every page and counted again by its
opening, a sweep of word-for-word passages shared by 4 or more papers found short items the families miss, and the
admitted and chosen items were counted with phrase searches over all 1,100 pages of 1783 in both transcriptions. See
outputs/story_discovery_1783/README.md and count_1783.md.

The 1783 pages are those whose issue the data release dates to 1783 (work/year_search_pages.py 1783 ... --printed-dates);
no 1783 issue has a corrected date. 1783 has 9 catalogue series, which are 9 papers: the Pennsylvania Packet (Philadelphia,
122 issues to 11 October), the New-Hampshire Gazette (Portsmouth, 51), the Connecticut Courant (Hartford, 41), the
New-Jersey Gazette (Burlington, 29), the Gazette of the State of South-Carolina (Charleston, 21, from 16 July), the
New-Jersey Journal (Chatham, 4, January to April) and three Charleston papers with a few issues in April and May.
The release's map of misfiled RevX pages (derived/revx_page_map.parquet) lists no page of 1783.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1783_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (reviews of other years run at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1783.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1783/search_pages.json). The excerpts are cut from
the 1783 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1783'
D = PROJECT/'outputs/story_discovery_1783'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1783_review.json'
OUT = HERE/'stories_1783.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83021127': 'The Pennsylvania Packet', 'sn83025585': 'The New-Hampshire Gazette', 'sn84023855': 'The Connecticut Courant',
         'sn83025471': 'The New-Jersey Gazette', 'sn84026945': 'The Gazette of the State of South-Carolina', 'sn84026485': 'The New-Jersey Journal',
         'sn84045495': 'The South-Carolina Weekly Gazette', 'sn83025790': 'The South-Carolina and American General Gazette',
         'sn84024758': 'The South-Carolina Gazette and General Advertiser'}
ONE = {'PP': 'sn83021127', 'NHG': 'sn83025585', 'CC': 'sn84023855', 'NJG': 'sn83025471', 'SCG': 'sn84026945', 'NJJ': 'sn84026485',
       'SCWG': 'sn84045495', 'SCAG': 'sn83025790', 'SCGA': 'sn84024758'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1783), page and edition."""
    return f'{ONE[paper]}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release (none in 1783)."""
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
STORIES = [
 # ---- January and February: letters and news of the last months of the war, and the first news of the peace ----
 dict(id='general-clark-letter-on-the-expedition-from-the-ohio-november-1782', kind='document_group',
      label="Richmond, December 1782: an extract of a letter from General Clark, dated Lincoln, 27 November 1782, on his expedition from the Ohio",
      definition="Printings of an extract of a letter from General Clark, dated Lincoln, 27 November 1782, that the papers print from Richmond, 28 December: 'We left the Ohio the 4th inst. with 1050 men, surprised the principal Shawanese town on the evening of the 10th, and immediately detached parties to different quarters; in a few hours afterwards two thirds of their towns were laid in ashes, and every thing they were possessed of destroyed'. General Clark's own account of his expedition against the Shawnee towns, as the papers print it.",
      role='published_document', words=60, dateline=True,
      head=r'E\s?XTRACT\s+of\s+a\s+[Ll]etter\s+from\s+Gen(?:eral|\.)\s+Clarke?,?\s+dated\s+Lincoln,?\s+Nov(?:ember|\.)\s+[12]7,?\s*1782\.?\s*[\"“]?\s*',
      core=[r'[\"“]?\s*W\s?E\s+left\s+the\s+Ohio,?\s+the\s+4th'],
      first="General Clark writes on 27 November 1782 that his force left the Ohio and 'surprised the principal Shawanese town'.",
      what="General Clark's letter",
      printings=[k('PP', '01-07', 2), k('NJG', '01-15', 2), k('CC', '01-21', 2), k('NHG', '02-01', 1)]),
 dict(id='mr-miller-late-printer-of-the-london-evening-post-arrives-january-1783', kind='message_group',
      label="Philadelphia, January 1783: 'In the Ostend cutter, which arrived at Baltimore on Wednesday last, came passenger Mr. Miller, late printer of the London Evening Post'",
      definition="Printings of a Philadelphia paragraph of 14 January 1783: 'In the Ostend cutter, which arrived at Baltimore on Wednesday last, came passenger Mr. Miller, late printer of the London Evening Post, and also of the London Courant, who for these fifteen years past, has so freely exercised the liberty of the press, to the advantage of his country and honour to himself; but particularly in asserting and defending the cause of America.' A Philadelphia paper's report.",
      role='report', words=50, dateline=True,
      core=[r'(?:I\s?N|In)\s+the\s+Ostend\s+cutter,?\s+which\s+arrived\s+at\s+Baltimore'],
      first="Mr. Miller, late printer of the London Evening Post, arrives at Baltimore in the Ostend cutter.",
      what="the Philadelphia report of Mr. Miller's arrival",
      printings=[k('PP', '01-14', 3), k('NJG', '01-22', 2), k('CC', '01-28', 2), k('NHG', '02-01', 2)]),
 dict(id='paris-the-negotiations-for-peace-seem-to-be-broken-up-october-1782', kind='message_group',
      label="Paris news of 24 October 1782: 'The negotiations for peace seem to be broken up'",
      definition="Printings of a paragraph of the Paris news, dated 24 October 1782: 'The negotiations for peace seem to be broken up; the propositions made on the part of the court of London, in the conferences which have been opened, are rejected. The contents of these propositions are not mentioned.' A paragraph of the European news, printed in January and February 1783.",
      role='report', words=40, dateline=True, stop=r'\sOct(?:ober|\.)\s+25\.',
      core=[r'(?:T\s?HE|The)\s+negotiations\s+for\s+peace,?\s+seem\s+to\s+be\s+broken\s+up'],
      first="Paris, 24 October 1782: the negotiations for peace 'seem to be broken up', the propositions of the court of London rejected.",
      what="the Paris paragraph on the negotiations for peace",
      printings=[k('PP', '01-14', 1), k('NJG', '01-29', 1), k('CC', '02-04', 1), k('NHG', '02-08', 2)]),
 dict(id='london-evening-post-statement-of-the-jamaica-fleet-of-july-1782', kind='message_group',
      label="The London Evening Post's statement of the fleet that sailed from Jamaica on 25 July 1782 under convoy of the Ramillies",
      definition="Printings of a paragraph from the London Evening Post of 12 November 1782: 'The London Evening Post of the 12th of November last, contains the following statement of the fleet which sailed from Jamaica on the 25th of July, under convoy of the Ramilies, and several other men of war'; the statement counts the merchant ships (arrived 62, taken 15, foundered 9, missing 14, retaken 2, put back 1) and gives the state of each ship of the convoy ('Ramilies 74, Quitted by her people, and burnt on the 21st of September'). A London paper's statement, printed at second hand.",
      role='report', words=50, dateline=True,
      core=[r'(?:T\s?HE|The)\s+London\s+Evening\s+Post\s+of\s+the\s+12th\s+of\s+November'],
      first="The London Evening Post's statement of the Jamaica fleet of 25 July 1782: of 103 merchant ships, 62 arrived and 15 were taken.",
      what="the statement of the Jamaica fleet",
      printings=[k('PP', '01-14', 3), k('NJG', '01-22', 2), k('CC', '01-28', 3),
                 (k('NHG', '02-01', 3), {'core': [r'State\s+of\s+the\s+ships\s+that\s+were\s+convoy\s+to\s+the\s+Jamaica\s+fleet'], 'note': "Prints the state of the ships of the convoy, 'as taken from the London evening post, of Nov. 12', without the statement of the merchant ships (counted with it, C-02)."})]),
 dict(id='major-burnet-arrives-with-general-greenes-dispatches-january-1783', kind='message_group',
      label="Philadelphia, January 1783: Major Burnet arrives from Charleston with General Greene's dispatches on the evacuation of the town",
      definition="Printings of a Philadelphia paragraph of 16 January 1783: 'On Tuesday evening major Burnet, aide-camp to the honourable major general Greene, arrived here, in twenty-one days from Charlestown, with dispatches from the General; of which the following is an extract', and the extract of General Greene's letter to the president of Congress, dated headquarters, 19 December 1782: 'I have the honour to communicate to your excellency the agreeable information of the evacuation of Charlestown'. A Philadelphia paper's report, with the general's own letter.",
      role='report', words=60, dateline=True,
      core=[r'(?:O\s?N|On)\s+Tuesday\s+evening,?\s+(?:last,?\s+)?[Mm]ajor\s+Burnet'],
      first="Major Burnet arrives at Philadelphia with General Greene's letter of 19 December 1782 on the evacuation of Charleston.",
      what="the Philadelphia report of Major Burnet's arrival with General Greene's letter",
      printings=[k('PP', '01-16', 1), k('NJG', '01-22', 2), k('NHG', '02-01', 2), k('CC', '02-04', 2)]),
 dict(id='townshend-letter-to-the-bank-of-england-november-1782', kind='document_group',
      label="London, 23 November 1782: Mr. Townshend's letter to the governors and directors of the Bank of England on the negotiations at Paris",
      definition="Printings of a London paragraph of 23 November 1782 and the letter it introduces: 'This day the governors and directors of the bank of England, received the following letter from the honourable T. Townshend, secretary for the home department. Whitehall, Nov. 22, 1782. Gentlemen, His majesty's ministers, anxious to prevent as early as possible, the mischiefs too commonly resulting from speculations in the funds, during the uncertain state of negotiations of peace'; it says that 'the negotiations now carrying on at Paris, are thought so near a crisis, as to promise a decisive conclusion, either for peace or war, before the meeting of parliament'. The secretary of state's own letter, with a London paper's introduction.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:T\s?HIS|This)\s+day,?\s+the\s+[Gg]overnors\s+and\s+[Dd]irectors\s+of\s+the\s+[Bb]ank\s+of\s+England'],
      first="London, 23 November 1782: Mr. Townshend writes to the Bank of England that the negotiations at Paris are near a crisis.",
      what="Mr. Townshend's letter to the Bank of England",
      printings=[k('PP', '01-30', 2), k('NJG', '02-05', 2), k('CC', '02-11', 2), k('NHG', '02-15', 2)]),
 dict(id='basseterre-report-of-a-peace-concluded-january-1783', kind='message_group',
      label="Basseterre, St. Christopher, 15 January 1783: 'The important and agreeable intelligence of a PEACE being concluded between the belligerent powers ... seems now to be confirmed'",
      definition="Printings of a paragraph from Basseterre, St. Christopher, of 15 January 1783: 'The important and agreeable intelligence of a PEACE being concluded between the belligerent powers, which has circulated here for some time, gains ground daily, and seems now to be confirmed; we heartily wish it to be true: It is said that the intelligence comes from good authority'; it gives terms that are 'said to be', beginning 'America to be acknowledged an independent state by all parties'. A West India paper's report of what is said.",
      role='report', words=50, dateline=True,
      core=[r'(?:T\s?HE|The)\s+important\s+and\s+agreeable\s+intelligence\s+of\s+a\s+P\s?EACE'],
      first="Basseterre, 15 January 1783: the news of a peace concluded between the powers at war 'seems now to be confirmed'.",
      what="the Basseterre report of a peace concluded",
      printings=[k('PP', '02-11', 3), k('NJG', '02-12', 3), k('CC', '02-25', 3), k('NHG', '03-01', 2)]),
 dict(id='prize-ship-of-20-guns-to-the-frigate-hague-january-1783', kind='message_group',
      label="Boston, January 1783: a ship of 20 guns, prize to the Continental frigate Hague, John Manley, Esq; commander, arrives",
      definition="Printings of a Boston paragraph of late January 1783: 'Yesterday arrived safe in port a ship of 20 guns, prize to the Continental frigate Hague, John Manly, Esq; Commander, she was from St. Lucia bound to St. Martins, and has about 1800 barrels provisions on board—This is the fifth prize Capt. Manly has sent into port on his late cruise.' The other papers print it from Boston as 'Wednesday arrived'. A Boston paper's report.",
      role='report', words=50, dateline=True,
      core=[r'(?:Y\s?ESTERDAY|Yesterday|W\s?EDNESDAY|Wednesday)\s+arrived\s+safe\s+in\s+port,?\s+a\s+ship'],
      first="Boston: a ship of 20 guns, from St. Lucia, arrives as a prize to the Continental frigate Hague.",
      what="the Boston report of the Hague's prize",
      printings=[k('NHG', '02-01', 2), k('CC', '02-11', 2), k('NJG', '02-19', 3), k('PP', '02-20', 2)]),
 dict(id='brig-ranger-and-mr-townshends-letter-to-the-lord-mayor-december-1782', kind='message_group',
      label="New York, 12 February 1783: by the brig Ranger, taken by the Eagle privateer, Mr. Townshend's letter to the Lord Mayor of London of 3 December 1782",
      definition="Printings of a New York paragraph of 12 February 1783: 'By the brig Ranger, captain Roger Boyce, who left France the 23d of December, 1782, and was captured on the 6th instant, by the Eagle privateer, captain George Benneison, which arrived here last night, the following letter was received', with the extract of Mr. Townshend's letter to the Lord Mayor of London of 3 December 1782: 'I take the earliest opportunity to inform your lordship, that an express has just arrived from Paris, who brings the preliminary articles for a peace, signed on the 30th of November, by the ambassadors on the part of England, and those on the part of the united states of America'. A New York paper's report, with the secretary of state's own letter.",
      role='report', words=60, dateline=True,
      core=[r'(?:B\s?Y|By)\s+the\s+brig\s+Ranger'],
      first="New York, 12 February 1783: a letter taken in the brig Ranger, Mr. Townshend's to the Lord Mayor of London of 3 December 1782.",
      what="the New York report of the letter taken in the brig Ranger",
      printings=[k('PP', '02-18', 3), k('NJG', '02-19', 3), k('CC', '02-25', 2), k('NHG', '03-01', 2)]),
 # ---- March to May: the superintendent of finance, the articles of peace, the cessation of arms ----
 dict(id='mr-morris-letter-to-congress-on-his-office-january-1783', kind='document_group',
      label="Office of Finance, 24 January 1783: Mr. Morris's letter to Congress, 'As nothing but the public danger would have induced me to accept my office'",
      definition="Printings of the letter of Mr. Morris, superintendent of finance, to Congress, dated Office of Finance, 24 January 1783, which the papers print in March, 'the resignation of the superintendant of finance having occasioned much conversation': 'As nothing but the public danger would have induced me to accept my office, so I was determined to hold it until the danger was past, or else to meet my ruin in the common wreck'; he writes that funding the public debts on solid revenues was 'the last essential work of our glorious revolution'. Mr. Morris's own letter.",
      role='published_document', words=60, dateline=False,
      head=r'(?:O\s?FFICE\s+of\s+F\s?INANCE,?\s+Jan(?:uary|\.)?\s+24,?\s*1783\.?\s*)?S\s?\s?I\s?\s?R,?\s*',
      core=[r'(?:A\s?\s?S|As)\s+nothing\s+but\s+the\s+publick?\s+danger\s+would\s+have\s+induced'],
      first="Mr. Morris, superintendent of finance, writes to Congress that only the public danger made him accept his office.",
      what="Mr. Morris's letter to Congress",
      printings=[k('PP', '03-04', 3), k('NJG', '03-12', 3), k('NJJ', '03-12', 2), k('CC', '03-18', 3)]),
 dict(id='the-articles-of-peace-and-the-cessation-of-arms-printed-march-may-1783', kind='context_group',
      label="The articles of peace and the cessation of arms, as the papers printed them from March to May 1783",
      children=['provisional-articles-of-peace-30-november-1782', 'preliminary-articles-between-great-britain-and-france-20-january-1783',
                'kings-proclamation-of-the-cessation-of-arms-february-1783', 'congress-proclamation-of-the-cessation-of-arms-11-april-1783',
                'washington-orders-for-proclaiming-the-cessation-of-hostilities-18-april-1783'],
      definition="Five public papers of the peace, as the papers printed them in the spring of 1783: the provisional articles agreed at Paris on 30 November 1782 between the King's commissioner and the commissioners of the United States; the preliminary articles between Great Britain and France signed at Versailles on 20 January 1783; the King's proclamation of the cessation of arms; the proclamation of the United States in Congress assembled of 11 April; and General Washington's orders of 18 April for proclaiming the cessation of hostilities to the army. Contains those five groups."),
 dict(id='provisional-articles-of-peace-30-november-1782', parent='the-articles-of-peace-and-the-cessation-of-arms-printed-march-may-1783', kind='document_group',
      label="The provisional articles of peace agreed at Paris on 30 November 1782 between Richard Oswald and the commissioners of the United States",
      definition="Printings of the provisional articles: 'Articles agreed upon by and between Richard Oswald, esquire, the commissioner of his Britannic majesty, for treating of peace with the commissioners of the united states of America, in behalf of his said majesty on the one part, and John Adams, Benjamin Franklin, John Jay, and Henry Laurens, four of the commissioners of the said states'; the first article reads 'His Britannic majesty acknowledges the said united states ... to be free, sovereign, and independent states'. The articles themselves, as the papers print them.",
      role='published_document', words=60, dateline=False,
      core=[r'A\s?RTICLES\s+agreed\s+upon\s+by\s+and\s+between\s+Richard\s+Oswald'],
      first="The provisional articles of peace agreed at Paris on 30 November 1782 between Richard Oswald and the American commissioners.",
      what='the provisional articles of peace',
      printings=[k('PP', '03-18', 3), k('NJG', '03-19', 2), k('CC', '04-08', 2), (k('PP', '04-10', 2), {'note': 'Printed again.'}), k('NHG', '04-12', 2)]),
 dict(id='preliminary-articles-between-great-britain-and-france-20-january-1783', parent='the-articles-of-peace-and-the-cessation-of-arms-printed-march-may-1783', kind='document_group',
      label="The preliminary articles of peace between Great Britain and France, signed at Versailles on 20 January 1783",
      definition="Printings of a translation of the preliminary articles: 'Translation of the Preliminary Articles of Peace, between His Britannic Majesty and the Most Christian King; signed at Versailles the 20th of January, 1783. In the name of the most Holy Trinity. The King of Great-Britain and the Most Christian King, equally animated with a desire of putting an end to the calamities of a destructive war'. The articles themselves, in translation.",
      role='published_document', words=60, dateline=False,
      head=r'(?:A\s?UTHENTIC\s+Copy\s+of\s+the\s+P\s?reliminary\s+A\s?rticles\s+of\s+P\s?\s?E\s?\s?A\s?\s?C\s?\s?E\.?\s*)?',
      core=[r'T\s?RANSLATION\s+of\s+the\s+P\s?RELIMINARY\s+A\s?RTICLES\s+of\s+P\s?EACE,?\s+between\s+(?:H\s?IS|his)\s+B\s?RITANNICK?\s+M\s?AJESTY,?\s+and\s+the\s+M\s?OST\s+C\s?HRISTIAN\s+K\s?ING'],
      first="The preliminary articles of peace between Great Britain and France, signed at Versailles on 20 January 1783, in translation.",
      what='the preliminary articles between Great Britain and France',
      printings=[k('PP', '04-08', 5), (k('PP', '04-10', 1), {'note': 'Printed again.'}), k('NJG', '04-23', 2), k('NHG', '04-26', 1), k('CC', '05-06', 1)]),
 dict(id='kings-proclamation-of-the-cessation-of-arms-february-1783', parent='the-articles-of-peace-and-the-cessation-of-arms-printed-march-may-1783', kind='document_group',
      label="The King's proclamation declaring the cessation of arms, as well by sea as land, agreed upon between him, the Most Christian King, the King of Spain, the States General and the United States",
      definition="Printings of the King's proclamation: 'By the King. A Proclamation, Declaring the Cessation of Arms, as well by Sea as Land, agreed upon between His Majesty, the Most Christian King, the King of Spain, the States General of the United Provinces, and the United States of America, and enjoining the Observance thereof. George R. Whereas Provisional Articles were signed at Paris, on the Thirtieth Day of November last, between Our Commissioner for treating of Peace with the Commissioners of the United States of America, and the Commissioners of the said States'. London reports of its reading at the Royal Exchange, which name its title, are not counted (C-07). The King's own proclamation.",
      role='published_document', words=60, dateline=False,
      head=r'B\s?Y\s+T\s?HE\s+K\s?ING[.,]?\s*A\s+P\s?ROCLAMATION[.,]?\s*',
      core=[r'Declaring\s+the\s+[Cc]essation\s+of\s+[Aa]rms,?\s+as\s+well\s+by\s+[Ss]ea\s+as\s+[Ll]and,?\s+agreed\s+upon\s+(?:between|by)\s+(?:H\s?IS|his)\s+M\s?ajesty'],
      first="The King's proclamation declaring the cessation of arms by sea and land agreed upon with France, Spain, the States General and the United States.",
      what="the King's proclamation of the cessation of arms",
      printings=[k('NJJ', '04-09', 2), k('PP', '04-10', 3), k('CC', '04-15', 3), k('NHG', '04-19', 3)]),
 dict(id='congress-proclamation-of-the-cessation-of-arms-11-april-1783', parent='the-articles-of-peace-and-the-cessation-of-arms-printed-march-may-1783', kind='document_group',
      label="The proclamation of the United States in Congress assembled, 11 April 1783, declaring the cessation of arms agreed upon between the United States and the King",
      definition="Printings of the proclamation of Congress of 11 April 1783: 'By the United States of America in Congress assembled. A Proclamation, Declaring the Cessation of Arms, as well by Sea as by Land, agreed upon between the United-States of America and His Britannic Majesty; and enjoining the Observance thereof. Whereas Provisional Articles were signed at Paris on the Thirtieth Day of November last, between the Ministers Plenipotentiary of the United-States of America for treating of Peace'. The New-Jersey Gazette prints it whole within a New Jersey proclamation, which recites it 'in the words following, to wit' (counted, C-02; X-1783-05). Congress's own proclamation.",
      role='published_document', words=60, dateline=False,
      head=r'B\s?Y\s+the\s+United[\s\-]States,?\s+of\s+America,?\s+(?:in|In)\s+C\s?ONGRESS\s+assembled[.,]?\s*A\s+P\s?ROCLAMATION[.,]?\s*',
      core=[r'Declaring\s+the\s+[Cc]essation\s+of\s+[Aa]rms,?\s+as\s+well\s+by\s+[Ss]ea\s+as\s+by\s+[Ll]and,?\s+agreed\s+upon\s+between\s+the\s+United',
            r'W\s?HEREAS\s+[Pp]rovisional\s+[Aa]rticles\s+were\s+signed\s+at\s+Paris,?\s+on\s+the\s+[Tt]hirtieth\s+[Dd]ay\s+of\s+November\s+last,?\s+between\s+the\s+M\s?inisters'],
      first="Congress proclaims on 11 April 1783 the cessation of arms agreed upon between the United States and the King.",
      what="Congress's proclamation of the cessation of arms",
      printings=[k('PP', '04-12', 3),
                 (k('NJG', '04-16', 2), {'core': [r'W\s?HEREAS\s+[Pp]rovisional\s+[Aa]rticles\s+were\s+signed\s+at\s+Paris,?\s+on\s+the\s+[Tt]hirtieth\s+[Dd]ay\s+of\s+November\s+last,?\s+between\s+the\s+M\s?inisters'], 'note': "Recited whole within a New Jersey proclamation ('in the words following, to wit'), counted with the printings of the proclamation itself (C-02)."}),
                 k('CC', '04-22', 3), k('NHG', '04-26', 3)]),
 dict(id='washington-orders-for-proclaiming-the-cessation-of-hostilities-18-april-1783', parent='the-articles-of-peace-and-the-cessation-of-arms-printed-march-may-1783', kind='document_group',
      label="Head-quarters, 18 April 1783: General Washington's orders that the cessation of hostilities be publicly proclaimed to the army",
      definition="Printings of the orders of 18 April 1783: 'The commander in chief orders the cessation of hostilities between the united states of America and the king of Great-Britain, to be publicly proclaimed to morrow at twelve o'clock, at the new building; and that the proclamation, which will be communicated herewith, be read to morrow evening at the head of every regiment and corps of the army; after which the chaplains, with the several brigades, will render thanks to Almighty God'. The commander in chief's own orders.",
      role='published_document', words=60, dateline=False,
      head=r'(?:G\s?\s?E\s?\s?N\s?\s?E\s?\s?R\s?\s?A\s?\s?L\s+O\s?\s?R\s?\s?D\s?\s?E\s?\s?R\s?\s?S\.?\s*)?H\s?\s?E\s?\s?A\s?\s?D[\s\-]*Q\s?\s?U\s?\s?A\s?\s?R\s?\s?T\s?\s?E\s?\s?R\s?\s?S,?\s+(?:Newburgh,?\s+)?April\s+18,?\s*1783\.?\s*',
      core=[r'(?:T\s?HE|The)\s+[Cc]ommander\s+in\s+[Cc]hief\s+orders\s+the\s+cessation\s+of\s+hostilities'],
      first="General Washington orders on 18 April 1783 that the cessation of hostilities be proclaimed to the army.",
      what="General Washington's orders of 18 April",
      printings=[k('PP', '04-29', 2), k('CC', '04-29', 3), k('NJG', '04-30', 2), k('NHG', '05-03', 3)]),
 dict(id='tell-it-to-the-whole-world-the-prisoners-at-new-york-april-1783', kind='message_group',
      label="'To all Printers of Public News-Papers. Tell it to the whole World': a notice signed 'An American' on the American prisoners said to have died in the prison ship at New York",
      definition="Printings of a notice signed 'An American': 'To all Printers of Public News-Papers. Tell it to the whole World, and let it be published in every News-Paper throughout America, Europe, Asia and Africa, to the everlasting disgrace and infamy of the British King's Commanders at New-York, That during the late War, it is said, Eleven Thousand Six Hundred and Forty Four American Prisoners, have suffered death by their inhumane, cruel, savage and barbarous usage on board the filthy and malignant British Prison Ship called the Jersey, lying at New-York.' An anonymous writer's allegation, of a number that 'it is said'.",
      role='published_document', words=60, dateline=False,
      head=r'T\s?O\s+all\s+(?:the\s+)?P\s?rinters\s+of\s+P\s?ublick?\s+(?:N\s?ews[\s\-]*)?P\s?apers\.?\s*',
      core=[r'T\s?ELL\s+it\s+to\s+the\s+whole\s+W\s?ORLD'],
      first="A notice signed 'An American' asks every newspaper to publish that, 'it is said', 11,644 American prisoners died on board the prison ship Jersey at New York.",
      what="the notice 'Tell it to the whole World'",
      printings=[k('NHG', '04-19', 3), k('PP', '04-29', 2), k('NJG', '05-07', 3), k('SCGA', '05-24', 4), k('SCWG', '05-24', 2)]),
 dict(id='philadelphia-port-open-to-vessels-from-any-foreign-port-april-1783', kind='message_group',
      label="Philadelphia, April 1783: 'this port is now open for the reception of vessels from any foreign port', and New York open for the American flag",
      definition="Printings of a Philadelphia paragraph of 29 April 1783: 'We have good authority for assuring our readers, that this port is now open for the reception of vessels from any foreign port.—Several vessels from different parts of the united states have lately arrived at New-York, that port being at this time open for the American flag.' A Philadelphia paper's report.",
      role='report', words=50, dateline=True,
      core=[r'(?:W\s?E|We)\s+have\s+good\s+authority\s+(?:for\s+assuring|to\s+assure)\s+our\s+readers'],
      first="Philadelphia, 29 April 1783: the port is open to vessels from any foreign port, and New York to the American flag.",
      what="the Philadelphia report of the ports open",
      printings=[k('PP', '04-29', 3), k('NJG', '05-07', 2), k('CC', '05-13', 2), k('NHG', '05-17', 2), k('SCWG', '05-24', 2)]),
 # ---- June to September: the troops in the south, the states' funds for Congress, ships and news ----
 dict(id='continental-troops-march-to-charleston-june-1783', kind='message_group',
      label="June 1783: 'The continental troops who were at Savanna, are on their march to Charlestown, where vessels are providing to transport them to their respective states'",
      definition="Printings of a paragraph of the southern news, printed from early June 1783: 'The continental troops who were at Savanna, are on their march to Charlestown, where vessels are providing to transport them to their respective states. General Wayne is gone to settle a treaty of peace with some tribes of Indians on the frontiers of Georgia. They are to negotiate the business at Augusta.' A paper's report of news from the south.",
      role='report', words=50, dateline=True,
      core=[r'(?:T\s?HE|The)\s+[Cc]ontinental\s+troops\s+who\s+were\s+at\s+Sav\w+'],
      first="The continental troops at Savannah march to Charleston to be carried home by sea; General Wayne goes to treat with Indian nations at Augusta.",
      what="the report of the troops' march to Charleston",
      printings=[k('PP', '06-03', 3), k('NJG', '06-04', 3), k('CC', '06-17', 3), k('NHG', '06-21', 2)]),
 dict(id='versailles-dispatches-of-m-de-suffren-march-1783', kind='message_group',
      label="Versailles, 28 March 1783: the King receives official dispatches from M. de Suffren on the proceedings in the East Indies",
      definition="Printings of a paragraph from Versailles of 28 March 1783: 'On the 25th of this month, the king received some official dispatches from M. de Suffrein, which after giving a detail of the late proceedings in the East Indies between the French and English fleets, as has been already mentioned, conclude as follow', with what the dispatches report of the fighting near Madras. The French court's account of the dispatches, in the European news.",
      role='report', words=50, dateline=True,
      core=[r'(?:O\s?N|On)\s+the\s+25th\s+of\s+this\s+month,?\s+the\s+[Kk]ing\s+received'],
      first="Versailles, 28 March 1783: the King receives M. de Suffren's dispatches on the proceedings in the East Indies.",
      what="the Versailles report of M. de Suffren's dispatches",
      printings=[k('PP', '06-07', 2), k('NHG', '06-07', 2), k('CC', '06-17', 1), k('NJG', '06-18', 1)]),
 dict(id='maryland-act-to-invest-congress-with-power-to-levy-duties-june-1783', kind='message_group',
      label="Philadelphia, 10 June 1783: the general assembly of Maryland passes an act to invest Congress with a power to levy duties on imported goods",
      definition="Printings of a Philadelphia paragraph of 10 June 1783: 'The general assembly of Maryland, at their last session, passed an act to invest the United States in Congress assembled, with a power to levy for the use of the said states, certain duties on imported foreign goods, wares and merchandizes, as a fund for the payment of the debt contracted by Congress during the late war.' A Philadelphia paper's report.",
      role='report', words=50, dateline=True, stop=r'\sThe\s+ship\s+Achilles',
      core=[r'(?:T\s?HE|The)\s+general\s+assembly\s+of\s+Maryland,?\s+at\s+their\s+last\s+session'],
      first="Philadelphia, 10 June 1783: Maryland's assembly passes an act giving Congress power to levy duties on imports, to pay the debt of the war.",
      what="the Philadelphia report of Maryland's act",
      printings=[k('PP', '06-10', 3), k('NJG', '06-18', 4), k('CC', '06-24', 3), k('NHG', '06-28', 2)]),
 dict(id='virginia-assembly-votes-50000-pounds-to-congress-june-1783', kind='message_group',
      label="Richmond, 7 June 1783: 'The honorable general assembly have voted an immediate payment of 50,000l. to Congress'",
      definition="Printings of a Richmond paragraph of 7 June 1783: 'The honorable general assembly have voted an immediate payment of 50,000l. to Congress; and the funds out of which this money is directed to be paid, being fully equal to that demand, it affords sensible pleasure that Virginia, by the wisdom of the legislature, will retrieve her character of good faith and exertion among the United States'. A Richmond paper's report and comment.",
      role='report', words=50, dateline=True,
      core=[r'(?:T\s?HE|The)\s+hono(?:u)?rable\s+(?:the\s+)?general\s+assembly\s+(?:of\s+this\s+[Ss]tate\s+)?have\s+voted'],
      first="Richmond, 7 June 1783: Virginia's assembly votes an immediate payment of £50,000 to Congress.",
      what="the Richmond report of Virginia's payment to Congress",
      printings=[k('PP', '06-17', 3), k('NJG', '06-25', 2), k('CC', '07-01', 3), k('NHG', '07-05', 2)]),
 dict(id='french-frigate-with-stores-for-the-america-portsmouth-june-1783', kind='message_group',
      label="Portsmouth, New Hampshire, 7 June 1783: a French frigate arrives from France with stores for the ship America, of 74 guns",
      definition="Printings of a Portsmouth paragraph of 7 June 1783: 'Yesterday arrived here a French frigate in 44 days from France, with stores, &c. for the ship America, of 74 guns, now lying before this town. She brings nothing new.' A Portsmouth paper's report.",
      role='report', words=40, dateline=True, stop=r'(?<=[Nn]othing\s[Nn]ew\.)\s',
      core=[r'arrived\s+(?:here|there),?\s+a\s+French\s+frigate,?\s+in\s+44\s+days'],
      back=True,
      first="Portsmouth, New Hampshire: a French frigate arrives with stores for the ship America, of 74 guns.",
      what="the Portsmouth report of the French frigate",
      printings=[k('NHG', '06-07', 3), k('CC', '06-24', 3),
                 (k('NJG', '06-25', 3), {'core': [r'(?:W\s?E|We)\s+learn\s+from\s+Portsmouth'], 'note': "Prints it in other words, 'We learn from Portsmouth, that on the 6th inst. arrived there a French frigate' (counted with it, C-02)."}),
                 k('PP', '07-01', 2)]),
 dict(id='schooner-molly-from-grenada-report-on-the-stadtholder-july-1783', kind='message_group',
      label="Philadelphia, July 1783: Captain Burrows, in the schooner Molly from Grenada, brings 'an account that the prince stadtholder was lately killed in a tumult'",
      definition="Printings of a Philadelphia paragraph of late June 1783: 'Captain Burrows, in the schooner Molly, arrived here last Saturday from Grenada, in fourteen days passage, informs us, that before he sailed, advice was received from Barbadoes of the arrival of a packet from England, which brought an account that the prince stadtholder was lately killed in a tumult among the people of Amsterdam.—If this be true, it is likely that some trouble will ensue'. A report at third hand, which the paper itself doubts ('If this be true').",
      role='report', words=50, dateline=True,
      core=[r'(?:C\s?APTAIN|Captain|Capt\.)\s+Burrows,?\s+in\s+the\s+schooner\s+Molly'],
      first="Captain Burrows of the schooner Molly, from Grenada, reports an account from Barbados that the stadtholder was killed in a tumult at Amsterdam.",
      what="the report brought by the schooner Molly",
      printings=[k('PP', '07-01', 3), k('NJG', '07-09', 3), k('CC', '07-15', 3), k('NHG', '07-19', 2), k('SCG', '08-27', 3)]),
 dict(id='no-foreign-vessels-entered-at-new-york-july-1783', kind='message_group',
      label="July 1783: 'No foreign vessels can yet be entered at New-York, neither is the American flag suffered to fly in that harbour'",
      definition="Printings of a paragraph of July 1783: 'No foreign vessels can yet be entered at New-York, neither is the American flag suffered to fly in that harbour. The few French and others that arrived hitherto, have either returned and entered some other port, or sailed up the North river'. A paper's report.",
      role='report', words=40, dateline=True,
      core=[r'(?:N\s?O|No)\s+foreign\s+vessels?\s+can\s+yet\s+be\s+entered\s+at\s+New'],
      first="No foreign vessels can yet be entered at New York, nor may the American flag fly in its harbour.",
      what="the report that no foreign vessels are entered at New York",
      printings=[k('PP', '07-17', 2), k('CC', '07-29', 3), k('NHG', '08-02', 2), k('SCG', '08-13', 3)]),
 dict(id='lisbon-treaty-of-commerce-with-the-united-states-nearly-agreed-april-1783', kind='message_group',
      label="Lisbon, 20 April 1783: an American of distinction received by the Queen, and the articles of a treaty of commerce with the United States 'nearly agreed upon'",
      definition="Printings of a Lisbon paragraph of 20 April 1783: 'An American of distinction, who has for some time past resided in this capital, was admitted a few days since to a private audience of the queen, and had a pretty long conference with her majesty. It is assured, that the articles of the treaty of commerce, which is upon the tapis between our court and the United-States, are nearly agreed upon'. The New-Hampshire Gazette prints it in other words ('We are assured that the articles of the treaty of commerce, which is on the tapis'), counted with it (C-02). A paragraph of the European news.",
      role='report', words=60, dateline=True,
      core=[r'(?:A\s?N|An)\s+American\s+of\s+distinction'],
      first="Lisbon, 20 April 1783: an American is received by the Queen, and a treaty of commerce with the United States is said to be nearly agreed.",
      what="the Lisbon paragraph on a treaty of commerce",
      printings=[k('PP', '07-26', 2), k('NHG', '07-26', 2), k('CC', '08-05', 3), k('SCG', '08-06', 3)]),
 dict(id='captain-dalton-arrives-from-canada-august-1783', kind='message_group',
      label="Philadelphia, 12 August 1783: Captain Dalton, superintendent of Indian affairs for the United States, arrives from Canada with 200 Americans",
      definition="Printings of a Philadelphia paragraph of 12 August 1783: 'Captain Dalton, superintendant of Indian affairs for the United States, arrived here last week from Canada, which he left about a month since, in company with 200 Americans, who are at length happily liberated from a cruel captivity'; it says that a number of others 'are still retained as prisoners by the Indians'. A Philadelphia paper's report; the excerpts end before it turns to Captain Dalton's family.",
      role='report', words=60, dateline=True, stop=r'\sThe\s+sufferings',
      core=[r'(?:C\s?APTAIN|Captain|Capt\.)\s+Dalton,?\s+superintend[ae]nt\s+of\s+Indian\s+affairs'],
      first="Philadelphia, 12 August 1783: Captain Dalton arrives from Canada with 200 Americans released from captivity; others are still held.",
      what="the Philadelphia report of Captain Dalton's arrival",
      printings=[k('PP', '08-12', 2), k('CC', '08-26', 2), k('NHG', '08-30', 3), k('SCG', '09-24', 2)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797 and 1800): "BOSTON, Nov. 30th, 1802."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}[\s\-]+){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:(?:\s|\s?-\s?)[A-Z][A-Za-z'\-]+){0,2})(?:,?\s*[\(\[][A-Za-z ,.]+[\)\]])?"
# As for 1774 (24 November): also a year after a stop ('Oct. 16. 1774.') and a date printed alone ('December 5.').
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)((?:" + PLACE + r",?\s+)?" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:[,.]?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


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
            problems.append((s['id'], key, 'page not in the 1783 pages'))
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
        r['id'] = f'S83-{n:03}'
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
               'admission_rule': 'Reviewed 1783 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1783/'
    return {
        'ledger_id': 'ledger:stories-1783', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1783', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1783, and of 1782 where they reach the 1783 pages (long-running ones '
                   'included), every item in 3 or more papers compared by machine with every page and counted again by its opening, a sweep of '
                   'word-for-word passages shared by 4 or more papers for short items the families miss, phrase searches on all 1,100 pages of '
                   '1783 in both transcriptions, reading of every hit, and scan checks of each admitted passage, by the thin-year rule (Y-THIN, '
                   'as amended on 23 November 2026: an item printed by more than half of the papers that survive for its weeks, and by at '
                   'least 4, is eligible; the items printed by every paper that survives for their weeks are admitted, and the other eligible '
                   'items are chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1782.json': 'retrieval_candidates', d+'count_1783.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1783.py': 'ledger_code', 'work/archive_data/ledgers/stories_1783_review.json': 'scan_review',
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
