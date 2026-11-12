"""Write ledgers/stories_1806.json (v0.10.2 -> v0.11.0): reviewed stories of 1806, round one.

The stories were chosen as for 1776, 1807 and 1808 (make_stories_1807.py, make_stories_1808.py): the automatic families
were split into single printed items with work/story_items.py, run with --long-running, every item printed in 7 or more
newspapers was read, and the chosen items were confirmed with phrase searches over all 4,381 pages of 1806 in both
transcriptions (work/story_phrase_search.py). story_items.py takes the families first printed in its year, so it was also
run with year 1805 over the 1806 pages (items_from_1805.json), for documents and news first printed in December 1805.
See outputs/story_discovery_1806/README.md.

The 1806 pages are those whose issue the base release dates to 1806 (work/year_search_pages.py --printed-dates): release
v0.10.2 dates the 98 Kentucky Gazette and General Advertiser issues that the collection files under 1808 to their printed
dates in 1806. Their page keys and ids keep the filed date, so k() turns a printed date into the filed key, and the
observations are numbered in order of printed date.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as
apply_ledger.py does: the excerpt is the opening of the printed item (about 40-60 words), starting with its
dateline or heading when one stands directly before it. Scan findings, crops and hand-drawn boxes are merged from
stories_1806_review.json after the scan check.

Nine 1806 issues have their RevX transcriptions filed one page off from the scans (derived/revx_page_map.parquet in
the base release, from outputs/revx_page_shift_check/). A printing on a page whose RevX slot holds another page's text
names the scan page and takes its excerpt from the CA transcription of that page, which is numbered as the scans are.

Run from the project root with Python 3.12 (needs outputs/story_discovery_1806/search_pages.json, made by
work/year_search_pages.py 1806 … --printed-dates):
    python work/archive_data/ledgers/make_stories_1806.py [--table]
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1806'
PAGES = PROJECT/'outputs/story_discovery_1806/search_pages.json'
REVIEW = HERE/'stories_1806_review.json'
OUT = HERE/'stories_1806.json'
BASE, TARGET = '0.10.2', '0.11.0'
RELEASE = PROJECT/f'outputs/data_foundation/v{BASE}'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

ADA, NG, NI, EN, VA, KG = 'sn84024012', 'sn85025815', 'sn83045242', 'sn84024736', 'sn84024710', 'sn84038147'
NHG, PGZ, HUS, BJ, LS, RIR = 'sn83025588', 'sn83016082', 'sn83021527', 'sn85059525', 'sn85025609', 'sn83021188'
PAPER = {ADA: 'The Alexandria Daily Advertiser', NG: 'The Norfolk Gazette and Publick Ledger', NI: 'The National Intelligencer',
         EN: 'The Enquirer', VA: 'The Virginia Argus', KG: 'The Kentucky Gazette', NHG: 'The New Hampshire Gazette',
         PGZ: 'The Portland Gazette', HUS: 'The Herald of the United States', BJ: 'The Berkeley and Jefferson Intelligencer',
         LS: 'The Lynchburg Star', RIR: 'The Rhode-Island Republican'}


def issue_dates():
    """(lccn, filed date, edition) -> printed date, from the base release's issues table."""
    out = {}
    with (RELEASE/'tables/issues.jsonl').open(encoding='utf8') as stream:
        for line in stream:
            row = json.loads(line)
            _, lccn, filed, ed = row['id'].split(':')
            out[(lccn, filed, int(ed))] = row['publication_date']
    return out


PRINTED = issue_dates()
FILED = {}
for (_lccn, _filed, _ed), _printed in PRINTED.items():
    if _printed != _filed:
        assert (_lccn, _printed, _ed) not in FILED, ('two issues printed on one day', _lccn, _printed)
        FILED[(_lccn, _printed, _ed)] = _filed


def k(paper, date, page, ed=1):
    """Page key of a printing, from its printed date (MM-DD in 1806): the key keeps the date the collection files the issue under."""
    printed = f'{YEAR}-{date}'
    return f'{paper}|{FILED.get((paper, printed, ed), printed)}|{ed}|{page}'


def printed_date(key):
    lccn, filed, ed, _ = key.split('|')
    return PRINTED.get((lccn, filed, int(ed)), filed)


