"""Write ledgers/stories_1787.json: reviewed stories of 1787, round one.

1787 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN) as the owner amended it on 23 November 2026 (B1): an
item, counted by its own words, is eligible when it was printed by more than half of the newspapers that survive for its weeks,
and by at least 4 newspapers; digests are not. Items printed by every newspaper that survives for their weeks are admitted; the
other eligible items are chosen to cover the months and the kinds of news, about as many stories as a standard year (20 to 35, a
target, not a quota); one affair's items as in X-1800-01. Sub-stories (C-01), private persons (R-04) and the list of items read
and not admitted (R-03) apply as in every year.

The automatic families first printed in 1787 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1786 over the 1787 pages
(items_from_1786.json); every item in 3 or more papers was counted by its own opening over all 1,297 pages of 1787 in both
transcriptions and merged into text units, a sweep of passages shared word for word by 4 or more papers found short items the
families miss, and every unit that meets the bar was read (outputs/story_discovery_1787/README.md). 1787 has 10 catalogue series,
which are 7 papers: the New-Hampshire Gazette, the Daily Advertiser and the New-York Journal each stand under two catalogue
numbers, one after the other (C-04). 4 papers are in print from January to April, 3 in May and June, 4 or 5 in July and
August, and 6 from September; the bar is 4. Three issues are filed under another date (README, Data issues); their
printings carry notes.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 25-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1787_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1787.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1787/search_pages.json). The excerpts are cut from
the 1787 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1787'
D = PROJECT/'outputs/story_discovery_1787'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1787_review.json'
OUT = HERE/'stories_1787.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83030137': 'The New-York Packet', 'sn83030586': 'The Independent Journal', 'sn83030565': 'The New-York Journal',
         'sn83030566': 'The New-York Journal', 'sn83030006': 'The Daily Advertiser', 'sn83030007': 'The Daily Advertiser',
         'sn83025586': 'The New-Hampshire Gazette', 'sn83025587': 'The New-Hampshire Gazette', 'sn82014784': 'The Kentucke Gazette',
         'sn83021129': 'The Pennsylvania Packet, and Daily Advertiser'}
ONE = {'NYP': 'sn83030137', 'IJ': 'sn83030586', 'KG': 'sn82014784', 'PPDA': 'sn83021129'}
# C-04: three papers stand under two catalogue numbers, one after the other: (first date of the second number, first, second)
SWITCH = {'NHG': ('1787-06-05', 'sn83025586', 'sn83025587'), 'DA': ('1787-10-17', 'sn83030006', 'sn83030007'),
          'NYJ': ('1787-11-20', 'sn83030565', 'sn83030566')}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1787), page and edition; for a paper under two catalogue numbers, the
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
 dict(id='heads-of-the-treaty-with-the-emperor-of-morocco-1786', kind='document_group',
      label='The heads of the treaty of peace between the United States and the Emperor of Morocco, concluded in July 1786',
      definition="Printings of 'the Heads of the Treaty of Peace concluded betwixt the Americans and the Emperor of Morocco, July 24, 1786': 'If the Americans are at war with any other nation, their vessels are to be allowed to take refuge in any of the ports belonging to his Imperial Majesty'; the articles on prisoners, salutes, merchants and consuls follow. A summary of the treaty's articles as the papers printed it.",
      role='published_document', words=55, dateline=False,
      head='(?:The\\s+following\\s+are\\s+the\\s+)?H\\s?EADS\\s+of\\s+the\\s+T\\s?REATY\\s+of\\s+P\\s?EACE\\s+concluded\\s+(?:between|betwixt)\\s+the\\s+A\\s?MERICANS\\s+and\\s+the\\s+E\\s?MPEROR\\s+of\\s+M\\s?OROCCO,?\\s+July\\s+24,?\\s+1786\\.?\\s*',
      core=['I\\s?F\\s+the\\s+Americans\\s+are\\s+at\\s+war\\s+with\\s+any\\s+other\\s+nation'],
      first='The treaty with Morocco, July 1786: its heads.',
      what='the heads of the treaty with Morocco',
      printings=[k('NYP', '04-10', 2), k('IJ', '04-11', 2), k('NHG', '04-28', 1), (k('NYJ', '05-03', 1), {'note': "The paper prints it '[Omitted several Weeks for want of Room.]'"})]),
 dict(id='congress-recommends-the-states-repeal-laws-inconsistent-with-the-treaty-of-peace-april-1787', kind='message_group',
      label='New York, April 1787: Congress recommends that the States repeal their laws inconsistent with the treaty of peace',
      definition="Printings of a New York paragraph of April 1787: 'On Friday last the United States in Congress assembled passed a resolution recommending it to the different states, to repeal all their laws, now in force, which are inconsistent with the treaty of peace between the United States of America, and the King of Great Britain' (one paper dates it 'April 14' and reads 'Yesterday'). A news paragraph reporting Congress's resolution.",
      role='report', words=40, dateline=False,
      core=['(?:On\\s+Friday\\s+last|Yesterday)\\s+the\\s+United\\s+States\\s+in\\s+Congress\\s+assembled,?\\s+passed\\s+a\\s+resolution,?\\s+recommending'],
      first='Congress, April 1787: the States to repeal laws against the treaty.',
      what="the New York paragraph on Congress's resolution",
      printings=[k('NYJ', '04-19', 3), k('NYP', '04-20', 2), k('IJ', '04-21', 3), (k('NHG', '04-28', 3), {'note': "Dated 'April 14', with 'Yesterday' for 'On Friday last'."})]),
 dict(id='boston-report-british-ship-maria-on-lake-champlain-1787', kind='message_group',
      label='Boston, summer 1787: a gentleman from Lake Champlain reports that the British have fitted out the ship Maria, of 20 guns, to cruise on the lake',
      definition="Printings of a Boston paragraph of June and July 1787: 'We are informed, by a gentleman of this town, who left Lake Champlain the 18th ult. that the British have fitted out the ship Maria, of 20 guns, in order to cruise on that Lake; that she was three miles from the line, within our territories, when he came from thence; that she had taken one vessel (said to have been on the smuggling business) belonging to the United States'. A report at second hand.",
      role='report', words=50, dateline=False,
      core=['W\\s?E\\s+are\\s+informed,?\\s+(?:by\\s+a\\s+gentleman\\s+of\\s+(?:this\\s+town|Boston),?\\s+who\\s+left\\s+[Ll]ake|via\\s+Boston,?\\s+that\\s+the\\s+British)'],
      first='Boston, 1787: the British ship Maria on Lake Champlain.',
      what='the Boston report of the ship Maria',
      printings=[k('NHG', '07-07', 2), k('NYP', '07-10', 2), k('NYJ', '07-12', 3), (k('KG', '10-13', 2, 2), {'note': 'The Kentucke Gazette of 13 October 1787; the same page is filed again as page 4 of the issue of 6 October.'})]),
 dict(id='congress-12-july-1787-certificates-for-pensioned-officers', kind='document_group',
      label='Congress, 12 July 1787: officers of the late army entitled to pensions to deposit a certificate that no balance is due from them',
      definition="Printings of Congress's resolution of 12 July 1787: 'That all officers in the line of the late army who may be entitled to pensions, in pursuance of the acts of Congress in that behalf made, shall previous to the receipt of such pension, deposit with the proper officers appointed to discharge the same in the States in which they reside, a certificate from the Commissioner of Army Accounts, purporting that no balance is due from the claimant to the United States'. Congress's own resolution.",
      role='published_document', words=50, dateline=False,
      head='(?:By\\s+the\\s+U\\s?NITED\\s+S\\s?TATES\\s+in\\s+C\\s?ONGRES+\\s+[Aa]ssembled[,.]?\\s+|I\\s?N\\s+C\\s?ONGRESS,?\\s+)July\\s+12,?\\s+1787\\.?\\s*',
      core=['R\\s?ESOLVED,?\\s+[Tt]hat\\s+all\\s+officers\\s+in\\s+the\\s+line\\s+of\\s+the\\s+late\\s+army'],
      first='Congress, 12 July 1787: certificates for pensioned officers.',
      what="Congress's resolution of 12 July",
      printings=[k('NYP', '07-17', 2), k('IJ', '07-18', 3), k('NHG', '07-28', 2), k('NYJ', '08-02', 2)]),
 dict(id='ordinance-for-the-government-of-the-territory-north-west-of-the-river-ohio-1787', kind='document_group',
      label='Congress, 13 July 1787: an ordinance for the government of the territory of the United States north-west of the river Ohio',
      definition="Printings of 'An Ordinance for the Government of the Territory of the United States, North-West of the River Ohio': 'Be it ordained by the United States in Congress assembled, That the said territory, for the purposes of temporary government, be one district'; the governor, secretary and judges, the general assembly, and the articles of compact, among them that 'there shall be neither slavery nor involuntary servitude in the said territory' and that 'the utmost good faith shall always be observed towards the Indians'. Congress's own ordinance.",
      role='published_document', words=55, dateline=False,
      head='A\\s?N\\s+O\\s?RDINANCE\\s+(?:for|of)\\s+the\\s+G\\s?OVERNMENT\\s+of\\s+the\\s+T\\s?ERRITORY\\s+of\\s+the\\s+U\\s?NITED\\s+S\\s?TATES,?\\s+North[\\s-]*West\\s+of\\s+the\\s+R\\s?IVER\\s+O\\s?HIO\\.?\\s*',
      core=['B\\s?E\\s+(?:IT|it)\\s+(?:ORDAINED|ordained)\\s+by\\s+the\\s+United\\s+States\\s+in\\s+Congress\\s+assembled,?\\s+[Tt]hat\\s+the\\s+said\\s+territory'],
      first='Congress, July 1787: the ordinance for the territory north-west of the Ohio.',
      what='the ordinance for the north-west territory',
      printings=[k('IJ', '07-18', 2), k('NYP', '07-20', 2), k('NYJ', '07-26', 2), k('KG', '11-03', 1)]),
 dict(id='result-of-the-federal-convention-the-constitution-september-1787', kind='document_group',
      label="The result of the Federal Convention, September 1787: the Constitution, with the Convention's resolutions and General Washington's letter to the President of Congress",
      definition="Printings of the result of the deliberations of the Federal Convention at Philadelphia, 17 September 1787: the Constitution ('We, the People of the United States, in order to form a more perfect Union, establish Justice, insure domestic Tranquility, provide for the common Defence, promote the general Welfare, and secure the Blessings of Liberty to ourselves and our Posterity, do ordain and establish this Constitution for the United States of America'), the Convention's resolutions that it be laid before Congress and submitted to conventions chosen by the people, and the letter of General Washington, its President, to the President of Congress ('We have now the honor to submit to the consideration of the United States in Congress assembled, that Constitution which has appeared to us the most advisable'). Printed together, counted as one item by whichever part stands first (X-1810-01). The Convention's own acts and words.",
      role='published_document', words=55, dateline=False,
      head='(?:(?:Copy\\s+of\\s+the\\s+Result\\s+of\\s+the\\s+Deliberations\\s+of\\s+the\\s+F\\s?EDERAL\\s+C\\s?ONVENTION\\.?\\s*)?In\\s+Convention,?\\s+September\\s+17,?\\s+1787\\.?\\s*(?:["“]?\\s*S\\s?\\s?I\\s?\\s?R[,.]?\\s*["“]?\\s*)?|P\\s?ROCEEDINGS\\s+OF\\s+THE\\s+Grand\\s+Federal\\s+Convention\\.?\\s*)',
      core=['W\\s?E\\s+have\\s+now\\s+the\\s+honou?r\\s+to\\s+submit\\s+to\\s+the\\s+consideration', 'W\\s?\\s?E,?\\s+the\\s+P\\s?EOPLE\\s+of\\s+the\\s+U\\s?NITED\\s+S\\s?TATES,?\\s+in\\s+order\\s+to\\s+form'],
      first='The Federal Convention, 17 September 1787: the Constitution.',
      what='the result of the Federal Convention',
      printings=[(k('IJ', '09-12', 5), {'note': "Printed in the Supplement to the Independent Journal of Saturday 22 September 1787, as its heading on this page reads; the archive files the supplement with the issue of 12 September (pages 5 to 8). The supplement prints General Washington's letter before the Constitution."}),
                 (k('PPDA', '09-19', 1), {'note': 'The Pennsylvania Packet, and Daily Advertiser of 19 September 1787, the one issue of that paper in the collection.'}),
                 k('NYP', '09-21', 2), k('NHG', '10-06', 1), k('KG', '10-20', 2)]),
 dict(id='wilmington-report-general-washington-at-the-bridge-near-the-head-of-elk-1787', kind='message_group',
      label='Wilmington, September 1787: General Washington, returning to Mount Vernon, alights to walk over the bridge near the Head of Elk, which gives way',
      definition="Printings of a paragraph from the Wilmington Gazette, late September 1787: 'his Excellency General Washington passed through Wilmington, on his return from Philadelphia to his seat in Mount Vernon, and on the same day, in crossing the bridge near the Head of Elk, the bridge gave way and his horse fell into the river. His Excellency had alighted in order to walk over the bridge, which fortunate circumstance probably saved a life so dear to his country'. A report from a paper, at second hand.",
      role='report', words=50, dateline=False,
      core=['On\\s+Wednesday\\s+(?:the\\s+26th\\s+ult\\.?|last|sen.?n?ight),?\\s+his\\s+Excellency\\s+Gen(?:eral|\\.)\\s+Washington\\s+passed\\s+through\\s+Wilmington'],
      first='Wilmington, September 1787: General Washington at the Head of Elk.',
      what='the Wilmington paragraph on General Washington',
      printings=[(k('NYP', '10-02', 6), {'note': 'Printed in the New-York Packet of Friday 5 October 1787 (No. 738, its masthead on page 5); the archive files that issue with the issue of 2 October (pages 5 to 8).'}),
                 k('DA', '10-05', 2), k('IJ', '10-06', 2), k('NHG', '10-13', 3)]),
 dict(id='cape-francois-letter-passes-required-for-american-vessels-in-french-west-indies-1787', kind='message_group',
      label='Cape Francois, September 1787: by an ordinance, no American vessel may enter a French port in the West Indies without a pass from the consul',
      definition="Printings of an extract of a letter from an American house in Cape Francois, Hispaniola, of 4 September 1787, to a gentleman in Boston: 'We are informed by an Ordinance of this day, that NO American vessel (except in distress) will be permitted to enter any French ports in the West-Indies, unless the Captain is provided with a Pass from the Consul resident at the place of his departure'. A merchants' letter reporting a French ordinance.",
      role='report', words=50, dateline=False,
      core=['E\\s?xtract\\s+of\\s+a\\s+letter\\s+from\\s+an\\s+American\\s+[Hh]ouse\\s+in\\s+Cape'],
      first='Cape Francois, September 1787: passes for American vessels.',
      what='the Cape Francois letter',
      printings=[k('NHG', '10-06', 3), k('DA', '10-06', 2), k('IJ', '10-06', 2), k('NYP', '10-09', 2)]),
 dict(id='congress-requisition-for-1787-11-october-1787', kind='document_group',
      label='Congress, 11 October 1787: the requisition for 1787',
      definition="Printings of Congress's resolutions of 11 October 1787 on a report of the Board of Treasury and a motion of Mr. Kean 'respecting the requisition for 1787': the sums wanting for the year's interest on the foreign and domestic debt, the quotas of the states, and the indents of interest to be received in payment. Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      head='By\\s+the\\s+U\\s?NITED\\s+S\\s?TATES\\s+in\\s+C\\s?ONGRESS\\s+assembled[,.]?\\s+O\\s?CTOBER\\s+11,?\\s+1787\\.?\\s*',
      core=['T\\s?HE\\s+[Cc]ommittee,?\\s+to\\s+whom\\s+was\\s+referred\\s+a\\s+report\\s+of\\s+the\\s+[Bb]oard\\s+of\\s+[Tt]reasury'],
      first='Congress, 11 October 1787: the requisition.',
      what="Congress's requisition of 11 October",
      printings=[k('DA', '10-16', 2), k('IJ', '10-17', 2), (k('NYJ', '10-18', 2, 2), {'note': 'Printed in the New-York Journal Extraordinary of 18 October 1787 (filed as edition 2 of that date).'}),
                 k('NYP', '10-19', 2)]),
 dict(id='congress-appoints-judges-in-the-western-territory-october-1787', kind='message_group',
      label='New York, October 1787: Congress appoints Samuel Holden Parsons, John Armstrong and James M. Varnum judges in the western territory',
      definition="Printings of a paragraph of October 1787: 'Congress yesterday appointed the Hon. Samuel Holden Parsons, John Armstrong, jun. and James M. Varnum, Esqrs. to be Judges in the Western Territory of the United States' (the time words change with each paper's date). A news paragraph reporting Congress's appointments.",
      role='report', words=25, dateline=False,
      core=['(?:Congress\\s+(?:yesterday|on\\s+Tuesday\\s+last),?\\s+appointed|Tuesday\\s+last,?\\s+Congress\\s+appointed|On\\s+the\\s+16th\\s+instant,?\\s+Congress\\s+appointed|Congress\\s+we\\s+hear,?\\s+have\\s+appointed)\\s+the\\s+[Hh]on'],
      first='Congress, 16 October 1787: judges for the western territory.',
      what='the paragraph on the judges of the western territory',
      printings=[k('DA', '10-17', 2), k('NYJ', '10-18', 3), k('NYP', '10-19', 2), k('NHG', '10-27', 3), (k('NHG', '11-09', 3), {'note': "Printed again, in the paper's own words under Portsmouth, 9 November ('Congress we hear, have appointed')."})]),
 dict(id='london-letter-on-virginia-additional-duty-on-british-ships-1787', kind='message_group',
      label="London, 17 July 1787: an American gentleman's letter calls Virginia's additional duty on British ships a wise measure",
      definition="Printings of an extract of a letter from an American gentleman in London, 17 July 1787, to his correspondent in Richmond: 'The additional duty on British ships, &c. laid by the last General Assembly of Virginia, is in my opinion, a wise measure, but would be much more so, if it was general throughout the United States. It has raised the value of American ships here'. A private letter printed at second hand, its writer's opinion.",
      role='report', words=50, dateline=False,
      core=['(?:E\\s?xtract\\s+of\\s+)?[Aa]\\s+letter\\s+from\\s+an\\s+American\\s+gentleman\\s+in\\s+London'],
      first="London, July 1787: a letter on Virginia's duty on British ships.",
      what="the London letter on Virginia's duty",
      printings=[k('DA', '11-08', 2), k('NYJ', '11-08', 3), k('NYP', '11-09', 2), k('NHG', '11-28', 2)]),
 dict(id='philadelphia-report-ship-caractacus-taken-by-an-algerine-corsair-1787', kind='message_group',
      label='Philadelphia, November 1787: the ship Caractacus, from Charleston for France, taken by an Algerine corsair under Spanish colours',
      definition="Printings of a Philadelphia paragraph of November 1787: 'The Caractacus, Sewall, from Charleston, South-Carolina, bound for France, laden with rice, chiefly, and some indigo, was captured within 30 leagues of her destination, by a stout bark, mounting 22 guns, under Spanish colours, which proved an Algerine corsair' (the New-York Packet and the New-Hampshire Gazette print the ship's name 'Ceractacus', and the New-Hampshire Gazette 'twenty leagues'); after rummaging the vessel they let her proceed. A report of a ship's news.",
      role='report', words=50, dateline=False,
      core=['The\\s+C\\w{2,9}us,?\\s+Se\\w+,?\\s+from\\s+(?:Charleston|Carolina|South)'],
      first='Philadelphia, November 1787: the Caractacus and the Algerine corsair.',
      what='the Philadelphia paragraph on the Caractacus',
      printings=[k('DA', '11-08', 2), k('NYP', '11-09', 3), k('IJ', '11-10', 2), k('NHG', '11-28', 2)]),
 dict(id='mr-jay-letter-denying-sentiments-against-the-constitution-december-1787', kind='document_group',
      label="Mr. Jay's letter of 1 December 1787, from the Independent Gazetteer: he authorises the denial of sentiments imputed to him against the proposed Constitution",
      definition="Printings of a letter of John Jay, New York, 1 December 1787, sent to the Independent Gazetteer of Philadelphia by the man he wrote to: 'I thank you for your obliging letter of the 24th ult. enclosing a paragraph respecting me in Mr. Oswald's paper of the same date'; he authorises its denial, 'and to declare, that, in my opinion, it is advisable for the people of America to adopt the Constitution proposed by the late Convention'. A letter and the note that sends it are counted as one item (X-1810-01). Mr. Jay's own letter.",
      role='published_document', words=50, dateline=False,
      core=['(?:M\\s?R\\.?\\s+O\\s?SWALD,?\\s+)?I\\s+S\\s?END\\s+you\\s+an\\s+extract\\s+of\\s+a\\s+letter\\s+I\\s+have\\s+received\\s+from\\s+Mr\\.?\\s+Jay', 'E\\s?xtract\\s+of\\s+a\\s+letter\\s+from\\s+Mr\\.?\\s+Jay,?\\s+dated\\s+New[\\s-]*York'],
      first='Mr. Jay, 1 December 1787: his letter on the Constitution.',
      what="Mr. Jay's letter",
      printings=[k('DA', '12-13', 2), k('NYP', '12-14', 3), k('IJ', '12-15', 2), (k('NHG', '12-26', 3), {'note': 'Printed without the note that sends the letter to the printer.'})]),
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
            problems.append((s['id'], key, 'page not in the 1787 pages'))
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
        r['id'] = f'S87-{n:03}'
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
               'admission_rule': 'Reviewed 1787 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1787/'
    return {
        'ledger_id': 'ledger:stories-1787', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1787', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1787, and of 1786 where they reach the 1787 pages (long-running ones '
                   'included), counts of every item in 3 or more papers by its own opening over all 1,297 pages of 1787 in both transcriptions, '
                   'a sweep of word-for-word passages shared by 4 or more papers for short items the families miss, reading of every item that '
                   'meets the bar, and scan checks of each admitted and chosen passage, by the thin-year rule as amended (register Y-THIN, B1: '
                   'more than half of the papers that survive for the item\'s weeks, and at least 4, make an item eligible; items printed by '
                   'every paper in print are admitted, the others chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1786.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1787.py': 'ledger_code', 'work/archive_data/ledgers/stories_1787_review.json': 'scan_review',
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
