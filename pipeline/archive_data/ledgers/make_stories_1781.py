"""Write ledgers/stories_1781.json: reviewed stories of 1781, round one.

1781 is read by the thin-year rule the owner chose on 23 November 2026 (docs/rules-and-exceptions.md, Y-THIN), as amended the
same night (the owner's choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the
newspapers that survive for its weeks, and by at least 4 newspapers; digests are not. The newspapers that survive for an item's
weeks are those with an eligible issue between its first and last printing, and at least in the three weeks from its first
printing. As in R-01, the eligible items printed by every newspaper that survives for their weeks are admitted, and the other
eligible items are chosen to cover the months and the kinds of news, about as many stories as a standard year (a target, not a
quota); one affair's items are handled as in X-1800-01. Sub-stories (C-01), private persons (R-04) and the list of items read and
not admitted (R-03) apply as in every year (outputs/story_discovery_1781/README.md).

The automatic families first printed in 1781 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1780 over the 1781 pages
(items_from_1780.json); every item in 3 or more papers was counted by machine, by about 100 words from the finder's position,
over every page, and the counts were joined into documents; the admitted and chosen items were counted again by about 70 words
from their own opening (counts_1781.json). The 1781 pages are those whose issue the data release dates to 1781
(work/year_search_pages.py 1781 ... --printed-dates). 1781 has 7 catalogue series, which are 6 papers (C-04): the Portsmouth
New-Hampshire Gazette under two catalogue numbers (sn83025584 to 3 September, sn83025585 from 8 September). The New-York
Gazette and the Royal Gazette of Charleston are printed under British occupation.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1781_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1781.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1781/search_pages.json).
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1781'
D = PROJECT/'outputs/story_discovery_1781'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1781_review.json'
OUT = HERE/'stories_1781.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83021127': 'The Pennsylvania Packet', 'sn83025789': 'The Royal Gazette (Charleston)', 'sn83025471': 'The New-Jersey Gazette',
         'sn84023855': 'The Connecticut Courant', 'sn83030493': 'The New-York Gazette, and the Weekly Mercury',
         'sn83025584': 'The New-Hampshire Gazette', 'sn83025585': 'The New-Hampshire Gazette'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, filed date (MM-DD in 1781), page and edition. The New-Hampshire Gazette has two
    catalogue numbers in 1781 (C-04); the date picks it."""
    if paper == 'NHG':
        lccn = 'sn83025584' if date <= '09-03' else 'sn83025585'
    else:
        lccn = {'PP': 'sn83021127', 'RGC': 'sn83025789', 'NJG': 'sn83025471', 'CC': 'sn84023855', 'NYG': 'sn83030493'}[paper]
    return f'{lccn}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()
