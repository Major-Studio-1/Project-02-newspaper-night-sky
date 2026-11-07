"""Write ledgers/stories_1797_round2.json (v0.3.0 -> v0.4.0). Kept as code so the long ledger stays readable.

Each row: id, page key, start anchor, end anchor, roles, groups, summary, note, [transcription field].
Scan findings and crops are filled in after the scan check (see fill step at the bottom).
"""
from pathlib import Path
import json

GUS, NH, KY, PG, MIR, EAG = 'sn83025881', 'sn83025588', 'sn82014782', 'sn84038410', 'sn83025525', 'sn84023150'
k = lambda paper, date, page: f'{paper}|1797-{date}|1|{page}'
CA = 'ca_ocr_text'
NOV, SS, HM, BA = 'congress-opening-nov-1797', 'special-session-1797', 'hermione-mutiny', 'blount-affair'

ROWS = [
 # Opening of Congress, November 1797
 ('E43', k(GUS, '11-23', 3), "PRESIDENT'S SPEECH. THIS DAY, At Twelve o'Clock", "to convene the National Legislature at some other place;", ['published_document'], [NOV], "Adams's speech opening the second session of Congress, which met in Philadelphia after the yellow fever.", "Earliest printing in the collection, on the day of the speech."),
 ('E44', k(NH, '12-06', 2), "On Thursday at 12 o'clock, the Senate having assembled", "to convene the national Legislature, at some other place.", ['published_document'], [NOV], "The New Hampshire Gazette prints the speech.", "Same speech; only the opening is excerpted."),
 ('E45', k(MIR, '12-12', 2), "At 12 o'clock, the Senate having assembled in the Representatives' Hall", "to convene the National Legislature, at some other place.", ['published_document'], [NOV], "The Mirror prints the speech.", "The speech continues on page 3."),
 ('E46', k(GUS, '11-28', 2), "The Senate, in a body, this day waited on the President", "which have always marked your official character.", ['reply'], [NOV], "The Senate's answer to the speech.", "Printed the day it was presented."),
 ('E47', k(NH, '12-13', 1), "The following is the address of the Senate, in answer", "which have always marked your official character.", ['reply'], [NOV], "The New Hampshire Gazette prints the Senate's answer.", "Same page as the House's answer."),
 ('E48', k(MIR, '12-19', 2), "The following is the Address of the Senate in answer", "which have always marked your official character.", ['reply'], [NOV], "The Mirror prints the Senate's answer.", "Same page as the House's answer."),
 ('E49', k(GUS, '11-28', 3), "Mr. OTIS, from the committee appointed to draft an address", "the duration of the late calamity was so limited", ['reply'], [NOV], "The House committee's draft answer, opening with sympathy for Philadelphia's sufferings.", "The draft as first reported; the House amended it before passing."),
 ('E50', k(NH, '12-13', 1), "The Answer of the House stands as follows", "the duration of the late calamity was so limited", ['reply'], [NOV], "The New Hampshire Gazette prints the House's answer as passed.", "After a report of the amendment debate."),
 ('E51', k(MIR, '12-19', 2), "Then answer was then reported to the House, and passed in the following words", "the duration of the late calamity was so limited", ['reply'], [NOV], "The Mirror prints the House's answer as passed.", "After a report of the amendment debate."),
 ('E52', k(GUS, '11-29', 3), "To which the President made the following reply", "with peculiar pleasure.", ['reply'], [NOV], "Adams's reply to the House's answer.", "Printed the day after it was given."),
 ('E53', k(MIR, '12-19', 3), "The President's Reply, to the Answer of the House.", "with peculiar pleasure.", ['reply'], [NOV], "The Mirror prints Adams's reply to the House.", "Follows Adams's reply to the Senate on the same page."),
 ('E54', k(EAG, '12-25', 3), "To which the President returned the following answer", "with peculiar pleasure.", ['reply'], [NOV], "The Eagle prints Adams's reply to the House.", "Same reply."),
 # Special session of Congress, 1797
 ('E55', k(PG, '04-06', 3), "By the President of the United States of America. A PROCLAMATION.", "divers great and weighty matters claim their attention", ['published_document'], [SS, 'special-session-proclamation'], "Adams's proclamation of 25 March 1797 summoning Congress to a special session.", "Reads 'claim their attention' where the other printings read 'consideration'."),
 ('E56', k(NH, '04-08', 2), "By the President of the United States of America, A Proclamation.", "divers great and weighty matters claim their consideration", ['published_document'], [SS, 'special-session-proclamation'], "The New Hampshire Gazette prints the proclamation.", "Same proclamation."),
 ('E57', k(KY, '04-19', 2), "By the President of the United States of America, A PROCLAMATION.", "divers great and weighty matters claim their consideration", ['published_document'], [SS, 'special-session-proclamation'], "The Kentucky Gazette prints the proclamation under 'By Authority'.", "Same proclamation."),
 ('E58', k(NH, '05-30', 3), "In committee of the whole, Mr. Dent in the chair on the address reported", "has excited in us the strongest emotions.", ['reply'], [SS, 'special-session-house-answer'], "The House's draft answer to Adams's special-session speech, as first reported.", "Draft text; the House debated amendments before passing it."),
 ('E59', k(GUS, '06-05', 3), "The house then withdrew, and waited upon the President", "has excited in us the strongest emotions.", ['reply'], [SS, 'special-session-house-answer'], "The House's answer as presented to the President.", "Final text."),
 ('E60', k(KY, '06-17', 2), "On motion, the house resolved itself into a committee of the whole", "has excited in us the strongest emotions.", ['reply'], [SS, 'special-session-house-answer'], "The Kentucky Gazette prints the draft answer.", "Draft text; the same paper printed the final answer two weeks later."),
 ('E61', k(KY, '07-01', 2), "At twelve o'clock the speaker and house went to the president's", "has excited in us the strongest emotions.", ['reply'], [SS, 'special-session-house-answer'], "The Kentucky Gazette prints the answer as presented.", "Final text, with a note that Mr. Lyon tried to end the custom of waiting on the president in a body."),
 # Hermione mutiny
 ('E62', k(GUS, '11-15', 3), "There is a report in circulation that the British frigate HERMIONE", "carried into Leguira.", ['report'], [HM], "First report: the crew of the British frigate Hermione are said to have seized her and taken her to La Guaira.", "A rumour, one sentence long."),
 ('E63', k(GUS, '11-16', 2), "Particulars of the Mutiny on board the Brigs Hermione.", "part of the crew were engaged handling the mizen topgall", ['report'], [HM, 'hermione-particulars'], "The detailed account of the mutiny, printed the next day.", "RevX abridges this item with '…'; read the scan for the full text."),
 ('E64', k(GUS, '11-21', 3), "The British frigate Hermione, which was lately carried into Laguira", "is sent to Porto Caballo and there laid up", ['later_related_account'], [HM], "Follow-up: the Spanish have laid the Hermione up at Puerto Cabello and the crew are dispersing.", "Later report."),
 ('E65', k(KY, '12-06', 3), "PHILADELPHIA November 15. We can say from the best authority that a mutiny", "delivered up to the Spaniards.", ['report'], [HM], "The Kentucky Gazette's first report of the mutiny, from Philadelphia, 15 November.", "Different wording from the Gazette of the United States rumour."),
 ('E66', k(MIR, '12-12', 2), "PHILAD. NOV. 16. Particulars of the mutiny", "when the others came down they were reprimanded", ['report'], [HM, 'hermione-particulars'], "The Mirror prints the detailed account.", "Same account; the scan reads 'Frigate', where RevX has 'Brigantine'."),
 ('E67', k(KY, '12-16', 2), "Particulars of the Mutiny on board the British Frigate Hermione.", "when the others came down they were reprimanded", ['report'], [HM, 'hermione-particulars'], "The Kentucky Gazette prints the detailed account, ten days after its first report.", "Same account."),
 ('E68', k(EAG, '12-25', 3), "PHILADELPHIA, NOV. 16. Particulars of the Mutiny onboard", "when the others came down they were reprimanded", ['report'], [HM, 'hermione-particulars'], "The Eagle prints the detailed account.", "Same account."),
 # Quito earthquake
 ('E69', k(GUS, '09-03', 3), "JAMAICA, July 15. Quito, 6th February, 1797.", "at half past 7 A. M.", ['report'], ['quito-earthquake'], "An account from Quito of the earthquake of 4 February 1797, via Jamaica.", "Earliest printing found."),
 ('E70', k(NH, '09-19', 2), "Earthquake in South-America. JAMAICA, July 15.", "THIS dreadful calamity begun", ['report'], ['quito-earthquake'], "The New Hampshire Gazette prints the same account under 'Earthquake in South-America'.", "Adds a footnote explaining where Quito is."),
 ('E71', k(KY, '09-27', 2), "JAMAICA, July 15. Quito, 6th February, 1797.", "at half past 7, A. M.", ['report'], ['quito-earthquake'], "The Kentucky Gazette prints the same account.", "Same account."),
 # Kosciuszko
 ('E72', k(GUS, '09-06', 3), "General Kosciusko, we hear, has left the city", "for his services in the cause of this country.", ['report'], ['kosciuszko-land-warrant'], "General Kościuszko, visiting Philadelphia, is offered a land warrant and back pay for his Revolutionary War service.", "Printed beside a yellow-fever burial report signed by Stephen Girard."),
 ('E73', k(NH, '09-19', 3), "PHILADELPHIA, Sept. 6. General Kosciuszko, we hear", "for his services in the cause of this country.", ['report'], ['kosciuszko-land-warrant'], "The New Hampshire Gazette prints the same item.", "Same item."),
 ('E74', k(KY, '09-27', 2), "General Kosciuszko, we hear, has left the city", "for his services in the cause of this country.", ['report'], ['kosciuszko-land-warrant'], "The Kentucky Gazette prints the item.", "Says he left to visit 'his friend General Gates, in the state of New York', not General White of New Brunswick."),
 # Jefferson's letter to Madison
 ('E75', k(NH, '01-21', 2), "We are informed, and from an authority which we rely on", "will be unquestionable.", ['report'], ['jefferson-madison-letter'], "Report that Jefferson wrote to Madison that Adams alone ought to have been elected, and that he would serve as Vice President under him.", "No dateline in this printing."),
 ('E76', k(GUS, '01-23', 3), "BOSTON, January 14. We are informed", "will be unquestionable.", ['report'], ['jefferson-madison-letter'], "The Gazette of the United States prints the report under a Boston dateline.", "Same report."),
 ('E77', k(PG, '02-09', 3), "WASHINGTON CITY, January 28. We are informed", "acceptance of Mr. Jefferson will be unquestion", ['report'], ['jefferson-madison-letter'], "The Patowmac Guardian prints the report under a Washington City dateline.", "Same report; spells out 'Mr. Jefferson' where others have 'Mr. J.'."),
 ('E78', k(GUS, '01-31', 2), "STOCKBRIDGE, January 23. It is true that Mr. Jefferson has written to Mr. Madison", "if there should be an equal vote between Mr. Adams and himself,", ['later_related_account'], ['jefferson-madison-letter'], "A Stockbridge report confirms the letter and gives a different account of what it asked.", "Different text: says the letter asked Madison to act if the vote was tied."),
 # Barney
 ('E79', k(GUS, '08-31', 3), "NORFOLK, August 24. Extract of a letter from Commodore Barney", "that is one ship of the", ['report'], ['barney-escapes-blockade'], "Commodore Barney, commanding French ships, writes that he has escaped a seven-month British blockade.", "Earliest printing found. RevX misreads the ship's name and a number; see the scan findings."),
 ('E80', k(NH, '09-12', 2), "NORFOLK, Aug. 24. Extract of a letter from Commodore Barney", "that is one ship of the", ['report'], ['barney-escapes-blockade'], "The New Hampshire Gazette prints Barney's letter.", "Same letter."),
 ('E81', k(KY, '09-27', 2), "NORFOLK, August 24. Extract of a letter from Commodore BARNEY", "that is one ship of the", ['report'], ['barney-escapes-blockade'], "The Kentucky Gazette prints Barney's letter.", "Same letter."),
 # Sonthonax leaves Saint-Domingue
 ('E82', k(GUS, '09-26', 3), "Capt, Cowper informs that Santhonax failed on the", "where he was hourly expefled.", ['report'], ['sonthonax-departure'], "Captain Cowper, from Cape François, reports that Sonthonax has sailed for France and Toussaint holds the chief command.", "RevX lacks this item, so the excerpt comes from the older CA transcription.", CA),
 ('E83', k(NH, '10-10', 3), "NORFOLK, Sept. 18. Yesterday arrived in Hampton roads the schooner Peggy", "where he was hourly expected.", ['report'], ['sonthonax-departure'], "The New Hampshire Gazette prints Cowper's report.", "Same report."),
 ('E84', k(MIR, '10-24', 3), "NORFOLK, SEPT. 18. Yesterday arrived in Hampton-Roads", "where he was hourly expected.", ['report'], ['sonthonax-departure'], "The Mirror prints Cowper's report.", "Same report."),
 ('E85', k(GUS, '10-17', 3), "Norfolk, Oct. 9. The fchr. Charles, 13 days from the Havana", "returned to the Havana.", ['later_related_account'], ['sonthonax-departure'], "A later report from Havana: Sonthonax sailed for France escorted by the Spanish frigate Juno.", "Different source and wording."),
 # French captures at Havana
 ('E86', k(MIR, '10-24', 2), "Sept. 25. By a gentleman of this city, who arrived at Savannah", "exceeds one hundred.", ['report'], ['havana-french-captures'], "A Charleston report that more than a hundred American vessels have been carried into Havana by French privateers and condemned.", "Headed 'French Piracies'."),
 ('E87', k(GUS, '10-24', 3), "CHARLESTON, Oct. 25. By a gentleman of this city", "exceed one hundred.", ['report'], ['havana-french-captures'], "The Gazette of the United States prints the report, headed 'French Piracies'.", "The printed dateline reads 'Oct. 25' on a 24 October page, where the other printings have Sept. 25: an error in the 1797 printing."),
 ('E88', k(NH, '10-25', 2), "CHARLESTON, Sept. 25. By a gentleman of this city", "exceeds one hundred.", ['report'], ['havana-french-captures'], "The New Hampshire Gazette prints the report.", "Same report."),
 # New Hampshire governor
 ('E89', k(NH, '11-29', 3), "The honorable Senate being assembled with the House", "afford so much cause for mutual congratulation,", ['published_document'], ['nh-governor-address-1797'], "The New Hampshire governor's address opening the legislature's session, 22 November 1797.", "Printed in the legislature's journal."),
 ('E90', k(MIR, '12-05', 3), "The Senate being assembled with the House in the Representatives' Chamber", "afford so much cause for mutual congratulation,", ['published_document'], ['nh-governor-address-1797'], "The Mirror prints the governor's address.", "Same address."),
 ('E91', k(GUS, '12-08', 2), "PORTSMOUTH, (N.H.) Nov. 25. On Wednesday last", "afford so much cause for mutual congratulation,", ['published_document'], ['nh-governor-address-1797'], "The Gazette of the United States in Philadelphia prints the New Hampshire governor's address.", "The only printing outside New Hampshire."),
 # Adams's reply to the Senate (addition to the farewell story)
 ('E92', k(GUS, '02-24', 3), "The reply of the Vice-President of the United States, to the address of the Senate", "established character in public affairs,", ['reply'], ['adams-senate-farewell'], "Adams's reply to the Senate's answer to his farewell address, 23 February 1797.", "Completes the exchange: address, answer, reply."),
 ('E93', k(PG, '03-09', 3), "The reply of the Vice President of the United States, to the Address of the Senate", "established character in public affairs,", ['reply'], ['adams-senate-farewell'], "The Patowmac Guardian prints Adams's reply.", "Same reply."),
 ('E94', k(NH, '03-11', 1), "REPLY Of the Vice-President of the United States to the address of the Senate", "established character in public affairs,", ['reply'], ['adams-senate-farewell'], "The New Hampshire Gazette prints Adams's reply on the same page as his address.", "Same reply."),
 # Blount affair: Knoxville welcome, House committee report
 ('E95', k(GUS, '10-12', 3), "On Saturday last returned to this towa the Hon. WILLIAM BLOUNT.", "conduced into town iu the following order", ['report'], [BA, 'blount-knoxville-welcome'], "A Knoxville report of Blount's welcome home: a cavalry troop and a crowd ride out eight miles to meet him.", "RevX lacks this item, so the excerpt comes from the older CA transcription.", CA),
 ('E96', k(NH, '10-25', 2), "KNOXVILLE, Sept. 18. Blount Forever.", "he was conducted into town in the following order", ['report'], [BA, 'blount-knoxville-welcome'], "The New Hampshire Gazette prints the Knoxville report under the heading 'Blount Forever'.", "Only this printing has the heading."),
 ('E97', k(KY, '11-01', 2), "KNOXVILLE, Sept. 18. On Saturday last returned to this town", "he was conducted into town in the following order", ['report'], [BA, 'blount-knoxville-welcome'], "The Kentucky Gazette prints the Knoxville report.", "Same report."),
 ('E98', k(GUS, '12-05', 3), "He then presented the report, which the clerk proceeded to read.", "was intimately connected with Mr. Blount;", ['report'], [BA, 'blount-committee-report'], "The House committee's report on evidence against Blount, as read on 4 December, naming Nicholas Romayne.", "Fuller account than the summaries in the other two papers."),
 ('E99', k(NH, '12-20', 2), "Of William Blount. Mr. Sngreaves, from the Committee", "made it necessary to secure their persons and papers.", ['report'], [BA, 'blount-committee-report'], "The New Hampshire Gazette's summary of the committee report.", "RevX reads 'Sngreaves' for Sitgreaves."),
 ('E100', k(MIR, '12-26', 2), "OF WILLIAM BLOUNT. Mr. Sirgreaves, from the Committee", "made it necessary to secure their persons and papers.", ['report'], [BA, 'blount-committee-report'], "The Mirror's summary of the committee report.", "Same summary as the New Hampshire Gazette."),
 # Greenock letter printed beside Boyd's report (no story group; linked by relations)
 ('E101', k(PG, '03-16', 3), "NORFOLK, March 6. Extract of a letter from a gentleman in Greenock", "ordered to leave Paris about three days ago", [], [], "A Greenock letter on Lord Malmesbury's recall, brought by the Peggy, Capt. Boyd.", "Printed on the same page as Boyd's Bantry report (H001)."),
 ('E102', k(NH, '03-25', 2), "NORFOLK, March 6. Extract of a letter from a gentleman in Greenock", "ordered to leave Paris about three days ago", [], [], "The same Greenock letter.", "Printed on the same page as Boyd's report (H002)."),
 ('E103', k(KY, '04-12', 3), "BALTIMORE, March 9. We are indebted to Captain Deglan", "which place she left the 2d of January.", [], [], "The same Greenock letter, under a Baltimore dateline.", "Printed on the same page as Boyd's report (H006). Dates the letter 25 December where the others have 29 December."),
]