def misfiled():
    """Page keys of 1806 pages whose RevX slot holds another scan page's text (shifted, two pages off or repeated)."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if printed_date(key(r['page_id'])).startswith(YEAR)}


MISFILED = misfiled()

# Story groups, as for 1776, 1807 and 1808. 'printings' lists each printing's page; a tuple adds overrides for that printing:
# core (regexes for the item's first words), role, field, note, words, dateline (include a dateline or heading directly
# before), back (start at the beginning of the sentence that holds the core, for quoted documents), stop (end the
# excerpt before the first match of this regex).
# Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
# account, in the papers' own words, never as what happened.
ACT = r'A\s?N\s+A\s?CT,?\s+'
TO_HOUSES = r'(?:T\s?O\s+THE\s+(?:THE\s+)?S\s?ENATE,?\s+(?:AND|&)\s+H\s?OUSE\s+OF\s+R\s?EPRESENTATIVES,?(?:\s+OF\s+THE\s+U[\w.]*\s?S\w*[.,]?)?["”]?\s+)?'
STORIES = [
 # --- January to March (first reader's half of the year) ---------------------------------------------------------------
 dict(id='vienna-opens-its-gates', kind='message_group', label='Strasburgh, 17 November 1805: Vienna opens its gates', role='report', words=55, dateline=False,
      core=[r'(?:S\s?TRASBURGH?,?\s+)?(?:N\s?OVEMBER|N\s?OV\.?)\s*17\.?\s*[—–-]*\s*["“]?\s*T\s?HE\s+city\s+of\s+Vienna\s+has\s+just', r'T\s?HE\s+city\s+of\s+Vienna\s+has\s+just\s+opened'],
      definition=("Printings of a paragraph dated Strasburgh, 17 November 1805, from French papers that reached New York in January 1806: "
                  "'The city of Vienna has just opened its gates for the first time to a victorious army. This glory was reserved for Frenchmen.' "
                  "A report from the French side."),
      first="A Strasburgh paragraph of 17 November 1805: 'The city of Vienna has just opened its gates for the first time to a victorious army.'", what='the Strasburgh paragraph',
      printings=[k(NG, '01-06', 3), k(VA, '01-10', 5), k(EN, '01-11', 3), k(NI, '01-13', 2), k(ADA, '01-15', 2), k(RIR, '01-16', 3), k(HUS, '01-18', 3), k(KG, '02-06', 3)]),
 dict(id='antigua-letter-american-vessels', kind='message_group', label="A shipmaster's letter from Antigua: American vessels carried in", role='report', words=55,
      core=[r'T\s?HE\s+following\s+extract\s+of\s+a\s+letter\s+was\s+put\s+in(?:to)?\s+our\s+hands\s+by\s+a\s+mercantile', r'Ext\w+\s+of\s+a\s+letter\s+from\s+a\s+master\s+of\s+a\s+vessel\s+to\s+his\s+owner'],
      definition=("Printings of an extract of a letter from the master of an American vessel, dated Antigua, 28 December 1805, first printed in "
                  "the Norfolk Gazette, which had it from 'a mercantile friend': 'Every American vessel coming from a French Island, with cargo, is "
                  "certain to be carried in'. One writer's account; it alleges that 'a junto consisting of the Judge, the Lawyers, the owners of "
                  "privateers' shares the costs charged to Americans."),
      first="A shipmaster writes from Antigua (28 December 1805) that 'Every American vessel coming from a French Island, with cargo, is certain to be carried in'.", what='the letter from Antigua',
      printings=[k(NG, '01-15', 2), k(VA, '01-21', 3), k(ADA, '01-22', 3), k(NI, '01-24', 3), k(BJ, '01-31', 3), k(NHG, '02-11', 3), k(RIR, '02-13', 3)]),
 dict(id='hamet-caramalli-1806', kind='context_group', label="Hamet Caramalli's claim on the United States, 1806",
      definition=("Papers on the claim of Hamet Caramalli, 'ex-bashaw of Tripoli', on the United States after the peace with Tripoli, as the "
                  "papers printed them in 1806: the President's message of 13 January, two documents sent with it (the convention Hamet made "
                  "with William Eaton, and Hamet's letter to the President), and the report of the Senate committee of 17 March. Contains "
                  "those four groups."),
      children=['message-13-january-hamet-caramalli', 'eaton-hamet-convention', 'hamet-letter-to-the-president', 'senate-report-hamet-caramalli']),
 dict(id='message-13-january-hamet-caramalli', parent='hamet-caramalli-1806', kind='document_group', label="The President's message of 13 January on Hamet Caramalli", role='published_document', words=55, dateline=False,
      core=[TO_HOUSES + r'I\s?\s?LAY\s+before\s+Congress\s+the\s+application\s+of\s+H\s?AMET'],
      definition=("Printings of President Jefferson's message to Congress of 13 January 1806: 'I lay before Congress the application of Hamet "
                  "Caramalli, elder brother of the reigning bashaw of Tripoli, soliciting from the United States attention to his services and "
                  "sufferings in the late war against that state'. The executive's own account of its dealings with him."),
      first="President Jefferson lays before Congress (13 January 1806) 'the application of Hamet Caramalli, elder brother of the reigning bashaw of Tripoli'.", what="the President's message",
      printings=[k(NI, '01-20', 2), k(ADA, '01-22', 2), k(EN, '01-23', 2), k(NG, '01-24', 3), k(VA, '01-28', 1), k(RIR, '01-30', 3), k(PGZ, '02-03', 2), k(NHG, '02-04', 2), k(HUS, '02-15', 1)]),
 dict(id='eaton-hamet-convention', parent='hamet-caramalli-1806', kind='document_group', label='The convention between William Eaton and Hamet Caramalli', role='published_document', words=55, dateline=False,
      core=[r'C\s?ONVENTION,?\s+[Bb]etween\s+the\s+U\s?NITED\s+S\s?TATES\s+of\s+A\s?MERICA,?\s+and\s+his\s+[Hh]ighness\s+H\s?AMET'],
      definition=("Printings of the convention of 1805 'between the United States of America and his highness Hamet Caramalli, bashaw of "
                  "Tripoli', made by William Eaton, one of the documents sent with the President's message of 13 January 1806: 'GOD IS INFINITE. "
                  "ARTICLE I. There shall be a firm and perpetual peace and free intercourse' between the two. An agreement, as the message printed it."),
      first="The convention made by William Eaton with Hamet Caramalli, 'bashaw of Tripoli', printed with the President's message.", what='the convention',
      printings=[k(NI, '01-20', 2), k(ADA, '01-22', 3), k(NG, '01-27', 2), k(VA, '01-28', 2), k(EN, '01-28', 4), k(PGZ, '02-03', 2), k(HUS, '02-15', 1), k(KG, '03-15', 2)]),
 dict(id='hamet-letter-to-the-president', parent='hamet-caramalli-1806', kind='message_group', label="Hamet's letter to the President", role='published_document', words=55, dateline=False,
      core=[r'(?:L\s?ETTER[.,]?\s+(?:F\s?rom\s+)?)?(?:A\s?CHMET|A\s?GAMEMNON)\s+B\s?ASHAW,?\s+to\s+the\s+P\s?RESIDENT', r'(?:L\s?ETTER[.,]?\s+)?F\s?rom\s+\w+\s+B\s?ASHAW,?\s+to\s+the\s+P\s?RESIDENT'],
      definition=("Printings of a letter from Hamet ('Achmet Bashaw') to the President, sent to Congress with the message of 13 January 1806: "
                  "'For nearly eleven years, I have been labouring under the weight of misfortune'. His own account of the war against Tripoli "
                  "and of his part in it with General Eaton."),
      first="Hamet's letter to the President, sent with the message of 13 January 1806: 'For nearly eleven years, I have been labouring under the weight of misfortune'.", what="Hamet's letter",
      printings=[k(NI, '01-31', 2), k(ADA, '02-05', 3), k(NG, '02-07', 2), k(EN, '02-08', 1), k(KG, '02-26', 3), k(HUS, '03-15', 1), k(PGZ, '04-07', 2)]),
 dict(id='senate-report-hamet-caramalli', parent='hamet-caramalli-1806', kind='document_group', label="The Senate committee's report on Hamet Caramalli, 17 March", role='published_document', words=55, dateline=False,
      core=[r'M\s?R\.?\s+B\s?RADLEY,?\s+from\s+the\s+[Cc]ommittee\s+to\s+whom\s+was\s+referred\s+the\s+application'],
      definition=("Printings of the report of the Senate committee on Hamet Caramalli's application, presented by Mr. Bradley on 17 March 1806. "
                  "It says he was 'deceived and amused with the prospect of being placed on the throne' and proposes relief for him. A committee's "
                  "findings and proposal, which differ from the President's account."),
      first="The Senate committee reports on Hamet Caramalli's application (17 March 1806): he was 'deceived and amused with the prospect of being placed on the throne'.", what="the committee's report",
      printings=[k(ADA, '03-27', 2), k(EN, '03-28', 2), k(NG, '04-02', 2), k(HUS, '04-05', 2), k(PGZ, '04-07', 2), k(NHG, '04-22', 1), k(KG, '04-30', 2)]),
 dict(id='trade-with-st-domingo-1806', kind='context_group', label='Trade with St. Domingo: the French complaints and the act of 28 February 1806',
      definition=("The President's message to the Senate of 10 January 1806 with the French government's complaints against American trade with "
                  "St. Domingo, and the act of 28 February 1806 that prohibited trade with the parts of the island 'not in possession, and under "
                  "the acknowledged government of France'. Contains those two groups."),
      children=['message-french-complaints-st-domingo', 'act-suspending-trade-with-st-domingo']),
 dict(id='message-french-complaints-st-domingo', parent='trade-with-st-domingo-1806', kind='document_group', label="The President's message with the French complaints on trade with St. Domingo", role='published_document', words=55, dateline=False,
      core=[r'M\s?ESSAGE,?\s+[Ff]rom\s+the\s+P\s?resident\s+of\s+the\s+U[\w.]*\s?S\w*\.?,?\s+transmitting\s+[Dd]ocuments', r'The\s+following\s+[Mm]essage\s+addressed\s+to\s+the\s+Senate',
            r'I\s?N\s+compliance\s+with\s+the\s+request\s+of\s+the\s+Senate,?\s+expressed\s+in\s+their\s+resolution'],
      definition=("Printings of the President's message to the Senate of 10 January 1806, sending 'documents and papers ... relative to complaints "
                  "by the government of France, against the commerce carried on by American citizens to the French Island of St. Domingo': letters "
                  "of General Turreau, the French minister, to the Secretary of State, and of Talleyrand to General Armstrong. The complaints are "
                  "the French government's own account, in its own words (Turreau writes of trade 'with the rebels of every color')."),
      first="The President sends the Senate (10 January 1806) the French government's 'complaints ... against the commerce carried on by American citizens to the French Island of St. Domingo'.", what="the message and the French letters",
      printings=[k(NI, '01-17', 1), k(ADA, '01-20', 2), k(NG, '01-20', 2), k(HUS, '01-25', 2), k(PGZ, '02-03', 1), k(VA, '02-04', 2), k(RIR, '02-06', 1)]),
 dict(id='act-suspending-trade-with-st-domingo', parent='trade-with-st-domingo-1806', kind='document_group', label='The act of 28 February 1806 suspending trade with parts of St. Domingo', role='published_document', words=55, dateline=False,
      core=[r'(?:A\s?N\s+(?:A\s?CT,?\s+)?)?T\s?O\s+(?:S\s?USPEND|E\s?XTEND)\s+THE\s+C\s?OMMERCIAL\s+I\s?N\w+\s+BETWEEN'],
      definition=("Printings of the act of Congress approved on 28 February 1806 'To suspend the commercial intercourse between the United States, "
                  "and certain parts of the island of St. Domingo': trade with any part of the island 'not in possession, and under the acknowledged "
                  "government of France, shall be, and is hereby prohibited'. A law."),
      first="The act of 28 February 1806 prohibits trade with the parts of St. Domingo 'not in possession, and under the acknowledged government of France'.", what='the act',
      printings=[k(NI, '03-05', 2), k(EN, '03-18', 4), k(HUS, '03-29', 1), (k(NHG, '04-01', 1), dict(field=CA, note='RevX lacks this item, so the excerpt comes from the older CA transcription.')),
                 k(VA, '04-01', 2), k(KG, '04-05', 2), k(RIR, '06-05', 1)]),
 dict(id='riley-journal-rochefort-squadron', kind='message_group', label="Captain Riley's journal: the Rochefort squadron at Teneriffe", role='report', words=55, dateline=False,
      core=[r'Extracts?\s+from\s+the\s+[Jj]ournal\s+kept\s+by', r'[Jj]ournal\s+kept\s+by\s+[Cc]ap\w*\.?\s+R\w+'],
      definition=("Printings of extracts from the journal of Captain Riley of the brig Eliza and Mary, from a Nassau paper of 1 January 1806: he "
                  "reached Teneriffe on 5 November 1805 and 'learnt the following intelligence': that the French squadron from Rochefort had come "
                  "into Santa Cruz with prizes, and had 'sunk or burned all neutral vessels they fell in with at sea'. A shipmaster's report of what he heard."),
      first="Captain Riley's journal: at Teneriffe (November 1805) he learnt that the Rochefort squadron had 'sunk or burned all neutral vessels they fell in with at sea'.", what="Captain Riley's journal",
      printings=[k(NG, '01-22', 2), k(EN, '01-28', 2), (k(ADA, '01-28', 3), dict(field=CA, core=[r'Extrassctsfrbin'], note='The page has no RevX transcription; the excerpt comes from the older CA transcription, which is garbled here.')),
                 k(VA, '01-31', 3), k(HUS, '02-08', 2), k(PGZ, '02-10', 2), k(NHG, '02-11', 2), k(RIR, '02-13', 2), k(KG, '02-19', 3)]),
 dict(id='british-seizures-papers-1806', kind='context_group', label='British seizures and impressment: papers sent to Congress, January 1806',
      definition=("Documents the President sent to Congress in January 1806 on the capture of American vessels and the impressment of American "
                  "seamen by Britain: his message of 17 January, the letter of the American minister in London to Lord Mulgrave that was sent "
                  "with it, and the Secretary of State's report on 'new principles interpolated into the law of nations'. Contains those three groups."),
      children=['message-17-january-1806', 'monroe-to-mulgrave-1805', 'madison-report-new-principles']),
 dict(id='message-17-january-1806', parent='british-seizures-papers-1806', kind='document_group', label="The President's message of 17 January on British seizures and impressment", role='published_document', words=55, dateline=False,
      core=[TO_HOUSES + r'I\s?N\s+my\s+message\s+to\s+both\s+[Hh]ouses\s+of\s+[Cc]ongress,?\s+at\s+the\s+opening'],
      definition=("Printings of President Jefferson's message to Congress of 17 January 1806: 'In my message to both Houses of Congress, at the "
                  "opening of their present session, I submitted to their attention, among other subjects, the oppression of our commerce and "
                  "navigation by the irregular practices of armed vessels, public and private'. The executive's account, with documents."),
      first="President Jefferson's message of 17 January 1806 on 'the oppression of our commerce and navigation by the irregular practices of armed vessels'.", what="the President's message",
      printings=[k(NI, '01-22', 2), k(VA, '01-28', 2), k(EN, '01-28', 1), k(ADA, '01-29', 2), k(RIR, '01-30', 3), k(HUS, '02-01', 3), k(PGZ, '02-03', 3), k(KG, '03-05', 3)]),
 dict(id='monroe-to-mulgrave-1805', parent='british-seizures-papers-1806', kind='document_group', label="Monroe's letter to Lord Mulgrave, 23 September 1805", role='published_document', words=55, dateline=False,
      core=[r'(?:N\s?o\.?\s*1[23],?\s+)?G\s?REAT\s+C\s?UMBERLAND\s+P\s?LACE', r'M\s?Y\s+L\s?ORD,?\s+I\s?\s?F\s?LATTERED\s+myself'],
      definition=("Printings of the letter of James Monroe, the American minister in London, to Lord Mulgrave of the British government, dated "
                  "Great Cumberland Place, 23 September 1805, sent to Congress with the President's message of 17 January 1806: 'I flattered "
                  "myself, from what passed in our last interview, that I should have been honored' with an answer. The American minister's case "
                  "against the British courts' decisions on neutral trade."),
      first="James Monroe writes to Lord Mulgrave (London, 23 September 1805): 'I flattered myself, from what passed in our last interview, that I should have been honored' with an answer.", what="Monroe's letter",
      printings=[k(NI, '01-27', 1), k(ADA, '01-30', 2), k(EN, '02-01', 2), k(NG, '02-03', 2), k(VA, '02-07', 1), k(NHG, '02-18', 1), k(RIR, '02-20', 1), k(HUS, '02-22', 4)]),
 dict(id='madison-report-new-principles', parent='british-seizures-papers-1806', kind='document_group', label="The Secretary of State's report on 'new principles' in the law of nations", role='published_document', words=55, dateline=False,
      core=[r'T\s?HE\s+Secretary\s+of\s+State,?\s+to\s+whom\s+the\s+[Pp]resident\s+has\s+been\s+pleased', r'REPORT\W{1,4}T\s?HE\s+most\s+important\s+of\s+th\w+\s+principles',
            r'T\s?HE\s+most\s+important\s+of\s+th\w+\s+principles,?\s+interpolated'],
      definition=("Printings of the report of the Secretary of State to the Senate, sent with a message of the President, 'respecting \"new "
                  "principles interpolated into the law of nations\"': 'The most important of the principles interpolated into the law of nations, "
                  "is that which appears to be maintained by the British government and its prize courts'. The American government's account and argument."),
      first="The Secretary of State reports to the Senate on the 'new principles interpolated into the law of nations' by the British government and its prize courts.", what="the Secretary of State's report",
      printings=[k(NI, '02-03', 1), k(ADA, '02-07', 2), k(EN, '02-08', 4), k(NG, '02-10', 3), k(BJ, '02-14', 2), k(PGZ, '02-17', 2), k(NHG, '02-18', 2)]),
 dict(id='yrujo-and-the-government-1806', kind='context_group', label='The Spanish minister Yrujo and the government, 1806',
      definition=("The Marquis de Casa Yrujo, Spain's minister to the United States, and the American government in January 1806: his circular "
                  "to the other foreign ministers against the President's message, and the letter in which the Secretary of State told him that "
                  "the President expected his departure, with his answers. Contains those two groups."),
      children=['yrujo-circular-to-the-foreign-ministers', 'madison-yrujo-letters-january-1806']),
 dict(id='yrujo-circular-to-the-foreign-ministers', parent='yrujo-and-the-government-1806', kind='message_group', label="Yrujo's circular to the foreign ministers", role='published_document', words=55, dateline=False,
      core=[r'A\s+translation\s+from\s+the\s+French,?\s+of\s+the\s+Marquis', r'(?:M\s?arquis\s+de\s+\w+\s+\w+.{0,3}s\s+circular,?\s+addressed)', r'T\s?HE\s+want\s+of\s+correctness\s+which\s+appears'],
      definition=("Printings of the circular of the Marquis de Casa Yrujo to the foreign ministers in the United States, dated Philadelphia, 21 "
                  "January 1806, in a translation from the French: 'The want of correctness which appears to prevail throughout the article, "
                  "relative to Spain, of the message' of the President. With his note to the Secretary of State. The Spanish minister's own account."),
      first="The Spanish minister, the Marquis de Casa Yrujo, writes to the foreign ministers (21 January 1806) of 'the want of correctness' in the President's message on Spain.", what="Yrujo's circular",
      printings=[k(ADA, '01-28', 2), k(VA, '01-31', 2), k(NG, '01-31', 2), k(EN, '02-01', 2), k(BJ, '02-14', 1), k(HUS, '02-15', 3), k(PGZ, '02-17', 1), k(KG, '02-22', 2)]),
 dict(id='madison-yrujo-letters-january-1806', parent='yrujo-and-the-government-1806', kind='message_group', label="Madison's letter to Yrujo of 15 January and Yrujo's answers", role='published_document', words=55, dateline=False,
      core=[r'(?:\(?N\s?O\.?\s*(?:1|I)\.?\)?\s+)?D\s?EPARTMENT\s+OF\s+S\s?TATE[.,]?\s+(?:Jan\w*\.?\s+15|15th\s+Jan)', r'I\s?N\s+consequence\s+of\s+the\s+just\s+objections'],
      definition=("Printings of the letter of the Secretary of State to the Marquis de Casa Yrujo of 15 January 1806: 'In consequence of the just "
                  "objections which your conduct has furnished against your continuance here, as the organ of communication on the part of his "
                  "Catholic Majesty', the President expects that his departure 'will not be unnecessarily postponed'; with the Marquis's answers. "
                  "Each side's own words, printed by the papers with their own remarks."),
      first="The Secretary of State writes to the Marquis de Casa Yrujo (15 January 1806) of 'the just objections which your conduct has furnished against your continuance here'.", what='the letters',
      printings=[k(NI, '02-19', 3), k(ADA, '02-19', 2), k(EN, '02-21', 2), k(NG, '02-24', 2), k(VA, '02-25', 2), k(PGZ, '03-03', 1), k(HUS, '03-08', 4), k(KG, '03-12', 2)]),
 dict(id='british-goods-resolutions-1806', kind='context_group', label='Congress and British goods, 1806',
      definition=("The House of Representatives and the President on stopping imports from Great Britain in 1806, as the papers printed it: "
                  "Mr. Gregg's resolution, Mr. J. Randolph's speech against it, the National Intelligencer's paragraph on the vote for Mr. "
                  "Nicholson's resolution, the act of 18 April prohibiting certain British goods, and the President's message of 3 December "
                  "asking that the act be suspended. Contains those five groups."),
      children=['gregg-resolution-29-january', 'randolph-speech-5-march', 'national-intelligencer-on-the-vote-of-17-march', 'non-importation-act-18-april', 'message-3-december-1806']),
 dict(id='gregg-resolution-29-january', parent='british-goods-resolutions-1806', kind='document_group', label="Mr. Gregg's resolution, 29 January", role='published_document', words=55, dateline=False,
      core=[r'W\s?HEREAS\s+Great\s+Britain\s+impre\w+\s+citizens'],
      definition=("Printings of the resolution offered in the House by Mr. Gregg of Pennsylvania on 29 January 1806: 'Whereas Great Britain "
                  "impresses citizens of the United States, and compels them to serve on board her ships of war, and also seizes and condemns "
                  "vessels belonging to citizens of the United States', no goods of Great Britain or its colonies should be imported 'until "
                  "equitable and satisfactory arrangements on these points shall be made'. A proposal in Congress."),
      first="Mr. Gregg moves (29 January 1806): 'Whereas Great Britain impresses citizens of the United States', British goods should not be imported until arrangements are made.", what="Mr. Gregg's resolution",
      printings=[k(NI, '01-31', 3), k(ADA, '02-01', 3), k(NG, '02-03', 2), k(VA, '02-04', 3), k(EN, '02-06', 4), k(PGZ, '02-10', 2), k(NHG, '02-11', 2), k(BJ, '02-14', 2), k(KG, '02-22', 3)]),
 dict(id='randolph-speech-5-march', parent='british-goods-resolutions-1806', kind='message_group', label="Mr. J. Randolph's speech on Mr. Gregg's resolution, 5 March", role='report', words=55, dateline=False,
      core=[r'M\s?R\.?\s+J\.?\s+R\s?ANDOLPH\.?\s*[—–-]*\s*I\s+am\s+extremely\s+afraid', r'I\s+am\s+extremely\s+afraid,?\s+[Ss]ir'],
      definition=("Printings of the report of the speech of Mr. J. Randolph of Virginia in the House on 5 March 1806, in the debate on Mr. Gregg's "
                  "resolution, as the National Intelligencer gave it: 'I am extremely afraid, sir, that so far as it may depend on my acquaintance "
                  "with details connected with the subject, I have very little right to address you'. A member's argument against the resolution."),
      first="Mr. J. Randolph speaks against Mr. Gregg's resolution (5 March 1806): 'I am extremely afraid, sir, that ... I have very little right to address you'.", what="Mr. Randolph's speech",
      printings=[k(NI, '03-17', 1), k(ADA, '03-19', 2), k(VA, '03-21', 2), k(EN, '03-21', 2), k(NG, '03-24', 2), k(PGZ, '04-14', 1), k(KG, '05-03', 2)]),
 dict(id='national-intelligencer-on-the-vote-of-17-march', parent='british-goods-resolutions-1806', kind='message_group', label='The National Intelligencer on the vote of 17 March', role='report', words=55,
      core=[r'T\s?HE\s+[Hh]ouse\s+of\s+[Rr]epresentatives,?\s+the\s+immediate\s+organs?\s+of\s+the\s+people'],
      definition=("Printings of the National Intelligencer's paragraph of 19 March 1806 on the House vote of 17 March: 'The House of "
                  "Representatives, the immediate organs of the people, have, after mature deliberation, taken ground in vindication of our "
                  "violated rights, on which we congratulate the nation'; with Mr. Nicholson's resolution and the yeas and nays. The Washington "
                  "paper's own report and judgement."),
      first="The National Intelligencer (19 March 1806): the House 'have, after mature deliberation, taken ground in vindication of our violated rights'.", what="the National Intelligencer's paragraph",
      printings=[k(NI, '03-19', 2), k(ADA, '03-20', 3), k(VA, '03-25', 3), k(EN, '03-25', 2), k(BJ, '03-28', 2), k(NHG, '04-08', 2), k(KG, '04-09', 2), k(RIR, '04-10', 2)]),
 dict(id='lisbon-and-st-ubes-report', kind='message_group', label='Lisbon and St. Ubes: a report of a French victory', role='report', words=55, dateline=False,
      core=[r'T\s?HE\s+report\s+at\s+Lisbon\s+and\s+St\.?\s+Ubes'],
      definition=("Printings of a report brought to Baltimore by the ship Commerce from St. Ubes, in February 1806: 'The report at Lisbon and "
                  "St. Ubes was, that a recent engagement had taken place along the whole French line'. A rumour heard in Portugal at the end of "
                  "December 1805, as the ship's master told it."),
      first="The ship Commerce brings to Baltimore 'The report at Lisbon and St. Ubes': a battle 'along the whole French line'.", what='the report from Lisbon and St. Ubes',
      printings=[k(NI, '02-12', 3), k(ADA, '02-13', 3), k(VA, '02-18', 3), k(EN, '02-18', 2), k(NG, '02-19', 3), k(RIR, '02-20', 3), k(HUS, '02-22', 3), k(NHG, '02-25', 2), k(KG, '03-08', 3)]),
 dict(id='austerlitz-in-the-papers-1806', kind='context_group', label='The battle of Austerlitz in the papers, 1806',
      definition=("Four accounts of the battle of 2 December 1805 near Austerlitz, between the French army and the armies of Russia and Austria, "
                  "as American papers printed them in February and March 1806: a notice of the British government, a letter of Marshal Berthier, "
                  "the French army's thirtieth bulletin, and the Emperor's proclamation to his army. Each is one side's account. Contains those four groups."),
      children=['london-bulletin-17-december-1805', 'berthier-letter-to-massena', 'thirtieth-bulletin-grand-army', 'napoleon-proclamation-after-austerlitz']),
 dict(id='london-bulletin-17-december-1805', parent='austerlitz-in-the-papers-1806', kind='message_group', label='The London bulletin of 17 December 1805', role='published_document', words=55, dateline=False,
      core=[r'B\s?ULLETIN\.?\W{0,4}Government\s+received\s+(?:la[sf]t\s+night\s+accounts|accounts\s+la[sf]t\s+night)', r'Government\s+received\s+(?:la[sf]t\s+night\s+accounts|accounts\s+la[sf]t\s+night)'],
      definition=("Printings of a bulletin issued by the British government in London in December 1805: 'Government received last night accounts, "
                  "dated at Olmutz, the 3d, by which it appears that a general battle took place on the 2d between the French and Austrian Russian "
                  "armies at Wischau'. The British government's notice, on the first reports from the allied side."),
      first="A London bulletin: 'Government received last night accounts, dated at Olmutz' of 'a general battle' on 2 December.", what='the London bulletin',
      printings=[k(ADA, '02-15', 3), k(NI, '02-17', 2), k(NG, '02-17', 3), k(NHG, '02-18', 3), k(VA, '02-18', 2),
                 (k(EN, '02-18', 1), dict(field=CA, note='RevX shortens this column with "..." and leaves out the bulletin, so the excerpt comes from the older CA transcription.')),
                 k(HUS, '02-22', 2), k(PGZ, '02-24', 2)]),
 dict(id='berthier-letter-to-massena', parent='austerlitz-in-the-papers-1806', kind='message_group', label="Marshal Berthier's letter to Marshal Massena on the battle", role='published_document', words=55, dateline=False,
      core=[r'B\s?LOODY\s+B\s?ATTLE\s+OF\s+THE\s+(?:2|S\s?ECOND)', r'Copy\s+of\s+a\s+letter\s+from\s+Marshal\s+B\s?ERTHIER'],
      definition=("Printings of a letter of Marshal Berthier, the French minister of war and major general of the Grand Army, to Marshal Massena, "
                  "on the battle of 2 December 1805, translated for the Baltimore American from papers brought from Leghorn: 'I am impatient, "
                  "marshal, to send you' the news of the battle. The French army's own account."),
      first="Marshal Berthier writes to Marshal Massena of the battle of 2 December 1805: 'I am impatient, marshal, to send you' the news.", what="Marshal Berthier's letter",
      printings=[k(NI, '03-05', 3), k(ADA, '03-05', 2), k(VA, '03-07', 3), k(EN, '03-07', 3), k(NG, '03-07', 2), k(RIR, '03-13', 2), k(BJ, '03-14', 3), k(HUS, '03-15', 3), k(KG, '03-22', 2)]),
 dict(id='thirtieth-bulletin-grand-army', parent='austerlitz-in-the-papers-1806', kind='message_group', label='The thirtieth bulletin of the Grand Army', role='published_document', words=55, dateline=False,
      core=[r'T\s?HIRTIETH\s+B\s?ULLETIN\s+OF\s+THE\s+G\s?RAND\s+A\s?RMY', r'The\s+6th\s+Frimaire,?\s+the\s+[Ee]mperor,?\s+upon\s+receiving'],
      definition=("Printings of the thirtieth bulletin of the French Grand Army, dated Austerlitz, 12 Frimaire, year 14 (3 December 1805): 'The 6th "
                  "Frimaire, the emperor, upon receiving the communication of the full powers of Messrs. de Stadion and de Giulay, offered previously "
                  "an armistice'. The French army's official account of the battle."),
      first="The thirtieth bulletin of the Grand Army, dated Austerlitz, 12 Frimaire (3 December 1805): the French army's account of the battle.", what='the thirtieth bulletin',
      printings=[k(NI, '03-14', 2), k(ADA, '03-15', 2), k(NG, '03-17', 1), (k(NHG, '03-18', 2), dict(note="Printed under the bulletin's heading but without its first paragraph; it begins 'At 1 o'clock in the morning the Emperor mounted on horseback'.")),
                 k(VA, '03-18', 5), k(RIR, '03-20', 1), k(HUS, '03-22', 1), k(KG, '04-02', 2)]),
 dict(id='napoleon-proclamation-after-austerlitz', parent='austerlitz-in-the-papers-1806', kind='message_group', label="The Emperor's proclamation to the army after the battle", role='published_document', words=55, dateline=False,
      core=[r'S\s?OLDIERS\s*[,!.:;]?\s+I\s+am\s+\w+\s+with\s+you'],
      definition=("Printings of the Emperor Napoleon's proclamation to his army after the battle of 2 December 1805, dated Austerlitz, 12 Frimaire: "
                  "'Soldiers, I am satisfied with you'; an army of 100,000 men 'has been in less than four hours cut to pieces and dispersed'. "
                  "A commander's address to his own army."),
      first="The Emperor Napoleon to his army after the battle: 'Soldiers, I am satisfied with you'.", what="the Emperor's proclamation",
      printings=[k(NI, '03-14', 2), k(ADA, '03-15', 3), k(NG, '03-17', 1), k(NHG, '03-18', 2), (k(VA, '03-18', 5), dict(note='Begins at the foot of page 5 and continues on page 6.')), k(RIR, '03-20', 2),
                 (k(BJ, '03-21', 2), dict(note='A different translation from the other printings. Begins at the foot of page 2 and continues on page 3.')), k(HUS, '03-22', 2), k(KG, '04-02', 2)]),
 dict(id='serious-questions-to-mr-madison', parent='miranda-expedition-1806', kind='message_group', label='"Serious Questions to Mr. Madison" on General Miranda\'s expedition', role='report', words=55, dateline=False,
      core=[r'S\s?ERIOUS\s+Q\s?UESTIONS\s+T\s?O\s+(?:M\s?R\.?|THE\s+H\s?ON)'],
      definition=("Printings of a communication first printed in the Philadelphia Gazette of 19 February 1806: 'SERIOUS QUESTIONS TO MR. MADISON. "
                  "Did Miranda go to Washington about the middle of December last? Had he two long interviews with you?' It asks what the "
                  "government knew of the ship Leander, fitted out at New York for General Miranda's expedition. Questions that carry an "
                  "allegation, by an unnamed writer."),
      first="'SERIOUS QUESTIONS TO MR. MADISON. Did Miranda go to Washington about the middle of December last?'", what='the Serious Questions',
      printings=[k(NI, '02-26', 2), k(ADA, '02-26', 3), k(EN, '02-28', 3), k(NG, '02-28', 2), k(VA, '03-04', 2), k(BJ, '03-07', 2), k(PGZ, '03-17', 1), k(NHG, '03-18', 2), k(KG, '03-19', 2)]),
 dict(id='speech-opening-parliament-21-january', kind='document_group', label='The speech opening Parliament, 21 January 1806', role='published_document', words=55, dateline=False,
      core=[r'(?:T\s?HE\s+)?S\s?PEECH,?\s+OF\s+THE\s+L\s?ORDS\s+C\s?OMM\w+', r'M\s?Y\s+L\s?ORDS\s+(?:AND|&)\s+G\s?ENTLEMEN,?\s+["“]?\s*I\s?N\s+pursuance\s+of\s+the\s+authority',
            r'Extracts?\s+from\s+His\s+Majesty.s\s+Message,?\s+on\s+the\s+opening\s+of\s+Parliament'],
      definition=("Printings of the speech of the Lords Commissioners to both Houses of Parliament on 21 January 1806, made in the King's name: "
                  "'In pursuance of the authority given to us by his Majesty's Commission under the Great Seal, among other things, to declare the "
                  "cause of his holding this Parliament'. It speaks of the success of the King's arms at sea and of the war on the Continent. The "
                  "British government's statement. Two papers printed only a part of it, headed 'His Majesty's Message'."),
      first="The speech opening Parliament (21 January 1806), made by the Lords Commissioners in the King's name.", what='the speech',
      printings=[k(PGZ, '03-17', 2), k(VA, '03-21', 3), k(EN, '03-21', 3), k(NG, '03-21', 3), k(ADA, '03-22', 3),
                 (k(NI, '03-24', 2), dict(field=CA, note='RevX lacks this item, so the excerpt comes from the older CA transcription.')),
                 (k(NHG, '03-25', 2), dict(role='document_excerpt', note="An extract, headed 'Extracts from His Majesty's Message, on the opening of Parliament yesterday.'")),
                 (k(RIR, '04-03', 1), dict(role='document_excerpt', note="An extract, headed 'Extract from His Majesty's Message, on the opening of Parliament, yesterday.'; it runs on to page 2.")),
                 k(KG, '04-09', 2)]),
 dict(id='treaty-of-pressburg', kind='document_group', label='The treaty of Pressburg between Austria and France', role='published_document', words=55, dateline=False,
      core=[r'(?-i:D\s?EFINITIVE\s+T\s?REATY\s+BETWEEN\s+F\s?RANCE)', r'(?-i:T\s?REATY\s+OF\s+P\s?EACE)\.?\s+["“]?\s*(?:N\s?APOLEON|Napoleon|B\s?ETWEEN|Between)',
            r'His\s+[Mm]ajesty\s+the\s+[Ee]mperor\s+of\s+Germany\s+and\s+Austria,?\s+(?:and|&)\s+his\s+[Mm]ajesty\s+the\s+[Ee]mperor\s+of\s+the\s+French'],
      definition=("Printings of the treaty of peace between Austria and France signed at Pressburg on 26 December 1805: 'His majesty the emperor "
                  "of Germany and Austria, and his majesty the emperor of the French, king of Italy, equally animated with a desire to put an end "
                  "to the calamities of war'. Some papers printed it with the Emperor Napoleon's act of ratification before it. A treaty."),
      first="The treaty of peace between Austria and France, signed at Pressburg on 26 December 1805.", what='the treaty',
      printings=[k(RIR, '03-20', 2), k(NI, '03-24', 3), k(NHG, '03-25', 1), k(ADA, '03-26', 2), k(NG, '03-26', 1), k(HUS, '03-29', 1), k(VA, '04-01', 5), k(KG, '04-16', 2)]),
 # --- April to December (second reader's part of the year) --------------------------------------------------------------
 dict(id='house-secret-journal-spain-1806', kind='document_group', label="The House's secret journal on Spanish affairs, published in April", role='published_document', words=55, dateline=False,
      core=[r'(?:S\s?ECRET\s+P\s?ROCEEDINGS\s+M\s?ADE\s+P\s?UBLICK?\.?\s+)?On\s+M\w+\s+the\s+ho\w*\W?\w*\s+of\s+represent\w+\s+were\s+[\w ]{0,20}?engaged\s+until',
            r'T\s?HE\s+injunction\s+of\s+secrecy\s+having\s+been\s+taken\s+off', r'S\s?ECRET\s+S\s?ESSIONS\.?\s+J\s?ANUARY', r'C\s?LOSED\s+D\s?OORS\s+P\s?ROCEEDINGS'],
      definition=("Printings of the journal of the House of Representatives' proceedings with closed doors in December 1805 and January 1806 on "
                  "the President's message of 6 December 1805 about Spain, made public at the beginning of April 1806 when 'the injunction of "
                  "secrecy' was taken off: the committee's report ('The committee have beheld with just indignation the hostile spirit manifested "
                  "by the court of Madrid'), the resolutions and the votes. Six papers printed the journal as the National Intelligencer gave it; "
                  "three printed a shorter account with the report or the resolutions. An official record."),
      first="The House's proceedings with closed doors on Spain are made public (April 1806): 'The committee have beheld with just indignation the hostile spirit manifested by the court of Madrid'.", what='the secret journal',
      printings=[k(NI, '04-02', 2), k(ADA, '04-03', 2), k(NG, '04-07', 2), k(VA, '04-08', 2), k(EN, '04-08', 2),
                 (k(BJ, '04-11', 3), dict(role='document_excerpt', note="A summary from the Frederick-Town Herald, headed 'CLOSED DOORS PROCEEDINGS', with the resolutions from the journal.")),
                 (k(NHG, '04-15', 2), dict(role='document_excerpt', note="A shorter account headed 'SECRET SESSIONS', which quotes the beginning of the committee's report.")),
                 (k(HUS, '04-19', 1), dict(role='document_excerpt', note="A shorter account of the proceedings, introduced: 'The injunction of secrecy having been taken off, the following detail of proceedings is inserted'.")),
                 k(KG, '04-23', 2)]),
 dict(id='bremen-letter-austrian-officers', kind='message_group', label='A Bremen letter on the sentences of the Austrian officers', role='report', words=55, dateline=False,
      core=[r'A\s+private\s+letter\s+from\s+Bremen'],
      definition=("Printings of a paragraph from London papers of February 1806: 'A private letter from Bremen of the 11th inst. contains the "
                  "following article, relative to the sentences passed on the officers whose conduct produced the recent misfortunes to the House "
                  "of Austria'. A report at second hand, from a private letter."),
      first="A London paragraph: 'A private letter from Bremen' reports 'the sentences passed on the officers whose conduct produced the recent misfortunes' of Austria.", what='the Bremen paragraph',
      printings=[k(ADA, '04-04', 3), k(NI, '04-07', 3), k(NG, '04-07', 3), k(VA, '04-08', 3), k(EN, '04-11', 2), k(HUS, '04-12', 2), k(PGZ, '04-14', 2), k(NHG, '04-15', 2), k(BJ, '04-18', 2), k(KG, '04-26', 2)]),
 dict(id='miranda-expedition-1806', kind='context_group', label="General Miranda's expedition, 1806",
      definition=("Printings about the expedition that General Francisco de Miranda fitted out at New York in the ship Leander for the coast of "
                  "Caracas, as the papers printed them through 1806: questions put to the Secretary of State in February, a letter from on board the "
                  "Leander in April, Miranda's proclamation of 28 June, and a report of the expedition's defeat in November. Contains those four groups."),
      children=['serious-questions-to-mr-madison', 'leander-letter-from-jacmel', 'miranda-proclamation-28-june', 'miranda-defeat-report']),
 dict(id='leander-letter-from-jacmel', parent='miranda-expedition-1806', kind='message_group', label='A letter from on board the Leander at Jacmel, 1 March', role='report', words=55, dateline=False,
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+a\s+gentleman\s+on\s+board\s+the\s+Leander'],
      definition=("Printings of an extract of a letter 'from a gentleman on board the Leander', dated Jacmel, 1 March 1806: 'General Miranda has "
                  "explained to us his plan'. One member of the expedition's own account."),
      first="A letter from on board the Leander, dated Jacmel, 1 March 1806: 'General Miranda has explained to us his plan'.", what='the letter from the Leander',
      printings=[k(ADA, '04-09', 3), k(NI, '04-11', 3), k(EN, '04-11', 3), k(NG, '04-11', 2), k(VA, '04-15', 3), k(NHG, '04-22', 3), k(BJ, '04-25', 2), k(HUS, '04-26', 2), k(KG, '04-26', 3)]),
 dict(id='miranda-proclamation-28-june', parent='miranda-expedition-1806', kind='document_group', label="General Miranda's proclamation of 28 June: 'Friends and Countrymen'", role='published_document', words=55, dateline=False,
      core=[r'F\s?RIENDS\s+(?:AND|&)\s+C\s?OUNTRYMEN'],
      definition=("Printings of the proclamation that General Miranda issued on 28 June 1806 ('published at Trinidad', in one paper's words): "
                  "'FRIENDS AND COUNTRYMEN, The glorious opportunity now presents itself of relieving from oppression and arbitrary government, a "
                  "people who are worthy of a better fate'. The expedition's own appeal."),
      first="General Miranda's proclamation of 28 June 1806: 'FRIENDS AND COUNTRYMEN, The glorious opportunity now presents itself of relieving from oppression and arbitrary government'.", what="Miranda's proclamation",
      printings=[k(PGZ, '08-04', 2), k(NI, '08-04', 3), k(NG, '08-04', 2), k(VA, '08-06', 2), k(EN, '08-08', 2), k(HUS, '08-09', 3), k(NHG, '08-12', 2), k(BJ, '08-15', 1),
                 k(KG, '08-18', 3), k(LS, '08-21', 2), (k(KG, '09-15', 3), dict(note='Printed again, introduced as "said to be one of Miranda\'s proclamations".'))]),
 dict(id='miranda-defeat-report', parent='miranda-expedition-1806', kind='message_group', label="'Miranda defeated': Captain Foster's report from Trinidad", role='report', words=55,
      core=[r'M\s?IRANDA\s+D\s?EFEATED', r'[Cc]ap\w*\.?\s+F\w+,?\s+(?:who\s+)?arrived\s+(?:here|at\s+Boston)'],
      definition=("Printings of a Boston paragraph of November 1806 headed 'MIRANDA DEFEATED': Captain Foster, arrived from Trinidad, 'informs, "
                  "that three days previous to his sailing, a Mr. Taylor, who had embarked in the expedition with Miranda, reached that place with "
                  "the unpleasant intelligence of their defeat'. A report at second hand."),
      first="A Boston paragraph, 'MIRANDA DEFEATED': a member of the expedition had reached Trinidad 'with the unpleasant intelligence of their defeat'.", what='the report of the defeat',
      printings=[k(NHG, '11-18', 2), k(HUS, '11-22', 3), k(PGZ, '11-24', 2), k(NI, '11-24', 3), k(ADA, '11-24', 3), k(VA, '11-28', 3), k(EN, '11-28', 2), k(BJ, '12-05', 2), k(KG, '12-15', 3)]),
 dict(id='tunisian-cruiser-message-april-1806', kind='document_group', label="The President's message on Tunis, April 1806", role='published_document', words=55, dateline=False,
      core=[TO_HOUSES + r'D\s?URING\s+the\s+blockade\s+of\s+Tripoli'],
      definition=("Printings of President Jefferson's message to Congress on the dispute with Tunis, read in the House on 14 April 1806: 'During the "
                  "blockade of Tripoli by the squadron of the U. S. a small cruiser, under the flag of Tunis, with two prizes' tried to enter the "
                  "port. The executive's own account."),
      first="President Jefferson's message on Tunis (April 1806): 'During the blockade of Tripoli by the squadron of the U. S. a small cruiser, under the flag of Tunis' was taken.", what="the President's message",
      printings=[k(NI, '04-16', 2), k(ADA, '04-18', 2), k(NG, '04-21', 2), k(VA, '04-22', 2), k(EN, '04-22', 4), k(HUS, '04-26', 2), k(PGZ, '04-28', 2), k(NHG, '04-29', 2), k(KG, '05-06', 3)]),
 dict(id='non-importation-act-18-april', parent='british-goods-resolutions-1806', kind='document_group', label='The act of 18 April 1806 prohibiting certain British goods', role='published_document', words=55, dateline=False,
      core=[r'(?:A\s?N\s+A\s?CT,?\s+)?T\s?O\s+PROHIBIT\s+THE\s+(?:IM|EX)PORTATION\s+OF\s+CERTAIN\s+GOODS'],
      definition=("Printings of the act of Congress approved on 18 April 1806 'To prohibit the importation of certain goods, wares and "
                  "merchandise': from 15 November 'it shall not be lawful to import into the United States, or the territories thereof, from any "
                  "port or place situated in Great Britain or Ireland' the goods it lists. A law."),
      first="The act of 18 April 1806 'To prohibit the importation of certain goods, wares and merchandise' from Great Britain and Ireland.", what='the act',
      printings=[k(NI, '04-25', 2), k(NG, '05-02', 2), k(VA, '05-16', 3), k(EN, '05-23', 4), k(NHG, '06-10', 1), k(KG, '07-15', 2),
                 (k(HUS, '10-11', 1), dict(note='Printed again in October, before the act took effect.')), (k(VA, '11-28', 2), dict(note='Printed again in November, when the act took effect.'))]),
 dict(id='leander-affair-1806', kind='context_group', label='The Leander off New York, 1806',
      definition=("Printings after a cannon shot from the British ship Leander killed an American seaman near the entrance of New York harbour on "
                  "25 April 1806, which the President's proclamation calls 'a murder': the resolutions of a meeting at New York and the President's "
                  "proclamation of 3 May. Contains those two groups."),
      children=['new-york-meeting-resolutions-leander', 'proclamation-against-the-leander']),
 dict(id='new-york-meeting-resolutions-leander', parent='leander-affair-1806', kind='document_group', label='Resolutions of a New York meeting after the Leander shot', role='published_document', words=55, dateline=False, stop=r'Pierce',
      core=[r'R\s?e\w*\W{0,3}\s*[Tt]hat\s+the\s+[Cc]itizens\s+of\s+the\s*U\w*\.?\s*S\w*\.?\s+are\s+of\s+right'],
      definition=("Printings of the resolutions of 'a meeting of Federal Republicans' at the Tontine Coffee House, New York, in late April 1806, called "
                  "'to take into consideration the defenceless state of our harbor': 'Resolved, That the citizens of the U. S. are of right, and "
                  "according to the constitution and laws of the land, entitled to the enjoyment of life, liberty, and property'. A party meeting's "
                  "own resolutions."),
      first="A New York meeting resolves (April 1806) 'That the citizens of the U. S. are of right ... entitled to the enjoyment of life, liberty, and property'.", what='the resolutions',
      printings=[k(NI, '05-02', 3), k(ADA, '05-02', 3), k(HUS, '05-03', 2), k(PGZ, '05-05', 2), k(NG, '05-05', 2), k(VA, '05-06', 2), k(EN, '05-06', 3), k(BJ, '05-09', 2)]),
 dict(id='proclamation-against-the-leander', parent='leander-affair-1806', kind='document_group', label="The President's proclamation of 3 May against the Leander, Cambrian and Driver", role='published_document', words=55, dateline=False, stop=r'John\s+Pierce',
      core=[r'B\s?Y\s+T\s?HOMAS\s+J\s?EFFERSON,?\s+P\s?RESIDENT', r'A\s+P\s?ROCLAMATION\.?\s+W\s?HEREAS,?\s+satisfactory\s+information'],
      definition=("Printings of President Jefferson's proclamation of 3 May 1806: Henry Whitby, commanding the British armed vessel Leander, had by a "
                  "cannon shot within the waters of the United States near New York committed what it calls 'a murder'; the Leander, the Cambrian "
                  "and the Driver are to leave American waters, and the President will 'forbid all intercourse with the said armed vessels' if they "
                  "do not. An official document; the charge is the President's. The excerpts end before the name of the man killed."),
      first="President Jefferson's proclamation of 3 May 1806 against the British armed vessels Leander, Cambrian and Driver.", what="the President's proclamation",
      printings=[k(NI, '05-12', 3), k(ADA, '05-12', 3), k(NG, '05-12', 3), k(NHG, '05-13', 2), k(RIR, '05-15', 2), k(VA, '05-16', 3), k(EN, '05-16', 3), k(PGZ, '05-19', 1), k(LS, '05-22', 1), k(KG, '05-27', 3)]),
 dict(id='napoleon-speech-legislative-body-1806', kind='document_group', label="The Emperor Napoleon's speech opening the Legislative Body, March 1806", role='published_document', words=55, dateline=False,
      core=[r'G\s?ENTLEMEN,?\s+\w{3}\s+[Dd]eputies\s+(?:from|of)\s+\w{3}\s+[Dd]epartment'],
      definition=("Printings of the speech of the Emperor Napoleon at the opening of the French Legislative Body in March 1806: 'Since your last "
                  "session, the greatest part of Europe has entered into a coalition with England. My armies have never ceased to conquer'. A "
                  "head of state's own account."),
      first="The Emperor Napoleon opens the Legislative Body (March 1806): 'Since your last session, the greatest part of Europe has entered into a coalition with England'.", what="the Emperor's speech",
      printings=[k(PGZ, '05-05', 2), k(NHG, '05-06', 1), k(ADA, '05-07', 3), k(VA, '05-09', 2), k(BJ, '05-09', 2), k(HUS, '05-10', 1), k(KG, '05-20', 3), k(LS, '05-22', 1)]),
 dict(id='st-domingo-report-may-1806', kind='message_group', label='A Philadelphia report of movements in St. Domingo, May 1806', role='report', words=55,
      core=[r'W\s?E\s+learn,?\s+from\s+a\s+gentleman\s+who\s+arrived\s+in\s+(?:this\s+city|Philadelphia)\s+a\s+day\s+or\s+two\s+ago'],
      definition=("Printings of a Philadelphia paragraph of 10 May 1806: 'We learn from a gentleman who arrived in this city a day or two ago, from "
                  "St. Domingo, that at the time of his departure there were very general movements among the subjects of the black emperor "
                  "Dessalines'; the cause was not known, 'but it was said that some advices had been received by way of Jamaica'. A traveller's "
                  "report at second hand, in the paper's words."),
      first="A Philadelphia paragraph (10 May 1806): a traveller from St. Domingo reports 'very general movements among the subjects of the black emperor Dessalines'.", what='the report from St. Domingo',
      printings=[k(ADA, '05-14', 3), k(VA, '05-16', 2), k(NHG, '05-20', 2), k(EN, '05-20', 2), k(NG, '05-21', 3), k(BJ, '05-23', 2), k(PGZ, '05-26', 2), k(KG, '06-03', 3)]),
 dict(id='linois-taken-1806', kind='message_group', label="Norfolk, May 1806: 'The French Admiral Linois taken'", role='report', words=55,
      core=[r'T\s?HE\s+F\s?RENCH\s+A\s?DMIRAL\s+L\w+\s+T\s?AKEN', r'F\s?RENCH\s+A\s?DMIRAL\s+L\w+\s+T\s?AKEN'],
      definition=("Printings of a Norfolk paragraph of May 1806 headed 'The French Admiral Linois taken': the British frigate Tartar, arrived in "
                  "Hampton Roads from Bermuda, had boarded the American ship Hunter from Lisbon, whose people had seen the French ship Marengo, "
                  "'Admiral Linois', and the frigate Belle Poule with the squadron of Sir John Borlase Warren, 'captured by Sir John'. A report "
                  "passed on from ship to ship."),
      first="A Norfolk paragraph (May 1806): 'The French Admiral Linois taken' by Sir John Borlase Warren's squadron.", what='the Norfolk paragraph',
      printings=[k(NG, '05-19', 2), k(VA, '05-23', 3), k(EN, '05-23', 3), k(NI, '05-26', 2), k(BJ, '05-30', 3), k(HUS, '05-31', 2), k(PGZ, '06-02', 2), k(RIR, '06-05', 2), k(KG, '06-14', 3)]),
 dict(id='dodge-report-cape-francois', kind='message_group', label="Captain Dodge's report from Cape François, June 1806", role='report', words=55,
      core=[r'M\s?A\w*ACRE\s+AT\s+C\s?APE.?F\s?RANCOIS', r'W\s?E\s+learn\s+from\s+[Cc]ap\w*\.?\s+Dodge', r'[Cc]ap\w*\.?\s+Dodge\s*,?\s+of\s+the\s+[Ss]chooner'],
      definition=("Printings of a New York paragraph of 9 June 1806 headed 'MASSACRE AT CAPE FRANCOIS': Captain Dodge of the schooner Mary Ann, "
                  "arrived from Cape François, reported 'that on the 14th and 15th of May, a general massacre of all the remaining white inhabitants "
                  "of Cape Francois took place, and it was said, generally, throughout that part of this ill-fated island under the dominion of "
                  "Dessalines'. A shipmaster's report, partly hearsay, in the paper's words."),
      first="A New York paragraph (9 June 1806), 'MASSACRE AT CAPE FRANCOIS': a shipmaster's report from Cape François.", what="Captain Dodge's report",
      printings=[k(NI, '06-13', 3), k(PGZ, '06-16', 2), k(NHG, '06-17', 3), k(VA, '06-17', 2), k(EN, '06-17', 2), k(RIR, '06-19', 2), k(LS, '06-26', 2)]),
 dict(id='heath-declines-lieutenant-governor', kind='message_group', label='General Heath declines to be Lieutenant Governor of Massachusetts', role='report', words=55, dateline=False,
      core=[r'T\s?o\s+the\s+[Hh]on\w*\.?\s+(?:the\s+)?[Ss]enate.{0,160}?Massachusetts[.,]?\s+G\s?ENTLEMEN', r'G\s?ENTLEMEN,?\s+I\s?\s?HAVE\s+been\s+notified'],
      definition=("Printings of the letter of William Heath to the Senate and House of Representatives of Massachusetts, June 1806: 'I have been "
                  "notified by a very respectable committee of both Houses, that I have been elected Lieutenant Governor of the Commonwealth'; he "
                  "declines the office. A public man's own statement."),
      first="William Heath writes to the Massachusetts legislature (June 1806) that he has been elected Lieutenant Governor, and declines.", what="General Heath's letter",
      printings=[k(PGZ, '06-16', 2), k(NHG, '06-17', 2), k(ADA, '06-20', 3), k(NI, '06-23', 2), k(NG, '06-23', 2), k(EN, '06-24', 3), k(VA, '06-25', 3), k(RIR, '06-26', 2), k(LS, '07-31', 2)]),
 dict(id='swedish-bulletin-lauenburg', kind='message_group', label='A Swedish bulletin: the Prussians cross into Lauenburg', role='published_document', words=55,
      core=[r'S\s?WEDISH\s+B\s?ULLETIN', r'Head\s*[Qq]uarters\s+of\s+the\s+Swedish\s+[Aa]rmy', r'Reports?\s+(?:of|received\s+on)\s+the\s+2[35]\w*,?\s+(?:received\s+)?from\s+[Aa]dj'],
      definition=("Printings of a 'Swedish bulletin' from the headquarters of the Swedish army, April 1806, from London papers: reports 'received "
                  "from adjutant general count Lowenhielm' said the Prussians had taken several villages near Lauenburg, and on the 23rd 'the "
                  "Prussians passed the Lauenburg frontier'. One army's own account."),
      first="A Swedish bulletin (April 1806): 'the Prussians passed the Lauenburg frontier' and the Swedish troops withdrew.", what='the Swedish bulletin',
      printings=[k(NI, '06-25', 3), k(ADA, '06-26', 3), k(HUS, '06-28', 3), k(PGZ, '06-30', 2), k(NG, '06-30', 2), k(EN, '07-01', 2), k(VA, '07-02', 2), k(BJ, '07-11', 2), k(KG, '07-12', 3)]),
 dict(id='detroit-letter-1-june-1806', kind='message_group', label='A letter from Detroit of 1 June on councils of the Indian nations', role='report', words=55, dateline=False,
      core=[r'Extracts?\s+of\s+a\s+[Ll]etter\s+from\s+a\s+[Gg]entleman\s+(?:at|in)\s+Detroit'],
      definition=("Printings of an extract of a letter from a gentleman at Detroit, dated 1 June 1806: traders had reported to the acting governor "
                  "'the frequent secret councils held by the Indians', and the writer says 'We are now no longer in doubt, that the Indians are "
                  "preparing to commence war against the United States'. One American writer's account of traders' reports, with his forecast."),
      first="A letter from Detroit (1 June 1806) reports 'the frequent secret councils held by the Indians' and the writer's fear of war.", what='the Detroit letter',
      printings=[k(NI, '07-02', 3), k(VA, '07-05', 2), k(NG, '07-07', 2), (k(NHG, '07-08', 2), dict(role='condensed_report', core=[r'From\s+Detroit,?\s+J\w+\s+1,?\s+1806'], note="A shorter version in other words, headed 'From Detroit, June 1, 1806. INDIAN WARS.'")), k(EN, '07-08', 2), k(BJ, '07-11', 2), k(LS, '07-17', 3), k(KG, '07-26', 3)]),
 dict(id='fox-note-blockade-may-1806', kind='document_group', label="Fox's note to Monroe on the blockade from the Elbe to Brest", role='published_document', words=55, dateline=False,
      core=[r'T\s?HE\s+following\s+letter\s+has\s+been\s+addressed\s+from\s+M\w*\.?\s+S\s?ecretary\s+F\s?ox', r'D\s?OWNING.?\s?S\s?TREET,?\s+May\s+1?6'],
      definition=("Printings of the note of Charles James Fox, the British Secretary of State for Foreign Affairs, to James Monroe, the American "
                  "minister (Downing Street, May 1806): the King 'has thought fit to direct that the necessary measures should be taken for the "
                  "blockade of the coasts, rivers and ports from the river Elbe to the port of Brest, both inclusive'. The British government's notice."),
      first="Fox informs Monroe (Downing Street, May 1806) of the blockade 'from the river Elbe to the port of Brest'.", what="Fox's note",
      printings=[k(NI, '07-11', 3), (k(HUS, '07-12', 2), dict(note="Found by the loose search of papers without a printing: the transcription reads 'Mrs. Secretary Fox'.")), k(PGZ, '07-14', 2), k(NHG, '07-15', 3), k(EN, '07-15', 2), k(VA, '07-16', 2), k(NG, '07-16', 3), k(LS, '07-24', 1)]),
 dict(id='louis-napoleon-king-of-holland', kind='document_group', label='Louis Napoleon proclaimed King of Holland, 1806', role='published_document', words=55, dateline=False,
      core=[r'["“]?\s*L\s?OUIS\s+N\s?APOLEON,?\s+by\s+the\s+[Gg]race\s+of\s+G\s?OD'],
      definition=("Printings of the proclamation of Louis Napoleon as King of Holland (June 1806), 'read this day to the military, and announced to "
                  "the people': 'Louis Napoleon, by the Grace of God and the constitutional laws of the state, King of Holland, to all who shall see "
                  "and read this, greeting'. A ruler's own proclamation."),
      first="Louis Napoleon proclaims himself 'King of Holland, to all who shall see and read this, greeting'.", what='the proclamation',
      printings=[k(NI, '08-06', 3), k(NG, '08-08', 3), k(NHG, '08-12', 2), k(EN, '08-12', 2), k(VA, '08-13', 2), k(HUS, '08-16', 1), k(LS, '08-21', 1), k(BJ, '08-22', 2)]),
 dict(id='spanish-troops-near-the-sabine-1806', kind='context_group', label='Spanish and American troops near the Sabine, 1806',
      definition=("Letters printed from September to November 1806 on Spanish troops east of the Sabine and the American army sent against them: "
                  "a letter of 2 August headed 'HOSTILE APPEARANCE', a Natchitoches letter on Mr. Freeman's exploring party, and a letter of "
                  "General Wilkinson. Each is one writer's account, from the American side. Contains those three groups."),
      children=['hostile-appearance-letter-2-august', 'freeman-party-turned-back', 'wilkinson-letter-red-river']),
 dict(id='hostile-appearance-letter-2-august', parent='spanish-troops-near-the-sabine-1806', kind='message_group', label="'Hostile appearance': a letter of 2 August on Spanish troops", role='report', words=55,
      core=[r'(?:H\s?OSTILE\s+A\s?PPEARANCES?\.?\s+)?Extra\w*\s+of\s+a\s+[Ll]etter\s+from\s+a\s+gentleman\s+(?:at|of)\s+Nat\w+'],
      definition=("Printings of an extract of a letter to the editor of a Natchez paper, dated 2 August 1806 and headed 'HOSTILE APPEARANCE': 'On "
                  "or about the 18th of July ult. a detachment of Spanish troops' came toward Natchitoches. The papers give the writer's place as "
                  "Natchez or Natchitoches. One writer's account."),
      first="'HOSTILE APPEARANCE': a letter of 2 August 1806 reports 'a detachment of Spanish troops' near Natchitoches.", what='the letter',
      printings=[k(KG, '09-04', 3), k(NI, '09-12', 2), k(VA, '09-13', 3), k(NG, '09-15', 2), k(EN, '09-19', 3), k(HUS, '09-20', 3), k(PGZ, '09-22', 2), k(NHG, '09-23', 2), k(LS, '09-25', 1),
                 (k(EN, '10-03', 3), dict(note='Printed again.'))]),
 dict(id='freeman-party-turned-back', parent='spanish-troops-near-the-sabine-1806', kind='message_group', label="Natchitoches, 26 August: Mr. Freeman's party turned back", role='report', words=55, dateline=False,
      core=[r'(?:E\s?XTRACT\W{0,3}\s*)?(?:N\s?a\w*ch\w*,?\s+(?:A\s?ug\w*\.?\s+26|26(?:th)?\s+A\s?ug\w*)\.?,?\s*(?:180[56]\.?)?\s*["“]?\s*)?M\s?r\.?\s+Freeman\s+returned'],
      definition=("Printings of an extract from Natchitoches, 26 August 1806: 'Mr. Freeman returned to this place on Saturday last, after having "
                  "ascended 430 miles above this place, where the Spaniards had been waiting for him'. One writer's account of the exploring party "
                  "sent up the Red River."),
      first="Natchitoches, 26 August 1806: 'Mr. Freeman returned to this place on Saturday last', turned back by Spanish troops.", what='the Natchitoches letter',
      printings=[k(ADA, '10-09', 3), k(NI, '10-10', 1), k(EN, '10-10', 3), k(VA, '10-11', 3), k(PGZ, '10-13', 2), k(NG, '10-13', 2), k(BJ, '10-17', 3), k(LS, '10-23', 2)]),
 dict(id='wilkinson-letter-red-river', parent='spanish-troops-near-the-sabine-1806', kind='message_group', label="General Wilkinson's letter from the Rapids of Red River, 19 September", role='report', words=55,
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+[Gg]en\w*\.?\s+W\s?ilkinson', r'[Gg]eneral\s+Wilkinson\s+to\s+a\s+gentleman\s+in\s+this\s+town'],
      definition=("Printings of an extract of a letter of General Wilkinson, dated Rapids of Red River, 19 September 1806: 'My orders, and the "
                  "conduct of the Mexicans, are so much at variance'; 'I fear you will be informed blood has been spilt'. The American commander's "
                  "own account, with his forecast."),
      first="General Wilkinson writes from the Rapids of Red River (19 September 1806): 'My orders, and the conduct of the Mexicans, are so much at variance'.", what="General Wilkinson's letter",
      printings=[k(KG, '11-03', 3), k(ADA, '11-13', 3), (k(BJ, '11-14', 3), dict(role='condensed_report', core=[r'C\s?INCINNATI,?\s+Oct\w*\.?\s+21\.?\s+A\s+letter\s+received\s+in\s+town'], note="A Cincinnati paragraph of 21 October that summarises a letter of 16 September and quotes the General's words ('I fear you will be informed blood has been spilt').")), k(NI, '11-17', 2), k(NG, '11-17', 3), k(VA, '11-18', 3), k(HUS, '11-22', 2)]),
 dict(id='lewis-and-clark-return-1806', kind='context_group', label='The return of Lewis and Clark, 1806',
      definition=("The first printed news of the return of Captain Lewis, Captain Clark and their party to St. Louis from the Pacific, in September "
                  "1806: the National Intelligencer's announcement and Captain Clark's letter to his brother. Contains those two groups."),
      children=['lewis-arrival-announced', 'clark-letter-to-his-brother']),
 dict(id='lewis-arrival-announced', parent='lewis-and-clark-return-1806', kind='message_group', label="The National Intelligencer announces Captain Lewis's arrival at St. Louis", role='report', words=55,
      core=[r'I\s?T\s+is,?\s+with\s+the\s+sincerest\s+pleasure,?\s+that\s+we\s+announce'],
      definition=("Printings of the National Intelligencer's paragraph of 27 October 1806: 'It is with the sincerest pleasure, that we announce to "
                  "our fellow citizens, the arrival of CAPTAIN LEWIS, with his exploring party, at St. Louis'; the President had a letter from him "
                  "dated 23 September. The government paper's report."),
      first="The National Intelligencer (27 October 1806) announces 'the arrival of CAPTAIN LEWIS, with his exploring party, at St. Louis'.", what="the National Intelligencer's announcement",
      printings=[k(NI, '10-27', 3), k(ADA, '10-28', 3), k(EN, '10-31', 3), k(VA, '11-01', 2), k(NG, '11-03', 2), k(BJ, '11-07', 3), k(HUS, '11-08', 3), k(PGZ, '11-10', 1), k(NHG, '11-11', 2), k(LS, '11-13', 3)]),
 dict(id='clark-letter-to-his-brother', parent='lewis-and-clark-return-1806', kind='message_group', label="Captain Clark's letter to his brother, St. Louis, 23 September", role='report', words=55, dateline=False,
      core=[r'(?:S\s?T\.?\s+L\s?OUIS,?\s+.{0,25}?1806\.?\s+)?D\s?EAR\s+B\s?ROTHER[,.]?\s+W\s?E\s+arrived'],
      definition=("Printings of Captain Clark's letter to his brother, dated St. Louis, 23 September 1806: 'We arrived at this place at 12 o'clock "
                  "to-day, from the Pacific Ocean, where we remained during the last winter, near the entrance of the Columbia river'. One of the "
                  "party's own account of the journey."),
      first="Captain Clark writes to his brother (St. Louis, 23 September 1806): 'We arrived at this place at 12 o'clock to-day, from the Pacific Ocean'.", what="Captain Clark's letter",
      printings=[k(KG, '10-16', 3), k(NI, '11-03', 2), k(ADA, '11-04', 2), k(EN, '11-04', 2), k(VA, '11-05', 2), k(NG, '11-07', 2), (k(LS, '11-13', 1), dict(field=CA, note='RevX lacks this item, so the excerpt comes from the older CA transcription.')), k(BJ, '11-14', 1)]),
 dict(id='francis-ii-gives-up-the-imperial-crown', kind='document_group', label='Francis II gives up the crown of the German Empire', role='published_document', words=55,
      core=[r'T\s?HE\s+Paris\s+M\s?onit\w+\s+of\s+the\s+14th\s+August\s+contains'],
      definition=("Printings of the declaration of Francis II, emperor of Austria, giving up 'the high office of emperor of Germany', from the "
                  "Paris Moniteur of 14 August 1806: 'Since the peace of Presburg all our attention and all our care have been employed to fulfil "
                  "with scrupulous fidelity all the engagements' of that treaty. A ruler's own declaration."),
      first="The Paris Moniteur of 14 August 1806 prints 'the resignation of the high office of emperor of Germany, by Francis, emperor of Austria'.", what="the Emperor's declaration",
      printings=[k(ADA, '10-17', 3), k(NI, '10-20', 2), k(NG, '10-22', 3), k(EN, '10-24', 1), k(VA, '10-25', 3), k(LS, '10-30', 1), k(KG, '11-06', 3)]),
 dict(id='buenos-ayres-captured-1806', kind='message_group', label='London, September 1806: Buenos Ayres captured', role='report', words=55,
      core=[r'(?:C\s?APTURE\s+OF\s+B\s?UENOS\s+A\s?YRES\.?\s+)?T\s?HE\s+official\s+news\s+of\s+the\s+capture\s+of\s+Buenos'],
      definition=("Printings of a London paragraph of September 1806: 'The official news of the capture of Buenos Ayres is received. It capitulated "
                  "on the 27th of June. There fell into the hands of the English 1,291,338 dollars'. A report from the British side."),
      first="A London paragraph (September 1806): 'The official news of the capture of Buenos Ayres is received. It capitulated on the 27th of June.'", what='the London paragraph',
      printings=[k(HUS, '11-01', 2), k(NHG, '11-04', 2), k(NI, '11-07', 2), k(ADA, '11-07', 3), k(EN, '11-11', 2), k(NG, '11-12', 2), k(VA, '11-14', 3), k(BJ, '11-14', 3), k(LS, '11-20', 1), k(KG, '12-01', 3)]),
 dict(id='burr-enterprise-1806', kind='context_group', label="Colonel Burr's enterprise in the papers, November 1806",
      definition=("The first widely printed items on Aaron Burr's enterprise in the West, November 1806: a Chillicothe report of an affidavit against "
                  "him in Kentucky, and the President's proclamation of 27 November against a military expedition against the dominions of Spain. "
                  "Contains those two groups."),
      children=['kentucky-affidavit-against-burr', 'proclamation-27-november-1806']),
 dict(id='kentucky-affidavit-against-burr', parent='burr-enterprise-1806', kind='message_group', label='Chillicothe, 13 November: the Kentucky affidavit against Colonel Burr', role='report', words=55, dateline=False,
      core=[r'I\s?MPORTANT\s+C\s?OMMUNICATION\.?\s*[—–-]*\s*B\s?y\s+a\s+gentleman'],
      definition=("Printings of a paragraph from the Scioto Gazette (Chillicothe, 13 November 1806) headed 'IMPORTANT COMMUNICATION': 'By a "
                  "gentleman of the highest respectability from Kentucky, we are furnished with the following intelligence'; the substance of an "
                  "affidavit of the United States attorney for Kentucky (printed 'Davies' or 'Daveiss') that Aaron Burr 'had formed an Association "
                  "for making war against Spain, invading Mexico, and forming a distinct Empire in the Western country'. An allegation, reported at second hand."),
      first="'IMPORTANT COMMUNICATION' from Chillicothe (13 November 1806): an affidavit in Kentucky against Aaron Burr.", what='the Chillicothe paragraph',
      printings=[k(NI, '11-24', 2), k(ADA, '11-24', 3), k(VA, '11-28', 2), k(EN, '11-28', 2), k(NG, '11-28', 2), (k(PGZ, '12-08', 2), dict(role='condensed_report', core=[r'C\s?HILLICOTHE,?\s+N\s?OV\.?\s+13,?\s+1806\.?\s+M\s?R\.?\s+B\s?URR'], note="A shorter version, headed 'CHILLICOTHE, NOV. 13, 1806. MR. BURR—AGAIN.', found by the loose search of papers without a printing.")), k(BJ, '12-05', 2), k(NHG, '12-09', 2), k(HUS, '12-13', 2)]),
 dict(id='proclamation-27-november-1806', parent='burr-enterprise-1806', kind='document_group', label="The President's proclamation of 27 November against a military expedition", role='published_document', words=55, dateline=False,
      core=[r'B\s?Y\s+THE\s+P\s?RESIDENT\s+OF\s+THE\s+U\w*\s+S\w*\s+OF\s+A\s?MERICA[,.]?\s+A\s+P\s?ROCLAMATION', r'A\s+P\s?ROCLAMATION\.?\s+W\s?HEREAS\s+information\s+has\s+been\s+received\s+that\s+sundry'],
      definition=("Printings of President Jefferson's proclamation of 27 November 1806: 'WHEREAS information has been received that sundry persons, "
                  "citizens of the United States, or residents within the same are conspiring and confederating together to begin and set on foot, "
                  "provide and prepare the means for a military expedition or enterprise against the dominions of Spain'; it warns citizens 'to "
                  "withdraw from the same without delay'. It names no one. An official document."),
      first="President Jefferson's proclamation of 27 November 1806 against 'a military expedition or enterprise against the dominions of Spain'.", what="the President's proclamation",
      printings=[k(NI, '11-28', 3), k(ADA, '11-29', 3), (k(NI, '12-01', 3), dict(note='Printed again.')), k(VA, '12-02', 3), k(EN, '12-02', 3), k(NG, '12-05', 2), k(LS, '12-11', 2), k(BJ, '12-12', 1), k(NHG, '12-16', 3), k(KG, '12-22', 2)]),
 dict(id='message-3-december-1806', parent='british-goods-resolutions-1806', kind='document_group', label="The President's message of 3 December on suspending the act", role='published_document', words=55, dateline=False,
      core=[TO_HOUSES + r'I\s?\s?HAVE\s+the\s+satisfaction\s+to\s+inform\s+you\s+that\s+the\s+\w+\s+depending'],
      definition=("Printings of President Jefferson's message to Congress of 3 December 1806: 'I have the satisfaction to inform you that the "
                  "negotiation depending between the United States and the government of Great Britain is proceeding in a spirit of friendship', "
                  "and that 'a temporary suspension of the act of last session, prohibiting certain importations, would, as a mark of candid "
                  "disposition on our part' help it. The executive's own account and request."),
      first="President Jefferson's message of 3 December 1806: the negotiation with Britain is proceeding, and the act prohibiting certain importations should be suspended.", what="the President's message",
      printings=[k(NI, '12-05', 3), k(ADA, '12-06', 3), k(VA, '12-09', 2), k(EN, '12-09', 3), k(NG, '12-10', 3), k(HUS, '12-13', 2), k(NHG, '12-16', 2), k(LS, '12-18', 2), k(KG, '12-29', 3)]),
 dict(id='annual-message-2-december-1806', kind='document_group', label="The President's annual message of 2 December 1806", role='published_document', words=55, dateline=False,
      core=[r'(?:T\s?O\s+the\s+S\s?enate\s+and\s+H\s?ouse\s+of\s+R\s?epresentatives\s+of\s+the\s+U\w*\s+S\w*\s+of\s+A\s?merica,?\s+in\s+C\s?ongress\s+[Aa]ssembled\.?\s+)?I\s?T\s+would\s+have\s+given\s+me,?\s+[Ff]ellow'],
      definition=("Printings of President Jefferson's annual message to Congress of 2 December 1806: 'It would have given me, fellow citizens, great "
                  "satisfaction to announce, in the moment of your meeting, that the difficulties in our foreign relations, existing at the time of "
                  "your last separation, had been amicably and justly terminated'. The executive's own account of the year."),
      first="President Jefferson's annual message of 2 December 1806 on 'the difficulties in our foreign relations'.", what="the President's message",
      printings=[k(NI, '12-02', 3), k(ADA, '12-03', 2), k(NG, '12-08', 2), k(VA, '12-09', 4), k(BJ, '12-12', 2), k(HUS, '12-13', 1), k(PGZ, '12-15', 1), k(NHG, '12-16', 1), k(LS, '12-18', 5), k(KG, '12-22', 2)]),
 dict(id='hague-17-october-war-france-prussia', kind='message_group', label='The Hague, 17 October 1806: war between France and Prussia', role='report', words=55,
      core=[r'L\s?AST\s+night\s+his\s+[Ee]xcellency\s+the\s+[Ss]ecretary\s+of\s+[Ss]tate\s+received'],
      definition=("Printings of a paragraph from Dutch papers (the Hague, 17 October 1806), translated in New York: 'Last night his excellency the "
                  "Secretary of State received the important intelligence, that hostilities have commenced between the French and Prussians'. A "
                  "first report of the war, through the Dutch papers."),
      first="The Hague, 17 October 1806: news 'that hostilities have commenced between the French and Prussians'.", what='the Hague paragraph',
      printings=[k(ADA, '12-13', 3), k(NI, '12-15', 1), k(NG, '12-15', 3), k(EN, '12-16', 3), k(VA, '12-19', 2), k(HUS, '12-20', 1), k(NHG, '12-23', 1), k(LS, '12-25', 2)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline or heading directly before the item, after a sentence boundary (as for 1776, 1807 and 1808): "NORFOLK, July 6."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*180[56])?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False):
    for core in cores:
        m = re.search(core, text, re.I)
        if m:
            start = m.start()
            if back:   # a quoted document: start at the beginning of the sentence that introduces it
                cuts = [(text.rfind(b, 0, start), len(b)) for b in ('. ', '.] ', '] ', '." ', '.” ', '? ')]
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
    stop: a regex; the excerpt ends before its first match (to end before private persons' names)."""
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
            problems.append((s['id'], key, 'page not in the 1806 pages'))
            continue
        text_fields = pages[key]['texts']
        cores = over.get('core', s['core'])
        if key in MISFILED:     # this page's RevX slot holds another scan page's text: read the CA text of the scan page
            fields = [CA]
        else:
            fields = [over['field']] if 'field' in over else [REVX, CA]
        for field in fields:
            text = text_fields.get(field) or ''
            start = item_start(text, cores, over.get('dateline', s.get('dateline', True)), over.get('back', False))
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
            note = (note+' ' if note else '') + ('The RevX transcriptions of this issue are filed one page off from the scans, so the excerpt '
                                                 'comes from the older CA transcription of this scan page.')
        elif field == CA and 'field' not in over:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'printed': pages[key]['date'], 'field': field, 'excerpt_start': first, 'excerpt_end': last,
                     'excerpt': excerpt, 'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['printed'], r['page_key'], r['story']))
    for n, r in enumerate(rows, 1):
        r['id'] = f'S06-{n:03}'
    return rows, problems


