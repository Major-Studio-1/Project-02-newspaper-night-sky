"""Write ledgers/stories_1801.json: reviewed stories of 1801, round one.

1801 is read by the one admission rule the other reviewed years follow (outputs/story_discovery_1809/README.md, "Selection
rule"; docs/rules-and-exceptions.md, R-01): every single printed item in 9 or more newspapers is admitted, except digests;
items in 7 or 8 papers are chosen to cover the months and the kinds of news; items are counted one by one; a sub-story may
have fewer papers when its parent reaches 7. The automatic families first printed in 1801 that reach 3 or more papers,
long-running ones included, were split into single printed items with work/story_items.py --long-running (items.json), and
again with year 1800 over the 1801 pages (items_from_1800.json); every item in 7 or more papers, and every item in 5 or 6
that a deeper comparison put in more papers, was counted again by its own words, and a sweep of word-for-word passages
shared by 7 or more papers (as for 1803, X-1803-09) found short items the families miss. Every chosen item and every
candidate set aside was counted with phrase searches over all 2,372 pages of 1801 in both transcriptions
(work/story_phrase_search.py). See outputs/story_discovery_1801/README.md.

The 1801 pages are those whose issue the data release dates to 1801 (work/year_search_pages.py 1801 ... --printed-dates);
no 1801 issue has a corrected date. 1801 has 14 catalogue series, which are 11 papers (C-04): the Portsmouth Oracle
(sn83025544, The United States Oracle of the Day, to 10 October; sn83025545, the United States Oracle and Portsmouth
Advertiser, from 17 October), the Republican Ledger (sn84023378 to 17 November, sn84023379 from 24 November, which continues
its numbering) and the Wilmington Monitor (sn84020424 in May, sn84038116 from August, which continues its total numbering).
k() below picks the catalogue number from the date.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. Where the item is a letter or a note printed inside different reports, the excerpt begins with
the letter or note (as 1803 did). Scan findings, crops and hand-drawn boxes are merged from stories_1801_review.json after
the scan check. Eighteen 1801 pages have their RevX transcriptions filed off from the scans
(derived/revx_page_map.parquet); a printing on such a page takes its excerpt from the CA transcription of its scan page
(one printing here: the National Intelligencer of 19 January, page 3).

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (1810, reviewed at the same time, is cut as v0.11.14, so
1801 goes on it as v0.11.15):
    python work/archive_data/ledgers/make_stories_1801.py [--table] [--base 0.11.14 --target 0.11.15]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1801/search_pages.json). The excerpts are cut from
the 1801 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1801'
D = PROJECT/'outputs/story_discovery_1801'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1801_review.json'
OUT = HERE/'stories_1801.json'
BASE, TARGET = '0.11.14', '0.11.15'   # defaults; see the docstring
DATA_RELEASE = '0.11.13'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-23'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn84024011': 'The Alexandria Advertiser', 'sn83045242': 'The National Intelligencer',
         'sn83025588': 'The New Hampshire Gazette', 'sn84023378': 'The Republican Ledger', 'sn84023379': 'The Republican Ledger',
         'sn83025544': 'The United States Oracle of the Day', 'sn83025545': 'The United States Oracle',
         'sn83016063': "Jenks's Portland Gazette", 'sn83021629': 'The Providence Journal', 'sn84024710': 'The Virginia Argus',
         'sn84022876': 'The Republican Gazette', 'sn84020424': 'The Monitor', 'sn84038116': 'The Monitor',
         'sn83021188': 'The Rhode-Island Republican'}
ONE = {'ALX': 'sn84024011', 'NI': 'sn83045242', 'NHG': 'sn83025588', 'POR': 'sn83016063', 'PJ': 'sn83021629',
       'VA': 'sn84024710', 'RG': 'sn84022876', 'RIR': 'sn83021188'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1801), page and edition. Three papers have two catalogue numbers
    in 1801 (C-04); the date picks it."""
    if paper == 'ORA':
        lccn = 'sn83025544' if date < '10-14' else 'sn83025545'
    elif paper == 'RL':
        lccn = 'sn84023378' if date < '11-20' else 'sn84023379'
    elif paper == 'MON':
        lccn = 'sn84020424' if date < '06-30' else 'sn84038116'
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

