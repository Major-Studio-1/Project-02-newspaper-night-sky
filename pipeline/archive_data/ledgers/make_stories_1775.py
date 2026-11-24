"""Write ledgers/stories_1775.json: reviewed stories of 1775, round one.

1775 is a thin year: no item of 1775 reaches 7 papers, so it is read by the thin-year rule (docs/rules-and-exceptions.md,
Y-THIN, as amended on 23 November 2026, the owner's choice B1): an item, counted by its own words, is eligible when it was
printed by more than half of the newspapers that survive for its weeks (those with a surviving issue between its first and
its last printing, and at least in the three weeks from its first printing), and by at least 4; as in R-01, the items
printed by every newspaper that survives for their weeks are admitted, and the other eligible items are chosen to cover the
months and the kinds of news, about as many stories as a standard year; one affair's items are treated as in X-1800-01;
digests are not admitted. In 1775 5 to 7 papers survive for any item's weeks (6 for most of the year), so every eligible item
is in 4 or more papers.
The automatic families first printed in 1775 that reach 3 or more papers, long-running ones included, were split into
single printed items with work/story_items.py --long-running (items.json), and again with year 1774 over the 1775 pages
(items_from_1774.json); every item in 3 or more papers was compared by machine with every page and counted again by its
opening, a sweep of word-for-word passages shared by 4 or more papers found short items the families miss, and the
admitted and chosen items were counted with phrase searches over all 1,286 pages of 1775 in both transcriptions. See
outputs/story_discovery_1775/README.md and count_1775.md.

The 1775 pages are those whose issue the data release dates to 1775 (work/year_search_pages.py 1775 ... --printed-dates);
no 1775 issue has a corrected date. 1775 has 7 catalogue series, which are 7 papers: the Connecticut Courant (Hartford),
Dunlap's Pennsylvania Packet, Gaine's New-York Gazette, the New-Hampshire Gazette (39 issues, to 12 December), two
Virginia Gazettes of Williamsburg (Dixon and Hunter's, sn84024739; Purdie's, sn84024742, from 3 February) and the
Pennsylvania Journal (one issue, 27 December).
The release's map of misfiled RevX pages (derived/revx_page_map.parquet) lists 2 pages of 1775; on those pages the
excerpt comes from the CA text of the scan page.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1775_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (reviews of other years run at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1775.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1775/search_pages.json). The excerpts are cut from
the 1775 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1775'
D = PROJECT/'outputs/story_discovery_1775'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1775_review.json'
OUT = HERE/'stories_1775.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn82016139': 'The Connecticut Courant', 'sn83021126': "Dunlap's Pennsylvania Packet",
         'sn83030493': "Gaine's New-York Gazette", 'sn83025582': 'The New-Hampshire Gazette',
         'sn84024739': "Dixon and Hunter's Virginia Gazette", 'sn84024742': "Purdie's Virginia Gazette",
         'sn85047530': 'The Pennsylvania Journal'}
ONE = {'CC': 'sn82016139', 'PP': 'sn83021126', 'NYG': 'sn83030493', 'NHG': 'sn83025582', 'VGDH': 'sn84024739', 'VGP': 'sn84024742',
       'PJ': 'sn85047530'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1775), page and edition."""
    return f'{ONE[paper]}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release (2 pages of 1775)."""
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
 # ---- January to March: the opening of Parliament, the Congress's petition, London news ----
 dict(id='opening-of-parliament-november-december-1774', kind='context_group',
      label="The opening of Parliament, 30 November 1774: the King's speech, the Lords' debate and protest on the address, and the Commons' address of thanks",
      children=['kings-speech-to-parliament-30-november-1774', 'house-of-lords-protest-against-the-address-december-1774', 'house-of-commons-address-of-thanks-december-1774'],
      definition="Three papers of the new Parliament's first days, as the colonial papers printed them from the London papers in January and February 1775: the King's speech from the throne of 30 November 1774, the House of Lords' rejection of an amendment to its address and the protest of the Lords who dissented, and the House of Commons' address of thanks. The King's and the Houses' own words."),
 dict(id='kings-speech-to-parliament-30-november-1774', parent='opening-of-parliament-november-december-1774', kind='document_group',
      label="The King's speech to both Houses of Parliament, 30 November 1774: 'a most daring spirit of resistance and disobedience to the law still unhappily prevails in the province of the Massachusetts Bay'",
      definition="Printings of the speech from the throne with which the King opened the new Parliament on 30 November 1774: 'It gives me much concern, that I am obliged, at the opening of this Parliament, to inform you, that a most daring spirit of resistance and disobedience to the law still unhappily prevails in the province of the Massachusetts Bay, and has in divers parts of it broke forth in fresh violences of a very criminal nature'; he says he has taken measures for carrying into execution the laws of the last session and will withstand every attempt to weaken his authority over the colonies. The King's own speech.",
      role='published_document', words=60, dateline=False,
      head=r'(?:M\s?Y\s+L\s?ORDS,?\s+and\s+G\s?ENTLEMEN,?\s*)',
      core=[r'I\s?T\s+gives\s+me\s+much\s+[Cc]oncern,?\s+that\s+I\s+am\s+obliged'],
      first="The King opens Parliament: a daring spirit of resistance and disobedience to the law still prevails in Massachusetts Bay, and he will withstand any attempt to weaken his authority over the colonies.",
      what="the King's speech of 30 November 1774",
      printings=[k('PP', '01-30', 5), k('NHG', '02-03', 4), k('VGP', '02-03', 6), k('VGDH', '02-04', 2), k('CC', '02-06', 2), k('NYG', '02-06', 1)]),
 dict(id='house-of-lords-protest-against-the-address-december-1774', parent='opening-of-parliament-november-december-1774', kind='document_group',
      label="The House of Lords on the address of thanks, December 1774: an amendment asking for the papers on America rejected, and the protest of the Lords who dissented",
      definition="Printings of the House of Lords' proceedings on its address in answer to the King's speech: the motion to add that the Lords would ask for full information on the state of America before the House committed itself was rejected ('Contents 13, Non-contents 63' in one printing), and the Lords who voted for it entered a protest: 'Dissentient, Because we cannot agree to commit ourselves with the careless facility of a common address of compliment, in expressions which may lead to measures in the event fatal to the lives, properties and liberties of a very great part of our fellow subjects'. Counted by the protest. A report of the Lords' vote with the dissenting Lords' own protest.",
      role='published_document', words=60, dateline=False, back=False,
      head=r'D\s?(?:ISSENTIENT|IFFIDENT|I\s?S\s?S\s?E\s?N\s?T\s?I\s?E\s?N\s?T)[,.]?\s*B\s?ECAUSE\s+we\s+',
      core=[r'D\s?ISSENTIENT,?\s+[Bb]ecause\s+we\s+cannot\s+agree', r'cannot\s+agree\s+to\s+(?:commit|submit)\s+(?:ourselves|themselves),?\s+with\s+the\s+careless'],
      first="The House of Lords rejects a motion to ask for the papers on America before addressing the King; the Lords who dissented protest against committing themselves to measures that may be fatal to their fellow subjects.",
      what="the Lords' protest against the address of December 1774",
      printings=[k('NHG', '02-03', 4), k('VGP', '02-03', 6), k('VGDH', '02-04', 2), k('CC', '02-06', 2), k('NYG', '02-06', 1), k('PP', '02-06', 2)]),
 dict(id='house-of-commons-address-of-thanks-december-1774', parent='opening-of-parliament-november-december-1774', kind='document_group',
      label="The House of Commons' address of thanks to the King for his speech, December 1774",
      definition="Printings of the address of thanks for the King's speech that the Speaker of the House of Commons presented in December 1774: 'Most gracious Sovereign, We, your Majesty's most dutiful and loyal subjects, the Commons of Great Britain, in Parliament assembled, return your Majesty our humble thanks for your most gracious speech from the throne'; the address answers the speech's points on America. The House of Commons' own address.",
      role='published_document', words=60, dateline=False, back=True,
      core=[r'your\s+Majesty.?s\s+most\s+dutiful,?\s+(?:and\s+|&\s+)?loyal\s+[Ss]ubjects,?\s+(?:of\s+)?the\s+Commons'],
      first="The House of Commons thanks the King for his speech from the throne.",
      what="the Commons' address of thanks of December 1774",
      printings=[k('PP', '01-30', 5), k('NHG', '02-03', 4), k('CC', '02-06', 2), k('NYG', '02-06', 1), k('VGP', '02-17', 3),
                 (k('VGDH', '02-18', 2), {'core': [r'(?:Most\s+gracious\s+Sovereign,?\s+)?W\s?E,?\s+your\s+Majesty.?s\s+most\s+dutiful'], 'back': False})]),
 dict(id='continental-congress-petition-to-the-king-printed-1775', kind='context_group',
      label="The Continental Congress's petition to the King of October 1774, as printed in 1775, and the colony agents' letter on its delivery",
      children=['continental-congress-petition-to-the-king-october-1774', 'colony-agents-letter-on-the-congress-petition-24-december-1774'],
      definition="The petition to the King that the Congress at Philadelphia adopted in October 1774, which the papers printed in January and February 1775, and the letter of the colony agents in London, dated 24 December 1774, saying they had delivered it to Lord Dartmouth and that the King had received it graciously. The Congress's and the agents' own words."),
 dict(id='continental-congress-petition-to-the-king-october-1774', parent='continental-congress-petition-to-the-king-printed-1775', kind='document_group',
      label="The Continental Congress's petition to the King, October 1774: 'we beg leave to lay our grievances before the throne'",
      definition="Printings of the petition to the King adopted by the Continental Congress in October 1774 and printed by the papers from January 1775: 'To the King's Most Excellent Majesty. Most Gracious Sovereign, We your Majesty's faithful subjects of the colonies of New-Hampshire, Massachusetts-Bay, Rhode-Island and Providence Plantations, Connecticut, New-York, New-Jersey, Pennsylvania, the counties of Newcastle, Kent and Sussex on Delaware, Maryland, Virginia, North-Carolina and South-Carolina, in behalf of ourselves and the inhabitants of those colonies who have deputed us to represent them in General Congress, by this our humble petition, beg leave to lay our grievances before the throne'; it lists the standing army, the new duties and courts and the acts of 1774, and asks the King's interposition. The Congress's own petition (its second petition of July 1775 opens with the same words and is a separate story).",
      role='published_document', words=70, dateline=False,
      head=(r'(?:(?:T\s?HE\s+)?following\s+is\s+the\s+(?:introductory\s+Part\s+of\s+the\s+)?P\s?ETITION\s+of\s+the\s+C\s?ONTINENTAL\s+C\s?ONGRESS[^.]{0,90}?[.,]\s*)?'
            r'(?:To\s+the\s+K\s?ING.?S\s+(?:[Mm]ost\s+)?[Ee]xcellent\s+M\s?AJESTY[.,]?\s*)?(?:M\s?OST\s+)?(?:G\s?RACIOUS\s+)?(?:S\s?OVEREIGN,?\s*)?'),
      core=[r'(?:W\s?E|\bE),?\s+your\s+Majesty.?s\s+(?:most\s+)?faithful\s+[Ss]ubjects\s+of\s+the\s+[Cc]olonies\s+of'],
      first="The Congress petitions the King in the name of twelve colonies, laying before the throne the standing army, the new duties and courts and the acts of 1774, and asking his interposition.",
      what="the Congress's petition to the King of October 1774",
      printings=[k('PP', '01-16', 5), (k('PP', '01-23', 1), {'note': 'Printed again.'}), k('NYG', '01-23', 3), k('CC', '01-30', 4),
                 (k('NHG', '02-03', 2), {'core': [r'(?:T\s?HE\s+)?following\s+is\s+the\s+[Pp]etition\s+of\s+the\s+[Cc]ontinental\s+[Cc]ongress'],
                                          'note': "The paper prints the petition from its middle ('To a sovereign, who glories in the name of Briton'), directly under its heading, as the scan shows; it prints the whole petition on 10 February. Not counted for the paper count (C-06)."}),
                 (k('VGP', '02-03', 5), {'core': [r'(?:T\s?HE\s+)?following\s+true\s+and\s+genuine\s+copy\s+of\s+the\s+petition'],
                                          'note': "The paper's first issue. A fold down the middle of the column hides a few letters in most lines, and the transcription loses them ('W E your MESTY\'s faithful subject the colonies')."}),
                 (k('NHG', '02-10', 2), {'note': 'Printed again, in full.'}), k('VGDH', '02-11', 5)]),
 dict(id='colony-agents-letter-on-the-congress-petition-24-december-1774', parent='continental-congress-petition-to-the-king-printed-1775', kind='message_group',
      label="The colony agents' letter from London, 24 December 1774: the Congress's petition delivered to Lord Dartmouth, and 'his Majesty had been pleased to receive it very graciously'",
      definition="Printings of the letter that the agents of the colonies in London sent to the speakers of the assemblies on 24 December 1774: 'having received the Petition of the General Congress to the King, we immediately communicated the same to Lord Dartmouth, Secretary of State for the American Department', who told them that the King had received it very graciously and would lay it before his two Houses of Parliament when they met. The agents' own letter.",
      role='report', words=60, dateline=False, back=True,
      head=(r'(?:A\s+[Ll]etter\s+(?:from\s+the\s+several\s+Agents|to\s+the\s+Hon\.\s+the\s+S\s?PEAKER).{0,200}?(?:1774|King)\.\s*)?'
            r'S\s?IR,?\s*(?:L\s?ONDON,?\s+Dec\w*\.?\s*24,?\s*1774\.?\s*)?(?:T\s?\s?HIS|This)\s+is\s+just\s+to\s+inform\s+you,?\s+that\s+'),
      core=[r'having\s+received\s+the\s+[Pp]etition\s+of\s+the\s+(?:[Gg]eneral\s+)?C\s?ONGRESS\s+to\s+the\s+K\s?ING'],
      first="The colony agents in London report that they gave the Congress's petition to Lord Dartmouth, and that the King received it very graciously and will lay it before Parliament.",
      what="the agents' letter on the petition",
      printings=[k('VGP', '03-17', 7), k('VGDH', '03-18', 3), k('PP', '03-20', 4), k('CC', '03-27', 2), k('NHG', '03-31', 1), k('NYG', '04-03', 3)]),
 dict(id='london-member-asks-the-lord-mayor-about-the-kings-speech-1774', kind='message_group',
      label="London, December 1774: a member of a certain assembly asks the Lord Mayor how he liked the King's speech ('What speech?')",
      definition="Printings of a paragraph of the London news of December 1774: 'A Gentleman who is a member of a certain assembly, asked the Lord Mayor, a few days ago, how he liked the King's Speech. What Speech? answers the Lord Mayor. Why, that printed speech in your hand, replies the member. You mistake, cries my Lord, this is no speech, it is the American death warrant.' An anecdote from the London papers (the Lord Mayor was John Wilkes), a single paragraph of the papers' London news.",
      role='report', words=50, dateline=False,
      core=[r'G\s?entleman,?\s+who\s+is\s+a\s+[Mm]ember\s+of\s+a\s+certain\s+a\S{0,3}\s?embly'], back=True,
      first="London: asked how he liked the King's speech, the Lord Mayor answers that it is no speech but the American death warrant.",
      what="the London anecdote of the Lord Mayor and the King's speech",
      printings=[k('PP', '01-30', 5), k('NHG', '02-10', 4), k('CC', '02-13', 2), k('NYG', '02-13', 1), k('VGP', '02-24', 2), k('VGDH', '02-25', 2)]),
 dict(id='london-ministers-said-to-be-offended-with-general-gage-1774', kind='message_group',
      label="London, 13 December 1774: 'The ministers, it is said, are much offended with General Gage', who acted on the defensive",
      definition="Printings of a paragraph of the London news of 13 December 1774: 'The ministers, it is said, are much offended with General Gage. They certainly have great reason, for he has most grievously disappointed them. They had great hopes of throwing the blame upon him; but he acting upon the defensive has thrown it upon them.' A London report, at second hand ('it is said'), with the London writer's comment; a single paragraph of the papers' London news.",
      role='report', words=50, dateline=False, back=True,
      core=[r'[Mm]ini[sſf]t(?:ers|ry),?\s+it\s+is\s+[sſf]aid,?\s+(?:are|is)\s+much\s+offended\s+with\s+Gen(?:eral|\.)?\s+G\s?AGE'],
      first="London: the ministers are said to be offended with General Gage, whose acting on the defensive has turned the blame on them.",
      what="the London paragraph on the ministers and General Gage",
      printings=[k('PP', '02-06', 2), k('NHG', '02-10', 4), k('CC', '02-13', 2), k('NYG', '02-13', 2), k('VGP', '02-17', 5), k('VGDH', '02-18', 2)]),
 dict(id='london-transports-for-ireland-howe-and-draper-1774', kind='message_group',
      label="London, December 1774: transports sail for Ireland to take on four regiments; Major General Howe and Sir William Draper to go out as brigadiers",
      definition="Printings of a paragraph of the London news of December 1774: 'A number of transports are sailed for Ireland, to receive on board the 22d, 49th, 55th, and 63d regiments. Major General Howe and Sir William Draper, are going out as Brigadiers on the Staff.' A London report, a single paragraph of the papers' London news.",
      role='report', words=40, dateline=False,
      core=[r'[Nn]umber\s+of\s+[Tt]ransports\s+(?:are\s+)?(?:s|f)ailed\s+for\s+Ireland'], back=True,
      stop=r'(?<=[Ss]taff\.)\s',
      first="London: transports sail for Ireland to embark four regiments, and Major General Howe and Sir William Draper are to go out as brigadiers.",
      what="the London paragraph on the transports for Ireland",
      printings=[k('NYG', '02-06', 2), k('PP', '02-06', 2), k('NHG', '02-17', 4), k('VGP', '02-17', 3), k('VGDH', '02-18', 2), k('CC', '02-20', 2)]),
 dict(id='lord-north-on-the-merchants-meetings-january-1775', kind='message_group',
      label="London, 7 January 1775: Lord North is said to have declared that, far from the merchants' meetings being disagreeable to him, he wishes for as much information as possible on America",
      definition="Printings of a paragraph of the London news of 7 January 1775: 'Lord North has publicly declared, that so far from the meetings of the American and West India Merchants being disagreeable to him, he, on the contrary, wishes for nothing more than as much information as possible on the American business to be laid before Parliament as soon as possible.' A London report of Lord North's words, a single paragraph of the papers' London news.",
      role='report', words=50, dateline=False,
      core=[r'Lord\s+N\s?ORTH\s+ha(?:s|th)\s+(?:publick?ly\s+)?declared'],
      stop=r'(?<=possible\.)\s',
      first="London: Lord North is reported to say that the merchants' meetings are not disagreeable to him and that he wants full information on America laid before Parliament.",
      what="the London paragraph on Lord North and the merchants",
      printings=[k('PP', '03-06', 5), k('NYG', '03-13', 2), k('VGP', '03-17', 5), k('VGDH', '03-18', 2), k('CC', '03-20', 2), k('NHG', '03-24', 1)]),
 dict(id='massachusetts-provincial-congress-resolves-february-1775', kind='document_group',
      label="The Massachusetts Provincial Congress, February 1775: the militia and minute men to perfect themselves in discipline, and the towns to encourage the making of fire-arms",
      definition="Printings of resolves of the Provincial Congress of Massachusetts Bay of February 1775, with the address to the inhabitants that some papers print before them: since a large reinforcement of troops is expected and the province's destruction appears intended, 'RESOLVED, That the great Law of self Preservation, calls upon the Inhabitants of this Colony, immediately to prepare against every Attempt that may be made to attack them by Surprise'; the militia and the minute men are to perfect themselves in military discipline, and the towns to encourage persons skilled in making fire-arms and bayonets. Counted by the resolves. The Provincial Congress's own resolves.",
      role='published_document', words=60, dateline=False, back=True,
      head=r'(?:T\s?HEREFORE,?\s+)?R\s?ESOLVED\s*,?\s+[Tt]hat\s+the\s+',
      core=[r'great\s+[Ll]aw\s+of\s+[sſfS]el[fſs][\s\-]*[Pp]re[sſf]ervation'],
      first="The Massachusetts Provincial Congress resolves that the inhabitants must prepare against a surprise attack: the militia and minute men are to train, and the towns to encourage the making of arms.",
      what="the Massachusetts Provincial Congress's resolves of February 1775",
      printings=[k('NHG', '02-24', 4), k('CC', '02-27', 2), k('NYG', '02-27', 3), k('PP', '03-06', 4), k('VGP', '03-10', 2), k('VGDH', '03-11', 3)]),
 dict(id='new-york-assembly-mr-thomas-motion-23-february-1775', kind='document_group',
      label="The New York General Assembly, 23 February 1775: Mr. Thomas's motion on the necessity of appointing delegates to the next Continental Congress, and the vote",
      definition="Printings of an extract from the votes and proceedings of the General Assembly of New York of 23 February 1775: 'A Motion was made by Mr. Thomas, in the Words following, viz. Mr. Speaker, I Move that the Sense of this House be taken, on the Necessity of appointing Delegates for this Colony, to meet the Delegates of the other Colonies on this Continent, in General Congress, on the 10th Day of May next'; the debates that followed and the vote, in which the motion was rejected. The Assembly's own votes.",
      role='published_document', words=60, dateline=False,
      head=r'(?:E\s?XTRACT\s+from\s+the\s+V\s?OTES\s+and\s+P\s?ROCEEDINGS\s+of\s+the\s+G\s?ENERAL\s+A\s?SSEMBLY\s+of\s+this\s+C\s?olony\.?\s*)?(?:Die\s+Jovis[^.]{0,60}\.\s*)?',
      core=[r'A\s+M\s?otion\s+was\s+made\s+by\s+Mr\.?\s+Thomas'],
      first="The New York Assembly votes on Mr. Thomas's motion to appoint delegates to the Continental Congress of May 1775.",
      what="the New York Assembly's vote of 23 February 1775",
      printings=[k('NYG', '02-27', 3), k('CC', '03-06', 2), k('PP', '03-06', 4), k('NHG', '03-10', 1), k('VGP', '03-17', 7), k('VGDH', '03-18', 3)]),
 dict(id='admiral-parry-ordered-to-boston-march-1775', kind='message_group',
      label="New York, March 1775: a captain from Antigua reports that Admiral Parry and his squadron are ordered to Boston",
      definition="Printings of a New York paragraph of early March 1775: 'We are informed by a Captain of a vessel who arrived here a few days ago from Antigua, that Admiral Parry with the royal squadron under his command, on that station, has received orders to sail for Boston, where this gentleman will be second in command'. A report at second hand, from a ship's captain; a single paragraph of the papers' news (some papers print it after a paragraph on orders from Virginia for arms, which is counted apart).",
      role='report', words=50, dateline=False,
      core=[r'[Cc]aptain\s+of\s+(?:a\s+)?[Vv]essel,?\s+who\s+arrived\s+(?:here\s+)?a\s+few\s+[Dd]ays\s+ago\s+from\s+Antigua', r'[Cc]aptain\s+of\s+a\s+[Vv]essel\s+from\s+Antigua,?\s+that\s+Admiral\s+Parry'], back=True,
      first="New York: a captain arrived from Antigua says Admiral Parry and his squadron are ordered to Boston.",
      what="the New York paragraph on Admiral Parry",
      printings=[k('CC', '03-06', 2), k('NYG', '03-06', 3), k('PP', '03-06', 3), k('NHG', '03-17', 1), k('VGP', '03-17', 7), k('VGDH', '03-18', 3)]),
 # ---- April to June ----
 dict(id='provincial-congress-on-the-commencement-of-hostilities-april-1775', kind='context_group',
      label="The fighting of 19 April 1775 at Lexington and Concord, as the Massachusetts Provincial Congress published it: depositions, and its address to the inhabitants of Great Britain",
      children=['provincial-congress-depositions-on-the-commencement-of-hostilities-1775', 'deposition-of-lieutenant-gould-april-1775'],
      definition="The papers that the Provincial Congress of Massachusetts Bay published on the first fighting of the war, the march of the King's troops to Lexington and Concord on 19 April 1775, as the papers printed them in May and June: the depositions it took and its address to the inhabitants of Great Britain, and the deposition of an officer of the King's troops taken prisoner. The Provincial Congress's publication and the deponents' sworn accounts."),
 dict(id='provincial-congress-depositions-on-the-commencement-of-hostilities-1775', parent='provincial-congress-on-the-commencement-of-hostilities-april-1775', kind='document_group',
      label="Affidavits and depositions relative to the commencement of the late hostilities in Massachusetts Bay, with the Provincial Congress's address to the inhabitants of Great Britain (published May 1775)",
      definition="Printings of the publication of the Provincial Congress of Massachusetts Bay: 'Affidavits and depositions, relative to the commencement of the late hostilities in the province of Massachusetts Bay: together with an address from the Provincial Convention of said province, to the inhabitants of Great-Britain', transmitted to the Congress at Philadelphia; the depositions are sworn accounts by inhabitants of Lexington and Concord, and the address begins 'Friends and fellow subjects, Hostilities are at length commenced in this colony by the troops under command of General Gage'. The Provincial Congress's publication of the deponents' sworn accounts; the accounts are the deponents'.",
      role='published_document', words=60, dateline=False, back=True,
      head=r'A\s?FFIDAVITS,?\s+(?:and|AND)\s+',
      core=[r'D\s?EPOSITIONS,?\s+[Rr]elative\s+to\s+the\s+C\s?OMMENCEMENT\s+of\s+the\s+late\s+H\s?OSTILITIES'],
      first="The Provincial Congress publishes depositions on the beginning of hostilities at Lexington and Concord, with its address to the people of Great Britain.",
      what="the Provincial Congress's depositions on the commencement of hostilities",
      printings=[k('PP', '05-15', 2), k('CC', '05-22', 2), k('NYG', '05-22', 1), k('NHG', '06-02', 2)]),
 dict(id='deposition-of-lieutenant-gould-april-1775', parent='provincial-congress-on-the-commencement-of-hostilities-april-1775', kind='document_group',
      label="The deposition of Lieutenant Edward Thoroton Gould, of the King's Own regiment, wounded and taken prisoner, on the march to Concord on 19 April 1775",
      definition="Printings of the deposition that Edward Thoroton Gould, an officer of the King's Own regiment of foot taken prisoner, made before the Massachusetts authorities and that the Provincial Congress published: 'I Edward Thoroton Gould, of his Majesty's own regiment of foot, being of lawful age, do testify and declare, that on the evening of the 18th instant, under the orders of General Gage, I embarked with the light infantry and grenadiers of the line'; he describes the march to Concord and the firing at the bridge. The officer's own sworn account, as the Provincial Congress published it.",
      role='published_document', words=60, dateline=False,
      core=[r'E\s?DWARD\s+T\s?HOROTON\s+G\s?OULD'],
      first="A wounded British officer taken prisoner gives his sworn account of the march to Concord and the firing at the bridge.",
      what="Lieutenant Gould's deposition",
      printings=[k('PP', '05-15', 3), k('NYG', '05-22', 2), k('CC', '05-29', 2), k('VGP', '06-02', 6), k('VGDH', '06-03', 3)]),
 dict(id='ticonderoga-taken-report-of-john-brown-may-1775', kind='message_group',
      label="Philadelphia, May 1775: John Brown, express from Ticonderoga to the Congress, reports that the fort was taken by men from Connecticut and Massachusetts",
      definition="Printings of a Philadelphia report of May 1775: 'On Wednesday evening last arrived here, John Brown, Esq; from Ticonderoga, express to the General Congress, from whom we learn, that on the beginning of this instant, a company of about fifty men, from Connecticut, and the western part of Massachusetts' 'and joined by upwards of one hundred from Bennington', took the fort of Ticonderoga; it adds news of the Indians in Canada. A Philadelphia report of what the express said.",
      role='report', words=60, dateline=False, back=True,
      core=[r'John\s+Brown,?\s+Esq;?,?\s+from\s+Ticonderoga'],
      first="Philadelphia: an express from Ticonderoga tells the Congress that men from Connecticut and western Massachusetts have taken the fort.",
      what="the Philadelphia report of the taking of Ticonderoga",
      printings=[k('PP', '05-22', 3), k('NYG', '05-29', 2), k('VGP', '06-02', 6), k('VGDH', '06-03', 2)]),
 dict(id='livery-of-london-address-and-the-kings-answer-april-1775', kind='context_group',
      label="The Livery of London's address, remonstrance and petition to the King, April 1775, and the King's answer",
      children=['livery-of-london-address-remonstrance-and-petition-april-1775', 'kings-answer-to-the-livery-of-london-april-1775'],
      definition="The address, remonstrance and petition that the Lord Mayor, Aldermen and Livery of London in Common Hall presented to the King on 10 April 1775 against the measures for America, and the King's answer, as the papers printed them in June 1775. The City's and the King's own words."),
 dict(id='livery-of-london-address-remonstrance-and-petition-april-1775', parent='livery-of-london-address-and-the-kings-answer-april-1775', kind='document_group',
      label="The address, remonstrance and petition of the Lord Mayor, Aldermen and Livery of London to the King against the measures for America (April 1775)",
      definition="Printings of 'The humble Address, Petition, and Remonstrance of the Lord Mayor, Aldermen, and Livery of the City of London, in Common Hall assembled' to the King: 'We your Majesty's dutiful and loyal subjects' 'beg leave to approach the throne, and to declare our abhorrence of the measures which have been pursued, and are now pursuing' against the colonies, and ask the King to dismiss his ministers. The Livery's own address.",
      role='published_document', words=60, dateline=False,
      head=r'(?:To\s+the\s+K\s?ING.?S\s+(?:[Mm]ost\s+)?[Ee]xcellent\s+M\s?AJESTY\.?\s*)?(?:The\s+humble\s+)?',
      core=[r'A\s?DDRESS,?\s+(?:P\s?ETITION,?\s+and\s+R\s?EMONSTRANCE|R\s?EMONSTRANCE,?\s+and\s+P\s?ETITION),?\s+of\s+the\s+L\s?ORD[\s\-]+M\s?AYOR', r'W\s?E\s+your\s+Majesty.?s\s+dutiful\s+and\s+loyal\s+[Ss]ubjects[;,]?\s+the\s+Lord\s+Mayor'],
      first="The Livery of London petitions the King against the measures pursued in America and asks him to dismiss his ministers.",
      what="the Livery of London's address of April 1775",
      printings=[k('PP', '06-05', 2), k('NHG', '06-09', 2), k('CC', '06-12', 4), k('NYG', '06-12', 2),
                 (k('VGP', '06-16', 5), {'core': [r'humble\s+A\s?DDRESS,?\s+R\s?EMONSTRANCE,?\s+and\s+P\s?ETITION']}), k('VGDH', '06-17', 2)]),
 dict(id='kings-answer-to-the-livery-of-london-april-1775', parent='livery-of-london-address-and-the-kings-answer-april-1775', kind='document_group',
      label="The King's answer to the Livery of London: 'It is with the utmost astonishment that I find any of my subjects capable of encouraging the rebellious disposition'",
      definition="Printings of the King's answer to the address, remonstrance and petition of the Livery of London, April 1775: 'It is with the utmost astonishment that I find any of my subjects capable of encouraging the rebellious disposition which unhappily exists in some of my colonies in North America'; he says he will continue to pursue the measures of Parliament. The King's own answer.",
      role='published_document', words=50, dateline=False, back=True,
      core=[r'I\s?T\s+is\s+with\s+the\s+utmost\s+[Aa]stonishment'],
      first="The King answers the Livery of London with astonishment that any of his subjects encourage the rebellious disposition in America.",
      what="the King's answer to the Livery of London",
      printings=[k('NHG', '06-09', 2), k('CC', '06-12', 4), k('NYG', '06-12', 2), k('PP', '06-12', 4), k('VGP', '06-16', 5), k('VGDH', '06-17', 2)]),
 dict(id='providence-letter-on-the-contest-of-17-june-1775', kind='message_group',
      label="A gentleman in Providence to his friend in New York, 20 June 1775: a narrative of the contest of 17 June between the King's troops and 'our army' at Charlestown",
      definition="Printings of an extract of a letter from a gentleman in Providence (45 miles from Boston) to his friend in New York, dated 20 June 1775: 'You doubtless have been alarmed with divers Accounts of the Contest which happened on the 17th Inst. between the King's Troops and our Army; shall give you a Narrative in a few Words'; it tells how Colonel Putnam took possession of Bunker's Hill on the evening of the 15th and began an entrenchment, and gives the writer's account of the battle and the losses as he heard them. A private letter at second hand, from the American side, with the writer's own figures.",
      role='report', words=60, dateline=False, back=True,
      core=[r'doubtless\s+have\s+been\s+alarmed\s+with\s+divers\s+[Aa]ccounts'],
      first="A letter from Providence gives a short narrative of the battle of 17 June at Charlestown between the King's troops and the provincial army.",
      what="the Providence letter on the battle of 17 June",
      printings=[k('NYG', '06-26', 3), k('PP', '07-03', 4), k('VGP', '07-14', 5), k('VGDH', '07-15', 1)]),
 dict(id='addresses-to-generals-washington-and-lee-june-july-1775', kind='context_group',
      label="Addresses to General Washington and General Lee, June and July 1775, and Washington's answer",
      children=['new-york-provincial-congress-address-to-washington-june-1775', 'massachusetts-provincial-congress-address-to-washington-july-1775',
                'washington-answer-to-the-massachusetts-provincial-congress-july-1775', 'massachusetts-provincial-congress-address-to-general-lee-july-1775'],
      definition="The addresses that the Provincial Congress of New York presented to General Washington on his way to the army, and that the Provincial Congress of Massachusetts presented to him and to General Lee on their arrival at Cambridge, with Washington's answer to the Massachusetts Congress, as the papers printed them in July and August 1775. The Congresses' and the general's own words."),
 dict(id='new-york-provincial-congress-address-to-washington-june-1775', parent='addresses-to-generals-washington-and-lee-june-july-1775', kind='document_group',
      label="The New York Provincial Congress's address to General Washington, June 1775",
      definition="Printings of the address of the Provincial Congress of New York 'To his Excellency, George Washington, Generalissimo of all the Forces raised and to be raised in the confederated Colonies of America': 'At a time when the most loyal of his Majesty's subjects, from a regard to the laws and constitution, by which he sits on the throne, feel themselves reduced to the unhappy necessity of taking up arms', the Congress welcomes him and trusts that he will lay down his command when an accommodation is made. The Provincial Congress's own address.",
      role='published_document', words=60, dateline=False,
      head=r'(?:(?:(?:The\s+Address\s+of\s+the\s+Provincial\s+Congress\s+of\s+the\s+Colony\s+of\s+New[\s\-]York\s+)?To\s+his\s+E\s?XCELLENCY,?\s+)?G\s?EORGE\s+W\s?ASHINGTON,?\s*(?:Esq;?,?\s*)?)?',
      core=[r'G\s?ENERALISSIMO\s+of\s+all\s+the\s+[Ff]orces'],
      first="The New York Provincial Congress welcomes General Washington and trusts he will resign his command once the colonies are reconciled with Britain.",
      what="the New York Provincial Congress's address to Washington",
      printings=[k('CC', '07-03', 2), k('NYG', '07-03', 3), k('PP', '07-03', 2), k('NHG', '07-11', 1), k('VGP', '07-14', 3), k('VGDH', '07-15', 3)]),
 dict(id='massachusetts-provincial-congress-address-to-washington-july-1775', parent='addresses-to-generals-washington-and-lee-june-july-1775', kind='document_group',
      label="The Massachusetts Provincial Congress's address to General Washington on his arrival at Cambridge, July 1775",
      definition="Printings of the address of the Provincial Congress of Massachusetts Bay 'To his Excellency George Washington, Esq; General and Commander in Chief of the Continental Army': 'The Congress of the Massachusetts Colony, impressed with every sentiment of gratitude and respect, beg leave to congratulate your Excellency on your safe arrival'; it describes the state of the province and of its army. The Provincial Congress's own address.",
      role='published_document', words=60, dateline=False, back=True,
      core=[r'T\s?HE\s+C\s?ongress\s+of\s+the\s+Massachusetts\s+Colony,?\s+impressed'],
      first="The Massachusetts Provincial Congress congratulates General Washington on his arrival at Cambridge and describes the state of the province and its army.",
      what="the Massachusetts Provincial Congress's address to Washington",
      printings=[k('CC', '07-10', 3), k('NHG', '07-11', 1), k('NYG', '07-17', 2), k('PP', '07-17', 2), k('VGP', '08-04', 1), k('VGDH', '08-05', 2)]),
 dict(id='washington-answer-to-the-massachusetts-provincial-congress-july-1775', parent='addresses-to-generals-washington-and-lee-june-july-1775', kind='document_group',
      label="General Washington's answer to the Massachusetts Provincial Congress, July 1775: 'Your kind congratulations on my appointment and arrival demand my warmest acknowledgments'",
      definition="Printings of General Washington's answer to the address of the Massachusetts Provincial Congress: 'Gentlemen, Your kind congratulations on my appointment and arrival, demand my warmest acknowledgments, and will ever be retained in grateful remembrance. In exchanging the enjoyments of domestic life for the duties of my present honourable, but arduous station, I only emulate the virtue and public spirit of the whole province of the Massachusetts-Bay'. The general's own answer.",
      role='published_document', words=50, dateline=False, back=True,
      core=[r'Y\s?OUR\s+kind\s+[Cc]ongratulations\s+on\s+my\s+[Aa]ppointment'],
      first="General Washington thanks the Massachusetts Provincial Congress and says he only emulates the public spirit of the province.",
      what="Washington's answer to the Massachusetts Provincial Congress",
      printings=[k('CC', '07-10', 3), k('NHG', '07-11', 1), k('NYG', '07-17', 2), k('PP', '07-17', 2), k('VGP', '08-04', 2), k('VGDH', '08-05', 2)]),
 dict(id='massachusetts-provincial-congress-address-to-general-lee-july-1775', parent='addresses-to-generals-washington-and-lee-june-july-1775', kind='document_group',
      label="The Massachusetts Provincial Congress's address to General Lee, July 1775",
      definition="Printings of the address of the Provincial Congress of Massachusetts Bay to Charles Lee, major general of the Continental army, on his arrival at Cambridge: it congratulates him on his safe arrival and says 'We admire and respect the character of a man who, disregarding the allurements of wealth and distinction his merit might procure, engages in the cause of mankind, in defence of the injured, and relief of the oppressed'. The Provincial Congress's own address.",
      role='published_document', words=60, dateline=False, back=True,
      core=[r'T\s?O\s+the\s+H\s?ON(?:OU?RABLE|\.)\s+C\s?HARLES\s+L\s?EE', r'We\s+admire\s+and\s+respect\s+the\s+[Cc]haracter\s+of\s+a\s+[Mm]an'],
      first="The Massachusetts Provincial Congress welcomes General Lee, who gave up the prospects his merit might have won to serve the cause of the oppressed.",
      what="the Massachusetts Provincial Congress's address to General Lee",
      printings=[k('CC', '07-10', 3), k('NHG', '07-11', 1), k('NYG', '07-17', 2), k('PP', '07-17', 2), (k('VGP', '08-04', 2), {'back': False}), k('VGDH', '08-05', 2)]),
 dict(id='continental-congress-july-1775', kind='context_group',
      label="The Continental Congress at Philadelphia, July 1775: its resolve on the restraining acts, its declaration of the causes of taking up arms, and its second petition to the King",
      children=['continental-congress-resolve-on-the-restraining-acts-4-july-1775', 'declaration-of-the-causes-and-necessity-of-taking-up-arms-1775',
                'continental-congress-second-petition-to-the-king-8-july-1775'],
      definition="Three papers of the second Continental Congress, as the papers printed them from July 1775: its resolve of 4 July on the two acts restraining the trade of the colonies, its declaration of 6 July setting forth the causes and necessity of taking up arms, and its petition to the King of 8 July. The Congress's own words."),
 dict(id='continental-congress-resolve-on-the-restraining-acts-4-july-1775', parent='continental-congress-july-1775', kind='document_group',
      label="The Continental Congress's resolve of 4 July 1775 on the two acts restraining the trade of the colonies",
      definition="Printings of the resolve of the Continental Congress of 4 July 1775: 'Resolved, that the two acts passed in the first session of the present parliament, the one entitled \"an act to restrain the trade and commerce of the provinces of Massachusetts Bay and New Hampshire, and colonies of Connecticut and Rhode Island and Providence plantations\"', and the act restraining the trade of the other colonies; the Congress resolves against them. The Congress's own resolve.",
      role='published_document', words=60, dateline=False,
      head=r'(?:I\s?N\s+(?:C\s?ONTINENTAL\s+)?C\s?ONGRESS,?\s+J\s?ULY\s+1?4(?:th)?,?\s*(?:1775)?\.?\s*)?R\s?ESOLVED\s*,?\s+(?:T\s?HAT|that)\s+the\s+',
      core=[r'two\s+[Aa]cts\s+passed\s+in\s+the\s+first\s+[Ss]ession\s+of\s+the\s+present\s+[Pp]arliament'],
      first="The Congress resolves against the two acts of Parliament that restrain the trade of the colonies.",
      what="the Congress's resolve on the restraining acts",
      printings=[k('PP', '07-10', 3), k('NYG', '07-10', 2), k('CC', '07-17', 3), k('VGP', '07-21', 11), k('VGDH', '07-22', 2), k('NHG', '07-25', 2)]),
 dict(id='declaration-of-the-causes-and-necessity-of-taking-up-arms-1775', parent='continental-congress-july-1775', kind='document_group',
      label="A declaration by the representatives of the United Colonies, 6 July 1775, setting forth the causes and necessity of their taking up arms",
      definition="Printings of 'A Declaration by the Representatives of the United Colonies of North-America, now met in General Congress at Philadelphia, setting forth the Causes and Necessity of their taking up Arms': 'If it was possible for men, who exercise their reason, to believe, that the divine Author of our existence intended a part of the human race to hold an absolute property in, and an unbounded power over others'; it recites the colonies' grievances and declares that they have taken up arms in defence of their liberty and will lay them down when hostilities cease. The New-Hampshire Gazette prints only a report that it was read to the army, with its title (not counted). The Congress's own declaration.",
      role='published_document', words=60, dateline=False,
      head=r'(?:A\s+D\s?ECLARATION,?\s+by\s+the\s+R\s?EPRESENTATIVES\s+of\s+the\s+U\s?NITED\s+C\s?OLONIES\s+of\s+N\s?ORTH[\s\-]A\s?MERICA,?\s*)?(?:now\s+met\s+in\s+G\s?ENERAL\s+C\s?ONGRESS\s+at\s+Philadelphia,?\s*)?',
      core=[r'setting\s+forth\s+the\s+[Cc]auses\s+and\s+[Nn]ecessity\s+of\s+their\s+taking\s+up\s+A\s?RMS'],
      first="The Congress declares the causes that compel the colonies to take up arms, and that they will lay them down when hostilities cease.",
      what="the declaration of the causes of taking up arms",
      printings=[k('PP', '07-10', 3), k('CC', '07-17', 2), k('NYG', '07-17', 1), k('VGP', '07-21', 6), k('VGDH', '07-22', 1)]),
 dict(id='continental-congress-second-petition-to-the-king-8-july-1775', parent='continental-congress-july-1775', kind='document_group',
      label="The Continental Congress's second petition to the King, 8 July 1775: 'the union between our Mother Country and these colonies'",
      definition="Printings of the petition to the King adopted by the Continental Congress on 8 July 1775: 'To the King's Most Excellent Majesty. Most Gracious Sovereign, We your Majesty's faithful subjects of the colonies of New-Hampshire, Massachusetts-Bay', and the others, ask the King to procure a happy and permanent reconciliation, and that in the meantime measures be taken to prevent the further destruction of lives and to repeal the statutes that most distress the colonies. The Congress's own petition (its petition of October 1774 opens with the same words and is a separate story).",
      role='published_document', words=70, dateline=False,
      head=r'To\s+the\s+K\s?ING.?S\s+(?:[Mm]ost\s+)?[Ee]xcellent\s+M\s?AJESTY[.,]?\s*(?:M\s?OST\s+)?(?:G\s?RACIOUS\s+)?(?:S\s?OVEREIGN,?\s*)?',
      core=[r'(?:W\s?E|\bE),?\s+your\s+Majesty.?s\s+(?:most\s+)?faithful\s+[Ss]ubjects\s+of\s+the\s+[Cc]olonies\s+of'],
      first="The Congress petitions the King again, asking him to procure a reconciliation and, meanwhile, to stop the bloodshed and repeal the acts that most distress the colonies.",
      what="the Congress's second petition to the King",
      printings=[k('NYG', '08-21', 3), k('PP', '08-21', 5), k('CC', '08-28', 1), k('VGDH', '09-02', 2), k('NHG', '09-05', 1), k('VGP', '12-15', 1)]),
 dict(id='burgoyne-and-lee-letters-june-july-1775', kind='context_group',
      label="General Burgoyne and General Lee, July 1775: Burgoyne's letter proposing an interview, and Lee's answer declining it",
      children=['burgoyne-letter-to-lee-july-1775', 'lee-answer-to-burgoyne-11-july-1775'],
      definition="The letters exchanged by two former comrades on opposite sides, as the papers printed them in July and August 1775: General Burgoyne's answer from Boston to a letter of General Lee, proposing an interview, and Lee's answer from Cambridge declining it. The generals' own letters."),
 dict(id='burgoyne-letter-to-lee-july-1775', parent='burgoyne-and-lee-letters-june-july-1775', kind='message_group',
      label="General Burgoyne's letter to General Lee from Boston, July 1775: 'When we were last together in service'",
      definition="Printings of the letter that General Burgoyne wrote from Boston in July 1775 in answer to one from General Lee: 'Dear Sir, When we were last together in service, I should not have thought it within the vicissitude of human affairs, that we should meet at any time, or in any sense, as foes'; he defends the authority of Parliament and proposes an interview on Boston Neck. General Burgoyne's own letter.",
      role='report', words=60, dateline=False, back=True,
      head=r'D\s?EAR\s+S\s?IR,?\s*(?:B\s?OSTON,?\s+July\s+9,?\s*1775\.?\s*)?',
      core=[r'W\s?HEN\s+we\s+were\s+last\s+together\s+in\s+[Ss]ervice'],
      first="General Burgoyne answers his old comrade General Lee from Boston, defends the authority of Parliament and proposes an interview.",
      what="General Burgoyne's letter to General Lee",
      printings=[k('NHG', '07-25', 1), k('CC', '08-07', 1), k('NYG', '08-07', 2), k('PP', '08-07', 5), k('VGP', '08-18', 3), k('VGDH', '08-19', 4)]),
 dict(id='lee-answer-to-burgoyne-11-july-1775', parent='burgoyne-and-lee-letters-june-july-1775', kind='message_group',
      label="General Lee's answer to General Burgoyne, Cambridge, 11 July 1775, declining the interview",
      definition="Printings of General Lee's note from the headquarters at Cambridge, 11 July 1775: 'General Lee's compliments to General Burgoyne. Would be extremely happy in the interview he so kindly proposed. But as he perceives that General Burgoyne has already made up his mind on this great subject', he declines it, lest it give rise to jealousies. General Lee's own letter.",
      role='report', words=50, dateline=False, back=True,
      core=[r'G\s?ENERAL\s+L\s?EE.?S\s+[Cc]ompliments\s+to\s+G\s?eneral\s+B\s?URGOYNE'],
      first="General Lee declines General Burgoyne's proposed interview, since Burgoyne's mind is already made up.",
      what="General Lee's answer to General Burgoyne",
      printings=[k('NHG', '07-25', 1), k('CC', '08-07', 1), k('NYG', '08-07', 2), k('PP', '08-07', 2), k('VGP', '08-18', 4), k('VGDH', '08-19', 4)]),
 dict(id='west-indies-report-of-the-parliament-house-pulled-down-1775', kind='message_group',
      label="New York, July 1775: captains from Dominica and St. Kitts are said to confirm the report that the Parliament House was pulled down and Lord North fled to France",
      definition="Printings of a report of late July 1775: 'Captain Lowndes, from Dominica, and Captain Hodge, from St. Kitts, confirm the above accounts' (of the Parliament House pulled down and Lord North fled to France), adding that a ship had arrived at St. Eustatia from Amsterdam with the same news. A report at second and third hand of a rumour from the West Indies; the papers print it as news.",
      role='report', words=50, dateline=False, back=True,
      head=r'C\s?APT(?:AIN|\.)\s*',
      core=[r'Lownde?r?s,?\s+from\s+Dominica'],
      first="New York: captains from the West Indies are said to confirm a rumour that the Parliament House was pulled down and Lord North fled to France.",
      what="the West Indies report of the Parliament House pulled down",
      printings=[k('NYG', '07-31', 3), k('CC', '08-07', 3), k('PP', '08-07', 6), k('VGDH', '08-12', 3), k('NHG', '08-15', 1), k('VGP', '08-18', 1)]),
 dict(id='philadelphia-letter-of-29-july-on-a-london-letter-of-31-may-1775', kind='message_group',
      label="Philadelphia, 29 July 1775: a letter quoting a London letter of 31 May on how London received the news of the defeat of Colonel Smith",
      definition="Printings of an extract of a letter from Philadelphia of 29 July 1775: 'I have a Letter from London, dated May 31, (by the Ship Rebecca, Capt. Hazelwood...) says, \"You will find by the Papers, that we have received an Account from Salem, of the Defeat of Col. Smith, and the precipitate Retreat of Lord Percy\"'; the London writer describes the effect of the news. A private letter quoting another, at second hand.",
      role='report', words=60, dateline=False, back=True,
      core=[r'I\s+have\s+a\s+[Ll]etter\s+from\s+London,?\s+dated\s+May\s+31', r'I\s+cannot\s+let\s+Capt(?:ain|\.)?\s+Ha[sz]lewood\s+depart'],
      first="A Philadelphia letter quotes a London letter of 31 May on how London took the news of the defeat of Colonel Smith's troops on 19 April.",
      what="the Philadelphia letter of 29 July",
      printings=[k('NYG', '07-31', 5), k('CC', '08-07', 3), k('PP', '08-07', 6), k('NHG', '08-15', 1), k('VGP', '08-18', 2), k('VGDH', '08-19', 3)]),
 dict(id='city-of-london-address-and-petition-july-1775', kind='context_group',
      label="The City of London's address and petition of July 1775 for ending the hostilities in America, and the King's answer",
      children=['common-council-of-london-address-and-petition-july-1775', 'kings-answer-to-the-common-council-of-london-1775'],
      definition="The address and petition that the Lord Mayor, Aldermen and Commons of London in Common Council resolved on in July 1775, praying the King to suspend hostilities in America, and the King's answer, as the papers printed them in September and October 1775. The City's and the King's own words."),
 dict(id='common-council-of-london-address-and-petition-july-1775', parent='city-of-london-address-and-petition-july-1775', kind='document_group',
      label="The address and petition of the Lord Mayor, Aldermen and Commons of London in Common Council to the King, July 1775",
      definition="Printings of 'The humble Address and Petition of the Lord Mayor, Aldermen, and Commons of the City of London, in Common Council assembled' to the King, of July 1775: the City's loyal subjects lament the hostilities in America and pray the King to suspend them and to adopt measures that will restore union and confidence. The Common Council's own address.",
      role='published_document', words=60, dateline=False,
      head=r'(?:To\s+the\s+K\s?ING.?S\s+(?:[Mm]ost\s+)?[Ee]xcellent\s+M\s?AJESTY\.?\s*)?(?:The\s+humble\s+|The\s+following\s+is\s+the\s+)?',
      core=[r'A\s?DDRESS(?:ES)?\s+and\s+P\s?ETITION\s+of\s+the\s+L\s?ORD\s+M\s?AYOR,?\s+A\s?LDERMEN,?\s+and\s+C\s?OMMONS', r'address\s+and\s+petition\s+of\s+the\s+[Cc]ity\s+of\s+London\s+to\s+the\s+K\s?ing'],
      first="The City of London's Common Council petitions the King to suspend the hostilities in America.",
      what="the Common Council's address and petition of July 1775",
      printings=[k('NYG', '09-11', 3), k('CC', '09-18', 2), k('PP', '09-18', 6), k('NHG', '09-26', 1), k('VGP', '09-29', 2), k('VGDH', '09-30', 2)]),
 dict(id='kings-answer-to-the-common-council-of-london-1775', parent='city-of-london-address-and-petition-july-1775', kind='document_group',
      label="The King's answer to the Common Council of London: 'I am always ready to listen to the dutiful petitions of my subjects'",
      definition="Printings of the King's answer to the address and petition of the Common Council of London: 'I am always ready to listen to the dutiful petitions of my subjects, and ever happy to comply with their reasonable requests, but while the constitutional authority of this kingdom is openly resisted by a part of my American subjects', he owes it to the rest of his people to enforce obedience. The King's own answer.",
      role='published_document', words=50, dateline=False, back=True,
      head=r'(?:T\s?HE\s+K\s?ING.?S\s+A\s?NSWER|His\s+M\s?AJESTY.?S\s+A\s?NSWER)[^\"“]{0,200}?[.:\]]\s*(?:\[See\s+the\s+Postscript\.\]\s*)?[\"“]?\s*',
      core=[r'I\s+am\s+always\s+ready\s+to\s+listen\s+to\s+the\s+dutiful\s+[Pp]etitions'],
      first="The King answers the City of London that while his authority is openly resisted in America he must enforce obedience.",
      what="the King's answer to the Common Council",
      printings=[k('NYG', '09-18', 2), k('PP', '09-18', 3), k('CC', '09-25', 2), k('VGP', '09-29', 2), k('VGDH', '09-30', 2), k('NHG', '10-03', 1)]),
 dict(id='letter-on-a-skirmish-near-st-johns-september-1775', kind='message_group',
      label="A letter from Albany, 2 September 1775: 'we hear there has been a skirmish near St. John's'; General Montgomery sets off toward St. John's",
      definition="Printings of an extract of a letter from a gentleman at Albany, 2 September 1775: 'By an Express arrived last Evening, we hear there has been a Skirmish near St. John's, between a reconnoitering Party of our Men in a Boat, and a Boat of Regulars, Canadians, and Indians'; it gives the general's account of the skirmish and says General Montgomery has set off with 1200 men for St. John's, to muster on the Isle aux Noix. A private letter at second hand, giving the general's letter.",
      role='report', words=60, dateline=False, back=True,
      core=[r'we\s+hear\s+there\s+has\s+been\s+a\s+[Ss]kirmish\s+near\s+St\.?\s+John'],
      first="A letter from Albany reports a skirmish near St. John's and General Montgomery's advance toward the Isle aux Noix.",
      what="the letter on the skirmish near St. John's",
      printings=[k('NYG', '09-11', 3), k('CC', '09-18', 2), k('PP', '09-18', 5), k('VGDH', '09-23', 2), k('NHG', '09-26', 2), k('VGP', '09-29', 2)]),
 # ---- October to December ----
 dict(id='washington-address-to-the-inhabitants-of-canada-1775', kind='document_group',
      label="General Washington's address to the inhabitants of Canada, to be published on Colonel Arnold's arrival there (September 1775)",
      definition="Printings of the address of 'His Excellency George Washington, Esq; Commander in Chief of the Army of the United Colonies of North-America. To the Inhabitants of Canada. Friends and Brethren', which the papers say was to be published in Canada on the arrival there of Colonel Arnold with the troops under his command: it asks the Canadians to join the cause of liberty and says the army comes not to plunder but to protect them. General Washington's own address.",
      role='published_document', words=60, dateline=False, back=True,
      core=[r'T\s?O\s+the\s+I\s?NHABITANTS\s+of\s+C\s?ANADA', r'F\s?RIENDS\s+and\s+B\s?RETHREN'],
      first="General Washington asks the inhabitants of Canada to join the cause of liberty, saying the army under Colonel Arnold comes to protect, not to plunder.",
      what="Washington's address to the inhabitants of Canada",
      printings=[k('CC', '10-02', 1), k('NHG', '10-03', 1), k('NYG', '10-09', 1), k('PP', '10-09', 3), (k('VGP', '10-20', 5), {'back': False})]),
 dict(id='captain-mowat-and-the-burning-of-falmouth-october-1775', kind='message_group',
      label="Falmouth, Casco Bay, October 1775: an account of the town's burning by Captain Mowat, with his letter to the people of Falmouth of 16 October",
      definition="Printings of a report of the burning of Falmouth in Casco Bay by the ships under Captain Mowat on 18 October 1775, with the letter he sent the town: 'Canceaux, Falmouth, October 16th, 1775. After so many premeditated attacks on the legal prerogative of the best of sovereigns', he gives the inhabitants two hours to remove; the report gives the number of houses and stores burnt. A report from the town, with Captain Mowat's own letter.",
      role='report', words=60, dateline=False, back=True,
      core=[r'A\s?FTER\s+so\s+many\s+premeditated\s+[Aa]ttacks'],
      first="A report of the burning of Falmouth by Captain Mowat's ships, with his letter giving the inhabitants two hours to leave.",
      what="the report of the burning of Falmouth",
      printings=[k('NHG', '11-02', 1), k('CC', '11-06', 2), k('NYG', '11-06', 3), k('VGP', '11-17', 2), k('VGDH', '11-18', 2)]),
 dict(id='kings-proclamation-for-suppressing-rebellion-and-sedition-1775', kind='document_group',
      label="The King's proclamation for suppressing rebellion and sedition, 23 August 1775",
      definition="Printings of the King's proclamation of 23 August 1775, 'By the King, A Proclamation, For suppressing Rebellion and Sedition': 'Whereas many of our subjects in divers parts of our colonies and plantations in North America, misled by dangerous and ill-designing men, and forgetting the allegiance which they owe', have proceeded to open and avowed rebellion, all officers and subjects are to exert themselves to suppress it and to disclose traitorous conspiracies. The King's own proclamation.",
      role='published_document', words=60, dateline=False, back=True,
      head=r'(?:B\s?Y\s+T\s?HE\s+K\s?ING[.,]?\s*)?A\s+P\s?ROCLAMATION[.,]?\s*',
      core=[r'[Ff]or\s+suppressing\s+R\s?EBELLION\s+and\s+S\s?EDITION', r'misled\s+by\s+dangerous\s+and\s+ill[\s\-]*designing\s+men'],
      first="The King proclaims that his American subjects are in open rebellion and orders all officers and subjects to help suppress it.",
      what="the King's proclamation for suppressing rebellion",
      printings=[k('NYG', '11-06', 2), k('PP', '11-06', 4), (k('VGP', '11-10', 2), {'core': [r'A\s+proclamation\s+by\s+the\s+K\s?ING,?\s+with\s+the\s+advice'], 'back': False,
                                         'note': "A report of the proclamation that gives its words in indirect speech ('A proclamation by the King... is just come to hand, declaring his subjects... to be in open and avowed rebellion'); counted with it (C-02)."}), k('CC', '11-13', 1), k('VGDH', '11-18', 2)]),
 dict(id='halifax-report-of-the-newfoundland-storm-1775', kind='message_group',
      label="December 1775: a person from Halifax reports the loss of more than 4000 men in the storm of 9 September at Newfoundland",
      definition="Printings of a report of December 1775: 'A person lately from Halifax to Cape Cod, reports, That he saw at Halifax a particular account of the loss in the several harbours of Newfoundland, on the 9th of September, amounting in the whole to more than 4000 men, who had nearly finished their fishing voyage'. A report at second hand.",
      role='report', words=50, dateline=False, back=True,
      core=[r'particular\s+account\s+of\s+the\s+loss\s+in\s+the\s+several\s+[Hh]arbours\s+of\s+Newfoundland'],
      first="A traveller from Halifax reports more than 4000 men lost in a storm in the harbours of Newfoundland.",
      what="the Halifax report of the Newfoundland storm",
      printings=[k('CC', '12-11', 2), k('NYG', '12-11', 3), k('PP', '12-11', 5), k('NHG', '12-12', 2), k('VGP', '12-29', 5)]),
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
    ('common-council-of-london-address-and-petition-july-1775', 'sn83021126|1775-09-18|1|6'): {'head': 'To\\s*the\\s+K\\s?ING.?S\\s+M\\w{2,3}\\s+[Ee]xcellent\\s+M\\s?AJESTY\\.?\\s*(?:The\\s+humble\\s+)?'},
    ('house-of-lords-protest-against-the-address-december-1774', 'sn84024742|1775-02-03|1|6'): {'head': 'W\\s?HEREUPON\\s+a\\s+protest\\s+was\\s+entered\\s+by\\s+nine\\s+of\\s+the\\s+Lords,?\\s+viz\\..{0,240}?effect:\\s*[\\"“]?\\s*That\\s+they\\s+'},
    ('livery-of-london-address-remonstrance-and-petition-april-1775', 'sn84024742|1775-06-16|1|5'): {'head': 'To\\s+the\\s+K\\s?ING.?S\\s+(?:[Mm]ost\\s+)?[Ee]xcellent\\s+M\\s?AJESTY\\.?\\s*(?:The\\s+)?'},
    ('massachusetts-provincial-congress-resolves-february-1775', 'sn84024739|1775-03-11|1|3'): {'back': False},
    ('west-indies-report-of-the-parliament-house-pulled-down-1775', 'sn83025582|1775-08-15|1|1'): {'head': 'T\\s?HE\\s+Account\\s+from\\s+St\\.\\s+Eustatia.{0,320}?is\\s+confirmed\\s+by\\s+Capt\\.\\s*'},
}
KEEP_WORDS = {
    ('burgoyne-letter-to-lee-july-1775', 'sn83021126|1775-08-07|1|5'): 66,
    ('burgoyne-letter-to-lee-july-1775', 'sn84024739|1775-08-19|1|4'): 66,
    ('burgoyne-letter-to-lee-july-1775', 'sn84024742|1775-08-18|1|3'): 66,
    ('colony-agents-letter-on-the-congress-petition-24-december-1774', 'sn82016139|1775-03-27|1|2'): 65,
    ('colony-agents-letter-on-the-congress-petition-24-december-1774', 'sn83021126|1775-03-20|1|4'): 38,
    ('colony-agents-letter-on-the-congress-petition-24-december-1774', 'sn83025582|1775-03-31|1|1'): 70,
    ('colony-agents-letter-on-the-congress-petition-24-december-1774', 'sn84024739|1775-03-18|1|3'): 94,
    ('colony-agents-letter-on-the-congress-petition-24-december-1774', 'sn84024742|1775-03-17|1|7'): 83,
    ('common-council-of-london-address-and-petition-july-1775', 'sn83021126|1775-09-18|1|6'): 79,
    ('common-council-of-london-address-and-petition-july-1775', 'sn83025582|1775-09-26|1|1'): 64,
    ('continental-congress-petition-to-the-king-october-1774', 'sn82016139|1775-01-30|1|4'): 87,
    ('continental-congress-petition-to-the-king-october-1774', 'sn83021126|1775-01-16|1|5'): 85,
    ('continental-congress-petition-to-the-king-october-1774', 'sn83021126|1775-01-23|1|1'): 85,
    ('continental-congress-petition-to-the-king-october-1774', 'sn83025582|1775-02-03|1|2'): 85,
    ('continental-congress-petition-to-the-king-october-1774', 'sn83025582|1775-02-10|1|2'): 98,
    ('continental-congress-petition-to-the-king-october-1774', 'sn83030493|1775-01-23|1|3'): 85,
    ('continental-congress-petition-to-the-king-october-1774', 'sn84024739|1775-02-11|1|5'): 92,
    ('continental-congress-petition-to-the-king-october-1774', 'sn84024742|1775-02-03|1|5'): 72,
    ('continental-congress-resolve-on-the-restraining-acts-4-july-1775', 'sn82016139|1775-07-17|1|3'): 65,
    ('continental-congress-resolve-on-the-restraining-acts-4-july-1775', 'sn83025582|1775-07-25|1|2'): 65,
    ('continental-congress-resolve-on-the-restraining-acts-4-july-1775', 'sn84024742|1775-07-21|1|11'): 69,
    ('continental-congress-second-petition-to-the-king-8-july-1775', 'sn84024742|1775-12-15|1|1'): 79,
    ('declaration-of-the-causes-and-necessity-of-taking-up-arms-1775', 'sn82016139|1775-07-17|1|2'): 71,
    ('house-of-lords-protest-against-the-address-december-1774', 'sn83030493|1775-02-06|1|1'): 55,
    ('house-of-lords-protest-against-the-address-december-1774', 'sn84024739|1775-02-04|1|2'): 56,
    ('house-of-lords-protest-against-the-address-december-1774', 'sn84024742|1775-02-03|1|6'): 71,
    ('kings-answer-to-the-common-council-of-london-1775', 'sn82016139|1775-09-25|1|2'): 71,
    ('kings-answer-to-the-common-council-of-london-1775', 'sn83021126|1775-09-18|1|3'): 73,
    ('kings-answer-to-the-common-council-of-london-1775', 'sn83030493|1775-09-18|1|2'): 68,
    ('kings-answer-to-the-common-council-of-london-1775', 'sn84024739|1775-09-30|1|2'): 69,
    ('kings-answer-to-the-common-council-of-london-1775', 'sn84024742|1775-09-29|1|2'): 53,
    ('kings-proclamation-for-suppressing-rebellion-and-sedition-1775', 'sn82016139|1775-11-13|1|1'): 65,
    ('kings-proclamation-for-suppressing-rebellion-and-sedition-1775', 'sn83030493|1775-11-06|1|2'): 65,
    ('kings-speech-to-parliament-30-november-1774', 'sn84024739|1775-02-04|1|2'): 64,
    ('livery-of-london-address-remonstrance-and-petition-april-1775', 'sn84024742|1775-06-16|1|5'): 81,
    ('massachusetts-provincial-congress-resolves-february-1775', 'sn84024739|1775-03-11|1|3'): 76,
    ('new-york-provincial-congress-address-to-washington-june-1775', 'sn83025582|1775-07-11|1|1'): 81,
    ('west-indies-report-of-the-parliament-house-pulled-down-1775', 'sn82016139|1775-08-07|1|3'): 51,
    ('west-indies-report-of-the-parliament-house-pulled-down-1775', 'sn83025582|1775-08-15|1|1'): 103,
    ('west-indies-report-of-the-parliament-house-pulled-down-1775', 'sn84024742|1775-08-18|1|1'): 51,
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
            problems.append((s['id'], key, 'page not in the 1775 pages'))
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
        r['id'] = f'S75-{n:03}'
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
               'admission_rule': 'Reviewed 1775 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1775/'
    return {
        'ledger_id': 'ledger:stories-1775', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1775', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1775, and of 1774 where they reach the 1775 pages (long-running ones '
                   'included), every item in 3 or more papers compared by machine with every page and counted again by its opening, a sweep of '
                   'word-for-word passages shared by 4 or more papers for short items the families miss, phrase searches on all 1,286 pages of '
                   '1775 in both transcriptions, reading of every hit, and scan checks of each admitted passage, by the thin-year rule (Y-THIN, '
                   'as amended on 23 November 2026: an item printed by more than half of the papers that survive for its weeks, and by at '
                   'least 4, is eligible; the items printed by every paper that survives for their weeks are admitted, and the other eligible '
                   'items are chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1774.json': 'retrieval_candidates', d+'count_1775.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1775.py': 'ledger_code', 'work/archive_data/ledgers/stories_1775_review.json': 'scan_review',
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
