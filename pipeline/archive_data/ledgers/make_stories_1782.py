"""Write ledgers/stories_1782.json: reviewed stories of 1782, round one.

1782 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN, as amended on 23 November 2026, the owner's
choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the newspapers that
survive for its weeks (those with a surviving issue between its first and last printing, and at least in the three weeks
from its first printing), and by at least 4; items printed by every newspaper that survives for their weeks are admitted;
the other eligible items are chosen to cover the months and the kinds of news, about as many stories as a standard year
(about 20 to 35, a target, not a quota), one affair's items treated as in X-1800-01; digests are not admitted. The
automatic families first printed in 1782 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1781 over the 1782 pages
(items_from_1781.json); every item in 3 or more papers was counted again by the first 40 words of its opening against every
page of the year (papers the comparison missed were looked for again, and read), and a sweep of word-for-word passages
shared by 4 or more papers (as for 1803, X-1803-09) found items the families miss. Every admitted and chosen item was
counted by its own opening with phrase searches over all 1,509 pages of 1782 in both transcriptions
(work/story_phrase_search.py's patterns). See outputs/story_discovery_1782/README.md.

The 1782 pages are those whose issue the data release dates to 1782 (work/year_search_pages.py 1782 ... --printed-dates).
1782 has 8 catalogue series, which are 8 papers: no paper is under two numbers.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. Where the item is a letter, a resolution or a declaration printed inside different reports, the
excerpt begins with it (as 1801 and 1803 did). Scan findings, crops and hand-drawn boxes are merged from
stories_1782_review.json after the scan check. A printing on a page whose RevX transcription is filed under another scan
page (derived/revx_page_map.parquet) takes its excerpt from the CA transcription of its scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied; other years are reviewed at the same time, and the main
session renumbers at release:
    python work/archive_data/ledgers/make_stories_1782.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1782/search_pages.json). The excerpts are cut from
the 1782 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1782'
D = PROJECT/'outputs/story_discovery_1782'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1782_review.json'
OUT = HERE/'stories_1782.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-23'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83021127': 'The Pennsylvania Packet', 'sn84023855': 'The Connecticut Courant', 'sn83025471': 'The New-Jersey Gazette',
         'sn83025789': 'The Royal Gazette', 'sn83025585': 'The New-Hampshire Gazette', 'sn84026485': 'The New-Jersey Journal',
         'sn83025791': 'The Royal South-Carolina Gazette', 'sn83030493': 'The New-York Gazette'}
ONE = {'PP': 'sn83021127', 'CC': 'sn84023855', 'NJG': 'sn83025471', 'RG': 'sn83025789', 'NHG': 'sn83025585', 'NJJ': 'sn84026485',
       'RSCG': 'sn83025791', 'NYG': 'sn83030493'}
# Scan pages that hold another issue's sheet a second time, found by the scan check. A printing listed on such a page keeps
# its number (so the ids of the scan check stay as they were) but is not an observation: it is not a printing of its own.
SECOND_SCANS = {}
# Printings found by the scan check not to be the item: they keep their number but are not observations.
NOT_PRINTINGS = {
    ('sn84023855|1782-10-29|1|3', 'congress-resolutions-of-4-october-1782-on-peace'):
        ("A state assembly's resolutions headed 'October, A. D. 1782', which repeat Congress's preamble ('Whereas, by the Articles "
         "of Confederation ...') and resolve 'by this Assembly'; not Congress's resolutions (C-07)."),
}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1782), page and edition."""
    return f'{ONE[paper]}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()
CONGRESS = r'I\s?N\s+C\s?O\s?N\s?G\s?R\s?E\s?S\s?S'