# Story groups. A parent ('context_group') lists its children and has no printings. 'printings' lists each printing's page;
# a tuple adds overrides for that printing: core (regexes for the item's first words), role, field, note, words, dateline
# (include a dateline directly before), back (start at the beginning of the sentence that holds the core), stop (a regex:
# the excerpt ends before it).
STORIES = [
 dict(id='augereau-notice-ending-the-armistice-november-1800', kind='document_group',
      label="Frankfort, November 1800: General Augereau's note to the Austrian commander that the armistice is at an end",
      definition="Printings of the note that the French general Augereau sent to the commander of the Austrian troops in Germany in November 1800, on orders from his government: 'GENERAL, According to the orders I have received from my government, I hereby notify to you the termination of the armistice. Hostilities will therefore recommence in fourteen days from this day, that is on the 22d of November.' Five papers print it within a report from Frankfort of 10 November ('While we were flattering ourselves with hopes of peace, appearances here have suddenly become very warlike. Yesterday General Augereau received a courier from Paris, with orders to give notice immediately of the termination of the armistice'); the National Intelligencer and the Republican Ledger print it in other runs of European news. The note, which all of them print, is counted as the item (C-02). Every paper prints the general's name 'Angereau'. A French general's own note, as the European papers reported it.",
      role='published_document', words=45, dateline=False,
      core=[r'["“]?\s*G\s?(?:ENERAL|eneral)\s*[,.—-]*\s*(?:A\s?CCORDING|According)\s+to\s+the\s+orders\s+I\s+have\s+received'],
      stop=r'H(?:AMBURGH?|amburgh?)\b|[S3](?:TRA|tra)[tsTS]{0,2}[bB][ouOU]*[rR][gG]|V(?:IENNA|ienna)\b|M(?:ENTZ|entz)\b',
      first="Frankfort, November 1800: the French general Augereau notifies the Austrian commander that the armistice is at an end.",
      what="General Augereau's note ending the armistice",
      printings=[k('PJ', '01-14', 2),
                 k('ORA', '01-17', 2),
                 k('ALX', '01-17', 3),
                 k('POR', '01-19', 2),
                 k('NI', '01-19', 3),
                 k('NHG', '01-20', 2),
                 k('RL', '01-20', 3)]),
 dict(id='jefferson-letter-of-4-september-1800', kind='document_group',
      label="Mr. Jefferson's letter of 4 September 1800 in reply to a citizen, as the papers printed it in 1801",
      definition="Printings of a letter that Thomas Jefferson, then Vice President and a candidate for President, wrote at Monticello on 4 September 1800 in reply to a letter of August: 'Your favor of August 26th, has been duly received, and is entitled to my thankfulness for the personal considerations you are pleased to express in it. How far the measure proposed might have the expected effect, you can best judge: however, in the great exercise of right in which the citizens of America are about to act, I have, on mature consideration, seen, that it is my duty to be passive'; 'The great question which divides our citizens is, whether it is safest that a preponderance of power should be lodged with the monarchical, or the republican branch of our government?' The papers head it as Mr. Jefferson's letter 'in reply to one addressed to him by a citizen of Berkeley', and print it with their own introductions: the National Intelligencer's correspondent values it because 'it contains the spontaneous effusions of his heart'; Jenks's Portland Gazette prints it as 'Jefferson's Second Letter', which 'will serve as a second part of his Mazzei Letter'. Mr. Jefferson's own letter, published by others, each paper with its own heading.",
      role='published_document', words=60, dateline=True,
      core=[r'["“]?\s*M\s?(?:ONTICELLO|onticello),?\s+S(?:EPT|ept)\w*\.?,?\s+4,?\s+1800\.?\s*["“]?\s*(?:S\s?IR|Sir)',
            r'["“]?\s*(?:S\s?IR|Sir)[,.]?\s*["“]?\s*(?:Y\s?OUR|Your)\s+favou?r\s+of\s+Aug', r'(?:Y\s?OUR|Your)\s+favou?r\s+of\s+Aug(?:ust|\.)?\s+\d+'],
      first="Mr. Jefferson's letter from Monticello of 4 September 1800, in reply to a citizen, printed in 1801.",
      what="Mr. Jefferson's letter of 4 September 1800",
      printings=[k('VA', '01-30', 3),
                 k('NI', '02-02', 2),
                 k('NHG', '02-17', 2),
                 k('RL', '02-17', 2),
                 k('ORA', '02-21', 2),
                 k('POR', '02-23', 1),
                 k('RG', '04-16', 1)]),
 dict(id='moreau-report-of-hohenlinden-december-1800', kind='document_group',
      label="General Moreau's report to the Minister of War on the battle of Hohenlinden, December 1800",
      definition="Printings of the letter of Moreau, general in chief of the French Army of the Rhine, to the Minister of War, from his head-quarters at Anzing, 12 Frimaire of the year 9 (2 or 3 December 1800), in three translations: 'I have the pleasure of giving you an account, my dear general, of an action most glorious for the army which I command, and of the greatest advantage to the republic' (the Alexandria Advertiser and the National Intelligencer, from London prints); 'I HAVE the pleasure, General, to give an account of an event very glorious for the army which I command, and of great advantage to the Republic' (the Oracle, the Portland Gazette, the New Hampshire Gazette and the Republican Ledger, from Paris papers brought to Boston by the Governor Strong); and a shorter form, 'An event has happened as glorious for the army which I command, as it is greatly advantageous to the Republic' (the Providence Journal). The forms are counted together (C-02). The letter reports the battle at Hohenlinden in Bavaria, the prisoners and the cannon taken. A French general's own report of a battle.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:The\s+General\s+in\s+Chief,?\s+)?(?:Gen(?:eral|\.)?\s+)?M\s?(?:OREAU|oreau),?\s+(?:general\s+in\s+chief,?\s+)?to\s+the\s+Minister\s+(?:at|of)\s+War'],
      first="General Moreau's report to the Minister of War of the action at Hohenlinden, December 1800.",
      what="General Moreau's report of Hohenlinden",
      printings=[k('ALX', '02-26', 2),
                 k('NI', '02-27', 2),
                 k('ORA', '02-28', 2),
                 k('POR', '03-02', 3),
                 k('NHG', '03-03', 2),
                 k('RL', '03-03', 2),
                 k('PJ', '03-04', 2)]),
 dict(id='jefferson-elected-and-inaugurated-february-march-1801', kind='context_group',
      label="Mr. Jefferson chosen President and inaugurated, February and March 1801: his answer to the House's committee, his farewell to the Senate and his inaugural address",
      children=['house-committee-notifies-jefferson-february-1801', 'jefferson-farewell-to-the-senate-28-february-1801',
                'jefferson-inaugural-address-4-march-1801'],
      definition="Three addresses of Thomas Jefferson as the papers printed them in February and March 1801, after the House of Representatives chose him President on 17 February 1801: the report of the House's committee that notified him of his election, with his answer; his address to the Senate on leaving its chair, 28 February; and his inaugural address of 4 March. Contains those three groups."),
 dict(id='house-committee-notifies-jefferson-february-1801', parent='jefferson-elected-and-inaugurated-february-march-1801', kind='document_group',
      label="The House committee's report of 19 February 1801 on notifying Mr. Jefferson of his election, with his answer",
      definition="Printings of the report of the committee of the House of Representatives 'instructed ... to wait on the President elect, and notify him of his election', made on 19 February 1801: 'That they have, according to order, performed that service, and addressed the President elect, in the following words to wit: The committee beg leave to express their wishes for the prosperity of your administration; and their sincere desire that it may promote your own happiness and the welfare of your country.' Mr. Jefferson's answer follows: 'I receive, gentlemen, with profound thankfulness, this testimony of confidence from the great representative council of our nation. It fills up the measure of that grateful satisfaction, which had already been derived from the suffrages of my fellow-citizens themselves'; 'In deciding between the candidates, whom their equal vote presented to your choice, I am sensible that age has been respected, rather than more active and useful qualifications.' The House committee's report, with Mr. Jefferson's own answer.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:The\s+)?[Cc](?:OMMITTEE|ommittee)(?:\s+of\s+Congress)?,?\s+instructed\s+on\s+the\s+\w+\s+(?:inst|ult)'],
      first="The House committee's report of 19 February 1801 on notifying the President elect, with Mr. Jefferson's answer.",
      what="the House committee's report and Mr. Jefferson's answer",
      printings=[k('NI', '02-23', 2),
                 k('ALX', '02-24', 3),
                 k('ORA', '03-07', 2),
                 k('POR', '03-09', 3),
                 k('NHG', '03-10', 2),
                 k('RL', '03-10', 2),
                 k('PJ', '03-11', 3)]),
 dict(id='jefferson-farewell-to-the-senate-28-february-1801', parent='jefferson-elected-and-inaugurated-february-march-1801', kind='document_group',
      label="Mr. Jefferson's address to the Senate on leaving its chair, 28 February 1801",
      definition="Printings of the address that the Vice President delivered to the Senate on Saturday 28 February 1801, when he 'took leave of that body': 'Gentlemen of the Senate, To give the usual opportunity of appointing a President pro tempore, I now propose to retire from the chair of the Senate; and as the time is near at hand, when the relations will cease, which have for some time subsisted between this honorable house and myself, I beg leave before I withdraw, to return them my grateful thanks for all the instances of attention and respect with which they have been pleased to honour me'; 'I may have erred at times. No doubt I have erred. This is the law of human nature.' Mr. Jefferson's own address.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:G\s?ENTLEMEN|Gentlemen)\s+of\s+the\s+Senate[,.]?\s+(?:T\s?O|To)\s+give\s+the\s+usual', r'(?:T\s?O|To)\s+give\s+the\s+usual\s+opportunity\s+of\s+appointing'],
      first="Mr. Jefferson's address to the Senate on leaving its chair, 28 February 1801.",
      what="Mr. Jefferson's farewell to the Senate",
      printings=[k('NI', '03-02', 2),
                 k('ALX', '03-03', 3),
                 k('NHG', '03-17', 2),
                 k('RL', '03-17', 2),
                 k('PJ', '03-18', 2),
                 k('ORA', '03-21', 2),
                 k('POR', '03-23', 1)]),
 dict(id='jefferson-inaugural-address-4-march-1801', parent='jefferson-elected-and-inaugurated-february-march-1801', kind='document_group',
      label="Mr. Jefferson's inaugural address, 4 March 1801",
      definition="Printings of the address that Thomas Jefferson delivered in the Senate Chamber before taking the oath of office as President on 4 March 1801: 'Friends and Fellow Citizens, Called upon to undertake the duties of the first Executive office of our country, I avail myself of the presence of that portion of my fellow citizens which is here assembled to express my grateful thanks for the favor with which they have been pleased to look towards me'; it goes on 'We have called by different names brethren of the same principle', and states 'the essential principles of our government'. Pages that print part of it, or quote it in essays, are not counted (C-06, C-07): the Rhode-Island Republican's extract of 17 October and quotations in the Republican Gazette. The President's own address.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:F\s?RIENDS|Friends)\s*(?:and|AND|&)\s*(?:F\s?ELLOW|Fellow)[\s-]*(?:C\s?ITIZENS|Citizens|citizens)[,.]?\s+(?:C\s?ALLED|Called)\s+upon',
            r'(?:C\s?ALLED|Called)\s+upon\s+to\s+undertake\s+the\s+duties'],
      first="Mr. Jefferson's inaugural address, 4 March 1801.",
      what="the inaugural address",
      printings=[k('NI', '03-04', 3),
                 k('ALX', '03-05', 1),
                 k('NHG', '03-17', 3),
                 k('RL', '03-17', 2),
                 k('PJ', '03-18', 2),
                 k('ORA', '03-21', 2),
                 k('POR', '03-23', 1)]),
 dict(id='bashaw-of-tripoli-war-on-the-united-states-1801', kind='context_group',
      label="The Bashaw of Tripoli's war on the United States, 1801: the consul's two circulars, Commodore Dale's letter on the schooner Enterprize, and the President's letter to Lieutenant Sterett",
      children=['cathcart-circular-of-3-january-1801', 'cathcart-circular-of-15-may-1801-war-declared',
                'dale-letter-enterprize-takes-a-tripoline-cruiser-august-1801', 'president-letter-to-lieutenant-sterett-1-december-1801'],
      definition="Four documents of the war that the Basha of Tripoli declared on the United States in May 1801, as the papers printed them from April to December 1801: the circular of the American consul at Tripoli of 3 January 1801, his circular of 15 May announcing the declaration of war, Commodore Dale's letter of 19 August on the schooner Enterprize's capture of a Tripoline cruiser, and the President's letter of 1 December to the schooner's commander, Lieutenant Sterett. Grouped by subject across the months. Contains those four groups."),
 dict(id='cathcart-circular-of-3-january-1801', parent='bashaw-of-tripoli-war-on-the-united-states-1801', kind='document_group',
      label="The American consul at Tripoli's circular of 3 January 1801 to the agents and consuls of the United States in the Mediterranean",
      definition="Printings of the circular of James L. Cathcart, consul of the United States at Tripoli, dated at the 'Chancery of the United States of America at Tripoli in Barbary, this 3d day of January 1801', 'To the Agents and Consuls of the United States of America residing in the different Ports of France, Spain, Portugal, Italy, the Barbary States and the British Garrisons in the Mediterranean': 'GENTLEMEN, I had the honor to inform you in my Circular of the 12th of November 1800, that certain unjust demands having been made by the Basha of Tripoli upon the United States of America, which I found it my duty to repel; that said Basha had publicly announced in an official manner that he would declare War against the United States of America in six months, to commence from the 22d day of October 1800'; as a treaty of peace had been concluded between Sweden and Tripoli on 3 January, 'it is now no longer safe for the merchant vessels of said United States of America to remain in these seas'. The consul's circular of 21 February ('all hopes of accommodation have subsided'), in 4 papers, is not counted with it. The consul's own circular.",
      role='published_document', words=60, dateline=False,
      core=[r'To\s+the\s+(?:Agents|AGENTS)\s+and\s+(?:Consuls|CONSULS)\s+of\s+the\s+United\s+States\s+of\s+America,?\s+residing'],
      first="The American consul at Tripoli's circular of 3 January 1801: the Basha of Tripoli has announced that he will declare war on the United States.",
      what="the consul's circular of 3 January",
      printings=[k('ORA', '04-18', 3),
                 k('POR', '04-20', 2),
                 k('NHG', '04-21', 3),
                 k('RL', '04-21', 2),
                 k('PJ', '04-22', 3),
                 k('NI', '04-27', 2),
                 k('RG', '04-30', 3)]),
 dict(id='cathcart-circular-of-15-may-1801-war-declared', parent='bashaw-of-tripoli-war-on-the-united-states-1801', kind='document_group',
      label="The American consul at Tripoli's circular of 15 May 1801: 'War was declared in form by the Basha of Tripoli against the United States'",
      definition="Printings of the second circular of the American consul at Tripoli to the agents and consuls of the United States, dated at Tripoli on 15 May 1801: 'GENTLEMEN, IN addition to my circular of the 11th instant, I am sorry to inform you that our flag staff was chopped down upon Thursday the 14th instant, and War was declared in form by the Basha of Tripoli against the United States of America. You will please to give every possible publicity to this circular, and transmit a copy thereof to the Department of State. I shall depart from Tripoli to Tunis in a few days, where I mean to wait the President's orders.' Several papers print 'cut down' for 'chopped down'. The consul's own circular.",
      role='published_document', words=55, dateline=False,
      core=[r'["“]?\s*(?:G\s?ENTLEMEN|Gentlemen)[,.]?\s*["“]?\s*I\s?N\s+addition\s+to\s+my\s+[Cc]ircular', r'I\s?N\s+addition\s+to\s+my\s+[Cc]ircular\s+of\s+the\s+11'],
      first="The American consul at Tripoli's circular of 15 May 1801: war declared by the Basha of Tripoli against the United States.",
      what="the consul's circular of 15 May",
      printings=[k('NI', '08-31', 3),
                 k('ALX', '09-01', 3),
                 k('NHG', '09-08', 3),
                 k('RL', '09-08', 2),
                 k('PJ', '09-09', 2),
                 k('ORA', '09-12', 2),
                 k('POR', '09-14', 1)]),
 dict(id='dale-letter-enterprize-takes-a-tripoline-cruiser-august-1801', parent='bashaw-of-tripoli-war-on-the-united-states-1801', kind='message_group',
      label="Commodore Dale's letter from Malta, 19 August 1801: the schooner Enterprize takes a Tripoline cruiser",
      definition="Printings of the passage of a letter from Commodore Dale, commanding the squadron of frigates the United States sent to the Mediterranean in 1801, to Mr. Gavino, the American consul at Gibraltar, dated Malta, 19 August 1801: 'I am happy to inform you that Mr. Sterrett, in the Schooner Enterprise, of 12 guns, and 90 men, fell in with one of the Tripolitan cruisers off this island ... He took her after an action of three hours ... Not a man hurt on board the Schooner.' Six papers print it as the commodore's letter, in runs of news from Gibraltar; the Republican Ledger and the Rhode-Island Republican print the same passage as a Boston paragraph, 'Lieutenant Sterett, in the Schooner Enterprise ... off the island of Malta', counted with them (C-02). The commodore's own report, as the papers printed it.",
      role='report', words=60, dateline=False,
      core=[r'(?:(?:E\s?XTRACT|Extract)\s+of\s+a\s+)?[Ll](?:ETTER|etter)\s+from\s+[Cc](?:OMMODORE|ommodore)\s+D\s?(?:ALE|ale)'],
      first="Commodore Dale's letter from Malta of 19 August 1801: the schooner Enterprize takes a Tripoline cruiser.",
      what="Commodore Dale's letter on the Enterprize",
      printings=[k('ORA', '11-07', 3),
                 k('POR', '11-09', 2),
                 k('NHG', '11-10', 3),
                 (k('RL', '11-10', 2), {'core': [r'Lieut\w*\.?\s+S\s?(?:TER|ter)+[EIei]?[Tt]+,?\s+in\s+the\s+[Ss](?:CHOONER|chooner)'],
                                        'note': "The Republican Ledger prints the passage as a paragraph, without the commodore's name: 'Lieutenant Steritt, in the Schooner Enterprise ... off the island of Malta'."}),
                 k('PJ', '11-11', 2),
                 (k('RIR', '11-14', 3), {'core': [r'Lieut\w*\.?\s+S\s?(?:TER|ter)+[EIei]?[Tt]+,?\s+in\s+the\s+[Ss](?:CHOONER|chooner)'],
                                         'note': "The Rhode-Island Republican prints the passage as a Boston paragraph of 9 November, 'Capture of a Tripoline Cruiser', without the commodore's name."}),
                 k('NI', '11-16', 3),
                 k('ALX', '11-16', 2)]),
 dict(id='president-letter-to-lieutenant-sterett-1-december-1801', parent='bashaw-of-tripoli-war-on-the-united-states-1801', kind='document_group',
      label="The President's letter to Lieutenant Sterett of the schooner Enterprize, 1 December 1801",
      definition="Printings of the letter dated Washington, 1 December 1801, and signed 'TH: JEFFERSON', to Andrew Sterett, lieutenant and commander of the schooner Enterprize: 'Sir, The secretary of the navy, the regular organ for the present communication, being absent from the seat of government, for causes which may detain him for some time, I do myself the pleasure without further delay, of expressing to you on behalf of your country, the high satisfaction inspired by your conduct in the late engagement with the Tripolitan cruiser captured by you.' Lieutenant Sterett's answer, dated Baltimore, 3 December, which some papers print with it and others a week later, is in 7 papers and is not counted with it (see the README). The President's own letter.",
      role='published_document', words=60, dateline=False,
      core=[r'To\s+A\s?(?:NDREW|ndrew)\s+S\s?(?:TER|ter)+[Ee]?[Tt]+', r'(?:A\s+)?[Ll]etter\s+from\s+the\s+President\s+of\s+the\s+United\s+States\s+to\s+Capt\w*\.?\s+S\s?(?:TER|ter)',
            r'(?:S\s?IR|Sir)[,.]?\s*["“]?\s*(?:T\s?HE|The)\s+[Ss]ecretary\s+of\s+the\s+[Nn]avy,?\s+the\s+regular\s+organ'],
      first="The President's letter of 1 December 1801 to Lieutenant Sterett of the schooner Enterprize.",
      what="the President's letter to Lieutenant Sterett",
      printings=[k('ALX', '12-15', 3),
                 k('PJ', '12-16', 3),
                 k('NI', '12-16', 3),
                 k('RIR', '12-19', 3),
                 k('ORA', '12-19', 2),
                 k('NHG', '12-22', 2),
                 k('RL', '12-22', 2),
                 k('POR', '12-28', 6)]),
 dict(id='nelson-letter-on-the-battle-of-copenhagen-april-1801', kind='document_group',
      label="Lord Nelson's letter on the battle of Copenhagen, 3 April 1801, as the London Gazette published it",
      definition="Printings of the letter of Vice-Admiral Lord Nelson to the commander in chief, Admiral Sir Hyde Parker, dated on board the Elephant, off Copenhagen, 3 April 1801, which the London Gazette published with the admiral's own dispatches: 'In obedience to your directions to report the proceedings of the squadron named in the margin, which you did me the honor to place under my command, I beg leave to inform you that having, by the assistance of that able officer Capt. Riou ... buoyed the channel of the Outer Deep, and the position of the middle ground, the squadron passed in safety', and engaged 'the Danish line'. Several papers head it 'Extract from Lord Nelson's Letter'. A British admiral's own report of a battle, as the London Gazette published it.",
      role='published_document', words=55, dateline=False,
      core=[r"(?:E\s?XTRACT|Extract)\s+(?:FROM|from)\s+(?:L\s?ORD|Lord|L\s?D\.?|Ld\.?)\s+N\s?(?:ELSON|elson)'?\s?[Ss]\s+L\s?(?:ETTER|etter)",
            r'(?:S\s?IR|Sir)[,.]?\s+Elephant,?\s+off\s+Copenhagen', r'Elephant,?\s+off\s+Copenhagen'],
      first="Lord Nelson's letter from off Copenhagen, 3 April 1801, on the action with the Danish line.",
      what="Lord Nelson's letter on Copenhagen",
      printings=[k('ORA', '05-23', 2),
                 k('MON', '05-23', 3),
                 k('POR', '05-25', 2),
                 k('NI', '05-25', 1),
                 (k('NHG', '05-26', 1), {'note': 'The letter opens at the foot of the first page and goes on over the second.'}),
                 k('RL', '05-26', 2),
                 k('PJ', '05-27', 2),
                 k('RG', '05-28', 2)]),
 dict(id='new-haven-remonstrance-and-the-president-reply-july-1801', kind='context_group',
      label="The New Haven remonstrance and the President's reply, 1801: the merchants' remonstrance against the removal of their Collector, and the President's answer of 12 July",
      children=['new-haven-merchants-remonstrance-1801', 'president-reply-to-the-new-haven-remonstrance-july-1801'],
      definition="Two documents that six papers printed together in July and August 1801: the remonstrance in which merchants of New Haven, Connecticut, objected to the President's removal of Elizur Goodrich from the office of Collector of the port and to the appointment of Samuel Bishop, and the President's reply of 12 July 1801. Each side's own words. Contains those two groups."),
 dict(id='new-haven-merchants-remonstrance-1801', parent='new-haven-remonstrance-and-the-president-reply-july-1801', kind='document_group',
      label="The remonstrance of the merchants of New Haven to the President against the removal of their Collector, 1801",
      definition="Printings of the remonstrance addressed 'To THOMAS JEFFERSON, Esq. President of the United States' by merchants of New Haven: 'The undersigned merchants, residing at the port and within the district of New-Haven, respectfully remonstrate against the late removal of Elizur Goodrich, Esq. from the office of Collector for the District of New-Haven, and the appointment of Samuel Bishop, Esq. to fill his vacancy. As the ground of our remonstrance we represent that the office while filled by Mr. Goodrich was conducted with a promptness, integrity and ability, satisfactory to the mercantile interest of this district—promptness and ability not to be found in his successor'; it goes on to Mr. Bishop's age ('seventy-eight years old in November next') and infirmities, says that the business would have to be done by his son, whom it calls 'so entirely destitute of public confidence' that no partisan would have recommended him, and asks the President to reconsider the appointment. It is 'Signed by' four merchants 'and others, to the number of eighty persons', with a certificate, signed by the president of the bank and of the chamber of commerce in New Haven and the president of its insurance company, that the signers own more than seven eighths of the port's shipping. Six papers print it before the President's reply; the New Hampshire Gazette prints the reply without it. It is in 6 papers, below the rule, and stands as a sub-story under a parent that reaches 7 (C-01), so that both sides of the exchange show (the owner's decision of 23 November 2026). The merchants' own remonstrance: an argument against an appointment, with their allegations about the new Collector's fitness and about his son.",
      role='published_document', words=60, dateline=False,
      core=[r'To\s+T\s?(?:HOMAS|homas)\s+J\s?(?:EFFERSON|efferson),?\s+Esq[.;,]*\s+[Pp](?:RESIDENT|resident)\s+of\s+the\s+United\s+States\W+(?:T\s?HE|The)\s+undersigned',
            r'(?:T\s?HE|The)\s+undersigned,?\s+[Mm](?:ERCHANTS|erchants),?\s+residing\s+at\s+the\s+port'],
      first="The merchants of New Haven's remonstrance to the President against the removal of their Collector and the appointment of Samuel Bishop.",
      what="the merchants of New Haven's remonstrance",
      printings=[k('NI', '07-29', 2),
                 k('ORA', '08-01', 2),
                 k('POR', '08-03', 1),
                 k('RL', '08-04', 1),
                 k('PJ', '08-05', 2),
                 k('RG', '08-06', 1)]),
 dict(id='president-reply-to-the-new-haven-remonstrance-july-1801', parent='new-haven-remonstrance-and-the-president-reply-july-1801', kind='document_group',
      label="The President's reply of 12 July 1801 to the remonstrance of the merchants of New Haven",
      definition="Printings of the President's reply, dated Washington, 12 July 1801, to the remonstrance in which merchants of New Haven had objected to the removal of Elizur Goodrich from the office of Collector of New Haven and the appointment of Samuel Bishop: 'Gentlemen, I HAVE received the remonstrance you were pleased to address to me, on the appointment of Samuel Bishop, to the office of Collector of New-Haven, lately vacated by the death of David Austin. The right of our fellow citizens to represent to the public functionaries their opinion on proceedings interesting to them, is unquestionably a constitutional right'. Six papers print it after the merchants' remonstrance (the sub-story beside this one), and the New Hampshire Gazette with its own introduction; pages that quote it in essays and satire are not counted (C-07). The President's own reply.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:G\s?ENTLEMEN|Gentlemen)[,.]?\s+I\s+(?:HAVE|have)\s+received\s+(?:the|your)\s+[Rr](?:EMONSTRANCE|emonstrance)',
            r'I\s+(?:HAVE|have)\s+received\s+(?:the|your)\s+[Rr](?:EMONSTRANCE|emonstrance)\s+you\s+were\s+pleased'],
      first="The President's reply of 12 July 1801 to the remonstrance of the merchants of New Haven on the appointment of their Collector.",
      what="the President's reply to the New Haven remonstrance",
      printings=[k('NI', '07-29', 2),
                 k('ORA', '08-01', 2),
                 k('POR', '08-03', 1),
                 k('NHG', '08-04', 1),
                 k('RL', '08-04', 2),
                 k('PJ', '08-05', 2),
                 k('RG', '08-06', 1)]),
 dict(id='baxter-journal-from-cadiz-august-1801', kind='message_group',
      label="New York, August 1801: Captain Baxter of the brig Huntress, from Cadiz, furnishes an extract from his journal",
      definition="Printings of an extract from the journal of Captain Francis Baxter, of the brig Huntress, who arrived at New York from Cadiz at the beginning of August 1801 'in 39 days' and furnished it to a New York gazette: 'Orders had been received from the French government by the Spanish Consul at Cadiz, to take possession of all captured American property; which was complied with'; 'The king of Spain has given to the French, 12 sail of the line, ready for sea, to be officered and manned by Frenchmen'; it also lists arrivals and captures in the Mediterranean. The papers print it under different introductions, counted together (C-02). The Oracle prints in italics within the extract, after its first paragraph, the words 'A sheer fabrication'. A ship captain's report at second hand, which one paper calls a fabrication.",
      role='report', words=55, dateline=False,
      core=[r'(?:C\s?APT(?:AIN|\.)?|Capt(?:ain|\.)?)\s+(?:F\s?RANCIS|Francis)\s+B\s?(?:AXTER|axter)', r'Capt\w*\.?\s+B\s?(?:AXTER|axter),?\s+who',
            r'(?:E\s?XTRACT|Extract)\s+from\s+the\s+[Jj](?:OURNAL|ournal)\s+of\s+(?:Capt\w*\.?\s+)?B\s?(?:AXTER|axter)', r'B\s?(?:AXTER|axter),?\s+who\s+arrived\s+here'],
      first="New York, August 1801: Captain Baxter, arrived from Cadiz, reports French orders to seize captured American property there.",
      what="Captain Baxter's journal from Cadiz",
      printings=[k('ALX', '08-06', 2),
                 k('NI', '08-07', 3),
                 k('MON', '08-08', 2),
                 k('POR', '08-10', 2),
                 k('NHG', '08-11', 2),
                 k('PJ', '08-12', 2),
                 k('ORA', '08-15', 2)]),
 dict(id='treaty-with-the-cherokees-at-south-west-point-1801', kind='context_group',
      label="The treaty with the Cherokees at South West Point, 1801: a Nashville paragraph on the commissioners' aims, and a Knoxville paragraph that the treaty is broken up",
      children=['nashville-general-wilkinson-and-the-cherokee-treaty-august-1801', 'knoxville-report-cherokee-treaty-broken-up-september-1801'],
      definition="Two paragraphs of Tennessee papers on the meeting of the federal commissioners with the Cherokees at South West Point in 1801, as the papers printed them in September and October: a Nashville paragraph of 12 August on what the commissioners were to seek, and a Knoxville paragraph dated 19 September (9 September in three papers) that the treaty was broken up, the Cherokees refusing to sell lands or to permit roads. Both are the Tennessee papers' accounts; neither is the Cherokees' own. Contains those two groups."),
 dict(id='nashville-general-wilkinson-and-the-cherokee-treaty-august-1801', parent='treaty-with-the-cherokees-at-south-west-point-1801', kind='message_group',
      label="Nashville, 12 August 1801: General Wilkinson sets off for South West Point, 'where a treaty is to be holden with the Cherokees'",
      definition="Printings of a paragraph from Nashville, Tennessee, of 12 August 1801: 'On Monday last, arrived in this town, major general Wilkinson, commander in chief of the army of the United States, and one of the commissioners for treating with the Southern Indians, and yesterday he set off for South West point, where a treaty is to be holden with the Cherokees—one of the objects of negotiation, we learn, is to obtain from the Indians a relinquishment of the tract of country, lying between the Cumberland and Holston settlements, an event so desirable to the citizens of Tennessee'; it adds that the fourth regiment is to open a road from Nashville to the Natchez. A Nashville paper's account of what the commissioners were to seek; the Cherokees' answer is not in it (the Knoxville paragraph of September, the sub-story beside this one, reports their refusal).",
      role='report', words=55, dateline=True,
      core=[r'(?:O\s?N|On)\s+Monday\s+last,?\s+arrived\s+in\s+this\s+town,?\s+[Mm](?:AJOR|ajor)[\s-]*G'],
      first="Nashville, August 1801: General Wilkinson, one of the commissioners for treating with the Southern Indians, sets off for a treaty with the Cherokees.",
      what="the Nashville paragraph on General Wilkinson",
      printings=[k('NI', '09-09', 2),
                 k('ALX', '09-17', 3),
                 k('NHG', '09-22', 3),
                 k('PJ', '09-23', 3),
                 k('POR', '09-28', 2),
                 k('RG', '10-01', 2),
                 k('RIR', '10-03', 3)]),
 dict(id='knoxville-report-cherokee-treaty-broken-up-september-1801', parent='treaty-with-the-cherokees-at-south-west-point-1801', kind='message_group',
      label="Knoxville, 19 September 1801: 'We hear from South West Point that the treaty with the Cherokees is broken up'",
      definition="Printings of a paragraph dated Knoxville, Tennessee, 19 September 1801 (9 September in three papers): 'We hear from South West Point that the treaty with the Cherokees is broken up, the commissioners not being able to effect the object of their appointment. The Cherokees refuse to sell lands, or to permit roads being cut through their country. Doublehead concluded his last talk with saying \"That the Indians do not wish to be spoken to on that subject.\" He then addressed the people of Tennessee, and said \"That the white people owed them three lives: that they had waited some time for satisfaction, and would wait yet longer, but were determined on retaliation.\"' The Alexandria Advertiser and the Providence Journal print 'do not wish to be again spoken to'; the three Portsmouth papers (the New Hampshire Gazette, the Oracle and the Republican Ledger) date the paragraph 'Sept. 9' and print 'did not wish to be again spoken to' and 'the white people owed them their lives' (read on the scans). A Knoxville paper's report at second hand ('We hear'), with Doublehead's words as the paper gives them; not the Cherokees' own account. It is in 6 papers, below the rule, and stands as a sub-story under a parent that reaches 7 (C-01), so that both sides of the affair show (the owner's decision of 23 November 2026). A paragraph that reports the rumour in other words (the Republican Gazette, 29 October) is not counted (C-07).",
      role='report', words=40, dateline=True,
      core=[r'(?:W\s?E|We)\s+hear\s+from\s+South[\s-]+We\w{1,3}\s+[Pp]oint,?\s+that\s+the\s+treaty'],
      first="Knoxville, September 1801: the treaty with the Cherokees at South West Point is broken up; the Cherokees refuse to sell lands or to permit roads.",
      what="the Knoxville paragraph on the Cherokee treaty",
      printings=[k('NI', '10-07', 3),
                 k('ALX', '10-07', 3),
                 k('NHG', '10-13', 3),
                 k('PJ', '10-14', 2),
                 k('ORA', '10-17', 2),
                 k('RL', '10-27', 2)]),
 dict(id='census-of-1800-total-population-september-1801', kind='message_group',
      label="Washington, September 1801: 'The total population of the United States, as taken in 1790, amounted to 3,929,326. The present census amounts to 5,064,801'",
      definition="Printings of the National Intelligencer's paragraph of 16 September 1801 on the returns of the second census: 'The total population of the United States, as taken in 1790, amounted to 3,929,326. The present census amounts to 5,064,801. In this statement Tennessee is wanting, the numbers of which state, with those deficient in N. York and Maryland, may be estimated at 150,000'; it goes on to the increase in ten years and to the numbers of slaves in 1790 and in the new returns, with the paper's own calculation. The Oracle prints the increase as 1,185,475 (the others 1,285,475), and the Republican Gazette gives the paragraph in shorter words ('more than 5,166,877'). The government paper's statement of the census returns and its own reckoning.",
      role='report', words=50, dateline=False,
      core=[r'(?:T\s?HE|The)\s+total\s+population\s+of\s+the\s+United\s+States,?\s+as\s+taken\s+in'],
      first="Washington, September 1801: the census returns put the population of the United States at 5,064,801.",
      what="the paragraph on the census",
      printings=[k('NI', '09-16', 3),
                 k('ALX', '09-17', 3),
                 k('RIR', '10-03', 3),
                 k('ORA', '10-03', 2),
                 k('PJ', '10-07', 1),
                 k('RL', '10-13', 2),
                 k('RG', '10-15', 2)]),
 dict(id='london-account-second-attack-on-boulogne-august-1801', kind='message_group',
      label="London, 17 August 1801: 'A second attack has been made upon the flotilla at Boulogne, and we are sorry to state, that it has not been attended with the desired success'",
      definition="Printings of a London account of 17 August 1801 of the second attack by Lord Nelson's boats on the French flotilla at Boulogne: 'A second attack has been made upon the flotilla at Boulogne, and we are sorry to state, that it has not been attended with the desired success. Late last night the Providence cutter arrived at Dover with dispatches from Lord Nelson. The attack commenced at about a quarter flood, at 12 o'clock on Saturday night. Our squadron, consisting of 70 boats, was divided into four divisions'. The Alexandria Advertiser prints 'the desired effect' and 'on Sunday night', and the Portland Gazette 'very sorry'; the Republican Gazette leaves out the sentence on the Providence cutter; the Rhode-Island Republican prints the account from its third sentence, under the heading 'Second Attack on Boulogne'. All are counted together (C-02). A London paper's account at second hand of the dispatches.",
      role='report', words=60, dateline=True,
      core=[r'A\s+(?:S\s?ECOND|Second|second)\s+attack\s+has\s+been\s+made\s+upon\s+the'],
      first="London, 17 August 1801: a second attack by Lord Nelson's boats on the flotilla at Boulogne has not succeeded.",
      what="the London account of the attack on Boulogne",
      printings=[k('NHG', '09-29', 3),
                 k('ORA', '10-03', 2),
                 (k('RIR', '10-03', 3), {'core': [r'(?:S\s?ECOND|Second)\s+(?:A\s?TTACK|Attack)\s+on\s+B\s?(?:OULOGNE|oulogne)\W+(?:T\s?HE|The)\s+attack\s+commenced',
                                                  r'(?:T\s?HE|The)\s+attack\s+commenced\s+(?:at\s+)?about\s+a\s+quarter'],
                                         'note': "The Rhode-Island Republican prints the account from its third sentence, 'The attack commenced at about a quarter past 12 o'clock on Saturday night'."}),
                 k('POR', '10-05', 2),
                 k('RL', '10-06', 2),
                 k('ALX', '10-06', 2),
                 k('PJ', '10-07', 2),
                 k('NI', '10-07', 4),
                 k('RG', '10-08', 2)]),
 dict(id='london-surrender-of-cairo-confirmed-august-1801', kind='message_group',
      label="London, 15 August 1801: 'The intelligence of the surrender of Cairo is confirmed'",
      definition="Printings of a London paragraph of 15 August 1801: 'The intelligence of the surrender of Cairo is confirmed. Two messengers arrived yesterday with dispatches from Constantinople and Vienna to government and the East India Company. The dispatches to government are from Lord Minto, who continues to congratulate his majesty's ministers on the fall of Cairo. The dispatches, however, to the East India Company, place the intelligence beyond all doubt.' Five of the papers print after it the letter it introduces, from Peter Tooke at Constantinople of 19 July ('I had the honor to address you, on the 17th inst. by an express courier, in order to inform you of the reduction of the castle and city of Cairo by his majesty's and the Ottoman armies'), which is in 7 papers with the Rhode-Island Republican and the Republican Gazette and is not counted with it (see the README). A London paper's report at second hand.",
      role='report', words=55, dateline=True,
      core=[r'(?:T\s?HE|The)\s+intelligence\s+of\s+the\s+surrender\s+of\s+Cairo,?\s+is\s+confirmed'],
      first="London, 15 August 1801: dispatches from Constantinople and Vienna confirm the surrender of Cairo.",
      what="the London paragraph on Cairo",
      printings=[k('NHG', '09-29', 3),
                 k('RL', '09-29', 2),
                 k('NI', '10-02', 1),
                 k('ALX', '10-02', 2),
                 k('ORA', '10-03', 2),
                 k('POR', '10-05', 2),
                 k('PJ', '10-07', 2)]),
 dict(id='court-martial-on-captain-little-september-1801', kind='document_group',
      label="The sentence of the court martial on Captain George Little, 7 September 1801, with the Secretary of the Navy's letter of 25 September",
      definition="Printings of the sentence of the court martial held on board the frigate Constitution on Captain George Little, of the frigate Boston, on charges brought by officers of the French corvette Le Berceau, which the Boston had taken in 1800: 'The Court, having heard all the evidence, and prisoner's defence, and maturely and seriously considered the whole, are unanimously of opinion, that the charges are malicious and ill-founded. The Court do, therefore, unanimously and honorably acquit the said Capt. George Little', dated on board the Constitution, 7 September 1801, and signed by the president of the court and its members; with the letter of the Navy Department of 25 September 1801, which approves the sentence and states that 'The evidence adduced in this trial clearly proves, that the prisoners on board the prize have been pillaged' by some persons belonging to the Boston. Several papers print them after a Boston paper's comment on the trial ('The trial of Captain Little ... has excited much sensibility in the breasts of every real friend to the American navy'). The court martial's own sentence and the Navy Department's own letter.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:T\s?HE|The)\s+[Cc](?:OURT|ourt),?\s+having\s+heard\s+all\s+the\s+evidence'],
      first="The court martial of 7 September 1801 acquits Captain George Little of the charges brought by officers of the French corvette Le Berceau.",
      what="the court martial's sentence on Captain Little",
      printings=[k('RIR', '10-31', 2),
                 k('ORA', '10-31', 2),
                 k('POR', '11-02', 2),
                 k('NHG', '11-03', 2),
                 k('RL', '11-03', 2),
                 k('PJ', '11-04', 2),
                 k('ALX', '11-06', 3),
                 k('NI', '11-13', 1)]),
 dict(id='john-appleton-brings-the-ratified-convention-october-1801', kind='message_group',
      label="Boston, October 1801: 'Mr. John Appleton, the official bearer of the ratified treaty between the United States and France, arrived here yesterday'",
      definition="Printings of a Boston paragraph of October 1801: 'Mr. JOHN APPLETON, the official bearer of the ratified treaty between the United States and France, arrived here yesterday in the brig Reward, from Dieppe.' The treaty is the convention of 30 September 1800 with the French Republic, which the Senate ratified with conditions in February 1801 and the First Consul in July. A Boston paper's notice.",
      role='report', words=24, dateline=True,
      core=[r'(?:M\s?[Rr]\.?\s+)?J\s?(?:OHN|ohn)\s+A\s?(?:PPLETON|ppleton),?\s+the\s+official\s+bearer'],
      first="Boston, October 1801: the bearer of the ratified convention between the United States and France arrives from Dieppe.",
      what="the Boston paragraph on Mr. Appleton's arrival",
      printings=[k('NHG', '10-27', 3),
                 k('RL', '10-27', 2),
                 k('PJ', '10-28', 3),
                 k('RIR', '10-31', 3),
                 k('ORA', '10-31', 3),
                 k('NI', '11-02', 3),
                 k('ALX', '11-03', 3)]),
 dict(id='preliminary-articles-of-peace-britain-and-france-october-1801', kind='document_group',
      label="The preliminary articles of peace between Great Britain and the French Republic, signed at London on 1 October 1801",
      definition="Printings of the preliminary articles of peace signed at London on 1 October 1801 by Lord Hawkesbury for the King and by Citizen Louis William Otto for the First Consul: 'His Majesty the King of the United Kingdom of Great-Britain and Ireland, and the First Consul of the French Republic, in the name of the French people, being animated with an equal desire of putting a stop to the calamities of a destructive war, and to re-establish harmony and good understanding between the two nations'; the first article reads 'As soon as the Preliminaries shall be signed and ratified, sincere friendship shall be re-established'. Three papers print the English text; four (the Alexandria Advertiser, the National Intelligencer, the Rhode-Island Republican and the New Hampshire Gazette) print a translation from the Moniteur, which names the First Consul first; and the Oracle, in an extraordinary of 2 December and again in its issue of 5 December, its own translation from French papers. All are counted together (C-02). The two governments' own articles.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:T\s?HE|The)\s+(?:F\s?IRST|First|first)\s+Consul\s+of\s+the\s+French\s+Republic,?\s+in\s+the\s+name\s+of\s+the\s+French\s+people,?\s+and\s+his\s+[Mm]ajesty',
            r'(?:H\s?IS\s+M\s?AJESTY|His\s+[Mm]ajesty)\s+the\s+[Kk](?:ING|ing)\s+of\s+the\s+[Uu](?:NITED|nited)\s+[Kk](?:INGDOMS?|ingdoms?)\s+of\s+Great[\s-]*Britain'],
      first="The preliminary articles of peace between Great Britain and the French Republic, signed at London on 1 October 1801.",
      what="the preliminary articles of peace",
      printings=[k('ALX', '11-26', 3),
                 k('NI', '11-27', 1),
                 (k('ORA', '12-02', 1), {'note': "The Oracle's extraordinary of Wednesday 2 December prints its own translation from French papers brought by the brig Hannah from Bordeaux."}),
                 k('RIR', '12-05', 2),
                 (k('ORA', '12-05', 1), {'note': "Printed again in the Oracle's issue of Saturday 5 December, in the translation of its extraordinary of 2 December."}),
                 k('POR', '12-07', 2),
                 k('NHG', '12-08', 2),
                 k('RL', '12-08', 2),
                 k('PJ', '12-09', 2)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797, 1800 and 1803): "MONTICELLO, SEPT. 4, 1800."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
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
            problems.append((s['id'], key, 'page not in the 1801 pages'))
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
        r['id'] = f'S01-{n:03}'
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
               'admission_rule': 'Reviewed 1801 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1801/'
    return {
        'ledger_id': 'ledger:stories-1801', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1801', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1801, and of 1800 where they reach the 1801 pages (long-running ones '
                   'included), a sweep of word-for-word passages shared by 7 or more papers for short items the families miss, phrase searches on '
                   'all 2,372 pages of 1801 in both transcriptions, reading of every hit, and scan checks of each admitted passage, by the one '
                   'admission rule (9 or more papers admitted, 7 or 8 chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1800.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1801.py': 'ledger_code', 'work/archive_data/ledgers/stories_1801_review.json': 'scan_review',
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
