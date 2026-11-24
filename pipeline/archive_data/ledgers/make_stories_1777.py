"""Write ledgers/stories_1777.json: reviewed stories of 1777, round one.

1777 is read by the thin-year rule the owner chose on 23 November 2026 (docs/rules-and-exceptions.md, Y-THIN): an item, counted
by its own words, is admitted when it was printed by more than half of the newspapers that survive for its weeks, and by at least
4 newspapers; digests are not. The newspapers that survive for an item's weeks are those with a surviving issue between its first
and last printing, and at least in the three weeks from its first printing. One affair's items are handled as in X-1800-01;
sub-stories (C-01), private persons (R-04) and the list of items read and not admitted (R-03) apply as in every year. 91 items
met the bar in the count of 23 November, more than the rule's 60, and the owner asked that all of them be read
(outputs/story_discovery_1777/README.md).

The automatic families first printed in 1777 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1776 over the 1777 pages
(items_from_1776.json); every item in 3 or more papers was compared by machine with every page, a sweep of passages shared word for
word by 4 or more papers found short items the families miss, every candidate was counted by its own opening over all 1,320 pages
of 1777 in both transcriptions, and every story and every candidate set aside was searched with phrase searches
(work/story_phrase_search.py). The 1777 pages are those whose issue the data release dates to 1777 (work/year_search_pages.py
1777 ... --printed-dates); no 1777 issue has a corrected date. 1777 has 11 catalogue series, which are 10 papers: Dunlap's
Pennsylvania Packet (Philadelphia, to 9 September) and The Pennsylvania Packet (Lancaster, from 29 November) are one paper under
two catalogue numbers (C-04). The release's map of misfiled RevX pages (derived/revx_page_map.parquet) lists two 1777 pages
(the Freeman's Journal of 8 March, pages 2 and 3); a printing on such a page takes its excerpt from the CA transcription.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 25-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1777_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1777.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1777/search_pages.json). The excerpts are cut from
the 1777 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1777'
D = PROJECT/'outputs/story_discovery_1777'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1777_review.json'
OUT = HERE/'stories_1777.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn82016139': 'The Connecticut Courant', 'sn83021126': "Dunlap's Pennsylvania Packet", 'sn83021127': 'The Pennsylvania Packet',
         'sn83021183': 'The Newport Gazette', 'sn83025471': 'The New-Jersey Gazette', 'sn83025583': "The Freeman's Journal",
         'sn83025790': 'The South-Carolina and American General Gazette', 'sn83030493': 'The New-York Gazette',
         'sn84024739': 'The Virginia Gazette (Dixon and Hunter)', 'sn84024742': 'The Virginia Gazette (Purdie)',
         'sn84026945': 'The Gazette of the State of South-Carolina'}
ONE = {'CC': 'sn82016139', 'NPT': 'sn83021183', 'NJG': 'sn83025471', 'FJ': 'sn83025583', 'SCG': 'sn83025790', 'NYG': 'sn83030493',
       'VDH': 'sn84024739', 'VP': 'sn84024742', 'GSC': 'sn84026945'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1777), page and edition. The Pennsylvania Packet has two catalogue
    numbers in 1777 (C-04); the date picks it."""
    if paper == 'PP':
        lccn = 'sn83021126' if date < '10-01' else 'sn83021127'
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

