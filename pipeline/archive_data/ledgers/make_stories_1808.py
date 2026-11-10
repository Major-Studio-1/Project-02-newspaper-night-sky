"""Write ledgers/stories_1808.json (v0.8.1 -> v0.9.0): reviewed stories of 1808, the fourth reviewed year.

The stories were chosen as for 1776 and 1807 (make_stories_1776.py, make_stories_1807.py): the automatic families were
split into single printed items with work/story_items.py, run with --long-running, every item printed in 7 or more
newspapers was read, and the chosen items were confirmed with phrase searches over all 4,466 pages of 1808 in both
transcriptions (work/story_phrase_search.py). story_items.py takes the families first printed in its year, so it was run
twice over the 1808 pages: with year 1808 (items.json) and with year 1807 (items_from_1807.json), because several of
the year's most printed documents (the Embargo Act's supplements, the papers on the Chesapeake negotiations that Congress
published in March) sit in families that began in 1807. See outputs/story_discovery_1808/README.md.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as
apply_ledger.py does: the excerpt is the opening of the printed item (about 40-60 words), starting with its
dateline or heading when one stands directly before it. Scan findings, crops and hand-drawn boxes are merged from
stories_1808_review.json after the scan check.

Nine 1808 issues have their RevX transcriptions filed one page off from the scans (derived/revx_page_map.parquet in
the base release, from outputs/revx_page_shift_check/). A printing on a page whose RevX slot holds another page's text
names the scan page and takes its excerpt from the CA transcription of that page, which is numbered as the scans are.

Run from the project root with Python 3.12 (needs outputs/story_discovery_1808/search_pages.json, made by
work/year_search_pages.py):
    python work/archive_data/ledgers/make_stories_1808.py [--table]
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PAGES = PROJECT/'outputs/story_discovery_1808/search_pages.json'
REVIEW = HERE/'stories_1808_review.json'
OUT = HERE/'stories_1808.json'
BASE = '0.8.1'
RELEASE = PROJECT/f'outputs/data_foundation/v{BASE}'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

NI, NG, ADA, ADG, EN, VA = 'sn83045242', 'sn85025815', 'sn84024012', 'sn84024013', 'sn84024736', 'sn84024710'
KG, PGZ, NHG, BJ, WR = 'sn84038147', 'sn83016082', 'sn83025588', 'sn85059525', 'sn86092519'
PAPER = {NI: 'The National Intelligencer', NG: 'The Norfolk Gazette and Publick Ledger', ADA: 'The Alexandria Daily Advertiser',
         ADG: 'The Alexandria Daily Gazette', EN: 'The Enquirer', VA: 'The Virginia Argus', KG: 'The Kentucky Gazette',
         PGZ: 'The Portland Gazette', NHG: 'The New Hampshire Gazette', BJ: 'The Berkeley and Jefferson Intelligencer',
         WR: 'The Wheeling Repository'}
k = lambda paper, date, page, ed=1: f'{paper}|1808-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text (shifted, two pages off or repeated), from the base release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith('1808')}


MISFILED = misfiled()

# Story groups, as for 1776 and 1807. 'printings' lists each printing's page; a tuple adds overrides for that printing:
# core (regexes for the item's first words), role, field, note, words, dateline (include a dateline or heading directly
# before), back (start at the beginning of the sentence that holds the core, for quoted documents).
ACT = r'A\s?N\s+A\s?CT,?\s+'
TO_HOUSES = r'(?:T\s?O\s+THE\s+S\s?ENATE,?\s+AND\s+H\s?OUSE\s+OF\s+R\s?EPRESENTATIVES,?(?:\s+OF\s+THE\s+U[\w.]*\s?S\w*[.,]?)?["”]?\s+)?'
STORIES = [
 # --- The embargo laws ------------------------------------------------------------------------------------------------
 dict(id='embargo-laws', kind='context_group', label='The embargo laws',
      definition=("The Embargo Act of 22 December 1807 and the acts of the first session of the Tenth Congress that extended it, enforced it "
                  "and allowed the President to suspend it, as the 1808 papers printed them, most of them 'by authority': the supplementary act of "
                  "9 January, the additional act of 12 March, the act of 22 April authorising a suspension and the act of 25 April. Contains those "
                  "five groups. Only 1808 printings are included; the Embargo Act was first printed in December 1807."),
      children=['embargo-act-22-dec-1807', 'embargo-supplementary-act-9-jan', 'embargo-additional-act-12-march', 'embargo-suspension-act-22-april', 'embargo-act-25-april']),
 dict(id='embargo-act-22-dec-1807', parent='embargo-laws', kind='document_group', label='The Embargo Act of 22 December 1807', role='published_document', words=55, dateline=False,
      core=[ACT + r'[Ll]aying\s+an\s+E\s?MBARGO\s+on\s+all\s+S\s?hips.{0,260}?That\s+an\s+E\s?MBARGO\s+be'],
      definition=("Printings of the act of 22 December 1807 laying an embargo on all ships and vessels in the ports and harbors of the United "
                  "States: no clearance for a foreign port, and bonds for coasting vessels. This group holds the act's 1808 printings; it was first "
                  "printed in late December 1807, and those printings are not included."),
      first="The Embargo Act of 22 December 1807 in a January printing: no ship or vessel in American ports may clear for a foreign port.", what='the Embargo Act',
      printings=[k(BJ, '01-01', 2), k(PGZ, '01-04', 2), (k(NHG, '01-05', 2), dict(note='The paper had printed the act in December 1807; this is its printing among the laws of the session.')),
                 k(WR, '01-07', 5), (k(VA, '01-15', 3), dict(note="Printed again 'By authority'; the paper had printed the act in December 1807."))]),
 dict(id='embargo-supplementary-act-9-jan', parent='embargo-laws', kind='document_group', label='The supplementary act of 9 January', role='published_document', words=55, dateline=False,
      core=[ACT + r'S\s?upplementary\s+to\s+(?:the|an)\s+act.{0,320}?licensed\s+for\s+the\s+coasting\s+trade',
            r'The\s+following\s+act,?\s+supplementary\s+to\s+the\s+act'],
      definition=("Printings of the act of 9 January 1808 supplementary to the Embargo Act: vessels licensed for the coasting trade, and fishing "
                  "and whaling vessels, may not depart without bond that they will not go to a foreign port, with penalties for evading the embargo."),
      first="The act of 9 January 1808 supplementary to the Embargo Act: coasting vessels may not depart without bond.", what='the supplementary act',
      printings=[(k(ADA, '01-09', 3), dict(note="Printed as the act that 'passed the Senate yesterday, the 5th', with the bill's wording 'coasting trade or fisheries'.")),
                 k(NI, '01-11', 3), k(NG, '01-15', 3), k(VA, '01-22', 1), k(PGZ, '02-01', 1), k(NHG, '02-09', 1)]),
 dict(id='embargo-additional-act-12-march', parent='embargo-laws', kind='document_group', label='The additional act of 12 March', role='published_document', words=55, dateline=False,
      core=[ACT + r'I\s?n\s+addition\s+to\s+the\s+act,?\s+entitled.{0,60}?supplementary.{0,800}?neither\s+registered'],
      definition=("Printings of the act of 12 March 1808 in addition to the supplementary act: no boat that is neither registered nor licensed, "
                  "and no foreign vessel, may depart, and goods may not be exported from the United States by land or by water."),
      first="The act of 12 March 1808: unregistered boats and foreign vessels may not depart, and goods may not be exported by land or water.", what='the act of 12 March',
      printings=[k(NI, '03-18', 4), k(NG, '03-18', 2), k(PGZ, '03-28', 1), k(NHG, '04-05', 1), k(VA, '04-12', 1)]),
 dict(id='embargo-suspension-act-22-april', parent='embargo-laws', kind='document_group', label='The act allowing the President to suspend the embargo', role='published_document', words=55, dateline=False,
      core=[ACT + r'T\s?o\s+authori[sz]e\s+the\s+[Pp]resident\s+of\s+the\s+United\s+States,?\s+under\s+certain\s+conditions'],
      definition=("Printings of the act of 22 April 1808 authorising the President, during the recess of Congress, to suspend the embargo in "
                  "whole or in part if peace, a suspension of hostilities or changes in the belligerents' measures made American commerce "
                  "sufficiently safe."),
      first="The act of 22 April 1808: the President may suspend the embargo in the recess if peace or changed measures make commerce safe.", what='the act',
      printings=[k(ADA, '04-22', 3), k(NI, '04-27', 1), k(BJ, '04-29', 3),
                 (k(WR, '05-05', 4), dict(core=[r'a\s+message\s+was\s+received\s+from\s+the\s+senate,?\s+announcing\s+that\s+they\s+had\s+passed\s+a\s+bill\s+authori[sz]ing'],
                                          role='quoted_document', words=70, note="Printed in the House proceedings: the bill as the Senate had passed it, with the act's enacting text.")),
                 k(VA, '05-20', 1), k(EN, '06-17', 4), k(NHG, '08-23', 1)]),
 dict(id='embargo-act-25-april', parent='embargo-laws', kind='document_group', label='The act of 25 April enforcing the embargo', role='published_document', words=55, dateline=False,
      core=[ACT + r'I\s?n\s+addition\s+to\s+the\s+act,?\s+entitled,?\s+.{0,3}An\s+act\s+laying\s+an\s+embargo.{0,500}?navigation\s+of\s+bays',
            r'Extracts\s+from\s+an\s+act,?\s+entitled.{0,500}?navigation\s+of\s+bays'],
      definition=("Printings of the act of 25 April 1808 in addition to the embargo acts: vessels whose trade is confined to bays, sounds, "
                  "rivers and lakes must give bond, and collectors may detain vessels and unusual deposits of goods suspected of evading the embargo."),
      first="The act of 25 April 1808 tightens the embargo: bonds for vessels on bays and rivers, and powers for collectors to detain.", what='the act of 25 April',
      printings=[k(NI, '05-02', 1),
                 (k(ADA, '05-10', 3), dict(core=[r'I\s?MPORTANT\s+I\s?NFORMATION\s+To\s+Captains\s+of\s+Coasting\s+Vessels'], role='document_excerpt', note="Printed as extracts from the act under the heading 'IMPORTANT INFORMATION To Captains of Coasting Vessels.'")),
                 k(VA, '05-10', 1), k(NG, '05-18', 1), k(EN, '05-19', 4), k(NHG, '06-21', 1)]),
 # --- Charges against General Wilkinson --------------------------------------------------------------------------------
 dict(id='wilkinson-accused', kind='context_group', label='Charges against General Wilkinson, 1808',
      definition=("Documents and reports of the charges that General James Wilkinson had taken money from the Spanish government, as the 1808 "
                  "papers printed them: his challenge to John Randolph and Randolph's answer (December 1807), Daniel Clark's statement to the "
                  "House, the President's message of 20 January, and the opinion of the military court of inquiry (printed from 4 July). "
                  "Contains those four groups. The statement and the letters are allegations and each writer's own account; the court found no evidence."),
      children=['wilkinson-randolph-letters', 'clark-statement-on-wilkinson', 'president-message-20-jan-wilkinson', 'wilkinson-court-of-inquiry']),
 dict(id='wilkinson-randolph-letters', parent='wilkinson-accused', kind='message_group', label="Wilkinson's challenge and Randolph's answer", role='report', words=50,
      core=[r'S\s?IR\W+I\s+understand\s+several\s+expressions'],
      definition=("Printings of two letters of 24 and 25 December 1807, from a pamphlet: General James Wilkinson asks John Randolph, a member "
                  "of the House, for satisfaction for words injurious to his reputation, and Randolph refuses. Each letter is its writer's own account."),
      first="General Wilkinson writes to John Randolph (24 December 1807) that 'several expressions have escaped you' injurious to his reputation; Randolph refuses him.", what='the letters',
      printings=[k(ADA, '01-05', 3), k(EN, '01-07', 3), k(VA, '01-08', 3), k(NG, '01-11', 2), k(BJ, '01-15', 2), k(PGZ, '01-18', 2), k(WR, '01-21', 5)]),
 dict(id='clark-statement-on-wilkinson', parent='wilkinson-accused', kind='message_group', label="Daniel Clark's statement to the House", role='report', words=55,
      core=[r"M\s?R\.?\s+C\s?LARKE?.?S\s+S\s?TATEMENT", r'S\s?TATEMENT\s+OF\s+D\s?ANIEL\s+C\s?LARK',
            r'In\s+obedience\s+to\s+the\s+direction\s+of\s+the\s+[Hh]ouse\s+of\s+[Rr]epresentatives', r'I\s+arrived\s+from\s+Europe\s+at\s+New.?Orleans'],
      definition=("Printings of the statement of Daniel Clark, delegate from the Territory of Orleans, laid before the House on 11 January 1808 and "
                  "sworn before Judge Cranch: that General Wilkinson had dealings with the Spanish government and received money from it. It is an allegation."),
      first="Daniel Clark's statement to the House (11 January 1808) alleges that General Wilkinson took money from the Spanish government.", what="Clark's statement",
      printings=[k(NI, '01-15', 2), k(ADA, '01-18', 2), k(EN, '01-21', 2), k(VA, '01-22', 1), k(NG, '01-22', 3), k(BJ, '01-29', 1), k(PGZ, '02-01', 1), k(WR, '02-04', 3)]),
 dict(id='president-message-20-jan-wilkinson', parent='wilkinson-accused', kind='document_group', label="The President's message of 20 January on Wilkinson", role='published_document', words=55, dateline=False,
      core=[r'(?:T\s?O\s+THE\s+H\s?OUSE\s+OF\s+R\s?EPRESENTATIVES(?:\s+OF\s+THE\s+U[\w.]*\s?S\w*)?[.,]?\s+)?S\s?OME\s+days\s+previous\s+to\s+your\s+resolutions?\s+of\s+the\s+(?:thirteenth|13th)'],
      definition=("Printings of President Jefferson's message to the House of 20 January 1808, answering its resolutions of 13 January on General "
                  "Wilkinson: a court of inquiry, asked for by Wilkinson, was already sitting, and he reported what the executive's records held on "
                  "foreign intrigues and on any corrupt receipt of money by an officer of the United States."),
      first="President Jefferson answers the House on 20 January 1808: a court of inquiry into General Wilkinson's conduct is already sitting.", what="the President's message",
      printings=[k(NI, '01-25', 1), k(ADA, '01-26', 2), k(EN, '01-28', 1), k(VA, '01-29', 1), k(NG, '02-02', 2), k(BJ, '02-05', 2), k(NHG, '02-09', 2)]),
 dict(id='wilkinson-court-of-inquiry', parent='wilkinson-accused', kind='document_group', label="The court of inquiry's opinion on Wilkinson", role='published_document', words=55,
      core=[r'After\s+a\s+full\s+investigation\s+of\s+such\s+evidence'],
      definition=("Printings of the opinion of the military court of inquiry at Washington on General Wilkinson (signed by its president, Colonel "
                  "Burbeck, and approved by the President), printed from 4 July 1808: it found no evidence that Wilkinson had received a pension or "
                  "money from the Spanish government for corrupt purposes."),
      first="The court of inquiry finds no evidence that General Wilkinson received a pension or corrupt money from Spain (Washington, 4 July 1808).", what="the court's opinion",
      printings=[k(NI, '07-04', 3), k(ADA, '07-05', 3), k(VA, '07-08', 3), k(EN, '07-08', 2), k(NG, '07-08', 3), k(BJ, '07-08', 2),
                 (k(NHG, '07-12', 3), dict(core=[r'Acquittal\s+of\s+Gen\w*\.?\s+Wilkinson'], role='document_excerpt', words=70,
                                           note="A Boston paragraph that quotes the court's conclusion."))]),
 # --- Orders and decrees against neutral trade -------------------------------------------------------------------------
 dict(id='decrees-on-neutral-trade', kind='context_group', label='Orders and decrees against neutral trade',
      definition=("Three measures of the warring powers against neutral commerce, as American papers printed them in the first half of 1808: "
                  "the British Order in Council of 11 November 1807, a merchant house's account of Napoleon's Milan decree, and the British "
                  "instructions of 11 April 1808 on provisions for the West Indies. Contains those three groups; the grouping is by subject."),
      children=['orders-in-council-11-nov-1807', 'amsterdam-letter-milan-decree', 'british-instructions-11-april']),
 dict(id='orders-in-council-11-nov-1807', parent='decrees-on-neutral-trade', kind='document_group', label='The British Order in Council of 11 November 1807', role='published_document', words=55, dateline=False,
      core=[r'A\s?T\s+the\s+[Cc]ourt,?\s+at\s+the\s+Q\s?ueen.?s\s+[Pp]alace,?\s+the\s+1[14]th\s+(?:of\s+|day\s+of\s+)?N\s?ov'],
      definition=("Printings of the order of the King in Council of 11 November 1807 that put the ports of France and her allies, and every port "
                  "from which the British flag was excluded, under the restrictions of a blockade, as retaliation for the French decrees."),
      first="Britain's Order in Council of 11 November 1807 puts the ports of France, her allies and every port closed to the British flag under the rules of a blockade.", what='the Order in Council',
      printings=[k(NI, '01-22', 3), k(ADA, '01-23', 2), k(NG, '01-25', 2), k(EN, '01-26', 2), k(NHG, '01-26', 2), k(VA, '01-26', 4)]),
 dict(id='amsterdam-letter-milan-decree', parent='decrees-on-neutral-trade', kind='message_group', label='An Amsterdam letter on the Milan decree', role='report', words=55,
      core=[r'The\s+following\s+important\s+extract\s+of\s+a\s+letter\s+from\s+Dan', r'A\s+mercantile\s+friend\s+has\s+obligingly\s+favou?red\s+us',
            r'A\s?MSTERDAM,?\s+Dec\w*\.?,?\s+30'],
      definition=("Printings of an extract of a letter from Daniel Crommelin and Sons, Amsterdam, 30 December 1807, received at New York on 13 "
                  "February 1808: official news of a decree of the French Emperor at Milan under which vessels that had submitted to British search "
                  "or paid duties in Britain were to be treated as denationalised. It is a merchant house's summary, not the decree."),
      first="A letter from Daniel Crommelin and Sons, Amsterdam, 30 December 1807, reports Napoleon's decree from Milan against vessels that submit to Britain.", what='the Amsterdam letter',
      printings=[k(NG, '02-17', 3), k(NI, '02-19', 2), k(ADA, '02-20', 3), k(PGZ, '02-22', 2), k(NHG, '02-23', 3), k(VA, '02-23', 2), k(EN, '02-23', 2), k(BJ, '02-26', 2)]),
 dict(id='british-instructions-11-april', parent='decrees-on-neutral-trade', kind='document_group', label='British instructions of 11 April on provisions for the colonies', role='published_document', words=55, dateline=False,
      core=[r'G\s?EORGE\s+[RB]\.?\W+I\s?nstructions\s+to\s+the\s+[Cc]ommanders\s+of\s+our\s+[Ss]hips'],
      definition=("Printings of the King's instructions to the commanders of British ships of war and privateers (Windsor, 11 April 1808): they "
                  "were not to interrupt neutral vessels laden with lumber and provisions bound to the British colonies, under the conditions the "
                  "instructions set."),
      first="Britain's instructions of 11 April 1808: neutral vessels carrying lumber and provisions to the British colonies are not to be interrupted.", what='the instructions',
      printings=[k(ADA, '05-27', 3), k(PGZ, '05-30', 2), k(NI, '05-30', 3), k(NHG, '05-31', 2), k(VA, '05-31', 2), k(EN, '05-31', 3), k(NG, '06-01', 2),
                 (k(ADA, '06-28', 3), dict(note='Printed again a month after its first printing in this paper.'))]),
 # --- Algiers ----------------------------------------------------------------------------------------------------------
 dict(id='algiers-1808', kind='context_group', label='Algiers and the American ships, 1808',
      definition=("A New Bedford report of February 1808 that Algiers had declared war on the United States, the American consul general's "
                  "circular of the same weeks that the dispute was settled, and a June report of the Dey's new demands. Contains those three groups."),
      children=['algiers-war-report', 'lear-circular-peace-with-algiers', 'dey-of-algiers-june']),
 dict(id='algiers-war-report', parent='algiers-1808', kind='message_group', label="New Bedford: 'War with Algiers'", role='report', words=55,
      core=[r'W\s?AR\s+WITH\s+A\s?LGIERS\W+Arrived', r'Arrived,?\s+(?:this\s+evening|at\s+New.?Bedford),?\s+(?:the\s+)?(?:fast\s+sailing\s+)?ship\s+Hone'],
      definition=("Printings of a New Bedford handbill of 30 January 1808: the ship Honestus, 42 days from the Downs, had been told off Cape "
                  "Trafalgar that Algiers had declared war against America and captured American vessels. It is a report; the consul general's "
                  "circular, printed in the same weeks, says the dispute had been settled."),
      first="New Bedford, 30 January 1808: the ship Honestus brings word that Algiers has declared war on the United States.", what='the New Bedford report',
      printings=[k(PGZ, '02-08', 2), k(NHG, '02-09', 2), k(NG, '02-10', 2), k(NI, '02-10', 3), k(ADA, '02-12', 2), k(VA, '02-12', 2), k(EN, '02-13', 1)]),
 dict(id='lear-circular-peace-with-algiers', parent='algiers-1808', kind='message_group', label="Lear's circular: peace with Algiers", role='report', words=55,
      core=[r'S\s?IR\W+Y\s?OU\s+have\s+undoubtedly'],
      definition=("Printings of the circular of Tobias Lear, American consul general at Algiers (16 December 1807), received at Salem in February "
                  "1808: three American vessels detained by an Algerine frigate, because the annuities were two years in arrears, had been released "
                  "after he settled with the Dey."),
      first="Tobias Lear writes from Algiers (16 December 1807) that the three detained American vessels are released and the dispute settled.", what="Lear's circular",
      printings=[k(PGZ, '02-08', 3), k(NHG, '02-09', 3), k(NI, '02-15', 2), k(ADA, '02-16', 2), k(NG, '02-17', 3),
                 (k(EN, '02-19', 2), dict(field=CA, core=[r'C\s?IRCULAR\.?\s+\(C\s?OPY\.?\)\s+ALG'], dateline=False)), k(VA, '02-23', 1), k(WR, '03-03', 6)]),
 dict(id='dey-of-algiers-june', parent='algiers-1808', kind='message_group', label='Washington: the Dey of Algiers makes new demands', role='report', words=55,
      core=[r'We\s+understand\s+that\s+the\s+Dey\s+of\s+Algiers'],
      definition=("Printings of a National Intelligencer paragraph of 24 June 1808 ('We understand'): after the settlement of December, the Dey had "
                  "demanded in March two thousand dollars a man for Algerine seamen lost in the rescue of a captured American vessel, threatening "
                  "to put Consul Lear in chains. It is a report from the government's paper."),
      first="Washington, 24 June 1808: the Dey of Algiers is reported to have demanded money of Consul Lear, threatening him with chains.", what='the report',
      printings=[k(NI, '06-24', 3), k(ADA, '06-25', 3), k(VA, '06-28', 3), k(EN, '06-28', 3), k(NG, '06-29', 3), k(BJ, '07-01', 2), k(PGZ, '07-04', 2), k(NHG, '07-05', 3)]),
 # --- More troops ------------------------------------------------------------------------------------------------------
 dict(id='president-message-25-feb-military-force', kind='document_group', label="The President's message on more troops, February 1808", role='published_document', words=55, dateline=False,
      core=[TO_HOUSES + r'T\s?HE\s+dangers?\s+(?:to|of)\s+our\s+country,?\s+arising'],
      definition=("Printings of President Jefferson's message to Congress of February 1808 (communicated on 26 February) recommending an increase "
                  "of the military force, regular and volunteer, with the Secretary of War's letter proposing new regiments; the message and the "
                  "letter are one publication, counted once."),
      first="President Jefferson asks Congress in February 1808 for a larger military force, regular and volunteer.", what="the President's message",
      printings=[k(NI, '02-29', 3), k(ADA, '02-29', 3), k(BJ, '03-04', 2), k(EN, '03-04', 2), k(NG, '03-04', 2), k(VA, '03-04', 2), k(NHG, '03-08', 3), k(PGZ, '03-14', 2), k(WR, '03-17', 5)]),
 # --- Lisbon under the French ------------------------------------------------------------------------------------------
 dict(id='latest-from-portugal-dec-1807', kind='message_group', label='Lisbon under the French, December 1807', role='report', words=55,
      core=[r'(?:L\s?ATEST\s+FROM\s+P\s?ORTUGAL\.?\s+)?By\s+the\s+(?:arrival,?\s+at\s+the\s+Vineyard,?\s+of\s+the\s+)?brig\s+Perseverance'],
      definition=("Printings of news from Lisbon papers of December 1807, brought by the brig Perseverance: decrees of the French general in chief "
                  "after the occupation, forbidding the use of arms to all but the military, confiscating English property and making French and "
                  "Spanish money current."),
      first="News from Lisbon by the brig Perseverance: under the French general, the use of arms is forbidden and English property confiscated (December 1807).", what='the Lisbon news',
      printings=[k(PGZ, '02-29', 2), k(ADA, '03-03', 3), k(NI, '03-04', 3), k(NG, '03-04', 2), k(EN, '03-08', 1),
                 (k(WR, '03-10', 6), dict(core=[r'L\s?ISBON,?\s+Dec\w*\.?\s+4\.?\s+A\s+proclamation\s+was\s+this\s+day\s+made'], dateline=False,
                                          note='Prints the Lisbon extracts without the Boston introduction.')),
                 k(BJ, '03-11', 2)]),
 # --- The British and French papers laid before Congress ---------------------------------------------------------------
 dict(id='papers-before-congress-march-1808', kind='context_group', label='The British and French papers laid before Congress, 1808',
      definition=("The President's message of 22 March 1808 and the correspondence with Britain and France it laid before Congress, as the papers "
                  "printed it from March to May: Canning and Monroe on the Chesapeake (No. II), the letters of George Rose and James Madison on "
                  "Rose's mission (No. III), and Champagny's letter to Armstrong of 15 January, made public on 2 April. Contains those four groups."),
      children=['president-message-22-march', 'canning-monroe-chesapeake-correspondence', 'rose-madison-letters', 'champagny-letter-15-jan']),
 dict(id='president-message-22-march', parent='papers-before-congress-march-1808', kind='document_group', label="The President's message of 22 March", role='published_document', words=55, dateline=False,
      core=[TO_HOUSES + r'A\s?T\s+the\s+opening\s+of\s+the\s+present\s+session'],
      definition=("Printings of President Jefferson's message of 22 March 1808 laying before Congress the correspondence with Britain on the "
                  "Chesapeake, the unratified treaty and Rose's mission, and with France."),
      first="President Jefferson's message of 22 March 1808 lays the correspondence with Britain and France before Congress.", what="the President's message",
      printings=[k(NI, '03-25', 2),
                 (k(ADA, '03-25', 3), dict(core=[r'A\s?T\s+\S+(?:\s+\S+)?\s+of\s+the\s+present\s+session'],
                                          note="Found on the scan page whose own text survives only in the older CA transcription, which is badly garbled here.")),
                 k(EN, '03-29', 3), k(VA, '03-29', 2), k(NG, '04-01', 1), k(BJ, '04-01', 5), k(NHG, '04-05', 3), k(WR, '04-07', 6)]),
 dict(id='canning-monroe-chesapeake-correspondence', parent='papers-before-congress-march-1808', kind='document_group', label='Canning and Monroe on the Chesapeake', role='published_document', words=55, dateline=False,
      core=[r'(?:\(\s?P\s?RIVATE\.?\s?\)\.?\s+)?(?:F\s?OREIGN\s+O\s?FFICE[.,]?\s+)?(?:S\s?ATURDAY,?\s+)?(?:July\s+25,?\s+1807\.?\s+)?M\s?r\.?\s+C\s?anning\s+presents\s+his\s+compliments\s+to\s+M\s?r\.?\s+M[ou]n?roe'],
      definition=("Printings of the correspondence between George Canning and James Monroe on the attack on the Chesapeake, with Monroe's letters "
                  "to the Secretary of State (No. II of the papers laid before Congress), counted by its first document, Canning's note of 25 July "
                  "1807 on the first news of the attack."),
      first="Canning's note to Monroe of 25 July 1807 on the first news of the Chesapeake, printed with the papers laid before Congress.", what='the correspondence',
      printings=[k(NI, '03-25', 2), k(ADA, '03-26', 2), k(VA, '03-29', 3), k(EN, '04-01', 1), k(NG, '04-01', 1), k(PGZ, '04-11', 1), k(NHG, '04-12', 2), k(WR, '04-14', 4)]),
 dict(id='rose-madison-letters', parent='papers-before-congress-march-1808', kind='document_group', label="Rose and Madison on Rose's mission", role='published_document', words=55, dateline=False,
      core=[r'(?:W\s?ASHINGTON,?\s+Jan\w*\.?,?\s+26(?:th)?,?\s+1808\.?\s+)?S\s?IR\W+H\s?AVING\s+had\s+the\s+hono\w*\s+to\s+state\s+to\s+you'],
      definition=("Printings of the correspondence between George Rose, the British envoy, and James Madison, Secretary of State (No. III of the "
                  "papers laid before Congress), counted by its first letter: Rose's of 26 January 1808, that his instructions forbade any "
                  "negotiation while the President's proclamation of 2 July 1807 remained in force; with Madison's answer of 5 March and Rose's "
                  "reply of 17 March."),
      first="George Rose writes to Madison (26 January 1808) that he may not negotiate on the Chesapeake while the proclamation of 2 July stands.", what='the correspondence',
      printings=[k(NI, '03-30', 1), k(ADA, '04-01', 2), k(EN, '04-05', 2), k(VA, '04-05', 1), k(NG, '04-07', 1), k(PGZ, '04-11', 2),
                 (k(BJ, '04-29', 1), dict(note="Madison's answer of 5 March follows Rose's letter on the same page.")),
                 k(NHG, '05-03', 1)]),
 dict(id='champagny-letter-15-jan', parent='papers-before-congress-march-1808', kind='document_group', label='Champagny to Armstrong, 15 January 1808', role='published_document', words=55, dateline=False,
      core=[r'(?:Translation\s+of\s+a\s+letter|(?:E\s?XTRAORDINARY\s+)?L\s?ETTER,?)\s+(?:F\s?rom\s+)?M[r.]*\.?\s+C\s?HAMPAGNY,?\s+to\s+(?:M\s?r\.?|G\s?en\w*\.?)\s+A\s?RMSTRONG,?\s+[Dd]ated', r'S\s?IR\W+T\s?HE\s+different\s+notes,?\s+which\s+you\s+have\s+done\s+me'],
      definition=("Printings of the letter of the French foreign minister, Champagny, to General Armstrong, the American minister (Paris, 15 "
                  "January 1808), made public by Congress on 2 April: the Emperor considered war as existing between England and the United "
                  "States from the day England published her decrees, and had 'no doubt of a declaration of war against her by the United States'. "
                  "It is France's own document."),
      first="Champagny writes to Armstrong (15 January 1808) that the Emperor has 'no doubt of a declaration of war' by the United States against England.", what="Champagny's letter",
      printings=[k(NI, '04-04', 3), k(NG, '04-07', 3), k(BJ, '04-08', 2), k(EN, '04-08', 2), k(VA, '04-08', 2), k(NHG, '04-12', 3), k(PGZ, '04-18', 3), k(WR, '04-21', 5)]),
 # --- The embargo at home, spring 1808 ---------------------------------------------------------------------------------
 dict(id='embargo-in-force-spring-1808', kind='context_group', label='The embargo at home, spring 1808',
      definition=("Reports and executive documents on the embargo's working in April and May 1808: a Georgia letter on its effect at Mobile and "
                  "Pensacola, the President's proclamation on Lake Champlain, and his letter to five governors on supplies of flour. Contains those "
                  "three groups; the grouping is by subject."),
      children=['georgia-letter-mobile-pensacola', 'proclamation-lake-champlain', 'president-circular-governors-6-may']),
 dict(id='georgia-letter-mobile-pensacola', parent='embargo-in-force-spring-1808', kind='message_group', label='A Georgia letter: Mobile and Pensacola', role='report', words=55,
      core=[r'Ex[\w\-]*(?:\s+of)?\s+a\s+letter\s+from\s+a\s+gentleman\s+in\s+Georgia'],
      definition=("Printings of an extract of a letter from a gentleman in Georgia (14 March 1808): the embargo had left the citizens of Mobile "
                  "and Pensacola 'almost in a state of starvation', with the prices of corn and flour there. It is one unnamed correspondent's report."),
      first="A letter from Georgia (14 March 1808): the embargo has left Mobile and Pensacola 'almost in a state of starvation'.", what='the Georgia letter',
      printings=[k(NI, '04-20', 3), k(ADA, '04-20', 3), k(NG, '04-25', 3), k(VA, '04-26', 4), k(BJ, '04-29', 3), k(PGZ, '05-02', 3), k(NHG, '05-03', 3), k(WR, '05-05', 7)]),
 dict(id='proclamation-lake-champlain', parent='embargo-in-force-spring-1808', kind='document_group', label="The President's proclamation on Lake Champlain", role='published_document', words=55, dateline=False,
      core=[r'(?:B\s?Y\s+THE\s+P\s?RESIDENT\s+OF\s+THE\s+U\w*\.?\s+S\w*\.?\s+(?:OF\s+A\s?MERICA\.?\s+)?)?(?:A\s+P\s?ROCLAMATION\.?\s+)?W\s?HEREAS\s+information\s+has\s+been\s+received\s+that\s+sundry\s+persons'],
      definition=("Printings of President Jefferson's proclamation of 19 April 1808: persons on Lake Champlain and the adjacent country were "
                  "combining to obstruct the embargo laws, too strong for the ordinary course of justice, and were commanded to disperse. It "
                  "alleges insurrection; several papers printed it from the Rutland Herald of 30 April."),
      first="President Jefferson's proclamation of 19 April 1808 orders those combining on Lake Champlain against the embargo laws to disperse.", what='the proclamation',
      printings=[k(NI, '05-13', 3), k(ADA, '05-13', 3), k(PGZ, '05-16', 2), k(NHG, '05-17', 2),
                 (k(EN, '05-17', 3), dict(field=CA, core=[r'A\s+P\s?ROCLAMATION\.?\s+W\S{3,7}\s+information\s+has\s+been\s+received,?\s+that\s+sundry'])),
                 k(VA, '05-17', 4), k(NG, '05-18', 2)]),
 dict(id='president-circular-governors-6-may', parent='embargo-in-force-spring-1808', kind='document_group', label="The President's letter to the governors on flour", role='published_document', words=55,
      core=[r'T\s?O\s+THE\s+G\s?OVERNORS\s+OF\s+O\s?RLEANS', r'["“]?(?:S\s?IR\W+)?["“]?T\s?HE\s+evasions\s+of\s+the\s+preceding\s+[Ee]mbargo'],
      definition=("Printings of President Jefferson's letter of 6 May 1808 to the governors of Orleans, Georgia, South Carolina, Massachusetts and "
                  "New Hampshire: since shipments of flour had become generally suspicious, the governors might certify merchants they trusted to "
                  "bring in flour for the needs of their states."),
      first="President Jefferson writes to five governors (6 May 1808) that they may certify trusted merchants to bring in flour.", what="the President's letter",
      printings=[(k(EN, '05-14', 3), dict(core=[r'We\s+understand\s+that\s+the\s+President\s+of\s+the\s+U'], role='quoted_document', words=70,
                                          note="The paper's own paragraph, which quotes the letter's opening sentences.")),
                 k(NI, '05-20', 3), k(ADA, '05-20', 2), k(PGZ, '05-23', 1), k(NG, '05-23', 2), k(NHG, '05-24', 3), k(VA, '05-24', 3),
                 (k(EN, '05-27', 3), dict(note='Printed again, as the letter the Governor of Massachusetts had published.')), k(BJ, '06-03', 2)]),
 # --- Spain, Adams ----------------------------------------------------------------------------------------------------
 dict(id='alicante-letters-1808', kind='context_group', label='Revolution in Spain: two letters from Alicante',
      definition=("Two letters from Alicante, both dated 27 March 1808, on the rising at Aranjuez and the fall of the Prince of Peace, as American "
                  "papers printed them in May 1808, several of them side by side ('Extract of another Letter'). Contains those two groups. Each is "
                  "one letter-writer's account."),
      children=['alicante-letter-aranjuez-rumour', 'alicante-letter-guards-ordered']),
 dict(id='alicante-letter-aranjuez-rumour', parent='alicante-letters-1808', kind='message_group', label="Alicante letter: 'a rumour being spread at Aranjuez'", role='report', words=55,
      core=[r'(?:R\s?EVOLUTION\s+IN\s+S\s?PAIN\.?\s+(?:A\s?CT\s+1\W+S\s?CENE\s+2,?\s+M\s?ADRID\.?\s+)?)?The\s+following\s+interesting\s+particulars\s+of\s+the\s+affairs\s+of\s+Spain'],
      definition=("Printings of a letter from Alicante of 27 March 1808, received at Boston and introduced as 'interesting particulars of the "
                  "affairs of Spain': a rumour that the royal family meant to leave for Cadiz and embark on the English squadron brought crowds to "
                  "the palace at Aranjuez; the Prince of Peace fell, and the King resigned his crown to his son. One paper prints only its later part."),
      first="A letter from Alicante (27 March 1808): a rumour at Aranjuez brings crowds to the palace, the Prince of Peace falls and Charles IV resigns the crown.", what='the Alicante letter',
      printings=[k(PGZ, '05-16', 2), (k(NI, '05-18', 3), dict(note="The paper prints the letter's later part on 20 May, as further details of the revolution.")),
                 k(ADA, '05-19', 3), k(NG, '05-23', 2), k(VA, '05-24', 2), k(EN, '05-24', 4),
                 (k(BJ, '05-27', 2), dict(core=[r'Details\s+relative\s+to\s+the\s+revolution\s+in\s+Spain'], dateline=False,
                                          note="Prints only the later part of the letter ('One of the first steps…'), as details relative to the revolution in Spain."))]),
 dict(id='alicante-letter-guards-ordered', parent='alicante-letters-1808', kind='message_group', label='Alicante letter: the guards ordered to Aranjuez', role='report', words=55,
      core=[r'["“]?A\s?LICANTE?,?\s+27(?:th)?,?\s+M\s?ARCH,?\s+1808\.?["”]?\s+["“]?On\s+the\s+1[78]th', r'On\s+the\s+1[78]th\s+inst\w*\.?,?\s+at\s+(?:nine|9)\s+in\s+the\s+evening'],
      definition=("Printings of another letter from Alicante of 27 March 1808, which reached Boston by the brig Sally: on the evening of 18 March "
                  "the Prince of Peace ordered the Spanish and Walloon guards to Aranjuez; a report that the royal family meant to flee to "
                  "Gibraltar and America brought a crowd to the palace crying 'kill the traitor'."),
      first="Another letter from Alicante (27 March 1808): the guards are ordered to Aranjuez, and a crowd at the palace cries 'kill the traitor'.", what='the second Alicante letter',
      printings=[k(NHG, '05-17', 2), k(ADA, '05-19', 3), k(NI, '05-20', 3), k(NG, '05-23', 2), k(VA, '05-24', 2), k(EN, '05-24', 4),
                 (k(BJ, '05-27', 3), dict(note='Printed on the page after the first letter\'s later part.'))]),
 dict(id='adams-resigns-senate', kind='document_group', label='John Quincy Adams resigns from the Senate', role='published_document', words=55, dateline=False,
      core=[r'(?:T\s?O\s+)?the\s+H\s?on\w*\.?\s+S\s?enate\s+and\s+H\s?ouse\s+of\s+R\s?epresentatives\s+of\s+the\s+[Cc]ommonwealth\s+of\s+M\s?assachusetts'],
      definition=("Printings of John Quincy Adams's letter of 8 June 1808 to the Massachusetts legislature, resigning his seat in the Senate after "
                  "the legislature had passed resolutions disapproving of measures he had supported."),
      first="John Quincy Adams writes to the Massachusetts legislature (8 June 1808) resigning his seat in the Senate.", what="Adams's letter",
      printings=[k(PGZ, '06-13', 2), k(NHG, '06-14', 3), k(ADA, '06-16', 3), k(NI, '06-17', 3), k(NG, '06-20', 2), k(EN, '06-21', 2), k(VA, '06-21', 2), k(BJ, '06-24', 2)]),
 # --- Second half of the year ------------------------------------------------------------------------------------------
 dict(id='charles-iv-appoints-murat', kind='document_group', label='Charles IV names Murat lieutenant-general of Spain', role='published_document', words=55, dateline=False,
      core=[r'L\s?etters?\s+(?:in|en)closing\s+the\s+R\s?o?yal\s+[Dd]ecree', r'L\s?ETTER\s+OF\s+THE\s+K\s?ING,?\s+[Aa]ppointing\s+M\s?urat', r'B\s?ROTHER\W+My\s+absence\s+and\s+infirmities'],
      definition=("Printings of Charles IV's letter to Murat, 'Brother, my absence and infirmities…', enclosing the royal decree (Bayonne, 4 May "
                  "1808) that made him lieutenant-general of the kingdom, to govern in the King's name. A document issued under French control."),
      first="Charles IV, at Bayonne (4 May 1808), names Murat lieutenant-general of Spain to govern in his name.", what="the King's letter",
      printings=[k(ADG, '07-27', 2), k(NI, '07-29', 2),
                 (k(EN, '07-29', 2), dict(words=45, note="The transcription runs on into a footnote of the preceding document after 'my crown,'; the excerpt ends before it.")),
                 (k(NG, '07-29', 3), dict(field=CA)), k(PGZ, '08-01', 2), k(VA, '08-02', 1), k(BJ, '08-05', 2)]),
 dict(id='order-in-council-4-july', kind='document_group', label='The British order in council of 4 July: peace with Spain', role='published_document', words=55, dateline=False,
      core=[r'A\s?T\s+the\s+[Cc]ourt\s+at\s+(?:the\s+)?Q\s?ueen.?s\s+P\s?alace,?\s+the\s+4th\s+(?:of\s+)?J\s?uly', r"(?:At\s+\w+\s+at\s+\[?)?(?:the\s+)?Queen.s\s+Palace,?\s+the\s+4th"],
      definition=("Printings of the order of the King in Council of 4 July 1808: in view of the Spanish nation's 'glorious exertions' against "
                  "France, all hostilities against Spain were to cease, the blockade of Spanish ports not held by France was raised, and Spanish "
                  "vessels were admitted to British ports."),
      first="Britain's order in council of 4 July 1808 ends hostilities against Spain after the Spanish rising against France.", what='the order in council',
      printings=[k(PGZ, '08-22', 2), k(NI, '08-24', 2), k(ADG, '08-24', 3), k(VA, '08-26', 2), k(EN, '08-26', 2), k(NG, '08-26', 3), k(NHG, '08-30', 2),
                 (k(NI, '09-23', 2), dict(note='Printed again a month after its first printing in this paper, from the London Gazette.'))]),
 dict(id='canning-on-america-24-june', kind='message_group', label='Canning in the Commons on America, 24 June', role='report', words=55, dateline=False,
      core=[r'(?:(?-i:A\s?MERICA)\.?\s+)?The\s+following\s+observations\s+were\s+made\s+by\s+M\s?r\.?\s+C\s?anning',
            r'(?:H\s?OUSE\s+OF\s+C\s?OMMONS\W+J\s?UNE\s+2[46]\.?\s+)?Extract\s+from\s+M\s?r\.?\s+C\s?ANNING.?s\s+[Ss]peech'],
      definition=("Printings of a report of George Canning's remarks in the House of Commons on 24 June 1808, answering Mr. Whitbread: no "
                  "communication had come from the American government since Mr. Rose's return; he could only conjecture that America was "
                  "negotiating with France; reparation for the Chesapeake had been offered without giving up the right of search. The papers' "
                  "heading calls him the Prime Minister; he was Foreign Secretary."),
      first="A report of Canning in the Commons, 24 June 1808: no communication from America since Rose's return, and only a conjecture why.", what='the report of the speech',
      printings=[k(NI, '08-26', 3), (k(ADG, '08-27', 2), dict(note="Prints the speech as an 'Extract from Mr. Canning's speech, on American affairs', in his own words. It begins at the foot of page 2 and continues on page 3.")),
                 (k(PGZ, '08-29', 1), dict(note='Begins on page 1 and continues on page 2.')), k(NG, '08-29', 2), (k(EN, '08-30', 2), dict(note="Prints the speech as an 'Extract from Mr. Canning's speech, on American affairs', in his own words.")),
                 k(VA, '09-02', 3), (k(BJ, '09-02', 2), dict(note="Prints the speech as an 'Extract from Mr. Canning's speech, on American affairs', in his own words. It begins at the foot of page 2 and continues on page 3."))]),
 dict(id='jefferson-answers-new-hampshire', kind='document_group', label="Jefferson's answer to the New Hampshire legislature", role='published_document', words=55, dateline=False,
      core=[r'(?:T\s?O\s+THE\s+L\s?EGISLATURE\s+OF\s+N\w*\.?\s*-?\s*H\s?AMPSHIRE\.?\s+)?I\s?N\s+the\s+review,?\s+[Ff]ellow.?[Cc]itizens'],
      definition=("Printings of President Jefferson's answer to the address of the New Hampshire legislature of 14 June 1808, which had approved "
                  "the measures of his administration, the embargo among them."),
      first="President Jefferson thanks the New Hampshire legislature for its address of 14 June 1808 approving his measures.", what="the President's answer",
      printings=[k(NHG, '08-16', 3), k(VA, '08-30', 3), k(EN, '08-30', 2), k(NI, '08-31', 3), k(ADG, '08-31', 2), k(NG, '08-31', 2), k(BJ, '09-09', 3)]),
 dict(id='arcturus-news-from-spain', kind='message_group', label='News from Spain by the Arcturus', role='report', words=55,
      core=[r'(?:L\s?ATEST\s+FROM\s+S\s?PAIN\.?\s+)?On\s+Saturday,?\s+arrived\s+the\s+\w+.?sailing\s+ship\s+Arcturus'],
      definition=("Printings of a Boston Gazette report of 5 September 1808: the ship Arcturus, 48 days from St. Sebastian, had arrived with P. R. "
                  "Livingston, bearer of dispatches from the French government, and with passengers' accounts that General Dupont had been "
                  "defeated at Cordova and Andujar. A report from passengers ('is said')."),
      first="Boston, September 1808: the ship Arcturus arrives from St. Sebastian with news that the French general Dupont has been defeated.", what='the Arcturus report',
      printings=[k(ADG, '09-10', 2), k(PGZ, '09-12', 2), k(VA, '09-13', 3), k(NI, '09-14', 1), k(NG, '09-14', 3), k(EN, '09-16', 1), k(BJ, '09-16', 2)]),
 dict(id='jefferson-answer-embargo-petitions', kind='document_group', label="Jefferson's answer to the petitions against the embargo", role='published_document', words=55, dateline=False,
      core=[r'(?:T\s?O\s+THE\s+I\s?NHABITANTS\s+OF\s+THE\s+T\s?OWN\s+(?:OF\s+)?\w+.{0,60}?assembled[.:]?\s+)?Y\s?OUR\s+representation\s+and\s+request\s+were\s+received'],
      definition=("Printings of President Jefferson's answer to the petition of the Boston town meeting, which had asked him to suspend the "
                  "embargo: he could not suspend it while the belligerents' edicts stood, and only the legislature could prescribe its course. "
                  "The Portland Gazette prints the same text as the answer to Portland's petition."),
      first="President Jefferson answers Boston's petition against the embargo: he cannot suspend it while the belligerents' edicts stand.", what="the President's answer",
      printings=[(k(PGZ, '09-12', 2), dict(note="The same answer, addressed to the inhabitants of Portland, whose petition was 'received on the 29th inst.'; the others print the answer to Boston, 'received on the 22d inst.'")),
                 k(NHG, '09-13', 2), k(NI, '09-14', 3), k(ADG, '09-14', 3), k(VA, '09-16', 3), k(EN, '09-16', 3), k(NG, '09-19', 2)]),
 dict(id='reding-dispatch-baylen', kind='message_group', label="General Reding's dispatch on the battle of Baylen", role='report', words=55,
      core=[r'(?:P\s?UBLICK?\s+N\s?OTICE\.?\s+)?The\s+[Ff]ield\s+[Mm]arshal\s+Don\s+T\w+\s+Rea?ding,?\s+has\s+sent'],
      definition=("Printings of the dispatch of the Spanish general Reding to General Castaños, 22 July 1808, on the action of 19 July near "
                  "Baylen, in which Dupont attacked the Spanish camp; printed from Spanish papers. One army's own account."),
      first="General Reding reports to Castaños (22 July 1808) on the battle near Baylen, in which Dupont attacked the Spanish camp.", what="Reding's dispatch",
      printings=[k(NI, '09-21', 3), (k(ADG, '09-22', 2), dict(note='Begins at the foot of page 2 and continues on page 3.')), k(PGZ, '09-26', 2), k(NG, '09-26', 2), k(VA, '09-27', 2), k(EN, '09-27', 2), k(BJ, '09-30', 2)]),
 dict(id='conventions-in-portugal', kind='context_group', label='The conventions in Portugal, 1808',
      definition=("The two conventions of late August and early September 1808 that ended the French occupation of Portugal, as American papers "
                  "printed them from London papers in October and November: the surrender of the Russian fleet in the Tagus, and the evacuation "
                  "of Portugal by the French army. Contains those two groups."),
      children=['russian-fleet-tagus-convention', 'cintra-convention']),
 dict(id='russian-fleet-tagus-convention', parent='conventions-in-portugal', kind='document_group', label='The convention for the Russian fleet in the Tagus', role='published_document', words=55, dateline=False,
      core=[r'A\s?RTICLES\s+OF\s+(?:A\s+)?C\s?ONVENTION[.,]?\s+(?:[Ee]ntered\s+into\s+between\s+[Vv]ice.?[Aa]dmiral\s+Sen\w+|[Ff]or\s+the\s+surrender\s+of\s+the\s+Russian\s+fleet)'],
      definition=("Printings of the articles agreed on 3 September 1808 between the Russian Vice-Admiral Seniavin and Admiral Sir Charles Cotton "
                  "for the surrender of the Russian fleet in the Tagus, to be held by Britain until after a peace, with Cotton's covering letter."),
      first="The convention of 3 September 1808: the Russian fleet in the Tagus is surrendered to Admiral Cotton, to be held until a peace.", what='the convention',
      printings=[k(NI, '10-26', 2), k(ADG, '10-28', 2), k(VA, '10-28', 3), k(EN, '10-28', 2), k(NG, '10-28', 2), k(PGZ, '10-31', 2),
                 (k(BJ, '11-11', 2), dict(core=[r'(?:and\s+other\s+Russian\s+orders,?\s+and\s+)?Admiral\s+Sir\s+Charles\s+Cotton,?\s+Baronet,?\s+for\s+the\s+surrender'],
                                          note="Cotton's covering letter is on page 1; the articles follow at the head of page 2, where the transcription begins in the middle of their heading."))]),
 dict(id='cintra-convention', parent='conventions-in-portugal', kind='document_group', label='The convention for the evacuation of Portugal', role='published_document', words=55, dateline=False,
      core=[r'D\s?EFINIT(?:IV)?E\s+C\s?ONVENTION[,.]?\s+(?:We\s+give\s+the\s+important\s+articles\s+)?F\s?OR\s+THE\s+E\s?VACUATION'],
      definition=("Printings of the definitive convention of 30 August 1808 (the Convention of Cintra) between the British and French commanders in "
                  "Portugal: the French army was to leave Portugal and be carried to France in British ships."),
      first="The definitive convention of 30 August 1808: the French army is to leave Portugal in British ships.", what='the convention',
      printings=[k(NI, '10-26', 2), k(ADG, '10-27', 2), k(VA, '10-28', 2), k(EN, '10-28', 2), k(NG, '10-28', 1), k(BJ, '11-04', 1)]),
 dict(id='message-8-november', kind='context_group', label="The President's message of 8 November and its documents",
      definition=("President Jefferson's last annual message, at the opening of the second session of the Tenth Congress on 8 November 1808, and "
                  "three of the diplomatic papers sent with it, which the papers printed in later issues and in instalments: Canning's note to "
                  "Pinkney, an extract of Armstrong's letter from France, and Madison's letter to Erskine. Contains those four groups."),
      children=['message-8-november-text', 'canning-to-pinkney-23-september', 'armstrong-letter-28-august', 'madison-to-erskine-25-march']),
 dict(id='message-8-november-text', parent='message-8-november', kind='document_group', label="The President's message of 8 November", role='published_document', words=55, dateline=False,
      core=[TO_HOUSES + r'I\s?T\s+would\s+have\s+been\s+a\s+source,?\s+[Ff]ellow.?[Cc]itizens'],
      definition=("Printings of President Jefferson's annual message to Congress of 8 November 1808: the overtures to Britain and France had "
                  "failed, their edicts stood, and Congress was to decide what course to take on the embargo."),
      first="President Jefferson's message of 8 November 1808 reports that the belligerents' edicts stand and leaves the course to Congress.", what="the President's message",
      printings=[k(NI, '11-08', 3), k(ADG, '11-09', 2), k(VA, '11-11', 2), k(EN, '11-11', 3), k(BJ, '11-11', 3), k(NHG, '11-15', 2), k(PGZ, '11-21', 1)]),
 dict(id='canning-to-pinkney-23-september', parent='message-8-november', kind='document_group', label="Canning's answer to Pinkney, 23 September", role='published_document', words=55, dateline=False,
      core=[r'(?:F\s?ROM\s+M\s?R\.?\s+)?C\s?ANNING\s+TO\s+M\s?R\.?\s+P\s?IN\w+\W+F\s?OREIGN\s+O\s?FFICE,?\s+September\s+23'],
      definition=("Printings of George Canning's note to William Pinkney (Foreign Office, 23 September 1808), sent to Congress with the President's "
                  "message: Britain declined the American offer to suspend the embargo as to Britain if the Orders in Council were withdrawn. The "
                  "British side's own statement."),
      first="Canning answers Pinkney (23 September 1808): Britain will not withdraw the Orders in Council in exchange for the embargo's suspension.", what="Canning's note",
      printings=[k(NI, '11-11', 1), k(ADG, '11-14', 2), k(VA, '11-15', 2), k(NG, '11-16', 2), (k(BJ, '11-25', 1), dict(note='Begins at the foot of page 1 and continues on page 2.')), k(PGZ, '11-28', 1)]),
 dict(id='armstrong-letter-28-august', parent='message-8-november', kind='document_group', label="Armstrong to Madison, 28 August", role='document_excerpt', words=55, dateline=False,
      core=[r'E\s?xtract\s+of\s+a\s+letter\s+from\s+(?:G\s?en\w*\.?\s+)?A\s?rmstrong.{0,60}?dated,?\s+B\s?OURBON', r'F\s?rom\s+G\s?en\.?\s+A\s?rmstrong\s+to\s+M\s?r\.?\s+M\s?adison\.?\s+.{0,3}B\s?ourbon'],
      definition=("Printings of an extract of General Armstrong's letter to the Secretary of State from Bourbon l'Archambault, 28 August 1808, sent "
                  "to Congress with the President's message: he would not return to Paris to renew his discussions with Champagny, being "
                  "convinced that a new attempt would be useless and probably injurious."),
      first="Armstrong writes from France (28 August 1808) that a new attempt to negotiate with Champagny would be useless.", what="Armstrong's letter",
      printings=[k(NI, '11-11', 1), k(ADG, '11-14', 2), k(VA, '11-15', 2),
                 (k(NI, '11-16', 1), dict(note='Printed again, with the fuller run of the documents.')), k(NG, '11-16', 2),
                 (k(NG, '11-21', 2), dict(note='Printed again, with the fuller run of the documents.')),
                 (k(ADG, '11-23', 2), dict(note='Printed again, with the fuller run of the documents.')), k(EN, '11-25', 1), k(BJ, '11-25', 1), k(PGZ, '11-28', 1),
                 (k(VA, '11-29', 1), dict(note='Printed again, with the fuller run of the documents.'))]),
 dict(id='madison-to-erskine-25-march', parent='message-8-november', kind='document_group', label='Madison to Erskine on the Orders in Council, 25 March', role='published_document', words=55, dateline=False,
      core=[r'(?:F\s?ROM\s+THE\s+S\s?ECRETARY\s+OF\s+S\s?TATE\s+TO\s+M\s?R\.?\s+E\w+\W+|(?:L\s?ETTER\s+FROM\s+)?M\s?R\.?\s+M\s?ADISON\s+TO\s+M\s?R\.?\s+E\s?RSKINE\.?\s+)?D\s?EPARTMENT\s+OF\s+S\s?TATE,?\s+March\s+25,?\s+1808'],
      definition=("Printings of the Secretary of State's letter to David Erskine, the British minister (25 March 1808), sent to Congress with the "
                  "President's message: the Orders in Council of November 1807 could not be justified as retaliation for the French decrees."),
      first="Madison answers Erskine (25 March 1808): the Orders in Council cannot be justified as retaliation against France.", what="Madison's letter",
      printings=[k(NI, '11-11', 1), k(ADG, '11-15', 2), k(VA, '11-18', 2), k(EN, '11-18', 4), k(NG, '11-18', 1), k(NHG, '11-22', 2), k(PGZ, '12-05', 1)]),
 dict(id='foreign-relations-report-22-november', kind='document_group', label="The House committee's report on foreign relations", role='published_document', words=55, dateline=False,
      core=[r'R\s?EPORT\.?\s+The\s+[Cc]ommittee\s+to\s+whom\s+was\s+referred\s+so\s+much\s+of\s+the\s+[Mm]essage',
            r'The\s+[Cc]ommittee\s+to\s+whom\s+was\s+referred\s+so\s+much\s+of\s+the\s+[Mm]essage\s+of\s+the\s+President.{0,80}?foreign\s+powers'],
      definition=("Printings of the report in part of the House committee on the part of the President's message concerning foreign relations "
                  "(presented on 22 November 1808 by George W. Campbell): the choice lay between submission, war with both Britain and France, "
                  "and continuing the embargo with stricter enforcement; with three resolutions."),
      first="The House committee on foreign relations reports (22 November 1808): submission, war with both, or the embargo enforced.", what="the committee's report",
      printings=[k(NI, '11-23', 3), k(ADG, '11-25', 2), k(NG, '11-28', 2), k(VA, '11-29', 1), k(EN, '11-29', 1), k(NHG, '12-06', 1), k(BJ, '12-09', 1)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline or heading directly before the item, after a sentence boundary (as for 1776 and 1807): "NORFOLK, July 6."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*180[78])?\.\s*(?:[—-]+\s*)?)$")


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


def cut_excerpt(text, start, words):
    """1776's cut: the opening of the item, ended at a clause boundary; the start anchor may run to 45 words."""
    tokens = list(re.finditer(r'\S+', text[start:]))
    n = min(words, len(tokens))
    for j in range(15, n):   # RevX sometimes abridges with an ellipsis; end before it.
        if '...' in tokens[j].group() or '…' in tokens[j].group():
            n = j if tokens[j].group().startswith(('...', '…')) else j+1
            break
    else:
        j = None
    limit = n if j is not None else min(n+15, len(tokens))
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
    for a in pq.read_table(RELEASE/'derived/reuse_family_appearances.parquet', columns=['family_id', 'page_id']).to_pylist():
        key = a['page_id'].split(':', 1)[1].replace(':', '|')
        if key.split('|')[1].startswith('1808'):
            out.setdefault(key, []).append(a['family_id'])
    return {key: sorted(v) for key, v in out.items()}


