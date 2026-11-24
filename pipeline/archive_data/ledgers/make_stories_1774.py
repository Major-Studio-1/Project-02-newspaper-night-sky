"""Write ledgers/stories_1774.json: reviewed stories of 1774, round one.

1774 is a thin year: no item of 1774 reaches 7 papers, so it is read by the thin-year rule (docs/rules-and-exceptions.md,
Y-THIN, as amended on 23 November 2026, the owner's choice B1): an item, counted by its own words, is eligible when it was
printed by more than half of the newspapers that survive for its weeks (those with a surviving issue between its first and
its last printing, and at least in the three weeks from its first printing), and by at least 4; as in R-01, the items
printed by every newspaper that survives for their weeks are admitted, and the other eligible items are chosen to cover the
months and the kinds of news, about as many stories as a standard year; one affair's items are treated as in X-1800-01;
digests are not admitted. In 1774 5 to 7 papers survive for any item's weeks, so every eligible item is in 4 or more papers.
The automatic families first printed in 1774 that reach 3 or more papers, long-running ones included, were split into
single printed items with work/story_items.py --long-running (items.json), and again with year 1773 over the 1774 pages
(items_from_1773.json); every item in 3 or more papers was compared by machine with every page and counted again by its
opening, a sweep of word-for-word passages shared by 4 or more papers found short items the families miss, and the
admitted and chosen items were counted with phrase searches over all 1,205 pages of 1774 in both transcriptions. See
outputs/story_discovery_1774/README.md and count_1774.md.

The 1774 pages are those whose issue the data release dates to 1774 (work/year_search_pages.py 1774 ... --printed-dates);
no 1774 issue has a corrected date. 1774 has 8 catalogue series, which are 7 papers: the Connecticut Courant of Hartford
is sn82016376 to 24 May and sn82016139 (The Connecticut Courant and Hartford Weekly Intelligencer) from 7 June (C-04).
The release's map of misfiled RevX pages (derived/revx_page_map.parquet) lists 5 pages of 1774; on those pages the
excerpt comes from the CA text of the scan page.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1774_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (reviews of other years run at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1774.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1774/search_pages.json). The excerpts are cut from
the 1774 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1774'
D = PROJECT/'outputs/story_discovery_1774'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1774_review.json'
OUT = HERE/'stories_1774.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-23'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn82016376': 'The Connecticut Courant', 'sn82016139': 'The Connecticut Courant',
         'sn83021126': "Dunlap's Pennsylvania Packet", 'sn83021194': 'The Massachusetts Spy',
         'sn83025582': 'The New-Hampshire Gazette', 'sn84024739': "Purdie and Dixon's Virginia Gazette",
         'sn84024741': "Rind's Virginia Gazette", 'sn85047530': 'The Pennsylvania Journal'}
ONE = {'PP': 'sn83021126', 'MS': 'sn83021194', 'NHG': 'sn83025582', 'VGPD': 'sn84024739', 'VGR': 'sn84024741', 'PJ': 'sn85047530'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1774), page and edition. The Connecticut Courant (CC) has two
    catalogue numbers: sn82016376 to 24 May, sn82016139 from 7 June."""
    lccn = ('sn82016376' if date < '06-01' else 'sn82016139') if paper == 'CC' else ONE[paper]
    return f'{lccn}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release (5 pages of 1774)."""
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
 dict(id='philadelphia-resolutions-on-the-tea-ship-polly-december-1773', kind='document_group',
      label="Philadelphia, 27 December 1773: the resolutions of the meeting at the State House on the tea ship Polly, Captain Ayres",
      definition="Printings of the resolutions that a public meeting at Philadelphia passed on Monday 27 December 1773, when the ship Polly, Captain Ayres, came up the Delaware with the East India Company's tea: 'That the Tea on board the ship Polly, Capt. Ayres, shall not be landed. That Capt. Ayres shall neither enter nor report his vessel at the Custom-House. That Capt. Ayres shall carry back the Tea immediately', and that he be allowed to stay in town a day to provide necessaries for his voyage. The Pennsylvania Packet prints them within its own account of the ship's arrival and the meeting, which the Massachusetts Spy and Purdie and Dixon's Virginia Gazette reprint; the Massachusetts Spy (13 January) and the New-Hampshire Gazette print them within another report from Philadelphia, in indirect speech ('That on Monday there was a meeting of the town, which consisted of at least 5000'). Counted by the resolutions, which both reports print (X-1803-02). The meeting's own resolutions, as the papers reported them.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:1\.\s*)?R\s?ESOLVED,?\s+(?:T\s?HAT|That)\s+the\s+T\s?EA,?\s+on\s+board', r'(?:R\s?ESOLVED,?\s*)?1\.?\s*That\s+the\s+Tea\s+on\s+board\s+Capt', r'That\s+the\s+Tea\s+on\s+board\s+the\s+Ship\s+Polly'],
      first="Philadelphia, 27 December 1773: a public meeting resolves that the tea on board the ship Polly shall not be landed and that the captain shall carry it back.",
      what='the resolutions of the Philadelphia meeting on the tea ship Polly',
      printings=[k('PP', '01-03', 1), k('MS', '01-13', 2), k('NHG', '01-14', 2), k('VGPD', '01-20', 2)]),
 dict(id='boston-the-judges-salaries-february-1774', kind='message_group',
      label="Boston, 7 February 1774: 'The greatest contest at present between the friends of Government and the friends of Liberty' is whether the judges are paid by the Assembly or by the Crown",
      definition="Printings of a Boston paragraph of 7 February 1774: 'The greatest contest at present between the friends of Government and the friends of Liberty, seems to be, whether the Judges of the Superior Court shall receive their Salaries as usual by the Grants of the General Assembly of this Province, or be dependent upon the Crown for their Support'; it says that both sides agree that if the latter takes place, the courts of justice will be turned into courts of politics. A Boston paper's own account of the question, with its argument; the papers print it in their Boston news.",
      role='report', words=50, dateline=True,
      core=[r'(?:T\s?HE|The)\s+great(?:est)?\s+[Cc]ontest\s+at\s+present'],
      first="Boston, 7 February 1774: the contest between the friends of government and of liberty is whether the judges of the Superior Court are paid by the Assembly or by the Crown.",
      what="the Boston paragraph on the judges' salaries",
      printings=[k('CC', '02-08', 1), k('NHG', '02-11', 1), k('PP', '02-21', 3), k('VGPD', '03-10', 2)]),
 dict(id='franklin-declaration-on-the-hutchinson-letters-1773', kind='document_group',
      label="Dr. Franklin's declaration that he alone obtained the Hutchinson letters and sent them to Boston, after the duel of Mr. Whately and Mr. Temple",
      definition="Printings of the declaration that Benjamin Franklin, agent of the Massachusetts House of Representatives in London, published in a letter of December 1773 to the printer of a London paper (the Morning Chronicle in one printing, the London Chronicle in another): 'Finding that two Gentlemen have been unfortunately engaged in a Duel, about a Transaction and its Circumstances of which both of them are totally ignorant and innocent, I think it incumbent on me to declare ... that I alone am the Person who obtained, and transmitted to Boston, the Letters in Question'; the letters, he says, were not of the nature of private letters between friends but were written by public officers on public affairs, to procure public measures. The New-Hampshire Gazette, the Pennsylvania Packet and Purdie and Dixon's Virginia Gazette print the letter; the Connecticut Courant and the Massachusetts Spy print a London report of the duel that gives the declaration in Franklin's words turned into indirect speech ('Benjamin Franklin, Esq; agent for the house of representatives of this province ... has published a declaration, That he alone was the person who obtained and transmitted to Boston the letters in question'). Counted together, a letter with a paragraph made from it (C-02, as X-1801-04): 5 papers, every paper that survives for its weeks. Franklin's own declaration.",
      role='published_document', words=60, dateline=False,
      head=r'To\s+the\s+P\s?\s?R\s?\s?I\s?\s?N\s?\s?T\s?\s?E\s?\s?R\s*(?:of\s+the\s+[A-Za-z]+\s+C\s?HRONICLE)?\.?\s*S\s?\s?I\s?\s?R,?\s*',
      core=[r'F\s?INDING\s+that\s+two\s+[Gg]entlemen\s+have\s+been', r'Benjamin\s+Franklin,?\s+Esq;?,?\s+[Aa]gent\s+for\s+the\s+[Hh]ouse\s+of\s+[Rr]epresentatives'],
      first="Dr. Franklin declares that he alone obtained the Hutchinson letters and sent them to Boston, so that the two gentlemen who fought a duel over them are innocent of it.",
      what="Dr. Franklin's declaration on the Hutchinson letters",
      printings=[(k('CC', '03-08', 3), {'note': "Printed within a London report of the duel, in indirect speech."}),
                 (k('MS', '03-10', 2), {'note': "Printed within a London report of the duel, in indirect speech."}),
                 k('NHG', '03-11', 2), k('PP', '03-14', 1), k('VGPD', '03-31', 2)]),
 dict(id='lord-viscount-pitt-to-tour-the-colonies-january-1774', kind='message_group',
      label="London, 21 January 1774: 'Lord Viscount Pitt, son to the Earl of Chatham, is to embark next month for North America'",
      definition="Printings of a paragraph of the London news of 21 January 1774: 'Lord Viscount Pitt, son to the Earl of Chatham, is to embark next month for North America, to make the tour of the British colonies on that continent.' A report from London, a single paragraph of the papers' London news.",
      role='report', words=40, dateline=False,
      head=r'Jan(?:uary|\.)?\s*21\.?\s*',
      core=[r'Lord\s+Visc(?:ount|\.)?\s+Pitt,?\s+[Ss]on\s+to\s+the\s+Earl'],
      stop=r'(?<=[Cc]ontinent\.)\s',
      first="London, 21 January 1774: Lord Viscount Pitt, the Earl of Chatham's son, is to sail next month to tour the British colonies in America.",
      what="the London paragraph on Lord Viscount Pitt",
      printings=[k('PP', '03-21', 3), k('CC', '03-22', 2), k('MS', '03-31', 3), k('VGPD', '04-07', 1), k('NHG', '04-08', 2)]),
 dict(id='letter-from-the-lower-elbe-on-the-insurrection-in-russia-1774', kind='message_group',
      label="London, 26 January 1774: a letter from the Lower Elbe, 'The insurrection in Russia is at present the topic of every conversation'",
      definition="Printings of a paragraph of the London news of 26 January 1774: 'A letter from the Lower Elbe, dated Jan. 13, says, \"The insurrection in Russia is at present the topic of every conversation. It seems to have happened in the most critical time, when fresh troops were greatly wanted\"'; it says that troops on their march for Moldavia have been recalled, that troops about Warsaw have orders to march for Petersburg, and that 'a total Revolution' is suspected to be the consequence. A report at second hand, from a letter, in the papers' London news.",
      role='report', words=60, dateline=False,
      head=r'Jan(?:uary|\.)?\s*26\.?\s*',
      core=[r'(?:A\s+)?letter\s+from\s+the\s+Lower\s+Elbe'],
      first="London, 26 January 1774: a letter from the Lower Elbe reports the insurrection in Russia and its effect on the war.",
      what="the letter from the Lower Elbe",
      printings=[k('PP', '03-21', 3), k('CC', '03-22', 2), k('MS', '03-31', 3), k('VGPD', '04-07', 1), k('NHG', '04-08', 2)]),
 dict(id='kings-speech-to-parliament-13-january-1774', kind='document_group',
      label="The King's speech to both Houses of Parliament, 13 January 1774",
      definition="Printings of the King's speech at the opening of the session of Parliament on 13 January 1774: 'My Lords and Gentlemen, The unusual length of the last session of Parliament made me desirous of giving you as long a recess as the public service would admit'; it regrets that 'the Peace so long expected, and so very desirable, is not yet effected between Russia and the Porte', says that the other foreign powers continue in the same pacific disposition, and that Parliament will have full leisure to attend to 'the Preservation and the Advancement of the Revenue and Commerce of the Kingdom'. The King's own speech.",
      role='published_document', words=60, dateline=False,
      head=r'[\"“]?\s*(?:M\s?Y\s+)?L\s?ORDS,?\s+and\s+G\s?ENTLEMEN,?\s*[\"“]?\s*',
      core=[r'(?:T\s?HE|The)\s+unusual\s+[Ll]ength\s+of\s+the\s+last\s+[Ss]ession'],
      first="The King's speech of 13 January 1774 at the opening of Parliament.",
      what="the King's speech of 13 January",
      printings=[k('PP', '03-21', 2), k('VGPD', '03-24', 2), k('MS', '03-31', 1), k('NHG', '04-01', 2), k('CC', '04-05', 5)]),
 dict(id='gentleman-in-england-on-the-warlike-preparations-of-the-french-1774', kind='message_group',
      label="'A gentleman in England writes his friend in Philadelphia: The warlike preparations of the French I imagine will alarm all Europe'",
      definition="Printings of a short extract of a letter from a gentleman in England to his friend in Philadelphia, printed from Philadelphia in March 1774: 'The warlike preparations of the French I imagine will alarm all Europe; what their designs are, time must bring forth. The insurrection at Petersburg, we imagine is set on foot by them, and that his Prussian Majesty is at the bottom of scheme'; it expects fleets and armies to be sent to different parts. A private letter printed at second hand, with the writer's conjectures.",
      role='report', words=60, dateline=False, back=True,
      core=[r'(?:A\s+)?[Gg]entleman\s+in\s+England,?\s+writes', r'warlike\s+preparations\s+of\s+the\s+French'],
      first="A gentleman in England writes that the warlike preparations of the French will alarm all Europe, and supposes them behind the insurrection in Russia.",
      what="the letter on the warlike preparations of the French",
      printings=[k('CC', '03-22', 2), k('PP', '03-28', 3), k('MS', '03-31', 2), k('NHG', '04-01', 3), k('VGPD', '04-14', 1)]),
 dict(id='privy-council-hearing-on-the-massachusetts-petition-january-1774', kind='message_group',
      label="London, February 1774: the Privy Council hears the petition of the Massachusetts Assembly to remove the Governor",
      definition="Printings of a paragraph of the London news of early February 1774: 'On Saturday last the Privy Council met to hear the arguments for and against the petition of the Assembly of Boston (which was sometime since presented by their Agent, Dr. Franklin) \"praying that his Majesty would be pleased to remove the Governor, &c.\"'; it names the counsel for the petition and says that the Solicitor General, instead of answering their arguments, 'contented himself with pronouncing a most severe philippic' on Dr. Franklin. A London paper's account, partisan in its words; the papers print it in their London news. A paragraph of the same news, that Dr. Franklin was dismissed as Postmaster General, is in 5 papers and not chosen (X-1800-01).",
      role='report', words=60, dateline=False,
      core=[r'(?:O\s?N|On)\s+Saturday\s+last,?\s+the\s+[Pp]rivy[\s-]*[Cc]ouncil', r'[Pp]rivy[\s-]*[Cc]ouncil,?\s+met\s+to\s+hear'],
      first="London, February 1774: the Privy Council hears the Massachusetts Assembly's petition to remove Governor Hutchinson; a London paper says the Solicitor General answered with an attack on Dr. Franklin.",
      what="the London paragraph on the Privy Council's hearing",
      printings=[k('CC', '04-12', 1), k('PP', '04-18', 3), k('MS', '04-22', 2), k('NHG', '04-29', 3), k('VGPD', '05-05', 1)]),
 dict(id='boston-port-act-1774', kind='document_group',
      label="The act of Parliament to discontinue the landing and shipping of goods at the town and harbour of Boston (the Boston Port Act), as the papers printed it in May 1774",
      definition="Printings of the act of Parliament of March 1774, 'An Act to discontinue, in such manner, and for such time as are therein mentioned, the landing and discharging, lading or shipping of goods, wares and merchandize, at the town, and within the harbour, of Boston, in the province of Massachusetts Bay, in North America': from 1 June 1774 no goods may be landed or shipped at Boston until the King in Council declares that trade may resume, which he may do when the East India Company has been paid for the tea destroyed and peace and obedience to the laws restored. Several papers print it after a London paragraph of 4 April ('The following is the much-talked-of Boston Port-Bill, which on Thursday last received the Royal Assent'). Counted where the act is printed whole; later documents that recite its title are not counted (C-07). The act of Parliament.",
      role='published_document', words=60, dateline=False,
      core=[r'A\s?N\s+A\s?CT\s+to\s+discontinue,?\s+in\s+such\s+[Mm]anner'],
      first="The Boston Port Act: from 1 June 1774 the landing and shipping of goods at Boston is stopped until the King in Council allows it again.",
      what='the Boston Port Act',
      printings=[k('CC', '05-10', 2), k('MS', '05-12', 5), k('PP', '05-16', 2), k('NHG', '05-20', 2), k('VGPD', '05-26', 1)]),
 dict(id='virginia-burgesses-resolution-for-a-fast-on-1-june-1774', kind='document_group',
      label="Williamsburg, 24 May 1774: the House of Burgesses sets apart 1 June, the day the port of Boston is to be shut, as a day of fasting, humiliation and prayer",
      definition="Printings of the resolution of the Virginia House of Burgesses of 24 May 1774, 'which was directed to be forthwith printed and published': 'This House being deeply impressed with apprehension of the great dangers to be derived to British America, from the hostile invasion of the city of Boston, in our sister colony of Massachusetts Bay, whose commerce and harbour are on the 1st day of June next to be stopped by an armed force, deem it highly necessary that the said first day of June be set apart by the members of this House as a day of fasting, humiliation and prayer'. The House of Burgesses' own resolution.",
      role='published_document', words=60, dateline=True,
      head=(r'(?:W\s?I\s?L\s?L\s?I\s?A\s?M\s?S\s?B\s?U\s?R\s?G\s?H?,?\s*(?:\((?:in\s+)?Virginia\)\s*|in\s+Virginia,\s*)?May\s+2[56]\.\s*)?'
            r'(?:O\s?N\s+)?Tuesday\s+(?:la\w+,?\s+)?(?:the\s+Hon\w*\.?\s+)?the\s+H\s?OUSE\s+OF\s+B\s?UR\s?GESS\w*\s+(?:here\s+)?came\s+(?:to|into)\s+the\s+following\s+[Rr]esolution[^\"“]{0,90}[\"“]?\s*'
            r'|P\s?ROCEEDINGS\s+of\s+the\s+H\s?OUSE\s+of\s+B\s?URGESSES\.\s*T\s?UESDAY,?\s+the\s+24th\s+of\s+May,?\s+14\s+Geo\.\s+III\.\s+1774\.\s*'),
      core=[r'[\"“]?\s*This\s+House\s+being\s+deeply\s+impressed\s+with'],
      first="The Virginia House of Burgesses resolves that 1 June 1774, when the port of Boston is to be shut, be a day of fasting, humiliation and prayer.",
      what="the Burgesses' resolution of 24 May",
      printings=[k('VGPD', '05-26', 2), k('VGR', '05-26', 2), k('PP', '06-06', 2), k('CC', '06-14', 2), k('NHG', '06-17', 2),
                 (k('MS', '07-16', 2), {'note': "The issue is filed under 16 July 1774; its first page prints 'Thursday, June 16, 1774' (number 176), so this printing appeared on 16 June."})]),
 dict(id='bills-for-massachusetts-bay-printed-june-1774', kind='context_group',
      label="Two bills of Parliament for the province of Massachusetts Bay, as the papers printed them in June 1774",
      children=['bill-for-regulating-the-government-of-massachusetts-bay-1774', 'bill-for-the-impartial-administration-of-justice-massachusetts-bay-1774'],
      definition="The bill for the better regulating the government of the province of Massachusetts Bay and the bill for the impartial administration of justice in the cases of persons questioned for acts done in the execution of the law, which the papers printed together in June 1774 from the London prints. Contains those two groups."),
 dict(id='bill-for-regulating-the-government-of-massachusetts-bay-1774', parent='bills-for-massachusetts-bay-printed-june-1774', kind='document_group',
      label="The bill for the better regulating the government of the province of Massachusetts Bay, as printed in June 1774",
      definition="Printings of the bill of Parliament 'for the better regulating the Government of the Province of the Massachusetts-Bay, in North-America': 'Whereas by letters patent under the great seal of England, made in the third year of the reign of their late majesties king William and queen Mary '; under that charter the councillors were chosen by the general court, and the bill provides that they be put on the footing of the colonies whose governors are appointed by the King's commission. The Massachusetts Spy and the Connecticut Courant print it again in July, headed 'A Bill, entitled, An Act'. The act as passed, printed in July by one paper, is counted apart (X-1803-10). The bill of Parliament.",
      role='published_document', words=60, dateline=False,
      core=[r'A\s+B\s?ILL,?\s+(?:entitled,?\s+An\s+A\s?CT\s+)?for\s+the\s+better\s+regulating\s+the\s+[Gg]overnment'],
      first="The bill for the better regulating the government of Massachusetts Bay: the councillors no longer to be chosen by the general court.",
      what='the bill for regulating the government of Massachusetts Bay',
      printings=[k('MS', '06-09', 1), k('NHG', '06-10', 2), k('PP', '06-13', 3), k('CC', '06-14', 1), k('VGR', '06-30', 2),
                 (k('MS', '07-15', 2), {'note': "Printed again, headed 'A Bill, entitled, An Act'."}),
                 (k('CC', '07-19', 2), {'note': "Printed again, headed 'A Bill, entitled An Act', after the Lords' protest on the bill."})]),
 dict(id='bill-for-the-impartial-administration-of-justice-massachusetts-bay-1774', parent='bills-for-massachusetts-bay-printed-june-1774', kind='document_group',
      label="The bill for the impartial administration of justice in the cases of persons questioned for acts done in the execution of the law in Massachusetts Bay, as printed in June 1774",
      definition="Printings of the bill of Parliament 'for the impartial administration of Justice in the Cases of Persons questioned for any Act done by them in the Execution of the Law, or for the Suppression of Riots and Tumults, in the Province of the Massachusetts-Bay, in New-England': 'Whereas in his Majesty's province of Massachusetts-Bay, in New-England, an attempt hath lately been made to throw off the authority of the parliament of Great-Britain over the said province'; it provides that a person indicted for murder or another capital offence committed in support of the laws or in suppressing riots may be tried in another colony or in Great Britain, if the governor judges that an indifferent trial cannot be had in the province. A sub-story under the parent (C-01). The bill of Parliament.",
      role='published_document', words=60, dateline=False,
      core=[r'A\s+B\s?ILL\s+for\s+the\s+impartial\s+[Aa]dministration\s+of\s+[Jj]ustice', r'[Ff]or\s+the\s+impartial\s+[Aa]dministration\s+of\s+[Jj]ustice\s+in\s+the\s+[Cc]ases'],
      first="The bill for the impartial administration of justice: persons indicted for acts done in support of the laws in Massachusetts Bay may be tried in another colony or in Great Britain.",
      what='the bill for the impartial administration of justice',
      printings=[k('MS', '06-09', 1), k('NHG', '06-10', 2), k('PP', '06-13', 3), k('CC', '06-14', 1)]),
 dict(id='gage-proclamation-against-illegal-combinations-june-1774', kind='document_group',
      label="Governor Gage's proclamation of June 1774 'for discouraging certain illegal combinations' (the solemn league and covenant)",
      definition="Printings of the proclamation of Thomas Gage, governor of Massachusetts Bay, dated 29 June 1774: 'A Proclamation, for discouraging certain illegal combinations. Whereas certain persons, calling themselves a Committee of Correspondence for the town of Boston, have lately presumed to make, or cause to be made, a certain unlawful instrument, purporting to be a solemn League and Covenant, intended to be signed by the inhabitants of this province; whereby they are most solemnly to covenant and engage, to suspend all commercial intercourse with the Island of Great-Britain'; it calls the covenant traitorous and orders magistrates to apprehend those who publish or sign it. The governor's own proclamation.",
      role='published_document', words=60, dateline=False,
      head=r'(?:(?:(?:P\s?ROVINCE\s+of\s+the\s+)?M\s?ASSACHUSETTS[\s-]*B\s?AY\.?\s*)?B\s?Y\s+the\s+G\s?OVERNOR\.?\s*)?A\s+P\s?ROCLAMATION[.,]?\s*',
      core=[r'[Ff](?:OR|or)\s+discouraging\s+certain\s+illegal\s+[Cc]ombinations'],
      first="Governor Gage's proclamation against the solemn league and covenant to suspend trade with Great Britain, which he calls an illegal combination.",
      what="Governor Gage's proclamation against illegal combinations",
      printings=[k('MS', '06-30', 3), k('CC', '07-05', 2), k('NHG', '07-08', 3), k('PP', '07-11', 2), k('VGPD', '07-21', 6), k('VGR', '07-21', 3)]),
 dict(id='gage-proclamation-for-piety-and-virtue-july-1774', kind='document_group',
      label="Governor Gage's proclamation of July 1774 'for the encouragement of piety and virtue, and for preventing and punishing of vice, profanity and immorality'",
      definition="Printings of the proclamation of Governor Gage of July 1774: 'A Proclamation, for the encouragement of piety and virtue, and for preventing and punishing of vice, profanity and immorality. In humble imitation of the laudable example of our most gracious Sovereign George the third, who in the first year of his reign was pleased to issue his royal proclamation'; it exhorts all his Majesty's subjects 'to avoid all hypocrisy, sedition, licentiousness' and other immoralities, and commands judges and officers to see the laws against vice executed. The governor's own proclamation.",
      role='published_document', words=60, dateline=False,
      head=r'(?:(?:P\s?ROVINCE\s+OF\s+)?M\s?ASSACHUSETTS[\s-]*B\s?AY\.?\s*)?(?:B\s?Y\s+(?:his\s+Excellency\s+)?the\s+G\s?OVERNOR[^.]{0,60}?[.,]\s*)?A\s+P\s?ROCLAMATION[.,]?\s*',
      core=[r'[Ff](?:OR|or)\s+the\s+[Ee]ncouragement\s+of\s+[Pp]iety\s+and\s+[Vv]irtue'],
      first="Governor Gage's proclamation for the encouragement of piety and virtue, which exhorts the people to avoid hypocrisy, sedition and licentiousness.",
      what="Governor Gage's proclamation for piety and virtue",
      printings=[k('MS', '07-28', 2), k('CC', '08-02', 2), k('PP', '08-08', 2), k('VGPD', '08-18', 2)]),
 dict(id='gage-and-the-selectmen-of-boston-on-town-meetings-august-1774', kind='message_group',
      label="Boston, August 1774: Governor Gage tells the selectmen of the clause of the new act that forbids town meetings without his leave",
      definition="Printings of a Boston paragraph of August 1774: 'We hear that his Excellency Governor Gage desired the attendance of the Selectmen of this town at the Province House on Saturday last, when he informed them of that clause in the late act of parliament forbidding town-meetings without special leave of the Governor'; it reports that he told them he would give leave for a meeting if he judged it expedient, and, being told that the province law had been the rule of their conduct, that he was determined to carry the acts of parliament into execution and they must be answerable for any bad consequences. A Boston paper's report at second hand ('We hear').",
      role='report', words=60, dateline=False, back=True,
      core=[r'(?:W\s?E|We)\s+hear\s+that\s+his\s+Excellency\s+Governor\s+Gage\s+desired', r'Governor\s+Gage\s+desired\s+the'],
      first="Boston, August 1774: Governor Gage tells the selectmen that the new act forbids town meetings without his leave and that he will carry the acts into execution.",
      what='the Boston report of Governor Gage and the selectmen',
      printings=[k('MS', '08-18', 2), k('NHG', '08-19', 2), k('CC', '08-23', 3), k('PP', '08-29', 3), k('VGPD', '09-08', 2), k('VGR', '09-08', 3)]),
 dict(id='sketch-of-a-popular-noblemans-speech-on-american-affairs-1774', kind='message_group',
      label="London, 9 June 1774: 'a sketch of a popular Nobleman's speech on American affairs', in the House of Lords",
      definition="Printings of a London paragraph of 9 June 1774: 'The following is a Sketch of a popular Nobleman's Speech on American Affairs: \"My Lords, Want of Health has hitherto prevented me from giving my Sentiments on the several Bills which have come under your Consideration with respect to America'; the speaker says 'Was I in Boston I would say they were wrong to destroy the Property of the East India Company; I say here, you have been the original Aggressors', and advises the Lords to 'be Friends with America for your own Interest and your own Safety'. The papers do not name the speaker, except Rind's Virginia Gazette, which heads it 'a sketch of lord Chatham's speech on American affairs'. The London papers also printed 'the heads of Lord Chatham's speech' of 27 May on the bill for quartering soldiers in America and, later, the speech's text; those are other texts, counted apart (5 papers) and not chosen (X-1800-01). A London paper's account of a speech in the House of Lords.",
      role='report', words=60, dateline=True,
      core=[r'(?:T\s?HE|The)\s+following\s+is\s+a\s+[Ss]ketch\s+of\s+a\s+popular\s+[Nn]obleman', r'(?:[\"“]\s*)?(?:M\s?Y|My)\s+L\s?ORDS,?\s+[Ww]ant\s+of\s+[Hh]ealth'],
      first="London, 9 June 1774: a sketch of a popular nobleman's speech in the House of Lords, which calls the ministry the original aggressors and advises friendship with America.",
      what="the sketch of a popular nobleman's speech",
      printings=[k('MS', '08-25', 3), k('NHG', '08-26', 1), k('PP', '08-29', 2), k('CC', '08-30', 1), k('VGPD', '09-15', 2), k('VGR', '09-15', 2)]),
 dict(id='quebec-act-1774', kind='document_group',
      label="The act of Parliament 'for making more effectual provision for the government of the province of Quebec in North America' (the Quebec Act), as the papers printed it in September 1774",
      definition="Printings of the act of Parliament of June 1774: 'Whereas his Majesty, by his Royal proclamation, bearing date the seventh day of October, in the third year of his reign, thought fit to declare the provisions which had been made in respect to certain countries, territories and islands in America, ceded to his Majesty by the definitive treaty of peace'; it extends the bounds of the province, along the western boundary of Pennsylvania, and, reciting that the inhabitants at the conquest professed 'the Religion of the Church of Rome' and enjoyed an established system of laws, provides for the laws of Canada in civil causes and keeps the criminal law of England. Rind's Virginia Gazette prints it headed 'A Bill intitled an Act'. Counted where the act is printed whole; abstracts of it and petitions that recite its title are not counted (C-07). The act of Parliament.",
      role='published_document', words=60, dateline=False,
      core=[r'A\s+B\s?ILL\s+intitled\s+an\s+act\s+for\s+making\s+more\s+effectual', r'A\s?N\s+A\s?CT,?\s+[Ff]or\s+making\s+more\s+effectual\s+[Pp]rovision\s+for\s+the\s+[Gg]overnment\s+of\s+the\s+[Pp]rovince\s+of\s+Q\s?UEBEC,?\s+in\s+N\s?ORTH[\s-]*A\s?MERICA\.?\W{0,12}W?\s?HEREAS',
            r'(?:(?:T\s?HE|The)\s+following\s+is\s+an\s+authentic\s+)?(?:COPY\s+OF\s+THE\s+ACT\s+OF\s+PARLIAMENT,?\s+)?F\s?OR\s+making\s+more\s+effectual\s+P\s?ROVISION\s+for\s+the\s+G\s?OVERNMENT\s+of\s+the\s+Province\s+of\s+Q\s?UEBEC'],
      first="The Quebec Act: the province of Quebec extended, the laws of Canada kept in civil causes and the criminal law of England in criminal ones.",
      what='the Quebec Act',
      printings=[k('PP', '09-05', 5), k('CC', '09-06', 2), k('NHG', '09-09', 1), k('VGR', '09-15', 1)]),
 dict(id='general-brattle-letter-to-governor-gage-august-1774', kind='document_group',
      label="Cambridge, 29 August 1774: a letter 'said to be wrote by General Brattle' to Governor Gage, on the militia and the province's powder",
      definition="Printings of a letter of 29 August 1774 that the papers print as 'a Copy of a Letter, said to be wrote by General Brattle, to the Commander in chief': 'Mr. Brattle presents his Duty to his Excellency Governor Gage, he apprehends it is his Duty to acquaint his Excellency from Time to Time with every Thing he hears and knows to be true & is of Importance in these troublesome Times'; it reports that a militia captain has been pressed to warn his company to meet at a minute's warning, and that the selectmen of Medford have taken their town's stock of powder from the arsenal on Quarry Hill, 'so that there is now therein the King's Powder only'. The papers printed it in early September among reports of the crowds that gathered at Cambridge on 2 September. The letter's own words, as printed by others; the excerpts end before it names militia officers.",
      role='published_document', words=60, dateline=False,
      head=(r'(?:T\s?HE|The)\s+following\s+is\s+a\s+[Cc]opy\s+of\s+a\s+[Ll]etter,?\s+said\s+to\s+be\s+(?:wrote|written)\s+by\s+Gen(?:eral|\.)\s+Brattle,?\s+(?:of\s+Cambridge,?\s+)?'
            r'to\s+(?:the\s+Commander\s+in\s+[Cc]hief|Gov\.\s+Gage)[^\"“]{0,60}?(?:[\"“][^\"”]{0,120}[\"”]\s*)?,?\s*(?:viz\.?)?[:.,]?\s*(?:[\"“]?\s*Cambridge,?\s+August\s+2\d,?\s*1774\.?\s*[\"“]?\s*)?'),
      core=[r'M\s?R\.?\s+Brattle\s+presents\s+his\s+[Dd]uty'],
      stop=r'\sCapt(?:ain|\.)\s',
      first="Cambridge, 29 August 1774: a letter said to be General Brattle's tells Governor Gage how the militia is being pressed to arm.",
      what="the letter said to be General Brattle's",
      printings=[k('NHG', '09-09', 3), k('CC', '09-12', 2), k('PP', '09-12', 2), k('VGPD', '09-22', 3), k('VGR', '09-22', 3)]),
 dict(id='suffolk-resolves-september-1774', kind='document_group',
      label="The resolves of the delegates of the towns of Suffolk County, Massachusetts Bay, 6–9 September 1774 (the Suffolk resolves)",
      definition="Printings of the resolves of a convention of delegates of every town and district of Suffolk County: 'At a meeting of the Delegates of every town and district in the county of Suffolk on Tuesday the 6th of September, at the house of Mr. Richard Woodward of Dedham, and by adjournment at the house of Mr. Vose of Milton, on Friday the ninth instant ... the following being several times read, and put paragraph by paragraph, was unanimously voted'; the resolves declare 'That no obedience is due from this province to either or any part of the acts above mentioned, but that they be rejected as the attempts of a wicked administration to enslave America', recommend that the people appear under arms at least once every week, and recommend withholding all commercial intercourse with Great Britain, Ireland and the West Indies. Several papers print them as they were laid before the Continental Congress at Philadelphia, which approved them on 17 September. The convention's own resolves.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:A\s?T|At)\s+a\s+[Mm]eeting\s+of\s+the\s+[Dd]elegates\s+of\s+every\s+[Tt]own'],
      first="The resolves of the convention of Suffolk County, Massachusetts Bay, September 1774: no obedience to the late acts of Parliament, militia drill every week, and no commerce with Great Britain.",
      what='the Suffolk resolves',
      printings=[k('PP', '09-19', 2), k('NHG', '09-23', 1), k('CC', '09-26', 1), k('VGPD', '10-06', 2), k('VGR', '10-06', 2)]),
 dict(id='continental-congress-at-philadelphia-september-october-1774', kind='context_group',
      label="The Continental Congress at Philadelphia, September and October 1774: its resolutions, its association and its declaration of 14 October",
      children=['continental-congress-resolution-of-22-september-1774', 'continental-congress-resolves-of-8-october-1774',
                'continental-congress-declaration-and-resolves-14-october-1774', 'continental-association-1774'],
      definition="Four papers of the Congress of delegates of the colonies that met at Philadelphia from 5 September 1774, as the papers printed them: its resolution of 22 September asking the merchants to send no more orders to Great Britain, its resolves of 8 October approving the opposition of Massachusetts Bay to the late acts, its declaration and resolves of 14 October, and its Association. Contains those four groups."),
 dict(id='continental-congress-resolution-of-22-september-1774', parent='continental-congress-at-philadelphia-september-october-1774', kind='document_group',
      label="The Congress's resolution of 22 September 1774: the merchants not to send any orders for goods to Great Britain",
      definition="Printings of the resolution of the Congress of 22 September 1774: 'Resolved unanimously, That the Congress request the merchants and others, in the several colonies, not to send to Great-Britain any orders for goods, and to direct the execution of all orders already sent to be delayed or suspended, until the sense of the Congress, on the means to be taken for the preservation of the liberties of America, is made public', with the secretary's attestation. The Massachusetts Spy prints it again in December with the Congress's proceedings. The Congress's own resolution.",
      role='published_document', words=60, dateline=True,
      head=r'(?:P\s?H\s?I\s?L\s?A\s?D\s?E\s?L\s?P\s?H\s?I\s?A\.\s*)?(?:I\s?N|In)\s+C\s?ONGRESS,?\s+(?:Thursday,?\s+)?Sept(?:ember|\.)?\s*22,?\s*1774\.?\s*(?:R\s?ESOLVED\s*,?\s*)?',
      core=[r'R\s?ESOLVED\s*,?\s+U\s?NANIMOUSLY\s*,?\s+(?:T\s?HAT|That)\s+the\s+Congress\s*,?\s+request', r'(?:T\s?HAT|That)\s+the\s+Congress\s*,?\s+request\s+the\s+[Mm]erchants'],
      first="The Continental Congress resolves on 22 September 1774 that the merchants send no more orders for goods to Great Britain.",
      what="the Congress's resolution of 22 September",
      printings=[k('PP', '09-26', 2), k('VGR', '09-29', 3), k('CC', '10-03', 3), k('VGPD', '10-06', 3), k('NHG', '10-07', 1), k('MS', '10-13', 3),
                 (k('MS', '12-16', 1), {'note': "Printed again, with the Congress's proceedings."})]),
 dict(id='continental-congress-resolves-of-8-october-1774', parent='continental-congress-at-philadelphia-september-october-1774', kind='document_group',
      label="The Congress's resolves of 8 October 1774: it approves the opposition of the inhabitants of Massachusetts Bay to the late acts of Parliament",
      definition="Printings of the Congress's resolution of 8 October 1774: 'Resolved, That the Congress approve of the opposition, by the inhabitants of the Massachusetts-Bay, to the execution of the late Acts of Parliament, and if the same shall be attempted to be carried into execution by force, that in such case all America ought to support them in their opposition', printed with its resolves of 10 and 11 October. The papers print it in two forms: from Philadelphia, under the date of the session, in October, and in the printed extracts of the Congress's proceedings ('Resolved, That this Congress do approve of the opposition made by the inhabitants of the Massachusetts-Bay'), from late October; counted together (C-02), and printed again counts again (C-08). Rind's Virginia Gazette prints the extracts too, but its transcriptions lack the resolution's opening, so that printing is not counted (C-06). The Congress's own resolves.",
      role='published_document', words=45, dateline=False,
      head=r'(?:I\s?N|In)\s+C\s?ONGRESS,?\s+Saturday,?\s+October\s+8,?\s*1774\.?\s*',
      core=[r'R\s?ESOLVED\s*,?\s+(?:T\s?HAT|That)\s+(?:the|this)\s+Congress\s+(?:do\s+)?approve'],
      first="The Continental Congress approves the opposition of the people of Massachusetts Bay to the late acts and says all America ought to support them if force is used.",
      what="the Congress's resolves of 8 October",
      printings=[k('MS', '10-20', 3), k('CC', '10-24', 3), k('NHG', '10-28', 2),
                 (k('PP', '10-31', 2), {'note': "In the printed extracts of the Congress's proceedings."}),
                 (k('VGPD', '11-10', 1), {'note': "In the printed extracts of the Congress's proceedings."}),
                 (k('NHG', '11-18', 3), {'note': "Printed again, in the printed extracts of the Congress's proceedings."}),
                 (k('MS', '12-16', 2), {'note': "Printed again, with the Congress's proceedings."})]),
 dict(id='continental-congress-declaration-and-resolves-14-october-1774', parent='continental-congress-at-philadelphia-september-october-1774', kind='document_group',
      label="The Congress's declaration and resolves of 14 October 1774: 'Whereas, since the close of the last war, the British Parliament claiming a power of right to bind the people of America, by statute in all cases whatsoever'",
      definition="Printings of the declaration and resolves that the Congress adopted on 14 October 1774, at the head of the printed extracts of its proceedings: 'Whereas, since the close of the last war, the British Parliament claiming a power, of right to bind the people of America, by statute in all cases whatsoever, hath in some acts expressly imposed taxes on them'; it lists the acts of Parliament the colonies complain of, and resolves that the inhabitants of the English colonies in North America 'are entitled to life, liberty, and property: and they have never ceded to any sovereign power whatever, a right to dispose of either without their consent', and to the rights, liberties and immunities of free and natural-born subjects within the realm of England. The Congress's own declaration.",
      role='published_document', words=60, dateline=False,
      head=r'(?:(?:F\s?RIDAY|Friday),?\s+October\s+14,?\s*1774\.?\s*)?(?:T\s?HE\s+)?(?:C\s?ONGRESS\s+CAME\s+INTO\s+THE\s+FOLLOWING\s+R\s?ESOLUTIONS[.:]?\s*)?',
      core=[r'(?:W\s?HEREAS|Whereas)\s*,?\s+since\s+the\s+close\s+of\s+the\s+last\s+war'],
      first="The Continental Congress's declaration of 14 October 1774: the acts of Parliament complained of, and the rights the colonists claim.",
      what="the Congress's declaration and resolves of 14 October",
      printings=[k('PP', '10-31', 2), k('VGR', '11-10', 1), k('VGPD', '11-17', 1), k('NHG', '11-18', 2)]),
 dict(id='continental-association-1774', parent='continental-congress-at-philadelphia-september-october-1774', kind='document_group',
      label="The Association of the Continental Congress, October 1774: no importation from Great Britain or Ireland after 1 December 1774",
      definition="Printings of the Association that the delegates signed at Philadelphia: 'We his Majesty's most loyal subjects, the Delegates of the several Colonies of New-Hampshire, Massachusetts-Bay, Rhode-Island, Connecticut, New-York, New-Jersey, Pennsylvania, the three Lower Counties of New-Castle, Kent, and Sussex, on Delaware, Maryland, Virginia, North-Carolina, and South-Carolina ... avowing our allegiance to his Majesty, our affection and regard for our fellow subjects in Great-Britain and elsewhere'; its articles bind them, from 1 December 1774, not to import goods from Great Britain or Ireland and the other goods it names, nor to 'import nor purchase any slave imported after the first day of December next', and its eleventh article directs that a committee be chosen in every county, city and town to see it observed. The papers that print its eleventh article again by itself are not counted again (C-07). The delegates' own Association.",
      role='published_document', words=60, dateline=False,
      head=r'(?:T\s?HE\s+)?A\s?SSOCIATION,?\s*(?:&|&amp;)c\.?\s*',
      core=[r'(?:(?:W\s?E?|We),?\s+)?[Hh]is\s+[Mm]ajesty\W{0,2}s?\s+most\s+(?:dutiful\s+and\s+)?loyal\s+[Ss]ubjects,?\s+the\s+[Dd]elegates'],
      first="The Association of the Continental Congress: the delegates bind themselves to stop importing from Great Britain and Ireland after 1 December 1774.",
      what='the Association',
      printings=[k('PP', '10-31', 2), k('VGPD', '11-03', 1), k('VGR', '11-03', 1), k('CC', '11-07', 1), k('MS', '11-10', 2), k('NHG', '11-11', 3)]),
 dict(id='members-chosen-for-the-general-court-meet-at-salem-october-1774', kind='message_group',
      label="Boston, October 1774: the members chosen for the General Court meet at Salem without the governor, and resolve themselves into a provincial congress",
      definition="Printings of a Boston report of October 1774, printed with the members' resolves: 'Wednesday last the members chosen in consequence of Governor Gage's writ for calling a General Assembly, met at the court-house in Salem pursuant to the precepts; and after waiting a day without being admitted to the usual oath, which should have been administered by the Governor or other constitutional officers; and having chosen the Honourable John Hancock, Esq; to be their Chairman ... they proceeded to business, and passed the following Resolves'; the resolves, dated at Salem on 7 October, say that the governor's proclamation discharging them was unconstitutional, and resolve that they form a provincial congress, to meet at Concord. A Boston paper's report, with the members' own resolves.",
      role='report', words=60, dateline=True,
      core=[r'(?:W\s?EDNESDAY|Wednesday)\s+last,?\s+the\s+members\s+chosen'],
      first="Boston, October 1774: the members chosen for the General Court meet at Salem though the governor does not attend, and resolve to meet as a provincial congress.",
      what='the Boston report of the members chosen meeting at Salem',
      printings=[k('MS', '10-13', 3), k('NHG', '10-14', 2), k('CC', '10-17', 2), k('PP', '10-24', 5), k('VGPD', '10-27', 2)]),
 dict(id='peace-between-russia-and-the-porte-vienna-august-1774', kind='message_group',
      label="Vienna, 3 August 1774: 'a courier arrived here with the news of peace between Russia and the Porte'",
      definition="Printings of a paragraph of the European news, from the London Gazette: 'Vienna, August 3. This day at noon a courier arrived here with the news of peace between Russia and the Porte having been concluded on the 17th of July, at the head quarters at Buyuk Canarochi, and signed, on the part of their respective Sovereigns, by Marshal Count Romanzow, and Achmed Effendi, Chiaga to the Grand Vizir.' A report from Vienna in the London Gazette, in the papers' foreign news.",
      role='report', words=45, dateline=True, stop=r'\s[\[(]\s*London\s+Gaz',
      core=[r'(?:T\s?HIS|This)\s+[Dd]ay,?\s+at\s+[Nn]oon,?\s+a\s+[Cc]ourier\s+arrived', r'[Cc]ourier\s+arrived\s+here\s+with\s+the\s+[Nn]ews\s+of\s+[Pp]eace'],
      first="Vienna, 3 August 1774: a courier brings the news that peace between Russia and the Ottoman Porte was signed on 17 July.",
      what='the Vienna report of the peace between Russia and the Porte',
      printings=[k('MS', '10-13', 2), k('VGPD', '10-13', 2), k('VGR', '10-13', 2), k('NHG', '10-14', 3), k('CC', '10-24', 1)]),
 dict(id='gage-letter-to-peyton-randolph-20-october-1774', kind='document_group',
      label="General Gage's answer to the Congress, Boston, 20 October 1774: 'Representations should be made with candour, and matters stated exactly as they stand'",
      definition="Printings of the letter of General Gage to Peyton Randolph, the president of the Continental Congress, dated Boston, 20 October 1774, in answer to the Congress's letter to him of 10 October: 'Representations should be made with Candour, and Matters stated exactly as they stand. People would be led to believe, from your Letter to me of the 10th Instant, that Works were raised against the Town of Boston, private Property invaded, the Soldiers suffered to insult the Inhabitants'; he answers that 'There is not a single Gun pointed against the Town, no Man's Property has been seized or hurt, except the King's', and that no troops have given less cause for complaint. General Gage's own letter.",
      role='published_document', words=60, dateline=False,
      head=r'(?:T\s?O\s+)?(?:the\s+)?(?:Hon(?:ou?rable|\.)\s+)?P\w+\s+R\s?ANDOLPH,?\s+Esq\w*[;.,]?\s*(?:S\s?IR,?\s*)?(?:\w+,?\s+Oct(?:ober|\.)?\s*20,?\s*1774\.?\s*)?(?:S\s?IR,?\s*)?',
      core=[r'R\s?EPRESENTATI(?:ONS|VES)\s+should\s+be\s+made'],
      first="General Gage answers the Continental Congress: no gun is pointed against Boston and no man's property has been seized.",
      what="General Gage's letter to Peyton Randolph",
      printings=[k('VGPD', '11-10', 1), k('VGR', '11-10', 3), k('PP', '11-28', 2), k('MS', '12-08', 2), k('CC', '12-12', 1)]),
 dict(id='kings-proclamation-dissolving-parliament-1-october-1774', kind='document_group',
      label="The King's proclamation of 30 September 1774 for dissolving the present Parliament and calling another (London Gazette, 1 October)",
      definition="Printings of the King's proclamation, from the London Gazette of 1 October 1774: 'A Proclamation, For dissolving the present Parliament, and declaring the calling of another. George R. Whereas we have thought fit, by and with the advice of our privy council, to dissolve the present Parliament, which now stands prorogued to Tuesday the fifteenth day of November next'; it declares that writs for calling a new Parliament will be issued. The King's own proclamation.",
      role='published_document', words=60, dateline=False,
      head=r'(?:B\s?Y\s+the\s+K\s?\s?I\s?\s?N\s?\s?G[.,]?\s*)?A\s+P\s?\s?R\s?\s?O\s?\s?C\s?\s?L\s?\s?A\s?\s?M\s?\s?A\s?\s?T\s?\s?I\s?\s?O\s?\s?N[.,]?\s*',
      core=[r'[Ff](?:OR|or)\s+[Dd]issolving\s+(?:the|this)\s+present\s+[Pp]arliament'],
      first="The King's proclamation dissolving Parliament, from the London Gazette of 1 October 1774.",
      what="the King's proclamation dissolving Parliament",
      printings=[k('MS', '11-24', 2), k('NHG', '11-25', 1), k('CC', '11-28', 2), k('PP', '11-28', 5), k('VGPD', '12-08', 2), k('VGR', '12-08', 2)]),
 dict(id='provincial-congress-at-cambridge-1-december-1774', kind='document_group',
      label="The Provincial Congress at Cambridge, 1 December 1774: thanks to the other colonies for their donations to Boston and Charlestown",
      definition="Printings of the resolves of the Provincial Congress of Massachusetts Bay of 1 December 1774: 'In Provincial Congress, Cambridge, December 1, 1774. Whereas the rigorous operation of the Boston Port-bill, the metropolis of this province and the neighbouring town of Charlestown have been brought into a most distressful state; many of the inhabitants being deprived of the means of their subsistence ... if they had not been supported by the free and generous contributions of our sister colonies'; it resolves that the Congress's grateful acknowledgments be returned to the several colonies, whose donations it calls convincing proofs of their attachment to the cause of liberty. The Provincial Congress's own resolves.",
      role='published_document', words=60, dateline=False,
      head=r'(?:I\s?N\s+)?P\s?ROVINCIAL\s+C\s?ONGRESS[.,]?\s+C\s?AMBRIDGE,?\s+Dec(?:ember|\.)?\s*1[.,]?\s*1774\.?\s*',
      core=[r'(?:W\s?HEREAS|Whereas),?\s+(?:by\s+)?the\s+rigorous\s+operation'],
      first="The Provincial Congress of Massachusetts Bay thanks the other colonies for their donations to the poor of Boston and Charlestown under the Port bill.",
      what="the Provincial Congress's resolves of 1 December",
      printings=[k('MS', '12-08', 3), k('CC', '12-12', 2), k('NHG', '12-16', 4), k('PP', '12-19', 2), k('VGPD', '12-29', 2), k('VGR', '12-29', 1)]),
 dict(id='scarborough-man-of-war-express-to-england-autumn-1774', kind='context_group',
      label="The Scarborough man of war, sent express from Boston to England in September 1774 and back in December",
      children=['portsmouth-letter-on-the-scarborough-4-october-1774', 'scarborough-returns-to-boston-december-1774'],
      definition="Two reports on the man of war Scarborough, which carried dispatches from Boston to England: a letter from Portsmouth in England of 4 October on her arrival there, and a Boston report of December on her return with dispatches for General Gage. Contains those two groups."),
 dict(id='portsmouth-letter-on-the-scarborough-4-october-1774', parent='scarborough-man-of-war-express-to-england-autumn-1774', kind='message_group',
      label="Portsmouth, England, 4 October 1774: 'Since the Scarborough man of war has arrived from Boston, not one of the men have been suffered to come on shore'",
      definition="Printings of an extract of a letter from Portsmouth in England, dated 4 October 1774: 'Since the Scarborough man of war has arrived from Boston, not one of the men have been suffered to come on shore, neither are their friends permitted to go on board'; the writer says that the officers keep everything secret, 'from which it is conjectured that things are worse at Boston than government are willing the public should be acquainted with', and that ships are being got ready for sea. A private letter printed at second hand, with the writer's conjecture.",
      role='report', words=60, dateline=False,
      head=r'E\s?XTRACT\s+of\s+a\s+[Ll]etter\s+from\s+Portsmouth,?\s+(?:in\s+England,?\s+)?(?:dated\s+)?Oct(?:ober|o?\.)\s+4\.?\s*[\"“]?\s*',
      core=[r'[\"“]?\s*Since\s+the\s+Scarborough'],
      first="Portsmouth, England, 4 October 1774: the crew of the Scarborough, arrived from Boston, are kept on board and everything kept secret.",
      what='the letter from Portsmouth on the Scarborough',
      printings=[k('MS', '12-01', 3), k('CC', '12-05', 3), k('PP', '12-05', 2), k('VGPD', '12-08', 2), k('VGR', '12-08', 3), k('NHG', '12-09', 1)]),
 dict(id='scarborough-returns-to-boston-december-1774', parent='scarborough-man-of-war-express-to-england-autumn-1774', kind='message_group',
      label="Boston, December 1774: 'the Scarborough man of war, which went express from hence to England the beginning of September last, returned hither again, with dispatches'",
      definition="Printings of a Boston paragraph of early December 1774: 'Last Saturday afternoon the Scarborough man of war, which went express from hence to England the beginning of September last, returned hither again, with dispatches for General Gage, the contents of which have not transpired'; it reports that three ships of the line, a frigate and a sloop of war, with 500 marines on board each of the large ships, were said to be about to sail for Boston. The Connecticut Courant prints it in other words ('which was sent express from hence'). A Boston paper's report, partly at second hand ('it was said').",
      role='report', words=60, dateline=True,
      core=[r'(?:L\s?AST|Last)\s+Saturday\s+[Aa]fternoon,?\s+the\s+Scarborough'],
      first="Boston, December 1774: the Scarborough returns from England with dispatches for General Gage; ships of the line with marines are said to follow.",
      what="the Boston report of the Scarborough's return",
      printings=[k('MS', '12-08', 3), k('NHG', '12-09', 1), k('CC', '12-12', 3), k('PP', '12-19', 2), k('VGPD', '12-29', 2), k('VGR', '12-29', 1)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797 and 1800): "BOSTON, Nov. 30th, 1802."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*[\(\[][A-Za-z ,.]+[\)\]])?"
