"""Write ledgers/stories_1776.json (v0.6.1 -> v0.7.0): reviewed stories of 1776.

The stories were chosen by reading the year's matched items (work/story_items.py splits the automatic
families into single printed items) and confirmed with phrase searches over all 2,319 pages of 1776 in
both transcriptions (work/story_phrase_search.py). See outputs/story_discovery_1776/README.md.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly
as apply_ledger.py does: the excerpt is the opening of the printed item (about 40-60 words), starting
with its dateline or heading when one stands directly before it. Scan findings, crops and hand-drawn
boxes are merged from stories_1776_review.json after the scan check.

Run from the project root with Python 3.12 (needs outputs/story_discovery_1776/search_pages.json,
made by work/year_search_pages.py):
    python work/archive_data/ledgers/make_stories_1776.py [--table]
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PAGES = PROJECT/'outputs/story_discovery_1776/search_pages.json'
REVIEW = HERE/'stories_1776_review.json'
OUT = HERE/'stories_1776.json'
RELEASE = PROJECT/'outputs/data_foundation/v0.6.1'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PEP, VGB, VGA, PP, PG, PL, PJ = 'sn83025894', 'sn84024742', 'sn84024739', 'sn83021126', 'sn84026371', 'sn83025898', 'sn85047530'
FJ, NYP, NEC, NYG, AG, CC, EJ, BG, NHG = 'sn83025583', 'sn83030135', 'sn83020482', 'sn83030493', 'sn83020494', 'sn82016139', 'sn83020452', 'sn83021292', 'sn83025582'
PAPER = {PEP: 'The Pennsylvania Evening Post', VGB: "Purdie's Virginia Gazette", VGA: "Dixon and Hunter's Virginia Gazette",
         PP: "Dunlap's Pennsylvania Packet", PG: 'The Pennsylvania Gazette', PL: 'The Pennsylvania Ledger', PJ: 'The Pennsylvania Journal',
         FJ: "The Freeman's Journal", NYP: 'The New-York Packet', NEC: 'The New-England Chronicle', NYG: 'The New-York Gazette',
         AG: 'The American Gazette', CC: 'The Connecticut Courant', EJ: 'The Essex Journal', BG: 'The Boston Gazette', NHG: 'The New-Hampshire Gazette'}
k = lambda paper, date, page, ed=1: f'{paper}|1776-{date}|{ed}|{page}'
CONGRESS = r'I\s?N\s+C\s?O\s?N\s?G\s?R\s?E\s?S\s?S\.?,?\s+'

# Story groups. 'printings' lists each printing's page; a tuple adds overrides for that printing:
# core (regexes for the item's first words), role, field, note, dateline (include a dateline or heading directly before).
STORIES = [
 dict(id='king-speech-october-1775', kind='document_group', label="The King's speech of October 1775", role='published_document', words=55, dateline=False,
      core=[r'My\s+Lords,?\s+and\s+Gentlemen[,.]?\W{0,6}T\s?HE\s+present\s+situation'],
      definition="Printings of George III's speech opening the session of Parliament in October 1775, which the American papers printed from January 1776. The printings date the speech differently: the 26th in one, the 27th in another.",
      first="George III's speech opening the session of Parliament in October 1775, as printed in New York in January 1776.", what="the King's speech",
      printings=[k(NYG, '01-08', 2), k(NHG, '01-09', 1), k(PEP, '01-09', 2), k(PG, '01-10', 1), k(NYP, '01-11', 1), k(PL, '01-13', 1),
                 k(PP, '01-15', 1), k(VGB, '01-19', 2), k(VGA, '01-20', 3)]),
 dict(id='quebec-siege-1776', kind='context_group', label='Siege of Quebec',
      definition="Reports of the American siege of Quebec in the 1776 papers: Montgomery's letter calling on Carleton to surrender (December 1775), the account of the failed assault of 31 December, and a camp letter of 6 April 1776. Contains those three groups; the wider coverage is not included.",
      children=['montgomery-letter-to-carleton', 'quebec-assault-report', 'quebec-camp-letter']),
 dict(id='montgomery-letter-to-carleton', parent='quebec-siege-1776', kind='document_group', label="Montgomery's letter to Carleton", role='published_document', words=50,
      core=[r'(?:Copy\s+of\s+a\s+letter|A\s+letter|The\s+following\s+is\s+a\s+genuine\s+Copy\s+of\s+a\s+Letter)\s+from\s+(?:his\s+Excellency\s+)?Gen\w*\.?\s+Montgomery'],
      definition="Printings of General Montgomery's letter to Governor Carleton from before Quebec, dated December 1775, calling on him to surrender the town.",
      first="General Montgomery's letter to Governor Carleton from before Quebec, calling on him to surrender.", what="Montgomery's letter",
      printings=[k(NYP, '01-18', 3), k(PP, '01-22', 3), k(NYG, '01-22', 1), k(PEP, '01-23', 2), k(PG, '01-24', 2), k(VGB, '02-02', 5), k(VGA, '02-03', 3)]),
 dict(id='quebec-assault-report', parent='quebec-siege-1776', kind='message_group', label='Failed assault on Quebec', role='report', words=55,
      core=[r'T\s?HE\s+last\s+letters\s+from\s+Canada'],
      definition="Printings of a Philadelphia report (25 January 1776) of the unsuccessful attempt to take Quebec by storm on 31 December 1775.",
      first="A Philadelphia report that the last letters from Canada tell of a failed attempt to take Quebec by storm on 31 December.", what='the report',
      printings=[k(PEP, '01-25', 2), k(PL, '01-27', 3), k(PP, '01-29', 3), k(PG, '01-31', 4), k(NYP, '02-01', 3), k(NYG, '02-05', 3), k(VGB, '02-09', 2)]),
 dict(id='quebec-camp-letter', parent='quebec-siege-1776', kind='message_group', label='Letter from the camp before Quebec', role='report', words=55,
      core=[r'(?:Extract|Excerpt)\s+of\s+a\s+[Ll]etter,?\s+(?:from\s+a\s+[Gg]entleman\s+in\s+the\s+[Cc]ontinental\s+[Aa]rmy|dated\s+in\s+the\s+[Cc]amp)',
            r'A\s+letter\s+from\s+a\s+[Gg]entleman\s+in\s+the\s+[Cc]ontinental\s+army'],
      definition="Printings of an extract of a letter from the American camp before Quebec, dated 6 April 1776, on the batteries and the want of men. It circulated in two versions.",
      first="An extract of a letter from the American army before Quebec, 6 April 1776: the batteries are firing, and more men are needed.", what='the letter',
      printings=[k(NYP, '05-02', 3), k(PEP, '05-04', 3), k(PP, '05-06', 3), k(NYG, '05-06', 3), k(PG, '05-08', 3), k(PJ, '05-08', 2),
                 k(NEC, '05-09', 3), k(VGB, '05-17', 2), k(VGA, '05-18', 3), k(VGB, '05-24', 1)]),
 dict(id='boston-evacuation-letter', kind='message_group', label='Boston evacuated', role='report', words=55,
      core=[r'(?:Extract|Excerpt)\s+of\s+a\s+letter,?\s+received\s+by\s+express'],
      definition="Printings of an extract of a letter from headquarters at Cambridge, 19 March 1776, reporting that the British army left Boston on 17 March.",
      first="An extract of a letter from headquarters at Cambridge, 19 March 1776: the British army left Boston on Sunday the 17th.", what='the letter',
      printings=[k(PP, '03-25', 6), k(PEP, '03-26', 1), k(PG, '03-27', 2), k(PJ, '03-27', 2),
                 k(PL, '03-30', 3), k(VGB, '04-05', 2), k(VGA, '04-06', 3)]),
 dict(id='congress-opens-ports', kind='document_group', label='Congress opens the ports', role='published_document', words=55,
      core=[CONGRESS+r'(?:April|March)\s+6'],
      definition="Printings of Congress's resolutions of 6 April 1776 opening American ports to trade with all countries not under the British crown.",
      first="Congress's resolutions of 6 April 1776 opening the ports to trade with all countries not under the British crown.", what='the resolutions',
      printings=[k(PP, '04-08', 3), k(PEP, '04-09', 1), k(PG, '04-10', 3), k(PJ, '04-10', 2), k(NYP, '04-11', 3), k(PL, '04-13', 4),
                 k(VGB, '04-19', 5), k(VGA, '04-20', 2), k(NEC, '04-25', 3)]),
 dict(id='hopkins-nassau-letter', kind='message_group', label="Hopkins's report from New Providence", role='report', words=55,
      core=[r'(?:Extract|Extra|Extrait|Excerpt)\w*\s+of\s+a\s+[Ll]etter\s+from\s+Es\w+\s+Hopkins'],
      definition="Printings of an extract of Commodore Esek Hopkins's letter of 9 April 1776 to the President of Congress, on the fleet's expedition to New Providence in the Bahamas.",
      first="An extract of Commodore Hopkins's letter to the President of Congress (9 April 1776) on the fleet's cruise to the Bahamas.", what="Hopkins's letter",
      printings=[k(PEP, '04-16', 2), k(PG, '04-17', 2), k(PJ, '04-17', 3), k(PL, '04-20', 3), k(PP, '04-22', 5), k(NYG, '04-22', 2), k(VGA, '05-04', 3)]),
 dict(id='dublin-paper-naval-force', kind='message_group', label='A Dublin paper: British force coming', role='report', words=50, back_to_sentence=True,
      core=[r'Dublin\s+[Pp]aper\s+of\s+the\s+(?:2d|second)\s+of\s+March'],
      definition="Printings of news brought to Philadelphia in May 1776 by a passenger from Europe with a Dublin paper of 2 March: that a large naval force was coming to America and was ordered to sail on 10 April, followed by London paragraphs from that paper. The forecast is a report, not an observed event.",
      first="A passenger from Europe brings a Dublin paper of 2 March: a large British naval force is coming to America, ordered to sail on 10 April.", what='the news',
      printings=[k(PP, '05-06', 5), k(PEP, '05-07', 1), k(PG, '05-08', 1), k(PJ, '05-08', 1), k(NYP, '05-09', 2), k(PL, '05-11', 1),
                 k(NEC, '05-16', 3), k(VGA, '05-18', 3), k(FJ, '05-25', 1)]),
 dict(id='ethan-allen-cork', kind='message_group', label='Ethan Allen at Cork', role='report', words=55,
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+Cork', r'The\s+following\s+occurrence\s+must\s+give\s+satisfaction'],
      definition="Printings of an extract of a letter from Cork (January 1776) on the gifts collected for Colonel Ethan Allen and his fellow prisoners in the Solebay, with Allen's note of thanks.",
      first="An extract of a letter from Cork: gentlemen of the city collect gifts for Ethan Allen and his fellow prisoners in the Solebay.", what='the Cork letter',
      printings=[k(PP, '05-06', 5), k(PEP, '05-07', 1), k(PG, '05-08', 2), k(PJ, '05-08', 2), k(PL, '05-11', 4), k(NEC, '05-16', 3),
                 k(VGA, '05-18', 3), k(FJ, '05-25', 2), (k(NYP, '08-15', 3), dict(core=[r'Copy\s+of\s+Colonel\s+ALLEN'], note="Prints only Allen's note, three months after the other papers."))]),
 dict(id='rhode-island-renunciation', kind='document_group', label='Rhode Island renounces allegiance', role='published_document', words=55,
      core=[r'Colony\s+of\s+R\s?HODE.?I\s?SLAND'],
      definition="Printings of the Rhode Island General Assembly's act of May 1776 repealing the act that secured allegiance to the King and putting the colony's name in place of his in commissions and writs.",
      first="Rhode Island's act of May 1776 repealing the act that secured allegiance to the King.", what='the act',
      printings=[k(PG, '05-15', 3), k(PJ, '05-15', 3), k(PEP, '05-18', 2), k(PL, '05-18', 3), k(PP, '05-20', 4), k(NYG, '05-20', 2), k(NEC, '05-23', 1),
                 (k(VGA, '06-01', 3), dict(core=[r'The\s+General\s+Assembly\s+of\s+Rhode\s+Island\s+have\s+passed'], role='condensed_report',
                                           note='A one-sentence summary of the act. A second scanned copy of this issue (edition 2) has the same text.'))]),
 dict(id='congress-may-15-resolution', kind='document_group', label="Congress's resolution of 15 May", role='published_document', words=55,
      core=[CONGRESS+r'M\s?A\s?Y\s+15,?\s+1776', r'W\s?HEREAS\s+his\s+Britann?ic?k?\s+Majesty,?\s+in\s+conjunction'],
      definition="Printings of Congress's resolution of 15 May 1776, with its preamble, recommending that the colonies adopt governments under the authority of the people. Includes printings that quote it in full in reports of other bodies' proceedings.",
      first="Congress's resolution of 15 May 1776: the colonies are to adopt governments under the authority of the people.", what='the resolution',
      printings=[k(PEP, '05-16', 3), k(PL, '05-18', 3), k(PP, '05-20', 2), k(NYG, '05-20', 3),
                 (k(PEP, '05-21', 2), dict(role='quoted_document', note='Read out and printed within the report of the Philadelphia meeting at the State House on 20 May.')),
                 k(PG, '05-22', 1), k(PJ, '05-22', 1), k(NEC, '05-30', 1), k(VGB, '05-31', 1),
                 (k(VGA, '06-01', 2), dict(note='A second scanned copy of this issue (edition 2) has the same text.')),
                 (k(NYP, '06-06', 3), dict(core=[r'And\s+whereas\s+the\s+Continental\s+Congress\s+did\s+resolve'], role='quoted_document',
                                           note="Quoted in the New York Provincial Congress's resolution of 31 May.")),
                 k(FJ, '06-08', 4),
                 (k(NYP, '06-13', 2), dict(core=[r'And\s+whereas\s+the\s+Continental\s+Congress\s+did\s+resolve'], role='quoted_document',
                                           note="Quoted in the New York Provincial Congress's resolution of 31 May, printed again a week later.")),
                 (k(PJ, '06-19', 3), dict(role='quoted_document', note='Quoted in a report of proceedings that had the resolution read.'))]),
 dict(id='virginia-independence-resolution', kind='document_group', label='Virginia Convention, 15 May 1776', role='published_document', words=55,
      core=[r'I\s?N\s+C\s?O\s?N\s?V\s?E\s?N\s?T\s?I\s?O\s?N\.?,?\s+P\s?R\s?E\s?S\s?E\s?N\s?T', r'F\s?ORASMUCH\s+as\s+(?:all\s+)?the\s+en'],
      definition="Printings of the Virginia Convention's resolutions of 15 May 1776, which instructed the colony's delegates to propose that Congress declare the colonies free and independent states.",
      first="The Virginia Convention's resolutions of 15 May 1776, instructing its delegates to propose independence.", what='the resolutions',
      printings=[k(VGB, '05-17', 2), k(VGA, '05-18', 4), k(PEP, '05-28', 2), k(PG, '05-29', 2), k(NYP, '05-30', 3), k(PL, '06-01', 1), k(NEC, '06-06', 3), k(AG, '07-02', 1)]),
 dict(id='london-address-to-king-1776', kind='document_group', label="London's address to the King", role='published_document', words=55, dateline=False,
      core=[r'(?:From\s+the\s+LONDON\s+GAZETTE\.\s+)?S\s?T\.?\s+J\s?A\s?M\s?E\s?S.S,?\s+M\s?a\s?r\s?c\s?h\s+22', r'T\s?HIS\s+day\s+the\s+Right\s+Hon'],
      definition="Printings of the City of London's address and petition to the King against the war (St. James's, 22 March 1776), with the King's answer.",
      first="The City of London's address and petition to the King of 22 March 1776, from the London Gazette, with his answer.", what='the address',
      printings=[k(PEP, '06-04', 1), k(PG, '06-05', 2), k(PJ, '06-05', 2),
                 (k(NYP, '06-06', 3), dict(core=[r'By\s+Capt\.\s+Farey'], note='Says the address was taken from a St. Kitts paper brought by Capt. Farey from St. Eustatius.')),
                 k(PL, '06-08', 1), k(PP, '06-10', 1), k(AG, '06-18', 2),
                 (k(NEC, '06-20', 1), dict(core=[r'By\s+him\s+we\s+have\s+been\s+favou?red\s+with\s+a\s+St\.?\s+Kitt'], note="Says the address was taken from a St. Kitt's paper brought from St. Eustatia.")),
                 k(FJ, '06-22', 1), k(VGA, '06-22', 2)]),
 dict(id='pennsylvania-new-instructions', kind='document_group', label="Pennsylvania's new instructions", role='published_document', words=55,
      core=[r'(?:This\s+day|Last\s+Saturday|The)\s+the\s+Hon\w*\.?\s+House\s+of\s+Assembly\s+gave', r'The\s+Hon\w*\.?\s+House\s+of\s+Assembly\s+gave'],
      definition="Printings of the Pennsylvania Assembly's instructions of 8 June 1776 to its delegates in Congress, which withdrew the November instruction to reject any proposal that might lead to separation from Great Britain.",
      first="The Pennsylvania Assembly's new instructions to its delegates in Congress, given on 8 June 1776.", what='the instructions',
      printings=[k(PEP, '06-08', 3), k(PP, '06-10', 2), k(PG, '06-12', 2), k(PL, '06-15', 1), k(NYP, '06-20', 3), k(VGA, '06-22', 5), k(NEC, '06-27', 2), k(AG, '07-02', 1)]),
 dict(id='declaration-of-independence', kind='document_group', label='Declaration of Independence', role='published_document', words=50,
      core=[CONGRESS+r'J\s?U\s?L\s?Y\s+4,?\s+1776', r'A\s+DECLARATION,?\s+[Bb]y\s+the'],
      definition="Printings of the Declaration of Independence (4 July 1776), plus one printing of its conclusion with a summary a week before that paper printed the full text.",
      first="The Declaration of Independence, printed in Philadelphia two days after it was adopted.", what='the Declaration',
      printings=[k(PEP, '07-06', 1), k(PP, '07-08', 1), k(PG, '07-10', 1), k(PJ, '07-10', 1), k(NYP, '07-11', 4), k(PL, '07-13', 2), k(CC, '07-15', 2),
                 k(AG, '07-16', 1), k(NEC, '07-18', 1), k(EJ, '07-19', 1),
                 (k(VGB, '07-19', 2), dict(core=[r'Abstract\s+from\s+the\s+minutes\s+of\s+the\s+General\s+Congress'], role='document_excerpt', dateline=False,
                                           note="A summary and the Declaration's closing paragraphs, with the promise that the full text will follow in the next week's Gazette.")),
                 (k(FJ, '07-20', 3), dict(core=[r'In\s+CONGRESS,\s+DECLARATION'])), (k(VGA, '07-20', 2), dict(note='A second scanned copy of this issue (edition 2) has the same text.')), k(BG, '07-22', 1),
                 (k(VGB, '07-26', 1), dict(note="Printed under the Virginia Council's order of 20 July that the printers publish the Declaration. A second scanned copy of this issue (edition 2) has the same text."))]),
 dict(id='campbell-captured-letter', kind='message_group', label="Campbell's letter after his capture", role='report', words=55,
      core=[r'Copy\s+of\s+a\s+[Ll]etter\s+from\s+Lieut'],
      definition="Printings of Lieutenant Colonel Campbell's letter to General Howe (Boston, 19 June 1776), reporting that he and two companies of Highlanders had been taken in Boston harbour.",
      first="Lieutenant Colonel Campbell writes to General Howe that his transports sailed into Boston harbour and were taken.", what="Campbell's letter",
      printings=[k(PG, '07-03', 2), k(PJ, '07-03', 3), k(PEP, '07-04', 3), k(PL, '07-06', 3), k(NYG, '07-08', 3), k(NEC, '07-18', 2), k(FJ, '07-27', 4), k(VGA, '07-29', 4), k(AG, '07-30', 2)]),
 dict(id='cedars-cartel-report', kind='document_group', label='Congress on the Cedars cartel', role='published_document', words=55,
      core=[r'T\s?HE\s+[Cc]ommittee,?\s+to\s+whom\s+the\s+[Cc]artel'],
      definition="Printings of the report adopted by Congress on 10 July 1776 on the cartel General Arnold agreed with Captain Foster after the surrender at the Cedars, with its resolutions.",
      first="Congress's committee report (10 July 1776) on the surrender at the Cedars and the cartel Arnold agreed with Captain Foster.", what='the report',
      printings=[k(PEP, '07-25', 1), k(PL, '07-27', 2), k(PP, '07-29', 2), k(PG, '07-31', 1), k(PJ, '07-31', 1), k(NYG, '08-05', 1), k(NEC, '08-08', 1),
                 k(VGB, '08-09', 2), k(VGA, '08-10', 3), k(FJ, '08-17', 1)]),
 dict(id='washington-patterson-interview', kind='message_group', label='Washington meets Colonel Patterson', role='report', words=50,
      core=[r'(?:The|An)\s+(?:following\s+is\s+an\s+)?exact\s+[Ss]tate\s+of\s+what\s+passed'],
      definition="Printings of the account of the interview of 20 July 1776 between General Washington and Colonel Patterson, General Howe's adjutant general.",
      first="An account of what passed when Colonel Patterson, General Howe's adjutant general, met Washington on 20 July.", what='the account',
      printings=[k(PEP, '07-27', 3), k(PP, '07-29', 3), k(PG, '07-31', 3), k(PJ, '07-31', 1), k(PL, '08-03', 2), k(NYG, '08-05', 1), k(NEC, '08-15', 4),
                 k(VGB, '08-16', 1), k(FJ, '08-17', 1), k(VGA, '08-17', 1)]),
 dict(id='prize-resolutions-extended', kind='document_group', label='Prize resolutions extended', role='published_document', words=60,
      core=[CONGRESS+r'July\s+24'],
      definition="Printings of Congress's resolution of 24 July 1776 extending its earlier resolutions on captured ships and goods to all subjects of the King of Great Britain, except the inhabitants of the Bermudas and the Bahamas.",
      first="Congress's resolution of 24 July 1776 extending its earlier prize resolutions to all British ships and goods.", what='the resolution',
      printings=[k(PEP, '07-27', 4), k(PL, '07-27', 3), k(PP, '07-29', 3), k(PG, '07-31', 3), k(PJ, '07-31', 3),
                 (k(PP, '08-05', 3), dict(note='Printed again a week after its first printing in this paper.')), k(NYG, '08-05', 1), k(NEC, '08-08', 2), k(VGB, '08-16', 1), k(FJ, '08-17', 4)]),
 dict(id='hudson-warships-1776', kind='context_group', label='British warships in the Hudson',
      definition="Reports of the British warships that went up the Hudson on 12 July 1776: lying in Haverstraw Bay, boats driven off at Tappan, the attack by American row galleys (3 August) and the fire-ship attack (16 August). Contains those four groups; the wider coverage is not included.",
      children=['haverstraw-bay-report', 'tappan-meadows-report', 'gondolas-attack-report', 'fire-ships-attack-report']),
 dict(id='haverstraw-bay-report', parent='hudson-warships-1776', kind='message_group', label='Warships in Haverstraw Bay', role='report', words=50,
      core=[r'(?:By\s+the\s+last\s+accounts?\s+we\s+ha(?:ve|d)\s+(?:had\s+)?of\s+the\s+two|The)\s+[Mm]en\s+of\s+[Ww]ar,?\s+that\s+lately\s+went\s+up'],
      definition="Printings of a New York report (24 July 1776) that the men of war lie in Haverstraw Bay, that a tender was fired on, and that a landing party was attacked at Peekskill.",
      first="A New York report: the men of war lie in Haverstraw Bay, a tender was hit near the fort, and a landing party at Peekskill was attacked.", what='the report',
      printings=[k(PEP, '07-25', 3), k(PL, '07-27', 3), k(PP, '07-29', 2), k(NYG, '07-29', 3), k(PG, '07-31', 2), k(PJ, '07-31', 2), k(FJ, '08-03', 2), k(VGB, '08-09', 2), k(VGA, '08-10', 3)]),
 dict(id='tappan-meadows-report', parent='hudson-warships-1776', kind='message_group', label='Boats driven off at Tappan', role='report', words=45,
      core=[r'On\s+Monday\s+last\s+five\s+of\s+the\s+men\s+of\s+war'],
      definition="Printings of a New York report (end of July 1776) that about fifteen inhabitants drove off five boats from the men of war trying to land on Tappan meadows.",
      first="A New York report: about fifteen inhabitants in a fishing hut drive off five boats trying to land on Tappan meadows.", what='the report',
      printings=[k(PEP, '08-01', 2), k(PL, '08-03', 2), k(PP, '08-05', 2), k(PJ, '08-07', 2), k(NEC, '08-08', 3), k(FJ, '08-10', 2), k(VGB, '08-16', 2)]),
 dict(id='gondolas-attack-report', parent='hudson-warships-1776', kind='message_group', label='Row galleys attack the warships', role='report', words=55,
      core=[r'(?:Last\s+)?Saturday\s+[Aa]fternoon,?\s+a\s+heavy\s+[Cc]annonade', r'We\s+have\s+the\s+following\s+particulars,?\s+from\s+a\s+New', r'At\s+about\s+(?:half\s+)?a\s+[Qq]uarter\s+after'],
      definition="Printings of an eyewitness account of the attack by American row galleys (gondolas) on the Phoenix and the Rose on 3 August 1776.",
      first="An eyewitness account of the row galleys' attack on the Phoenix and the Rose in the Hudson.", what='the account',
      printings=[k(NYG, '08-05', 3), k(PEP, '08-06', 3), k(PG, '08-07', 2), k(PL, '08-10', 3), k(NEC, '08-15', 2), k(VGB, '08-16', 2),
                 (k(VGA, '08-17', 2), dict(note='Says the particulars are taken from a New York paper of 5 August.')), k(FJ, '08-24', 1)]),
 dict(id='fire-ships-attack-report', parent='hudson-warships-1776', kind='message_group', label='Fire-ship attack', role='report', words=50,
      core=[r'(?:Last\s+Friday|Same\s+day)\s+two\s+[Ff]ire.?[Ss]hips'],
      definition="Printings of a New York report of the fire-ship attack on the British ships in the Hudson on 16 August 1776.",
      first="A New York report: two fire-ships attack the British ships in the Hudson; one grapples the Phoenix.", what='the report',
      printings=[k(PEP, '08-20', 4), k(PG, '08-21', 2), k(PJ, '08-21', 2), k(PL, '08-24', 2), k(PP, '08-27', 4), k(NEC, '08-29', 2), k(FJ, '08-31', 3), k(VGB, '09-06', 2)]),
 dict(id='king-speech-may-1776', kind='document_group', label="The King's speech of May 1776", role='published_document', words=50, dateline=False,
      core=[r'My\s+Lords,?\s+and\s+Gentlemen[,.]?\W{0,6}T\s?HE\s+[Cc]onclusion'],
      definition="Printings of George III's speech closing the session of Parliament on 23 May 1776.",
      first="George III's speech closing the session of Parliament on 23 May 1776, brought by the Lord Hyde packet.", what='the speech',
      printings=[k(NYP, '07-18', 4), k(PEP, '08-08', 3), k(PL, '08-10', 3), k(PP, '08-13', 3), (k(PG, '08-14', 1), dict(core=[r'By\s+the\s+Lord\s+Hyde\s+Packet'], note='RevX shortens the passage before the speech with an ellipsis.')), k(FJ, '08-24', 3), k(VGA, '08-24', 2), k(NYG, '09-30', 1)]),
 dict(id='staten-island-conference', kind='context_group', label='Staten Island peace conference',
      definition="Reports of the meeting of a committee of Congress (Franklin, John Adams and Edward Rutledge) with Lord Howe on Staten Island in September 1776: their setting off, and the committee's report to Congress. Contains those two groups.",
      children=['conference-committee-departs', 'conference-committee-report']),
 dict(id='conference-committee-departs', parent='staten-island-conference', kind='message_group', label='Committee sets off to meet Lord Howe', role='report', words=45,
      core=[r'(?:Yesterday|Last\s+Monday|LAST\s+Monday|On\s+Monday\s+last|Monday\s+last)\s+the\s+[Hh]on\w*\.?\s+B\s?enjamin\s+F\s?ranklin'],
      definition="Printings of a Philadelphia report (September 1776) that Franklin, John Adams and Edward Rutledge had set off for New York to confer with Lord Howe.",
      first="A Philadelphia report that Franklin, John Adams and Rutledge have set off for New York to confer with Lord Howe.", what='the report',
      printings=[k(PP, '09-10', 3), (k(PG, '09-11', 3), dict(field=CA)), k(PJ, '09-11', 3), k(PEP, '09-14', 2), k(VGB, '09-20', 2), k(VGA, '09-21', 2), k(FJ, '10-05', 2)]),
 dict(id='conference-committee-report', parent='staten-island-conference', kind='document_group', label="Committee's report on the conference", role='published_document', words=55, dateline=False,
      core=[r'The\s+Committee,?\s+who\s+were\s+appointed\s+to\s+wait\s+on\s+Lord\s+Howe'],
      definition="Printings of the committee's report to Congress on its meeting with Lord Howe on Staten Island, published by order of Congress in September 1776.",
      first="The committee's report to Congress on its meeting with Lord Howe on Staten Island.", what='the report',
      printings=[k(PEP, '09-17', 2), k(PG, '09-18', 2), k(PL, '09-21', 2), k(PP, '09-24', 4), k(VGA, '10-04', 2), k(VGB, '10-04', 2), k(FJ, '10-05', 2)]),
 dict(id='eighty-eight-battalions', kind='document_group', label='Congress orders 88 battalions', role='published_document', words=55,
      core=[CONGRESS+r'Sept\w*\.?,?\s+16'],
      definition="Printings of Congress's resolutions of 16 September 1776 to raise eighty-eight battalions to serve during the war, with each state's quota and the bounties, plus one condensed report.",
      first="Congress's resolutions of 16 September 1776: eighty-eight battalions to serve during the war, with each state's quota.", what='the resolutions',
      printings=[k(PP, '09-24', 2), k(PEP, '09-24', 3), k(PG, '09-25', 3), k(PJ, '09-25', 3), k(PL, '09-28', 4),
                 (k(VGA, '10-04', 7), dict(core=[r'The\s+Hon\.\s+Continental\s+Congress\s+have\s+resolved\s+that\s+88'], role='condensed_report',
                                           note='A short summary giving Virginia\'s quota of 15 battalions; the same paper printed the full resolutions a week later.')),
                 k(VGB, '10-04', 5), k(VGA, '10-11', 4), k(FJ, '10-22', 1)]),
 dict(id='congress-intelligence-october-1776', kind='message_group', label='Intelligence received in Congress, October 1776', role='report', words=55,
      core=[r'I\s?NTELLIGENCE\s+received\s+in\s+C\s?ONGRESS'],
      definition="Printings of the 'Intelligence received in Congress, October 21st, from the Middle and Northern Departments': General Mercer's raid on Staten Island and Arnold's fleet engaging the British on Lake Champlain on 11 October.",
      first="Intelligence received in Congress on 21 October 1776: Mercer's raid on Staten Island, and Arnold's fleet fights the British on Lake Champlain.", what='the intelligence',
      printings=[k(PP, '10-22', 3), k(PEP, '10-22', 1), k(PG, '10-23', 2), k(PJ, '10-23', 2), k(PL, '10-26', 3), k(VGA, '11-01', 2), k(VGB, '11-01', 2)]),
]

MONTHS = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
# A dateline or heading directly before the item, after a sentence boundary: "PHILADELPHIA, July 27."
# "NEW-YORK, Aug. 19." "NORFOLK, (Virginia) January 4." "IN CONGRESS, July 10, 1776." "P H I L A D E L P H I A, April 16."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1776)?\.\s*)$")


def item_start(text, cores, dateline=True, back_to_sentence=False):
    for core in cores:
        m = re.search(core, text, re.I)
        if m:
            start = m.start()
            if back_to_sentence:
                cuts = [(text.rfind(b, 0, start), len(b)) for b in ('. ', '.] ', '] ', '." ', '.” ')]
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
    tokens = list(re.finditer(r'\S+', text[start:]))
    n = min(words, len(tokens))
    # RevX sometimes abridges with an ellipsis; end the excerpt before it rather than run into other text.
    for j in range(15, n):
        if '...' in tokens[j].group() or '…' in tokens[j].group():
            n = j if tokens[j].group().startswith(('...', '…')) else j+1
            break
    else:
        j = None
    # Extend to the end of the clause, if one ends within 15 more words (not across an ellipsis).
    limit = n if j is not None else min(n+15, len(tokens))
    for j in range(n-1, limit):
        if re.search(r'[.;:]["”’)]*$', tokens[j].group()):
            n = j+1
            break
    end_tok = tokens[n-1]
    end = start + end_tok.end()
    excerpt = text[start:end]
    first = None
    for w in range(6, 30):
        candidate = text[start:start+tokens[min(w, n)-1].end()]
        if text.count(candidate) == 1:
            first = candidate
            break
    last_from = tokens[max(0, n-7)].start()
    last = text[start+last_from:end]
    return excerpt, first, last


def printings():
    for s in STORIES:
        for p in s.get('printings', []):
            key, over = (p, {}) if isinstance(p, str) else p
            yield s, key, over


def build_rows(pages):
    rows, problems = [], []
    families = page_families()
    seen = {}
    for s, key, over in printings():
        text_fields = pages[key]['texts']
        cores = over.get('core', s['core'])
        fields = [over['field']] if 'field' in over else [REVX, CA]
        for field in fields:
            text = text_fields.get(field) or ''
            start = item_start(text, cores, over.get('dateline', s.get('dateline', True)), s.get('back_to_sentence', False))
            if start is not None:
                break
        if start is None:
            problems.append((s['id'], key, 'item start not found'))
            continue
        excerpt, first, last = cut_excerpt(text, start, s['words'])
        if not first or text.find(last, start) < 0:
            problems.append((s['id'], key, 'anchors not unique'))
            continue
        lccn, date = key.split('|')[:2]
        story = s['id']
        groups = [story] if 'parent' not in s else [s['parent'], story]
        earlier = seen.get(story, 0)
        seen[story] = earlier + 1
        if earlier == 0:
            summary = s['first']
        else:
            summary = f"{PAPER[lccn]} prints {s['what']}."
        note = over.get('note', '')
        if field == CA and 'field' not in over:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'field': field, 'excerpt_start': first, 'excerpt_end': last, 'excerpt': excerpt,
                     'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['page_key'].split('|')[1], r['page_key']))
    for n, r in enumerate(rows, 1):
        r['id'] = f'S76-{n:03}'
    return rows, problems


def page_families():
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    out = {}
    for a in pq.read_table(RELEASE/'derived/reuse_family_appearances.parquet', columns=['family_id', 'page_id']).to_pylist():
        if a['family_id'].startswith('R1776-'):
            out.setdefault(a['page_id'].split(':', 1)[1].replace(':', '|'), []).append(a['family_id'])
    return {k: sorted(v) for k, v in out.items()}


def build(rows, review):
    findings, crops, boxes, notes = review.get('findings', {}), review.get('crops', {}), review.get('boxes', {}), review.get('notes', {})
    obs = []
    for r in rows:
        note = notes.get(r['id'], r['note']) or ('' if r['earliest'] else 'Same item as the other printings.')
        if r['earliest'] and not note.startswith('Earliest'):
            note = ('Earliest printing found. ' + note).strip()
        o = {'id': r['id'], 'page_key': r['page_key'], 'excerpt_start': r['excerpt_start'], 'excerpt_end': r['excerpt_end'],
             'roles': r['roles'], 'groups': r['groups'], 'summary': r['summary'],
             'note': note,
             'scan_findings': findings.get(r['id'], ['pending']), 'crops': crops.get(r['id'], [])}
        if r['field'] != REVX:
            o['transcription_field'] = r['field']
        if r['family']:
            o['family'] = r['family']
        if r['id'] in boxes:
            o['scan_boxes'] = boxes[r['id']]
        obs.append(o)
    groups = [{'id': s['id'], 'kind': s['kind'], 'label': s['label'], 'definition': s['definition'],
               'admission_rule': 'Reviewed 1776 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    return {
        'ledger_id': 'ledger:stories-1776', 'ledger_version': 1, 'base_release': '0.6.1', 'target_release': '0.7.0',
        'recorded_date': '2026-11-08', 'namespace': 'expansion-1776', 'evidence_dir': 'outputs/story_discovery_1776/evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': 'Single printed items split from the automatic 1776 families, phrase searches on all 2,319 pages in both transcriptions, reading of every printing, and scan checks of each admitted passage',
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             'outputs/story_discovery_1776/items.json': 'retrieval_candidates', 'outputs/story_discovery_1776/phrase_patterns.json': 'retrieval_patterns',
                             'outputs/story_discovery_1776/phrase_hits.json': 'retrieval_candidates', 'work/archive_data/ledgers/make_stories_1776.py': 'ledger_code',
                             'work/archive_data/ledgers/stories_1776_review.json': 'scan_review', 'outputs/story_discovery_1776/SCAN_PROTOCOL.md': 'review_protocol',
                             'outputs/story_discovery_1776/scan_points.json': 'review_protocol'},
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
