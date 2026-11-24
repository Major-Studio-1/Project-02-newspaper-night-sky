"""Write ledgers/stories_1778.json: reviewed stories of 1778, round one.

1778 is read by the thin-year rule the owner chose on 23 November 2026 (docs/rules-and-exceptions.md, Y-THIN), as amended the
same night (the owner's choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the
newspapers that survive for its weeks, and by at least 4 newspapers; digests are not. The newspapers that survive for an item's
weeks are those with an eligible issue between its first and last printing, and at least in the three weeks from its first
printing. As in R-01, the eligible items printed by every newspaper that survives for their weeks are admitted, and the other
eligible items are chosen to cover the months and the kinds of news, about as many stories as a standard year (a target, not a
quota); one affair's items are handled as in X-1800-01. Sub-stories (C-01), private persons (R-04) and the list of items read and
not admitted (R-03) apply as in every year. Counted by their own words, 76 items of 1778 are eligible; 3 are printed by every
paper that survives for their weeks; with 30 chosen, 26 stories in 38 groups are admitted (outputs/story_discovery_1778/README.md).

The automatic families first printed in 1778 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1777 over the 1778 pages
(items_from_1777.json); every item in 3 or more papers was compared by machine with every page; a sweep of passages shared word
for word by 4 or more papers found short items the families miss; every candidate was counted by its own opening over all 970
pages of 1778 in both transcriptions, and the hits were read. The 1778 pages are those whose issue the data release dates to 1778
(work/year_search_pages.py 1778 ... --printed-dates); no 1778 issue has a corrected date in the releases. 1778 has 11 catalogue
series, which are 8 papers (C-04): the Connecticut Courant under three catalogue numbers (sn82016139 to 10 February, sn82016133 on
17 February, sn84023855 from 24 February) and the Freeman's Journal, or New-Hampshire Gazette, of Portsmouth under two
(sn83025583 to 2 June, sn83025584 from 16 June); the two Williamsburg Virginia Gazettes (Dixon and Hunter's, Purdie's) are two
papers. The release's map of misfiled RevX pages (derived/revx_page_map.parquet) lists one 1778 page (the New-Hampshire Gazette of
8 September, page 3); no printing stands on it. Pages filed under dates they do not print (outputs/story_discovery_1778/README.md,
"Data issues"): one admitted printing stands on such an issue (the Freeman's Journal filed under 31 January 1778, which prints
31 March 1778); its date is the filed one until a correction release, and its note gives the printed date.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1778_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1778.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1778/search_pages.json). The excerpts are cut from
the 1778 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1778'
D = PROJECT/'outputs/story_discovery_1778'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1778_review.json'
OUT = HERE/'stories_1778.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83025471': 'The New-Jersey Gazette', 'sn83030493': 'The New-York Gazette, and the Weekly Mercury',
         'sn82016139': 'The Connecticut Courant', 'sn82016133': 'The Connecticut Courant', 'sn84023855': 'The Connecticut Courant',
         'sn83025583': "The Freeman's Journal, or New-Hampshire Gazette", 'sn83025584': 'The New-Hampshire Gazette',
         'sn83021183': 'The Newport Gazette', 'sn83021127': 'The Pennsylvania Packet',
         'sn84024739': 'The Virginia Gazette (Dixon and Hunter)', 'sn84024742': 'The Virginia Gazette (Purdie)'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, filed date (MM-DD in 1778), page and edition. The Connecticut Courant and the
    Freeman's Journal / New-Hampshire Gazette have several catalogue numbers in 1778 (C-04); the date picks it."""
    if paper == 'CC':
        lccn = 'sn82016139' if date < '02-17' else 'sn82016133' if date == '02-17' else 'sn84023855'
    elif paper == 'NHG':
        lccn = 'sn83025583' if date <= '06-02' else 'sn83025584'
    else:
        lccn = {'NJG': 'sn83025471', 'NYG': 'sn83030493', 'NPG': 'sn83021183', 'PP': 'sn83021127',
                'VGD': 'sn84024739', 'VGP': 'sn84024742'}[paper]
    return f'{lccn}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release (one page in 1778)."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()

S = r'\s+'
MARCH31 = ("Filed under 31 January 1778; the issue's first page prints 'TUESDAY MARCH, 31, 1778' and No. 42 (the issues of 3 and "
           "10 March are Nos. 38 and 39), so it is the issue of 31 March 1778.")
