"""Write ledgers/stories_1780.json: reviewed stories of 1780, round one.

1780 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN) as the owner amended it on 23 November 2026 (B1): an
item, counted by its own words, is eligible when it was printed by more than half of the newspapers that survive for its weeks,
and by at least 4 newspapers; digests are not. Items printed by every newspaper that survives for their weeks are admitted; the
other eligible items are chosen to cover the months and the kinds of news, about as many stories as a standard year (20 to 35, a
target, not a quota); one affair's items as in X-1800-01. Sub-stories (C-01), private persons (R-04) and the list of items read
and not admitted (R-03) apply as in every year.

The automatic families first printed in 1780 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1779 over the 1780 pages
(items_from_1779.json); every item in 3 or more papers was counted by its own opening over all 1,406 pages of 1780 in both
transcriptions and merged into text units, a sweep of passages shared word for word by 4 or more papers found short items the
families miss, and every unit that meets the bar was read (outputs/story_discovery_1780/README.md). 1780 has 7 catalogue series,
which are 7 papers; 6 are in print in most weeks, 7 in the weeks of 20 June, when the Royal South-Carolina Gazette's one issue
survives.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 25-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1780_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1780.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1780/search_pages.json). The excerpts are cut from
the 1780 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1780'
D = PROJECT/'outputs/story_discovery_1780'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1780_review.json'
OUT = HERE/'stories_1780.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83021127': 'The Pennsylvania Packet', 'sn83025471': 'The New-Jersey Gazette', 'sn83030493': 'The New-York Gazette',
         'sn84023855': 'The Connecticut Courant', 'sn84024739': 'The Virginia Gazette', 'sn83025584': 'The New-Hampshire Gazette',
         'sn83025791': 'The Royal South-Carolina Gazette'}
ONE = {'PP': 'sn83021127', 'NJG': 'sn83025471', 'NYG': 'sn83030493', 'CC': 'sn84023855', 'VG': 'sn84024739', 'NHG': 'sn83025584',
       'RSCG': 'sn83025791'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1780), page and edition."""
    return f'{ONE[paper]}|{YEAR}-{date}|{ed}|{page}'


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
 dict(id='washington-letter-to-congress-18-january-1780-staten-island', kind='document_group',
      label="General Washington to Congress, Morristown, 18 January 1780, on the descent upon Staten Island over the ice, with Lord Stirling's report",
      definition="Printings of General Washington's letter to the President of Congress, Morristown, 18 January 1780: 'The severity of the weather having rendered a descent upon Staten-Island practicable by the ice ...', with Lord Stirling's report of the expedition enclosed (one item, X-1810-01). The commander's own letter.",
      role='published_document', words=50, dateline=False,
      head='(?:E\\s?XTRACT|E\\s?XCERPT|C\\s?OPY)\\s+of\\s+a\\s+letter\\s+from\\s+(?:his\\s+Excellency\\s+)?Gen(?:eral|\\.)\\s+W\\s?ASHINGTON[^"“]{0,200}(?:["“]?\\s*S\\s?\\s?I\\s?\\s?R[,.]?\\s*["“]?\\s*)?',
      core=['T\\s?HE\\s+severity\\s+of\\s+the\\s+weather\\s+having\\s+rendered\\s+a\\s+descent'],
      first='General Washington to Congress, 18 January 1780: Staten Island.',
      what="General Washington's letter of 18 January",
      printings=[k('PP', '01-22', 2), k('PP', '01-25', 3), k('NJG', '01-26', 3), k('NYG', '01-31', 2), k('VG', '02-12', 2),
                 k('CC', '02-15', 2)]),
 dict(id='the-serapis-and-paul-jones-letters-of-the-two-commanders-1779', kind='context_group',
      label="The action of the Serapis and Paul Jones's squadron, September 1779: the letters of Commodore Jones and Captain Pearson",
      children=['paul-jones-letter-off-the-texel-3-october-1779', 'pearson-letter-on-the-action-with-paul-jones-6-october-1779'],
      definition="Commodore Paul Jones's letter of 3 October 1779 and Captain Pearson's report of 6 October to the Admiralty, on the action off Flamborough Head in which the Serapis was taken, as the papers printed them in 1780. Each letter is counted by its own words. Contains those two groups."),
 dict(id='paul-jones-letter-off-the-texel-3-october-1779', parent='the-serapis-and-paul-jones-letters-of-the-two-commanders-1779', kind='document_group',
      label='Commodore Paul Jones to Messieurs Gourlade and Moylan, on board the Serapis off the Texel, 3 October 1779',
      definition="Printings of a letter of Commodore John Paul Jones to Messieurs Gourlade and Moylan at L'Orient, dated on board the Serapis off the Texel, 3 October 1779: 'I have only time, my dear friends, to inform you, that I have this day anchored here, having taken this ship in the night of the 23d ult. on the coast of England, after a battle of three hours and a half'. The American commander's own letter.",
      role='published_document', words=50, dateline=False,
      head='(?:C\\s?OPY|E\\s?XTRACT)\\s+of\\s+a\\s+letter\\s+from\\s+Com(?:modore|\\.)\\s+(?:John\\s+)?Paul\\s+Jones[^"“]{0,320}',
      core=['I\\s+have\\s+only\\s+time,?\\s+my\\s+dear\\s+friends'],
      first="Paul Jones's letter off the Texel, 3 October 1779.",
      what="Paul Jones's letter",
      printings=[k('PP', '01-25', 2), k('NYG', '02-07', 2), k('NJG', '02-09', 4), k('CC', '02-15', 2)]),
 dict(id='pearson-letter-on-the-action-with-paul-jones-6-october-1779', parent='the-serapis-and-paul-jones-letters-of-the-two-commanders-1779', kind='document_group',
      label="Captain Pearson of the Serapis to the Admiralty, Texel, 6 October 1779, on his action with Paul Jones's squadron",
      definition="Printings of the letter of Captain Richard Pearson of his Majesty's ship Serapis to Mr. Stephens of the Admiralty, published by the Admiralty Office on 12 October 1779: 'A letter from Captain Pearson, of his Majesty's ship Serapis, to Mr. Stephens ... was yesterday received at this office: Pallas, French Frigate in Congress Service, Texel, October 6, 1779. Sir, You will be pleased to inform the Lords Commissioners of the Admiralty, that on the 23d ult. being close in with Scarborough ...'; his account of the action with Paul Jones's squadron and the loss of his ship. The British captain's own report.",
      role='published_document', words=50, dateline=False,
      head='A\\s?DMIRALTY[\\s-]*O\\s?FFICE,?\\s+Oct(?:ober|\\.)\\s+12,?\\s+1779\\.?\\s*',
      core=['A\\s?\\s?L\\s?ETTER\\s+from\\s+Capt(?:ain|\\.)\\s+Pe\\w{2,4}on,?\\s+of\\s+his\\s+Majesty'],
      first="Captain Pearson's letter to the Admiralty, 6 October 1779, on the Serapis and Paul Jones.",
      what="Captain Pearson's letter",
      printings=[k('NHG', '02-19', 4), k('NYG', '02-28', 4), k('PP', '03-02', 2), k('CC', '03-07', 1), k('NJG', '03-08', 1),
                 k('VG', '03-18', 1)]),
 dict(id='king-speech-opening-parliament-25-november-1779', kind='document_group',
      label="The King's speech to both Houses of Parliament, 25 November 1779",
      definition="Printings of the King's speech at the opening of Parliament, 25 November 1779: 'My Lords and Gentlemen, I meet you in Parliament at a time when we are called upon by every principle of duty, and every consideration of interest, to exert our united efforts in the support and defence of our country, attacked by an unjust and unprovoked war ...'; it speaks too of the kingdom of Ireland. A letter to a printer that quotes the speech is not counted (C-07). The King's own speech.",
      role='published_document', words=55, dateline=False,
      head='M\\s?Y\\s+L\\s?ORDS,?\\s+(?:A\\s?ND|&)\\s+G\\s?(?:ENTLEMEN|\\w{3,5}MEN)[,.]?\\s*',
      core=['(?:I\\s?\\s?)?M\\s?EET\\s+you\\s+in\\s+Parliament\\s+at\\s+a\\s+time\\s+when'],
      first="The King's speech of 25 November 1779.",
      what="the King's speech of 25 November 1779",
      printings=[k('NYG', '02-21', 2), k('PP', '02-24', 2), k('NJG', '03-01', 1), k('VG', '03-04', 2), k('CC', '03-07', 2)]),
 dict(id='congress-and-the-currency-march-1780', kind='context_group',
      label='Congress and the currency, March 1780: the resolutions of 18 March and the recommendation of 20 March on the tender laws',
      children=['congress-recommends-the-states-revise-their-tender-laws-20-march-1780', 'congress-resolutions-on-the-currency-18-march-1780'],
      definition="Congress's resolutions of 18 March 1780 on the currency and its recommendation of 20 March that the States revise their tender laws, as the papers printed them. Each counted by its own words. Contains those two groups."),
 dict(id='congress-recommends-the-states-revise-their-tender-laws-20-march-1780', parent='congress-and-the-currency-march-1780', kind='document_group',
      label='Congress, 20 March 1780: the States to revise their laws making the Continental bills a tender in discharge of debts',
      definition="Printings of Congress's resolution of 20 March 1780: 'Resolved, That it be recommended to the States to revise their laws enacted pursuant to a former resolution of Congress, making the Continental bills of credit a tender in discharge of debts and contracts, and to amend the same in such manner as they shall judge most conducive to justice in the present state of the paper currency'. Congress's own resolution.",
      role='published_document', words=50, dateline=False,
      head='(?:I\\s?N\\s+C\\s?ONGRESS[;,.]?\\s+)?M\\s?\\s?A\\s?\\s?R\\s?\\s?C\\s?\\s?H\\s+20(?:th)?(?:,?\\s+1780)?\\.?\\s*',
      core=['R\\s?ESOLVED\\s*,?\\s+[Tt]hat\\s+it\\s+(?:be\\s+)?recommended\\s+to\\s+the\\s+(?:several\\s+)?States,?\\s+to\\s+revise\\s+their\\s+[Ll]aws'],
      first='Congress, 20 March 1780: the States to revise their tender laws.',
      what="Congress's resolution of 20 March",
      printings=[k('PP', '03-25', 3), k('NJG', '03-29', 3), k('CC', '04-04', 3), k('NHG', '04-08', 2), k('VG', '04-08', 5),
                 k('NYG', '04-10', 2)]),
 dict(id='congress-resolutions-on-the-currency-18-march-1780', parent='congress-and-the-currency-march-1780', kind='document_group',
      label="Congress, 18 March 1780: resolutions on the currency (the States' monthly quotas; silver and gold at one for forty; new bills to be emitted)",
      definition="Printings of Congress's resolutions of 18 March 1780: 'These United States having been driven into this just and necessary war at a time when no regular civil governments were established ...'; the States to bring in their quotas of fifteen million dollars monthly, silver and gold to be received at one Spanish milled dollar for forty dollars of the bills, and new bills to be emitted on the funds of the States. Pennsylvania's and New Jersey's acts that recite the resolutions are not counted (C-07). Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      head='I\\s?N\\s+C\\s?ONGRESS[;,.]?\\s+March\\s+18(?:th)?,?\\s+17[78][08]\\.?\\s*',
      core=['T\\s?\\s?HE(?:SE)?\\s+United\\s+States\\s+having\\s+been\\s+driven\\s+into\\s+this\\s+just'],
      first='Congress, 18 March 1780: resolutions on the currency.',
      what="Congress's resolutions of 18 March",
      printings=[k('PP', '03-28', 1), k('NJG', '03-29', 3), k('CC', '04-04', 3), k('NHG', '04-08', 2), k('VG', '04-08', 5),
                 k('NYG', '04-10', 2)]),
 dict(id='limerick-rejoicing-at-lord-north-order-december-1779', kind='message_group',
      label="Limerick, 20 December 1779: rejoicing 'in consequence of an order from Lord North' on the trade of Ireland",
      definition="Printings of a paragraph from Limerick, 20 December 1779: 'Last Friday, in consequence of an order from Lord North, there was a scene of rejoicing in this city ...'; bells, the Limerick volunteers firing three rounds; part of the news of Ireland's free trade. A report from an Irish paper.",
      role='report', words=50, dateline=True,
      head='L\\s?IMERICK,?\\s+Dec(?:ember|\\.)?\\s+20(?:th)?\\.?,?\\s*',
      core=['L\\s?AST\\s+Friday,?\\s+in\\s+consequence\\s+of\\s+an\\s+order\\s+from\\s+Lord\\s+North'],
      first="Limerick, 20 December 1779: rejoicing at Lord North's order.",
      what='the Limerick paragraph',
      printings=[k('PP', '04-08', 4), k('NJG', '04-12', 2), k('NYG', '04-17', 2), k('NHG', '04-22', 2), k('CC', '04-25', 1)]),
 dict(id='jonathan-williams-letter-to-merchants-who-remit-bills-of-exchange-nantes-8-february-1780', kind='document_group',
      label='Jonathan Williams at Nantes, 8 February 1780, to the merchants and others in America who remit bills of exchange to Europe',
      definition="Printings of a letter of Jonathan Williams, at Nantes, 8 February 1780, 'To the gentlemen merchants and other persons in America, who remit bills of exchange to Europe': 'Of the many bills which have been sent from America to me, few whole sets have arrived ...'; how bills should be endorsed and sent; 'Every Printer on the continent is requested to insert this Letter'. The writer's own notice.",
      role='published_document', words=50, dateline=False,
      head='(?:T\\s?O\\s+the\\s+(?:G\\s?entlemen,?\\s+)?[Mm]erchants[^.]{0,140}\\.\\s*)?(?:G\\s?entlemen,?\\s*)?(?:\\S{2,12},?\\s+Feb(?:ruary|\\.)?\\s+8(?:th)?,?\\s+1780\\.?\\s*)?(?:G\\s?entlemen,?\\s*)?',
      core=['O\\s?F\\s+the\\s+many\\s+bills\\s+which\\s+have\\s+been\\s+sent\\s+from\\s+America'],
      first='Jonathan Williams, Nantes, 8 February 1780: how to send bills of exchange.',
      what="Jonathan Williams's letter",
      printings=[k('CC', '05-09', 2), k('NHG', '05-13', 3), k('NYG', '05-15', 2), k('PP', '05-16', 2), k('NJG', '05-24', 2),
                 k('VG', '06-14', 2)]),
 dict(id='britain-and-the-states-general-1780', kind='context_group',
      label="Britain and the States General, 1780: Sir Joseph Yorke's memorial and the Order in Council of 17 April",
      children=['hague-23-march-1780-sir-joseph-yorke-memorial-to-the-states-general', 'order-in-council-on-the-states-general-17-april-1780'],
      definition="The Hague paragraph on Sir Joseph Yorke's memorial of 21 March 1780 to the States General and the King's Order in Council of 17 April suspending the treaties with the United Provinces, as the papers printed them. Each counted by its own words. Contains those two groups."),
 dict(id='hague-23-march-1780-sir-joseph-yorke-memorial-to-the-states-general', parent='britain-and-the-states-general-1780', kind='message_group',
      label="The Hague, 23 March 1780: Sir Joseph Yorke's memorial to the States General of 21 March",
      definition="Printings of a paragraph from the Hague, 23 March 1780, as Rivington's Royal Gazette printed it from the Carteret packet: 'Sir Joseph Yorke, Ambassador Extraordinary from his Britannic Majesty, presented a memorial to the States-General on the 21st inst. which, after a recapitulation of many matters ... concludes thus: His Majesty has ordered the under-written, to declare ...'. The British ambassador's memorial, as the paragraph gives it.",
      role='report', words=50, dateline=False,
      head='H\\s?\\s?A\\s?\\s?G\\s?\\s?U\\s?\\s?E,?\\s+March\\s+23\\.?\\s*',
      core=['S\\s?IR\\s+Joseph\\s+Yorke,?\\s+Ambassador\\s+Extraordinary'],
      first="The Hague, 23 March 1780: Sir Joseph Yorke's memorial.",
      what="the Hague paragraph on Sir Joseph Yorke's memorial",
      printings=[k('NYG', '05-29', 1), k('PP', '05-30', 2), k('NJG', '06-07', 1), k('VG', '06-14', 2), k('NHG', '06-24', 1)]),
 dict(id='order-in-council-on-the-states-general-17-april-1780', parent='britain-and-the-states-general-1780', kind='document_group',
      label="The King's Order in Council, St. James's, 17 April 1780, on the States General's failure to furnish the succours stipulated by treaty",
      definition="Printings of the Order of the King in Council of 17 April 1780, from the London Gazette: 'Whereas since the commencement of the war in which Great-Britain is engaged by the unprovoked aggression of France and Spain, repeated memorials have been presented by his Majesty's Ambassador to the States General of the United Provinces, demanding the succours stipulated by treaty ...'; the treaties' stipulations in favour of the Dutch suspended. The British government's own order.",
      role='published_document', words=55, dateline=False,
      head='(?:A\\s?T\\s+the\\s+C\\s?OURT\\s+(?:of|at)\\s+S\\s?T\\.?\\s+J\\s?AMES.?S,?\\s+(?:the\\s+)?(?:17(?:th)?\\s+of\\s+April|April\\s+17),?\\s+1780[.:,]?\\s*)?P\\s?\\s?R\\s?\\s?E\\s?\\s?S\\s?\\s?E\\s?\\s?N\\s?\\s?T[,.]?\\s+(?:W\\s+)?(?:[Tt]he|Her)\\s+(?:K\\s?ING.?S|majesty.?s)\\s+[Mm]ost\\s+[Ee]xcellent\\s+M\\s?AJESTY\\s+in\\s+C\\s?OUNCIL\\.?\\s*',
      core=['(?:W\\s?HEREAS|Hereby)\\s+since\\s+the\\s+commencement\\s+of\\s+the\\s+war\\s+in\\s+which\\s+Great[\\s-]*Britain'],
      first='The Order in Council of 17 April 1780 on the States General.',
      what='the Order in Council of 17 April',
      printings=[k('NYG', '07-03', 2), k('PP', '07-11', 2), k('NJG', '07-19', 2), k('CC', '07-25', 2), k('NHG', '07-29', 2),
                 k('VG', '08-02', 1)]),
 dict(id='papers-of-the-capitulation-of-charlestown-may-1780', kind='document_group',
      label="The papers of the capitulation of Charlestown, April-May 1780, with General Lincoln's letter to Congress of 24 May",
      definition="Printings of the papers of the siege and capitulation of Charlestown: the summons of Sir Henry Clinton and Admiral Arbuthnot of 10 April and General Lincoln's answers, their letters of 19 April to 11 May, and the articles of capitulation, with General Lincoln's letter to Congress, Charlestown, 24 May 1780: 'The enclosed papers will inform Congress of each important circumstance which has occurred in this department ...' (the Virginia Gazette prints the papers without his letter, under 'Copies of letters, and articles of capitulation'; one item, X-1810-01). The commanders' own letters and articles.",
      role='published_document', words=55, dateline=False,
      head='C\\s?HARLES[\\s-]*T\\s?OWN,?\\s+May\\s+24,?\\s+1780\\.?\\s*(?:["“]?\\s*S\\s?\\s?I\\s?\\s?R[,.]?\\s*["“]?\\s*)?',
      core=['T\\s?HE\\s+[ei]nclosed\\s+papers\\s+will\\s+inform\\s+Congress', 'C\\s?OPIES\\s+of\\s+L\\s?ETTERS,?\\s+(?:and|&)\\s+A\\s?RTICLES\\s+of\\s+C\\s?APITULATION'],
      first="The capitulation of Charlestown: the papers, with General Lincoln's letter of 24 May.",
      what='the papers of the capitulation',
      printings=[k('VG', '06-07', 2), k('PP', '06-17', 1), k('NYG', '06-26', 2), k('NJG', '06-28', 1), k('NHG', '06-24', 3),
                 k('CC', '07-04', 1)]),
 dict(id='boston-june-1780-brig-from-cork-taken-by-the-hermione', kind='message_group',
      label='Boston, June 1780: a brig from Cork for New York, taken by the French frigate Hermione, arrives at Dartmouth',
      definition="Printings of a Boston paragraph of June 1780: 'Monday last arrived at Dartmouth, a brig bound from Cork to New York, taken by his Most Christian Majesty's frigate La Hermoine [the Hermione], commanded by the Chevalier de la Touche; her cargo consists of ... butter, ... candles, and ... soap'. A report of a prize.",
      role='report', words=50, dateline=True,
      core=['(?:M\\s?ONDAY\\s+last\\s+)?arrived\\s+at\\s+Dartmouth,?\\s+a\\s+brig\\s+bound\\s+from\\s+Cork'],
      first='Boston, June 1780: a brig taken by the Hermione.',
      what="the Boston paragraph on the Hermione's prize",
      printings=[k('NHG', '06-10', 3), k('CC', '06-13', 3), k('PP', '06-24', 2), k('NJG', '06-28', 3), k('VG', '07-12', 2)]),
 dict(id='the-crisis-number-ix-1780', kind='document_group',
      label="The Crisis, Number IX: 'Had America pursued her advantages with half the spirit she resisted her misfortunes'",
      definition="Printings of The Crisis, Number IX (by the author of Common Sense, June 1780): 'Had America pursued her advantages with half the spirit she resisted her misfortunes, she would, before now, have been a conquering and a peaceful people ...'. An essay, its author's argument.",
      role='published_document', words=50, dateline=False,
      head='(?:T\\s?HE\\s+)?(?:A\\s?MERICAN\\s+)?C\\s?RISIS,?\\s+N(?:o|umber|º)\\.?\\s+(?:IX|9)\\.?\\s*',
      core=['(?:H\\s?\\s?)?AD\\s+A\\s?MERICA\\s+pursued\\s+her\\s+advantages'],
      first='The Crisis, Number IX, June 1780.',
      what='The Crisis, Number IX',
      printings=[k('PP', '06-10', 2), k('PP', '06-13', 2), k('NJG', '06-21', 1), k('CC', '06-27', 2), k('NHG', '07-08', 1),
                 k('VG', '07-19', 1)]),
 dict(id='letter-from-near-morristown-9-june-1780-the-enemy-at-elizabethtown', kind='message_group',
      label='A letter from near Morristown, 9 June 1780: the British incursion from Elizabethtown',
      definition="Printings of an extract of a letter from 'an intelligent gentleman in the neighbourhood of Morristown', 9 June 1780: 'Although extremely fatigued, I catch a moment to inform you that I have just returned from Elizabeth-Town, where I have been reconnoitring the enemy's situation and strength ...'; the letter goes on to the burning of Connecticut Farms and General Washington drawing the army back above Springfield. The New-Hampshire Gazette prints only the later part of the letter and is not counted (C-06). A private letter: the writer's account.",
      role='report', words=50, dateline=False,
      head='(?:E\\s?XTRACT|E\\s?XCERPT)\\s+of\\s+a\\s+letter\\s+from\\s+an\\s+intelligent\\s+[Gg]entlem[ae]n[^"“]{0,140}',
      core=['A\\s?LTHOUGH\\s+extremely\\s+fatigued,?\\s+I\\s+catch\\s+a\\s+moment'],
      first='A letter from near Morristown, 9 June 1780.',
      what='the letter from near Morristown',
      printings=[k('PP', '06-13', 3), k('NJG', '06-21', 4), k('CC', '06-27', 3), k('VG', '06-28', 2)]),
 dict(id='the-french-fleet-and-army-for-america-1780', kind='context_group',
      label="The French fleet and army for America, 1780: news of its sailing, and General Washington's orders on its arrival",
      children=['boston-29-june-1780-the-french-fleet-sailed-from-brest', 'washington-general-orders-20-july-1780-on-the-arrival-of-the-french'],
      definition="A Boston paragraph of 29 June 1780 that the French fleet with 12,000 troops had sailed from Brest, and General Washington's general orders of 20 July on its arrival at Rhode Island, as the papers printed them. Each counted by its own words. Contains those two groups."),
 dict(id='boston-29-june-1780-the-french-fleet-sailed-from-brest', parent='the-french-fleet-and-army-for-america-1780', kind='message_group',
      label='Boston, 29 June 1780: letters by a vessel from Bilbao, that the French fleet bound to America sailed from Brest on 23 April',
      definition="Printings of a Boston paragraph of 29 June 1780: 'A vessel is arrived from Bilboa ... who brought letters which mention that the French fleet bound to America, with 12,000 troops, sailed from Brest the 23d of April. Also that a large Spanish fleet ... sailed from Cadiz the 27th'. A report at second hand.",
      role='report', words=50, dateline=True,
      core=['A\\s+vessel\\s+is\\s+arrived\\s+from\\s+Bilb\\w+'],
      stop='T\\s?wo\\s+vessels\\s+laden\\s+with\\s+salt',
      first='Boston, 29 June 1780: the French fleet sailed from Brest.',
      what='the Boston paragraph of 29 June',
      printings=[k('NHG', '07-01', 2), k('CC', '07-04', 3), k('PP', '07-13', 2), k('NYG', '07-17', 2), k('NJG', '07-19', 2)]),
 dict(id='washington-general-orders-20-july-1780-on-the-arrival-of-the-french', parent='the-french-fleet-and-army-for-america-1780', kind='document_group',
      label="General Washington's general orders, 20 July 1780, congratulating the army on the arrival of the French fleet and army",
      definition="Printings of General Washington's general orders of 20 July 1780: 'The Commander in Chief has the pleasure to congratulate the army on the arrival of a large land and naval armament at Rhode Island, sent by his Most Christian Majesty ...'; black and white cockades recommended, 'emblematic of the expected union of the two armies'. Printed with two introductions (C-02). The commander's own orders.",
      role='published_document', words=50, dateline=False,
      head="(?:E\\s?XTRACT\\s+(?:from|of)\\s+(?:the\\s+)?G\\s?ENERAL\\s+O\\s?RDERS[.,:;]?\\s*)?H\\s?EAD[\\s-]*Q\\s?UARTERS,?\\s+(?:[A-Z][\\w\\']{3,14},?\\s+)?July\\s+20,?\\s+1780\\.?\\s*",
      core=['T\\s?HE\\s+Commander\\s+in\\s+Chief\\s+has\\s+the\\s+pleasure'],
      first="General Washington's general orders of 20 July 1780 on the French arrival.",
      what="General Washington's general orders of 20 July",
      printings=[k('NHG', '08-05', 3), k('CC', '08-15', 2), k('NYG', '08-28', 2), k('NJG', '08-30', 2), k('NHG', '09-16', 2)]),
 dict(id='declaration-of-the-empress-of-russia-on-neutral-commerce-1780', kind='document_group',
      label='The declaration of the Empress of Russia to the Courts of London, Versailles and Madrid on the rights of neutral commerce',
      definition="Printings of the declaration of the Empress of Russia to the Courts of London, Versailles and Madrid (1780): 'The Empress of all the Russias has so fully manifested her sentiments of equity and moderation ... of the regard she has for the rights of neutrality and the liberty of universal commerce ...'; the principles of neutral navigation. The Empress's own declaration.",
      role='published_document', words=55, dateline=False,
      head='(?:(?:[Tt]he\\s+following\\s+is\\s+)?a\\s+[Dd]eclaration\\s+(?:from|of)\\s+the\\s+Empress\\s+of\\s+(?:all\\s+the\\s+)?Russia[^"“]{0,120}|D\\s?ECLARATION\\s+from\\s+the\\s+E\\s?MPRESS\\s+of\\s+R\\s?USSIA\\s+to\\s+the\\s+C\\s?OURTS\\s+of\\s+L\\s?ONDON,?\\s+V\\s?ERSAILLES,?\\s+and\\s+M\\s?ADRID\\.?\\s*)',
      core=['T\\s?HE\\s+Empress\\s+of\\s+all\\s+the\\s+Russias\\s+has\\s+so\\s+fully\\s+manifested'],
      first="The Empress of Russia's declaration on neutral commerce, 1780.",
      what="the Empress of Russia's declaration",
      printings=[k('NYG', '07-03', 2), k('PP', '07-11', 2), k('CC', '07-25', 2), k('NJG', '08-02', 1), k('VG', '08-02', 1)]),
 dict(id='washington-letter-to-congress-26-july-1780-bergen-neck', kind='document_group',
      label='General Washington to Congress, Bergen County, 26 July 1780: General Wayne sent to Bergen Neck for the cattle; the blockhouse',
      definition="Printings of General Washington's letter to Congress, Head Quarters, Bergen County, 26 July 1780: 'Having received information that there were considerable numbers of cattle and horses in Bergen Neck, within reach of the enemy ... I detached Brigadier General Wayne, on the 20th, with the first and second Pennsylvania brigades ...'. The commander's own letter.",
      role='published_document', words=50, dateline=False,
      head='H\\s?EAD[\\s-]*Q\\s?UARTERS,?\\s+\\(?Bergen\\s+County\\)?,?\\s+July\\s+26(?:,?\\s+1780)?\\.?\\s*(?:["“]?\\s*S\\s?\\s?I\\s?\\s?R[,.]?\\s*["“]?\\s*)?',
      core=['H\\s?AVING\\s+received\\s+information\\s+that\\s+there\\s+were\\s+considerable\\s+numbers\\s+of\\s+cattle'],
      first='General Washington to Congress, 26 July 1780: Bergen Neck.',
      what="General Washington's letter of 26 July",
      printings=[k('PP', '08-01', 3), k('NJG', '08-09', 4), k('NYG', '08-14', 3), k('NHG', '08-19', 2)]),
 dict(id='london-8-june-1780-the-riots', kind='message_group',
      label="London, 8 June 1780: accounts of the riots (houses burnt; Lord Mansfield's house destroyed)",
      definition="Printings of a London paragraph of 8 June 1780: 'Justice Wilmot's house and office, and a house in Moor-Fields were burnt, and several other houses pillaged and all the goods burnt. Lord North's house was also about to be attacked ...'; the riots in London that June. A London report.",
      role='report', words=50, dateline=True,
      core=['J\\s?USTICE\\s+W\\s?ILMOT.?S\\s+house\\s+and\\s+office'],
      first='London, 8 June 1780: the riots.',
      what='the London paragraph of 8 June',
      printings=[k('PP', '08-26', 3), k('NJG', '08-30', 1), k('CC', '09-05', 2), k('VG', '09-13', 1)]),
 dict(id='gates-letter-to-congress-20-august-1780-the-defeat-near-camden', kind='document_group',
      label="General Gates to Congress, Hillsborough, 20 August 1780, on 'the defeat of the troops under my command' near Camden",
      definition="Printings of General Gates's letter to the President of Congress, Hillsborough, 20 August 1780: 'In the deepest distress and anxiety of mind, I am obliged to acquaint your Excellency with the defeat of the troops under my command ...', with Colonel Sumter's letter to him of 15 August; published by order of Congress. The commander's own letter.",
      role='published_document', words=55, dateline=False,
      head='(?:E\\s?XTRACT|C\\s?OPY)\\s+of\\s+a\\s+[Ll]etter\\s+from\\s+(?:Major[\\s-]*)?Gen(?:eral|\\.)\\s+G\\s?ATES,?\\s+to\\s+the\\s+President\\s+of\\s+(?:the\\s+)?Congress,?\\s+dated\\s+Hillsborough,?\\s+Aug(?:ust|\\.)?\\s+2[06],?\\s+1780\\.?\\s*(?:["“]?\\s*S\\s?\\s?I\\s?\\s?R[,.]?\\s*["“]?\\s*)?',
      core=['I\\s?N\\s+the\\s+deepest\\s+distress\\s+and\\s+anxiety\\s+of\\s+mind'],
      first='General Gates to Congress, 20 August 1780: the defeat near Camden.',
      what="General Gates's letter of 20 August",
      printings=[k('PP', '09-12', 3), k('NJG', '09-13', 2), k('NYG', '09-25', 2), k('CC', '09-26', 2), k('NHG', '09-30', 2)]),
 dict(id='congress-resolutions-on-the-memorial-of-the-general-officers-august-1780', kind='document_group',
      label='Congress, 10 and 24 August 1780: resolutions on the memorial of the general officers (lands, pay and rations)',
      definition="Printings of Congress's resolutions of 10 and 24 August 1780 on the memorial of the general officers: 'Congress took into consideration the report of the Committee on the memorial of the general officers; whereupon, Resolved, That the said general officers be informed, that Congress have at no time been unmindful of the military virtues ...'; grants of land extended to general officers, two months' pay, rations. Congress's own resolutions.",
      role='published_document', words=55, dateline=False,
      head='I\\s?N\\s+C\\s?ONGRESS,?\\s+Aug(?:ust|\\.)?\\s+10,?\\s+1780\\.?\\s*',
      core=['C\\s?ONGRESS\\s+took\\s+into\\s+consideration\\s+the\\s+report\\s+of\\s+the\\s+[Cc]ommittee\\s+on\\s+the\\s+memorial'],
      first='Congress, August 1780: the memorial of the general officers.',
      what="Congress's resolutions of 10 and 24 August",
      printings=[k('PP', '09-19', 3), k('NJG', '09-27', 2), k('NYG', '10-02', 3), k('CC', '10-03', 2), k('NHG', '10-21', 4)]),
 dict(id='general-arnold-september-november-1780', kind='context_group',
      label="General Arnold, September-November 1780: his letter to General Washington, and Congress's resolutions",
      children=['arnold-letter-to-washington-on-board-the-vulture-25-september-1780', 'congress-4-october-1780-arnold-name-erased-and-3-november-the-captors-of-andre'],
      definition="General Arnold's letter to General Washington from the Vulture, 25 September 1780, and Congress's resolutions of 4 October and 3 November (his name erased from the register; the militiamen who intercepted Major Andre rewarded), as the papers printed them. Each counted by its own words. Contains those two groups."),
 dict(id='arnold-letter-to-washington-on-board-the-vulture-25-september-1780', parent='general-arnold-september-november-1780', kind='document_group',
      label='General Arnold to General Washington, on board the Vulture, 25 September 1780',
      definition="Printings of General Arnold's letter to General Washington, on board the Vulture, 25 September 1780: 'The heart which is conscious of its own rectitude, cannot attempt to palliate a step which the world may censure as wrong ...'; he asks protection for Mrs. Arnold. The papers' headings ('Arnold's infamous letter') are their own. The writer's own letter.",
      role='published_document', words=50, dateline=False,
      head='O\\s?N\\s+board\\s+the\\s+Vulture\\s*,?\\s+Sept(?:ember|\\.)?\\s+25,?\\s+1780\\.?\\s*(?:["“]?\\s*S\\s?\\s?I\\s?\\s?R[,.]?\\s*["“]?\\s*)?',
      core=['T\\s?\\s?H\\s?\\s?E\\s+heart\\s+which\\s+is\\s+conscious\\s+of\\s+its\\s+own\\s+rectitude'],
      first='General Arnold to General Washington, 25 September 1780.',
      what="General Arnold's letter of 25 September",
      printings=[k('PP', '10-03', 2), k('NJG', '10-11', 3), k('CC', '10-17', 2), k('VG', '10-18', 1), k('NHG', '10-21', 2)]),
 dict(id='congress-4-october-1780-arnold-name-erased-and-3-november-the-captors-of-andre', parent='general-arnold-september-november-1780', kind='document_group',
      label="Congress, 4 October 1780: Benedict Arnold's name erased from the register of officers; 3 November: thanks to the three militiamen who intercepted Major Andre",
      definition="Printings of Congress's resolutions of 4 October 1780, 'That the board of war be and hereby are directed to erase from the register of the names of the officers of the army of the United States the name of Benedict Arnold', and of 3 November, giving thanks, a silver medal and a pension to each of the three young militiamen of New York who intercepted Major Andre (X-1780-03: the excerpts end before their names). Congress's own resolutions.",
      role='published_document', words=45, dateline=False,
      head='I\\s?N\\s+C\\s?ONGRESS,?\\s+Oct(?:ober|\\.)?\\s+4(?:,?\\s+1780)?\\.?\\s*',
      core=['R\\s?ESOLVED\\s*,?\\s+[Tt]hat\\s+the\\s+[Bb]oard\\s+of\\s+[Ww]ar\\s+be,?\\s+and\\s+(?:they\\s+)?(?:are\\s+)?here\\s?by\\s+(?:are\\s+)?directed\\s+to\\s+(?:erase|make)'],
      stop='N\\s?OV(?:EMBER|\\.)\\s+3\\.?,?\\s*W\\s?HEREAS',
      first='Congress, 4 October and 3 November 1780: Arnold; the captors of Major Andre.',
      what="Congress's resolutions of 4 October and 3 November",
      printings=[k('PP', '11-14', 2), k('NJG', '11-22', 1), k('VG', '11-25', 2), k('CC', '11-28', 3), k('NHG', '12-04', 3)]),
 dict(id='jefferson-letter-to-congress-15-october-1780-with-dispatches-from-the-south', kind='document_group',
      label="Governor Jefferson to Congress, Richmond, 15 October 1780, with dispatches from the south (Augusta; Major Ferguson defeated at King's Mountain)",
      definition="Printings of Governor Jefferson's letter to the President of Congress, Richmond, 15 October 1780: 'I do myself the pleasure of congratulating your Excellency on the small dawn of good fortune which at length appears in the South, as you will find by the dispatches I have the honour of inclosing ...', with the letters it enclosed (an officer's letter of 2 October on Colonel Clarke at Augusta; letters on the defeat of Major Ferguson at King's Mountain). The Virginia Gazette prints the enclosed letters without the Governor's (one item, X-1810-01). The writers' own letters.",
      role='published_document', words=55, dateline=False,
      head='(?:(?:E\\s?XTRACT|C\\s?OPY)\\s+of\\s+a\\s+letter\\s+from\\s+his\\s+Excellency\\s+Governor\\s+Jefferson[^"“]{0,200}|E\\s?XTRACT\\s+of\\s+a\\s+letter\\s+from\\s+an\\s+officer\\s+of\\s+the\\s+southern\\s+army,?\\s+dated\\s+Burke\\s+county,?\\s+Oct(?:ober|\\.)?\\s+2,?\\s+1780\\.?\\s*)',
      core=['I\\s+do\\s+myself\\s+the\\s+pleasure\\s+of\\s+congratulating\\s+your\\s+Excellency\\s+on\\s+the\\s+small\\s+dawn', 'O\\s?N\\s+my\\s+crossing\\s+the\\s+Catawba\\s+river'],
      first='Governor Jefferson to Congress, 15 October 1780, with dispatches from the south.',
      what="Governor Jefferson's letter of 15 October",
      printings=[k('VG', '10-18', 2), k('PP', '10-24', 3), k('NJG', '10-25', 3), k('CC', '11-07', 4), k('NHG', '11-13', 1)]),
 dict(id='philadelphia-31-october-1780-the-privateer-holker-returns-with-prizes', kind='message_group',
      label='Philadelphia, 31 October 1780: the privateer Holker returns from a cruise with prizes bound to Charlestown',
      definition="Printings of a Philadelphia paragraph of 31 October 1780: 'On Sunday last arrived in port the privateer Holker, captain Keane, from a cruise, during which she took the following prizes, all bound to Charlestown, South-Carolina ...'; the ship Richmond struck after a smart action. A report of prizes.",
      role='report', words=50, dateline=False, back=True,
      core=['privateer\\s+Holker,?\\s+capt(?:ain|\\.)\\s+Ke\\w+'],
      stop='T\\s?hese\\s+vessels\\s+have\\s+valuable',
      first="Philadelphia, 31 October 1780: the privateer Holker's prizes.",
      what='the Philadelphia paragraph on the Holker',
      printings=[k('PP', '10-31', 3), k('NJG', '11-08', 3), k('VG', '11-11', 2), k('CC', '11-14', 3), k('NHG', '11-27', 3)]),
 dict(id='philadelphia-14-november-1780-the-enemy-force-in-virginia', kind='message_group',
      label="Philadelphia, November 1780: 'By authentic advices from Virginia', the enemy's force there of 2500 to 3000 men",
      definition="Printings of a Philadelphia paragraph of 14 November 1780: 'By authentic advices from Virginia, as late as the 7th inst. we learn, that the enemy's forces in that quarter consist of between 2500 and 3000 men; that part of them lay on board their ships in Hampton road, and the remainder at Suffolk and Portsmouth ...'. A report at second hand.",
      role='report', words=50, dateline=False,
      core=['B\\s?Y\\s+authentic\\s+advices\\s+from\\s+Virginia,?\\s+as\\s+late\\s+as'],
      stop='S\\s?ince\\s+our\\s+last\\s+arrived',
      first="Philadelphia, November 1780: the enemy's force in Virginia.",
      what='the Philadelphia paragraph on Virginia',
      printings=[k('PP', '11-14', 2), k('NJG', '11-15', 3), k('CC', '11-28', 3), k('NHG', '12-04', 3)]),
 dict(id='london-october-1780-the-warrant-committing-henry-laurens-to-the-tower', kind='message_group',
      label="A London paragraph: the warrant of the Secretaries of State, 6 October 1780, committing Henry Laurens to the Tower 'on suspicion of high treason'",
      definition="Printings of a London paragraph: 'The commitment of Mr. Laurens to the Tower of London, by the three Secretaries of State, runs thus: These are, in his Majesty's name, to authorize you to receive into your custody the person of Henry Laurens, Esq. ... on suspicion of high treason ... Dated at Whitehall, the 6th day of October, 1780'. Mr. Laurens, a former President of Congress, had been taken at sea on his way to Holland. The British warrant, as the paragraph gives it.",
      role='report', words=50, dateline=False,
      core=['T\\s?HE\\s+commitment\\s+of\\s+Mr\\.?\\s+Laurens\\s+to\\s+the\\s+Tower'],
      first='London, October 1780: Henry Laurens committed to the Tower.',
      what='the London paragraph on Mr. Laurens',
      printings=[k('NYG', '12-11', 2), k('PP', '12-12', 2), k('NJG', '12-20', 3), k('VG', '12-23', 2), k('CC', '12-26', 3)]),
 dict(id='barbados-28-october-1780-the-hurricane', kind='message_group',
      label="Bridgetown, Barbados, 28 October 1780 (from the Antigua Gazette): the account of 'the late terrible storm' of 10 October",
      definition="Printings of an account from Bridgetown, Barbados, 28 October 1780, as the Antigua Gazette Extraordinary of 7 November gave it: 'To give a full description of the late terrible storm, is not only entirely out of our power, but is we believe beyond the abilities of any human being ...'; the hurricane of 10 October. A report from a West India paper.",
      role='report', words=50, dateline=False,
      core=['T\\s?O\\s+give\\s+a\\s+full\\s+description\\s+of\\s+the\\s+late\\s+terrible\\s+storm'],
      first='Barbados, 28 October 1780: the hurricane.',
      what='the Barbados account of the hurricane',
      printings=[k('CC', '12-19', 2), k('NJG', '12-20', 4), k('VG', '12-23', 1), k('NHG', '12-25', 2)]),
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
            problems.append((s['id'], key, 'page not in the 1780 pages'))
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
        r['id'] = f'S80-{n:03}'
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
               'admission_rule': 'Reviewed 1780 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1780/'
    return {
        'ledger_id': 'ledger:stories-1780', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1780', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1780, and of 1779 where they reach the 1780 pages (long-running ones '
                   'included), counts of every item in 3 or more papers by its own opening over all 1,406 pages of 1780 in both transcriptions, '
                   'a sweep of word-for-word passages shared by 4 or more papers for short items the families miss, reading of every item that '
                   'meets the bar, and scan checks of each admitted and chosen passage, by the thin-year rule as amended (register Y-THIN, B1: '
                   'more than half of the papers that survive for the item\'s weeks, and at least 4, make an item eligible; items printed by '
                   'every paper in print are admitted, the others chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1779.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1780.py': 'ledger_code', 'work/archive_data/ledgers/stories_1780_review.json': 'scan_review',
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
