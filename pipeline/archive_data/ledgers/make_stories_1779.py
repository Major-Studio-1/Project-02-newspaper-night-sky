"""Write ledgers/stories_1779.json: reviewed stories of 1779, round one.

1779 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN, as amended on 23 November 2026, the owner's
choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the newspapers that
survive for its weeks (those with a surviving issue between its first and last printing, and at least in the three weeks
from its first printing), and by at least 4; items printed by every newspaper that survives for their weeks are admitted;
the other eligible items are chosen to cover the months and the kinds of news, about as many stories as a standard year
(about 20 to 35, a target, not a quota), one affair's items treated as in X-1800-01; digests are not admitted. The
automatic families first printed in 1779 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1778 over the 1779 pages
(items_from_1778.json); every item in 3 or more papers was counted again by about 100 words of its opening against every
page of the year, and a sweep of word-for-word passages shared by 4 or more papers (as for 1803, X-1803-09) found short
items the families miss. Every chosen item was counted by its own opening with phrase searches over all 1,660 pages of
1779 in both transcriptions (work/story_phrase_search.py's patterns). See outputs/story_discovery_1779/README.md.

The 1779 pages are those whose issue the data release dates to 1779 (work/year_search_pages.py 1779 ... --printed-dates);
no 1779 issue has a corrected date. 1779 has 9 catalogue series, which are 9 papers: no paper is under two numbers.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. Where the item is a letter, a resolution or a declaration printed inside different reports, the
excerpt begins with it (as 1801 and 1803 did). Scan findings, crops and hand-drawn boxes are merged from
stories_1779_review.json after the scan check. Six 1779 pages have their RevX transcriptions filed off from the scans
(derived/revx_page_map.parquet); a printing on such a page takes its excerpt from the CA transcription of its scan page
(one printing here: the New-York Gazette of 31 May, page 2).

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied; other years are reviewed at the same time, and the main
session renumbers at release:
    python work/archive_data/ledgers/make_stories_1779.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1779/search_pages.json). The excerpts are cut from
the 1779 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1779'
D = PROJECT/'outputs/story_discovery_1779'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1779_review.json'
OUT = HERE/'stories_1779.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-23'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83021127': 'The Pennsylvania Packet', 'sn83030493': 'The New-York Gazette', 'sn84023855': 'The Connecticut Courant',
         'sn83025471': 'The New-Jersey Gazette', 'sn83025584': 'The New-Hampshire Gazette', 'sn84024739': 'The Virginia Gazette',
         'sn84026485': 'The New-Jersey Journal', 'sn83021183': 'The Newport Gazette', 'sn84026945': 'The Gazette of the State of South-Carolina'}
ONE = {'PP': 'sn83021127', 'NYG': 'sn83030493', 'CC': 'sn84023855', 'NJG': 'sn83025471', 'NHG': 'sn83025584', 'VG': 'sn84024739',
       'NJJ': 'sn84026485', 'NG': 'sn83021183', 'SCG': 'sn84026945'}
# Scan pages that hold another issue's sheet a second time, found by the scan check. A printing listed on such a page keeps
# its number (so the ids of the scan check stay as they were) but is not an observation: it is not a printing of its own.
SECOND_SCANS = {
    'sn83021127|1779-04-10|1|2': ("The film of the Pennsylvania Packet of Saturday 10 April 1779 holds the sheet of Tuesday 6 April "
                                  "(pages 2 and 3) a second time: the same text and the same broken letters and blots on two scans. "
                                  "The issue's own pages 2 and 3 are not in the collection."),
}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1779), page and edition."""
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
 dict(id='congress-and-the-paper-money-january-1779', kind='context_group',
      label="Congress and its paper money, January 1779: the resolutions of 2 January and Congress's address of 13 January",
      definition="Two acts of the Continental Congress on its bills of credit, printed in January and February 1779, often together: the resolutions of 2 January calling on the states for their quotas and taking two emissions out of circulation, and Congress's address of 13 January explaining why it had issued paper money and why it now called for taxes.",
      children=['congress-resolutions-of-2-january-1779-on-the-bills-of-credit', 'congress-address-of-13-january-1779-on-the-paper-money']),
 dict(id='congress-resolutions-of-2-january-1779-on-the-bills-of-credit', parent='congress-and-the-paper-money-january-1779', kind='document_group',
      label="Congress, 2 January 1779: 'Whereas these United States, unprovided with revenues ... have ... been under the necessity of emitting bills of credit': the states' quotas, and two emissions taken out of circulation",
      definition="Printings of the resolutions of the Continental Congress of 2 January 1779, headed 'In Congress, January 2, 1779': 'Whereas these United States, unprovided with revenues, and not heretofore in a condition to raise them, have, in the course of the present war, repeatedly been under the necessity of emitting bills of credit, for the redemption of which the faith of these United States has been solemnly pledged...' The resolutions call on the states to raise by taxes their quotas of fifteen millions of dollars for 1779, and, 'whereas many counterfeits have appeared in circulation' of the emissions of 20 May 1777 and 11 April 1778, take those two emissions out of circulation. The Pennsylvania Packet printed them in five issues; four papers print them again after Congress's address of 13 January, which recommends 'the annexed resolutions'. Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      core=[CONGRESS + r'\W+Jan(?:uary|\.)?\s*2\b[^W]{0,12}W\s?H\s?E\s?R\s?E\s?A\s?S', r'W\s?H\s?E\s?R\s?E\s?A\s?S\s+the(?:se)?\s+United\s+States,?\s+unprovided'],
      first="Congress, 2 January 1779: the states called on for their quotas, and the emissions of 1777 and 1778 taken out of circulation.",
      what="Congress's resolutions of 2 January 1779 on the bills of credit",
      printings=[k('PP', '01-05', 3), k('PP', '01-07', 3), k('PP', '01-12', 4), k('NJG', '01-13', 1), k('PP', '01-14', 4), k('CC', '01-19', 3),
                 (k('PP', '01-21', 3), {'core': [r'January\W+2,?\W+1779\W+W\W*HEREAS\W+these'], 'dateline': False, 'words': 72}), k('NYG', '01-25', 2), (k('NHG', '01-26', 1), {'core': [r'I\W*N\W+C\W*O\W*N\W*G\W*R\W*E\W*S\W*S,?\W+January\W+2,?\W+1779\W+W\W*HEREAS'], 'dateline': False, 'words': 76}), (k('NJG', '02-03', 2), {'core': [r'January\W+2,?\W+1779\W+W\W*HEREAS\W+these'], 'dateline': False, 'words': 72}), k('CC', '02-16', 1), k('VG', '02-19', 2)]),
 dict(id='congress-address-of-13-january-1779-on-the-paper-money', parent='congress-and-the-paper-money-january-1779', kind='document_group',
      label="Congress, 13 January 1779: 'We cannot review the progress of the revolution which has given freedom to America': Congress's address on its paper money",
      definition="Printings of Congress's address headed 'In Congress, January 13, 1779': 'We cannot review the progress of the revolution which has given freedom to America, without admiring the goodness and gratefully acknowledging the interposition of Divine Providence...' It says that taxation was impracticable at the start of the war, that Congress 'from necessity, embraced the expedient of emitting paper money on the faith of the United States', and that the enemy had counterfeited the bills, and it recommends the resolutions of 2 January to the legislatures. Congress's own words.",
      role='published_document', words=55, dateline=False,
      core=[CONGRESS + r'\W+Jan(?:uary|\.)?\s*13\b', r'W\s?E\s+cannot\s+review\s+the\s+progress\s+of\s+the\s+revolution'],
      first="Congress, 13 January 1779: its address on the paper money.",
      what="Congress's address of 13 January 1779 on its paper money",
      printings=[k('PP', '01-21', 3), k('NJG', '02-03', 1), k('CC', '02-16', 1), k('VG', '02-19', 2)]),
 dict(id='fuser-summons-to-the-fort-at-sunbury-and-the-answer-november-1778', kind='document_group',
      label="Sunbury, Georgia, 25 November 1778: Lieutenant Colonel Fuser's summons to the fort, and Colonel McIntosh's answer, 'Come and take it'",
      definition="Printings of two letters, as the papers published them in January and February 1779 with other papers from Georgia: 'In the morning of the 24th of November Colonel John M'Intosh, commanding officer in Fort Morris, received the following from Lieut. Col. Fuser, commanding a body of British troops, who had the night before taken possession of the upper end of the town of Sunbury': 'You cannot be ignorant that four armies are in motion to reduce this province... if you deliver me the fort which you command, lay down your arms, and remain neuter until the fate of America is determined, you shall, as well as all the inhabitants of this parish, remain in the peaceable possession of your property'; and the answer: 'We, Sir, are fighting the battle of America, and therefore disdain to remain neuter till its fate is determined.—As to surrendering the fort, receive this laconic reply.—Come and take it.' A British officer's summons and an American officer's answer, in an American publication.",
      role='published_document', words=55, dateline=False,
      core=[r'In\s+the\s+morning\s+of\s+the\s+2[45]th\s+of\s+November', r'Sunbury,?\s+Nov(?:ember|\.)?\s+25,?\s+1778'],
      first="Sunbury, Georgia, November 1778: a British officer's summons to the fort and the American commander's answer.",
      what="Colonel Fuser's summons at Sunbury and the answer",
      printings=[k('PP', '01-30', 2), k('NJG', '02-03', 2), k('NYG', '02-15', 2), k('NJJ', '02-16', 4), k('NHG', '02-23', 2)]),
 dict(id='king-speech-opening-parliament-26-november-1778', kind='document_group',
      label="The King's speech at the opening of Parliament, 26 November 1778: 'I have called you together in a conjuncture which demands your most serious attention'",
      definition="Printings of George III's speech to both Houses of Parliament at the opening of the session on 26 November 1778, as the papers took it from London papers ('From the London General Advertiser and Morning Intelligencer of November 27, 1778'): 'My Lords and Gentlemen, I have called you together in a conjuncture which demands your most serious attention. In the time of profound peace, without pretence of provocation or colour of complaint, the Court of France hath not forbore to disturb the public tranquillity, in violation of the faith of treaties and the general rights of Sovereigns, at first by the clandestine supply of arms and other aid to my revolted subjects in North-America...' Printed by all seven newspapers that survive for its weeks; admitted by the rule's first part. The King's own words.",
      role='published_document', words=55, dateline=False,
      core=[r'My\s+Lords\s+and\s+Gentlemen\W+(?:I\s*)?H\s?AVE\s+called\s+you\s+together'],
      first="London, 26 November 1778: the King's speech at the opening of Parliament.",
      what="the King's speech of 26 November 1778",
      printings=[k('PP', '02-09', 2), k('NJG', '02-10', 2), k('VG', '02-12', 1), k('NYG', '02-15', 2), k('NJJ', '02-16', 2), k('CC', '02-23', 3), k('NHG', '03-02', 2)]),
 dict(id='washington-proclamation-pardoning-deserters-10-march-1779', kind='document_group',
      label="General Washington's proclamation of 10 March 1779: 'full pardon to all those who shall rejoin their respective corps by the first of May next'",
      definition="Printings of a proclamation 'By His Excellency George Washington, Esq. General and Commander in Chief of the Forces of the United States of America': 'Whereas it hath been represented, that many of those soldiers who have been induced from divers motives to desert their corps, and are now dispersed in different parts of these States, having seen their error, would be glad to return to their duty, but are restrained by the fear of punishment... I do hereby proclaim full pardon to all those who shall rejoin their respective corps by the first of May next', with a warning to those who do not. Given at Head-Quarters, Middlebrook, 10 March 1779. The Pennsylvania Packet printed it in four issues. The commander in chief's own proclamation.",
      role='published_document', words=55, dateline=False,
      core=[r'B\s?Y\s+H\s?I\s?S\s+E\s?X\s?C\s?E\s?L\s?L\s?E\s?N\s?C\s?Y\s+G\s?E\s?O\s?R\s?G\s?E\s+W\s?A\s?S\s?H\s?I\s?N\s?G\s?T\s?O\s?N', r'W\s?H\s?E\s?R\s?E\s?A\s?S\s+it\s+hath\s+been\s+represented'],
      first="Middlebrook, 10 March 1779: General Washington's proclamation offering pardon to deserters who return.",
      what="General Washington's proclamation of 10 March 1779",
      printings=[k('NJG', '03-17', 2), k('PP', '03-20', 3), k('CC', '03-23', 2), k('VG', '04-02', 2), k('PP', '04-03', 1), k('NHG', '04-06', 3), k('PP', '04-10', 4), k('PP', '04-17', 4)]),
 dict(id='putnam-letter-on-the-incursion-to-horseneck-march-1779', kind='document_group',
      label="General Putnam's account of the enemy's incursion to Horseneck, Camp at Reading, 2 March 1779, sent to Congress by General Washington",
      definition="Printings of an extract of Major General Putnam's letter dated Camp at Reading, 2 March 1779: 'A detachment from the enemy at Kingsbridge, consisting of the 17th, 44th and 57th British regiments, one of Hessian, and two of new levies, marched from their lines for Horseneck on the evening of the 25th ult. with an intention of surprising the troops at that place and destroying the salt works...' Three papers print it with General Washington's letter to the President of Congress from Head-Quarters, Middlebrook ('I herewith transmit your Excellency an extract of a letter from Major General Putnam, containing an account of the incursion of the enemy to Horseneck'), published by order of Congress; the Virginia Gazette prints the extract alone. Counted by the letter all four print (C-02). An American general's own account.",
      role='published_document', words=55, dateline=True,
      core=[r'Head\W*Quarters,?\s+Middle\W*brook,?\s+March\s+[38]\b', r'Extract\s+of\s+a\s+letter\s+from\s+Major\W+General\s+Putnam'],
      first="Middlebrook, March 1779: General Washington sends Congress General Putnam's account of the enemy's incursion to Horseneck.",
      what="General Putnam's account of the incursion to Horseneck",
      printings=[k('PP', '03-13', 2), k('NJG', '03-17', 2), k('VG', '04-02', 2), k('NHG', '05-04', 2)]),
 dict(id='charlestown-report-campbell-retreat-from-augusta-march-1779', kind='message_group',
      label="Charlestown, 3 March 1779: 'Col. Campbell's expedition from Savannah to Augusta ... has proved as unfortunate as Major Gardiner's to Port Royal'",
      definition="Printings of a paragraph of Charlestown (South Carolina) news dated 3 March 1779: 'Col. Campbell's expedition from Savannah to Augusta, with the Highlanders and Col. Brown's rangers, has proved as unfortunate as Major Gardiner's to Port Royal; to escape a Burgoyne he has made a very sudden and precipitate retreat down the country, leaving us in possession of all the back counties of Georgia, and his friends the Tories to fall a sacrifice, a whole regiment whereof... have already been defeated, and upwards of 150 of them made prisoners.' A Charlestown paper's report. The film of the Pennsylvania Packet of 10 April holds the sheet of 6 April a second time; that second scan is not counted as a printing.",
      role='report', words=55, dateline=True,
      core=[r'(?:Col\.?|Colonel)\s+\S+\s+expedition\s+from\s+Savannah\s+to\s+Augusta'],
      first="Charlestown, March 1779: a report that Colonel Campbell's expedition to Augusta has retreated down the country.",
      what="the Charlestown report of Colonel Campbell's retreat from Augusta",
      printings=[k('PP', '04-06', 2), (k('NHG', '04-06', 4), {'core': [r'March\W+3\W+Col\W+Ca'], 'dateline': False, 'words': 57}), k('NJG', '04-07', 2), k('VG', '04-09', 2), k('PP', '04-10', 2), (k('CC', '04-13', 2), {'core': [r'March\W+3\W+Col\W+Ca'], 'dateline': False, 'words': 57})]),
 dict(id='livingston-answer-to-clinton-15-april-1779', kind='document_group',
      label="Governor Livingston of New Jersey to Sir Henry Clinton, Elizabeth-Town, 15 April 1779: 'I received your Excellency's letter of the 10th instant this afternoon'",
      definition="Printings of a letter from William Livingston, Governor of New Jersey, to the British commander in chief, Sir Henry Clinton, answering Clinton's letter of 10 April, which a New York paper had published with Livingston's letter of 29 March: 'I received your Excellency's letter of the 10th instant this afternoon, and had an opportunity about an hour thereafter, to see a copy of it in the New-York American Gazette, together with mine of the 29th of March, which occasioned it...' The New-York Gazette, printed in the city the British held, prints it under its own introduction, which calls the writer 'titular Governor of that province'. A governor's own letter to an enemy commander, printed by papers of both sides.",
      role='published_document', words=55, dateline=False,
      core=[r'Elizabeth\W*Town,?\s+(?:15th\s+April|April\s+15)', r'I\s+R\s?E\s?C\s?E\s?I\s?V\s?E\s?D\s+your\s+Excellency.s\s+letter\s+of\s+the\s+10th'],
      first="Elizabeth-Town, April 1779: Governor Livingston's answer to Sir Henry Clinton.",
      what="Governor Livingston's answer to Sir Henry Clinton",
      printings=[k('NYG', '04-26', 3), k('NJG', '04-28', 2), k('PP', '05-01', 2), k('CC', '05-18', 4)]),
 dict(id='thomson-mason-letter-enemy-in-hampton-road-may-1779', kind='message_group',
      label="Thomson Mason to the President of Congress, Leesburg, 17 May 1779: 'about forty sail of the enemy appeared in Hampton Road'",
      definition="Printings of an extract of a letter from Thomson Mason to the President of Congress, dated Leesburg, Virginia, 17 May 1779: 'My son, who is immediately from Hampton, informs me, that about forty sail of the enemy appeared in Hampton Road on Sunday the 9th instant. On Monday they attacked our fort at Portsmouth, where Major Matthews commanded with 150 men...' It goes on with the fort given up, ships burned on the stocks, and a party intercepted at the Great Bridge. The New-Hampshire Gazette of 8 June prints another letter of Mr. Mason's of the same day, in other words, sent on by General Gates; it is not counted with this one. A Virginian's letter, giving his son's account.",
      role='report', words=55, dateline=True,
      core=[r'Extra\w*\s+of\s+a\s+letter\s+from\s+Thomson', r'Thomson\s+M\w+,?\s+to\s+the\s+Pre\w+\s+of\s+Congress'],
      first="Leesburg, Virginia, May 1779: a letter to the President of Congress reports enemy ships in Hampton Road and the attack on Portsmouth.",
      what="Thomson Mason's letter on the enemy in Hampton Road",
      printings=[k('PP', '05-22', 3), (k('NJG', '05-26', 2), {'core': [r'M\W*A\W*Y\W+22\W+Extract\W+of\W+a\W+letter'], 'dateline': False}), k('NYG', '05-31', 2), (k('CC', '06-08', 2), {'core': [r'M\W*A\W*Y\W+22\W+Extract\W+of\W+a\W+letter'], 'dateline': False})]),
 dict(id='philadelphia-general-meeting-on-prices-may-1779', kind='document_group',
      label="Philadelphia, 25 May 1779: a general meeting of the citizens at the State-House Yard, General Roberdeau's address, and the meeting's resolutions on prices",
      definition="Printings of the proceedings of a general meeting 'of the Citizens of Philadelphia, and Parts adjacent, at the State-House Yard in this City' (held on 25 May 1779): 'General Roberdeau was unanimously requested to take the Chair, who introduced the Business with the following Address: Gentlemen, Although I feel pain from the situation in which you have been pleased to place me, it is with pleasure I meet you, my Fellow Citizens, to consider and determine upon measures for our mutual and public happiness...' The address is followed by the meeting's resolutions, among them that 'the advanced, or monopolized, price of the present month be instantly taken off', and the choice of committees on prices. A citizens' meeting's own proceedings, signed by its chairman.",
      role='published_document', words=55, dateline=True,
      core=[r'At\s+a\s+General\s+Meeting\s+of\s+the\s+Citizens\s+of\s+Philadelphia'],
      first="Philadelphia, May 1779: a general meeting of the citizens on prices.",
      what="the proceedings of the Philadelphia general meeting of May 1779",
      printings=[k('PP', '05-27', 2), k('NYG', '06-07', 3), k('NJG', '06-09', 4), k('VG', '06-12', 1), k('CC', '06-15', 2)]),
 dict(id='congress-address-to-the-inhabitants-26-may-1779', kind='document_group',
      label="Congress to the inhabitants of the United States, 26 May 1779: 'The present situation of public affairs demands your most serious attention'",
      definition="Printings of the address of Congress 'To the inhabitants of the United States of America', done in Congress by unanimous consent on 26 May 1779 and signed by John Jay, President: 'Friends and Countrymen, The present situation of public affairs demands your most serious attention, and particularly the great and encreasing depreciation of your currency requires the immediate, strenuous, and united efforts of all true friends to their country...' It reviews the war and the alliance and asks the states to fill their battalions, pay their quotas, lend money and sink their own emissions. Congress's own words.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:AN\s+ADDRESS\s+)?TO\s+THE\s+INHABITANTS\s+OF\s+THE\s+United\W+States\s+of\s+America\W+FRIENDS', r'FRIENDS\s+AND\s+COUNTRYMEN'],
      first="Philadelphia, 26 May 1779: Congress's address to the inhabitants of the United States.",
      what="Congress's address of 26 May 1779",
      printings=[k('PP', '05-29', 2), k('NJG', '06-02', 1), k('VG', '06-19', 1), k('NHG', '07-06', 2)]),
 dict(id='fishkill-british-vessels-in-the-north-river-june-1779', kind='message_group',
      label="Fishkill, 3 June 1779: 'a number of British vessels made their appearance in the North River'",
      definition="Printings of a Fishkill (New York) report of 3 June 1779: 'The latter end of last week, a number of British vessels made their appearance in the North River; they consist of 13 ships, 3 brigs, 4 top-sail schooners, 3 galleys, 6 top-sail sloops, about 20 smaller vessels, and a great number of flat-bottom boats. Last Lord's day, (31st ult.) 1500 men landed eight miles below Peekskill...' It goes on with the enemy's batteries against Fort de la Fayette. A Fishkill paper's report.",
      role='report', words=55, dateline=False,
      core=[r'FISH\W*KILL\W+J(?:une|UNE)\s+3', r'The\s+latter\s+end\s+of\s+last\s+week,?\s+a\s+number\s+of\s+British\s+vessels'],
      first="Fishkill, June 1779: a report of British ships and troops on the North River.",
      what="the Fishkill report of British vessels in the North River",
      printings=[k('PP', '06-08', 2), k('CC', '06-08', 3), k('NJG', '06-09', 2), k('NYG', '06-14', 2), k('VG', '06-19', 2)]),
 dict(id='philadelphia-last-advices-from-south-carolina-may-1779', kind='message_group',
      label="Philadelphia, May 1779: 'The last advices from South Carolina inform that the British army had entered that State, with intent ... to get possession of Charlestown'",
      definition="Printings of a paragraph of news dated Philadelphia, 27 May 1779 in some papers: 'The last advices from South-Carolina inform that the British army had entered that State, with intent, it was supposed, to get possession of Charlestown, and that Count Pulaski has had a smart skirmish, in which his horse was killed under him with fourteen balls... but as General Moultrie was in their front, and General Lincoln in their rear, both with a considerable army, it was very probable there would be another Burgoyneade.' A report at second hand, with a prediction.",
      role='report', words=55, dateline=True,
      core=[r'The\s+last\s+advices\s+from\s+South\W+Carolina\s+inform'],
      first="Philadelphia, May 1779: a report that the British army has entered South Carolina.",
      what="the paragraph on the last advices from South Carolina",
      printings=[k('NJG', '06-02', 3), k('NYG', '06-07', 3), (k('VG', '06-12', 2), {'core': [r'May\W+29\W+The\W+last\W+advices'], 'dateline': False}), k('CC', '06-15', 3), k('NHG', '06-22', 2)]),
 dict(id='collier-and-tryon-address-to-the-inhabitants-of-connecticut-july-1779', kind='document_group',
      label="Commodore Sir George Collier and Major General Tryon, July 1779: their address to the inhabitants of Connecticut",
      definition="Printings of the address of the commanders of a British expedition to the Connecticut coast in July 1779: 'By Commodore Sir George Collier, Commander in Chief of His Majesty's Ships and Vessels in North-America; and Major-General William Tryon, Commanding His Majesty's Land Forces on a Separate Expedition. Address to the Inhabitants of Connecticut. The ungenerous and wanton Insurrection against the Sovereignty of Great-Britain, into which this Colony has been deluded by the Artifices of desperate and designing Men for private Purposes...' It is dated on board the Camilla in the Sound, 4 July 1779. The Newport Gazette, printed in the town the British held, prints it on 8 July (a separate sheet of that paper, which the collection files under 2 July although it prints the address and a Newport paragraph of 5 July, is left out until its date is settled); the Connecticut Courant prints it as one of 'the following insolent Addresses' left in New Haven by the British troops, and the Pennsylvania Packet and the New-Jersey Gazette after General Parsons's letter on the expedition. Satirical verses printed under the same title by three papers are not counted. The British commanders' own address.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:By\s+)?Commodore\s+Sir\s+G\s?E\s?O\s?R\s?G\s?E\s+C\s?O\s?L\s?L\s?I\s?E\s?R', r'C\s?O\s?L\s?L\s?I\s?E\s?R,?\s+Commander\s+in\s+Chief\s+of\s+[Hh]is\s+Majesty'],
      first="Connecticut, July 1779: the British commanders' address to the inhabitants.",
      what="the address of Sir George Collier and General Tryon to the inhabitants of Connecticut",
      printings=[k('NG', '07-08', 1), k('NYG', '07-12', 1), k('CC', '07-13', 2), k('PP', '07-20', 2), k('NJG', '07-28', 2)]),
 dict(id='officer-of-rank-letter-on-the-attack-at-stono-ferry-june-1779', kind='message_group',
      label="South Carolina, 22 June 1779: 'General Lincoln having received such intelligence of the intention, strength, and position of the enemy, as rendered it advisable to attack them at Stono Ferry'",
      definition="Printings of an account of General Lincoln's attack on the British post at Stono Ferry, South Carolina, on 20 June 1779, which four papers print as an 'Extract of a letter from an officer of rank, in South-Carolina, June 22, 1779' and the Virginia Gazette as 'Authentic intelligence received by his Excellency the Governor from South Carolina': 'General Lincoln having received such intelligence of the intention, strength, and position of the enemy, as rendered it advisable to attack them at Stono Ferry, did so on the 20th instant about 7 in the morning, with great vigour; they were advantageously posted and covered by three strong redoubts...' An American officer's account.",
      role='report', words=55, dateline=True,
      core=[r'Authentic\s+intelligence\s+received\s+by\s+his\s+Excellency', r'Extra\w*\s+of\s+a\s+letter\s+from\s+an\s+officer\s+of\s+rank,?\s+in\s+South'],
      first="South Carolina, June 1779: an officer's account of General Lincoln's attack at Stono Ferry.",
      what="the account of the attack at Stono Ferry",
      printings=[k('VG', '07-17', 3), k('PP', '07-20', 3), k('NYG', '08-02', 1), k('CC', '08-03', 2), k('NG', '08-19', 2)]),
 dict(id='stony-point-taken-july-1779', kind='context_group',
      label="Stony Point, July 1779: General Washington's two letters to Congress with General Wayne's reports, and the thanks of Congress",
      definition="Three public acts on the night attack on the British post at Stony Point on the Hudson, 15 and 16 July 1779, as the papers printed them in July and August: General Washington's letter of 16 July sending General Wayne's first note, his letter of 21 July sending Wayne's report, and the resolutions of Congress of 26 July thanking the commanders, officers and soldiers.",
      children=['washington-letter-of-16-july-1779-with-wayne-note', 'washington-letter-of-21-july-1779-with-wayne-report', 'congress-thanks-for-stony-point-26-july-1779']),
 dict(id='washington-letter-of-16-july-1779-with-wayne-note', parent='stony-point-taken-july-1779', kind='document_group',
      label="General Washington to Congress, New Windsor, 16 July 1779, 'half after nine o'clock, A. M.', with General Wayne's note from Stony Point: 'The fort and garrison ... are ours'",
      definition="Printings of General Washington's letter to the President of Congress, Head-Quarters, New-Windsor, 16 July 1779, 'Half after nine o'clock, A. M.', published by order of Congress: 'I have the pleasure to transmit your Excellency the inclosed copy of a letter from Brigadier General Wayne, which this moment came to hand. I congratulate Congress upon our success...', with General Wayne's note to him from Stony Point at two in the morning: 'The fort and garrison with Col. Johnston are ours. Our officers and men behaved like men who are determined to be free.' The commanders' own letters.",
      role='published_document', words=55, dateline=False,
      core=[r'Head\W*[Qq]uarters,?\s+N\.?\W*\w*\W*Windsor,?\s+July\s+1?6\b', r'Half\s+after\s+nine\s+o.clock'],
      first="New Windsor, 16 July 1779: General Washington sends Congress General Wayne's note that Stony Point is taken.",
      what="General Washington's letter of 16 July 1779 with General Wayne's note",
      printings=[k('PP', '07-20', 3), k('NJG', '07-28', 2), k('VG', '07-31', 2), k('NYG', '08-02', 3), k('CC', '08-03', 2)]),
 dict(id='washington-letter-of-21-july-1779-with-wayne-report', parent='stony-point-taken-july-1779', kind='document_group',
      label="General Washington to Congress, New Windsor, 21 July 1779, with General Wayne's report of 17 July on the reduction of Stony Point",
      definition="Printings of General Washington's letter to the President of Congress, Head-Quarters, New-Windsor, 21 July 1779: 'On the 16th instant I had the honor to inform Congress of a successful attack upon the enemy's post at Stony-Point, on the preceding night, by Brigadier General Wayne, and the corps of light infantry under his command...', with General Wayne's report from Stony Point of 17 July ('a full and particular relation of the reduction of this point, by the light infantry under my command') and the return of the killed and wounded, published by order of Congress. The commanders' own letters.",
      role='published_document', words=55, dateline=False,
      core=[r'Head\W*Quarters,?\s+New\W*Windsor,?\s+July\s+21', r'On\s+the\s+1[56]th\s+instant\s+I\s+had\s+the\s+hono'],
      first="New Windsor, 21 July 1779: General Washington sends Congress General Wayne's report on Stony Point.",
      what="General Washington's letter of 21 July 1779 with General Wayne's report",
      printings=[k('PP', '07-27', 3), k('NJG', '08-04', 1), k('NYG', '08-09', 2), k('CC', '08-10', 2), k('NHG', '08-17', 2)]),
 dict(id='congress-thanks-for-stony-point-26-july-1779', parent='stony-point-taken-july-1779', kind='document_group',
      label="Congress, 26 July 1779: the thanks of Congress to General Washington, General Wayne and the officers and soldiers at Stony Point",
      definition="Printings of the resolutions of Congress of 26 July 1779: 'Resolved unanimously, that the thanks of Congress be given to his Excellency General Washington, for the vigilance, wisdom and magnanimity, with which he hath conducted the military operations of these States...'; the thanks to Brigadier General Wayne 'for his brave, prudent and soldierly conduct', and the sense of Congress of the good conduct of the officers and soldiers in the assault. Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      core=[CONGRESS + r'\W+J(?:uly|ULY)\W*2[56]', r'thanks\s+of\s+Congress\s+be\s+given\s+to\s+his\s+Excellency\s+Gen'],
      first="Congress, 26 July 1779: thanks to General Washington, General Wayne and the troops for Stony Point.",
      what="the thanks of Congress of 26 July 1779 for Stony Point",
      printings=[k('PP', '07-27', 3), k('NJG', '08-04', 2), k('VG', '08-07', 2), k('NYG', '08-09', 2), k('NHG', '08-17', 2), k('CC', '08-17', 4)]),
 dict(id='spanish-manifesto-delivered-by-almodovar-june-1779', kind='document_group',
      label="The King of Spain's manifesto, delivered in London by his ambassador the Marquis d'Almodovar, June 1779: 'All the world has been witness to the noble impartiality of the King'",
      definition="Printings of the paper the Spanish ambassador delivered in London in June 1779 before leaving, which Lord North laid before the House of Commons as 'a true translation of the manifesto delivered by the Spanish Ambassador': 'Spanish Manifesto. All the world has been witness to the noble impartiality of the King, in the midst of the disputes of the court of London with its American colonies and with France...' It sets out Spain's grievances and ends that the King 'finds himself under the disagreeable necessity of making use of all the means which the Almighty has intrusted him with'. Most papers print it from an English paper brought to Salem from Bilbao; the New-York Gazette prints another translation ('The world can bear witness to the noble partiality of the King') within the House of Lords' proceedings, and the Pennsylvania Packet prints it a second time within the King of Spain's own decree from the Madrid Gazette of 29 June ('All the world has been witness to my noble impartiality'). Counted together (C-02). The Spanish court's own declaration, in English translations.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:S\s?P\s?A\s?N\s?I\s?S\s?H\s+)?M\s?A\s?N\s?I\s?F\s?E\s?S\s?T\s?O\.?\s+(?:A\s?LL|T\s?HE)\s+(?:the\s+)?world', r'A\s?LL\s+the\s+world\s+has\s+been\s+witness\s+to\s+my'],
      first="London, June 1779: the Spanish ambassador's manifesto, as the House of Commons received it.",
      what="the Spanish manifesto delivered by the Marquis d'Almodovar",
      printings=[k('CC', '08-31', 2), k('NHG', '08-31', 2), k('PP', '09-02', 5), k('NG', '09-02', 1), k('NYG', '09-06', 1), k('NJG', '09-08', 1), k('PP', '09-09', 2), k('VG', '09-18', 2)]),
 dict(id='continental-frigates-with-jamaica-prizes-august-1779', kind='message_group',
      label="Boston, August 1779: 'arrived here the Continental frigates Providence, Queen of France and Ranger', with ships of a Jamaica fleet",
      definition="Printings of a Boston paragraph of August 1779: 'Saturday last arrived here the Continental Frigates Providence, Queen of France & Ranger; during their cruise they fell in with a Jamaica Fleet of upwards of 100 sail, under convoy of several Frigates.—This favourable opportunity they improved as well as circumstances would admit.—They picked out nine ships and one brig deeply laden with rum, sugar, &c. seven of which have arrived here, and one at Cape Ann.' Some papers print 'Sunday last', and the Connecticut Courant 'Saturday se'nnight' (a week before); the papers differ on how many of the prizes had arrived and where. A Boston paper's report.",
      role='report', words=55, dateline=True,
      core=[r'(?:S\s?ATURDAY|S\s?UNDAY)\s+last\s+(?:night\s+)?(?:arrived\s+here\s+)?the\s+Continental\s+Frigates'],
      first="Boston, August 1779: three Continental frigates arrive with prizes from a Jamaica fleet.",
      what="the Boston report of the Continental frigates and their Jamaica prizes",
      printings=[k('NHG', '08-31', 3), k('CC', '08-31', 3), k('PP', '09-02', 5), k('NYG', '09-06', 3), k('NJG', '09-08', 1), k('VG', '09-25', 2)]),
 dict(id='basseterre-report-byron-and-estaing-off-grenada-july-1779', kind='message_group',
      label="Basseterre, St. Christopher's, 17 July 1779: 'Admiral Byron engaged Mons. d'Estaing's fleet off Grenada'",
      definition="Printings of a report from Basseterre in the British island of St. Christopher's, 17 July 1779 (the New-Hampshire Gazette: 'taken from the St. Christopher's Gazette'): 'On Thursday morning last arrived here Admiral Byron, with the ships under his command. On Tuesday the sixth of July inst. at six in the morning, Admiral Byron engaged Mons. d'Estaing's fleet off Grenada. The Monmouth engaged a French Rear Admiral for three hours...' It names the British ships engaged and ends with remarks on the admiral's conduct. A report from a British island, as the American papers reprinted it.",
      role='report', words=55, dateline=False,
      core=[r'B\W*A\W*S\W*S?\W*[EA]\W*T\W*T?\W*E\W*R\W*R?\W*E\W*,?\s+July\s+17', r'Thursday\s+morning\s+last\s+arrived\s+here'],
      first="Basseterre, St. Christopher's, July 1779: a report of Admiral Byron's engagement with the Count d'Estaing's fleet off Grenada.",
      what="the Basseterre report of the engagement off Grenada",
      printings=[k('NJG', '08-11', 2), k('NYG', '08-16', 3), k('NG', '08-19', 2), k('CC', '08-24', 1), k('NHG', '08-31', 4)]),
 dict(id='lovell-letter-from-majorbagaduce-28-july-1779', kind='document_group',
      label="Brigadier General Lovell to the President of the Council of Massachusetts, Majorbagaduce, 28 July 1779: 'The army under my command having arrived in Penobscot River'",
      definition="Printings of an extract of a letter from Brigadier General Lovell (the papers print 'Lovell' or 'Lovel'), commanding the Massachusetts expedition against the British post at Majorbagaduce on the Penobscot, to Jeremiah Powell, President of the Council: 'The army under my command having arrived in Penobscot River on the 25th instant—I the same evening attempted to make a lodgment on Majorbaggaduce, but the wind springing up very strong, I was obliged to desist...' An American commander's own report.",
      role='published_document', words=55, dateline=True,
      core=[r'Extra\w*\s+of\s+a\s+[Ll]etter\s+from\s+the\s+Hon\w*\.?\s+Brig\w*\.?\s+Gen\w*\.?\s+Lo[vw]el'],
      first="Majorbagaduce, July 1779: the Massachusetts commander reports the landing at Penobscot.",
      what="General Lovell's letter from Majorbagaduce",
      printings=[k('NHG', '08-17', 3), (k('CC', '08-17', 2), {'core': [r'B\W*O\W*S\W*T\W*O\W*N\W+August\W+12\W+Extract'], 'dateline': False, 'words': 63}), k('PP', '08-24', 3), k('NJG', '08-25', 2)]),
 dict(id='charlestown-report-militia-turn-out-volunteers-september-1779', kind='message_group',
      label="Charlestown, 15 September 1779: 'the militia turn out volunteers, in all parts of the State', and news of the Count d'Estaing's fleet",
      definition="Printings of a paragraph of the Gazette of the State of South-Carolina of 15 September 1779: 'We are assured, that exclusive of draughts, the militia turn out volunteers, in all parts of the State, with such spirit and alacrity, that the ferry men at the several rivers cannot carry the men across fast enough. By the last accounts from Count d'Estaing's fleet, seven British vessels had fallen into their hands...' The Charlestown paper's own report, reprinted in the north in October and November.",
      role='report', words=55, dateline=True,
      core=[r'We\s+are\s+assured,?\s+(?:that,?\s+)?exclusive'],
      first="Charlestown, September 1779: the Charlestown paper reports the militia turning out and prizes taken by the French fleet.",
      what="the Charlestown paragraph of 15 September 1779",
      printings=[k('SCG', '09-15', 3), k('VG', '10-09', 2), k('PP', '10-16', 5), k('NJG', '10-27', 4), k('NYG', '11-01', 2), k('CC', '11-02', 2), k('NHG', '11-09', 2)]),
 dict(id='officer-in-sullivan-army-letter-9-september-1779', kind='message_group',
      label="A letter from an officer in General Sullivan's army, Konadasagea, 9 September 1779: 'Since the action of the 29th of last month, the Indians have fled at the approach of our army'",
      definition="Printings of an extract of a letter 'from an officer in the western army commanded by Major General Sullivan', dated Konadasagea (the papers spell it several ways), 9 September 1779: 'Since the action of the 29th of last month, the Indians have fled at the approach of our army, and left their settlements to our mercy—New-Town, Konowarohala, French Katherines, Candai, Skayes, Gagheonghwa, and Konadasagea, are great heaps of ruin: besides these, we have burnt a number of scattering houses; and destroyed a large country of corn...' An American officer's own account of his army's burning of the towns; it is not the account of the Six Nations.",
      role='report', words=55, dateline=True,
      core=[r'Extra\w*\s+of\s+a\s+letter\s+from\s+an\s+officer\s+in\s+the\s+western\s+army'],
      first="The Six Nations' country, September 1779: an American officer writes that the army has burned the towns.",
      what="the letter from an officer in General Sullivan's army",
      printings=[k('PP', '09-25', 3), k('NJG', '09-29', 3), (k('CC', '10-05', 2), {'core': [r'S\W*E\W*P\W*T\W*E\W*M\W*B\W*E\W*R\W+25\W+Extract'], 'dateline': False}), k('VG', '10-09', 2)]),
 dict(id='king-proclamation-on-the-threatened-invasion-july-1779', kind='document_group',
      label="The King's proclamation of 9 July 1779: 'Whereas we have received intelligence that preparations are making by our enemies to invade this our kingdom'",
      definition="Printings of a proclamation of George III given at St. James's on 9 July 1779, as the papers took it from London papers: 'Whereas we have received intelligence that preparations are making by our enemies to invade this our kingdom... and to the intent that they may not, in case of their landing, strengthen themselves by seizing the horses, oxen and cattle of our subjects...' It charges the officers of the coasts to have the cattle and provisions driven inland 'upon the first approach of the enemy'. The King's own proclamation.",
      role='published_document', words=55, dateline=False,
      core=[r'A\s+P\s?R\s?O\s?C\s?L\s?A\s?M\s?A\s?T\s?I\s?O\s?N\W+(?:G\s?E\s?O\s?R\s?G\s?E\.?\s*R?\.?\W+)?W\s?H\s?E\s?R\s?E\s?A\s?S\W+we\s+have\s+received', r'W\s?H\s?E\s?R\s?E\s?A\s?S\W+we\s+have\s+received\s+intelligence\s+that\s+preparations'],
      first="London, July 1779: the King's proclamation on the threatened invasion.",
      what="the King's proclamation on the threatened invasion",
      printings=[k('NYG', '09-27', 1), k('PP', '10-02', 2), k('NJG', '10-06', 2), k('VG', '10-16', 2), k('CC', '10-19', 2)]),
 dict(id='congress-appoints-jay-minister-to-spain-september-1779', kind='document_group',
      label="Congress, 28 September 1779: John Jay appointed minister plenipotentiary to Spain, Samuel Huntington chosen President, and the thanks of 1 October to Mr. Jay",
      definition="Printings of an extract of the journals of Congress: 'In Congress, Sept. 28, 1779. Congress having appointed the Hon. John Jay, Esq; their Minister Plenipotentiary, to negotiate a treaty of amity and commerce and of alliance between the United States of America and his Catholic Majesty, and he having signified his acceptance of that office, and thereupon resigned the chair, Resolved, That Congress proceed to the choice of a President...'; Samuel Huntington was elected, and on 1 October Congress thanked Mr. Jay for his conduct in the chair. Congress's own journal.",
      role='published_document', words=55, dateline=False,
      core=[CONGRESS + r'\W+Sept(?:ember|\.)?\s+28'],
      first="Congress, September 1779: John Jay appointed minister to Spain, and a new President chosen.",
      what="the journal of Congress of 28 September 1779 on Mr. Jay's appointment",
      printings=[k('PP', '10-05', 2), k('NYG', '10-18', 3), k('CC', '10-19', 3), k('NJG', '10-20', 2)]),
 dict(id='lincoln-letter-on-the-siege-of-savannah-22-october-1779', kind='document_group',
      label="General Lincoln to Congress, Charlestown, 22 October 1779: 'In my last of the 5th ultimo, I had the honor of informing Congress that Count d'Estaing was arrived off Savannah'",
      definition="Printings of Major General Lincoln's letter to the President of Congress, Charlestown, 22 October 1779, published by order of Congress: 'In my last of the 5th ultimo, I had the honor of informing Congress that Count D'Estaing was arrived off Savannah: Orders were immediately given for assembling the troops...' It goes on through the march, the siege and the assault, and ends by referring Congress to the officer who carries it. The New-York Gazette, printed in the city the British held, prints it under its own heading: 'Lincoln's Letter to the Congress. Acknowledging the Defeat of the French and Rebels, in Georgia.' An American general's own report.",
      role='published_document', words=55, dateline=False,
      core=[r'L?INCOLN.S\s+Letter\s+to\s+the\s+CONGRESS', r'(?:S\s?I\s?R,?\s+)?Charlestown,?\s+Oct(?:ober|\.)?\s+22'],
      first="Charlestown, October 1779: General Lincoln reports to Congress on the siege of Savannah.",
      what="General Lincoln's letter of 22 October 1779 on the siege of Savannah",
      printings=[k('PP', '11-13', 2), k('NJG', '11-17', 2), k('NYG', '11-29', 2), k('NHG', '11-30', 1), k('CC', '11-30', 1)]),
 dict(id='gates-letter-rhode-island-evacuated-27-october-1779', kind='document_group',
      label="General Gates to the President of Congress, Newport, 27 October 1779: 'this Island was evacuated by the enemy's troops on the night of the 25th instant'",
      definition="Printings of extracts of Major General Gates's letter to the President of Congress, dated Newport, 27 October 1779: 'I have the honour to acquaint your Excellency, that this Island was evacuated by the enemy's troops on the night of the 25th instant, and the next morning the army under my command took possession of the town of Newport; I have further the pleasure to inform your Excellency, that the enemy did not commit any wanton destruction upon their leaving the Island...' An American general's own report.",
      role='published_document', words=55, dateline=True,
      core=[r'Extra\w*\s+of\s+a\s+letter\s+from\s+Major\W+General\s+Gates'],
      first="Newport, October 1779: General Gates reports that the British have left Rhode Island.",
      what="General Gates's letter of 27 October 1779",
      printings=[k('PP', '11-09', 3), k('NJG', '11-17', 2), k('VG', '11-20', 2), k('CC', '11-30', 1)]),
 dict(id='congress-audience-of-the-french-minister-17-november-1779', kind='document_group',
      label="Congress, 17 November 1779: the public audience of the Chevalier de la Luzerne, minister plenipotentiary of France, with his address and the President's answer",
      definition="Printings of a Philadelphia report of Congress's entertainment and public audience for the new French minister: 'Last Wednesday an entertainment was given by Congress to the Minister Plenipotentiary of France, at which were present by invitation several Foreigners of distinction, and gentlemen of public character. In Congress, November 17, 1779. According to order the Hon. the Chevalier De la Luzerne, Minister Plenipotentiary of his Most Christian Majesty, was introduced to an audience...', with the minister's address ('Since treaties dictated by moderation have fixed upon a permanent base the Union of France with the American Republic...') and the President's answer. The minister's and Congress's own words, in a Philadelphia report.",
      role='published_document', words=55, dateline=True,
      core=[r'L\s?AST\s+Wednesday\s+an\s+entertainment\s+was\s+given\s+by\s+Congress'],
      first="Philadelphia, November 1779: Congress receives the French minister in public audience.",
      what="the report of Congress's audience of the French minister",
      printings=[k('PP', '11-20', 2), k('NJG', '11-24', 2), k('VG', '12-11', 2), k('NHG', '12-14', 1), k('CC', '12-14', 1)]),
 dict(id='congress-resolutions-on-prices-19-november-1779', kind='document_group',
      label="Congress, 19 November 1779: 'Whereas the fluctuating state of prices not only causes inequality and injustice in private dealings': laws to limit prices recommended to the states",
      definition="Printings of the resolutions of Congress of 19 November 1779: 'Whereas the fluctuating state of prices not only causes inequality and injustice in private dealings, and in furnishing the public supplies from the several States, but renders it impracticable to make the proper estimates for future expences, and to fix equitable salaries...' They recommend that the states pass laws limiting the prices of labour and of articles of domestic produce, 'not to exceed twenty fold of the prices current through the various seasons of the year 1774', from 1 February 1780. Two papers print them with the President's letter sending them to the states; the Pennsylvania Packet printed them twice. Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      core=[CONGRESS + r'\W+Nov(?:ember|\.)?\s+19', r'W\s?H\s?E\s?R\s?E\s?A\s?S\s+the\s+fluctuating'],
      first="Congress, 19 November 1779: the states asked to pass laws limiting prices.",
      what="Congress's resolutions of 19 November 1779 on prices",
      printings=[k('PP', '12-09', 2), k('PP', '12-11', 3), k('NHG', '12-14', 1), k('NJG', '12-15', 3), k('CC', '12-21', 1), k('NYG', '12-27', 2)]),
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
            problems.append((s['id'], key, 'page not in the 1779 pages'))
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
        r['id'] = f'S79-{n:03}'
    rows = [r for r in rows if r['page_key'] not in SECOND_SCANS]   # second scans keep their number, not a row
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
               'admission_rule': 'Reviewed 1779 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1779/'
    return {
        'ledger_id': 'ledger:stories-1779', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1779', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1779, and of 1778 where they reach the 1779 pages (long-running ones '
                   'included), every item in 3 or more papers counted again by its opening against every page, a sweep of word-for-word passages '
                   'shared by 4 or more papers for short items the families miss, phrase searches on all 1,660 pages of 1779 in both '
                   'transcriptions for every chosen item, and scan checks of each admitted passage, by the thin-year rule (Y-THIN as amended '
                   'on 23 November 2026: an item printed by more than half of the newspapers that survive for its weeks, and by at least 4, is '
                   'eligible; items printed by every surviving paper are admitted, the others chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1778.json': 'retrieval_candidates',
                             d+'counted_items.json': 'retrieval_candidates', d+'phrase_patterns.json': 'retrieval_patterns',
                             d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1779.py': 'ledger_code', 'work/archive_data/ledgers/stories_1779_review.json': 'scan_review',
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