# Story groups. A parent ('context_group') lists its children and has no printings. 'printings' lists each printing's page;
# a tuple adds overrides for that printing: core (regexes for the item's first words), role, field, note, words, dateline
# (include a dateline directly before), head (a regex for a heading that ends directly before the core: the excerpt starts
# with it), back (start at the beginning of the sentence that holds the core), stop (a regex: the excerpt ends before it).
STORIES = [
 dict(id='civil-usage-owners-present-a-coach-to-john-hancock-january-1778', kind='document_group',
      label="Boston, 1 January 1778: the owners of the privateer Civil Usage present John Hancock with a coach taken in one of their prizes",
      definition="Printings of a Boston paragraph of 1 January 1778: 'The owners of the privateer Civil Usage, of Newbury Port, have made a present to the honourable John Hancock, Esq; of an elegant coach, which was lately taken in one of their prizes; as a token of their respect for that gentleman, who has so nobly distinguished himself in the present contest with Great-Britain'. The New-York Gazette, printed under British occupation, gives it twice in February among other Boston paragraphs. A Boston paper's report.",
      role='report', words=50, dateline=True,
      core=[r'(?:T\s?HE|The)\s+(?:O\s?WNERS|Owners|owners)\s+of\s+the\s+(?:P\s?RIVATEER|[Pp]rivateer),?\s+(?:C\s?IVIL|Civil)\s+(?:U\s?SAGE|Usage)'],
      first="Boston, 1 January 1778: the owners of the privateer Civil Usage present John Hancock with a coach taken in one of their prizes.",
      what='the Boston paragraph on the coach given to John Hancock',
      printings=[(k('CC', '01-06', 3), {'head': 'B\\s?O\\s?S\\s?T\\s?O\\s?N,?\\s+January\\s+1,?\\s+1778\\.?\\s*'}), k('NHG', '01-06', 2), k('PP', '01-14', 2), (k('NJG', '01-21', 2), {'head': 'Jan\\.?\\s+1\\.\\s*'}),
                 k('NYG', '02-02', 2), (k('NYG', '02-09', 2), {'note': 'Printed again.'})]),
 dict(id='congress-on-provisions-for-prisoners-19-december-1777', kind='document_group',
      label="Congress, 19 December 1777: accounts for provisions supplied to prisoners to be discharged in kind or in gold and silver before any release",
      definition="Printings of the resolutions of Congress of 19 December 1777: 'Whereas Sir William Howe, Commander in Chief of his Britannic Majesty's forces, has required, that provisions should be sent in for the subsistence of the American prisoners in his possession, ... and has prohibited the circulation of the money struck by the authority of these States'; it resolves that the accounts of all provisions and other necessaries supplied by the public to prisoners in the power of these States shall be discharged in provisions of equal quality and kind, or in gold and silver at four shillings and six pence sterling for every dollar, before the release of any prisoners. The resolutions of Congress, as the papers printed them.",
      role='published_document', words=55, dateline=False,
      head=r'I\s?N\s+C\s?O\s?N\s?G\s?R\s?E\s?S\s?S,?\s+December\s+19,?\s+1777\.?\s*',
      core=[r'(?:W\s?HEREAS|Whereas|\S{0,4}HEREAS)\s+Sir\s+Will\w+\s+Howe,?\s+[Cc]om\S*\s*(?:der|in)'],
      first="Congress, 19 December 1777: the accounts for provisions supplied to prisoners in the power of these States to be discharged before any prisoners are released.",
      what="the resolutions of Congress of 19 December 1777 on provisions for prisoners",
      printings=[k('PP', '01-28', 5), k('NJG', '02-11', 1),
                 (k('NYG', '03-09', 2), {'field': CA, 'note': 'RevX lacks the opening of this item on this page, so the excerpt comes from the older CA transcription.'}),
                 k('NHG', '03-10', 1)]),
 dict(id='house-of-lords-debate-on-the-address-20-november-1777', kind='document_group',
      label="House of Lords, 20 November 1777: the debate on the address of thanks for the King's speech, as a London account printed it",
      definition="Printings of a London account of the debate in the House of Lords on 20 November 1777, at the opening of the session: 'As soon as his Majesty had left the House, the Earl of Harcourt and Lord Percy were introduced, and took their seats; the Lord Chancellor then read his Majesty's speech'; Lord Percy moved an address of thanks, Lord Coventry opposed it and recommended withdrawing the troops from America, and the account goes on with the Earl of Chatham's amendment and the Earl of Sandwich's reply. The Newport Gazette prints it from papers brought by the ship Tom from Liverpool. A London account of the debate, with the speakers' words as reported.",
      role='report', words=50, dateline=False,
      head=r'(?:H\s?OUSE\s+OF\s+L\s?ORDS\.?\s*(?:T\s?HURSDAY|Thursday),?\s+(?:N\s?OVEMBER|November)\s+20\.?\s*)',
      core=[r'(?:A\s?S|As)\s+soon\s+as\s+his\s+Majesty\s+had\s+left\s+the\s+House'],
      first="House of Lords, 20 November 1777: a London account of the debate on the address of thanks, with the Earl of Chatham's amendment.",
      what="the London account of the debate in the House of Lords of 20 November 1777",
      printings=[k('NPG', '02-12', 1), k('CC', '02-24', 1), (k('PP', '03-09', 1), {'head': 'H\\s?O\\s?U\\s?S\\s?E\\s+o\\s?f\\s+L\\s?O\\s?R\\s?D\\s?S\\.?\\s*THURSDAY,?\\s+November\\s+20\\.?\\s*'}), k('NJG', '03-11', 1)]),
 dict(id='washington-address-to-the-inhabitants-on-cattle-for-the-army-february-1778', kind='document_group',
      label="General Washington's address to the inhabitants of New Jersey, Pennsylvania, Maryland and Virginia, February 1778: cattle to be fattened for the army",
      definition="Printings of the address 'To the Inhabitants of New-Jersey, Pennsylvania, Maryland and Virginia. Friends, Countrymen and Fellow Citizens! After three campaigns, during which the brave subjects of these States have contended, not unsuccessfully, with one of the most powerful kingdoms on earth, we now find ourselves at least upon a level with our opponents'; it recommends that the inhabitants put up and feed as many of their stock-cattle as they can spare, so that they may be driven to the army in May, June and July, and promises a bounty. General Washington's own address, from headquarters at Valley Forge, as the papers printed it from the New-Jersey Gazette of 25 February.",
      role='published_document', words=50, dateline=True,
      core=[r'(?:T\s?O|To)\s+the\s+(?:I\s?NHABITANTS|[Ii]nhabitants)\s+of\s+(?:N\s?EW|New)[\s\-]+(?:J\s?ERSEY|Jersey)'],
      first="General Washington's address to the inhabitants of New Jersey, Pennsylvania, Maryland and Virginia: cattle to be put up and fed for the army.",
      what="General Washington's address to the inhabitants",
      printings=[k('NJG', '02-25', 2), k('PP', '03-04', 1), k('CC', '03-17', 1), (k('NHG', '01-31', 1), {'note': MARCH31})]),
 dict(id='congress-on-the-exchange-of-prisoners-26-february-1778', kind='document_group',
      label="Congress, 26 February 1778: the propositions on an exchange of prisoners that General Washington accepted from General Howe",
      definition="Printings of the resolutions of Congress of 26 February 1778: 'Whereas it appears to Congress by the copy of a letter from General Washington to General Howe of the 10th of this month, that he has consented to the propositions of General Howe to the following effect, \"That an exchange of all prisoners now in our possession, officer for officer, soldier for soldier, and citizen for citizen, so far as number and rank will apply\"'; since its resolution of 19 December requires the accounts for prisoners' provisions to be settled before any release, it asks the states for their accounts of what they have supplied to prisoners. The resolutions of Congress, as the papers printed them from York-Town.",
      role='published_document', words=55, dateline=False,
      head=r'(?:I\s?N\s+C\s?O\s?N\s?G\s?R\s?E\s?S\s?S,?\s+(?:February|Feb\.?)\s+26,?\s+1778\.?\s*)',
      core=[r'(?:W\s?HEREAS|Whereas)\s+it\s+appears\s+to\s+Congress,?\s+by\s+the\s+copy\s+of\s+a\s+letter'],
      first="Congress, 26 February 1778: General Washington's consent to General Howe's propositions for an exchange of prisoners, and Congress's conditions.",
      what="the resolutions of Congress of 26 February 1778 on the exchange of prisoners",
      printings=[k('PP', '03-04', 2), k('NJG', '03-11', 3), k('NYG', '03-23', 2), k('NPG', '04-16', 3)]),
 dict(id='shreve-party-at-billingsport-april-1778', kind='document_group',
      label="Trenton, April 1778: Colonel Shreve's party and the militia against the Tories fortified at Billingsport",
      definition="Printings of a Trenton paragraph of April 1778: 'We hear that on Saturday morning last, Colonel Shreve, who commands the second Jersey regiment, sent a party of men under Major Howel to join some of the Salem and Cumberland militia, in order to invest Billingsfort, where about 150 Tories had been intrenching and fortifying themselves'. The New-Jersey Gazette's report, at second hand ('We hear').",
      role='report', words=50, dateline=True,
      core=[r'(?:W\s?E|We)\s+hear\s+that\s+on\s+Saturday\s+morning\s+last,?\s+Col(?:onel|\.)?\s+Shreve'],
      first="Trenton, April 1778: Colonel Shreve's party sent with the Salem and Cumberland militia against the Tories fortified at Billingsport.",
      what="the Trenton paragraph on Colonel Shreve's party",
      printings=[k('NJG', '04-08', 3), k('PP', '04-15', 2), k('NYG', '04-20', 2), k('NPG', '04-30', 2)]),
 dict(id='lord-norths-conciliatory-bills-and-congress-april-1778', kind='context_group',
      label="Lord North's conciliatory bills and Congress's answer, as the papers printed them in April and May 1778",
      children=['draught-of-a-bill-declaring-the-intentions-of-parliament-on-taxation-1778',
                'draught-of-a-bill-to-appoint-commissioners-1778',
                'congress-report-on-the-draught-bills-22-april-1778'],
      definition="The two bills that Lord North brought into the House of Commons in February 1778, as copies printed in New York reached the papers in April (the New-York Gazette heads them 'Copies of two bills presented and read in the House of Commons, on the 19th of February last'), and Congress's report of 22 April 1778 on 'a certain printed paper sent from Philadelphia, purporting to be the draught of a bill'. Contains those three groups."),
 dict(id='draught-of-a-bill-declaring-the-intentions-of-parliament-on-taxation-1778', parent='lord-norths-conciliatory-bills-and-congress-april-1778', kind='document_group',
      label="The draught of a bill for declaring the intentions of the Parliament of Great Britain concerning the exercise of the right of imposing taxes in the colonies",
      definition="Printings of the draught of the first of Lord North's two bills: 'A Bill for declaring the intentions of the Parliament of Great-Britain, concerning the exercise of the right of imposing taxes within his Majesty's colonies, provinces and plantations in North-America'; it declares that Parliament will impose no duty, tax or assessment payable in the colonies, except duties for the regulation of commerce, whose net produce is to be paid and applied for the use of the colony where it is levied. The New-York Gazette prints it in three issues; American papers print it with Congress's report on it. The British government's draught bill, as printed in America.",
      role='published_document', words=45, dateline=False,
      head=r'(?:No\.?\s*I\.?\s*Copy\s+of\s+a\s+|D\s?RA(?:U\s?)?G?H?F?T\s+(?:of|OF)\s+(?:a|A)\s+)',
      core=[r'B\s?ILL,?\s+(?:F\s?OR|[Ff]or)\s+(?:D\s?ECLARING|declaring)\s+the\s+(?:I\s?NTENTIONS|[Ii]ntentions)\s+of\s+(?:the\s+)?(?:P\s?ARLIAMENT|Parliament)'],
      first="The draught of Lord North's bill declaring that Parliament will not impose taxes in the colonies except duties for the regulation of commerce.",
      what="the draught bill on taxation",
      printings=[k('NYG', '04-20', 1), k('NPG', '04-23', 2), (k('NYG', '04-27', 1), {'note': 'Printed again.'}), k('NJG', '04-29', 3),
                 (k('NYG', '05-04', 1), {'note': 'Printed again.'}), k('CC', '05-05', 1), k('VGD', '05-08', 2)]),
 dict(id='draught-of-a-bill-to-appoint-commissioners-1778', parent='lord-norths-conciliatory-bills-and-congress-april-1778', kind='document_group',
      label="The draught of a bill to enable the King to appoint commissioners to treat, consult and agree upon the means of quieting the disorders in the colonies",
      definition="Printings of the draught of the second of Lord North's two bills: 'A Bill to enable his Majesty to appoint Commissioners, with sufficient powers to treat, consult, and agree upon the means of quieting the disorders now subsisting in certain of the colonies, plantations, and provinces of North-America'; the commissioners may treat, consult and agree 'with such body or bodies political and corporate, or with such assembly or assemblies of men, or with such person or persons, as in their wisdom and discretion they shall think meet', suspend the act prohibiting trade with the colonies, and appoint governors. The New-York Gazette prints it in three issues; American papers print it with Congress's report on it. The British government's draught bill, as printed in America.",
      role='published_document', words=45, dateline=False,
      head=r'(?:No\.?\s*II\.?\s*Copy\s+of\s+a\s+|D\s?RA(?:U\s?)?G?H?F?T\s+(?:of|OF)\s+(?:a|A)\s+)',
      core=[r'B\s?ILL\s+(?:T\s?O|to)\s+(?:E\s?NABLE|enable)\s+his\s+(?:M\s?AJESTY|Majesty)\s+to\s+(?:A\s?PPOINT|appoint)'],
      first="The draught of Lord North's bill enabling the King to appoint commissioners to treat for quieting the disorders in the colonies.",
      what="the draught bill to appoint commissioners",
      printings=[k('NYG', '04-20', 1), k('NPG', '04-23', 3), (k('NYG', '04-27', 1), {'note': 'Printed again.'}), k('NJG', '04-29', 3),
                 (k('NYG', '05-04', 1), {'note': 'Printed again.'}), k('CC', '05-05', 1), k('VGD', '05-08', 2)]),
 dict(id='congress-report-on-the-draught-bills-22-april-1778', parent='lord-norths-conciliatory-bills-and-congress-april-1778', kind='document_group',
      label="Congress, 22 April 1778: the report on the printed draught bills, agreed to by Congress",
      definition="Printings of the report agreed to by Congress on 22 April 1778: 'The Committee to whom was referred the General's letter of the 18th, containing a certain printed paper sent from Philadelphia, purporting to be the draught of a bill for declaring the intentions of the Parliament of Great-Britain'; it gives, point by point, the committee's reasons for believing the bills will be brought into Parliament ('1st. Because their General hath made divers feeble efforts to set on foot some kind of treaty during the last winter'), and ends with resolutions of Congress, among them that the Congress is 'invested with an exclusive authority to treat with the King of Great Britain', and on 'any man, or body of men, who shall presume to make any separate or partial convention or agreement with the King of Great-Britain'. The Newport Gazette heads it 'Extract from a Rebel Paper'. Congress's own report.",
      role='published_document', words=55, dateline=False,
      head=r'(?:I\s?N\s+C\s?O\s?N\s?G\s?R\s?E\s?S\s?S,?\s+(?:A\s?PRIL|April)\s+22,?\s+1778\.?\s*)',
      core=[r'(?:T\s?\s?HE|The)\s+(?:C\s?OMMITTEE|Committee)\s+to\s+whom\s+was\s+referred\s+the\s+General'],
      first="Congress, 22 April 1778: the report on the printed draught bills, and Congress's resolutions on treating with the King of Great Britain.",
      what="Congress's report of 22 April 1778 on the draught bills",
      printings=[k('PP', '04-22', 8), k('NJG', '05-06', 1), k('VGD', '05-08', 3), k('CC', '05-12', 2), (k('NPG', '05-14', 4), {'head': 'Extract\\s+from\\s+a\\s+Rebel\\s+Paper\\.\\s*In\\s+CONGRESS,?\\s+April\\s+22,?\\s+1778\\.?\\s*'}), k('NYG', '05-18', 1)]),
 dict(id='simeon-deane-arrives-at-congress-with-the-treaties-with-france-may-1778', kind='document_group',
      label="York-Town, 4 May 1778: Simeon Deane arrives at Congress with dispatches from the American plenipotentiaries in France",
      definition="Printings of a York-Town paragraph of 4 May 1778, first published in a postscript to the Pennsylvania Gazette of 2 May: 'On Saturday last Simeon Deane, Esq; arrived at Congress, express from the American Plenipotentiaries at the court of France, and delivered his dispatches to the President. The important contents are, by a correspondent, thus communicated'; it says that the King of France 'was determined to acknowledge our Independence, and make a Treaty with us of Amity and Commerce'. A correspondent's account of the dispatches, as the York-Town paper gave it.",
      role='report', words=50, dateline=True,
      core=[r'(?:O\s?N|On)\s+Saturday\s+last\s+S\s?I\s?M\s?E?\s?O\s?N\s+D\s?E\s?A\s?N\s?E'],
      first="York-Town, 4 May 1778: Simeon Deane brings Congress the dispatches of the American plenipotentiaries in France, on the treaties with France.",
      what="the York-Town paragraph on Simeon Deane's arrival",
      printings=[k('PP', '05-06', 2), (k('NJG', '05-13', 2), {'head': 'Y\\s?O\\s?R\\s?K\\s?-\\s?T\\s?O\\s?W\\s?N,?\\s+May\\s+4\\.\\s*'}), (k('VGD', '05-15', 2), {'head': 'M\\s?A\\s?Y\\s+4\\.\\s*'}), k('CC', '05-19', 2), k('NYG', '05-25', 1)]),
 dict(id='kings-message-on-the-french-declaration-17-march-1778', kind='document_group',
      label="The King's message to Parliament of 17 March 1778 on the French ambassador's declaration of a treaty with the United States",
      definition="Printings of the King's message to the House of Lords, delivered by Lord Weymouth on 17 March 1778, as a London account printed it with the paper delivered by the French ambassador: 'His Majesty having been informed, by order of the French King, that a treaty of amity and commerce has been signed between the court of France and certain persons employed by his Majesty's revolted subjects in North-America, has judged it necessary to direct, that a copy of the declaration delivered by the French Ambassador to Lord Viscount Weymouth be laid before the House of Lords'; the King says he has sent orders to his ambassador to withdraw from the French court, and is determined to be prepared to exert all the force and resources of his kingdoms. The papers printed it in May from a Philadelphia paper of 9 May, which had it by the Porcupine frigate. The King's own message, with the French ambassador's paper.",
      role='published_document', words=55, dateline=False,
      head=r'(?:The\s+following\s+is\s+the\s+message\s+delivered\s+by\s+Lord\s+Weymouth\s+to\s+the\s+House\s+of\s+Lords\s+last\s+Tuesday[.:]?\s*["“]?\s*)',
      core=[r'(?:G\s?EORGE|George)\s+R\.?\s*["“]?\s*(?:H\s?IS|H\s?\s?IS|His)\s+Majesty\s+having\s+been\s+informed'],
      first="The King's message of 17 March 1778: the French ambassador has declared a treaty with the United States; the King prepares to exert the force of his kingdoms.",
      what="the King's message of 17 March 1778",
      printings=[k('PP', '05-20', 2), k('NJG', '05-20', 2), (k('NYG', '05-25', 2), {'head': 'HOUSE\\s+OF\\s+LORDS,?\\s+March\\s+17\\.\\s*The\\s+following\\s+is\\s+the\\s+message\\s+delivered\\s+by\\s+Lord\\s+Weymouth\\s+to\\s+the\\s+House\\s+of\\s+Lords\\s+last\\s+Tuesday[.:]?\\s*[\\"“]?\\s*'}), k('CC', '05-26', 3), k('NHG', '06-02', 2)]),
 dict(id='governor-livingston-message-to-the-new-jersey-assembly-may-1778', kind='document_group',
      label="Governor Livingston's message to the General Assembly of New Jersey, May 1778, on the news from France and on the Tories",
      definition="Printings of extracts from the message of William Livingston, Governor of New Jersey, to the General Assembly of the state: 'Gentlemen, I heartily congratulate you upon the agreeable news we have received from France, since I had the pleasure of meeting you last in this place'; it lays before the Assembly the resolution of Congress of 23 April recommending pardon for those who return, and argues against receiving back Tories who have taken part with the enemy. The Governor's own message, as the New-Jersey Gazette printed it.",
      role='published_document', words=50, dateline=True,
      core=[r'(?:E\s?XTRA\w*|Extra\w*)\s+from\s+his\s+(?:E\s?XCELLENCY|Excellency)\s+Governor\s+\S*'],
      first="Governor Livingston's message to the New Jersey Assembly: congratulations on the news from France, and his argument against receiving back the Tories.",
      what="Governor Livingston's message",
      printings=[k('NJG', '06-03', 1), k('PP', '06-10', 5), k('CC', '06-23', 1), k('NHG', '07-07', 1)]),
 dict(id='washington-to-congress-24-may-1778-barren-hill', kind='document_group',
      label="General Washington to Congress, Valley Forge, 24 May 1778: the enemy's move against the Marquis de la Fayette's detachment",
      definition="Printings of an extract of General Washington's letter to Congress dated Valley Forge, 24 May 1778: 'On the night of the 19th the enemy moved out in force against the detachment under the Marquis la Fayette, mentioned in my letter of the 18th, which made a timely and handsome retreat'. The commander's own report to Congress, as the York-Town paper published the extract on 30 May.",
      role='published_document', words=50, dateline=False,
      head=r'(?:Extra\w*\s+of\s+a\s+[Ll]etter\s+from\s+(?:General|Gen\.)\s+W\s?ASHINGTON\s+to\s+C\S*\.?\s*(?:Head[\s\-]*Quarters,?\s+)?Valley[\s\-]+Forge,?\s+May\s+24,?\s*(?:1778\.?)?\s*["“]?\s*)',
      core=[r'["“]?\s*(?:O\s?N|On)\s+the\s+night\s+of\s+the\s+19(?:th)?\s+the\s+enemy\s+moved\s+out'],
      first="General Washington's letter to Congress of 24 May 1778: the detachment under the Marquis de la Fayette made a timely retreat before the enemy.",
      what="General Washington's letter of 24 May 1778",
      printings=[(k('PP', '06-03', 3), {'head': 'Extract\\s+of\\s+a\\s+letter\\s+from\\s+Gen\\w*\\.?\\s+WASHINGTON,?\\s+to\\s+\\S+\\s*\\S*\\s*Head\\s+Quarters,?\\s+Valley\\s+Forge,?\\s+May\\s+24,?\\s+1778\\.?\\s*'}), k('NJG', '06-10', 2), k('CC', '06-16', 1), (k('NYG', '06-22', 1), {'head': 'Extract\\s+of\\s+a\\s+letter\\s+from\\s+Gen\\w*\\.?\\s+WASHINGTON,?\\s+to\\s+\\S+\\s*\\S*\\s*Head\\s+Quarters,?\\s+Valley\\s+Forge,?\\s+May\\s+24,?\\s+1778\\.?\\s*'})]),
 dict(id='congress-on-lord-howe-and-general-clinton-letters-6-june-1778', kind='document_group',
      label="Congress, 6 June 1778: Lord Howe's and General Clinton's letters with three acts of Parliament, and the President's answer",
      definition="Printings of the proceedings of Congress of 6 June 1778: 'Letter of the 27th of May from Lord Howe, and one of the 3d of June from General Clinton, at Philadelphia, accompanied with three acts of Parliament, were read'; Congress ordered an answer, which the President sent: 'they have already expressed their sentiments upon bills, not essentially different from those acts, in a publication of the 22d of April last', and 'when the King of Great-Britain shall be seriously disposed to put an end to the unprovoked and cruel war waged against these United States, Congress will readily attend to such terms of peace as may consist with the honour of independent nations'. The proceedings of Congress and the President's letter, as published.",
      role='published_document', words=50, dateline=False,
      head=r'(?:I\s?N\s+C\s?\s?O\s?N\s?G\s?R\s?E\s?S\s?S,?\s+June\s+6,?\s+1778\.?\s*)',
      core=[r'(?:A\s+)?(?:L\s?ETTER|Letter)\s+of\s+the\s+27th\s+of\s+May,?\s+from\s+Lord\s+Howe'],
      first="Congress, 6 June 1778: Lord Howe's and General Clinton's letters with three acts of Parliament are read; the President answers that Congress has already given its sentiments on them.",
      what="the proceedings of Congress of 6 June 1778 and the President's answer",
      printings=[k('PP', '06-17', 2), k('CC', '06-30', 3), k('NJG', '07-01', 1), (k('NHG', '07-07', 2), {'head': 'In\\s+CONGRESS,?\\s+June\\s+6\\W+1778\\.?\\s*'}), k('NYG', '07-13', 1)]),
 dict(id='british-army-completes-the-evacuation-of-philadelphia-june-1778', kind='document_group',
      label="Philadelphia, 20 June 1778: the British army completes its evacuation of the city",
      definition="Printings of a Philadelphia paragraph of 20 June 1778: 'The British army, early last Thursday morning, completed their evacuation of this city, having before transported their stores and most of their artillery into Jersey, where they had thrown up some works, and several of their regiments were encamped'. A Philadelphia report.",
      role='report', words=50, dateline=True,
      core=[r'(?:T\s?\s?HE|The)\s+British\s+army,?\s+early\s+last\s+Thursday\s+morning'],
      first="Philadelphia, 20 June 1778: the British army completes its evacuation of the city and crosses into New Jersey.",
      what="the Philadelphia paragraph on the evacuation",
      printings=[(k('NJG', '07-01', 2), {'note': "The New-Jersey Gazette's issue of 1 July 1778 (a second copy of it is filed under 24 June)."}),
                 k('CC', '07-07', 3), k('NYG', '07-13', 1), k('NHG', '07-14', 1)]),
 dict(id='the-battle-of-monmouth-june-july-1778', kind='context_group',
      label="The battle of Monmouth, 28 June 1778: General Washington's account to Congress, and the thanks of Congress",
      children=['washington-to-congress-1-july-1778-on-the-battle-of-monmouth', 'congress-thanks-to-washington-and-the-army-7-july-1778'],
      definition="Two public papers on the battle fought near Monmouth Court-House, New Jersey, on 28 June 1778, as the British army marched from Philadelphia to New York: General Washington's letter to Congress of 1 July, and the resolution of thanks of Congress of 7 July. Contains those two groups."),
 dict(id='washington-to-congress-1-july-1778-on-the-battle-of-monmouth', parent='the-battle-of-monmouth-june-july-1778', kind='document_group',
      label="General Washington to Congress, Englishtown, 1 July 1778: a full account of the movements of the army and the action of 28 June",
      definition="Printings of General Washington's letter to the President of Congress dated Englishtown, 1 July 1778: 'I embrace this first moment of leisure to give Congress a more full and particular account of the movements of the army under my command, since its passing the Delaware, than the situation of our affairs would heretofore permit'. The commander's own account to Congress.",
      role='published_document', words=45, dateline=False,
      head=r'(?:S\s?I\s?R,?\s+Engl?i?sh[\s\-]*[Tt]own,?\s+July\s+1,?\s+1778\.?\s*)',
      core=[r'I?\s*E\s?M\s?B\s?R\s?A\s?C\s?E\s+this\s+first\s+moment\s+of\s+leisure'],
      first="General Washington's letter to Congress of 1 July 1778: his account of the army's movements since it crossed the Delaware and of the action of 28 June.",
      what="General Washington's letter of 1 July 1778",
      printings=[k('NJG', '07-08', 5), k('VGD', '07-17', 1), k('CC', '07-21', 1), k('NHG', '07-28', 2)]),
 dict(id='congress-thanks-to-washington-and-the-army-7-july-1778', parent='the-battle-of-monmouth-june-july-1778', kind='document_group',
      label="Congress, 7 July 1778: the thanks of Congress to General Washington and the officers and men who distinguished themselves at Monmouth",
      definition="Printings of the resolutions of Congress of 7 July 1778: 'Resolved unanimously, That the thanks of Congress be given to General Washington for the activity with which he marched from the camp at Valley Forge in pursuit of the enemy; for his distinguished exertions in forming the order of battle; and for his great good conduct in leading on the attack and gaining the important victory of Monmouth over the British grand army'. The resolutions of Congress.",
      role='published_document', words=50, dateline=False,
      head=r'(?:I\s?\s?N\s+C\s?\s?O\s?\s?N\s?\s?G\s?\s?R\s?\s?E\s?\s?S\s?\s?S,?\s+July\s+7(?:th)?,?\s*(?:1778)?\.?\s*)',
      core=[r'(?:R\s?ESOLVED|Resolved)\s+unanimously[.,]?\s+[Tt]hat\s+the\s+[Tt]hanks\s+of\s+(?:C\s?ONGRESS|Congress)\s+be\s+given\s+to\s+(?:General|G\s?ENERAL)'],
      first="Congress, 7 July 1778: thanks to General Washington and the army for the victory of Monmouth.",
      what="the thanks of Congress of 7 July 1778",
      printings=[k('NJG', '07-15', 2), k('VGD', '07-17', 2), k('NHG', '07-28', 1), k('CC', '07-28', 1)]),
 dict(id='count-destaing-offer-of-protection-to-american-armaments-july-1778', kind='document_group',
      label="Monsieur Gerard's message to Congress, July 1778: Count d'Estaing offers American armaments the protection of the French squadron, and the prizes they take",
      definition="Printings of the French minister's message to Congress, published by order of Congress: 'His Excellency the Count D'Estaing, Vice-Admiral of France, commanding the King's squadron, is desirous of enabling all the armaments either public or private in the United States of North-America, to derive every possible advantage from the operations of this squadron in order to make prizes of the common enemy'; such armaments shall enjoy the protection of the squadron, and their prizes shall belong to them only. Signed Gerard. The French minister's message, as Congress published it.",
      role='published_document', words=50, dateline=False,
      head=r'(?:Extra\w*\s+of\s+a\s+MESSAGE\s+from\s+M\S*\s+G\S*\s+to\s+C\S*\.?\s*)',
      core=[r'(?:H\s?IS|His)\s+(?:E\s?XCELLENCY|Excellency)\s+the\s+Count\s+D.?\s?E?S?T?R?A?I?G?N|desirous\s+of\s+enabling\s+all\s+the\s+armaments'],
      first="The French minister's message to Congress, July 1778: Count d'Estaing offers American armaments the protection of his squadron, and their prizes.",
      what="the French minister's message on Count d'Estaing's offer",
      printings=[k('NJG', '07-22', 3), k('VGP', '07-31', 1), k('CC', '08-04', 3), k('NHG', '08-11', 2)]),
 dict(id='congress-receives-the-french-minister-gerard-6-august-1778', kind='document_group',
      label="Congress, 6 August 1778: the audience of the Sieur Gerard, Minister Plenipotentiary of the King of France",
      definition="Printings of the proceedings of Congress of 6 August 1778: 'According to order the Honourable the Sieur Gerard being introduced to an audience by the two Members for that purpose appointed, and being seated in his chair, his Secretary delivered to the President a letter from his most Christian Majesty, which was read in the words following'; with the King's letter, the minister's address and the President's answer. The proceedings of Congress, as published.",
      role='published_document', words=50, dateline=False,
      head=r'(?:I\s?N\s+C\s?\s?O\s?\s?N\s?\s?G\s?\s?R\s?\s?E\s?\s?S\s?\s?S,?\s+August\s+6,?\s*(?:1778)?\.?\s*)',
      core=[r'(?:A\s?CCORDING|According)\s+to\s+order,?\s+the\s+(?:Hon\w*\.?)\s+the\s+Sieur\s+Gerard'],
      first="Congress, 6 August 1778: the French minister, the Sieur Gerard, is received in audience and presents the King of France's letter.",
      what="the proceedings of Congress of 6 August 1778",
      printings=[k('NJG', '08-19', 1), k('NYG', '08-24', 2), k('NHG', '09-01', 2), k('CC', '09-01', 4)]),
 dict(id='the-commissioner-johnstone-and-congress-august-september-1778', kind='context_group',
      label="George Johnstone and Congress, August and September 1778: Congress's declaration, the commissioners' declaration and Mr. Johnstone's declaration",
      children=['congress-declaration-on-george-johnstone-11-august-1778', 'commissioners-declaration-of-26-august-1778',
                'george-johnstone-declaration-of-26-august-1778'],
      definition="Three public declarations on one of the British commissioners, George Johnstone: Congress's declaration of 11 August 1778 that it is incompatible with the honour of Congress to hold any correspondence with him, and the two declarations of 26 August answering it, one by the other three commissioners and one by Mr. Johnstone. Contains those three groups."),
 dict(id='congress-declaration-on-george-johnstone-11-august-1778', parent='the-commissioner-johnstone-and-congress-august-september-1778', kind='document_group',
      label="Congress's declaration of 11 August 1778 on George Johnstone, one of the British commissioners",
      definition="Printings of the declaration of Congress of 11 August 1778: 'Whereas George Johnstone, Esq. one of the British Commissioners for restoring peace in America, on the eleventh of April last, did write and send a letter to Joseph Reed, Esq. a Member of Congress'; it recites the passages of his letters and the account Mr. Reed gave of an offer made to him, and declares it incompatible with the honour of Congress to hold any manner of correspondence or intercourse with Mr. Johnstone. The New-York Gazette and the Newport Gazette print it with the commissioners' answers. Congress's own declaration; the allegations are those of Congress and of Mr. Reed's account.",
      role='published_document', words=50, dateline=False,
      head=r'(?:A\s+)?D\s?E\s?C\s?L\s?A\s?R\s?A\s?T\s?I\s?O\s?N\.?\s*',
      core=[r'W\s?\s?HEREAS\s+Geor\S*\s+John\S*,?\s+Esq|Whereas\s+Geor\S*\s+John\S*,?\s+Esq'],
      first="Congress's declaration of 11 August 1778: it will hold no correspondence with George Johnstone, whose letters to members it recites.",
      what="Congress's declaration of 11 August 1778",
      printings=[k('NJG', '08-19', 2),
                 (k('NYG', '09-07', 1), {'field': CA, 'note': 'RevX lacks the opening of this item on this page, so the excerpt comes from the older CA transcription.'}),
                 k('NPG', '09-10', 1), k('CC', '09-22', 2)]),
 dict(id='commissioners-declaration-of-26-august-1778', parent='the-commissioner-johnstone-and-congress-august-september-1778', kind='document_group',
      label="The declaration of the Earl of Carlisle, Sir Henry Clinton and William Eden, 26 August 1778, on Congress's declaration about their colleague",
      definition="Printings of the declaration of three of the British commissioners, the Earl of Carlisle, Sir Henry Clinton and William Eden, dated New York, 26 August 1778: they 'have received a declaration of the American Congress, dated the 11th instant, which relates to a gentleman with whom they have the honour to be joined in commission'; 'they hereby think proper on their part solemnly to declare, that they had not any knowledge, either directly or indirectly, of the letter and conversation alluded to in the said Declaration until they saw them made public in the news-papers', and they go on to the treaty with France. Printed in the New York and Newport papers with the papers sent to Congress, and in the American papers after Congress's resolution of 31 August. The commissioners' own declaration.",
      role='published_document', words=45, dateline=False,
      head=r'(?:WHEREAS\s+they\s+)',
      core=[r'(?:H\s?AVE|have)\s+received\s+a\s+(?:D\s?ECLARATION|[Dd]eclaration)\s+of\s+the\s+American\s+Congress'],
      first="The commissioners' declaration of 26 August 1778: they had no knowledge of the letter and conversation that Congress's declaration recites until they saw them in the newspapers.",
      what="the commissioners' declaration of 26 August 1778",
      printings=[k('NYG', '09-07', 1), k('NPG', '09-10', 4), k('CC', '09-22', 2), k('NJG', '09-23', 1), (k('VGD', '10-09', 1), {'head': 'Extract\\s+from\\s+the\\s+declaration\\s+of\\s+the\\s+Earl\\s+of\\s+Carlisle.{0,140}?commissioners\\.\\s*WHEREAS\\s+they\\s+'})]),
 dict(id='george-johnstone-declaration-of-26-august-1778', parent='the-commissioner-johnstone-and-congress-august-september-1778', kind='document_group',
      label="George Johnstone's declaration of 26 August 1778: he declines to act as a commissioner in anything that regards Congress",
      definition="Printings of George Johnstone's declaration dated New York, 26 August 1778, in answer to Congress's declaration: having seen the declaration of Congress of 11 August and its resolution, 'The said George Johnstone for himself says, That he is far from considering the said resolution of the Congress as offensive to him; That he rather receives it as a mark of distinction'; he declares that 'the subscriber, George Johnstone, thinks proper to decline acting as a Commissioner, or otherwise interfering in any message, answer, agreement, negotiation, matter or thing that may regard the said Congress, which he does with so much the more pleasure as he is perfectly satisfied the business will be left in more able and sufficient hands', reserving the liberty of publishing a justification of his conduct. Mr. Johnstone's own declaration.",
      role='published_document', words=45, dateline=False,
      head=r'(?:G\s?EORGE\s+J\s?OHNSTONE,?\s*)',
      core=[r'having\s+[sf]een\s+a\s+[Dd]eclaration\s+of\s+the\s+American\s+Congre[sf][sf]'],
      first="George Johnstone's declaration of 26 August 1778: he declines to act as a commissioner in anything that regards Congress, and reserves a justification of his conduct.",
      what="George Johnstone's declaration",
      printings=[(k('NYG', '09-07', 1), {'field': REVX, 'core': [r'the\s+more\s+pleasure,?\s+as\s+he\s+is\s+perfectly\s+satisfied'],
                                     'note': "Neither transcription has the opening of the declaration on this page: RevX runs on from Congress's resolution to 'the more pleasure, as he is perfectly satisfied', and the CA text is garbled. The excerpt is the passage RevX keeps; the scan check reads the print."}),
                 k('NPG', '09-10', 2), k('NJG', '09-16', 2), k('CC', '09-22', 2),
                 (k('VGD', '10-09', 1), {'head': 'Extract\\s+from\\s+the\\s+declaration\\s+of\\s+G\\s?EORGE\\s+J\\s?OHNSTONE.{0,120}?Majesty\\.\\s*G\\s?EORGE\\s+J\\s?OHNSTONE,?\\s*', 'note': "Dixon and Hunter's Virginia Gazette prints an 'Extract from the declaration of George Johnstone'."})]),
 dict(id='kings-speech-to-parliament-3-june-1778', kind='document_group',
      label="The King's speech to both Houses of Parliament, 3 June 1778, giving them a recess after a long session",
      definition="Printings of the King's speech of 3 June 1778: 'My Lords and Gentlemen, After so long and laborious an application to the public business, I think it proper at this season of the year to give you some recess. I come at the same time to return you my particular thanks for the zeal you have shewn in supporting the honour of my crown'. The papers printed it in August from the June mail. The King's own speech.",
      role='published_document', words=50, dateline=False,
      head=r"(?:His\s+)?M\s?AJESTY'?S\s+most\s+(?:G\s?RACIOUS|gracious)\s+S\s?PEECH,?\s+to\s+both\s+H\s?OUSES\s+of\s+P\s?ARLIAMENT,?\s*(?:on\s+Wednesday,?\s*(?:June\s*3,?\s*)?1778\.?)?\s*",
      core=[r'(?:M\s?Y|My)\s+(?:L\s?ORDS|Lords),?\s+and\s+(?:G\s?ENTLEMEN|Gentlemen),?\s*(?:A\s?F)?\s?T\s?E\s?R\s+[st]o\s+long'],
      first="The King's speech to both Houses of Parliament, 3 June 1778: a recess after a long session, and his thanks for their support.",
      what="the King's speech of 3 June 1778",
      printings=[k('NYG', '08-03', 2), k('NJG', '08-12', 2), k('VGP', '08-21', 2), k('CC', '08-25', 2), k('NHG', '09-01', 2)]),
 dict(id='letter-from-the-hague-on-american-proposals-for-a-treaty-june-1778', kind='document_group',
      label="A letter from the Hague of 4 June 1778: American proposals for a treaty lie before the States of the United Provinces",
      definition="Printings of an extract of a letter from the Hague dated 4 June 1778, in London news: 'The proposals for a treaty between the Americans and the United Provinces now lie before the States; the answer I am told the Americans received on the delivery of them was, that the business required a very serious attention'. The New-York Gazette and the Newport Gazette print it in August; three American papers print it in November as 'a letter from Holland, dated in June'. A correspondent's letter, as the London papers gave it.",
      role='report', words=45, dateline=False,
      head=r'(?:Extract\s+of\s+a\s+Letter\s+from\s+the\s+Hague,?\s+June\s+4\.?\s*["“]?\s*|(?:Another\s+|A\s+)letter\s+from\s+Holland,?\s+dated\s+in\s+June,?\s+says,?\s*["“]?\s*)',
      core=[r'(?:T\s?HE|The)\s+proposals\s+for\s+a\s+treaty\s+between\s+the\s+Americans'],
      first="A letter from the Hague of 4 June 1778: American proposals for a treaty lie before the States of the United Provinces.",
      what="the letter from the Hague of 4 June 1778",
      printings=[k('NYG', '08-24', 1), k('NPG', '08-27', 2), k('NHG', '11-03', 3), k('CC', '11-03', 3), k('NJG', '11-11', 2)]),
 dict(id='british-landing-at-bedford-september-1778', kind='document_group',
      label="September 1778: about forty sail of British ships appear off Bedford and land some 4,000 men",
      definition="Printings of a report of September 1778 from New England: 'Last Saturday about 40 sail of British men of war and transports appeared off Bedford, at six o'clock they landed about 4000 British troops, Tories, &c. under the command of General Gray'; the papers' versions go on in different words to the rope-walks, houses, stores and shipping burned, and one adds a comment of its own ('Oh Clinton! can you expect that after such savage and cowardly conduct, that Americans will treat with Britons upon terms of reconciliation'). Printed by every paper that survives for its weeks, the New-York Gazette among them. A report at second hand.",
      role='report', words=45, dateline=True,
      core=[r'(?:L\s?AST|Last)\s+Saturday,?\s+(?:noon\s+)?about\s+40\s+[sf]ail\s+of\s+British'],
      first="September 1778: about forty sail of British men of war and transports appear off Bedford and land some 4,000 men, who burn vessels and buildings.",
      what='the report of the landing at Bedford',
      printings=[k('NHG', '09-15', 3), k('CC', '09-15', 2), (k('NYG', '09-28', 2), {'head': 'SEPTEMBER\\s+10\\.\\s*'}), k('NJG', '09-30', 2)]),
 dict(id='the-troops-of-the-convention-of-saratoga-august-september-1778', kind='context_group',
      label="The troops of the convention of Saratoga, August and September 1778: the commissioners' requisition and Congress's resolution",
      children=['commissioners-requisition-on-the-troops-of-the-convention-26-august-1778',
                'congress-on-the-troops-of-the-convention-of-saratoga-4-september-1778'],
      definition="The two public papers on the troops that surrendered at Saratoga in October 1777, whose embarkation Congress had suspended in January 1778: the British commissioners' requisition of 26 August 1778 that the troops be allowed to sail, and Congress's resolution of 4 September 1778. Contains those two groups."),
 dict(id='commissioners-requisition-on-the-troops-of-the-convention-26-august-1778', parent='the-troops-of-the-convention-of-saratoga-august-september-1778', kind='document_group',
      label="The commissioners' requisition of 26 August 1778: the troops of the convention of Saratoga to be allowed to embark for Great Britain",
      definition="Printings of the requisition of the British commissioners, the Earl of Carlisle, Sir Henry Clinton and William Eden, dated New York, 26 August 1778: 'Upon a representation from the Commander in Chief of his Majesty's forces, that the troops lately serving under Lieutenant-General Burgoyne'; it requires that passports be given for transports to the harbour of Boston 'for the immediate embarkation of the said troops; and that they be allowed to depart for Great-Britain in term of the said Convention', offers 'to renew, on the part of Great-Britain, all the stipulations of the said Convention', and is sent 'to the American Congress for their direct and explicit answer'. Printed with the commissioners' other papers of 26 August. The commissioners' own requisition.",
      role='published_document', words=45, dateline=False,
      core=[r'(?:U\s?PON|Upon)\s+a\s+representation\s+from\s+the\s+(?:C\s?OMMANDER|[Cc]ommander)\s+in\s+(?:C\s?HIEF|[Cc]hief)'],
      first="The British commissioners' requisition of 26 August 1778: the troops of the convention of Saratoga to be allowed to embark for Great Britain, with an offer to renew the convention's stipulations.",
      what="the commissioners' requisition of 26 August 1778",
      printings=[k('NYG', '09-07', 1), k('NPG', '09-10', 1), k('CC', '09-22', 3), k('NJG', '09-23', 1), k('VGD', '10-09', 1)]),
 dict(id='congress-on-the-troops-of-the-convention-of-saratoga-4-september-1778', parent='the-troops-of-the-convention-of-saratoga-august-september-1778', kind='document_group',
      label="Congress, 4 September 1778: no ratification of the convention of Saratoga resting on powers 'by construction and implication', or subject to the approval of Parliament, can be accepted",
      definition="Printings of the resolution of Congress of 4 September 1778: 'Whereas Congress did, on the eighth day of January, 1778, Resolve, \"That the embarkation of Lieutenant General Burgoyne, and the troops under his command, be suspended till a distinct and explicit ratification of the Convention of Saratoga shall be properly notified by the Court of Great Britain to Congress\"'; it resolves 'That no ratification of the Convention of Saratoga, which may be tendered in consequence of powers which may reach that case by construction and implication, or which may subject whatever is transacted relative to it to the future approbation or disapprobation of the Parliament of Great Britain, can be accepted by Congress'. Congress's answer, in effect, to the commissioners' requisition of 26 August on those troops. Printed by every paper that survives for its weeks. The resolution of Congress.",
      role='published_document', words=50, dateline=False,
      head=r'(?:I\s?N\s+C\s?O\s?N\s?G\s?R\s?E\s?S\s?S,?\s+S\s?ept\w*\.?\s+4(?:th)?,?\s+1778\.?\s*)',
      core=[r'(?:W\s?HEREAS|Whereas|WHEN)\s+(?:the\s+)?Congress\s+did,?\s+on\s+the\s+(?:eighth|8(?:th)?|5th)\s+day\s+of\s+January'],
      first="Congress, 4 September 1778: no ratification of the convention of Saratoga resting on implied powers, or subject to the approval of Parliament, can be accepted.",
      what="the resolution of Congress of 4 September 1778",
      printings=[k('CC', '09-22', 3), k('NJG', '09-23', 1), k('NYG', '09-28', 2), k('NHG', '09-29', 1), k('VGD', '10-09', 2)]),
 dict(id='privateer-general-hancock-and-the-levant-frigate-september-1778', kind='document_group',
      label="Boston, September 1778: the privateer General Hancock returns from a cruise after an engagement with the British frigate Levant",
      definition="Printings of a Boston paragraph of September 1778: 'Last Monday returned into port, from a cruise, the private armed ship General Hancock, late commanded by Capt. Ishmael Hardy. On the 9th instant, she fell in with the Le Vant English frigate, of 32 guns'; it gives the course of the engagement, in which the captain of the privateer was wounded and the frigate blew up, and the privateer's boats saved part of her crew. A Boston paper's report.",
      role='report', words=45, dateline=True,
      core=[r'(?:L\s?AST|Last)\s+Monday\s+returned\s+into\s+[Pp]ort,?\s+from\s+a\s+[Cc]ruiz?s?\w*,?\s+the\s+private\s+armed\s+[Ss]hip',
            r'(?:M\s?ONDAY|Monday)\s+returned\s+into\s+port,?\s+from\s+a\s+cruise,?\s+the\s+private\s+armed\s+ship'],
      first="Boston, September 1778: the privateer General Hancock returns after an engagement with the British frigate Levant, of 32 guns.",
      what="the Boston report of the privateer General Hancock",
      printings=[k('NHG', '09-29', 1), k('CC', '09-29', 3), k('NJG', '10-07', 2), k('NYG', '10-19', 2), k('VGP', '10-23', 2)]),
 dict(id='colonel-clark-takes-fort-chartres-and-the-western-posts-1778', kind='document_group',
      label="Williamsburg, October 1778: intelligence that Colonel Clark has taken Fort Chartres and the other western posts between the Ohio and the Mississippi",
      definition="Printings of a Williamsburg paragraph of 9 October 1778, 'Intelligence from the south-western frontiers of this state': 'Col. Clark, with a body of militia, has taken possession of Fort Charters and the other western posts between the river Ohio and Mississippi. The Commandant is on his way to this city'. A Williamsburg paper's report.",
      role='report', words=45, dateline=True,
      head=r'(?:I\s?NTE\S*\s+from\s+the\s+south[\s\-]*west\w*\s+frontiers\s+of\s+this\s+[Ss]tate\.?\s*)',
      core=[r'(?:C\s?OL|Col)\.?\s+Clark,?\s+with\s+a\s+body\s+of\s+militia'],
      first="Williamsburg, October 1778: intelligence that Colonel Clark and a body of militia have taken Fort Chartres and the other western posts.",
      what="the Williamsburg report of Colonel Clark",
      printings=[k('VGD', '10-16', 3), (k('NJG', '11-11', 2), {'head': 'W\\s?I\\s?L\\s?L\\s?I\\s?A\\s?M\\s?S\\s?B\\s?U\\s?R\\s?G,?\\s+O\\s?C\\s?T\\.?\\s+9\\.\\s*'}), (k('NYG', '11-16', 2), {'head': 'WILLIAMSBURG,?\\s+Octo?\\.?\\s+9\\.\\s*'}), k('NHG', '11-24', 3), k('CC', '11-24', 2)]),
 dict(id='the-commissioners-manifesto-and-the-congress-manifesto-october-1778', kind='context_group',
      label="The British commissioners' manifesto and proclamation of 3 October 1778, and the manifesto of Congress of 30 October",
      children=['commissioners-manifesto-and-proclamation-3-october-1778', 'congress-manifesto-30-october-1778'],
      definition="The two manifestos of October 1778: the British commissioners' manifesto and proclamation of 3 October, addressed to the members of Congress, the assemblies and all the inhabitants, and the manifesto of Congress of 30 October. Contains those two groups."),
 dict(id='commissioners-manifesto-and-proclamation-3-october-1778', parent='the-commissioners-manifesto-and-the-congress-manifesto-october-1778', kind='document_group',
      label="The British commissioners' manifesto and proclamation of 3 October 1778, to the members of Congress, the assemblies and all the inhabitants",
      definition="Printings of the manifesto and proclamation of the Earl of Carlisle, Sir Henry Clinton and William Eden, dated New York, 3 October 1778: 'To the Members of the Congress, the Members of the General Assemblies or Conventions of the several colonies, plantations and provinces' and all the free inhabitants; the commissioners say they will return to England, renew the offers made to the Congress and the assemblies, proclaim a pardon to those who return to their allegiance, and declare the manifesto in force for forty days, from 3 October to 11 November. The New-York Gazette prints it in three issues and the Newport Gazette in two; American papers print it with comments of their own. The commissioners' own manifesto.",
      role='published_document', words=45, dateline=False,
      head=r'(?:M\s?ANIFESTO\s+(?:AND|and)\s+P\s?ROCLAMATION\.?\s*)',
      core=[r'(?:T\s?O|To)\s+the\s+(?:M\s?EMBERS|[Mm]embers)\s+of\s+the\s+(?:C\s?ONGRESS|Congress),?\s+the\s+(?:M\s?EMBERS|[Mm]embers)\s+of\s+the\s+General'],
      first="The British commissioners' manifesto and proclamation of 3 October 1778: their offers renewed and a pardon proclaimed, in force for forty days.",
      what="the commissioners' manifesto and proclamation",
      printings=[k('NYG', '10-19', 1), k('CC', '10-20', 2), k('NJG', '10-21', 1), k('NPG', '10-22', 1),
                 (k('NYG', '10-26', 1), {'note': 'Printed again.'}), k('NHG', '10-27', 2), (k('NPG', '10-29', 1), {'note': 'Printed again.'}),
                 k('VGD', '10-30', 1), (k('NYG', '11-02', 1), {'note': 'Printed again.'})]),
 dict(id='congress-manifesto-30-october-1778', parent='the-commissioners-manifesto-and-the-congress-manifesto-october-1778', kind='document_group',
      label="The manifesto of Congress, 30 October 1778",
      definition="Printings of the manifesto of Congress done on 30 October 1778: 'These United States, having been driven to hostilities by the oppressive and tyrannous measures of Great Britain; having been compelled to commit the essential rights of man to the decision of arms'; it declares 'That if our enemies presume to execute their threats, or persist in their present career of barbarity, we will take such exemplary vengeance as shall deter others from a like conduct'. Printed by every paper that survives for its weeks; the New-York Gazette prints it twice, the second time 'with the remarks subjoined to it'. Congress's own manifesto.",
      role='published_document', words=45, dateline=False,
      head=r'(?:By\s+the\s+C\s?ONGRESS\s+of\s+the\s+U\s?NITED\s+S\s?TATES\s+of\s+A\s?MERICA\.?\s*M\s?\s?A\s?\s?N\s?\s?I\s?\s?F\s?\s?E\s?\s?S\s?\s?T\s?\s?O\.?\s*)',
      core=[r'T\s?HESE\s+United\s+States,?\s+having\s+been\s+driven\s+to\s+hostilities'],
      first="The manifesto of Congress of 30 October 1778: if the enemy execute their threats or persist in their present career, Congress will take exemplary vengeance.",
      what="the manifesto of Congress",
      printings=[k('NJG', '11-04', 2), k('NYG', '11-09', 2), k('NHG', '11-17', 2), k('CC', '11-17', 3), k('NPG', '11-19', 3),
                 (k('NYG', '11-23', 1), {'note': "Printed again, 'with the remarks subjoined to it'."}), k('VGD', '12-04', 1)]),
 dict(id='count-pulaski-to-the-president-of-congress-16-october-1778', kind='document_group',
      label="Count Pulaski to the President of Congress, 16 October 1778: his account of the enemy's attack on his men on the 15th",
      definition="Printings of an extract of a letter from General Count Pulaski to the President of Congress dated 16 October 1778: 'For fear that my first letter concerning my engagement should miscarry or be delayed, and having other particulars to mention, I thought proper to send you this letter'; it gives his account of the enemy's attack on his men on the 15th, at three o'clock in the morning, with 400 men, and of the pursuit. The commander's own report.",
      role='published_document', words=45, dateline=False,
      head=r'(?:Extract\s+of\s+a\s+[Ll]etter\s+from\s+General\s+Count\s+\S+,?\s+to\s+the\s+[Pp]resident\s+of\s+Congress,?\s+dated\s+October\s+16,?\s+1778[.,]?\s*["“]?\s*(?:SIR,?\s*["“]?\s*)?)',
      core=[r'["“]?\s*(?:F\s?OR|For)\s+fear\s+that\s+my\s+(?:first\s+)?letter\s+concerning\s+my\s+engagement'],
      stop=r'["“]?\s*You\s+must\s+know',
      first="Count Pulaski's letter to the President of Congress of 16 October 1778: his account of the enemy's attack on his men and of the pursuit.",
      what="Count Pulaski's letter of 16 October 1778",
      printings=[k('NJG', '10-21', 2), k('CC', '11-03', 2), k('NHG', '11-10', 2), k('NPG', '11-19', 2)]),
 dict(id='admiral-byron-fleet-in-the-storm-november-1778', kind='document_group',
      label="Boston, November 1778: the British fleet under Admiral Byron, cruising near Cape Cod, in the violent storm",
      definition="Printings of a Boston paragraph of 12 November 1778: 'In the violent storm of last week, the wind being at N. E. though variable, the British fleet under the command of Admiral Byron, consisting of sixteen sail of the line, were cruising near Cape Cod'; it reports that the Somerset, of 64 guns, was cast ashore near the Race, at the head of the Cape, and entirely lost. A Boston paper's report, at second hand.",
      role='report', words=45, dateline=True,
      core=[r'(?:I\s?N|In)\s+the\s+(?:late\s+)?violent\s+storm,?\s+(?:of\s+last\s+week,?\s+)?the\s+wind\s+being\s+at\s+N'],
      first="Boston, November 1778: the British fleet under Admiral Byron, sixteen sail of the line, was cruising near Cape Cod in the violent storm.",
      what="the Boston report of Admiral Byron's fleet",
      printings=[k('NHG', '11-17', 2), k('CC', '11-17', 3), k('NPG', '11-19', 3), k('NJG', '11-25', 2)]),
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
            problems.append((s['id'], key, 'page not in the 1778 pages'))
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
        r['id'] = f'S78-{n:03}'
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
               'admission_rule': 'Reviewed 1778 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1778/'
    return {
        'ledger_id': 'ledger:stories-1778', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1778', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1778, and of 1777 where they reach the 1778 pages (long-running ones '
                   'included), a sweep of word-for-word passages shared by 4 or more papers for short items the families miss, counts of every '
                   'candidate by its own opening over all 970 pages of 1778 in both transcriptions, reading of the hits, and scan checks of each '
                   "admitted passage, by the thin-year rule (Y-THIN, as amended with the owner's choice B1): eligible when printed by more than "
                   "half of the papers that survive for the item's weeks and by at least 4; eligible items printed by every paper that survives "
                   'for their weeks admitted; the others chosen to cover the months and the kinds of news'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1777.json': 'retrieval_candidates',
                             d+'counts_1778.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1778.py': 'ledger_code', 'work/archive_data/ledgers/stories_1778_review.json': 'scan_review',
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