def build(rows, review):
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
               'admission_rule': 'Reviewed 1806 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    return {
        'ledger_id': 'ledger:stories-1806', 'ledger_version': 1, 'base_release': BASE, 'target_release': TARGET,
        'recorded_date': '2026-11-12', 'namespace': 'expansion-1806', 'evidence_dir': 'outputs/story_discovery_1806/evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1806, and of 1805 where they reach the 1806 pages (long-running ones '
                   'included), phrase searches on all 4,381 pages of 1806 in both transcriptions, reading of every hit, and scan checks of each '
                   'admitted passage'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             'outputs/story_discovery_1806/items.json': 'retrieval_candidates', 'outputs/story_discovery_1806/items_from_1805.json': 'retrieval_candidates',
                             'outputs/story_discovery_1806/phrase_patterns.json': 'retrieval_patterns', 'outputs/story_discovery_1806/phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1806.py': 'ledger_code', 'work/archive_data/ledgers/stories_1806_review.json': 'scan_review',
                             'outputs/story_discovery_1806/SCAN_PROTOCOL.md': 'review_protocol', 'outputs/story_discovery_1806/scan_points.json': 'review_protocol'},
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
            print(f"{r['id']} {r['story'][:26]:26} {r['page_key']:30} {r['field'][:4]} {r['roles'][0][:9]:9} | {r['excerpt'][:110]} … {r['excerpt'][-50:]}")
    review = json.loads(REVIEW.read_text(encoding='utf8')) if REVIEW.exists() else {}
    if problems and '--force' not in sys.argv:
        raise SystemExit(f'{len(problems)} printings without anchors')
    OUT.write_text(json.dumps(build(rows, review), ensure_ascii=False, indent=2), encoding='utf8')
    print('wrote', OUT, len(rows), 'observations,', len(STORIES), 'groups')