GROUPS = [
 (NOV, 'context_group', 'Opening of Congress, November 1797', "Printings of Adams's speech opening the second session of the Fifth Congress (23 November 1797), the Senate's and House's answers, and his reply to the House."),
 (SS, 'context_group', 'Special session of Congress, 1797', "The special session of 1797: Adams's summoning proclamation (25 March), his speech (16 May) and the House's answer. Contains the speech, proclamation and answer groups."),
 ('special-session-proclamation', 'document_group', 'Proclamation summoning Congress', "Printings of Adams's proclamation of 25 March 1797 convening Congress on 15 May."),
 ('special-session-house-answer', 'document_group', "House's answer to the special-session speech", "Printings of the House of Representatives' answer to Adams's speech of 16 May 1797, in draft and final form."),
 (HM, 'context_group', 'Hermione mutiny', "Reports of the mutiny on the British frigate Hermione (September 1797) and her delivery to the Spanish at La Guaira: first rumours, the detailed 'Particulars', and a follow-up."),
 ('hermione-particulars', 'message_group', "'Particulars of the mutiny'", "Printings of the detailed account of the Hermione mutiny first printed in Philadelphia on 16 November 1797."),
 ('quito-earthquake', 'message_group', 'Quito earthquake', "Printings of a Quito account (6 February 1797), via Jamaica, of the earthquake of 4 February."),
 ('kosciuszko-land-warrant', 'message_group', "Kościuszko's land warrant", "Printings of a Philadelphia item (September 1797): Kościuszko is offered a land warrant and back pay for his Revolutionary War service and declines the money."),
 ('jefferson-madison-letter', 'context_group', "Jefferson's letter to Madison", "Reports (January 1797) that Jefferson wrote to Madison about the election result, and a later report giving a different account of the letter."),
 ('barney-escapes-blockade', 'message_group', "Barney escapes the blockade", "Printings of an extract of Commodore Barney's letter of 21 August 1797 on escaping a seven-month blockade."),
 ('sonthonax-departure', 'context_group', 'Sonthonax leaves Saint-Domingue', "Reports (September–October 1797) that the commissioner Sonthonax had sailed for France and Toussaint Louverture held the chief command."),
 ('havana-french-captures', 'message_group', 'French captures at Havana', "Printings of a Charleston report (September 1797) that more than a hundred American vessels had been carried into Havana by French privateers."),
 ('nh-governor-address-1797', 'document_group', "New Hampshire governor's address", "Printings of the New Hampshire governor's address to the legislature, 22 November 1797."),
 (BA, 'context_group', 'Blount affair', "The Blount affair in the 1797 papers: the letter made public (July), Blount's welcome home at Knoxville (September), and the House committee's report (December). Contains those three groups; the wider coverage is not included."),
 ('blount-knoxville-welcome', 'message_group', "Blount's welcome at Knoxville", "Printings of a Knoxville report (18 September 1797) of Blount's welcome home."),
 ('blount-committee-report', 'context_group', "House committee report on Blount", "Reports of the House committee's evidence report on Blount, 4 December 1797: a fuller account and a shorter summary."),
]