# Story groups. A parent ('context_group') lists its children and has no printings. 'printings' lists each printing's page;
# a tuple adds overrides for that printing: core (regexes for the item's first words), role, field, note, words, dateline
# (include a dateline directly before), back (start at the beginning of the sentence that holds the core), stop (a regex:
# the excerpt ends before it).
STORIES = [
 # ---- chosen: January to September ----
 dict(id='head-quarters-orders-of-10-january-1782-on-leave-of-absence', kind='document_group',
      label="Head Quarters, Philadelphia, 10 January 1782: orders on the officers and men 'indulged with leave of absence from their corps' for the winter",
      definition="Printings of the army's orders dated 'Head Quarters, Philadelphia, Thursday, January 10, 1782. ORDERS': 'As it is expected, that in the course of the present winter, many of the officers and men belonging to the army of the United States, will be indulged with leave of absence from their corps for a limited time: and as it is absolutely necessary the strictest punctuality should be observed, in returning at the expiration of the time for which leave is given...'; 'The general, however, cannot but hope, by taking the precaution of causing this public notice of his intention to be given to the army, the disagreeable consequences will be...' The Pennsylvania Packet printed them in six issues. The commander's own orders.",
      role='published_document', words=55, dateline=False,
      core=[r'Head\W*-?\W*Quarters,?\W+Philadelphia,?\W+(?:Thursday,?\W+)?Jan(?:uary|\.)?\W+10', r'ORDERS\.?\W+A\W*S\W+it\W+is\W+expected', r'officers\W+and\W+men,?\W+belonging\W+to\W+the\W+army\W+of\W+the\W+United\W+States,?\W+will\W+be\W+indulged'],
      first="Philadelphia, January 1782: the army's orders on leave of absence for the winter.",
      what="the orders of 10 January 1782 on leave of absence",
      printings=[k('PP', '01-12', 3), k('PP', '01-15', 1), k('PP', '01-17', 1), k('PP', '01-19', 1), k('PP', '01-22', 1), k('NJG', '01-23', 3),
                 k('PP', '01-24', 1), k('CC', '02-05', 2), k('NHG', '02-16', 2), k('RG', '02-16', 1)]),
 dict(id='king-speech-opening-parliament-27-november-1781', kind='document_group',
      label="The King's speech at the opening of Parliament, 27 November 1781: 'When I last met you in Parliament, I acquainted you with the arduous situation of public affairs'",
      definition="Printings of George III's speech to both Houses of Parliament on 27 November 1781, at the opening of the session, as the papers took it from London papers in February 1782: 'My Lords and Gentlemen, When I last met you in Parliament, I acquainted you with the arduous situation of public affairs at that time, and I represented to you the objects which I had in view, and the resolution with which I was determined to persevere in the defence of...' The Pennsylvania Packet printed it twice. The King's own words. The addresses of the two Houses in answer and the King's answer to the Lords are listed as not chosen (the same affair and weeks).",
      role='published_document', words=55, dateline=False,
      core=[r'My\W+Lords\W+and\W+Gentlemen\W+W\W*HEN\W+I\W+last\W+met\W+you', r'WHEN\W+I\W+last\W+met\W+you\W+in\W+Parliament'],
      first="London, 27 November 1781: the King's speech at the opening of Parliament.",
      what="the King's speech of 27 November 1781",
      printings=[k('PP', '02-16', 5), k('PP', '02-19', 2), k('NJG', '02-20', 2), k('NHG', '02-23', 2), k('CC', '02-26', 1), k('RG', '02-27', 1)]),
 dict(id='cornwallis-letter-to-clinton-of-13-october-1781', kind='document_group',
      label="Earl Cornwallis to Sir Henry Clinton, York-Town, Virginia, 13 October 1781: 'Last evening the enemy carried my two advanced redoubts on the left by storm'",
      definition="Printings of Lord Cornwallis's letter to the British commander in chief, as the London Gazette published it ('White-Hall, Nov. 27. Copy of a letter from Earl Cornwallis, to his Excellency Sir Henry Clinton, dated York-Town, Virginia, October 13, 1781'): 'Last evening the enemy carried my two advanced redoubts on the left by storm, and during the night have included them in their second parallel, which they are at present busy in perfecting...' The Pennsylvania Packet prints it twice and dates it 'Octo. 15', as the New-Jersey Gazette does. A British commander's own letter, published by his government. Sir Henry Clinton's letter to Lord George Germain, published with it, is listed as not chosen.",
      role='published_document', words=55, dateline=False,
      core=[r'letter\W+from\W+(?:the\W+)?(?:Earl|Lord)\W+Cornwallis,?\W+to\W+(?:his\W+Excellency\W+)?Sir\W+H', r'LAST\W+evening\W+the\W+enemy\W+carried\W+my\W+two\W+advanced\W+redoubts'],
      back=True,
      first="York-Town, Virginia, October 1781: Lord Cornwallis's letter to Sir Henry Clinton, published in London.",
      what="Lord Cornwallis's letter of 13 October 1781 to Sir Henry Clinton",
      printings=[k('PP', '02-16', 5), k('PP', '02-19', 2), k('CC', '02-26', 3), k('RG', '02-27', 1), k('NHG', '03-02', 2), k('NJG', '03-06', 2)]),
 dict(id='letter-from-camden-south-carolina-february-1782', kind='message_group',
      label="A letter from Camden, South Carolina, February 1782: 'general Greene's army still remain quiet'",
      definition="Printings of an extract of a letter 'from Camden, South Carolina, to a gentleman in this town' (Philadelphia), dated 5 February 1782 (on the Pennsylvania Packet's scan the day is faded, and its transcription reads 25): 'I imagine by this time your expectations are great with respect to news in our quarter. I have only to inform you that general Greene's army still remain quiet at... (thirty miles from Charlestown)...' A private correspondent's account, at second hand.",
      role='report', words=55, dateline=True,
      core=[r'letter\W+from\W+Camden,?\W+South\W*-?\W*Carolina'],
      back=True,
      first="Camden, South Carolina, February 1782: a letter on General Greene's army near Charlestown.",
      what="the letter from Camden, South Carolina",
      printings=[k('PP', '03-14', 3), k('NJG', '03-20', 3), k('NJJ', '03-20', 3), k('CC', '03-26', 2), k('NHG', '03-30', 2)]),
 dict(id='vermont-relinquishes-its-unions-february-1782', kind='message_group',
      label="March 1782: 'the inhabitants of the territories of the State of Vermont did, on the 21st of Feb. last, relinquish all claims to the unions which they had formed'",
      definition="Printings of a paragraph first printed by the New-Hampshire Gazette: 'We learn from good authority, that the inhabitants of the territories of the State of Vermont did, on the 21st of Feb. last, relinquish all claims to the unions which they had formed on the eastern side of Connecticut river; as also the western union, which contained part of the State of New-York; the Representatives who composed said union, have returned to...' A report from good authority, as the papers say.",
      role='report', words=55, dateline=True,
      core=[r'We\W+learn\W+from\W+good\W+authority,?\W+that\W+the\W+inhabitants\W+of\W+the\W+territories\W+of\W+the\W+State\W+of\W+Vermont'],
      first="March 1782: a report that Vermont has given up its unions east of the Connecticut River and in New York.",
      what="the report on Vermont's unions",
      printings=[k('NHG', '03-09', 3), k('CC', '03-12', 3), k('NJG', '03-20', 3), k('NJJ', '03-20', 3), k('PP', '03-26', 2)]),
 dict(id='martinique-merchant-letter-on-st-kitts-march-1782', kind='message_group',
      label="A merchant's letter from Fort St. Pierre, Martinique, March 1782: 'You have no doubt been informed of the reduction of the island of St. Kitts'",
      definition="Printings of an extract of a letter of a merchant at Fort St. Pierre, Martinique, as Boston and Richmond papers published it in March 1782: 'You have no doubt been informed of the reduction of the island of St. Kitts, which capitulated on the 12th ult. at ten o'clock, P. M. Nevis surrendered immediately, and Monserrat had the same fate...' The papers date the letter 1 March (Boston) or 3 March (the Royal Gazette, from Richmond) and call the island St. Kitts or St. Christopher. A merchant's account; the articles of capitulation, printed in the same weeks, are listed as not chosen.",
      role='report', words=55, dateline=True,
      core=[r'(?:Extract|Extra)\W+of\W+a\W+letter\W+(?:of|from)\W+mon[sf]ieur\W+\w+,?\W+merchant', r'You\W+have\W+no\W+doubt\W+been\W+informed\W+of\W+the\W+reduction'],
      first="Martinique, March 1782: a merchant's letter on the capitulation of St. Kitts to the French.",
      what="the Martinique letter on the capitulation of St. Kitts",
      printings=[k('NHG', '03-30', 2), k('PP', '04-09', 3), k('NJJ', '04-10', 2), k('NJG', '04-24', 1), (k('RG', '04-24', 2), {'core': [r'RICHMOND,?\W+in\W+VIRGINIA,?\W+March\W+23\W+Extra'], 'dateline': False, 'words': 60})]),
 dict(id='martinico-gazette-account-of-the-sea-engagement-april-1782', kind='message_group',
      label="Boston, 16 May 1782: 'The following account of a sea engagement between the French fleet under the command of ... the Count de Grasse, and the British fleet, under ... Sir George B. Rodney, is translated from the Martinico Gazette'",
      definition="Printings of a translation from the Martinico Gazette of 18 April 1782, brought to Newbury by the brig Swan, of an account of a sea engagement in the West Indies in April 1782: 'The following account of a sea engagement between the French fleet under the command of his Excellency the Count de Grasse, and the British fleet, under the orders of Sir George B. Rodney, is translated from the Martinico Gazette, of April 18...' The French side's published account, as Boston papers translated it; the Royal Gazette of Charleston prints it too. Accounts from the British side in the same weeks are listed as not chosen.",
      role='report', words=55, dateline=True,
      core=[r'following\W+account\W+of\W+a\W+sea\W+engagement\W+between\W+the\W+French', r'translated\W+from\W+the\W+Martinico\W+Gazette'],
      back=True,
      first="Boston, May 1782: the Martinico Gazette's account of the battle between the Count de Grasse and Sir George Rodney.",
      what="the Martinico Gazette's account of the sea engagement",
      printings=[k('NHG', '05-18', 3), k('CC', '05-21', 2), k('PP', '05-28', 1), k('NJG', '05-29', 2), k('RG', '06-15', 2)]),
 dict(id='handbill-from-amsterdam-holland-declares-america-independent-march-1782', kind='document_group',
      label="Translation of a handbill printed in Amsterdam: 'A Declaration of Independence from the United States of Holland to the United States of America', 'done at the Hague' 28 March 1782",
      definition="Printings of a text the papers call the 'Translation of the Hand-Bill, printed in Amsterdam' ('Extra tidings from the United States of Holland, to the United States of North-America, that is to say, the Seven Provinces of Holland have declared America free and independent States'): 'We the United States of Holland, have these twenty-five years past seen the iniquity of the British administration to the American colonies, and finding ourselves in gratitude to the calls of religion, freedom and virtue...' A handbill, as the papers describe it, in their translation.",
      role='published_document', words=55, dateline=False,
      core=[r'Translation\W+of\W+the\W+Hand\W*-?\W*Bill', r'Holland\W+have\W+declared\W+America\W+FREE', r'W\W*E,?\W+the\W+United\W+States\W+of\W+HOLLAND,?\W+have\W+these'],
      back=True,
      first="Amsterdam, March 1782: a handbill declaring the Dutch provinces' recognition of American independence.",
      what="the Amsterdam handbill on Holland and American independence",
      printings=[k('NHG', '05-25', 2), k('CC', '05-28', 3), k('PP', '06-01', 3), k('NJG', '06-05', 2), k('RG', '06-15', 2)]),
 dict(id='charlestown-report-savannah-evacuated-july-1782', kind='message_group',
      label="Charlestown, July 1782: 'The town of Savannah was evacuated by the British troops, on the 11th of this month'",
      definition="Printings of a Charlestown paragraph first printed by the Royal Gazette of Charleston (held by the British) on 24 July 1782, and dated 'Charlestown, July 30' by the other papers in September: 'The town of Savannah was evacuated by the British troops, on the 11th of this month; the public stores and the effects of the inhabitants who have come away, being previously removed down to the island of Tybee. On the 20th of the same month, a fleet sailed from Tybee for Jamaica, with about 1800 negroes, and other property...' A report printed in the town the British held.",
      role='report', words=55, dateline=True,
      core=[r'T\W*he\W+town\W+of\W+Savanna?h?\W+was\W+evacuated\W+by\W+the\W+British\W+troops'],
      first="Charlestown, July 1782: the Royal Gazette's report of the British evacuation of Savannah.",
      what="the Charlestown report of the evacuation of Savannah",
      printings=[k('RG', '07-24', 3), k('PP', '09-03', 3), k('NJG', '09-04', 2), k('CC', '09-24', 4), (k('NHG', '09-28', 2), {'core': [r'July\W+30\W+The\W+town\W+of\W+Savannah'], 'dateline': False, 'words': 57})]),
 dict(id='carleton-and-digby-letter-and-congress-august-1782', kind='context_group',
      label="Sir Guy Carleton and Admiral Digby to General Washington, 2 August 1782, and Congress's resolutions of 12 August on it",
      definition="Two texts printed in August 1782: the letter of the British commanders at New York to General Washington, published there 'at the request of the inhabitants', that negotiations for a general peace had begun at Paris; and the resolutions of Congress that called it 'mere matter of information'.",
      children=['carleton-and-digby-letter-to-washington-2-august-1782', 'congress-resolutions-of-12-august-1782-on-the-letter']),
 dict(id='carleton-and-digby-letter-to-washington-2-august-1782', parent='carleton-and-digby-letter-and-congress-august-1782', kind='document_group',
      label="Sir Guy Carleton and Rear Admiral Digby to General Washington, New-York, 2 August 1782: 'We are acquainted, Sir, by authority, that negotiations for a general peace have already commenced at Paris'",
      definition="Printings of the letter of the British commander in chief and the admiral at New York to General Washington, as the Royal American Gazette of New York published it 'at the request of the inhabitants of New York': 'Sir, The pacific disposition of the parliament and people of England towards the thirteen provinces, has already been communicated to you... We are acquainted, Sir, by authority, that negotiations for a general peace have already commenced at Paris...' The Pennsylvania Packet printed it twice, the second time with the resolutions of Congress. The British commanders' own letter.",
      role='published_document', words=55, dateline=False,
      core=[r'letter\W+from\W+sir\W+GUY\W+CARLE?TON,?\W+and\W+(?:rear\W*-?\W*)?admiral\W+DIGBY', r'pacific\W+disposition\W+of\W+the\W+parliament\W+and\W+people\W+of\W+England', r'We\W+are\W+acquainted,?\W+Sir,?\W+by\W+authority'],
      back=True,
      first="New-York, August 1782: the British commanders' letter to General Washington that peace negotiations had begun at Paris.",
      what="Sir Guy Carleton and Admiral Digby's letter of 2 August 1782",
      printings=[k('PP', '08-10', 3), k('CC', '08-13', 3), k('NJG', '08-14', 2), k('PP', '08-15', 3), k('NHG', '08-17', 2)]),
 dict(id='congress-resolutions-of-12-august-1782-on-the-letter', parent='carleton-and-digby-letter-and-congress-august-1782', kind='document_group',
      label="Congress, 12 August 1782: 'Resolved, That Congress consider the above letter as mere matter of information'",
      definition="Printings of the resolutions of Congress of 12 August 1782: 'Whereas from the late publications, the people throughout the United States may be induced to believe that Congress have received authentic communications upon the subject of an approaching peace. Resolved, That the letter of August 2d, 1782, from Sir Guy Carleton and Admiral Digby to the Commander in Chief be made public. Resolved, That Congress consider the above letter as mere matter of information, inexplicit as to the nature and extent of the independence directed to be proposed by the British Plenipotentiary...' Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      core=[r'By\W+the\W+UNITED\W+STATES\W+in\W+CONGRESS\W+assembled[,.]?\W+August\W+12', r'CONGRESS\W+assembled,?\W+August\W+12,?\W+1782', r'from\W+the\W+late\W+publications,?\W+the\W+people\W+throughout', r'Congress\W+consider\W+the\W+above\W+letter\W+as\W+mere\W+matter'],
      back=True,
      first="Congress, August 1782: resolutions on the British commanders' letter.",
      what="Congress's resolutions of 12 August 1782 on the letter",
      printings=[k('PP', '08-15', 3), k('NJG', '08-21', 3), k('CC', '08-27', 2), k('NHG', '08-31', 2)]),
 dict(id='king-speech-closing-the-session-11-july-1782', kind='document_group',
      label="The King's speech to both Houses of Parliament, 11 July 1782: 'The unwearied assiduity with which you have persevered in the discharge of your duty'",
      definition="Printings of George III's speech at the close of the session of Parliament on 11 July 1782, as the papers took it from London papers in September: 'My Lords and Gentlemen, The unwearied assiduity with which you have persevered in the discharge of your duty in parliament, during so long a session, bears the most honourable testimony of your zeal and industry in the service of the public...' The King's own words.",
      role='published_document', words=55, dateline=False,
      core=[r'My\W+Lords\W+and\W+Gentlemen,?\W+T\W*HE\W+unwearied', r'T\W*HE\W+unwearied\W+assiduity\W+with\W+which\W+you\W+have\W+persevered'],
      first="London, 11 July 1782: the King's speech at the close of the session.",
      what="the King's speech of 11 July 1782",
      printings=[k('NJJ', '09-11', 3), k('PP', '09-12', 3), k('NHG', '09-14', 2), k('CC', '09-17', 1), k('NJG', '09-18', 1)]),
# ---- admitted: printed by every newspaper that survives for their weeks (Y-THIN's first part) ----
 dict(id='boston-comment-on-a-treaty-between-france-and-holland-april-1782', kind='message_group',
      label="Boston, April 1782: 'The authentic account we have lately received of the conclusion of a new treaty between France and the States of Holland, is very important'",
      definition="Printings of a Boston paragraph of April 1782 (dated 11 April in the Pennsylvania Packet): 'The authentic account we have lately received of the conclusion of a new treaty between France and the States of Holland, is very important: It destroys all idea of a separate peace between England and that Republic. The treaty with France has been for some time warmly demanded by the old republicans of Holland, and opposed with every art by the British party...' Printed by all five newspapers that survive for its weeks, the Royal Gazette of Charleston among them; admitted by the rule's first part. A Boston paper's comment on the account it had received.",
      role='report', words=55, dateline=True,
      core=[r'T\W*he\W+authentick?\W+accounts?\W+we\W+have\W+lately\W+received'],
      first="Boston, April 1782: a paper's comment on an account of a new treaty between France and Holland.",
      what="the Boston comment on the treaty between France and Holland",
      printings=[k('NHG', '04-13', 2), k('CC', '04-16', 3), k('NJG', '04-24', 2), k('PP', '04-25', 3), k('RG', '05-22', 3)]),
 dict(id='washington-letter-of-10-may-1782-with-carleton-letter', kind='document_group',
      label="General Washington to Congress, 10 May 1782: 'Just as I am closing these dispatches, a letter from Sir Guy Carleton is handed me', with Sir Guy Carleton's letter",
      definition="Printings of General Washington's letter to Congress, Head-Quarters, 10 May 1782: 'Just as I am closing these dispatches, a letter from Sir Guy Carleton is handed me, covering sundry printed papers, a copy of which, with the papers, I have now the honour to enclose to your Excellency, together with a copy of my answer to him...', with the letter of Sir Guy Carleton, the British commander at New York, that it encloses ('...upon this one point we must perfectly concur, being alike interested to preserve the name of Englishmen from reproach, and individuals from experiencing such unnecessary evils, as can have no effect upon a general decision...'). Printed by all six newspapers that survive for its weeks, the New-York Gazette and the Royal Gazette of Charleston among them; admitted by the rule's first part. The commanders' own letters.",
      role='published_document', words=55, dateline=False,
      core=[r'letter\W+from\W+(?:his\W+Excellency\W+)?(?:General\W+)?Washington,?\W+to\W+(?:the\W+President\W+of\W+)?Congress', r'J\W*UST\W+as\W+I\W+am\W+closing\W+these\W+d[ie]spatches'],
      back=True,
      first="Head-Quarters, May 1782: General Washington's letter to Congress sending Sir Guy Carleton's letter.",
      what="General Washington's letter of 10 May 1782 with Sir Guy Carleton's letter",
      printings=[k('PP', '06-01', 3), k('NYG', '06-10', 2), k('NHG', '06-15', 2), k('RG', '06-15', 2), k('CC', '06-18', 2), k('NJG', '06-19', 2)]),
 dict(id='greene-letters-of-may-1782', kind='context_group',
      label="General Greene's letters to the President of Congress of 21 and 31 May 1782, near Bacon's Bridge, South Carolina",
      definition="Two letters of the commander of the southern army, printed together in July 1782: the first on a verbal message from the British general at Charlestown proposing a cessation of hostilities, the second sending General Wayne's report of an action near Savannah.",
      children=['greene-letter-of-21-may-1782-on-a-proposed-cessation-of-hostilities', 'greene-letter-of-31-may-1782-with-wayne-letter']),
 dict(id='greene-letter-of-21-may-1782-on-a-proposed-cessation-of-hostilities', parent='greene-letters-of-may-1782', kind='document_group',
      label="General Greene to the President of Congress, near Bacon's Bridge, 21 May 1782: 'I do myself the honour to enclose to your Excellency a copy of a resolution of the British House of Commons, and the King's reply'",
      definition="Printings of an extract of General Greene's letter to the President of Congress, Head-Quarters near Bacon's Bridge, South Carolina, 21 May 1782: 'I do myself the honor to enclose to your Excellency a copy of a resolution of the British House of Commons, and the King's reply, which were sent out to me last evening by Lieutenant-General Leslie, through Major Skelly, his Aid de Camp, accompanied with a verbal message, that as those changes of measures seemed to lead directly to a peace, he would agree to a cessation of hostilities on their part, provided we would on ours...'; 'As the proposition for a cessation of hostilities did not come with the necessary forms, I gave no written answer.' A sub-story (C-01): in 4 of the 5 newspapers that survive for its weeks. The general's own letter.",
      role='published_document', words=55, dateline=False,
      core=[r'letter\W+from\W+Major\W*-?\W*General\W+GREENE\W+to\W+(?:His\W+Excellency\W+)?the\W+President\W+of\W+(?:the\W+)?CONGRESS', r'I\W+DO\W+myself\W+the\W+honou?r\W+to\W+enclose\W+to\W+your\W+Excellency'],
      back=True,
      first="South Carolina, May 1782: General Greene's letter on a proposed cessation of hostilities.",
      what="General Greene's letter of 21 May 1782",
      printings=[k('PP', '07-11', 3), k('NJG', '07-17', 2), k('CC', '07-23', 1), k('RG', '07-31', 2)]),
 dict(id='greene-letter-of-31-may-1782-with-wayne-letter', parent='greene-letters-of-may-1782', kind='document_group',
      label="General Greene to the President of Congress, near Bacon's Bridge, 31 May 1782, with General Wayne's letter of 24 May: 'On the 21st inst. I received intelligence of the enemy being out in force from Savannah'",
      definition="Printings of an extract of General Greene's letter to the President of Congress of 31 May 1782 ('I had the honor to address your Excellency on the 21st inst. on the subject of a verbal message from Lieut. Gen. Leslie, proposing a cessation of hostilities in this country. Since then I have received...'), with the letter it encloses from General Wayne, Ebenezer, 24 May 1782: 'On the 21st inst. I received intelligence of the enemy being out in force from Savannah, in consequence of which White's dragoons and Posey's infantry were put in motion...'. The letter and its enclosure are counted as one item (as X-1810-01), and the enclosure printed alone with it (as 1779's General Putnam letter, X-1779-03): four papers print the letter, three of them with General Wayne's letter; the New-Hampshire Gazette prints General Wayne's letter alone, 'extracted' from a Philadelphia paper, and later a paragraph of General Greene's letter ('Flying parties of the British cavalry are frequently making excursions into the country from Charlestown'), which is not counted again. In all five newspapers that survive for its weeks; admitted by the rule's first part. The generals' own letters. The New-Jersey Gazette dates General Greene's letter 21 May.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:Extract|Extra)\W+of\W+another\W+letter\W+from\W+General\W+Greene', r'I\W+(?:had|HAD)\W+the\W+honou?r\W+to\W+address\W+your\W+Excellency\W+on\W+the\W+21st'],
      first="South Carolina, May 1782: General Greene's letter sending General Wayne's report of an action near Savannah.",
      what="General Greene's letter of 31 May 1782 with General Wayne's letter",
      printings=[k('PP', '07-11', 3), k('NJG', '07-17', 2), k('CC', '07-23', 1),
                 (k('NHG', '07-27', 2), {'core': [r'Ebenezer,?\W+(?:24th\W+May|May\W+24)', r'On\W+the\W+21st\W+inst(?:\.|ant)?,?\W+I\W+received\W+intelligence'],
                                         'note': "General Wayne's letter, printed alone ('extracted' from a Philadelphia paper of 10 July)."}),
                 k('RG', '07-31', 2)]),
 dict(id='fishkill-report-rochambeau-at-verplanck-point-september-1782', kind='message_group',
      label="Fish-Kill, 19 September 1782: 'his Excellency the Count De Rochambeau, commander in chief of the French army, arrived with his suite at Verplank's point; he was saluted on his approach by the American army'",
      definition="Printings of a Fish-Kill paragraph of 19 September 1782: 'On last Saturday his Excellency the Count De Rochambeau, commander in chief of the French army, arrived with his suite at Verplank's point; he was saluted on his approach by the American army, drawn up for that purpose in two lines fronting each other, and extending from Head-Quarters to the ferry...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. A Fish-Kill paper's report.",
      role='report', words=55, dateline=True,
      core=[r'Count\W+De\W+Rochambeau,?\W+commander\W+in\W+chief\W+of\W+the\W+French\W+army,?\W+arrived', r'Rochambeau,?\W+Commander\W+in\W+Chief\W+of\W+the\W+French\W+army'],
      back=True,
      first="Fish-Kill, September 1782: the Count de Rochambeau saluted by the American army at Verplanck's Point.",
      what="the Fish-Kill report of the Count de Rochambeau at Verplanck's Point",
      printings=[k('PP', '09-24', 2), k('CC', '09-24', 3), k('NJG', '09-25', 3), (k('NHG', '09-28', 2), {'core': [r'F\W*I\W*S\W*H\W*-?\W*K\W*I\W*L\W*L,?\W+September\W+19\W+On\W+Saturday'], 'dateline': False, 'words': 66})]),
 dict(id='brig-brought-into-beverly-by-her-prisoners-september-1782', kind='message_group',
      label="September 1782: 'arrived at Beverly a brig of 16 guns, late in the service of his Britannic Majesty. The crew of the Hope ... being prisoners on board her ... rose upon the brig's people'",
      definition="Printings of a Massachusetts paragraph of September 1782: 'Yesterday arrived at Beverly a brig of 16 guns, late in the service of his Britannic Majesty. The crew of the Hope (a small privateer lately captured by her) being prisoners on board her, to the number of 21, rose upon the brig's people, in number 62, while laying in a small harbour on the Labrador shore; overcame them, and took the command of the vessel...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. A report at second hand.",
      role='report', words=55, dateline=True,
      core=[r'arrived\W+at\W+Beverly,?\W+a\W+brig\W+of\W+1[56]\W+guns'],
      back=True,
      first="Beverly, September 1782: a British brig brought in by the American prisoners on board her.",
      what="the report of the brig brought into Beverly",
      printings=[k('NHG', '09-28', 3), k('CC', '10-08', 3), k('PP', '10-15', 2), (k('NJG', '10-16', 2), {'core': [r'Oct\W+1\W+Yesterday'], 'dateline': False, 'words': 57})]),
 dict(id='letter-from-fort-pitt-3-september-1782', kind='message_group',
      label="A letter from Fort Pitt, 3 September 1782: 'From the middle to the last of July, the Indians have been very troublesome on the frontiers of this country—Hanna's town was burned'",
      definition="Printings of an extract of a letter from Fort Pitt dated 3 September 1782: 'From the middle to the last of July, the Indians have been very troublesome on the frontiers of this country—Hanna's town was burned, several inhabitants killed and taken, and about the same time Fort Wheeling was blockaded for several days; for two weeks the inhabitants were in such consternation that a total evacuation of the country was to be dreaded...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. A correspondent's account from Fort Pitt.",
      role='report', words=55, dateline=True,
      core=[r'letter\W+from\W+Fort\W*-?\W*Pitt,?\W+(?:dated\W+)?Sept', r'From\W+the\W+middle\W+t[oi]l?l?\W+the\W+last\W+of\W+July', r'Indians\W+have\W+been\W+very\W+troublesome\W+on\W+the\W+frontiers?'],
      back=True,
      first="Fort Pitt, September 1782: a letter on Indian attacks on the frontier in July.",
      what="the letter from Fort Pitt of 3 September 1782",
      printings=[k('PP', '10-01', 3), k('CC', '10-15', 2), k('NHG', '10-19', 2), k('NJG', '10-30', 3)]),
 dict(id='office-for-foreign-affairs-arret-on-prize-goods-september-1782', kind='document_group',
      label="Office for Foreign Affairs, 30 September 1782: 'Translation of an Arret of his most christian majesty's council of state, prescribing the formalities to be observed in the shipping of prize goods'",
      definition="Printings of a translation published by order of Congress: 'Office for Foreign Affairs, September 30, 1782. Translation of an Arret of his most christian majesty's council of state, prescribing the formalities to be observed in the shipping of prize goods out of the ports of his kingdom. Published by order of congress. Extract from the Registers of the Council of State...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. The French council's decree, in Congress's translation.",
      role='published_document', words=55, dateline=False,
      core=[r'OFFICE\W+for\W+FOREIGN\W+AFFAIRS,?;?\W+September\W+30'],
      first="Philadelphia, October 1782: Congress publishes a French decree on prize goods.",
      what="the French decree on prize goods, published by order of Congress",
      printings=[k('PP', '10-01', 3), k('NJG', '10-09', 2), k('CC', '10-15', 2), k('NHG', '10-26', 4)]),
 dict(id='congress-resolutions-of-4-october-1782-on-peace', kind='document_group',
      label="Congress, 4 October 1782: 'Resolved unanimously, That congress are sincerely desirous of an honourable and permanent peace' and will conclude neither a separate peace nor a truce",
      definition="Printings of the resolutions of Congress of 4 October 1782: 'Whereas by the articles of confederation and perpetual union, the sole and exclusive right of making peace is vested in the United States in Congress assembled; and by the treaty of alliance between His Most Christian Majesty and these United States, it is declared that neither of the contracting parties shall conclude peace or truce with Great Britain without the consent of the other... Resolved unanimously, That congress are sincerely desirous of an honourable and permanent peace: that as the only means of obtaining it, they will inviolably adhere to the treaty of alliance...' The Pennsylvania Packet printed them twice; a page of the Connecticut Courant (29 October) that repeats their preamble prints a state assembly's resolutions, not counted (C-07). Printed by all four newspapers that survive for their weeks; admitted by the rule's first part. Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      core=[r'CONGRESS\W+Assembled,?\W+October\W+4,?\W+1782', r'W\W*HEREAS,?\W+by\W+the\W+articles\W+of\W+confederation\W+and\W+perpetual\W+union,?\W+the\W+sole'],
      back=True,
      first="Congress, October 1782: resolutions that it will conclude neither a separate peace nor a truce.",
      what="Congress's resolutions of 4 October 1782",
      printings=[k('PP', '10-05', 3), k('PP', '10-08', 1), k('NJG', '10-16', 2), k('CC', '10-22', 2), k('NHG', '10-26', 2), k('CC', '10-29', 3)]),
 dict(id='greene-letters-of-28-and-29-august-1782-with-leslie-and-gist', kind='document_group',
      label="General Greene's letters of 28 and 29 August 1782, with General Leslie's letter on provisions and General Gist's report of the skirmish of 27 August",
      definition="Printings of extracts of General Greene's letters from Ashley Hill, South Carolina: of 28 August 1782 ('The inclosed copy of a letter from Lieutenant General Leslie, contains an extraordinary requisition for a supply of provision, which was refused. I cannot but consider it as an evidence of the intention of the enemy to seduce and lull the people of this country...'), with General Leslie's letter from Charlestown ('I hope these considerations will induce you to accept a proposal so evidently advantageous to the interests of your own party; and that you will in consequence, order rice and other provisions to be sent into town...'); and of 29 August ('I have the honour to transmit your excellency the report of brigadier general Gist, relative to the operations of the troops under his command... It is very unfortunate that we have to lament the loss of so valuable and distinguished an officer as lieutenant colonel Laurens, who was killed in the skirmish on the 27th instant'), with General Gist's report and a list of the killed and wounded. Printed together by all four newspapers that survive for their weeks; admitted by the rule's first part (the letters and their enclosures as one item, as X-1810-01). The generals' own letters.",
      role='published_document', words=55, dateline=True,
      core=[r'letter\W+from\W+Major\W+General\W+Greene?\W+(?:\S+\W+){0,10}?dated\W+(?:Head\W*-?\W*quarters,?\W+)?(?:South\W*-?\W*Carolina,?\W+)?Ashley', r'(?:in|en)clo[sf]ed\W+copy\W+of\W+a\W+letter\W+from\W+(?:Lieutenant|Lieut\.?)\W+General\W+Leslie'],
      back=True,
      first="South Carolina, August 1782: General Greene's letters on the British general's request for provisions and on the skirmish of 27 August.",
      what="General Greene's letters of 28 and 29 August 1782",
      printings=[k('PP', '10-05', 3), k('NJG', '10-16', 2), k('CC', '10-22', 2), k('NHG', '10-26', 3)]),
 dict(id='portsmouth-report-captain-snider-from-canada-october-1782', kind='message_group',
      label="Portsmouth, 5 October 1782: five men returned 'from their captivity in Canada' report that '4000 troops ... had marched for Lake Champlain'",
      definition="Printings of a Portsmouth (New Hampshire) paragraph of 5 October 1782: five men returned to Cohas 'from their captivity in Canada' (a captain of Esopus, in New-York State, 'and four others'): 'they left Canada about the 10th of September, and inform, that some military preparations had taken place there—that 4000 troops, consisting of Europeans, Canadians, Tories and Indians, had marched for Lake Champlain, to embark for Ticonderoga; and it was reported in Canada, their intention was for Albany...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. Returned prisoners' report, at second hand.",
      role='report', words=55, dateline=True,
      core=[r'arrived\W+at\W+Cohas'],
      back=True,
      first="Portsmouth, October 1782: prisoners returned from Canada report troops marching for Lake Champlain.",
      what="the Portsmouth report of the prisoners returned from Canada",
      printings=[k('NHG', '10-05', 3), k('CC', '10-15', 3), k('PP', '10-17', 4), k('NJG', '10-23', 3)]),
 dict(id='congress-proclamation-of-a-day-of-thanksgiving-october-1782', kind='document_group',
      label="Congress's proclamation of a day of thanksgiving, October 1782: 'It being the indispensable duty of all nations, not only to offer up their supplications to Almighty God'",
      definition="Printings of the proclamation of Congress of October 1782 appointing a day of public thanksgiving: 'It being the indispensable duty of all nations, not only to offer up their supplications to Almighty God, the giver of all good, for his gracious assistance in a time of distress, but also in a solemn and public manner to give him praise for his goodness in general, and especially for great and signal interpositions of his providence in their behalf...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. Pages that recite it inside a state's proclamation are not counted (C-07). Congress's own proclamation.",
      role='published_document', words=55, dateline=False,
      core=[r'By\W+the\W+UNITED\W+STATES\W+in\W+CONGRESS\W+[Aa]ssembled\.?\W+P\W*R\W*O\W*C\W*L\W*A\W*M', r'CONGRESS\W+[Aa]ssembled\.?\W+P\W*R\W*O\W*C\W*L\W*A\W*M\W*A\W*T\W*I\W*O\W*N', r'I\W*T\W+being\W+the\W+indispensable\W+duty\W+of\W+all\W+nations'],
      back=True,
      first="Congress, October 1782: a proclamation appointing a day of thanksgiving.",
      what="Congress's proclamation of a day of thanksgiving",
      printings=[k('PP', '10-15', 3), k('NJG', '10-23', 1), k('CC', '10-29', 2), k('NHG', '11-02', 3)]),
 dict(id='letter-from-greene-camp-of-2-september-1782', kind='message_group',
      label="A letter from a gentleman at General Greene's camp, 2 September 1782: 'Orders have been repeated for the evacuation of Charlestown'",
      definition="Printings of an extract of a letter 'from a gentleman at General Greene's camp, dated September 2, 1782': 'Orders have been repeated for the evacuation of Charlestown: they have not transports enough to convey their stores, and provide for the refugees who are to go to East Florida. We have good information they have fallen upon this method:—they will evacuate Charlestown in a few days, and leave the refugees at Beaufort on Port Royal Island...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. A correspondent's account.",
      role='report', words=55, dateline=False,
      core=[r'letter\W+from\W+a\W+gentleman\W+at\W+General\W+Greene.s\W+[Cc]amp'],
      back=True,
      first="South Carolina, September 1782: a letter from General Greene's camp on the coming evacuation of Charlestown.",
      what="the letter from General Greene's camp of 2 September 1782",
      printings=[k('PP', '10-15', 3), k('NJG', '10-23', 3), k('CC', '10-29', 2), k('NHG', '11-02', 2)]),
 dict(id='fishkill-report-lloyds-neck-evacuated-october-1782', kind='message_group',
      label="Fish-Kill, 10 October 1782: 'We learn from Long-Island, that the enemy have evacuated their post at Lloyd's-Neck'",
      definition="Printings of a Fish-Kill paragraph of 10 October 1782: 'We learn from Long-Island, that the enemy have evacuated their post at Lloyd's-Neck the 22d ult.—That the loyalists on that part of the island had the indulgence offered them of emigrating to Nova Scotia on certain terms of encouragement—That many of them chose rather to risk the forfeited mercy of their country...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. A Fish-Kill paper's report.",
      role='report', words=55, dateline=True,
      core=[r'We\W+learn\W+from\W+Long\W*-?\W*Island,?\W+that\W+the\W+enemy\W+have\W+evacuated'],
      first="Fish-Kill, October 1782: a report that the British have left their post at Lloyd's Neck.",
      what="the Fish-Kill report of Lloyd's Neck",
      printings=[k('PP', '10-15', 2), k('CC', '10-15', 2), k('NJG', '10-16', 2), k('NHG', '10-19', 2)]),
 dict(id='siege-of-gibraltar-autumn-1782', kind='context_group',
      label="Gibraltar, autumn 1782: four accounts of the siege, as the papers printed them from October to December",
      definition="Four texts on the siege of Gibraltar by France and Spain, each printed by every newspaper that survives for its weeks: a London paragraph of 10 August; Governor Elliot's letter of 12 September as a Cork paper printed it; a Boston report of the news by a brig from Cadiz; and a Hague paragraph with a letter from Paris on the attack of the floating batteries.",
      children=['gibraltar-paragraph-of-10-august-1782', 'elliot-letter-of-12-september-1782-from-a-cork-gazette', 'boston-report-of-a-brig-from-cadiz-29-november-1782', 'hague-1-october-1782-letter-from-paris-on-the-siege']),
 dict(id='gibraltar-paragraph-of-10-august-1782', parent='siege-of-gibraltar-autumn-1782', kind='message_group',
      label="10 August 1782: 'The attention of all Europe is now turned with infinite apprehension and solicitude to the fate of Gibraltar'",
      definition="Printings of a paragraph of foreign news dated 10 August 1782: 'The attention of all Europe is now turned with infinite apprehension and solicitude to the fate of Gibraltar. On this theatre the greatest exploits are shortly expected to take place. The fame acquired by the Duke de Crillon in his siege of Minorca, on the one hand, and the tried and determined bravery of General Elliot, on the other, must produce a contest...' A single paragraph from a run of foreign news (C-09), printed by all four newspapers that survive for its weeks; admitted by the rule's first part. A writer's expectation, from the European papers.",
      role='report', words=55, dateline=False,
      core=[r'Aug(?:ust|\.)?\W*10\W+T\W*he\W+attention\W+of\W+all\W+Europe', r'T\W*he\W+attention\W+of\W+all\W+Europe\W+is\W+now\W+turned'],
      first="August 1782: a European paragraph on the coming contest at Gibraltar.",
      what="the paragraph of 10 August on Gibraltar",
      printings=[k('NHG', '10-26', 1), k('CC', '10-29', 2), k('PP', '10-29', 3), k('NJG', '11-06', 2)]),
 dict(id='elliot-letter-of-12-september-1782-from-a-cork-gazette', parent='siege-of-gibraltar-autumn-1782', kind='document_group',
      label="Governor Elliot to Secretary Stevens, Gibraltar, 12 September 1782, from 'a Gazette extraordinary, printed at Cork': 'our success against the Spaniards, in their so much boasted attack with their floating batteries'",
      definition="Printings of a letter of the British governor of Gibraltar as the papers took it from 'a Gazette extraordinary, printed at Cork' ('Admiralty-Office, Sept. 19, 1782. Extract of a letter from Governor Elliot, to Secretary Stevens, dated Sept. 12, 1782'): 'I have taken an opportunity of sending this by [the master of] the Speedwell cutter, who is to sail to-morrow for England, with the subsequent account of our success against the Spaniards, in their so much boasted attack with their floating batteries... As it was always my opinion that we should be attacked by their whole force on St. Louis's day...' Printed by all five newspapers that survive for its weeks; admitted by the rule's first part. The letter as a Cork paper printed it.",
      role='published_document', words=55, dateline=False,
      core=[r'Gazette\W+extraordinary,?\W+printed\W+at\W+Cork', r'letter\W+from\W+Governor\W+Elliot,?\W+to\W+Secretary\W+Stevens', r'I\W*HAVE\W+taken\W+an\W+opportunity\W+of\W+sending\W+this\W+by\W+Mr\.?\W+Frazier'],
      back=True,
      first="Gibraltar, September 1782: Governor Elliot's letter on the attack of the floating batteries, as a Cork paper printed it.",
      what="Governor Elliot's letter of 12 September 1782 from a Cork paper",
      printings=[k('NJG', '11-27', 2), (k('NJJ', '11-27', 2), {'core': [r'Admiralty\W*Office,?\W+Sept\w*\W+10,?\W+1782\W+Extract\W+of\W+a\W+(?:L|l)etter\W+from\W+(?:Gov|gov)'], 'dateline': False, 'back': False, 'words': 73}), (k('PP', '11-29', 2), {'core': [r'Admiralty\W*Office,?\W+Sept\w*\W+19,?\W+1782\W+Extract\W+of\W+a\W+(?:L|l)etter\W+from\W+(?:Gov|gov)'], 'dateline': False, 'back': False, 'words': 52}), k('NHG', '12-07', 2), (k('CC', '12-17', 4), {'core': [r'Admiralty\W*Office,?\W+Sept\w*\W+9,?\W+1782\W+Extract\W+of\W+a\W+(?:L|l)etter\W+from\W+(?:Gov|gov)'], 'dateline': False, 'back': False, 'words': 73})]),
 dict(id='boston-report-of-a-brig-from-cadiz-29-november-1782', parent='siege-of-gibraltar-autumn-1782', kind='message_group',
      label="Boston, 29 November 1782: 'Tuesday evening arrived here a brig from Cadiz ... Lord Howe with the British fleet having appeared in sight of the combined fleet before Gibraltar'",
      definition="Printings of a Boston paragraph of 29 November 1782: 'Tuesday evening arrived here a brig from Cadiz, which place she left the 26th ultimo: By this vessel we have received intelligence that Lord Howe with the British fleet having appeared in sight of the combined fleet before Gibraltar, induced the latter to pursue them, when they immediately stood for the coast of Barbara, and taking the advantage of a fair wind, stood for, and (as the account says) effectually relieved that fortress...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. News by a ship, at second hand.",
      role='report', words=55, dateline=True,
      core=[r'arrived\W+here\W+a\W+brig\W+from\W+Cadiz,?\W+which\W+place\W+she\W+left'],
      back=True,
      first="Boston, November 1782: news from Cadiz that Lord Howe's fleet had relieved Gibraltar.",
      what="the Boston report of the brig from Cadiz",
      printings=[(k('NHG', '11-30', 2), {'core': [r'B\W*O\W*S\W*T\W*O\W*N\W*,?\W+November\W+29\W+Tuesday\W+evening\W+arrived\W+here\W+a\W+brig'], 'dateline': False, 'back': False, 'words': 64}), (k('CC', '12-03', 3), {'core': [r'B\W*O\W*S\W*T\W*O\W*N\W*,?\W+November\W+29\W+Tuesday\W+evening\W+arrived\W+here\W+a\W+brig'], 'dateline': False, 'back': False, 'words': 64}), (k('PP', '12-10', 2), {'core': [r'Nov\W+29\W+Tuesday\W+evening\W+arrived\W+here\W+a\W+brig'], 'dateline': False, 'back': False, 'words': 57}), k('NJG', '12-11', 3)]),
 dict(id='hague-1-october-1782-letter-from-paris-on-the-siege', parent='siege-of-gibraltar-autumn-1782', kind='message_group',
      label="Hague, 1 October 1782: 'the following private intelligence from Paris, the contents of which are sufficient to excite the tears of every humane person': the disasters at the siege of Gibraltar",
      definition="Printings of a Hague paragraph of 1 October 1782 with a letter from Paris of late September: 'We have just received the following private intelligence from Paris, the contents of which are sufficient to excite the tears of every humane person. Paris, September 26. Sir, I here send you the melancholy relation of the disasters which happened at the siege of Gibraltar. On the 9th the land batteries began to play on the place...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. A private letter from Paris, as a Hague paper printed it.",
      role='report', words=55, dateline=False,
      core=[r'H\W*A\W*G\W*U\W*E,?\W+(?:October|Oct\.?)\W+1\.?\W+We\W+have\W+just\W+received', r'We\W+have\W+just\W+received\W+the\W+following\W+private\W+intelligence\W+from\W+Paris'],
      first="Paris, September 1782: a private letter on the attack of the floating batteries at Gibraltar.",
      what="the Hague paragraph with the letter from Paris on the siege of Gibraltar",
      printings=[k('PP', '12-05', 2), k('NHG', '12-07', 2), k('CC', '12-10', 2), k('NJG', '12-11', 2)]),
 dict(id='london-report-royal-george-lost-at-spithead-august-1782', kind='message_group',
      label="London, August 1782: 'an express arrived at the Admiralty, from Admiral Lord Howe at Portsmouth, informing the Board, of the melancholy disaster of his Majesty's ship the Royal George'",
      definition="Printings of a London paragraph of late August 1782: 'Yesterday an express arrived at the Admiralty, from Admiral Lord Howe at Portsmouth, informing the Board, of the melancholy disaster of his Majesty's ship the Royal George of 100 guns with most of her crew, being lost at Spithead, about half past ten in the morning of the preceding day. This unfortunate accident happened while the ship was hove upon a careen...' The papers date it 29 August (the New-Hampshire Gazette) or 31 August (the Pennsylvania Packet); the New-Jersey Gazette prints '110 guns'. Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. A London paper's report.",
      role='report', words=55, dateline=False,
      core=[r'(?:Aug(?:ust|\.)?\W*\d\d\.\W+)?Yesterday\W+an\W+express\W+arrived\W+at\W+the\W+[Aa]dmiralty,?\W+from\W+(?:[Aa]dm(?:iral|\.)\W+)?[Ll]ord\W+Howe'],
      first="London, August 1782: the Royal George lost with most of her crew at Spithead.",
      what="the London report of the loss of the Royal George",
      printings=[k('PP', '11-02', 2), k('CC', '11-12', 2), k('NJG', '11-13', 1), k('NHG', '11-16', 2)]),
 dict(id='head-quarters-verplanck-point-orders-of-24-october-1782', kind='document_group',
      label="Head-Quarters, Verplank's Point, 24 October 1782: orders 'Before the army marches from this ground'",
      definition="Printings of the orders of Head-Quarters, Verplank's Point, 24 October 1782, which a correspondent sent to the editor ('as it exhibits the army in so respectable a point of view, he presents it with pleasure to the public'): 'Before the army marches from this ground, the Commander in Chief orders it to be signified to the several corps...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. The army's own orders, with a correspondent's introduction.",
      role='published_document', words=55, dateline=False,
      core=[r'Head\W*-?\W*Quarters,?\W+Verplank.s\W+Point,?\W+Oct(?:ober|\.)?\W+24'],
      first="Verplanck's Point, October 1782: the army's orders before it marched.",
      what="the orders of 24 October 1782 at Verplanck's Point",
      printings=[k('CC', '11-05', 3), k('NJG', '11-06', 2), k('PP', '11-07', 3), k('NHG', '11-09', 2)]),
 dict(id='congress-order-of-7-november-1782-releasing-captain-asgill', kind='document_group',
      label="Congress, 7 November 1782: the order releasing Captain Asgill",
      definition="Printings of the resolution of Congress of 7 November 1782, which several papers head 'Copy of an order of Congress, releasing Capt. Asgill': 'By the United States in Congress assembled, November 7, 1782. On the report of a Committee to whom was referred a letter of the 19th of August, from the Commander in Chief, a report of a Committee thereon, and motion of Mr. Williamson and Mr. Rutledge relative thereto, and also another letter of the 25th of October from the Commander in Chief, with a copy of a letter from the Count de Vergennes...' Printed by all five newspapers that survive for its weeks; admitted by the rule's first part. Congress's own resolution.",
      role='published_document', words=55, dateline=False,
      core=[r'Copy\W+of\W+an\W+order\W+of\W+Congress,?\W+releasing', r'Congress\W+assembled\.?,?\W+November\W+7,?\W+1782'],
      back=True,
      first="Congress, November 1782: the order releasing Captain Asgill.",
      what="Congress's order of 7 November 1782 releasing Captain Asgill",
      printings=[k('NJJ', '11-27', 3), k('PP', '11-29', 2), k('NJG', '12-04', 2), k('CC', '12-10', 2), k('NHG', '12-14', 2)]),
 dict(id='boston-report-bouille-at-martinique-december-1782', kind='message_group',
      label="Boston, 5 December 1782: 'on the 6th of that month the Marquis de Bouille arrived there with a number of ships of the line, and 12,000 troops'",
      definition="Printings of a Boston paragraph of 5 December 1782: 'By a vessel arrived at a neighbouring port from Martinico, which left that Island the eighth of November, we have the very pleasing account, that on the 6th of that month the Marquis de Bouille arrived there with a number of ships of the line, and 12,000 troops. This event has diffused great joy through the dominions of our illustrious ally in that quarter.' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. News by a ship, at second hand.",
      role='report', words=60, dateline=True, stop=r'Tuesday\W+arrived\W+here',
      core=[r'By\W+a\W+vessel\W+arrived\W+at\W+a\W+neighbouring\W+port\W+from\W+Martinico'],
      first="Boston, December 1782: news from Martinique of the Marquis de Bouillé's arrival with ships and troops.",
      what="the Boston report of the Marquis de Bouillé at Martinique",
      printings=[k('NHG', '12-07', 3), k('CC', '12-10', 3), (k('PP', '12-17', 2), {'core': [r'Dec\W+5\W+By\W+a\W+vessel'], 'dateline': False}), (k('NJG', '12-18', 2), {'core': [r'December\W+5\W+By\W+a\W+vessel'], 'dateline': False})]),
 dict(id='letter-from-uxbridge-near-charlestown-5-october-1782', kind='message_group',
      label="A letter dated Uxbridge, near Charlestown, 5 October 1782: 'To write news I have none scarce worth communicating, except that the fleet of transports from Jamaica are arrived'",
      definition="Printings of an extract of a letter 'dated Uxbridge, near Charlestown, South-Carolina, October 5, 1782': 'To write news I have none scarce worth communicating, except that the fleet of transports from Jamaica are arrived, and which, with the fleet arrived a few days before, make upwards of ninety sail: they have threatened to carry away the 1500 negroes they have collected; but if they do, our government is determined to confiscate every marriage settlement of their friends...' Printed by all four newspapers that survive for its weeks; admitted by the rule's first part. A South Carolina correspondent's account.",
      role='report', words=55, dateline=False,
      core=[r'letter,?\W+dated\W+Uxbridge,?\W+near\W+Charlestown'],
      back=True,
      first="South Carolina, October 1782: a letter from near Charlestown on the British transports and the people they are to carry away.",
      what="the letter from Uxbridge, near Charlestown",
      printings=[k('PP', '12-10', 2), k('NJG', '12-18', 3), k('CC', '12-24', 3), k('NHG', '12-28', 2)]),
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
            problems.append((s['id'], key, 'page not in the 1782 pages'))
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
        r['id'] = f'S82-{n:03}'
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
               'admission_rule': 'Reviewed 1782 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1782/'
    return {
        'ledger_id': 'ledger:stories-1782', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1782', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1782, and of 1781 where they reach the 1782 pages (long-running ones '
                   'included), every item in 3 or more papers counted again by the first 40 words of its opening against every page, papers that '
                   'comparison missed looked for again and read, a sweep of word-for-word passages shared by 4 or more papers for items the '
                   'families miss, phrase searches on all 1,509 pages of 1782 in both transcriptions for every admitted and chosen item, and scan '
                   'checks of each admitted passage, by the thin-year rule (Y-THIN as amended on 23 November 2026: an item printed by more than '
                   'half of the newspapers that survive for its weeks, and by at least 4, is eligible; items printed by every surviving paper are '
                   'admitted, the others chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1781.json': 'retrieval_candidates',
                             d+'counted_items.json': 'retrieval_candidates', d+'phrase_patterns.json': 'retrieval_patterns',
                             d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1782.py': 'ledger_code', 'work/archive_data/ledgers/stories_1782_review.json': 'scan_review',
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