S = r'\s+'
# Story groups. A parent ('context_group') lists its children and has no printings. 'printings' lists each printing's page;
# a tuple adds overrides for that printing: core (regexes for the item's first words), role, field, note, words, dateline
# (include a dateline directly before), head (a regex for a heading that ends directly before the core: the excerpt starts
# with it), back (start at the beginning of the sentence that holds the core), stop (a regex: the excerpt ends before it).
STORIES = [
 dict(id='american-crisis-number-one-1777', kind='document_group',
      label="The American Crisis, Number I, by the author of Common Sense: 'These are the times that try men's souls'",
      definition="Printings of the first number of The American Crisis, 'by the author of Common Sense' (Thomas Paine), printed in January 1777: 'These are the times that try men's souls: The summer soldier and the sunshine patriot will, in this crisis, shrink from the service of his country; but he that stands it now, deserves the love and thanks of man and woman. Tyranny, like hell, is not easily conquered'. Only printings dated 1777 are counted (C-11); Dunlap's Packet of 4 January prints its later part, whose opening stood in an issue of 1776 (C-06). The writer's own argument.",
      role='published_document', words=55, dateline=False,
      head=r"T\s?HE\s+A\s?MERICAN\s+C\s?RISIS\.?\s*(?:N\s?UMBER|N\s?o\.?)\s+I\.?\s+B\s?Y\s+the\s+A\s?UTHOR\s+of\s+C\s?OMMON\s+S\s?ENSE\.?\s*",
      core=['T\\s?\\s?H\\s?ESE\\s+are\\s+the\\s+times\\s+that\\s+try\\s+men'],
      first="The American Crisis, Number I, by the author of Common Sense: 'These are the times that try men's souls.'",
      what='The American Crisis, Number I',
      printings=[k('CC', '01-06', 2), k('VDH', '01-10', 1), k('VP', '01-10', 1), k('FJ', '01-28', 2)]),
 dict(id='new-london-report-hessian-troops-recalled-january-1777', kind='message_group',
      label='New London, 24 January 1777: Captain Phips heard a letter read by a Hessian officer at Newport, that the Hessian troops were to be recalled',
      definition="Printings of a New London paragraph of 24 January 1777: 'We are informed, that Captain Phips, who lately escaped from the fleet at Newport, heard a letter read by an Hessian officer; another Hessian, who stood by, heard it, and could speak English, told Phips, that the contents were to recall the Hessian troops, for the dominions of the Prince of Hesse were invaded by the French King.' A report at second hand of what a Hessian soldier said.",
      role='report', words=55, dateline=True,
      core=['W\\s?E\\s+are\\s+informed,?\\s+that\\s+Capt(?:ain|\\.)?\\s+Phip'],
      stop='The\\s+following\\s+is\\s+an\\s+extract',
      first='New London, 24 January 1777: a report that a letter recalling the Hessian troops was read at Newport.',
      what='the New London paragraph on the Hessian letter',
      printings=[k('CC', '01-27', 3), k('FJ', '02-04', 4), k('VDH', '02-28', 2), k('VP', '02-28', 5)]),
 dict(id='washington-proclamation-on-british-protections-25-january-1777', kind='document_group',
      label="General Washington's proclamation of 25 January 1777 on inhabitants who signed the British commissioners' declaration of fidelity",
      definition="Printings of General Washington's proclamation given at headquarters, Morristown, 25 January 1777: 'Whereas several persons, inhabitants of the United States of America, influenced by inimical motives, intimidated by the threats of the enemy, or deluded by a proclamation issued the 30th of November last, by Lord and General Howe, styled the King's commissioners for granting pardons, &c. ... have been so lost to the interest and welfare of this country, as to repair to the enemy, sign a declaration of fidelity'; it commands everyone who has taken such protections to repair to headquarters or the nearest general officer, deliver them up and take the oath of allegiance to the United States, or withdraw within the enemy's lines. The New-York Gazette prints it with its own heading. The commander's own proclamation.",
      role='published_document', words=55, dateline=False,
      head='(?:["“]?\\s*B\\s?Y\\s+H\\s?IS\\s+E\\s?XCELLENCY\\s+G\\s?EORGE\\s+W\\s?ASHINGTON,?\\s*E\\s?SQ\\w*[;:,.]?\\s+[^"“]{0,140}?A\\s?MERICA\\.?\\s*["“]?\\s*)?(?:A\\s+)?P\\s?R\\s?O\\s?C\\s?L\\s?A\\s?M\\s?A\\s?T\\s?I\\s?O\\s?N\\.?\\s*["“]?\\s*',
      core=['W\\s?HEREAS\\s+several\\s+[Pp]ersons,?\\s+["“]?\\s*[Ii]nhabitants\\s+of\\s+the\\s+United\\s+States'],
      first="General Washington's proclamation of 25 January 1777 on those who took the British protections.",
      what="General Washington's proclamation of 25 January",
      printings=[k('CC', '02-03', 3), k('PP', '02-04', 1), k('NYG', '02-10', 2), k('FJ', '02-11', 3), k('VP', '02-14', 1)]),
 dict(id='king-speech-opening-parliament-31-october-1776', kind='document_group',
      label="The King's speech at the opening of Parliament, 31 October 1776",
      definition="Printings of the speech of George III to both Houses of Parliament, 31 October 1776, as the American papers printed it in February 1777: 'My Lords and Gentlemen, Nothing could have afforded me so much satisfaction as to have been able to inform you, at the opening of this session, that the troubles which have so long distracted my colonies in North America were at an end'; it says that the colonies' leaders 'have now openly renounced all allegiance to the crown'. Purdie's Virginia Gazette heads it 'Speech of George III. tyrant of Great Britain, to his venal parliament'. The King's own speech.",
      role='published_document', words=60, dateline=False,
      head='(?:["“]?\\s*M\\s?Y\\s+L\\s?ORDS\\s+and\\s+G\\s?ENTLEMEN[,.:;]?\\s*)',
      core=['N\\s?\\s?O\\s?THING\\s+could\\s+have\\s+afforded\\s+(?:me|us)\\s+(?:so|such|of)\\s+(?:much\\s+)?satisfaction'],
      first="The King's speech at the opening of Parliament, 31 October 1776.",
      what="the King's speech of 31 October 1776",
      printings=[k('PP', '02-04', 4), k('VDH', '02-14', 1), k('VP', '02-14', 1), k('CC', '02-17', 3), k('FJ', '02-25', 2)]),
 dict(id='philadelphia-report-accomack-militia-march-to-salisbury-february-1777', kind='message_group',
      label='Philadelphia, February 1777: Colonel Simpson with 500 Accomack militia marched against the Tories entrenched at Salisbury, Maryland',
      definition="Printings of a Philadelphia paragraph of February 1777: 'We hear Col. Simpson, with 500 of the Accomack county militia, marched the beginning of this month to Salisbury, on the eastern shore of Maryland, where a large body of Tories were entrenched, under the command of the famous General Gray. Upon the approach of the Colonel and his militia, the dastards ran away; but several of their ringleaders were taken and sent to Congress.' A report at second hand. Of the same affair and weeks, the Baltimore paragraph of 4 February on the 'perfidious people' of Worcester and Somerset counties who 'assembled in hostile array' (4 papers) is not chosen (X-1800-01).",
      role='report', words=55, dateline=True,
      core=['W\\s?E\\s+hear,?\\s+[Cc]ol(?:onel|\\.)?\\s+Simpson,?\\s+with\\s+(?:500|five\\s+hundred)'],
      stop='E\\s?xtract\\s+of\\s+a\\s+letter',
      first="Philadelphia, February 1777: the Accomack militia march against the Tories at Salisbury, on Maryland's Eastern Shore.",
      what='the Philadelphia paragraph on the Accomack militia',
      printings=[k('PP', '02-25', 3), k('VDH', '03-07', 6), k('VP', '03-07', 5), k('CC', '03-10', 2), k('FJ', '03-15', 3)]),
 dict(id='king-proclamation-for-a-general-fast-and-burke-remarks-1776', kind='context_group',
      label="The King's proclamation for a general fast, 1776, and Mr. Burke's remarks on it",
      children=['burke-remarks-on-the-proclamation-for-a-fast-1776', 'king-proclamation-for-a-general-fast-1776'],
      definition="The King's proclamation of a public fast for the war in America, and the remarks Mr. Burke made on it in the House of Commons, which the papers printed together in March and April 1777. Contains those two groups."),
 dict(id='burke-remarks-on-the-proclamation-for-a-fast-1776', parent='king-proclamation-for-a-general-fast-and-burke-remarks-1776', kind='message_group',
      label="Mr. Burke's remarks in the House of Commons on the proclamation for a general fast",
      definition="Printings of a report of Mr. Burke's words in the House of Commons on the American contest and the proclamation for a fast: 'Mr. Burke, in the House of Commons, speaking on the American contest, in which he was very severe against the Ministry, said—That, after having been massacred, first by the Hessians and then by the Lawyers, they now talked of a revisal of the acts that had been complained of seven years ago'; 'he complained bitterly of some expressions in the proclamation for the general fast'. Printed after the proclamation. A report of a member's speech, his own argument as the papers gave it.",
      role='report', words=60, dateline=False,
      head=r"(?:M\s?R\.?\s+B\s?URKE'?s\s+(?:remarks|strictures|Observations)\s+(?:on|upon)\s+(?:the\s+foregoing\s+)?(?:P\s?roclamation|it)[.:]?\s*)",
      core=['M\\s?R\\.?\\s+B\\s?URKE,?\\s+in\\s+the\\s+House\\s+of\\s+Commons,?\\s+speaking\\s+on\\s+the\\s+American'],
      first="Mr. Burke's remarks in the Commons on the American contest and the proclamation for a fast.",
      what="Mr. Burke's remarks on the fast",
      printings=[k('FJ', '03-04', 1), k('CC', '03-10', 1), k('PP', '03-11', 3), k('VP', '04-04', 1), k('VDH', '04-11', 1)]),
 dict(id='king-proclamation-for-a-general-fast-1776', parent='king-proclamation-for-a-general-fast-and-burke-remarks-1776', kind='document_group',
      label="The King's proclamation for a general fast, 1776: 'the just and necessary measures of force which we are obliged to use against our rebellious subjects'",
      definition="Printings of the King's proclamation for a general fast: 'George R. We, taking into our most serious consideration the just and necessary measures of force which we are obliged to use against our rebellious subjects in our colonies and provinces in North America, and putting our trust in almighty God'; it commands a public fast and humiliation to be observed in England, Wales and Berwick upon Tweed on Friday 13 December 1776. The King's own proclamation.",
      role='published_document', words=55, dateline=False,
      head='(?:B\\s?Y\\s+the\\s+K\\s?ING\\.?\\s*)?(?:A\\s+)?P\\s?R\\s?O\\s?C\\s?L\\s?A\\s?M\\s?A\\s?T\\s?I\\s?O\\s?N[.,]?\\s*(?:F\\s?OR|for)\\s+a\\s+(?:G\\s?ENERAL|general)\\s+F\\s?AST\\.?\\s*["“]?\\s*G\\s?EORGE\\s+R\\.?\\s*',
      core=['(?:W\\s?E,?\\s+)?taking\\s+(?:it\\s+)?into\\s+our\\s+most\\s+serious\\s+consideration,?\\s+the\\s+just'],
      first="The King's proclamation for a general fast, 1776.",
      what="the King's proclamation for a general fast",
      printings=[k('FJ', '03-04', 1), k('CC', '03-10', 1), k('PP', '03-11', 3), k('NPT', '03-13', 2), k('VDH', '04-11', 1)]),
 dict(id='charleston-report-brigantine-notre-dame-from-france-february-1777', kind='message_group',
      label='Charleston, 20 February 1777: the armed brigantine Notre Dame arrives from France with a valuable cargo',
      definition="Printings of a Charleston paragraph of 20 February 1777: 'Last night Capt. Cockran, in the armed Brigantine Notre Dame, arrived here from France, with a valuable cargo, after a passage of 7 weeks'; it reports news brought from France, among it Dr. Franklin's arrival and the burning of the dockyard at Portsmouth. A report at second hand.",
      role='report', words=55, dateline=True,
      core=['L\\s?AST\\s+night,?\\s+Capt(?:ain|\\.)?\\s+Coc[kh]r[ai]n'],
      first='Charleston, February 1777: the Notre Dame arrives from France with a cargo and news.',
      what='the Charleston paragraph on the Notre Dame',
      printings=[k('FJ', '03-22', 3), k('CC', '03-24', 3), k('VDH', '03-28', 6), k('VP', '04-04', 5)]),
 dict(id='baltimore-report-of-a-french-fleet-at-charleston-march-1777', kind='message_group',
      label='Baltimore, 17 March 1777: a report from North Carolina of a large French fleet seen at Charleston',
      definition="Printings of a Baltimore paragraph of 17 March 1777: 'Last Night Mr. Charles Cook, arrived here in 12 Days from Newbern, in North-Carolina, and brings the following important intelligence', that a captain of the North Carolina forces, just returned from Charleston, said he saw there 'a large French Fleet, consisting of 15 Men of War ... and 40 Merchantmen' with cannon, small arms and goods for the American states. A report at third hand.",
      role='report', words=60, dateline=True,
      core=['L\\s?AST\\s+N\\s?ight,?\\s+Mr\\.?\\s+Charles\\s+Cook', 'B\\s?Y\\s+Mr\\.?\\s+Charles\\s+Cook,?\\s+a\\s+[Gg]entleman\\s+who\\s+arrived\\s+here\\s+last\\s+night'],
      first='Baltimore, March 1777: a report at third hand of a French fleet at Charleston.',
      what='the Baltimore paragraph on a French fleet',
      printings=[(k('VDH', '03-28', 6), {'note': "Printed in another form, dated Baltimore, March 18: 'By Mr. Charles Cook, a gentleman who arrived here last night in 12 days from Newbern'. Counted with the others (C-02)."}),
                 (k('VP', '03-28', 5), {'note': "Printed in another form, dated Baltimore, March 18: 'By Mr. Charles Cook, a gentleman who arrived here last night in 12 days from Newbern'. Counted with the others (C-02)."}),
                 k('CC', '04-07', 2), k('FJ', '04-12', 3), k('NPT', '05-15', 3)]),
 dict(id='pittsburgh-letter-of-24-march-1777-indians-assembled', kind='message_group',
      label="A letter from Pittsburgh, 24 March 1777: 'matters have a very gloomy aspect here'; Indians said to be assembled to attack Kittanning and the post",
      definition="Printings of an extract of a letter from Pittsburgh of 24 March 1777: 'I must inform you that matters have a very gloomy aspect here. Daniel Sullivan has returned from the Indian country, and brings accounts of Indians being assembled; in order to attack the Kittanning and this post'; the letter goes on to tell of settlers killed near Kittanning and of a message from Niagara left on one of them. The excerpts end before the names of the settlers (C-12). A private letter: the writer's account.",
      role='report', words=45, dateline=False,
      head=r"(?:E\s?XTRA\w*|Excerpt)\s+OF\s+A?\s*LETTER\s+FROM\s+\S{1,14},?\s+DATED\s+M\s?ARCH\s+24(?:,?\s*1777)?\.?\s*",
      core=['["“]?\\s*I\\s+must\\s+inform\\s+(?:you,?\\s+)?that\\s+(?:matters|affairs)\\s+(?:have|bear)\\s+a\\s+very\\s+gloomy\\s+aspect'],
      stop='A\\s+few\\s+days\\s+ago\\s+the\\s+Indians\\s+killed',
      first='A letter from Pittsburgh, March 1777: accounts of Indians assembling to attack Kittanning and Fort Pitt.',
      what='the letter from Pittsburgh',
      printings=[k('PP', '04-08', 2), k('VDH', '04-18', 6), k('CC', '04-28', 1), k('NPT', '05-01', 3), k('SCG', '05-15', 2)]),
 dict(id='congress-orders-monuments-to-warren-and-mercer-april-1777', kind='message_group',
      label="'The Honourable the Congress have ordered a monument to be erected in Boston, in honour of Major General Warren; and in Virginia, in honour of Brigadier General Mercer'",
      definition="Printings of a paragraph of April 1777: 'The Honourable the Congress have ordered a monument to be erected in Boston, in honour of Major General Warren; and in Virginia, in honour of Brigadier General Mercer, as a testimony of their illustrious virtues, and of the gratitude of their country. They have likewise ordered the eldest son of the former of those Gentlemen, and the youngest son of the latter, to be educated at the expence of the United States.' A report of Congress's resolutions.",
      role='report', words=60, dateline=False,
      core=['T\\s?HE\\s+(?:Hon(?:ourable|orable|\\.)\\s+)?(?:the\\s+)?Congress\\s+have\\s+ordered\\s+a\\s+[Mm]onument\\s+to\\s+be\\s+erected\\s+in\\s+(?:the\\s+town\\s+of\\s+)?Boston'],
      stop='P\\s?ENNSYLVANIA\\s+War|W\\s?e\\s+hear\\s+that\\s+on\\s+Sunday',
      first='Congress orders monuments to Generals Warren and Mercer and the education of a son of each.',
      what='the paragraph on the monuments to Warren and Mercer',
      printings=[k('PP', '04-15', 3), k('VP', '04-25', 2), k('CC', '04-28', 2), k('VDH', '05-02', 3), k('FJ', '05-03', 4),
                 k('NPT', '05-15', 4), k('SCG', '05-15', 2)]),
 dict(id='washington-and-the-british-commanders-on-the-exchange-of-prisoners-1777', kind='context_group',
      label='Letters between General Washington and the British commanders on the exchange of prisoners, published in April and June 1777',
      children=['cornwallis-letter-to-washington-3-april-1777-walcott-demand', 'washington-letter-to-howe-9-april-1777-on-the-exchange-of-prisoners', 'howe-letter-to-washington-21-april-1777-on-the-exchange-of-prisoners', 'washington-letter-to-howe-10-june-1777-final-determination-on-prisoners'],
      definition="The letters on the exchange of prisoners that the papers printed in April 1777 (Lord Cornwallis's letter of 3 April with Lieutenant Colonel Walcott's demand, General Washington's letter to General Howe of 9 April) and in June and July 1777, by order of Congress of 16 June (General Howe's letter of 21 April, General Washington's answer of 10 June). Each letter is counted by its own words (X-1810-01). Contains those four groups."),
 dict(id='cornwallis-letter-to-washington-3-april-1777-walcott-demand', parent='washington-and-the-british-commanders-on-the-exchange-of-prisoners-1777', kind='document_group',
      label="Lord Cornwallis to General Washington, Brunswick, 3 April 1777, with Lieutenant Colonel Walcott's demand for the return of prisoners",
      definition="Printings of Lord Cornwallis's letter to General Washington, dated Brunswick, 3 April 1777: 'I enclose to you a paper which Lieutenant Colonel Walcott delivered yesterday to Lieutenant Colonel Harrison, and which Lieut. Col. Harrison did not then think proper to receive', with the paper itself: Lieutenant Colonel Walcott's 'Demand ... of return of prisoners' of 2 April, that General Washington return prisoners for those sent back to him. A letter and the paper it encloses are one item (X-1810-01). The British commanders' own letter and demand.",
      role='published_document', words=55, dateline=False,
      core=['C\\s?OPY\\s+of\\s+a\\s+[Ll]etter\\s+from\\s+(?:Lieut(?:enant|\\.)?\\s+Gen(?:eral|\\.)?\\s+)?(?:Lord|Ld\\.?)\\s+C\\s?ORNWALLIS\\s+to\\s+(?:Gen(?:eral|\\.)\\s+)?W\\s?ASHINGTON'],
      first="Lord Cornwallis to General Washington, 3 April 1777, enclosing Colonel Walcott's demand for the return of prisoners.",
      what="Lord Cornwallis's letter of 3 April",
      printings=[k('PP', '04-15', 1), k('VDH', '05-02', 1), k('CC', '05-05', 1), k('SCG', '05-15', 2), k('NPT', '05-29', 1),
                 k('FJ', '05-31', 2)]),
 dict(id='washington-letter-to-howe-9-april-1777-on-the-exchange-of-prisoners', parent='washington-and-the-british-commanders-on-the-exchange-of-prisoners-1777', kind='document_group',
      label="General Washington to General Howe, 9 April 1777, on Lieutenant Colonel Walcott's demand and the exchange of prisoners",
      definition="Printings of General Washington's letter to General Howe of 9 April 1777: 'I take the liberty of transmitting you a copy of a paper addressed to me by Lieut. Col. Walcott of your army, which came inclosed in a letter from Lieut. Gen. Lord Cornwallis'; he answers the demand, says the prisoners returned to him had been so treated that they could not be deemed fit for exchange, and holds that the discrimination made in the case of General Lee is an obstacle to compliance. Purdie's Virginia Gazette prints a summary of it in its own words (not counted, C-07). The commander's own letter.",
      role='published_document', words=55, dateline=False,
      core=['(?:I\\s+)?T\\s?AKE\\s+the\\s+liberty\\s+of\\s+transmitting\\s+(?:to\\s+)?you\\s+a\\s+copy\\s+of\\s+a\\s+paper'],
      first='General Washington to General Howe, 9 April 1777, answering the demand for the return of prisoners.',
      what="General Washington's letter of 9 April to General Howe",
      printings=[k('PP', '04-15', 1), k('VDH', '05-02', 1), k('CC', '05-05', 1), k('SCG', '05-15', 2), k('NPT', '05-29', 1),
                 k('FJ', '05-31', 2)]),
 dict(id='howe-letter-to-washington-21-april-1777-on-the-exchange-of-prisoners', parent='washington-and-the-british-commanders-on-the-exchange-of-prisoners-1777', kind='document_group',
      label='General Howe to General Washington, New York, 21 April 1777, on the exchange of prisoners',
      definition="Printings of General Howe's letter to General Washington of 21 April 1777, which Congress ordered published on 16 June with the other letters on the subject: 'I have received your letter of the 9th instant, concerning the requisition of Lieutenant Colonel Walcot, a copy of which came inclosed. Though I observe that officer has meant to insist very strongly on the justice of the claim for the return of prisoners in your possession'; he answers the charge on the usage of the prisoners. The British commander's own letter.",
      role='published_document', words=55, dateline=False,
      core=['I\\s+H\\s?AVE\\s+received\\s+your\\s+letter,?\\s+of\\s+the\\s+\\d+(?:th)?\\s+inst(?:ant|\\.)?,?\\s+concerning\\s+the\\s+requisition'],
      first='General Howe to General Washington, 21 April 1777, answering on the prisoners.',
      what="General Howe's letter of 21 April",
      printings=[k('PP', '06-24', 1), k('VDH', '07-04', 2), k('CC', '07-07', 3), k('FJ', '07-19', 2)]),
 dict(id='washington-letter-to-howe-10-june-1777-final-determination-on-prisoners', parent='washington-and-the-british-commanders-on-the-exchange-of-prisoners-1777', kind='document_group',
      label='General Washington to General Howe, Middlebrook, 10 June 1777: his final determination on the exchange of prisoners',
      definition="Printings of General Washington's letter to General Howe of 10 June 1777: 'Your several letters of the 21st of April, 22d of May, and 5th instant, have been received. Having stated my sentiments in an explicit manner, in my letter of the ninth of April, upon the subject of your demand'; as General Howe has called upon him for his final determination, he gives it. The commander's own letter.",
      role='published_document', words=55, dateline=False,
      core=['Y\\s?OUR\\s+several\\s+letters\\s+of\\s+the\\s+21st\\s+(?:of\\s+)?April'],
      first='General Washington to General Howe, 10 June 1777: his final answer on the exchange of prisoners.',
      what="General Washington's letter of 10 June to General Howe",
      printings=[k('PP', '06-24', 4), k('VDH', '07-04', 2), k('CC', '07-14', 1), k('FJ', '07-19', 2), k('NPT', '07-24', 1)]),
 dict(id='lewistown-letter-ship-morris-run-ashore-and-blown-up-april-1777', kind='message_group',
      label='Lewistown (Lewes), 12 April 1777: the ship Morris, Captain Anderson, chased into the Delaware Bay, run ashore and blown up',
      definition="Printings of a letter from Lewistown, Delaware, of 12 April 1777: 'Yesterday morning the ship Morris, Capt. Anderson was chased into the mouth of our Bay by a frigate; the Roebuck, laying in the Road, made sail after her. Capt. Anderson run his ship on shore about half a mile from the Light House'; he fought for near three hours, landed his packet for Congress, and, finding he could defend her no longer, 'laid a train, and blew the ship up'. A report at second hand.",
      role='report', words=60, dateline=True,
      core=['Y\\s?ESTERDAY\\s+morning,?\\s+the\\s+ship\\s+Morris'],
      first='Lewistown, April 1777: the ship Morris run ashore under fire and blown up by her captain.',
      what='the letter from Lewistown on the ship Morris',
      printings=[k('CC', '04-28', 3), k('VDH', '05-02', 3), k('FJ', '05-03', 4), k('NPT', '05-15', 4), k('SCG', '05-15', 2)]),
 dict(id='london-paragraph-preparations-for-a-decisive-campaign-february-1777', kind='message_group',
      label="London, 17 February 1777: 'Every preparation is making on the side of Government, in order to render the ensuing campaign in America decisive'",
      definition="Printings of a London paragraph of 17 February 1777: 'Every preparation is making on the side of Government, in order to render the ensuing campaign in America decisive; as the land forces are to be considerably augmented, and double the number of cruisers will be employed'; 'General Burgoyne is expected to sail in about six weeks for Canada'. A paragraph of a run of London news; a report at second hand.",
      role='report', words=60, dateline=False,
      core=['(?:Feb(?:ruary|\\.)?\\s+17\\.?\\s+)?E\\s?VERY\\s+preparation\\s+is\\s+making\\s+on\\s+the\\s+side\\s+of\\s+[Gg]overnment'],
      first='London, February 1777: preparations to make the next campaign in America decisive; General Burgoyne to sail for Canada.',
      what='the London paragraph of 17 February',
      printings=[k('NPT', '05-01', 2), k('VDH', '05-23', 1), k('VP', '05-23', 2), k('FJ', '05-24', 2), k('GSC', '06-02', 2)]),
 dict(id='boston-report-privateer-takes-six-prizes-for-the-british-army-may-1777', kind='message_group',
      label='Boston, 15 May 1777: an American privateer has taken six prizes bound from Europe for the British army at New York',
      definition="Printings of a Boston paragraph of 15 May 1777: 'We have advice from Dartmouth, that a privateer belonging to one of the United States has lately captured six prizes bound from Europe for the rebel army, under Howe, or the Howes, at New York, laden with provisions and dry goods, three of which are safe arrived in port'; they were part of a provision fleet of about 40 sail without convoy. A report at second hand.",
      role='report', words=55, dateline=True,
      core=['W\\s?E\\s+have\\s+advice\\s+from\\s+Dartmouth'],
      first='Boston, May 1777: a privateer takes six provision ships bound for the British army at New York.',
      what='the Boston paragraph on the privateer from Dartmouth',
      printings=[k('VDH', '06-13', 1), k('VP', '06-13', 2), k('FJ', '06-14', 4), k('NYG', '06-16', 2), k('NPT', '07-03', 4)]),
 dict(id='washington-letters-to-congress-on-the-british-movements-in-new-jersey-june-1777', kind='context_group',
      label="General Washington's letters to Congress of 25 and 28 June 1777 on the British army's retreat to Amboy and its advance to Westfield",
      children=['washington-letter-to-congress-25-june-1777-the-enemy-retreat-to-amboy', 'washington-letter-to-congress-28-june-1777-howe-advances-from-amboy'],
      definition="Extracts of General Washington's letters to Congress of 25 and 28 June 1777, on the British army's retreat from Brunswick to Amboy and on General Howe's advance from Amboy towards Westfield, as the papers printed them in July and August. Each letter is counted by its own words; his letter of 20 June (4 papers) is not chosen (X-1800-01). Contains those two groups."),
 dict(id='washington-letter-to-congress-25-june-1777-the-enemy-retreat-to-amboy', parent='washington-letters-to-congress-on-the-british-movements-in-new-jersey-june-1777', kind='document_group',
      label="General Washington to Congress, Quibbletown, 25 June 1777: on the enemy's retreat from Brunswick to Amboy and their loss",
      definition="Printings of an extract of General Washington's letter to Congress of 25 June 1777: 'When I had the honour to address you last, it was on the subject of the enemy's retreat from Brunswick to Amboy, and of the measures pursued to annoy them'; he writes that their loss fell chiefly on the grenadiers and light infantry who covered the retreat. The commander's own report.",
      role='published_document', words=55, dateline=False,
      head=r"(?:(?:E\s?XTRACT|E\s?XCERPT|C\s?OPY)\s+of\s+(?:a|another)\s+letter\s+from\s+)?Gen(?:eral|\.)\s+W\s?ASHINGTON\s+to\s+C\s?ONGRESS,?\s+dated\s+(?:camp\s+at\s+)?Quibble[\s-]*[Tt]own,?\s+June\s+2[35],?\s+1777\.?\s*(?:S\s?IR[,.]?\s*)?",
      core=['["“]?\\s*W\\s?HEN\\s+I\\s+had\\s+the\\s+hono\\w*\\s+to\\s+address\\s+you\\s+last,?\\s+it\\s+was\\s+on\\s+the\\s+subject', '["“]?\\s*S\\s?IR,?\\s+W\\s?ITH\\s+respect\\s+to\\s+the\\s+subject\\s+of\\s+the\\s+enemy'],
      first="General Washington to Congress, 25 June 1777: the enemy's loss in the retreat to Amboy.",
      what="General Washington's letter of 25 June",
      printings=[k('VDH', '07-11', 1), k('VP', '07-11', 2), k('CC', '07-14', 2), k('NPT', '07-17', 2), k('FJ', '07-19', 4)]),
 dict(id='washington-letter-to-congress-28-june-1777-howe-advances-from-amboy', parent='washington-letters-to-congress-on-the-british-movements-in-new-jersey-june-1777', kind='document_group',
      label='General Washington to Congress, Middlebrook, 28 June 1777: General Howe advanced with his whole army from Amboy as far as Westfield',
      definition="Printings of an extract of General Washington's letter to Congress of 28 June 1777: 'On Thursday morning General Howe advanced with his whole army, in several columns, from Amboy as far as Westfield'; he judges the design was to bring on a general engagement on disadvantageous terms or to cut off the light parties and Lord Stirling's division. The commander's own report.",
      role='published_document', words=55, dateline=False,
      head=r"(?:(?:E\s?XTRACT|E\s?XCERPT|C\s?OPY)\s+of\s+(?:a|another)\s+letter\s+from\s+)?Gen(?:eral|\.)\s+W\s?ASHINGTON\s+to\s+C\s?ONGRESS,?\s+dated\s+(?:camp\s+at\s+)?Middle[\s-]*[Bb]rook,?\s+June\s+28,?\s*(?:1777)?\.?\s*(?:S\s?\s?I\s?R[,.]?\s*)?",
      core=['["“]?\\s*O\\s?N\\s+Thursday\\s+morning,?\\s+Gen(?:eral|\\.)\\s+Howe,?\\s+advanced'],
      first='General Washington to Congress, 28 June 1777: General Howe advances from Amboy to Westfield.',
      what="General Washington's letter of 28 June",
      printings=[k('VDH', '07-11', 2), k('VP', '07-11', 2), k('CC', '07-14', 2), k('FJ', '07-26', 2), k('NPT', '08-07', 1)]),
 dict(id='evacuation-of-ticonderoga-july-august-1777', kind='context_group',
      label="The evacuation of Ticonderoga and Mount Independence, July and August 1777: the council of officers, General St. Clair's letter and Congress's inquiry",
      children=['council-of-general-officers-at-ticonderoga-5-july-1777', 'st-clair-letter-to-congress-14-july-1777-on-the-evacuation', 'congress-inquiry-into-the-evacuation-of-ticonderoga-29-july-1777'],
      definition="Documents printed in July, August and September 1777 on the American army's evacuation of Ticonderoga and Mount Independence before General Burgoyne's army: the council of general officers of 5 July, General St. Clair's letter to Congress of 14 July and Congress's resolutions of 29 July for an inquiry (6 papers each). Of the same affair, General Schuyler's letter of 7 July (5), General St. Clair's letter on General Schuyler (4) and a letter from headquarters on the papers' prejudice against General St. Clair (4) are not chosen (X-1800-01). Contains those three groups."),
 dict(id='council-of-general-officers-at-ticonderoga-5-july-1777', parent='evacuation-of-ticonderoga-july-august-1777', kind='document_group',
      label='The council of general officers held at Ticonderoga, 5 July 1777',
      definition="Printings of the minutes of the council of general officers held at Ticonderoga on 5 July 1777, published by order of Congress: 'At a Council of General Officers held at Ticonderoga, July 5, 1777. Present, Major General St. Clair, Brig. General de Roche Fermoy, Brig. General Poor, Brig. General Paterson, Col. Commandant Long'; General St. Clair put to them whether the posts could be held or should be evacuated. The council's own minutes.",
      role='published_document', words=55, dateline=False,
      core=['A[ts]\\s+a\\s+C\\s?OUNCIL\\s+of\\s+G\\s?ENERAL\\s+O\\s?FFICERS,?\\s+held\\s+at\\s+Ticonderoga'],
      first='The council of general officers at Ticonderoga, 5 July 1777.',
      what='the council of general officers at Ticonderoga',
      printings=[k('PP', '07-22', 2), k('VP', '08-01', 5), k('CC', '08-04', 2), k('NPT', '08-07', 3), k('FJ', '08-09', 2),
                 k('NYG', '08-11', 2)]),
 dict(id='st-clair-letter-to-congress-14-july-1777-on-the-evacuation', parent='evacuation-of-ticonderoga-july-august-1777', kind='document_group',
      label='General St. Clair to Congress, Fort Edward, 14 July 1777, on the evacuation of the posts entrusted to him',
      definition="Printings of General St. Clair's letter to Congress of 14 July 1777: 'Congress may probably think it extraordinary that so much time should have elapsed before they heard from me, after a step of such consequence as the evacuation of the posts that had been intrusted to my care'; he gives the reasons that induced it. Published by order of Congress. The commander's own report.",
      role='published_document', words=55, dateline=False,
      core=['C\\s?OPY\\s+of\\s+a\\s+[Ll]etter\\s+from\\s+(?:Gen(?:eral|\\.)\\s+|Major\\s+General\\s+)?St\\.?\\s+Clair\\s+to\\s+(?:the\\s+)?Congress', '(?:S\\s?\\s?I\\s?R[,.]?\\s*)?C\\s?ONGRESS\\s+may\\s+probably\\s+think\\s+it\\s+extraordinary'],
      first='General St. Clair to Congress, 14 July 1777: his reasons for evacuating Ticonderoga.',
      what="General St. Clair's letter of 14 July",
      printings=[k('PP', '07-22', 2), k('VP', '08-01', 5), k('CC', '08-04', 2), k('FJ', '08-09', 2), k('NYG', '08-11', 2),
                 k('NPT', '08-21', 1)]),
 dict(id='congress-inquiry-into-the-evacuation-of-ticonderoga-29-july-1777', parent='evacuation-of-ticonderoga-july-august-1777', kind='document_group',
      label='Congress, 29 July 1777: an inquiry into the evacuation of Ticonderoga and Mount Independence; Generals St. Clair and Schuyler to repair to headquarters',
      definition="Printings of resolutions of Congress of 29 July to 1 August 1777: 'Resolved, That an inquiry be made into the reasons of the evacuation of Ticonderoga and Mount Independence, and into the conduct of the general officers who were in the Northern department at the time of the evacuation'; General St. Clair and General Schuyler are directed to repair to headquarters, and General Washington to send a general officer to relieve General Schuyler. Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      head=r"I\s?N\s+C\s?ONGRESS,?\s+July\s+29,?\s*(?:1777)?\.?\s*",
      core=['R\\s?ESOLVED,?\\s+[Tt]hat\\s+an\\s+[ei]nquiry\\s+be\\s+made\\s+into\\s+the\\s+reasons?\\s+of\\s+the\\s+[ae]vacuation'],
      first='Congress, 29 July 1777: an inquiry into the evacuation of Ticonderoga.',
      what="Congress's resolutions on the inquiry",
      printings=[k('PP', '08-05', 3), k('CC', '08-18', 2), k('NYG', '08-18', 2), k('VDH', '08-22', 2), k('FJ', '08-23', 2),
                 k('NPT', '09-04', 2)]),
 dict(id='congress-thanks-to-meigs-and-barton-25-july-1777', kind='document_group',
      label='Congress, 25 July 1777: thanks and swords to Lieutenant Colonel Meigs for the expedition to Long Island and to Lieutenant Colonel Barton for taking General Prescott',
      definition="Printings of resolutions of Congress of 25 July 1777: 'Resolved, That Congress have a just sense of the merit of Lieutenant-Colonel Meigs, and the officers and men under his command, who distinguished their prudence, activity, enterprise, and valour in the late expedition to Long-Island; and that an elegant sword be provided ... and presented to Lieut. Colonel Meigs'; a second resolution does the same for Lieutenant Colonel Barton, who made prisoner of Major General Prescott. Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      head=r"I\s?N\s+C\s?ONGRESS,?\s+July\s+25,?\s+1777\.?\s*",
      core=['R\\s?ESOLVED,?\\s+[Tt]hat\\s+Congress\\s+have\\s+a\\s+just\\s+sense\\s+of\\s+the\\s+merit\\s+of\\s+Lieut'],
      first='Congress, 25 July 1777: swords for Lieutenant Colonels Meigs and Barton.',
      what="Congress's resolutions of 25 July",
      printings=[k('PP', '07-29', 3), k('CC', '08-11', 2), k('VDH', '08-15', 5), k('VP', '08-15', 5), k('FJ', '08-16', 2),
                 k('NYG', '09-01', 2)]),
 dict(id='washington-letter-to-howe-16-july-1777-prescott-for-lee', kind='document_group',
      label='General Washington to General Howe, 16 July 1777, proposing General Prescott, taken at Rhode Island, in exchange for General Lee, with his letter of 25 July sending it to Congress',
      definition="Printings of General Washington's letter to General Howe of 16 July 1777: 'The fortune of war having thrown Major General Prescott into our hands, I beg leave to propose his exchange for that of Major General Lee'; most papers print it after his letter to Congress of 25 July, 'I do myself the honour to transmit you a copy of my letter to General Howe, of the 16th instant, proposing an exchange between Generals Lee and Prescott', and the New-York Gazette prints it alone, from the Pennsylvania Packet. A letter and the copy it sends are one item, counted by the first that stands on the page (X-1810-01). Of the same affair, General Washington's letter to Congress of 16 July on the capture (4 papers) and the Providence account of it (4) are not chosen (X-1800-01); Congress's resolutions of 25 July thank Lieutenant Colonel Barton. The commander's own letters.",
      role='published_document', words=55, dateline=False,
      core=['["“]?\\s*(?:S\\s?IR,?\\s*)?I\\s+do\\s+my\\s*self\\s+the\\s+hono\\w*\\s+to\\s+transmit\\s+you\\s+a\\s+copy\\s+of\\s+my\\s+letter\\s+to\\s+General\\s+Howe', 'T\\s?HE\\s+[Ff]ortune\\s+of\\s+[Ww]ar\\s+having\\s+thrown\\s+Major\\s+General\\s+Prescott'],
      first='General Washington to General Howe, 16 July 1777: Prescott for Lee.',
      what="General Washington's letter to General Howe on Prescott",
      printings=[k('PP', '07-29', 3), k('VDH', '08-08', 1), k('CC', '08-11', 2), k('NYG', '08-11', 3), k('FJ', '08-16', 2)]),
 dict(id='moses-creek-letter-26-july-1777-a-brush-with-the-enemy-at-fort-edward', kind='message_group',
      label="A letter from Moses Creek, 26 July 1777: 'We have just had a brush with the enemy at Fort Edward'",
      definition="Printings of an extract of a letter from Moses Creek of 26 July 1777: 'We have just had a brush with the enemy at Fort Edward, in which Lieut. Van Veghten was most inhumanly butchered and scalped. Two serjeants and two privates were likewise killed and scalped'; the letter goes on to tell that a young woman was taken from a house at Fort Edward and killed and scalped, and that another woman was killed near the same place. The excerpts end before the young woman's name (C-12). A report at second hand.",
      role='report', words=40, dateline=True,
      core=["(?:E\\s?XTRA\\w*|Excerpt)\\s+of\\s+a\\s+[Ll]etter\\s+from\\s+M[\\w'’]+\\s+[Cc]reek,?\\s+(?:dated\\s+)?July\\s+26"],
      stop='T\\s?hey\\s+took\\s+a\\s+young\\s+woman',
      first='A letter from Moses Creek, July 1777: a skirmish at Fort Edward; men killed and scalped.',
      what='the letter from Moses Creek of 26 July',
      printings=[k('CC', '08-04', 2), k('PP', '08-05', 3), k('NYG', '08-11', 2), k('VP', '08-15', 2), k('NPT', '08-21', 2),
                 k('VDH', '08-22', 1)]),
 dict(id='franklin-and-deane-to-lord-stormont-2-april-1777-and-his-reply', kind='document_group',
      label='Benjamin Franklin and Silas Deane to Lord Stormont, the British ambassador at Paris, 2 April 1777, on prisoners, and his reply',
      definition="Printings of the American commissioners' letter to Lord Stormont of 2 April 1777: 'We did ourselves the honor of writing some time since to your Lordship on the subject of exchanging prisoners; you did not condescend to give us any answer'; they send depositions on the treatment of American prisoners in Europe. The papers add the reply they say was made: 'The king's ambassadour receives no letters from rebels, except when they come to ask mercy.' The commissioners' own letter.",
      role='published_document', words=55, dateline=False,
      core=['A\\s+L\\s?ETTER\\s+from\\s+B\\s?ENJAMIN\\s+F\\s?RANKLIN,?\\s+and\\s+S\\s?ILAS\\s+D\\s?EANE'],
      first='Franklin and Deane to Lord Stormont, April 1777, on prisoners, and his reply.',
      what="the commissioners' letter to Lord Stormont",
      printings=[k('PP', '08-05', 2), k('CC', '08-18', 2), k('NYG', '08-18', 2), k('VP', '08-22', 2), k('FJ', '08-23', 2),
                 k('NPT', '09-04', 2)]),
 dict(id='burgoyne-proclamation-1777', kind='document_group',
      label="General Burgoyne's proclamation, 1777: 'The forces intrusted to my command are designed to act in concert ... with the numerous armies and fleets'",
      definition="Printings of the proclamation of Lieutenant General John Burgoyne, commanding the expedition from Canada, 1777: 'The forces intrusted to my command are designed to act in concert, and upon a common principle, with the numerous armies and fleets which already display, in every quarter of America, the power, the justice, and, when properly sought, the mercy of the King'. The Connecticut Courant calls it 'Burgoyne's pompous proclamation'. The British commander's own proclamation.",
      role='published_document', words=60, dateline=False,
      head='(?:B\\s?Y\\s+J\\s?OHN\\s+B\\s?URGOYNE,?\\s+E\\s?SQ\\w*[;:,.]?\\s+[^"“]{0,500}?(?:&c\\.?\\s*){1,3})',
      core=['T\\s?HE\\s+[Ff]orces\\s+[ei]ntrusted\\s+to\\s+my\\s+[Cc]ommand,?\\s+are\\s+design\\w*\\s+to\\s+act'],
      first="General Burgoyne's proclamation from the expedition from Canada, 1777.",
      what="General Burgoyne's proclamation",
      printings=[k('NYG', '08-18', 3), k('PP', '08-26', 4), k('CC', '09-08', 2), k('FJ', '09-20', 4)]),
 dict(id='close-of-the-session-of-parliament-6-june-1777', kind='context_group',
      label="The close of the session of Parliament, 6 June 1777: the Speaker's address and the King's speech",
      children=['king-speech-closing-parliament-6-june-1777', 'speaker-of-the-commons-address-to-the-king-6-june-1777'],
      definition="The Speaker of the House of Commons' address to the King and the King's speech at the close of the session of Parliament on 6 June 1777, as the papers printed them from September to November. Contains those two groups."),
 dict(id='king-speech-closing-parliament-6-june-1777', parent='close-of-the-session-of-parliament-6-june-1777', kind='document_group',
      label="The King's speech at the close of the session of Parliament, 6 June 1777",
      definition="Printings of the King's speech closing the session of Parliament, 6 June 1777: 'My Lords and Gentlemen, The conclusion of the public business, and the consideration of the inconvenience which I fear you must have suffered by so long an attendance, call upon me to put an end to this session of Parliament'; he thanks them for their 'steady perseverance in maintaining the rights' of the crown and the nation. The King's own speech.",
      role='published_document', words=55, dateline=False,
      head='["“]?\\s*M\\s?Y\\s+L\\s?ORDS\\s+and\\s+G\\s?ENTLEMEN[,.:;]?\\s*["“]?\\s*',
      core=['["“]?\\s*T\\s?HE\\s+conclusion\\s+of\\s+(?:the\\s+)?publi\\w*\\s+business'],
      first="The King's speech closing Parliament, 6 June 1777.",
      what="the King's speech of 6 June",
      printings=[k('NYG', '09-08', 2), k('NPT', '09-11', 2), k('FJ', '09-27', 3), k('CC', '10-07', 1), k('VP', '11-07', 1)]),
 dict(id='speaker-of-the-commons-address-to-the-king-6-june-1777', parent='close-of-the-session-of-parliament-6-june-1777', kind='document_group',
      label='The Speaker of the House of Commons to the King at the close of the session, 6 June 1777',
      definition='Printings of a report of the Speaker\'s address to the King on 6 June 1777: \'When the Speaker of the House of Commons came to the Bar of the House of Peers the 6th Instant, he delivered himself to the following Effect: "Your Majesty\'s loyal Commons have passed five Bills for the Service of the current Year. The first a Bill for enabling your Majesty to defray the Extra-Expences of the American War"\'. The Speaker\'s address as the papers gave it.',
      role='published_document', words=55, dateline=False,
      core=['W\\s?HEN\\s+the\\s+Speaker\\s+of\\s+the\\s+House\\s+of\\s+Commons\\s+came\\s+to\\s+the\\s+Bar'],
      first='The Speaker of the Commons to the King, 6 June 1777: the bills of the session.',
      what="the Speaker's address of 6 June",
      printings=[k('NYG', '09-08', 2), k('NPT', '09-25', 2), k('FJ', '09-27', 3), k('VP', '11-07', 1)]),
 dict(id='washington-letters-of-11-september-1777-brandywine', kind='context_group',
      label="General Washington's letters to Congress of 11 September 1777 on the battle on the Brandywine",
      children=['washington-letter-chadds-ford-11-september-1777-five-in-the-afternoon', 'washington-letter-chester-11-september-1777-midnight'],
      definition="General Washington's two letters to Congress of 11 September 1777, from Chadds Ford at five in the afternoon and from Chester at midnight, printed together in most papers. Contains those two groups."),
 dict(id='washington-letter-chadds-ford-11-september-1777-five-in-the-afternoon', parent='washington-letters-of-11-september-1777-brandywine', kind='document_group',
      label='General Washington to Congress, Chadds Ford, 11 September 1777, five in the afternoon: the enemy have kept up a brisk fire from their artillery',
      definition="Printings of General Washington's letter to Congress from Chadds Ford, 11 September 1777, 5 p.m.: 'When I had the honor of addressing you this morning, I mentioned that the enemy were advancing, and had began a cannonade; I would now beg leave to inform you, that they have kept up a brisk fire from their artillery ever since'; their advanced party was attacked by General Maxwell's light troops. The commander's own report.",
      role='published_document', words=55, dateline=False,
      head=r"C\s?HAD'?S?[\s-]*F\s?ORD,?\s+Sept(?:ember|\.)?\s+11,?\s+1777,?\s+5\s+o'?\s?[Cc]lock,?\s*(?:P\.?\s*M\.?)?\s*(?:S\s?\s?I\s?R[,.]?\s*)?",
      core=['W\\s?HEN\\s+I\\s+had\\s+the\\s+hono\\w*\\s+of\\s+(?:addressing|advising)\\s+you\\s+this\\s+morning'],
      first='General Washington to Congress, Chadds Ford, 11 September 1777, afternoon.',
      what="General Washington's letter of 5 p.m., 11 September",
      printings=[k('CC', '09-22', 2), k('NYG', '09-22', 3), k('VDH', '09-26', 1), k('FJ', '09-27', 3)]),
 dict(id='washington-letter-chester-11-september-1777-midnight', parent='washington-letters-of-11-september-1777-brandywine', kind='document_group',
      label="General Washington to Congress, Chester, 11 September 1777, midnight: 'in this day's engagement we have been obliged to leave the enemy masters of the field'",
      definition="Printings of General Washington's letter to Congress from Chester, 11 September 1777, at midnight: 'I am sorry to inform you that in this day's engagement we have been obliged to leave the enemy masters of the field. Unfortunately, the intelligence received of the enemy's advancing up the Brandywine, and crossing at a ford about six miles above us, was uncertain and contradictory'. Published by order of Congress. The commander's own report.",
      role='published_document', words=55, dateline=False,
      head=r"C\s?HESTER,?\s+Sept(?:ember|\.)?\s+11,?\s+1777,?\s+12\s+o'?\s?[Cc]lock\s+at\s+[Nn]ight\.?\s*(?:S\s?\s?I\s?R[,.]?\s*)?",
      core=['I\\s+A\\s?M\\s+sorry\\s+to\\s+inform\\s+you,?\\s+that\\s+in\\s+this\\s+day'],
      first='General Washington to Congress, Chester, midnight, 11 September 1777: the enemy left masters of the field.',
      what="General Washington's letter of midnight, 11 September",
      printings=[k('CC', '09-22', 2), k('NYG', '09-22', 3), k('VDH', '09-26', 1), k('VP', '09-26', 2), k('FJ', '09-27', 3)]),
 dict(id='congress-resolution-on-loan-office-interest-in-bills-on-paris-10-september-1777', kind='document_group',
      label='Congress, 10 September 1777: the interest on loan office certificates to be paid in bills of exchange on the commissioners in Paris',
      definition="Printings of a resolution of Congress of 10 September 1777: 'Resolved, That the interest which shall arise, after the date of this resolution, on loan office certificates already issued, or which shall be issued before the first day of March next, be annually paid at the respective loan offices in bills of exchange on the Commissioners of the United States in Paris, at the rate of five livres of France, for every Spanish milled dollar'. Congress's own resolution.",
      role='published_document', words=55, dateline=False,
      head=r"I\s?N\s+C\s?ONGRESS,?\s+September\s+10\.?,?\s*(?:1777\.?)?\s*",
      core=['R\\s?ESOLVED,?\\s+[Tt]hat\\s+the\\s+[Ii]nterest\\s+which\\s+shall\\s+arise'],
      first='Congress, 10 September 1777: loan office interest to be paid in bills on Paris.',
      what="Congress's resolution of 10 September",
      printings=[k('VP', '09-26', 2), k('CC', '09-29', 2), k('VDH', '10-03', 1), k('NYG', '11-10', 2), k('NPT', '12-11', 2),
                 k('PP', '12-24', 3)]),
 dict(id='convention-of-saratoga-october-1777', kind='context_group',
      label="The convention of Saratoga, October 1777: the articles of convention and General Burgoyne's letter to Sir William Howe",
      children=['articles-of-convention-between-burgoyne-and-gates-october-1777', 'burgoyne-letter-to-howe-after-the-convention-october-1777'],
      definition="The articles of convention between Lieutenant General Burgoyne and Major General Gates (October 1777), under which General Burgoyne's troops were to march out and leave their arms, printed by all seven papers that survive for its weeks, and General Burgoyne's letter to Sir William Howe on the campaign and the convention, as the papers printed them from October to December. Contains those two groups."),
 dict(id='articles-of-convention-between-burgoyne-and-gates-october-1777', parent='convention-of-saratoga-october-1777', kind='document_group',
      label='The articles of convention between Lieutenant General Burgoyne and Major General Gates, Saratoga, October 1777',
      definition="Printings of the articles of convention of October 1777: 'I. The troops under Lieut. Gen. Burgoyne are to march out of their camp, with the honors of war, and the artillery of the intrenchments, to the verge of the river ... where the arms and artillery are to be left'; 'II. A free passage to be granted to the army, under Lieutenant Gen. Burgoyne, to Great-Britain, upon condition of not serving again in North-America, during the present contest'. Published by order of Congress. The two generals' own convention.",
      role='published_document', words=55, dateline=False,
      head=r"A\s?RTICLES\s+of\s+C\s?ONVENTION\s+between\s+Lieut(?:enant|\.)?[\s-]*Gen(?:eral|\.)?\s+B\s?URGOYNE,?\s+and\s+Major[\s-]*Gen(?:eral|\.)?\s+G\s?ATES\.?\s*",
      core=['(?:I|1)\\.?\\s+T\\s?HE\\s+[Tt]roops\\s+under\\s+Lieut(?:enant|\\.)?[\\s-]*Gen(?:eral|\\.)?\\s+Burgoyne\\s+(?:are\\s+)?to\\s+march\\s+out'],
      first="The articles of convention of Saratoga, October 1777: General Burgoyne's army to lay down its arms.",
      what='the articles of convention',
      printings=[k('CC', '10-28', 2), k('VDH', '11-07', 2), k('VP', '11-07', 5), k('NYG', '11-10', 2), k('NJG', '11-14', 3),
                 k('NPT', '12-11', 1), k('PP', '12-17', 4)]),
 dict(id='burgoyne-letter-to-howe-after-the-convention-october-1777', parent='convention-of-saratoga-october-1777', kind='document_group',
      label='General Burgoyne to Sir William Howe, October 1777: his account of the campaign and the convention',
      definition='Printings of General Burgoyne\'s letter to Sir William Howe, brought by Lieutenant Valancy of the 62d regiment: \'In conformity to my orders, "to proceed by the most vigorous exertions to Albany," I passed the Hudson\'s river at Saratoga, on the 13th of September. No exertions have been left untried. The army under my command has fought twice against great superiority of numbers\'. The British commander\'s own account.',
      role='published_document', words=55, dateline=False,
      core=['C\\s?OPY\\s+of\\s+a\\s+letter\\s+from\\s+his\\s+Excellency\\s+Lieut(?:enant|\\.)?\\s+Gen(?:eral|\\.)?\\s+B\\w+,?\\s+to\\s+his\\s+Excellency\\s+Sir\\s+W\\s?ILLIAM\\s+H\\s?OWE'],
      first='General Burgoyne to Sir William Howe, October 1777: his account of the campaign.',
      what="General Burgoyne's letter to Sir William Howe",
      printings=[k('VDH', '11-28', 1), k('NYG', '12-01', 2), k('CC', '12-02', 3), k('NPT', '12-11', 1), k('PP', '12-17', 3)]),
 dict(id='washington-proclamation-pardon-to-deserters-who-return-1777', kind='document_group',
      label="General Washington's proclamation of 24 October 1777: a full and free pardon to deserters who return to their corps before 1 January",
      definition="Printings of General Washington's proclamation of 24 October 1777 (printed in November and December): 'Whereas sundry soldiers belonging to the armies of the said states have deserted from the same, these are to make known to all those who have so offended, and who shall return to their respective corps ... before the first day of January next, that they shall obtain a full and free pardon'; those who do not may expect the punishment of the law. The commander's own proclamation.",
      role='published_document', words=55, dateline=False,
      head='(?:P\\s?R\\s?O\\s?C\\s?L\\s?A\\s?M\\s?A\\s?T\\s?I\\s?O\\s?N\\.?\\s*)?(?:B\\s?Y\\s+(?:H\\s?IS\\s+)?E\\s?XCELLENCY\\s+G\\s?EORGE\\s+W\\s?ASHINGTON,?\\s*E\\s?SQ\\w*[;:,.]?\\s+[^"“]{0,140}?A\\s?MERICA\\.?\\s*)?(?:(?:A\\s+)?P\\s?R\\s?O\\s?C\\s?L\\s?A\\s?M\\s?A\\s?T\\s?I\\s?O\\s?N\\.?\\s*)?',
      core=['W\\s?HEREAS\\s+sundry\\s+soldiers,?\\s+belonging\\s+to\\s+the\\s+armies'],
      first="General Washington's proclamation of 24 October 1777: pardon for deserters who return before 1 January.",
      what="General Washington's proclamation on deserters",
      printings=[k('CC', '11-25', 1), k('VDH', '11-28', 1), k('VP', '11-28', 1), k('PP', '11-29', 3), k('NJG', '12-05', 2)]),
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
            problems.append((s['id'], key, 'page not in the 1777 pages'))
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
        r['id'] = f'S77-{n:03}'
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
               'admission_rule': 'Reviewed 1777 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1777/'
    return {
        'ledger_id': 'ledger:stories-1777', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1777', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1777, and of 1776 where they reach the 1777 pages (long-running ones '
                   'included), a deeper comparison of every item in 3 or more papers with every page, a sweep of word-for-word passages shared by 4 '
                   'or more papers for short items the families miss, counts of every candidate by its own opening over all 1,320 pages of 1777 in '
                   'both transcriptions, phrase searches, reading of every hit, and scan checks of each admitted passage, by the thin-year rule '
                   '(register Y-THIN: more than half of the papers that survive for the item\'s weeks, and at least 4)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1776.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1777.py': 'ledger_code', 'work/archive_data/ledgers/stories_1777_review.json': 'scan_review',
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