HIERARCHY = [(SS, 'adams-special-session-speech'), (SS, 'special-session-proclamation'), (SS, 'special-session-house-answer'),
             (HM, 'hermione-particulars'), (BA, 'blount-letter'), (BA, 'blount-knoxville-welcome'), (BA, 'blount-committee-report')]
ADDED = [('E13', SS, ['published_document']), ('E14', SS, ['published_document']), ('E15', SS, ['published_document']),
         ('E29', BA, ['published_document']), ('E30', BA, ['report']), ('E31', BA, ['report']), ('E32', BA, ['report'])]
RELATIONS = [('greenock-boyd-pg', 'E101', 'obs:chain-20261030:H001'), ('greenock-boyd-nh', 'E102', 'obs:chain-20261030:H002'), ('greenock-boyd-ky', 'E103', 'obs:chain-20261030:H006')]


def build(findings=None, crops=None, boxes=None):
    findings, crops, boxes = findings or {}, crops or {}, boxes or {}
    obs = []
    for row in ROWS:
        oid, key, start, end, roles, groups, summary, note = row[:8]
        o = {'id': oid, 'page_key': key, 'excerpt_start': start, 'excerpt_end': end, 'roles': roles, 'groups': groups,
             'summary': summary, 'note': note, 'scan_findings': findings.get(oid, ['pending']), 'crops': crops.get(oid, [])}
        if len(row) > 8:
            o['transcription_field'] = row[8]
        if oid in boxes:
            o['scan_boxes'] = boxes[oid]
        obs.append(o)
    return {
        'ledger_id': 'ledger:stories-1797-round2', 'ledger_version': 1, 'base_release': '0.3.0', 'target_release': '0.4.0',
        'recorded_date': '2026-11-06', 'namespace': 'expansion-1797', 'evidence_dir': 'outputs/story_discovery_1797/evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': 'Three-paper reuse families, round-two phrase searches on all 1,587 pages, reading of every printing, and scan checks of each admitted passage',
        'supporting_files': {'work/story_phrase_search_1797.py': 'retrieval_code', 'outputs/story_discovery_1797/phrase_patterns_round2.json': 'retrieval_patterns',
                             'outputs/story_discovery_1797/phrase_hits_round2.json': 'retrieval_candidates', 'work/archive_data/ledgers/make_stories_1797_round2.py': 'ledger_code'},
        'scan_scope': 'Each crop covers the excerpt, the opening of the printed item. Long documents were not proofread in full.',
        'observations': obs,
        'new_groups': [{'id': g, 'kind': kind, 'label': label, 'definition': d, 'admission_rule': 'Reviewed 1797 printings, checked against the scan.'} for g, kind, label, d in GROUPS],
        'new_hierarchy': [{'parent': p, 'child': c} for p, c in HIERARCHY],
        'added_memberships': [{'observation': o, 'group': g, 'roles': r, 'basis': 'Passage already admitted in an earlier release; joins the new parent story.'} for o, g, r in ADDED],
        'new_relations': [{'id': rid, 'subject': s, 'predicate': 'printed_alongside', 'object': o, 'directed': False, 'evidence_level': 'context_only',
                           'note': "The Greenock letter and Boyd's Bantry report are printed on the same page and both say they came on the Peggy, Capt. Boyd. Side-by-side printing, not a claim that one caused the other."} for rid, s, o in RELATIONS],
        'dispositions_summary': {'families_admitted': ['F97-030', 'F97-032', 'F97-060', 'F97-092', 'F97-074', 'F97-025', 'F97-068', 'F97-052', 'F97-088', 'F97-095', 'F97-097', 'F97-119', 'F97-065', 'F97-039', 'F97-093', 'F97-120', 'F97-033', 'F97-066'],
                                 'added_by_phrase_search': ['GUS 1797-11-15 p3', 'GUS 1797-11-16 p2', 'GUS 1797-11-21 p3', 'KY 1797-12-06 p3', 'GUS 1797-01-31 p2', 'GUS 1797-10-17 p3'],
                                 'not_admitted': {'GUS 1797-06-07 p2 (F97-025)': 'answer text not found on this page', 'GUS 1797-10-25 p3': 'ship arrival list naming the Cleopatra, not the report',
                                                  'other Kosciuszko and Romayne pages': 'different items about the same people'}},
    }


if __name__ == '__main__':
    import sys
    out = Path(__file__).with_name('stories_1797_round2.json')
    extra = json.loads(Path(sys.argv[1]).read_text(encoding='utf8')) if len(sys.argv) > 1 else {}
    out.write_text(json.dumps(build(extra.get('findings'), extra.get('crops'), extra.get('boxes')), ensure_ascii=False, indent=2), encoding='utf8')
    print('wrote', out, len(ROWS), 'observations')