# 24 November: also a year after a stop ('Oct. 16. 1774.'), a date printed alone ('December 5.') and the Massachusetts Spy's
# heading of its Boston news ('THURSDAY, October 13. BOSTON.').
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)((?:(?:" + PLACE + r",?\s+)?" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:[,.]?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?"
                      r"|(?:MONDAY|TUESDAY|WEDNESDAY|T?HURSDAY|FRIDAY|SATURDAY|SUNDAY),\s+" + MONTHS + r"\.?\s*\d{1,2}\.\s*[A-Z]{3,}\.\s*))$")


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
    ('gage-proclamation-against-illegal-combinations-june-1774', 'sn84024739|1774-07-21|1|6'): {'head': 'W\\s?\\s?E\\s+have\\s+just\\s+received\\s+the\\s+following\\s+Proclamation\\s+from\\s+Boston,?\\s+dated\\s+the\\s+29th\\s+ult\\.?\\s+the\\s+Title\\s+of\\s+which\\s+is,?\\s*[\\"“]?\\s*'},
    ('sketch-of-a-popular-noblemans-speech-on-american-affairs-1774', 'sn84024741|1774-09-15|1|2'): {'core': ['(?:T\\s?HE|The)\\s+following\\s+is\\s+a\\s+sketch\\s+of\\s+lord\\s+C\\s?HATHAM']},
}
KEEP_WORDS = {
    ('continental-congress-resolution-of-22-september-1774', 'sn82016139|1774-10-03|1|3'): 76,
    ('continental-congress-resolution-of-22-september-1774', 'sn83021194|1774-10-13|1|3'): 72,
    ('continental-congress-resolution-of-22-september-1774', 'sn83025582|1774-10-07|1|1'): 69,
    ('continental-congress-resolution-of-22-september-1774', 'sn84024741|1774-09-29|1|3'): 69,
    ('gage-letter-to-peyton-randolph-20-october-1774', 'sn82016139|1774-12-12|1|1'): 80,
    ('gage-letter-to-peyton-randolph-20-october-1774', 'sn83021126|1774-11-28|1|2'): 85,
    ('gage-letter-to-peyton-randolph-20-october-1774', 'sn83021194|1774-12-08|1|2'): 85,
    ('gage-letter-to-peyton-randolph-20-october-1774', 'sn84024741|1774-11-10|1|3'): 83,
    ('gage-proclamation-against-illegal-combinations-june-1774', 'sn84024739|1774-07-21|1|6'): 79,
    ('gage-proclamation-for-piety-and-virtue-july-1774', 'sn82016139|1774-08-02|1|2'): 64,
    ('general-brattle-letter-to-governor-gage-august-1774', 'sn82016139|1774-09-12|1|2'): 100,
    ('general-brattle-letter-to-governor-gage-august-1774', 'sn83021126|1774-09-12|1|2'): 81,
    ('general-brattle-letter-to-governor-gage-august-1774', 'sn84024741|1774-09-22|1|3'): 80,
    ('kings-proclamation-dissolving-parliament-1-october-1774', 'sn83021126|1774-11-28|1|5'): 66,
    ('kings-proclamation-dissolving-parliament-1-october-1774', 'sn83021194|1774-11-24|1|2'): 66,
    ('members-chosen-for-the-general-court-meet-at-salem-october-1774', 'sn82016139|1774-10-17|1|2'): 71,
    ('members-chosen-for-the-general-court-meet-at-salem-october-1774', 'sn83021194|1774-10-13|1|3'): 70,
    ('peace-between-russia-and-the-porte-vienna-august-1774', 'sn82016139|1774-10-24|1|1'): 58,
    ('peace-between-russia-and-the-porte-vienna-august-1774', 'sn83021194|1774-10-13|1|2'): 58,
    ('portsmouth-letter-on-the-scarborough-4-october-1774', 'sn82016139|1774-12-05|1|3'): 68,
    ('portsmouth-letter-on-the-scarborough-4-october-1774', 'sn83021126|1774-12-05|1|2'): 68,
    ('portsmouth-letter-on-the-scarborough-4-october-1774', 'sn83025582|1774-12-09|1|1'): 70,
    ('portsmouth-letter-on-the-scarborough-4-october-1774', 'sn84024739|1774-12-08|1|2'): 68,
    ('portsmouth-letter-on-the-scarborough-4-october-1774', 'sn84024741|1774-12-08|1|3'): 68,
    ('provincial-congress-at-cambridge-1-december-1774', 'sn83021126|1774-12-19|1|2'): 67,
    ('provincial-congress-at-cambridge-1-december-1774', 'sn83025582|1774-12-16|1|4'): 67,
    ('provincial-congress-at-cambridge-1-december-1774', 'sn84024739|1774-12-29|1|2'): 67,
    ('quebec-act-1774', 'sn82016139|1774-09-06|1|2'): 65,
    ('quebec-act-1774', 'sn83025582|1774-09-09|1|1'): 65,
    ('scarborough-returns-to-boston-december-1774', 'sn83021194|1774-12-08|1|3'): 64,
    ('scarborough-returns-to-boston-december-1774', 'sn84024741|1774-12-29|1|1'): 62,
    ('sketch-of-a-popular-noblemans-speech-on-american-affairs-1774', 'sn84024741|1774-09-15|1|2'): 78,
    ('virginia-burgesses-resolution-for-a-fast-on-1-june-1774', 'sn83021126|1774-06-06|1|2'): 92,
    ('virginia-burgesses-resolution-for-a-fast-on-1-june-1774', 'sn83021194|1774-07-16|1|2'): 77,
    ('virginia-burgesses-resolution-for-a-fast-on-1-june-1774', 'sn83025582|1774-06-17|1|2'): 88,
    ('virginia-burgesses-resolution-for-a-fast-on-1-june-1774', 'sn84024741|1774-05-26|1|2'): 75,
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
            problems.append((s['id'], key, 'page not in the 1774 pages'))
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
        r['id'] = f'S74-{n:03}'
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
               'admission_rule': 'Reviewed 1774 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1774/'
    return {
        'ledger_id': 'ledger:stories-1774', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1774', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1774, and of 1773 where they reach the 1774 pages (long-running ones '
                   'included), every item in 3 or more papers compared by machine with every page and counted again by its opening, a sweep of '
                   'word-for-word passages shared by 4 or more papers for short items the families miss, phrase searches on all 1,205 pages of '
                   '1774 in both transcriptions, reading of every hit, and scan checks of each admitted passage, by the thin-year rule (Y-THIN, '
                   'as amended on 23 November 2026: an item printed by more than half of the papers that survive for its weeks, and by at '
                   'least 4, is eligible; the items printed by every paper that survives for their weeks are admitted, and the other eligible '
                   'items are chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1773.json': 'retrieval_candidates', d+'count_1774.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1774.py': 'ledger_code', 'work/archive_data/ledgers/stories_1774_review.json': 'scan_review',
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
