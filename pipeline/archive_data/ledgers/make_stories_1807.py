"""Write ledgers/stories_1807.json (v0.7.2 -> v0.8.0): reviewed stories of 1807, the third reviewed year.

The stories were chosen as for 1776 (make_stories_1776.py): the automatic 1807 families were split into single
printed items (work/story_items.py, run with --long-running so that documents inside long-running chains, such as
the President's message of 27 October, are candidates too), every item printed in 7 or more newspapers was read,
and the chosen items were confirmed with phrase searches over all 4,167 pages of 1807 in both transcriptions
(work/story_phrase_search.py). See outputs/story_discovery_1807/README.md.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as
apply_ledger.py does: the excerpt is the opening of the printed item (about 40-60 words), starting with its
dateline or heading when one stands directly before it. Scan findings, crops and hand-drawn boxes are merged from
stories_1807_review.json after the scan check.

Run from the project root with Python 3.12 (needs outputs/story_discovery_1807/search_pages.json, made by
work/year_search_pages.py):
    python work/archive_data/ledgers/make_stories_1807.py [--table]
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PAGES = PROJECT/'outputs/story_discovery_1807/search_pages.json'
REVIEW = HERE/'stories_1807_review.json'
OUT = HERE/'stories_1807.json'
RELEASE = PROJECT/'outputs/data_foundation/v0.7.2'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

ADA, NG, NI, EN, VA, WR = 'sn84024012', 'sn85025815', 'sn83045242', 'sn84024736', 'sn84024710', 'sn86092519'
NHG, PGZ, BJ, HUS, LS, KG = 'sn83025588', 'sn83016082', 'sn85059525', 'sn83021527', 'sn85025609', 'sn84038147'
PAPER = {ADA: 'The Alexandria Daily Advertiser', NG: 'The Norfolk Gazette and Publick Ledger', NI: 'The National Intelligencer',
         EN: 'The Enquirer', VA: 'The Virginia Argus', WR: 'The Wheeling Repository', NHG: 'The New Hampshire Gazette',
         PGZ: 'The Portland Gazette', BJ: 'The Berkeley and Jefferson Intelligencer', HUS: 'The Herald of the United States',
         LS: 'The Lynchburg Star', KG: 'The Kentucky Gazette'}
k = lambda paper, date, page, ed=1: f'{paper}|1807-{date}|{ed}|{page}'

# Story groups, as for 1776. 'printings' lists each printing's page; a tuple adds overrides for that printing:
# core (regexes for the item's first words), role, field, note, words, dateline (include a dateline or heading directly
# before), back (start at the beginning of the sentence that holds the core, for quoted documents).
BELLONA = r'(?:H\s?IS\s+)?M\s?AJESTY.?S\s+S\s?HIP,?\s+B\s?ELLONA[.,]?\s+H\s?ampton\s+R\s?oads[.,]?\s+'
STORIES = [
 # --- Burr's conspiracy and trial -------------------------------------------------------------------------------------
 dict(id='burr-conspiracy-1807', kind='context_group', label="Burr's conspiracy and trial",
      definition="Documents and reports of Aaron Burr's alleged conspiracy and his trial, as the 1807 papers printed them: the President's message to Congress of 22 January, a New York report of news from New Orleans (February), Chief Justice Marshall's opinion on committing Burr (April), the jury's verdict in the treason trial (September), and Marshall's opinion of 20 October after the trial. Contains those five groups; the wider coverage is not included. The message and the reports carry allegations; the jury found the charge of treason not proved.",
      children=['burr-conspiracy-message', 'burr-in-arms-new-orleans', 'marshall-commitment-opinion', 'burr-treason-verdict', 'marshall-october-opinion']),
 dict(id='burr-conspiracy-message', parent='burr-conspiracy-1807', kind='document_group', label="The President's message on the conspiracy", role='published_document', words=55, dateline=False,
      core=[r'T\s?O\s+THE\s+S\s?ENATE,?\s+AND\s+H\s?OUSE\s+OF\s+R\s?EPRESENTATIVES(?:(?!T\s?O\s+THE\s+S\s?ENATE).){0,60}?A\s?GREE?ABL[YE]\s+to\s+the\s+request',
            r'A\s?GREE?ABL[YE]\s+to\s+the\s+request\s+of\s+the\s+House'],
      definition="Printings of President Jefferson's message to Congress of 22 January 1807, sent at the request of the House, on 'an illegal combination of private individuals' against the peace of the Union and a military expedition planned against Spanish territory, with the measures taken to suppress it. It names Aaron Burr as the principal actor. Its enclosures (General Wilkinson's affidavit and letters) are not counted separately.",
      first="President Jefferson's message of 22 January 1807 lays before Congress what he knows of Burr's conspiracy and the measures taken against it.", what="the President's message",
      printings=[k(NI, '01-23', 3), k(ADA, '01-24', 2), (k(VA, '01-27', 5), dict(note='Printed in a Virginia Argus Extra of 27 January.')), k(EN, '01-27', 2), k(NG, '01-30', 2),
                 k(NHG, '02-03', 2), k(BJ, '02-06', 2), k(HUS, '02-07', 1), k(PGZ, '02-09', 1)]),
 dict(id='burr-in-arms-new-orleans', parent='burr-conspiracy-1807', kind='message_group', label="News from New Orleans: 'Burr in arms'", role='report', words=55,
      core=[r'(?:B\s?URR\s+IN\s+A\s?RMS\.?\s+)?Last\s+night\s+(?:the\s+[Ee]ditors\s+)?(?:of\s+the\s+N\w*\.?\s*-?\s*York\s+Gazette,?\s+)?(?:we\s+)?received\s+the\s+following\s+interesting'],
      definition="Printings of a New York report (3 February 1807) of news from New Orleans brought by the brig Neptune: General Wilkinson had refused Burr passage, the city was under arms, and Burr was said to be at Natchez with 600 men and an advanced guard of 200 cavalry. The numbers are a report, not an observed fact.",
      first="A New York report of news from New Orleans by the brig Neptune: Wilkinson refuses Burr passage, and the city is put under arms.", what='the report',
      printings=[k(NG, '02-06', 2), k(ADA, '02-07', 3), k(NI, '02-09', 2), k(NHG, '02-10', 3), k(VA, '02-10', 3), k(EN, '02-13', 3), k(BJ, '02-13', 3), k(HUS, '02-14', 3), k(LS, '02-19', 2)]),
 dict(id='marshall-commitment-opinion', parent='burr-conspiracy-1807', kind='document_group', label="Marshall's opinion on committing Burr", role='published_document', words=55, dateline=False,
      core=[r'I\s+A\s?M\s+required\s+on\s+the\s+part\s+of\s+the\s+[Aa]ttorney'],
      definition="Printings of Chief Justice Marshall's opinion of 1 April 1807 at Richmond on the motion to commit Aaron Burr on two charges: he committed him for setting on foot an expedition against Spanish territory, a misdemeanor, but not for treason, finding no proof yet that war had been levied. Includes one printing of a summary of the opinion.",
      first="Chief Justice Marshall's opinion at Richmond, 1 April 1807, on the motion to commit Burr for treason and for an expedition against Spanish territory.", what="Marshall's opinion",
      printings=[k(VA, '04-03', 2), k(EN, '04-03', 3), k(ADA, '04-06', 2), k(NI, '04-08', 2), k(NG, '04-08', 2), k(LS, '04-16', 1), k(WR, '04-23', 4),
                 (k(BJ, '04-24', 2), dict(core=[r'On\s+Wednesday,?\s+the\s+1st\s+day\s+of\s+April,?\s+Chief\s+Justice\s+Marshall'], role='condensed_report', words=60,
                                          note="A summary of the opinion in a Richmond report of 4 April, with the names of Burr's sureties."))]),
 dict(id='burr-treason-verdict', parent='burr-conspiracy-1807', kind='document_group', label="The verdict: 'not proved to be guilty'", role='quoted_document', words=62, dateline=False,
      core=[r'The\s+[Jj]ury\s+(?:then\s+)?retired,?\s+and\s+after\s+an\s+absence', r'The\s+[Jj]ury\s+then\s+withdrew'],
      definition="Printings of the jury's written verdict in Aaron Burr's trial for treason at Richmond on 1 September 1807, 'We of the jury find that Aaron Burr is not proved to be guilty under this indictment by any evidence submitted to us. We therefore find him not guilty', quoted in accounts of that day's proceedings, with Burr's objection to its form. Three different accounts carry it; most papers printed the same one.",
      first="An account of the court at Richmond on 1 September 1807: the jury finds that Burr is 'not proved to be guilty' of treason, and he objects to the form of the verdict.", what="the jury's verdict",
      printings=[k(VA, '09-02', 3),
                 (k(NI, '09-04', 3), dict(core=[r'The\s+jury\s+accordingly\s+retired'], note="The National Intelligencer's own account of the day.")),
                 k(ADA, '09-04', 2), k(NG, '09-04', 2), k(EN, '09-05', 2),
                 (k(NI, '09-07', 1), dict(core=[r'The\s+jury\s+accordingly\s+retired'], note='The same account printed again three days later.')),
                 (k(LS, '09-10', 3), dict(core=[r'IN\s+BURR.S\s+AFFAIR'], note="The account most papers printed. The page is torn, and the transcription keeps only fragments of these lines.")),
                 (k(NI, '09-11', 1), dict(note="The account most papers printed, a week after this paper's own.")),
                 k(BJ, '09-11', 2), k(PGZ, '09-14', 2), k(NHG, '09-15', 3)]),
 dict(id='marshall-october-opinion', parent='burr-conspiracy-1807', kind='document_group', label="Marshall's opinion of 20 October", role='published_document', words=55, dateline=False,
      core=[r'Conclusive\s+O\s?PINION\s+of\s+the\s+C\s?HIEF\s+J\s?USTICE', r'O\s?PINION\s+OF\s+C\s?HIEF\s+J\s?USTICE\s+M\s?ARSHALL,?\s+Delivered\s+the\s+20th'],
      definition="Printings of Chief Justice Marshall's opinion of 20 October 1807 at Richmond, after the treason trial, on the motion to commit Burr, Blennerhassett and Israel Smith to be tried elsewhere for treason and misdemeanor: he held it improper to commit them on the charge of treason, and committed Burr and Blennerhassett for preparing and providing the means for a military expedition. Includes printings of a Richmond report that quotes the opinion's conclusion.",
      first="A Richmond report of 20 October 1807: Chief Justice Marshall holds it improper to commit Burr for treason, and commits him and Blennerhassett for preparing a military expedition.", what="Marshall's opinion",
      printings=[(k(EN, '10-20', 3), dict(core=[r'The\s+court\s+has\s+just\s+delivered\s+a\s+long\s+and\s+elaborate\s+opinion'], role='document_excerpt', words=68,
                                          note="A report from the court at twelve o'clock that quotes the opinion's conclusion; the full opinion follows in this paper on 23 October.")),
                 (k(NI, '10-23', 3), dict(core=[r'The\s+court\s+has\s+just\s+delivered\s+a\s+long\s+and\s+elaborate\s+opinion'], role='document_excerpt', words=68, note="The Richmond report that quotes the opinion's conclusion.")),
                 (k(ADA, '10-23', 3), dict(core=[r'The\s+court\s+has\s+just\s+delivered\s+a\s+long\s+and\s+elaborate\s+opinion'], role='document_excerpt', words=68, note="The Richmond report that quotes the opinion's conclusion.")),
                 k(EN, '10-23', 1), k(NG, '10-26', 2), k(VA, '10-27', 2),
                 (k(BJ, '10-30', 3), dict(core=[r'The\s+court\s+has\s+just\s+delivered\s+a\s+long\s+and\s+elaborate\s+opinion'], role='document_excerpt', words=68, note="The Richmond report that quotes the opinion's conclusion.")),
                 (k(PGZ, '11-02', 2), dict(core=[r'The\s+court\s+has\s+just\s+delivered\s+a\s+long\s+and\s+elaborate\s+opinion'], role='document_excerpt', words=68, note="The Richmond report that quotes the opinion's conclusion.")),
                 (k(NHG, '11-03', 2), dict(core=[r'The\s+court\s+has\s+just\s+delivered\s+a\s+long\s+and\s+elaborate\s+opinion'], role='document_excerpt', words=64, note="The Richmond report that quotes the opinion's conclusion.")),
                 k(WR, '11-12', 3)]),
 # --- The treaty agreed in London --------------------------------------------------------------------------------------
 dict(id='monroe-pinkney-treaty-letter', kind='document_group', label='Monroe and Pinkney: a treaty agreed', role='published_document', words=55, dateline=False,
      core=[r'L\s?ONDON,?\s+Dec\w*\.?,?\s+27,?\s+1806', r'Dec\w*\.?\s+27,?\s+1806\W+S\s?IR', r'(?:S\s?IR\W+)?W\s?E\s+have\s+the\s+pleasure\s+to\s+acquaint\s+you,?\s+(?:that\s+)?we\s+have\s+this\s+day'],
      definition="Printings of the letter of James Monroe and William Pinkney from London, 27 December 1806, to the Secretary of State: they had agreed with the British commissioners to conclude a treaty on all the points of their negotiation, on terms they trusted the government would approve. The President sent it to Congress on 19 February 1807. Several papers printed it again in October and November, after the treaty had been set aside.",
      first="Monroe and Pinkney write from London (27 December 1806) that they have agreed with the British commissioners to conclude a treaty, as the President told Congress on 19 February.", what="the ministers' letter",
      printings=[k(NI, '02-20', 2), k(ADA, '02-20', 3), k(EN, '02-24', 3), k(NG, '02-27', 2), k(LS, '03-05', 2), k(BJ, '03-06', 2), k(HUS, '03-07', 1), k(NHG, '03-10', 2), k(WR, '03-12', 6),
                 (k(ADA, '10-02', 3), dict(note='Printed again in October, with the words on all the points of the negotiation set in capitals.')),
                 (k(NG, '10-07', 2), dict(note='Printed again in October, with the words on all the points of the negotiation set in capitals.')),
                 (k(PGZ, '10-12', 2), dict(note='First printed in this paper in October, with the words on all the points of the negotiation set in capitals.')),
                 (k(NG, '11-02', 2), dict(note='Printed a third time in this paper, set as a quotation, with the same words in capitals.')),
                 (k(ADA, '11-05', 2), dict(note="Printed a third time in this paper, now with 'on all the points which have formed the object of our negociation' in italics and 'WE TRUST OUR GOVERNMENT WILL APPROVE' in capitals."))]),
 # --- War in Europe ----------------------------------------------------------------------------------------------------
 dict(id='lubeck-stormed', kind='message_group', label='Lübeck stormed', role='report', words=50,
      core=[r'The\s+6th\s+of\s+this\s+month\s+was\s+the\s+most\s+dreadful'],
      definition="Printings of a report from Lübeck (9 or 10 November 1806) of the French attack of 6 November, which took the town from the Prussians: 'the most dreadful day in the annals of Lubeck'.",
      first="A report from Lübeck: the French storm the town on 6 November 1806, 'the most dreadful day in the annals of Lubeck'.", what='the report',
      printings=[k(HUS, '01-31', 1), k(PGZ, '02-02', 2), k(ADA, '02-02', 3), k(NG, '02-04', 3), k(NI, '02-06', 3), k(VA, '02-06', 2), k(EN, '02-06', 1), k(BJ, '02-06', 3)]),
 dict(id='harford-jones-russian-army', kind='message_group', label='Sir Harford Jones on the Russian army', role='report', words=50,
      core=[r'From\s+the\s+Liverpool\s+Advertiser,?\s+Jan\w*\.?\s+\d+\.?\s+Sir\s+H', r'Sir\s+H\w+ford\s+Jones,?\s+has'],
      definition="Printings of a London paragraph of January 1807: Sir Harford Jones, back from the Russian headquarters, had never seen an army in a higher state of discipline or more eager to meet the enemy, with news of the Russian columns and of the French crossing the Vistula. It is one witness's account. Two versions circulated, dated London 6 January and 'From the Liverpool Advertiser'.",
      first="A London report: Sir Harford Jones, back from the Russian headquarters, never saw an army in a higher state of discipline.", what='the report',
      printings=[k(ADA, '03-03', 3), k(NI, '03-06', 2), (k(ADA, '03-06', 3), dict(note='The London version, three days after this paper printed the Liverpool one.')), k(HUS, '03-07', 2),
                 k(PGZ, '03-09', 2), (k(NG, '03-09', 2), dict(note='A variant dated London, 5 January, in which Jones presents a letter of credence from the Russian court.')),
                 k(NHG, '03-10', 2), k(EN, '03-10', 2), k(VA, '03-13', 2), k(LS, '03-19', 1), k(WR, '03-19', 4), k(BJ, '03-20', 2)]),
 dict(id='bennigsen-pultusk-account', kind='document_group', label="Bennigsen's account of Pultusk", role='published_document', words=55,
      core=[r'B\s?ATTLE\s+OF\s+P\s?ULTUSK\.?\s+R\s?ussian', r'R\s?ussian\s+O\s?fficial\s+A\s?ccount[.,]?\s+(?:G\s?en\w*\.?\s+)?B\s?en\w+\s+to\s+the\s+K',
            r'(?:G\s?en\w*\.?\s+)?B\s?en\w+\s+to\s+the\s+K\s?ing\s+of\s+P\s?russia', r'I\s+H\s?AVE\s+the\s+happiness\s+most\s+respectfully', r'T\s?O\s+THE\s+K\s?ING\s+OF\s+P\s?RUSSIA\.?\s+S\s?IR'],
      definition="Printings of General Bennigsen's report to the King of Prussia on the battle of Pultusk (26 December 1806), the Russian official account, in which he writes that he repulsed the French attack on every point.",
      first="General Bennigsen reports to the King of Prussia that he repulsed the French at Pultusk: the Russian official account.", what="Bennigsen's account",
      printings=[k(NHG, '03-17', 2), k(HUS, '03-21', 2), k(NI, '03-25', 2), k(ADA, '03-25', 3), k(NG, '03-30', 1), k(VA, '03-31', 2), k(EN, '03-31', 1), k(BJ, '04-03', 1), k(LS, '04-09', 1)]),
 dict(id='bulletin-66', kind='document_group', label="The French army's 66th bulletin", role='published_document', words=50, dateline=False,
      core=[r'S\s?IXTY.S\s?IXTH\s+B\s?ULLETIN(?:\s+OF\s+THE\s+G\s?RAND\s+A\s?RMY)?\.?\s+\w+\.?,?\s+March\s+14'],
      definition="Printings of the 66th bulletin of the French Grand Army (Osterode, 14 March 1807): the army rests in cantonments, with skirmishes between the outposts. New York papers had it by the brig Alonzo from Bordeaux, with the 65th.",
      first="The 66th bulletin of the French Grand Army, from Osterode, 14 March 1807: the army rests in cantonments.", what='the bulletin',
      printings=[k(ADA, '05-18', 2), k(EN, '05-19', 3), k(NI, '05-20', 1), k(VA, '05-20', 2), k(NG, '05-20', 2),
                 (k(BJ, '05-22', 2), dict(note="The paper prints the 65th bulletin just before, headed 'SIXTY-FIFTH BULLETIN.'; the RevX transcription puts the 66th's heading over it.")),
                 k(HUS, '05-23', 1), k(PGZ, '05-25', 2), k(NHG, '05-26', 2)]),
 dict(id='bulletin-78', kind='document_group', label='The 78th bulletin: the action of Spanden', role='document_excerpt', words=55, dateline=False,
      core=[r'F\s?RENCH\s+G\s?RAND\s+A\s?RMY\s+B\s?ULLETIN', r'This\s+Bulletin\s+gives\s+an\s+account', r'A\s?CTION\s+OF\s+S\s?PANDEN'],
      definition="Printings of an abstract of the 78th bulletin of the French Grand Army (Heilsberg, 12 June 1807), received at Boston from Nantes: the overtures of peace made in the winter, broken off by the Russian attacks, and the action of Spanden on 5 June.",
      first="An abstract of the 78th bulletin of the French Grand Army (12 June 1807): the overtures of peace in the winter, and the Russian attack at Spanden.", what='the abstract of the bulletin',
      printings=[k(HUS, '08-15', 2), k(PGZ, '08-17', 2), k(NHG, '08-18', 2), k(ADA, '08-18', 2), k(NI, '08-19', 2), k(EN, '08-21', 1), k(NG, '08-21', 3), k(VA, '08-22', 2), k(BJ, '09-04', 2)]),
 dict(id='armistice-france-russia', kind='document_group', label='Armistice between France and Russia', role='published_document', words=55, dateline=False,
      core=[r'A\s?RMISTICE\s+BETWEEN\s+F\s?RANCE', r'(?:As\s+)?[Hh]is\s+[Mm]ajesty\s+the\s+Emperor\s+of\s+the\s+French(?:(?!Emperor\s+of\s+the\s+French).){0,220}?resolved\s+to\s+conclude\s+an\s+[Aa]rmistice',
            r'(?:The\s+)?two\s+nations,?\s+they\s+have\s+in\s+the\s+mean\s+time\s+resolved'],
      definition="Printings of the armistice between the French and Russian armies agreed at Tilsit on 21 June 1807 (signed by Berthier and Prince Labanoff), the preliminary to the peace.",
      first="The armistice between the French and Russian armies, agreed at Tilsit on 21 June 1807.", what='the armistice',
      printings=[(k(PGZ, '09-07', 1), dict(note='Begins at the foot of page 1 and continues on page 2.')), k(NHG, '09-08', 2), k(ADA, '09-08', 2), k(NI, '09-09', 2), k(NG, '09-11', 1), k(VA, '09-12', 2), k(EN, '09-12', 1), k(BJ, '09-18', 1)]),
 # --- The Driver at Charleston ----------------------------------------------------------------------------------------
 dict(id='driver-at-charleston', kind='context_group', label='The Driver at Charleston',
      definition="Reports of the British sloop of war Driver, which the President had barred from American ports, anchoring in Charleston harbour in April and May 1807: the commandant of Fort Johnson's demand that she leave, and her commander's answer. Contains those two groups.",
      children=['kalteisen-letter-driver', 'driver-answer-charleston']),
 dict(id='kalteisen-letter-driver', parent='driver-at-charleston', kind='message_group', label='Fort Johnson orders the Driver out', role='report', words=55,
      core=[r'F\s?ort\s+J\s?ohnson[.,]?\s+H\s?arbou?r\s+of\s+C\s?harleston', r'The\s+President\s+of\s+the\s+U[\w.\s]{1,12}of\s+America,?\s+having,?\s+by\s+proclamation'],
      definition="Printings of the letter of Captain Michael Kalteisen, commandant of Fort Johnson in Charleston harbour (2 May 1807), to the commander of the British sloop of war Driver, which a proclamation of the President had barred from American harbours: she must leave within twenty-four hours. Most papers printed it inside a Charleston report of the Driver's arrival, reprinted from New York; the papers give the proclamation different dates.",
      first="The commandant of Fort Johnson writes to the Driver, barred from American harbours, that she must leave Charleston within 24 hours.", what="the commandant's letter",
      printings=[k(NI, '05-15', 3), k(EN, '05-15', 3), k(NG, '05-15', 3), k(HUS, '05-16', 3), k(VA, '05-16', 2), k(PGZ, '05-18', 2),
                 (k(VA, '05-20', 3), dict(note='Printed again four days after its first printing in this paper, above the Driver\'s answer.')), k(BJ, '05-22', 3)]),
 dict(id='driver-answer-charleston', parent='driver-at-charleston', kind='message_group', label="The Driver's commander answers", role='report', words=55, dateline=False,
      core=[r'H\.?\s*M\.?\s*S\.?\s+D\s?RIVER', r'R\s?EBELLION\s+R\s?OADS?[.,]?\s+(?:C\s?harleston,?\s+)?M\s?AY\s+3', r'S\s?IR\W+I\s+H\s?AVE\s+received\s+your\s+letter;?,?\s+and\s+having\s+some\s+doubts'],
      definition="Printings of the answer of Captain William Love, commanding the British sloop of war Driver (Rebellion Roads, Charleston, 3 May 1807), to Captain Kalteisen: he doubted the authority by which the demand was written, knew nothing of a proclamation of May 1807, and would not leave until ready.",
      first="Captain Love of the Driver answers the commandant of Fort Johnson: he doubts the authority of the demand and knows nothing of the proclamation cited.", what="the Driver's answer",
      printings=[k(ADA, '05-19', 3), k(EN, '05-19', 3), k(NI, '05-20', 2), k(VA, '05-20', 3), k(NG, '05-20', 2), k(HUS, '05-23', 2), k(PGZ, '05-25', 2), k(BJ, '05-29', 3)]),
 # --- The Chesapeake affair -------------------------------------------------------------------------------------------
 dict(id='chesapeake-affair-1807', kind='context_group', label='The Chesapeake affair',
      definition="Documents and reports of the attack of the British ship Leopard on the American frigate Chesapeake off the Virginia capes on 22 June 1807, and its aftermath, as the 1807 papers printed them: the National Intelligencer's account, the President's proclamation of 2 July, Admiral Berkeley's order, the opinion of the court of inquiry on Commodore Barron, and the House committee's report. Contains those five groups; the wider coverage is not included.",
      children=['chesapeake-attack-account', 'july-2-proclamation', 'berkeley-order', 'chesapeake-court-of-inquiry', 'house-report-chesapeake']),
 dict(id='chesapeake-attack-account', parent='chesapeake-affair-1807', kind='message_group', label="The National Intelligencer's account of the attack", role='report', words=55,
      core=[r'B\s?RITISH\s+O\s?UTRAGE', r'We\s+give\s+the\s+public'],
      definition="Printings of the National Intelligencer's account of 26 June 1807, headed 'British Outrage': the Leopard, one of the British squadron at the capes, followed the Chesapeake out to sea, demanded three men said to be deserters, and fired on her until she struck.",
      first="The National Intelligencer's account of 26 June: the British ship Leopard fires on the frigate Chesapeake off the capes and takes men from her.", what='the account',
      printings=[k(NI, '06-26', 3), k(ADA, '06-27', 2), k(VA, '07-01', 2), k(NG, '07-01', 2), k(BJ, '07-03', 2),
                 (k(HUS, '07-04', 2), dict(field=CA, core=[r'B\s?RITISH\s+O\s?UTRAGE'], words=45,
                                          note="The RevX transcriptions of this issue are shifted by one page against the scans: this account, on page 2 of the scan, is filed under page 1 in RevX. The excerpt comes from the older CA transcription of page 2.")),
                 (k(PGZ, '07-06', 2), dict(note="Adds '(says Mr. Jefferson's official paper)' to the opening sentence.")), k(NHG, '07-07', 2)]),
 dict(id='july-2-proclamation', parent='chesapeake-affair-1807', kind='document_group', label="The President's proclamation of 2 July", role='published_document', words=55, dateline=False,
      core=[r'(?:B\s?Y\s+)?T\s?HOMAS\s+J\s?EFFERSON,?\s+P\s?RESIDENT', r'A\s+P\s?ROCLAMATION\.?\s+(?:Washington.City,?\s+July\s+2,?\s+1807\.?\s+)?D\s?URING\s+the\s+wars?', r'D\s?URING\s+the\s+wars?\s+which,?\s+for\s+some\s+time'],
      definition="Printings of President Jefferson's proclamation of 2 July 1807, which recited the attack on the Chesapeake and required all armed vessels bearing commissions under the British government to leave the harbours and waters of the United States, forbidding all intercourse with them.",
      first="President Jefferson's proclamation of 2 July 1807 orders British armed vessels out of American waters after the attack on the Chesapeake.", what="the President's proclamation",
      printings=[(k(NI, '07-03', 2), dict(note='Printed first in an extra paper the night before, as the paper says; republished here.')), k(ADA, '07-03', 3), k(EN, '07-07', 1), k(NG, '07-08', 2),
                 k(BJ, '07-10', 2), k(HUS, '07-11', 2), k(PGZ, '07-13', 2), (k(NHG, '07-14', 2), dict(core=[r'D\s?URING\s+the\s+wars?\s+which'])), k(WR, '07-23', 2)]),
 dict(id='berkeley-order', parent='chesapeake-affair-1807', kind='document_group', label="Admiral Berkeley's order", role='published_document', words=55,
      core=[r'B\s?Y\s+the\s+(?:h\s?ono?u?rable|h\s?on\.?)\s+(?:G\s?eo\.?\s+)?G\s?EORGE\s+[\w.]+\s+B\s?ERKELEY'],
      definition="Printings of the order of Vice-Admiral George Cranfield Berkeley, British commander in chief at Halifax (1 June 1807), directing the captains under his command, if they met the Chesapeake at sea, to show her captain the order and search her for the deserters named in its margin. American papers printed it from late July.",
      first="Admiral Berkeley's order of 1 June 1807: his captains are to search the Chesapeake at sea for British deserters.", what="Berkeley's order",
      printings=[k(ADA, '07-28', 2), k(NI, '07-29', 3), k(EN, '07-31', 2), k(NG, '07-31', 2), k(HUS, '08-01', 3), k(VA, '08-01', 3), k(PGZ, '08-03', 1), k(BJ, '08-07', 2),
                 (k(NG, '09-30', 1), dict(note='Printed again two months later, after a question whether the court of inquiry would make the order part of its report.'))]),
 dict(id='chesapeake-court-of-inquiry', parent='chesapeake-affair-1807', kind='document_group', label='The court of inquiry on the Chesapeake', role='published_document', words=55, dateline=False,
      core=[r'A\s?T\s+a\s+C\s?ourt\s+of\s+(?:I|E)\s?nquiry', r'C\s?ourt\s+of\s+(?:I|E)\s?nquiry,?\s+(?:assembled|held|convened)\s+on\s+board'],
      definition="Printings of the opinion of the naval court of inquiry held on board the Chesapeake at Norfolk (5 October to 4 November 1807) on the conduct of Commodore James Barron: among other findings, that the Chesapeake was prematurely surrendered when she was nearly prepared for battle. Includes one printing of its conclusion only.",
      first="The opinion of the court of inquiry on board the Chesapeake at Norfolk, October to November 1807, on Commodore Barron's conduct.", what="the court's opinion",
      printings=[k(NI, '11-16', 2), k(ADA, '11-17', 2), k(VA, '11-20', 2), k(EN, '11-20', 2), k(NG, '11-23', 2), k(BJ, '11-27', 1), k(PGZ, '11-30', 2), k(WR, '12-03', 3),
                 (k(NHG, '12-08', 1), dict(core=[r'25\W+The\s+[Cc]ourt\s+is\s+therefore\s+of\s+the\s+opinion'], back=True, role='document_excerpt',
                                           note="Quotes the court's 25th finding inside an editorial, 'The Court of Inquiry' (credited to the Democratic Press), which also quotes the 20th."))]),
 dict(id='house-report-chesapeake', parent='chesapeake-affair-1807', kind='document_group', label="The House committee's report", role='document_excerpt', words=53, dateline=False,
      core=[r'Mr\.?\s+Blount,?\s+from\s+the\s+committee\s+to\s+whom\s+was\s+referred\s+so\s+much\s+of\s+the\s+message\s+of\s+the\s+President\s+as\s+relates\s+to\s+aggressions,?\s+&c\.?\s+made',
            r'The\s+report\s+commences\s+with\s+an\s+expression'],
      definition="Printings of a summary of the report made to the House on 17 November 1807 by Mr. Blount for the committee on the part of the President's message relating to aggressions, with the report's conclusion quoted: the outrage on the Chesapeake 'has been stamped with circumstances of indignity and insult' with scarcely a parallel.",
      first="The House committee on aggressions reports on 17 November: the attack on the Chesapeake was an outrage 'stamped with circumstances of indignity and insult'.", what='the summary of the report',
      printings=[k(NI, '11-18', 2), k(ADA, '11-21', 3), k(VA, '11-24', 2), k(EN, '11-24', 3), k(NG, '11-25', 2), k(BJ, '11-27', 3), k(NHG, '12-01', 2), (k(WR, '12-10', 6), dict(words=28))]),
 # --- Commodore Douglas and the Mayor of Norfolk ----------------------------------------------------------------------
 dict(id='douglas-and-the-mayor-of-norfolk', kind='context_group', label='Commodore Douglas and the Mayor of Norfolk',
      definition="The letters exchanged in July 1807 between Commodore John E. Douglas, commanding the British squadron in Hampton Roads, and Richard E. Lee, Mayor of Norfolk, over the Norfolk committee's ban on communication with the British ships, with the report of Littleton W. Tazewell, who carried the Mayor's answer. Contains those four groups.",
      children=['douglas-letter-3-july', 'mayor-answer-4-july', 'tazewell-report', 'douglas-letter-6-july']),
 dict(id='douglas-letter-3-july', parent='douglas-and-the-mayor-of-norfolk', kind='message_group', label="Commodore Douglas's letter of 3 July", role='report', words=55, dateline=False,
      core=[BELLONA + r'July\s+3'],
      definition="Printings of Commodore Douglas's letter to the Mayor of Norfolk (Bellona, Hampton Roads, 3 July 1807): unless the committee's resolution forbidding communication with the British consul and ships was annulled, he would stop every vessel bound in or out of Norfolk; it rested with the inhabitants 'either to engage in a war or remain on terms of peace'.",
      first="Commodore Douglas writes to the Mayor of Norfolk from the Bellona: unless the ban on communication is annulled, he will stop all vessels in or out of Norfolk.", what="Douglas's letter",
      printings=[k(NG, '07-06', 2), k(EN, '07-07', 2), k(ADA, '07-09', 2), (k(NI, '07-10', 3), dict(core=[r'Majesty.?s\s+Ship\s+Bel\w+\s*,?\s+Hampton\s+Roads,?\s+July\s+3'])), k(BJ, '07-17', 2), k(HUS, '07-18', 2), k(PGZ, '07-20', 2), k(NHG, '07-21', 2), k(WR, '07-30', 1)]),
 dict(id='mayor-answer-4-july', parent='douglas-and-the-mayor-of-norfolk', kind='message_group', label="The Mayor's answer of 4 July", role='report', words=55, dateline=False,
      core=[r'(?:A\s?NSWER\.?\s+)?N\s?ORFOLK,?\s+J\s?ULY\s+4,?\s+1807\.?\W+S\s?IR\W+I\s+H\s?AVE\s+received'],
      definition="Printings of the answer of Richard E. Lee, Mayor of Norfolk, to Commodore Douglas (4 July 1807): 'the American people are not to be intimidated by menace'; the ban was an act of individuals, not of the government, and the inhabitants would protect themselves against any aggression.",
      first="The Mayor of Norfolk answers Commodore Douglas on 4 July: the American people are not to be intimidated by menace.", what="the Mayor's answer",
      printings=[k(NG, '07-06', 2), k(EN, '07-07', 2), k(ADA, '07-09', 2), k(NI, '07-10', 3), k(BJ, '07-17', 2), k(HUS, '07-18', 2), k(PGZ, '07-20', 2), k(NHG, '07-21', 2), k(WR, '07-30', 2)]),
 dict(id='tazewell-report', parent='douglas-and-the-mayor-of-norfolk', kind='message_group', label="Tazewell's report to the Mayor", role='report', words=55, dateline=False,
      core=[r'N\s?orfolk,?\s+July\s+5,?\s+1807\.?\s+S\s?IR', r'T\s?O\s+THE\s+M\s?AYOR\.?\s+S\s?IR', r'I\s?N\s+pursuance\s+of\s+your\s+request,?\s+I\s+this\s+day'],
      definition="Printings of the report of Littleton W. Tazewell to the Mayor of Norfolk (5 July 1807) on delivering the Mayor's answer on board the Bellona: Douglas said his letter had been misapprehended and that he intended no menace. Includes one shorter account of the report.",
      first="Littleton W. Tazewell reports to the Mayor of Norfolk: on board the Bellona, Douglas says his letter was misapprehended and meant no menace.", what="Tazewell's report",
      printings=[k(NG, '07-08', 2), k(VA, '07-11', 2), k(EN, '07-11', 2), k(NI, '07-13', 3), k(ADA, '07-13', 3), k(BJ, '07-17', 3), k(PGZ, '07-20', 2),
                 (k(WR, '07-30', 2), dict(core=[r'The\s+following\s+sketch\s+may\s+serve'], back=True, role='condensed_report', words=60,
                                          note="A shorter account of Tazewell's report, 'to give an idea of what passed at the interview'."))]),
 dict(id='douglas-letter-6-july', parent='douglas-and-the-mayor-of-norfolk', kind='message_group', label="Commodore Douglas's letter of 6 July", role='report', words=55, dateline=False,
      core=[BELLONA + r'(?:J\s?uly\s+6|6th\s+J\s?uly)', r'I\s+have\s+the\s+hono\w*\s+to\s+acknowledge\s+the\s+receipt\s+of\s+your\s+letter\s+of\s+the\s+4th'],
      definition="Printings of Commodore Douglas's second letter to the Mayor of Norfolk (Bellona, Hampton Roads, 6 July 1807): every circumstance had been discussed with the gentlemen who carried the Mayor's answer, and he would use every exertion, consistent with the honour of the British flag, toward an amicable end.",
      first="Commodore Douglas's second letter to the Mayor of Norfolk, 6 July: he will work for an amicable end, consistent with the honour of the British flag.", what="Douglas's second letter",
      printings=[k(NG, '07-08', 2), k(VA, '07-11', 2), k(EN, '07-11', 2), k(NI, '07-13', 3), k(ADA, '07-13', 3), k(BJ, '07-17', 3), k(HUS, '07-18', 3), k(PGZ, '07-20', 2), k(NHG, '07-21', 2)]),
 # --- Congress called early -------------------------------------------------------------------------------------------
 dict(id='special-session-1807', kind='context_group', label='Congress called early, 1807',
      definition="The President's proclamation of 30 July 1807 calling Congress to meet on 26 October instead of in December, and his message to the session on 27 October. Contains those two groups.",
      children=['proclamation-convening-congress', 'president-message-october-27']),
 dict(id='proclamation-convening-congress', parent='special-session-1807', kind='document_group', label='The proclamation calling Congress', role='published_document', words=55, dateline=False,
      core=[r'B\s?Y\s+the\s+P\s?RESIDENT[^.]{0,60}?A\s?MERICA,?\s+A\s+P\s?ROCLAMATION', r'A\s+P\s?ROCLAMATION\.?\s+W\s?HEREAS\s+great', r'W\s?HEREAS\s+great\s+and\s+weighty\s+matters'],
      definition="Printings of President Jefferson's proclamation of 30 July 1807 that 'great and weighty matters' required Congress to meet at Washington on Monday 26 October. The National Intelligencer printed it seven times, as a standing notice.",
      first="President Jefferson's proclamation of 30 July 1807 calls Congress to meet on 26 October.", what='the proclamation',
      printings=[k(NI, '07-31', 3), k(ADA, '08-01', 3), k(EN, '08-04', 2), (k(NI, '08-05', 3), dict(note='Printed again as a standing notice (second printing in this paper).')),
                 k(VA, '08-05', 2), k(NG, '08-05', 2), (k(NI, '08-07', 4), dict(note='Printed again as a standing notice (third printing in this paper).')), k(BJ, '08-07', 3),
                 k(HUS, '08-08', 3), k(PGZ, '08-10', 2), (k(NI, '08-10', 4), dict(note='Printed again as a standing notice (fourth printing in this paper).')), k(NHG, '08-11', 2),
                 (k(NI, '08-12', 4), dict(note='Printed again as a standing notice (fifth printing in this paper).')),
                 (k(NI, '08-14', 4), dict(note='Printed again as a standing notice (sixth printing in this paper).')),
                 (k(NI, '08-17', 4), dict(note='Printed again as a standing notice (seventh printing in this paper).'))]),
 dict(id='president-message-october-27', parent='special-session-1807', kind='document_group', label="The President's message of 27 October", role='published_document', words=55, dateline=False,
      core=[r'T\s?O\s+THE\s+S\s?ENATE\s+AND\s+H\s?OUSE\s+OF\s+R\s?EPRESENTATIVES(?:(?!T\s?O\s+THE\s+S\s?ENATE).){0,50}?C\s?IRCUMSTANCES', r'C\s?IRCUMSTANCES,?\s+fellow.?citizens'],
      definition="Printings of President Jefferson's message to Congress at the opening of the special session, 27 October 1807: the British answer on the treaty, the attack on the Chesapeake and the proclamation that followed, the defence of the ports, the Burr trials, the finances, and the Indian nations.",
      first="President Jefferson's message of 27 October 1807 to the special session: circumstances which seriously threatened the peace of the country.", what="the President's message",
      printings=[k(NI, '10-27', 3), k(ADA, '10-28', 3), (k(EN, '10-30', 1, 2), dict(note='Printed in an Enquirer Extra of 30 October.')), k(NG, '11-02', 2), k(NHG, '11-03', 2),
                 k(BJ, '11-06', 2), k(PGZ, '11-09', 1), k(WR, '11-12', 1)]),
 # --- Britain and France against American ships -----------------------------------------------------------------------
 dict(id='britain-answer-peace-or-war', kind='message_group', label="London: 'the question of peace or war'", role='report', words=55,
      # The heading AMERICA. in capitals only: VA's preceding sentence ends "...our Minister in America."
      core=[r'(?:(?-i:A\s?MERICA)\.?\s+(?:—\s*)?)?(?:The|That)\s+most\s+important\s+matter,?\s+the\s+question\s+of\s+peace\s+or\s+war'],
      definition="Printings of a London paragraph of October 1807: the British ministers had delivered to Monroe and Pinkney their final answer on the leading points in dispute, so that 'the question of peace or war with America' was decided as far as it could be in England, and Monroe was preparing to leave. It is a London paper's report and forecast.",
      first="A London report of 12 October 1807: Britain's ministers have given Monroe and Pinkney their final answer, and 'the question of peace or war with America' is decided there.", what='the report',
      printings=[k(PGZ, '11-23', 2), k(NHG, '11-24', 2), k(NI, '11-27', 3), k(ADA, '11-27', 3), k(VA, '12-01', 3), k(EN, '12-01', 3), k(NG, '12-02', 3), k(BJ, '12-04', 3)]),
 dict(id='antwerp-letter-capture-order', kind='message_group', label='An Antwerp letter: ships to or from England to be taken', role='report', words=62,
      core=[r'(?:Extract|Excerpt)\s+of\s+a\s+letter\s+from\s+a\s+house\s+of\s+the\s+first\s+respectability', r'From\s+A\s?NTWERP,?\s+Sept', r'We\s+understand,?\s+an\s+order\s+has\s+been\s+given'],
      definition="Printings of an extract of a letter from a house in Antwerp to one in Bordeaux (28 September 1807), brought by the Sally-Barker-Windsor: 'We understand' that the Emperor had ordered every vessel bound to or from England to be captured, 'a mortal blow to the American commerce'. It reports a rumoured order.",
      first="A letter from Antwerp, 28 September 1807: Napoleon is said to have ordered every vessel bound to or from England to be captured.", what='the Antwerp letter',
      printings=[k(NI, '11-20', 2), k(ADA, '11-20', 3), (k(PGZ, '11-23', 1), dict(note='Heads the extract ALARMING TO COMMERCE.')), k(NG, '11-23', 3), k(VA, '11-24', 3), k(EN, '11-24', 2),
                 k(BJ, '11-27', 3), k(WR, '12-03', 6), (k(BJ, '12-25', 1), dict(note='Printed again four weeks after its first printing in this paper.'))]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline or heading directly before the item, after a sentence boundary (as for 1776): "NORFOLK, July 6."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*180[67])?\.\s*(?:[—-]+\s*)?)$")


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
        if a['family_id'].startswith('R1807-'):
            out.setdefault(a['page_id'].split(':', 1)[1].replace(':', '|'), []).append(a['family_id'])
    return {key: sorted(v) for key, v in out.items()}


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
        if field == CA and 'field' not in over:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'field': field, 'excerpt_start': first, 'excerpt_end': last, 'excerpt': excerpt,
                     'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['page_key'].split('|')[1], r['page_key'], r['story']))
    for n, r in enumerate(rows, 1):
        r['id'] = f'S07-{n:03}'
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
               'admission_rule': 'Reviewed 1807 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    return {
        'ledger_id': 'ledger:stories-1807', 'ledger_version': 1, 'base_release': '0.7.2', 'target_release': '0.8.0',
        'recorded_date': '2026-11-09', 'namespace': 'expansion-1807', 'evidence_dir': 'outputs/story_discovery_1807/evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': 'Single printed items split from the automatic 1807 families (long-running ones included), phrase searches on all 4,167 pages in both transcriptions, reading of every hit, and scan checks of each admitted passage',
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             'outputs/story_discovery_1807/items.json': 'retrieval_candidates', 'outputs/story_discovery_1807/phrase_patterns.json': 'retrieval_patterns',
                             'outputs/story_discovery_1807/phrase_hits.json': 'retrieval_candidates', 'work/archive_data/ledgers/make_stories_1807.py': 'ledger_code',
                             'work/archive_data/ledgers/stories_1807_review.json': 'scan_review', 'outputs/story_discovery_1807/SCAN_PROTOCOL.md': 'review_protocol',
                             'outputs/story_discovery_1807/scan_points.json': 'review_protocol'},
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
