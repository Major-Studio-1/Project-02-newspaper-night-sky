"""Write ledgers/stories_1792.json: reviewed stories of 1792, round one.

1792 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN) as the owner amended it on 23 November 2026 (B1): an
item, counted by its own words, is eligible when it was printed by more than half of the newspapers that survive for its weeks,
and by at least 4 newspapers; digests are not. Items printed by every newspaper that survives for their weeks are admitted; the
other eligible items are chosen to cover the months and the kinds of news, about as many stories as a standard year (20 to 35, a
target, not a quota); one affair's items as in X-1800-01. Sub-stories (C-01), private persons (R-04) and the list of items read
and not admitted (R-03) apply as in every year.

The automatic families first printed in 1792 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1791 over the 1792 pages
(items_from_1791.json); every item in 3 or more papers was counted by its own opening over all 1,629 pages of 1792 in both
transcriptions and merged into text units, a sweep of passages shared word for word by 4 or more papers found short items the
families miss, and every unit that meets the bar was read (outputs/story_discovery_1792/README.md). 1792 has 8 catalogue series,
which are 8 papers: the National Gazette and the Gazette of the United States (Philadelphia), the New-Hampshire Gazette
(Portsmouth), the New Hampshire Gazetteer (Exeter), the Kentucky Gazette (Lexington), the Potowmac Guardian (its news is dated
at Martinsburg), the Mirrour (Concord, from September) and one issue of the Phenix (Dover, 26 December). 6 papers survive from
January to September and 5 to 7 after (the Kentucky Gazette has no October issues); the bar is 4, and 5 for the last week of
December. The Kentucky Gazette's issues are filed as edition 2.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 25-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1792_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1792.py [--table] [--base 0.11.30 --target 0.11.31]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1792/search_pages.json). The excerpts are cut from
the 1792 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1792'
D = PROJECT/'outputs/story_discovery_1792'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1792_review.json'
OUT = HERE/'stories_1792.json'
BASE, TARGET = '0.11.30', '0.11.31'   # defaults (v0.11.30 is current since the first thin years were released, 24 November); see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83025887': 'The National Gazette', 'sn83030483': 'The Gazette of the United States',
         'sn83025587': 'The New-Hampshire Gazette, and the General Advertiser', 'sn84023133': 'The New Hampshire Gazetteer',
         'sn82014782': 'The Kentucky Gazette', 'sn84038410': 'The Potowmac Guardian, and Berkeley Advertiser',
         'sn83025523': 'The Mirrour', 'sn84023045': 'The Phenix'}
ONE = {'NG': 'sn83025887', 'GUS': 'sn83030483', 'NHG': 'sn83025587', 'NHGZ': 'sn84023133', 'KG': 'sn82014782',
       'PG': 'sn84038410', 'MIR': 'sn83025523', 'PHX': 'sn84023045'}
SWITCH = {}   # C-04: no paper stands under two catalogue numbers in 1792


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1792), page and edition; for a paper under two catalogue numbers, the
    number it has on that date."""
    full = f'{YEAR}-{date}'
    if paper in SWITCH:
        cut, before, after = SWITCH[paper]
        lccn = before if full < cut else after
    else:
        lccn = ONE[paper]
    return f'{lccn}|{full}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
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
 dict(id='boston-paragraph-colonel-humphreys-resident-in-portugal-1792', kind='message_group',
      label='Boston, January 1792: of the diplomatic corps in Portugal, none support a more elegant style than Colonel Humphreys, the Resident from the United States',
      definition="Printings of a Boston paragraph of January 1792: 'Of the Corps Diplomatique, in Portugal, none support a more elegant style than Col. HUMPHREYS, the Resident from the United States'; his domestics are Americans, and his state coach was made at Philadelphia and is drawn by four American horses; the paragraph adds that he is said to be shortly to be married at Lisbon. A news paragraph about the United States' Resident in Portugal.",
      role='report', words=50, dateline=False,
      core=['Of\\s+the\\s+Corps\\s+Diplomatique'],
      first='Boston, January 1792: Colonel Humphreys at Lisbon.',
      what='the Boston paragraph on Colonel Humphreys',
      printings=[k('NHGZ', '01-14', 3), k('NHG', '01-18', 3), k('NG', '01-26', 3), k('GUS', '01-28', 3), k('PG', '02-07', 1),
                 k('KG', '04-14', 3, 2)]),
 dict(id='english-paper-colonel-simcoe-to-deliver-up-the-british-posts-1791', kind='message_group',
      label="An English paper of 24 October 1791: it is said that one of the first acts of Colonel Simcoe's government in Canada will be to deliver up the British posts",
      definition="Printings of an article of an English paper of 24 October 1791: 'It is said that one of the first acts of Colonel Simcoe's Government in Canada will be, to deliver up the British Posts situated on the east of the River St. Lawrance, and to the south of Nova-Scotia, according to certain articles in the peace with America.' (two papers print 'administration' for 'Government' and 'the treaty of peace'). A report of what is said, from a London paper.",
      role='report', words=38, dateline=False,
      core=['(?:It\\s+is\\s+[sl]aid,?\\s+that\\s+)?one\\s+of\\s+the\\s+first\\s+acts\\s+of\\s+Col'],
      first='An English paper, October 1791: Colonel Simcoe and the British posts.',
      what="the English paper's article on the British posts",
      printings=[k('GUS', '01-18', 3), k('NG', '01-19', 2), k('NHG', '02-01', 3), k('PG', '02-07', 1), k('NHGZ', '02-11', 2),
                 k('KG', '03-31', 3, 2)]),
 dict(id='the-president-letter-and-the-secretary-of-war-statement-on-the-indian-war-january-1792', kind='document_group',
      label="The President to the Secretary of War, 16 January 1792: a statement, from authentic documents, of the circumstances of the present Indian war; the Secretary's statement follows",
      definition="Printings of the President's letter of 16 January 1792 to the Secretary of War: 'As the circumstances which have engaged the United States in the present Indian war may some of them be out of the public recollection, and others perhaps be unknown, it may appear adviseable that you prepare and publish, from authentic documents, a statement of those circumstances, as well as of the measures which have been taken, from time to time, for the re-establishment of peace and friendship'; the Secretary of War's statement of the causes of the hostilities with the Indian tribes north-west of the Ohio follows. Printed together, counted as one item (X-1810-01). The President's and the Secretary's own words.",
      role='published_document', words=55, dateline=False,
      head='(?:S\\s?TATE\\s+P\\s?APER\\.?\\s*)?U\\s?NITED\\s+S\\s?TATES,?\\s+Jan(?:uary|\\.)?\\s*(?:the\\s+)?16(?:th)?,?\\s+1792\\.?\\s*(?:["“]?\\s*S\\s?\\s?I\\s?\\s?R[,.]?\\s*["“]?\\s*)?',
      core=['A\\s?S\\s+the\\s+circumstances\\s+which\\s+have\\s+engaged\\s+the\\s+United\\s+States\\s+in\\s+the\\s+present\\s+Indian'],
      first='The President, 16 January 1792: a statement on the Indian war.',
      what="the President's letter and the Secretary of War's statement",
      printings=[k('NG', '01-30', 2), k('GUS', '02-01', 1), k('PG', '02-21', 1), k('NHG', '02-22', 1), k('NHGZ', '02-22', 2),
                 k('KG', '06-23', 1, 2)]),
 dict(id='albany-paragraph-the-brothertown-indians-petition-to-be-free-citizens-1792', kind='message_group',
      label='Albany, 9 February 1792: the Indians settled at Brothertown petition the Legislature to be put on the footing of free white citizens',
      definition="Printings of an Albany paragraph of 9 February 1792: 'The Indians settled at Brothertown in Herkemer county, we are told, have sent a petition to the Legislature, praying to be put on the footing of free white citizens, except that they do not wish the privilege of selling their lands'; the reasons they give follow. A news paragraph reporting a petition.",
      role='report', words=50, dateline=False,
      core=['The\\s+Indians\\s+settled\\s+at\\s+Brother\\w*'],
      first='Albany, February 1792: the Brothertown petition.',
      what='the Albany paragraph on the Brothertown petition',
      printings=[k('GUS', '02-22', 3), k('NG', '02-23', 2), k('NHG', '02-29', 2), k('NHGZ', '02-29', 3), k('PG', '03-27', 3)]),
 dict(id='act-to-establish-the-post-office-and-post-roads-1792', kind='document_group',
      label='Congress, February 1792: an act to establish the post-office and post-roads within the United States',
      definition="Printings of 'An Act to establish the Post-Office and Post-Roads within the United States', of the first session of the Second Congress: 'Be it enacted by the Senate and House of Representatives of the United States of America, in Congress assembled', the post roads, the postmaster general, the rates of postage and the carriage of newspapers. Congress's own act.",
      role='published_document', words=55, dateline=False,
      core=['A\\s?N\\s+A\\s?CT\\s+to\\s+establish\\s+the\\s+P\\s?OST[\\s-]*O\\s?FFICE'],
      first='Congress, February 1792: the post-office act.',
      what='the act establishing the post-office and post-roads',
      printings=[k('NG', '02-27', 1), k('GUS', '03-03', 1), k('NHGZ', '03-21', 1), k('NHG', '03-21', 1)]),
 dict(id='act-for-the-protection-of-the-frontiers-1792', kind='document_group',
      label='Congress, March 1792: an act for making farther and more effectual provision for the protection of the frontiers of the United States',
      definition="Printings of 'An Act for making farther and more effectual Provision for the Protection of the Frontiers of the United States', of the first session of the Second Congress: 'Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled', the battalions to be raised and their officers. Congress's own act.",
      role='published_document', words=55, dateline=False,
      core=['A\\s?N\\s+A\\s?CT\\s+for\\s+making\\s+f[au]rther\\s+and\\s+more\\s+effectual\\s+provision\\s+for\\s+the\\s+protection\\s+of\\s+the\\s+frontiers'],
      first='Congress, March 1792: the act for the protection of the frontiers.',
      what='the act for the protection of the frontiers',
      printings=[k('NG', '03-08', 3), k('GUS', '03-14', 1), k('PG', '04-03', 2), k('NHGZ', '04-04', 1), k('KG', '04-14', 2, 2)]),
 dict(id='the-president-message-the-king-of-france-letter-accepting-the-constitution-march-1792', kind='document_group',
      label="The President to both Houses, 5 March 1792: the King of France's letter announcing his acceptance of the constitution",
      definition="Printings of the President's message to both Houses of 5 March 1792: 'Knowing the friendly interest you take in whatever may promote the happiness and prosperity of the French nation, it is with pleasure that I lay before you the translation of a letter which I have received from his most Christian Majesty, announcing to the United States of America, his acceptance of the constitution presented to him by his nation'; the translation of the King's letter of 19 September 1791 follows. The President's own message, with the King's letter.",
      role='published_document', words=50, dateline=False,
      head='(?:U\\s?NITED\\s+S\\s?TATES,?\\s+March\\s+5(?:th)?[.,]?\\s+1792\\.?\\s*)?G\\s?ENTLEMEN\\s+of\\s+the\\s+S\\s?ENATE,?\\s+and\\s+(?:of\\s+the\\s+)?H\\s?OUSE\\s+of\\s+R\\s?EPRESENTATIVES[,.:]?\\s*',
      core=['Knowing\\s+the\\s+friendly\\s+interest\\s+you\\s+take'],
      first="The President, 5 March 1792: the King of France's letter.",
      what="the President's message with the King of France's letter",
      printings=[k('NG', '03-08', 2), k('GUS', '03-10', 3), k('NHG', '03-21', 3), k('NHGZ', '04-04', 1), k('KG', '04-21', 2, 2)]),
 dict(id='philadelphia-paragraph-loan-of-three-millions-of-guilders-at-amsterdam-1792', kind='message_group',
      label='Philadelphia, 29 March 1792: a loan of three millions of guilders for the United States effected at Amsterdam at four per cent',
      definition="Printings of a Philadelphia paragraph of 29 March 1792: 'We have authority to assure the public that a loan of three millions of guilders for account of the United States, has been effected at four per cent interest, in the city of Amsterdam.' A news paragraph, 'by authority'.",
      role='report', words=24, dateline=False,
      core=['(?:We\\s+have\\s+authority\\s+to\\s+assure\\s+the\\s+public,?\\s+that\\s+a|We\\s+hear,?\\s+(?:that\\s+)?a|A)\\s+loan\\s+of\\s+three\\s+millions\\s+of\\s+guilders'],
      first='Philadelphia, March 1792: a loan at Amsterdam.',
      what='the Philadelphia paragraph on the Amsterdam loan',
      printings=[k('NG', '03-29', 3), k('GUS', '03-31', 3), k('PG', '04-03', 3), k('NHG', '04-11', 2), k('NHGZ', '04-11', 3),
                 k('KG', '05-26', 2, 2)]),
 dict(id='the-president-returns-the-apportionment-act-with-his-objections-april-1792', kind='document_group',
      label='The President to the House, 5 April 1792: he returns the act for an apportionment of representatives with his objections',
      definition="Printings of the President's message to the House of Representatives of 5 April 1792: 'I have maturely considered the act passed by the two Houses, entitled an act for an apportionment of representatives among the several states, according to the first enumeration—and I return it to your House, wherein it originated, with the following objections'; two objections follow, the first that no proportion or divisor applied to the states' numbers will yield the bill's allotment. The President's own message.",
      role='published_document', words=50, dateline=False,
      head='(?:U\\s?NITED\\s+S\\s?TATES,?\\s+April\\s+5(?:th)?[.,]?\\s+1792\\.?\\s*)?G\\s?ENTLEMEN\\s+of\\s+the\\s+H\\s?OUSE\\s+of\\s+R\\s?EPRESENTATIVES[,.:]?\\s*',
      core=['I\\s+have\\s+maturely\\s+considered\\s+the\\s+act'],
      first='The President, 5 April 1792: the apportionment act returned.',
      what="the President's objections to the apportionment act",
      printings=[k('GUS', '04-07', 3), k('NG', '04-09', 2), k('NHG', '04-25', 3), k('NHGZ', '04-25', 3), k('KG', '05-26', 3, 2)]),
 dict(id='act-establishing-a-mint-and-regulating-the-coins-1792', kind='document_group',
      label='Congress, April 1792: an act establishing a mint, and regulating the coins of the United States',
      definition="Printings of 'An Act establishing a Mint, and regulating the Coins of the United States', of the first session of the Second Congress (the New Hampshire Gazetteer's title reads 'to establish a Mint, and regulate the Coins'): 'Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled', the mint, its officers, and the gold, silver and copper coins. Congress's own act.",
      role='published_document', words=55, dateline=False,
      core=['A\\s?N\\s+A\\s?CT\\s+(?:establishing|to\\s+establish)\\s+a\\s+M\\s?INT'],
      first='Congress, April 1792: the mint act.',
      what='the act establishing a mint',
      printings=[k('NG', '04-12', 1), k('GUS', '04-14', 1), k('NHGZ', '05-02', 1), k('KG', '05-26', 1, 2)]),
 dict(id='charleston-letter-from-the-rock-landing-mr-bowles-seized-by-the-spaniards-1792', kind='message_group',
      label='Charleston, April 1792: a letter from the Rock Landing reports that the Spaniards seized Mr. Bowles and carried him to St. Augustine',
      definition="Printings of a Charleston paragraph of 18 April 1792: 'By a letter received in town from the Rock Landing, we are informed that on information of Mr. Bowles's having taken possession of the store of Messrs. Panton, Leslie, and Co. the Indians had dispatched a party to put him to death, but were prevented by the Spaniards'; the Spaniards drew him on board a vessel, 'seized him and immediately made sail for St. Augustine'. Some papers print it as 'A Charleston paper mentions, that' (C-02). A report from a letter.",
      role='report', words=50, dateline=False,
      core=['By\\s+a\\s+letter\\s+received\\s+in\\s+town\\s+from\\s+the\\s+Rock\\s+Landing', 'on\\s+information\\s+of\\s+Mr\\.?\\s+Bowles'],
      first='Charleston, April 1792: Mr. Bowles seized by the Spaniards.',
      what='the Charleston paragraph on Mr. Bowles',
      printings=[k('GUS', '04-28', 3), k('NG', '04-30', 3), k('NHGZ', '05-09', 3), k('NHG', '05-10', 2), k('KG', '05-26', 3, 2)]),
 dict(id='act-more-effectually-to-provide-for-the-national-defence-by-an-uniform-militia-1792', kind='document_group',
      label='Congress, May 1792: an act more effectually to provide for the national defence, by establishing an uniform militia throughout the United States',
      definition="Printings of 'An Act more effectually to provide for the National Defence, by establishing an Uniform Militia throughout the United States', of the first session of the Second Congress: 'Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled', who shall be enrolled in the militia, and their arms and officers. Congress's own act.",
      role='published_document', words=55, dateline=False,
      core=['A\\s?N\\s+A\\s?CT\\s+more\\s+effectually\\s+to\\s+provide\\s+for\\s+the\\s+N\\s?ATIONAL\\s+D\\s?EFENCE'],
      first='Congress, May 1792: the militia act.',
      what='the militia act',
      printings=[k('GUS', '05-16', 1), k('NG', '05-28', 1), k('PG', '06-12', 1), k('NHGZ', '06-20', 1)]),
 dict(id='paragraph-the-prince-royal-of-denmark-abolishes-the-slave-trade-after-1803-1792', kind='message_group',
      label='Spring 1792: the Prince Royal of Denmark has published an arret by which the slave trade is to cease after 1803',
      definition="Printings of a news paragraph of spring 1792: 'The Prince Royal of Denmark has published an arret, by which the SLAVE-TRADE IS TO CEASE, and be forever ABOLISHED after 1803.' A news paragraph reporting a decree.",
      role='report', words=18, dateline=False,
      core=['The\\s+Prince\\s+Royal\\s+of\\s+Denmark\\s+has\\s+published'],
      first='Denmark, 1792: the slave trade to cease after 1803.',
      what='the paragraph on the Danish arret',
      printings=[k('GUS', '05-19', 3), k('NG', '05-21', 3), k('NHG', '05-31', 2), k('PG', '06-12', 2)]),
 dict(id='petersburg-paragraph-alarming-accounts-of-an-insurrection-on-the-eastern-shore-1792', kind='message_group',
      label="Petersburg, 17 May 1792: the paper reports 'several alarming accounts' of an insurrection on the Eastern Shore of Virginia, its particulars not obtained",
      definition="Printings of a Petersburg paragraph of 17 May 1792 (the Kentucky Gazette dates it Richmond, 5 May): 'Several alarming accounts have been received in this town, of a very dangerous insurrection among the negroes on the Eastern Shore of Virginia; the particulars of which we have not been able to obtain'; what 'Reports state' follows. A paper's report of the accounts and reports it had received.",
      role='report', words=40, dateline=False,
      core=['Several\\s+alarming\\s+accounts\\s+have\\s+been\\s+received'],
      first='Petersburg, May 1792: accounts of an insurrection.',
      what='the Petersburg paragraph',
      printings=[k('GUS', '05-26', 2), k('PG', '06-05', 3), k('NHG', '06-07', 2), k('NHGZ', '06-13', 2), (k('KG', '07-14', 3, 2), {'note': "Dated 'RICHMOND, May 5' (C-02)."})]),
 dict(id='baltimore-report-brigantine-greyhound-from-cape-francois-1792', kind='message_group',
      label='Baltimore, June 1792: by the brigantine Greyhound from Cape-Francois, affairs in Hispaniola wore every day a more melancholy aspect',
      definition="Printings of a Baltimore paragraph of early June 1792: 'By the brigantine Greyhound, Captain Elias Porter, who arrived here in thirteen days from Cape-Francois, we are informed, that the situation of affairs, respecting the disturbances in Hispaniola, wore every day a more melancholy aspect—that all hopes of peace being restored, were relinquished'. The Potowmac Guardian prints it under Boston, 16 June, as 'The last accounts from Cape Francois state' (C-02). A report of a ship's news.",
      role='report', words=50, dateline=False,
      core=['By\\s+the\\s+[Bb]rigantine\\s+Greyhound', 'The\\s+last\\s+accounts\\s+from\\s+Cape[\\s-]*Francois\\s+state'],
      first='Baltimore, June 1792: news from Cape-Francois.',
      what='the Baltimore report from Cape-Francois',
      printings=[k('NG', '06-07', 3), k('GUS', '06-09', 3), k('NHGZ', '06-20', 3), k('NHG', '06-21', 2), (k('PG', '07-10', 2), {'note': "Printed under Boston, 16 June, as 'The last accounts from Cape Francois state' (C-02)."})]),
 dict(id='decree-of-the-national-assembly-declaring-war-against-the-king-of-hungary-and-bohemia-april-1792', kind='document_group',
      label='The National Assembly of France, 20 April 1792: decree declaring war against the King of Hungary and Bohemia',
      definition="Printings of the decree of the National Assembly of France of Friday 20 April 1792, 'declaring war against the King of Hungary and Bohemia': 'The National Assembly deliberating on the formal proposition of the King, considering that the Court of Vienna, in contempt of treaties, has continued to grant an open protection to French rebels'; the considerations and the decree follow. The Assembly's own decree, in translation.",
      role='published_document', words=50, dateline=False,
      head='D\\s?ECREE\\s+(?:of\\s+the\\s+N\\s?ATIONAL\\s+A\\s?SSEMBLY(?:\\s+of\\s+F\\s?RANCE)?,?\\s+)?declaring\\s+W\\s?AR\\s+against\\s+the\\s+K\\s?ING\\s+of\\s+H\\s?UNGARY\\s+and\\s+B\\s?OHEMIA\\.?\\s*(?:Friday,?\\s+April\\s+20\\.?\\s*)?',
      core=['The\\s+National\\s+Assembly\\s+deliberating\\s+on\\s+the\\s+formal\\s+proposition'],
      first='France, 20 April 1792: war declared on the King of Hungary.',
      what="the National Assembly's decree of war",
      printings=[k('GUS', '06-20', 2), k('NG', '06-21', 2), k('NHG', '06-28', 2), k('PG', '07-03', 2)]),
 dict(id='philadelphia-paragraph-the-constitution-of-kentucky-ratified-1792', kind='message_group',
      label='Philadelphia, June 1792: the Constitution of Kentucky ratified by the Convention at Danville; Isaac Shelby elected Governor',
      definition="Printings of a Philadelphia paragraph of 27 June 1792: 'The Constitution of Kentucky was finally ratified by the Convention of Danville, on the 26th day of April last. The first Legislature was to meet at Lexington, on the 4th instant. Isaac Shelby, Esq. is elected Governor.' A news paragraph.",
      role='report', words=35, dateline=False,
      core=['The\\s+Constitution\\s+of\\s+Kentucky\\s+was\\s+finally\\s+ratified'],
      first='Kentucky, 1792: its constitution ratified.',
      what='the paragraph on the Constitution of Kentucky',
      printings=[k('GUS', '06-27', 3), k('NG', '06-28', 3), k('NHG', '07-05', 3), k('PG', '07-10', 3)]),
 dict(id='albany-gazette-deputation-of-the-five-nations-to-the-miami-village-1792', kind='message_group',
      label='The Albany Gazette, July 1792: a deputation from the chiefs of the Five Nations on its way to the Miami village, where the hostile Indians are to hold a treaty',
      definition="Printings of a report of the Albany Gazette of July 1792: 'a deputation from the Chiefs of the Five Nations, are on their way to the Miami Village, where a treaty is shortly to be held by the hostile Indians. This deputation is sent under the direction of the Superintendant of Indian Affairs, and charged with a message from the Executive of the United States to the said Indians, demanding a cessation of hostilities'. The papers introduce it in their own words ('The Albany Gazette says, that'; 'A gentleman of respectability from the Genesee country informs, that'); the excerpt starts at the words they share (C-02). A report at second hand.",
      role='report', words=50, dateline=False,
      core=['A\\s+gentleman\\s+of\\s+respectability\\s+from\\s+the\\s+Genesee', 'a\\s+deputation\\s+from\\s+the\\s+(?:Chiefs\\s+of\\s+the\\s+)?Five\\s+Nations'],
      first='Albany, July 1792: a deputation of the Five Nations.',
      what="the Albany report of the Five Nations' deputation",
      printings=[k('GUS', '07-18', 3), k('NG', '07-21', 2), (k('NHGZ', '07-27', 3), {'note': "Printed under Albany, 9 July, as the report of 'A gentleman of respectability from the Genesee country' (C-02)."}),
                 (k('PG', '08-07', 1), {'note': "Printed as an addition to the paper's previous paragraph: 'The above gentlemen add, that a deputation from the Five Nations' (C-02)."})]),
 dict(id='general-advertiser-report-la-fayette-army-takes-the-citadel-of-namur-1792', kind='message_group',
      label='Philadelphia, August 1792, from the General Advertiser: by a courier at Havre, news that the army of M. la Fayette had taken the citadel of Namur',
      definition="Printings of a report of the General Advertiser of Philadelphia, 14 August 1792: 'By a courier arrived at Havre-de-Grace, just as an American vessel was about to sail for New-York, and which had but 27 days passage, the intelligence was received, that the army of M. la Fayette had taken the citadel of Namur'. A report at second hand, of news brought by a courier.",
      role='report', words=50, dateline=False,
      core=['By\\s+a\\s+courier\\s+arrived\\s+at\\s+Havre'],
      first='Philadelphia, August 1792: news of Namur by way of Havre.',
      what="the General Advertiser's report from Havre",
      printings=[k('GUS', '08-15', 3), k('NG', '08-15', 3), k('NHG', '08-23', 3), k('PG', '08-27', 2), k('NHGZ', '08-31', 3)]),
 dict(id='boston-letter-from-macao-captain-kendrick-attacked-on-the-coast-1792', kind='message_group',
      label='Boston, August 1792: a letter from Macao of December 1791 reports that Captain Kendrick had his vessel attacked on the coast',
      definition="Printings of a Boston paragraph of late August 1792: an extract of a letter dated Macao, December 1791, to a gentleman in Boston: 'Captain Kendrick had his vessel attacked on the coast'. A merchant's letter printed at second hand.",
      role='report', words=50, dateline=False,
      core=['E\\s?xtract\\s+of\\s+a\\s+letter,?\\s+dated\\s+Macao'],
      first="Macao, December 1791: Captain Kendrick's vessel attacked.",
      what='the letter from Macao',
      printings=[k('GUS', '09-05', 3), k('NG', '09-05', 2), k('NHG', '09-06', 3), k('NHGZ', '09-14', 2)]),
 dict(id='paris-the-assembly-sends-a-deputation-to-the-funeral-of-paul-jones-1792', kind='message_group',
      label='Paris, July 1792: the National Assembly sends a deputation to the funeral of the celebrated American Paul Jones',
      definition="Printings of a Paris paragraph of 19 July 1792: 'The Assembly sent a deputation to attend the funeral of the celebrated American PAUL JONES, who died yesterday at Paris. It was objected, that he was a Calvinist, but the objection was overruled.' The New-Hampshire Gazette and the New Hampshire Gazetteer print it among deaths: 'In Paris, July 18, the celebrated American JOHN PAUL JONES. The Assembly sent a deputation to attend his funeral' (C-02). A news paragraph from the Assembly's proceedings.",
      role='report', words=30, dateline=False,
      head='(?:—\\s*)?In\\s+Paris,?\\s+July\\s+18,?\\s+the\\s+celebrated\\s+American\\s+JOHN\\s+PAUL\\s+JONES\\.?\\s*',
      core=['The\\s+Assembly\\s+sent\\s+a\\s+deputation\\s+to\\s+attend\\s+(?:the|his)\\s+funeral'],
      first='Paris, July 1792: the funeral of Paul Jones.',
      what="the Paris paragraph on Paul Jones's funeral",
      printings=[k('GUS', '09-15', 2), (k('NHG', '09-20', 3), {'note': "Printed among deaths: 'In Paris, July 18, the celebrated American JOHN PAUL JONES' (C-02)."}),
                 (k('NHGZ', '09-21', 3), {'note': "Printed among deaths: 'In Paris, July 18, the celebrated American JOHN PAUL JONES' (C-02)."}),
                 k('PG', '09-24', 2)]),
 dict(id='the-president-proclamation-against-proceedings-obstructing-the-laws-on-distilled-spirits-september-1792', kind='document_group',
      label="The President's proclamation, September 1792: against the violent and unwarrantable proceedings that obstruct the laws on spirits distilled within the United States",
      definition="Printings of the President's proclamation of September 1792: 'Whereas certain violent and unwarrantable proceedings have lately taken place, tending to obstruct the operation of the laws of the United States for raising a revenue upon spirits distilled within the same'; he exhorts all persons to desist from such proceedings. The President's own proclamation. A proclamation printed again in later issues counts again (C-08).",
      role='published_document', words=55, dateline=False,
      head='B\\s?Y\\s+THE\\s+P\\s?R\\s?E\\s?S\\s?I\\s?D\\s?E\\s?N\\s?T\\s+of\\s+the\\s+U\\s?NITED\\s+S\\s?TATES[.,]?\\s*A\\s+P\\s?ROCLAMATION\\.?\\s*(?:\\(?\\s*L\\.?\\s?S\\.?\\s*\\)?\\s*)?',
      core=['W\\s?\\s?HEREAS\\s+certain\\s+violent\\s+and\\s+unwarrantable\\s+proceedings'],
      first='The President, September 1792: a proclamation on the excise.',
      what="the President's proclamation",
      printings=[k('GUS', '09-29', 4), k('NG', '09-29', 1), k('PG', '10-08', 3), (k('PG', '10-15', 1), {'note': 'Printed again (C-08).'}),
                 k('NHG', '10-18', 4), k('KG', '11-24', 3, 2), (k('KG', '12-01', 4, 2), {'note': 'Printed again (C-08).'}),
                 (k('KG', '12-15', 4, 2), {'note': 'Printed again (C-08).'}),
                 (k('KG', '12-22', 3, 2), {'note': 'Printed again (C-08).'}),
                 (k('KG', '12-29', 3, 2), {'note': 'Printed again (C-08).'})]),
 dict(id='decree-of-the-national-assembly-accusing-m-la-fayette-august-1792', kind='document_group',
      label='The National Assembly of France, August 1792: decree of accusation against M. La Fayette, heretofore commander of the army of the north',
      definition="Printings of the National Assembly's decree of August 1792 against M. La Fayette, which the papers print after an account of soldiers of his army at the bar of the Assembly: '1. It appears to this Assembly that there is just ground for accusation against M. de la Fayette, heretofore Commander of the army of the North. 2. The Executive Power shall in the most expeditious manner possible, put the present decree into execution'; all authorities, citizens and soldiers are enjoined to secure his person, and the army of the north is forbidden to obey him. The National Gazette gives the account before the decree in its own words (C-02). The Assembly's own decree, in translation.",
      role='published_document', words=45, dateline=False,
      head='D\\s?ECREE\\s+of\\s+[Aa]ccusation\\s+against\\s+M\\.?\\s+(?:de\\s+)?la\\s+F\\s?AYETTE[.:]?\\s*',
      core=['(?:[I1]\\.\\s+)?It\\s+appears\\s+to\\s+this\\s+[Aa]ssembly,?\\s+that\\s+there\\s+is\\s+just\\s+ground'],
      first='France, August 1792: La Fayette accused.',
      what="the National Assembly's decree against La Fayette",
      printings=[k('GUS', '10-13', 3), k('NG', '10-13', 3), k('NHGZ', '10-19', 2), k('PG', '10-22', 2), k('KG', '12-08', 2, 2)]),
 dict(id='paris-essay-comparative-statement-of-the-forces-of-the-concerting-kings-1792', kind='message_group',
      label='From an essay published at Paris, summer 1792: a comparative statement of the forces of the concerting kings, opposed to the numbers France may bring into the field',
      definition="Printings of a 'comparative statement of the forces of the concerting Kings, opposed to the numbers which France may bring into the field', 'extracted from an Essay on that subject, lately published at Paris, by an ingenious geographic writer': 'France contains twenty-seven millions of inhabitants'; the numbers of the powers follow. A writer's estimate, from a Paris essay.",
      role='report', words=50, dateline=False,
      core=['(?:This|The\\s+following)\\s+comparative\\s+s?tatement\\s+of\\s+the\\s+for\\s?ces'],
      first='Paris, 1792: the forces of the concerting kings.',
      what='the comparative statement of forces',
      printings=[k('NHGZ', '10-19', 3), k('PG', '10-22', 3), k('NHG', '10-25', 3), k('NG', '10-31', 4), k('MIR', '11-05', 1),
                 k('KG', '12-15', 3, 2)]),
 dict(id='knoxville-paragraph-the-governors-of-louisiana-and-pensacola-arm-the-creeks-and-cherokees-1792', kind='message_group',
      label="Knoxville, 10 October 1792: the Knoxville paper states as 'an undoubted truth' that the governors of Louisiana and Pensacola have opened the King of Spain's stores to the Creeks and Cherokees",
      definition="Printings of a paragraph of the Knoxville Gazette of 10 October 1792: 'It is an undoubted truth, (strange as it may appear)' that the governor of Louisiana and the governor of Pensacola 'have opened the stores of the King of Spain, in West Florida, to the Creeks and Cherokees, and delivered them arms and ammunition in abundance, advising and stimulating them to go to war against the frontier inhabitants of the United States'. Two papers print it without '(strange as it may appear)'. The Knoxville paper's allegation.",
      role='report', words=50, dateline=False,
      core=['I\\s?T\\s+is\\s+an\\s+undoubted\\s+truth'],
      first='Knoxville, October 1792: the Spanish governors and the Creeks and Cherokees.',
      what='the Knoxville paragraph on the Spanish governors',
      printings=[k('NG', '11-03', 2), k('PG', '11-12', 3), k('NHG', '11-21', 3), k('NHGZ', '11-21', 3), k('KG', '12-08', 2, 2)]),
 dict(id='the-president-speech-to-both-houses-of-congress-november-1792', kind='document_group',
      label="The President's speech to both Houses of Congress, 6 November 1792",
      definition="Printings of the President's speech to both Houses at the opening of the session, 6 November 1792: 'It is some abatement of the satisfaction, with which I meet you on the present occasion, that, in felicitating you on a continuance of the national prosperity generally, I am not able to add to it information that the Indian hostilities, which have for some time past distressed our North-Western frontier, have terminated'. The President's own speech.",
      role='published_document', words=55, dateline=False,
      head='Fellow[\\s-]*Citizens\\s+of\\s+the\\s+Senate,?\\s+(?:and\\s+of\\s+the\\s+House|and\\s+House)\\s+of\\s+Representatives[.,:]?\\s*',
      core=['I\\s?T\\s+is\\s+some\\s+abatement\\s+of\\s+the\\s+satisfaction'],
      first='The President, 6 November 1792: his speech to Congress.',
      what="the President's speech of 6 November",
      printings=[k('GUS', '11-07', 3), k('NG', '11-07', 3), k('PG', '11-19', 1), k('NHGZ', '11-28', 1), k('KG', '12-22', 1, 2)]),
 dict(id='dublin-letter-subscription-of-three-millions-sterling-1792', kind='message_group',
      label='Dublin, 13 September 1792: it is said that a subscription amounting to three millions sterling was made in the course of the last week',
      definition="Printings of an extract of a letter from Dublin, 13 September 1792: 'It is said that in the course of last week a subscription, amounting to three millions sterling'. Two papers print it under Dublin, 13 September, without the words 'Extract of a letter' (C-02). A report of what is said, from a letter.",
      role='report', words=50, dateline=False,
      core=['E\\s?xtract\\s+of\\s+a\\s+letter\\s+from\\s+Dublin', 'It\\s+is\\s+said,?\\s+that\\s+in\\s+the\\s+course\\s+of\\s+last\\s+week'],
      first='Dublin, September 1792: a subscription of three millions.',
      what='the Dublin letter on the subscription',
      printings=[k('GUS', '11-17', 1), k('NG', '11-17', 2), k('NHGZ', '11-28', 2), k('PG', '12-03', 1), k('MIR', '12-17', 2)]),
 dict(id='mr-seagrove-letter-to-the-citizens-of-georgia-on-the-creek-nation-october-1792', kind='document_group',
      label="Mr. Seagrove, agent of Indian affairs in the southern department, to the citizens of Georgia, St. Mary's, 4 October 1792: the chiefs of the Creek nation not unfriendly",
      definition="Printings of a letter of James Seagrove, agent of Indian affairs in the southern department, to the citizens of Georgia, from St. Mary's, 4 October 1792, as a Savannah paper gave it: 'It being (in my opinion) of some consequence to the citizens of Georgia to know the disposition of the Creek Indians towards them at this time, I have therefore taken this mode of assuring them, that, from the whole of my late communications, and the investigation of matters, I do not find any disposition in the chiefs of the Creek nation to be unfriendly to any part of the United States'; more mischief, he writes, is to be dreaded from the ill-disposed among ourselves. Mr. Seagrove's own letter. A Philadelphia paragraph that sums it up ('By the latest accounts from Georgia, received from Mr. Seagrove'), in three papers, is not counted (C-07).",
      role='published_document', words=55, dateline=False,
      head='(?:Letter\\s+from\\s+James\\s+Seagrove,?\\s+Esq\\.?\\s*\\(?agent\\s+of\\s+Indian\\s+affairs\\s+in\\s+the\\s+southern\\s+department\\s+of\\s+the\\s+United\\s+States\\)?\\s+to\\s+the\\s+citizens\\s+of\\s+the\\s+state\\s+of\\s+Georgia\\.?|St\\.?\\s+MARY.S,?\\s+4th\\s+Oct(?:ober|\\.)?,?\\s+1792\\.?\\s*["“]?\\s*G\\s?ENTLEMEN,?)\\s*["“]?\\s*',
      core=['I\\s?T\\s+being\\s+\\(?in\\s+my\\s+opinion\\)?\\s+of\\s+some\\s+consequence'],
      first='Mr. Seagrove, October 1792: the Creek nation.',
      what="Mr. Seagrove's letter to the citizens of Georgia",
      printings=[k('NG', '11-17', 3), k('MIR', '12-10', 4), k('NHG', '12-12', 2), k('NHGZ', '12-19', 2)]),
 dict(id='general-dumourier-letter-to-servan-the-prussians-in-full-retreat-october-1792', kind='document_group',
      label='General Dumourier to M. Servan, Saint Menehould, 1 October 1792: the Prussians are in full retreat',
      definition="Printings of General Dumourier's letter to M. Servan of 1 October 1792: 'At length, my dear Servan, what I expected and predicted in my letters has taken place. The Prussians are in full retreat.' The general's own letter, in translation.",
      role='published_document', words=50, dateline=False,
      head='L\\s?ETTER\\s+from\\s+General\\s+D\\w+[,.]?\\s*["“]?\\s*Sain\\w*\\s+M\\w+,?\\s+(?:October|Oct\\.?|O\\.\\s*T\\.|Oâ\\.?)\\s*(?:1\\.?)?\\s*["“]?\\s*',
      core=['At\\s+length,?\\s+my\\s+dear\\s+Serv'],
      first='Dumourier, 1 October 1792: the Prussians in retreat.',
      what="General Dumourier's letter to Servan",
      printings=[k('NHG', '12-12', 2), k('GUS', '12-15', 2), k('NG', '12-15', 3), k('NHGZ', '12-19', 2), k('PG', '12-24', 3),
                 k('MIR', '12-31', 4)]),
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
            problems.append((s['id'], key, 'page not in the 1792 pages'))
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
        r['id'] = f'S92-{n:03}'
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
               'admission_rule': 'Reviewed 1792 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1792/'
    return {
        'ledger_id': 'ledger:stories-1792', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1792', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1792, and of 1791 where they reach the 1792 pages (long-running ones '
                   'included), counts of every item in 3 or more papers by its own opening over all 1,629 pages of 1792 in both transcriptions, '
                   'a sweep of word-for-word passages shared by 4 or more papers for short items the families miss, reading of every item that '
                   'meets the bar, and scan checks of each admitted and chosen passage, by the thin-year rule as amended (register Y-THIN, B1: '
                   'more than half of the papers that survive for the item\'s weeks, and at least 4, make an item eligible; items printed by '
                   'every paper in print are admitted, the others chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1791.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1792.py': 'ledger_code', 'work/archive_data/ledgers/stories_1792_review.json': 'scan_review',
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