def build_rows(pages):
    rows, problems = [], []
    families = page_families()
    seen = {}
    for s, key, over in printings():
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
        excerpt, first, last = cut_excerpt(text, start, over.get('words', s['words']))
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
        rows.append({'story': story, 'page_key': key, 'field': field, 'excerpt_start': first, 'excerpt_end': last, 'excerpt': excerpt,
                     'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['page_key'].split('|')[1], r['page_key'], r['story']))
    for n, r in enumerate(rows, 1):
        r['id'] = f'S08-{n:03}'
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
               'admission_rule': 'Reviewed 1808 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    return {
        'ledger_id': 'ledger:stories-1808', 'ledger_version': 1, 'base_release': BASE, 'target_release': '0.9.0',
        'recorded_date': '2026-11-10', 'namespace': 'expansion-1808', 'evidence_dir': 'outputs/story_discovery_1808/evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1808, and of 1807 where they reach the 1808 pages (long-running ones '
                   'included), phrase searches on all 4,466 pages in both transcriptions, reading of every hit, and scan checks of each admitted passage'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             'outputs/story_discovery_1808/items.json': 'retrieval_candidates', 'outputs/story_discovery_1808/items_from_1807.json': 'retrieval_candidates',
                             'outputs/story_discovery_1808/phrase_patterns.json': 'retrieval_patterns', 'outputs/story_discovery_1808/phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1808.py': 'ledger_code', 'work/archive_data/ledgers/stories_1808_review.json': 'scan_review',
                             'outputs/story_discovery_1808/SCAN_PROTOCOL.md': 'review_protocol', 'outputs/story_discovery_1808/scan_points.json': 'review_protocol'},
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