AGAIN = {'note': 'Printed again.'}
LG = r'(?:From\s+the\s+)?LONDON\s+GAZETTE,?\s+EXTRA\W*ORDINARY\.?\s*'
# Story groups. A parent ('context_group') lists its children and has no printings. 'printings' lists each printing's page;
# a tuple adds overrides for that printing: core (regexes for the item's first words), role, field, note, words, dateline
# (include a dateline directly before), head (a regex for a heading that ends directly before the core: the excerpt starts
# with it), back (start at the beginning of the sentence that holds the core), stop (a regex: the excerpt ends before it).
STORIES = [
 dict(id='richmond-report-of-a-repulse-of-tarletons-legion-december-1780', kind='document_group',
      label="Richmond, 30 December 1780: a report from the southern army that Colonel Tarleton's legion received a severe repulse",
      definition="Printings of a Richmond paragraph of 30 December 1780: 'By an officer, immediately from the southern army, we have the agreeable and certain intelligence, that on the 10th instant colonel Tarleton's legion, commanded by himself in person, received a severe repulse in an attempt to surprize colonels Marian and Clarke'. A Virginia paper's report, from an officer's account.",
      role='report', words=50, dateline=True,
      core=[r'By\s+an\s+officer,?\s+immediately\s+from\s+the\s+southern\s+army'],
      first="Richmond, 30 December 1780: a report from the southern army that Colonel Tarleton's legion received a severe repulse.",
      what="the Richmond report of a repulse of Colonel Tarleton's legion",
      printings=[k('PP', '01-09', 3), k('NJG', '01-17', 1), k('NYG', '01-22', 2), k('CC', '01-23', 2), k('NHG', '01-29', 2)]),
 dict(id='kings-speech-to-parliament-6-november-1780', kind='document_group',
      label="The King's speech to both Houses of Parliament at the opening of the new Parliament, 6 November 1780",
      definition="Printings of the King's speech opening the new Parliament: 'My Lords and Gentlemen, It is with more than ordinary satisfaction that I meet you in Parliament, at a time when the late elections may afford an opportunity of receiving the most certain information of the disposition and the wishes of my people'. The King's own words, as the papers printed them from London papers.",
      role='published_document', words=50, dateline=False,
      core=[r'My\s+Lords\s+and\s+Gentlemen,?\W*It\s+is\s+with\s+more\s+than\s+ordinary\s+satisfaction'],
      first="The King's speech to both Houses of Parliament, 6 November 1780.",
      what="the King's speech of 6 November 1780",
      printings=[k('NYG', '02-05', 2), k('PP', '02-10', 2), k('NJG', '02-14', 2), k('CC', '02-20', 3), k('NHG', '02-26', 1)]),
 dict(id='morgan-to-greene-on-the-action-at-the-cowpens-january-1781', kind='document_group',
      label="General Morgan to General Greene, Camp near Cain Creek, 19 January 1781: his account of the action at the Cowpens",
      definition="Printings of General Morgan's letter to General Greene of 19 January 1781: 'The troops I have the honor to command, have gained a compleat victory over a detachment from the British army, commanded by lieutenant colonel Tarleton. The action happened on the 17th instant, about sun-rise, at a place called the Cowpens, near Pacolet river'. General Morgan's own account, sent to Congress by General Greene.",
      role='published_document', words=50, dateline=False,
      head=r'Camp,?\s+near\s+Cain\s+Creek,?\s+Jan\w*\.?\s*19,?\s*1781\.?\s*(?:Dear\s+)?S\s?I\s?R,?\s*',
      core=[r'T\s?HE\s+troops\s+I\s+have\s+the\s+hono\w*\s+to\s+command,?\s+have\s+gained\s+a\s+compl?ea?te?\s+victory'],
      first="General Morgan to General Greene, 19 January 1781: his account of the action at the Cowpens.",
      what="General Morgan's letter on the action at the Cowpens",
      printings=[k('PP', '02-10', 2), k('NJG', '02-14', 2), k('CC', '02-20', 2), k('NHG', '02-26', 1)]),
 dict(id='philadelphia-intelligence-from-the-southward-3-march-1781', kind='document_group',
      label="Philadelphia, 3 March 1781: intelligence from the southward on General Morgan's prisoners and Lord Cornwallis's pursuit",
      definition="Printings of a Philadelphia paragraph of 3 March 1781: 'Intelligence from the Southward. By authentic advices we learn, That General Morgan collected near one hundred prisoners, by parties sent out for the purpose, after the account he gave in his letter to general Greene, dated the 19th of January last. That upon receiving the news of Tarleton's defeat, lord Cornwallis marched with his army in pursuit'. A Philadelphia paper's report from advices.",
      role='report', words=50, dateline=True,
      core=[r'(?:Intelligence\s+from\s+the\s+Southward\.?\s*)?\W?By\s+authentic\w*\s+advices\s+we\s+learn,?\s+that\s+Gen\w*\.?\s+Morgan'],
      first="Philadelphia, 3 March 1781: intelligence from the southward on General Morgan's prisoners and Lord Cornwallis's pursuit.",
      what="the Philadelphia intelligence from the southward of 3 March",
      printings=[k('PP', '03-03', 2), k('NJG', '03-07', 2), k('NYG', '03-12', 1), k('CC', '03-13', 2), k('NHG', '03-19', 1), k('RGC', '03-31', 3)]),
 dict(id='britain-and-the-united-provinces-december-1780', kind='context_group',
      label="Britain and the United Provinces, December 1780: the King's manifesto and the order for general reprisals, as the papers printed them in 1781",
      children=['kings-manifesto-against-the-united-provinces-december-1780', 'order-for-general-reprisals-against-the-united-provinces-20-december-1780'],
      definition="The King's manifesto against the States General of the United Provinces and the order of the King in Council of 20 December 1780 for general reprisals against their ships, goods and subjects, as the papers printed them from London papers in March, April and May 1781. The British government's own words."),
 dict(id='kings-manifesto-against-the-united-provinces-december-1780', parent='britain-and-the-united-provinces-december-1780', kind='document_group',
      label="The King's manifesto against the States General of the United Provinces (London Gazette Extraordinary, 21 December 1780)",
      definition="Printings of the King's manifesto: 'MANIFESTO. GEORGE R. Through the whole course of our reign, our conduct towards the States General of the United Provinces has been that of a sincere friend and faithful ally'; it sets out the King's complaints against the Republic. The King's own words, from the London Gazette Extraordinary of 21 December 1780.",
      role='published_document', words=50, dateline=False,
      head=LG + r'(?:THURSDAY,?\s+)?Dec\w*\.?\s+21,?\s*1780\.?\s*',
      core=[r'MANIFESTO\.?\s*GEORGE\s+R\.?\s*THROUGH\s+the\s+whole\s+course', r'THROUGH\s+the\s+whole\s+course\s+of\s+our\s+reign,?\s+our\s+conduct\s+towards\s+the\s+States\s+General'],
      first="The King's manifesto against the States General of the United Provinces, December 1780.",
      what="the King's manifesto against the United Provinces",
      printings=[k('NYG', '03-19', 1), k('PP', '03-20', 2), (k('RGC', '03-24', 3), {'head': '(?:From\\s+the\\s+)?LONDON\\s+GAZETTE,?\\s+EXTRA\\W*ORDINARY[.,]?\\s*(?:THURSDAY,?\\s+)?Dec\\w*\\.?\\s+21,?\\s*1780\\.?\\s*'}), k('NJG', '03-28', 1), k('CC', '04-03', 3)]),
 dict(id='order-for-general-reprisals-against-the-united-provinces-20-december-1780', parent='britain-and-the-united-provinces-december-1780', kind='document_group',
      label="The King in Council, 20 December 1780: general reprisals to be granted against the ships, goods and subjects of the States General of the United Provinces",
      definition="Printings of the order of the King in Council: 'At the Court at St. James's, the 20th of December, 1780. Present, the King's most excellent Majesty in Council. His Majesty having taken into consideration the many injurious proceedings of the States General of the United Provinces, and their subjects, as set forth in his royal manifesto of this date ... is pleased ... to order, and it is hereby ordered, That general reprisals be granted against the ships, goods, and subjects, of the States General of the United Provinces'. An order of the King in Council.",
      role='published_document', words=50, dateline=False,
      core=[r'At\s+the\s+Court\s+at\s+St\.?\s*James\W?s,?\s+the\s+20th', r'James\W?s,?\s+the\s+20th\s+(?:of\s+)?December,?\s+1780', r'Court\s+of\s+St\.?\s*James\W?s,?\s+the\s+\w+\s+of\s+Dec\w*\.?\s+1780', r'H\s?IS\s+Majesty,?\s+having\s+taken\s+into\s+consideration\s+the\s+many\s+injurious'],
      first="The King in Council, 20 December 1780: general reprisals against the States General of the United Provinces.",
      what="the order in council for general reprisals against the United Provinces",
      printings=[k('NYG', '03-19', 1), k('PP', '03-20', 3), k('RGC', '03-24', 3), k('NJG', '03-28', 1), k('NHG', '04-02', 1), k('CC', '04-10', 2)]),
 dict(id='account-of-the-action-off-the-chesapeake-16-march-1781', kind='document_group',
      label="Royal Oak, Lynnhaven Bay, 21 March 1781: the British account of the action of 16 March between the British and French squadrons off the Chesapeake",
      definition="Printings of the account dated 'Royal Oak, Lynhaven Bay, March 21, 1781. On Friday the 16th instant, at 6 A. M. the Iris made the signal for discovering five strange sail to the N. N. E.', which a New York paper introduces as 'an account of an action fought on the 16th, between the British and French squadrons, off the Chesapeake', brought by an officer of Vice-Admiral Arbuthnot's flagship. The British squadron's account.",
      role='report', words=50, dateline=False,
      core=[r'Royal\s+Oak,?\s*Lyn\W*h?aven\s+Bay,?\s*March\s+21', r'On\s+Friday\s+the\s+16th\s+instant,?\s+at\s+6\s+A\.?\s*M\.?\s+the\s+Iris\s+made\s+the\s+signal'],
      first="Royal Oak, Lynnhaven Bay, 21 March 1781: the British account of the action of 16 March off the Chesapeake.",
      what="the British account of the action of 16 March off the Chesapeake",
      printings=[k('NYG', '04-02', 2), k('PP', '04-03', 2), k('NJG', '04-11', 2), k('NHG', '04-16', 1), k('CC', '04-17', 1), k('RGC', '04-28', 1)]),
 dict(id='greene-to-congress-iron-works-10-march-1781', kind='document_group',
      label="General Greene to the President of Congress, Head Quarters, Iron Works, North Carolina, 10 March 1781",
      definition="Printings of General Greene's letter to the President of Congress of 10 March 1781: 'Since I had the honour of addressing your excellency last, there have been some changes in our circumstances. On the second, Lieut. Col. Lee, with a detachment of riflemen, attacked the advance of the British army, under col. Tarleton, near Allamance'. General Greene's own account.",
      role='published_document', words=50, dateline=False,
      core=[r'Head\s*[- ]?Quarters,?\s*Iron[- ]?Works', r'S\s?INCE\s+I\s+had\s+the\s+hono\w*\s+of\s+addressing\s+your\s+excellency\s+last'],
      first="General Greene to the President of Congress, Iron Works, North Carolina, 10 March 1781.",
      what="General Greene's letter of 10 March 1781",
      printings=[k('PP', '04-03', 2), k('NJG', '04-04', 3), k('NYG', '04-09', 1), k('CC', '04-17', 2), k('NHG', '04-23', 1), k('RGC', '05-19', 1)]),
 dict(id='letter-from-st-eustatius-14-february-1781', kind='document_group',
      label="A letter from St. Eustatius of 14 February 1781, after the island was taken by the British",
      definition="Printings of an extract of a letter from St. Eustatius dated 14 February 1781: 'The strictest discipline and decorum is kept up by the military here; a bomb battery and several new fortifications are constructing'. The Royal Gazette of Charleston prints it under 'Basseterre, (St. Christopher) Feb. 15'. A letter-writer's account from the island.",
      role='report', words=50, dateline=True,
      core=[r'(?:The\s+following\s+is\s+an\s+)?[Ee]xtract\s+of\s+a\s+letter\s+from\s+St\.?\s*Eustatius,?\s+dated\s+Feb', r'The\s+strictest\s+discipline\s+and\s+decorum\s+is\s+kept\s+up'],
      first="A letter from St. Eustatius of 14 February 1781, after the island was taken by the British.",
      what="the letter from St. Eustatius of 14 February",
      printings=[k('RGC', '04-04', 2), (k('PP', '04-14', 3), {'head': 'FEBRUARY\\s+15\\.\\s*'}), k('NYG', '04-16', 1), (k('NJG', '04-18', 2), {'head': 'February\\s+15\\.\\s*'}), k('CC', '04-24', 2), k('NHG', '05-07', 2)]),
 dict(id='cornwallis-proclamation-after-the-action-of-15-march-1781', kind='document_group',
      label="Lord Cornwallis's proclamation after the action of 15 March 1781, calling on loyal subjects to take an active part",
      definition="Printings of Lord Cornwallis's proclamation: 'By Charles Earl Cornwallis, Lieutenant General of his Majesty's Forces, &c. Proclamation. Whereas, by the blessing of Almighty God, his Majesty's arms have been crowned with signal success, by the complete victory obtained over the rebel forces on the 15th instant, I have thought proper to issue this proclamation, to call upon all loyal subjects to stand forth'. Lord Cornwallis's own words; some papers print it with comments of their own.",
      role='published_document', words=50, dateline=False,
      core=[r'By\s+CHARLES,?\s+EARL\s+CORNWALLIS', r'WHEREAS,?\s+by\s+the\s+blessing\s+of\s+Almighty\s+God,?\s+his\s+Majesty\W?s\s+arms'],
      first="Lord Cornwallis's proclamation after the action of 15 March 1781.",
      what="Lord Cornwallis's proclamation",
      printings=[k('PP', '04-21', 3), k('NJG', '04-25', 2), k('CC', '05-01', 2), k('NHG', '05-07', 1), k('NYG', '05-07', 2), k('RGC', '07-28', 4)]),
 dict(id='plan-for-a-national-bank-may-1781', kind='document_group',
      label="The plan for a national bank for the United States, submitted to Congress on 17 May 1781",
      definition="Printings of 'To the Public. On the 17th day of May, 1781, the following plan was submitted to the consideration of the United States, in Congress assembled. Plan for establishing a National Bank, for the United States of North-America. I. That a subscription be opened for four hundred thousand dollars, in shares of four hundred dollars each'. The plan and the papers printed with it, as published.",
      role='published_document', words=50, dateline=False,
      core=[r'TO\s+THE\s+PUBLIC\.?\s+On\s+the\s+17th\s+day\s+of\s+May', r'Plan\s+for\s+establishing\s+a\s+National\s+Bank'],
      first="The plan for a national bank, submitted to Congress on 17 May 1781.",
      what="the plan for a national bank",
      printings=[k('PP', '05-29', 2), k('NJG', '06-06', 1), k('NYG', '06-11', 2), k('CC', '06-12', 2), k('NHG', '06-25', 1)]),
 dict(id='de-barras-arrives-at-boston-may-1781', kind='document_group',
      label="Boston, 10 May 1781: Rear-Admiral de Barras arrives from Brest in the frigate la Concorde",
      definition="Printings of a Boston paragraph of 10 May 1781: 'Last Sunday arrived in this harbour, after a passage of about 6 weeks from Brest, M. M. de Barras, Rear Admiral appointed to the chief command of the squadron of his most Christian Majesty at Newport, in the frigate la Concorde'. A Boston paper's report.",
      role='report', words=50, dateline=True,
      core=[r'(?:LAST|Last)\s+Sunday\s+arrived\s+in\s+this\s+[Hh]arbour,?\s+after\s+a\s+[Pp]assage\s+of\s+(?:about\s+)?6\s+[Ww]eeks\s+from\s+Brest'],
      first="Boston, 10 May 1781: Rear-Admiral de Barras arrives from Brest.",
      what="the Boston report of Rear-Admiral de Barras's arrival",
      printings=[k('NHG', '05-14', 1), k('CC', '05-15', 2), k('PP', '05-22', 3), (k('NJG', '05-23', 2), {'head': 'May\\s+10\\.\\s*'}), k('NYG', '05-28', 2)]),
 dict(id='letter-from-newcastle-virginia-28-may-1781', kind='document_group',
      label="A letter from Newcastle, Virginia, 28 May 1781: Lord Cornwallis has joined General Arnold at Petersburg",
      definition="Printings of an extract of a letter dated 'Newcastle, 18 miles this side of Richmond, May 28, 1781': 'Yesterday was a week since Cornwallis joined Arnold (Philips being dead of a fever) at Petersburg; the latter had 3500 men, the former 1500'. A letter-writer's account, as a Philadelphia paper printed it.",
      role='report', words=50, dateline=True,
      core=[r'Extract\s+of\s+a\s+letter,?\s+dated\s+New\W?Castle'],
      first="A letter from Newcastle, Virginia, 28 May 1781: Lord Cornwallis has joined General Arnold at Petersburg.",
      what="the letter from Newcastle, Virginia, of 28 May",
      printings=[k('PP', '06-09', 3), k('NJG', '06-13', 2), k('NYG', '06-18', 2), k('CC', '06-19', 2), k('NHG', '06-25', 2)]),
 dict(id='lafayette-to-greene-27-june-1781', kind='document_group',
      label="The Marquis de Lafayette to General Greene, near Williamsburg, 27 June 1781, sent to Congress with his letter of 28 June",
      definition="Printings of the Marquis de Lafayette's letter to General Greene dated 'Mr. Tyree's plantation, 20 miles from Williamsburg, June 27, 1781': 'My letter of the 28th informed you of the enemy's retrograde movement to Richmond, where they had made a stop'; it goes on to the action of the advanced corps under Colonel Butler. The Marquis's own account; the Pennsylvania Packet prints it after his covering letter to the President of Congress.",
      role='published_document', words=50, dateline=False,
      head=r"(?:Mr\W*\s*)?Tyre\w*\W?s\s+[Pp]lantation.{0,60}?(?:June\s+2[78]|2[78]th\s+June),?\s*1781\.?\s*S\s?I\s?R,?\s*",
      core=[r'(?:MY|My)\s+letter\s+of\s+the\s+[12]8th\s+informed\s+you\s+of\s+the\s+enemy\W?s\s+retrograde'],
      first="The Marquis de Lafayette to General Greene, near Williamsburg, 27 June 1781.",
      what="the Marquis de Lafayette's letter to General Greene of 27 June",
      printings=[k('PP', '07-07', 3), k('NJG', '07-11', 2), (k('NYG', '07-16', 2), {'field': CA, 'note': 'RevX lacks the opening of this item on this page, so the excerpt comes from the older CA transcription.'}),
                 k('CC', '07-24', 2), (k('RGC', '07-25', 3), {'head': 'Mr\\W*\\s*Tyre\\w*\\W?s\\s+[Pp]lantation.{0,60}?S\\s?I\\s?R,?\\s*June\\s+27,?\\s*1781\\.?\\s*'}), k('NHG', '07-30', 2)]),
 dict(id='congress-on-a-loan-for-citizens-of-south-carolina-and-georgia-23-july-1781', kind='document_group',
      label="Congress, 23 July 1781: a loan and donations for citizens of South Carolina and Georgia driven from their country",
      definition="Printings of the resolutions of Congress of 23 July 1781: 'Resolved, That five suitable persons be appointed and authorized to open a subscription for a loan of thirty thousand dollars, for the support of such of the citizens of the States of South-Carolina and Georgia, as have been driven from their country'. The resolutions of Congress.",
      role='published_document', words=50, dateline=False,
      core=[r'By\s+the\s+UNITED\s+STATES\s+in\s+Congress\s+[Aa]ssembled,?\s+July\s+23', r'RESOLVED,?\s+THAT\s+five\s+suitable\s+persons\s+be\s+appointed'],
      first="Congress, 23 July 1781: a loan and donations for citizens of South Carolina and Georgia driven from their country.",
      what="the resolutions of Congress of 23 July 1781",
      printings=[k('PP', '07-28', 2), k('CC', '08-14', 2), k('NHG', '08-20', 1), k('NJG', '08-22', 1)]),
 dict(id='london-on-the-capture-of-the-st-eustatius-convoy-may-1781', kind='document_group',
      label="London, 17 May 1781: reports after the capture of the convoy from St. Eustatius",
      definition="Printings of a London paragraph of 17 May 1781: 'Since the news of the unfortunate capture of our Eustatia fleet on the 2d current, the public has been pestered with a variety of reports concerning them'. A London paper's report, as the American papers printed it from London papers.",
      role='report', words=50, dateline=True,
      core=[r'Since\s+the\s+news\s+of\s+the\s+unfortunate\s+capture\s+of\s+our\s+Eustati\w+\s+fleet'],
      first="London, 17 May 1781: reports after the capture of the convoy from St. Eustatius.",
      what="the London paragraph of 17 May on the Eustatius convoy",
      printings=[k('PP', '08-14', 3), (k('PP', '08-16', 4), AGAIN), k('NHG', '08-20', 2), k('NJG', '08-22', 2), (k('CC', '09-04', 1), {'head': 'L\\s?O\\s?N\\s?D\\s?O\\s?N\\.\\s*May\\s+17\\.\\s*'})]),
 dict(id='albany-letter-on-a-scout-from-fort-plain-september-1781', kind='document_group',
      label="Albany, 8 September 1781: a letter that of forty men Colonel Willett sent on a scout from Fort Plain, twelve returned",
      definition="Printings of an extract of a letter from a gentleman in Albany dated 8 September 1781: 'We have just received the disagreeable news, that out of forty men colonel Willet sent out on a scout from fort Plain (his present station) only twelve returned; the rest either being killed or taken, by a superior force of the enemy'. A letter-writer's account.",
      role='report', words=50, dateline=True, stop=r'Extract\s+of\s+another\s+letter',
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+a\s+gentleman\s+(?:in|at)\s+Albany,?\s+dated\s+Sept\w*\.?\s+8', r'We\s+have\s+just\s+received\s+the\s+disagreeable\s+news,?\s+that\s+out\s+of\s+(?:forty|40)\s+men'],
      first="Albany, 8 September 1781: a letter on a scout from Fort Plain.",
      what="the Albany letter of 8 September",
      printings=[k('PP', '09-18', 2), k('CC', '09-18', 2), k('NJG', '09-19', 2), k('NYG', '09-24', 2), k('NHG', '09-29', 4), k('RGC', '10-24', 2)]),
 dict(id='militia-officer-letter-from-new-london-7-september-1781', kind='document_group',
      label="New London, 7 September 1781: a militia officer's letter on the enemy's landing and attack on New London",
      definition="Printings of an extract of a letter from an officer commanding militia, dated 'New-London, Friday, 9 o'clock September 7, 1781': 'Yesterday morning at 10 o'clock, I received advice that the enemy were landing at New-London Harbour's mouth---I immediately ordered the regiment under my command to march to New-London for its defence'. The officer's own account, as a Hartford paper printed it.",
      role='report', words=50, dateline=True,
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+an\s+Officer\s+commanding\s+Militia,?\s+dated\s+New[- ]?London'],
      first="New London, 7 September 1781: a militia officer's letter on the attack on New London.",
      what="the militia officer's letter from New London",
      printings=[k('CC', '09-11', 3), k('NHG', '09-15', 2), k('PP', '09-18', 2), k('NJG', '09-19', 2)]),
 dict(id='amsterdam-letter-on-mr-adams-memorial-may-1781', kind='document_group',
      label="Amsterdam, 10 May 1781: a letter that Mr. Adams has presented a memorial to the States General",
      definition="Printings of an extract of a letter from a gentleman at Amsterdam dated 10 May 1781: 'His Excellency Mr. Adams, who has been well received at the Hague, presented last week a Memorial to their High Mightinesses, which will bring on the great question of your Independence'. A letter-writer's account.",
      role='report', words=45, dateline=True, stop=r'Extract\s+of\s+a\s+letter\s+from\s+Capt',
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+a\s+gentleman\s+of\s+character,?\s+at\s+Amsterdam', r'His\s+Excellency\s+Mr\.?\s+Adams,?\s+who\s+has\s+been\s+well\s+received\s+at\s+the\s+Hague'],
      first="Amsterdam, 10 May 1781: a letter on Mr. Adams's memorial to the States General.",
      what="the Amsterdam letter on Mr. Adams's memorial",
      printings=[k('NHG', '09-15', 3), k('CC', '09-18', 3), k('NJG', '09-26', 2), k('PP', '09-27', 3)]),
 dict(id='new-york-account-of-the-engagement-off-the-chesapeake-5-september-1781', kind='document_group',
      label="New York, 24 September 1781: an account of the engagement of 5 September off the Chesapeake between the British and French fleets",
      definition="Printings of a New York paragraph of 24 September 1781: 'The following is said to be a pretty accurate Account of the Engagement off the Chesapeake the 5th inst. between the British and French Fleets: The first certain notice our Admiral received of the enemy's fleet being actually upon the coast'. A New York paper's account, from the British side; the Connecticut Courant and the New-Hampshire Gazette print it under an introduction of their own, from 'The first certain notice'.",
      role='report', words=50, dateline=True,
      core=[r'(?:The\s+)?following\s+is\s+said\s+to\s+be\s+a\s+pretty\s+accurate\s+Account\s+of\s+the\s+Engagement\s+off\s+the\s+Chesapeake', r'T\s?HE\s+first\s+certain\s+notice\s+our\s+Admiral\s+received'],
      first="New York, 24 September 1781: an account of the engagement of 5 September off the Chesapeake.",
      what="the New York account of the engagement of 5 September",
      printings=[k('NYG', '09-24', 2), k('PP', '10-02', 2), k('CC', '10-02', 2), k('NHG', '10-06', 4), k('RGC', '10-06', 3)]),
 dict(id='greene-proclamation-after-the-execution-of-colonel-hayne-1781', kind='document_group',
      label="General Greene's proclamation after the execution of Colonel Isaac Hayne, 1781",
      definition="Printings of General Greene's proclamation: 'By Nathaniel Greene, Esquire, Major-General, commanding the American army in the southern department. A Proclamation. Whereas on the fourth day of the present month, colonel Isaac Hayne, commanding a regiment of militia in the service of the United States, was captured by a party of British troops'. General Greene's own words.",
      role='published_document', words=50, dateline=False,
      core=[r'By\s+NATHANIEL\s+GREENE,?\s+Esq', r'A\s+PROCLAMATION\.?\s+WHEREAS\s+on\s+the\s+fourth\s+day\s+of\s+the\s+present\s+month'],
      first="General Greene's proclamation after the execution of Colonel Isaac Hayne.",
      what="General Greene's proclamation on Colonel Hayne",
      printings=[k('PP', '09-27', 3), k('NYG', '10-08', 2), k('NJG', '10-10', 1), k('CC', '10-16', 2), k('NHG', '11-03', 4)]),
 dict(id='de-grasse-to-de-la-luzerne-13-september-1781', kind='document_group',
      label="The Count de Grasse to the Chevalier de la Luzerne, Cape Henry, 13 September 1781",
      definition="Printings of an extract of a letter from the Count de Grasse to the Chevalier de la Luzerne, minister plenipotentiary of France, dated Cape Henry, 13 September 1781: 'Nothing gave me greater pleasure than the approach of the armies under general Washington and count de Rochambeau'. The admiral's own account, as a Philadelphia paper printed it.",
      role='published_document', words=50, dateline=True,
      core=[r'(?:Extract\s+of\s+a\s+)?letter\s+from\s+(?:the\s+)?count\s+de\s+Gra[sf]+e,?\s+to\s+the\s+hon', r'Nothing\s+gave\s+me\s+greater\s+pleasure\s+than\s+the\s+approach\s+of\s+the\s+armies'],
      first="The Count de Grasse to the Chevalier de la Luzerne, Cape Henry, 13 September 1781.",
      what="the Count de Grasse's letter to the Chevalier de la Luzerne",
      printings=[k('PP', '09-29', 3), (k('NJG', '10-03', 3), {'head': 'SEPTEMBER\\s+29\\.\\s*'}), k('NYG', '10-08', 2), k('CC', '10-16', 2), k('NHG', '10-20', 3), k('RGC', '10-20', 3)]),
 dict(id='parker-letter-on-the-engagement-on-the-dogger-bank-august-1781', kind='document_group',
      label="London Gazette Extraordinary, 9 August 1781: Vice-Admiral Parker's letter on the engagement with the Dutch squadron on the Dogger Bank",
      definition="Printings of the London Gazette Extraordinary of 9 August 1781: 'Lieutenant Rivett, of his Majesty's cutter the Surprize, arrived here this afternoon, with a letter from Vice Admiral Parker to Mr. Stephens, of which the following is a copy. Sir, Fortitude, at Sea, August 6. Yesterday morning we fell in with the Dutch squadron, with a large convoy, on the Dogger Bank'. The British admiral's own account.",
      role='published_document', words=50, dateline=False,
      head=LG + r'Admiralty[- ]?Office,?\s+Aug\w*\.?\s+9,?\s*1781\.?\s*',
      core=[r'Lieutenant\s+Rivett,?\s+of\s+his\s+Majesty\W?s\s+cutter', r'Yesterday\s+morning\s+we\s+fell\s+in\s+with\s+the\s+Dutch\s+squadron'],
      first="London Gazette Extraordinary, 9 August 1781: Vice-Admiral Parker's letter on the Dogger Bank.",
      what="Vice-Admiral Parker's letter on the Dogger Bank",
      printings=[k('NYG', '10-15', 2), k('PP', '10-20', 2), k('NHG', '10-20', 2), (k('RGC', '10-24', 2), {'head': 'ADMIRALTY[- ]?OFFICE,?\\s+AUG\\w*\\.?\\s+9,?\\s*1781\\.?\\s*'}), k('CC', '11-06', 1), k('NJG', '11-07', 2)]),
 dict(id='greene-to-congress-martins-tavern-11-september-1781', kind='document_group',
      label="General Greene to the President of Congress, Martin's Tavern, near Ferguson's Swamp, 11 September 1781",
      definition="Printings of General Greene's letter to the President of Congress of 11 September 1781: 'In my dispatch of the 25th of August I informed your Excellency, that we were on our march for Friday's Ferry, to form a junction with the State troops and a body of militia collecting at that place'; it reports the action of the 8th at Eutaw. General Greene's own account.",
      role='published_document', words=50, dateline=False,
      core=[r'Head\s*[- ]?Quarters,?\s*Martin\W?s\s+Tavern', r'IN\s+my\s+dispatch\s+of\s+the\s+25th\s+of\s+August'],
      first="General Greene to the President of Congress, Martin's Tavern, 11 September 1781.",
      what="General Greene's letter of 11 September 1781",
      printings=[k('PP', '10-18', 3), k('NYG', '10-22', 2), k('NJG', '10-24', 2), k('CC', '10-30', 2), k('NHG', '11-03', 1), k('RGC', '11-21', 2)]),
 dict(id='the-surrender-at-york-october-december-1781', kind='context_group',
      label="The surrender of the British army at York, Virginia, as the papers printed it from October to December 1781",
      children=['washington-to-congress-near-york-19-october-1781', 'cornwallis-to-clinton-york-town-20-october-1781'],
      definition="General Washington's letter to the President of Congress of 19 October 1781 on the surrender of the British army under Lord Cornwallis, with the correspondence and the articles of capitulation, and Lord Cornwallis's own letter to Sir Henry Clinton of 20 October, as the papers printed them."),
 dict(id='washington-to-congress-near-york-19-october-1781', parent='the-surrender-at-york-october-december-1781', kind='document_group',
      label="General Washington to the President of Congress, near York, 19 October 1781, with the correspondence and the articles of capitulation",
      definition="Printings of General Washington's letter of 19 October 1781: 'Head quarters, near York, 19th October, 1781. Sir, I have the honour to inform Congress, that a reduction of the British army under the command of lord Cornwallis is most happily effected', printed with Lord Cornwallis's and General Washington's letters of 17 and 18 October and the articles of capitulation. General Washington's own account; one publication, counted by its opening (X-1810-01).",
      role='published_document', words=50, dateline=False,
      core=[r'Head\s*[- ]?quarters,?\s*near\s+York,?\s*19th\s+October', r'I\s+HAVE\s+the\s+hono\w*\s+to\s+inform\s+Congress,?\s+that\s+a\s+reduction'],
      first="General Washington to the President of Congress, near York, 19 October 1781, on the surrender of Lord Cornwallis's army.",
      what="General Washington's letter of 19 October 1781 with the articles of capitulation",
      printings=[k('PP', '10-25', 3), (k('PP', '10-27', 2), AGAIN), k('NJG', '10-31', 1), k('NYG', '11-05', 1), k('CC', '11-13', 1), k('NHG', '11-17', 2), k('RGC', '11-28', 2)]),
 dict(id='cornwallis-to-clinton-york-town-20-october-1781', parent='the-surrender-at-york-october-december-1781', kind='document_group',
      label="Lord Cornwallis to Sir Henry Clinton, York Town, Virginia, 20 October 1781",
      definition="Printings of Lord Cornwallis's letter to the Commander in Chief: 'York Town, in Virginia, October 20th, 1781. Sir, I have the mortification to inform your Excellency, that I have been forced to give up the posts of York and Gloucester, and to surrender the troops under my command, by capitulation'. Lord Cornwallis's own account.",
      role='published_document', words=50, dateline=False,
      core=[r'(?:Copy\s+of\s+a\s+)?Letter\s+from\s+Lieutenant[- ]General\s+Earl\s+Cornwallis', r'York\s*[- ]?Town,?\s+in\s+Virginia,?\s+Oct\w*\.?\s+20', r'I\s+HAVE\s+the\s+mortification\s+to\s+inform\s+your\s+Excellency'],
      first="Lord Cornwallis to Sir Henry Clinton, York Town, 20 October 1781.",
      what="Lord Cornwallis's letter to Sir Henry Clinton",
      printings=[k('NYG', '11-26', 2), k('PP', '12-06', 2), k('CC', '12-11', 2), k('NJG', '12-12', 1), k('RGC', '12-19', 1)]),
 dict(id='fishkill-report-of-an-enemy-party-under-major-ross-november-1781', kind='document_group',
      label="Fishkill, 1 November 1781: a report that a party of the enemy under Major Ross came down the Oneida Lake",
      definition="Printings of a Fishkill paragraph of 1 November 1781: 'We have just heard from Albany, that a party of the enemy, upward of 500 strong, commanded by a Major Ross, came down the Oneida Lake, and committed depredations as usual; they burnt twenty dwelling and several out houses'. A Fishkill paper's report, from Albany news.",
      role='report', words=50, dateline=True,
      core=[r'We\s+have\s+just\s+heard\s+from\s+Albany,?\s+that\s+a\s+party\s+of\s+the\s+enemy'],
      first="Fishkill, 1 November 1781: a report of an enemy party under Major Ross.",
      what="the Fishkill report of 1 November",
      printings=[k('CC', '11-06', 2), (k('NJG', '11-07', 2), {'head': 'November\\s+1\\.\\s*'}), k('PP', '11-08', 3), k('NHG', '11-10', 1), k('NYG', '11-19', 2)]),
]


MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797 and 1800): "BOSTON, Nov. 30th, 1802."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False, head=None):
    for core in cores:
        m = re.search(core, text, re.I | re.S)
        if m:
            start = m.start()
            if head:   # a heading that ends directly before the core: the excerpt starts with it
                window = text[max(0, start-260):start]
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
            problems.append((s['id'], key, 'page not in the 1781 pages'))
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
        r['id'] = f'S81-{n:03}'
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
               'admission_rule': 'Reviewed 1781 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1781/'
    return {
        'ledger_id': 'ledger:stories-1781', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1781', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1781, and of 1780 where they reach the 1781 pages (long-running ones '
                   'included), counted by machine over all 1,623 pages of 1781 in both transcriptions and joined into documents; the admitted '
                   'and chosen items counted again by their own opening, and scan checks of each admitted passage, by the thin-year rule '
                   "(Y-THIN, as amended with the owner's choice B1): eligible when printed by more than half of the papers that survive for "
                   "the item's weeks and by at least 4; eligible items printed by every paper that survives for their weeks admitted; the "
                   'others chosen to cover the months and the kinds of news'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1780.json': 'retrieval_candidates',
                             d+'counts_1781.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1781.py': 'ledger_code', 'work/archive_data/ledgers/stories_1781_review.json': 'scan_review',
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
