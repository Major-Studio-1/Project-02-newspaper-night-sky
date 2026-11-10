"""Write ledgers/stories_1793.json (v0.9.0 -> v0.10.0): reviewed stories of 1793, the fifth reviewed year.

The stories were chosen as for 1776, 1807 and 1808 (make_stories_1776.py, make_stories_1807.py, make_stories_1808.py):
the automatic families first printed in 1793 that reach 3 or more papers (long-running ones included) were split into
single printed items with work/story_items.py, every item printed in 5 or more newspapers was read, and the chosen
items were confirmed with phrase searches over all 1,751 pages of 1793 in both transcriptions
(work/story_phrase_search.py). The same script was also run with year 1792 over the 1793 pages (items_from_1792.json);
none of those items reaches 6 papers. See outputs/story_discovery_1793/README.md.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as
apply_ledger.py does: the excerpt is the opening of the printed item (about 40-60 words), starting with its
dateline or heading when one stands directly before it. Scan findings, crops and hand-drawn boxes are merged from
stories_1793_review.json after the scan check.

Two 1793 issues have their RevX transcriptions filed one page off from the scans (derived/revx_page_map.parquet in
the base release, from outputs/revx_page_shift_check/). A printing on a page whose RevX slot holds another page's text
names the scan page and takes its excerpt from the CA transcription of that page, which is numbered as the scans are.
Most Kentucky Gazette issues of 1793 were scanned twice (editions 1 and 2 of one issue); a printing names one copy.
Two Gazette of the United States issues are filed under the wrong dates (outputs/story_discovery_1793/masthead_dates.csv);
a printing on one of them says so in its note.

Run from the project root with Python 3.12 (needs outputs/story_discovery_1793/search_pages.json, made by
work/year_search_pages.py):
    python work/archive_data/ledgers/make_stories_1793.py [--table]
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PAGES = PROJECT/'outputs/story_discovery_1793/search_pages.json'
REVIEW = HERE/'stories_1793_review.json'
OUT = HERE/'stories_1793.json'
BASE = '0.9.0'
TARGET = '0.10.0'
RELEASE = PROJECT/f'outputs/data_foundation/v{BASE}'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

NGZ, GUS, KG, PG, MIR, NHG = 'sn83025887', 'sn83030483', 'sn82014782', 'sn84038410', 'sn83025523', 'sn83025588'
NHGA, AHL, NHGR, CI, PHX, EAG = 'sn83025587', 'sn84023134', 'sn84023133', 'sn84023313', 'sn84023045', 'sn84023150'
PAPER = {NGZ: 'The National Gazette', GUS: 'The Gazette of the United States', KG: 'The Kentucky Gazette', PG: 'The Patowmac Guardian',
         MIR: 'The Mirrour', NHG: 'The New Hampshire Gazette', NHGA: 'The New-Hampshire Gazette and General Advertiser',
         AHL: 'The American Herald of Liberty', NHGR: 'The New Hampshire Gazetteer', CI: 'The Columbian Informer', PHX: 'The Phoenix',
         EAG: 'The Eagle, or Dartmouth Centinel'}
k = lambda paper, date, page, ed=1: f'{paper}|1793-{date}|{ed}|{page}'

# Issues filed under a date their masthead contradicts (masthead_dates.csv; the whole number fits the masthead).
MISDATED = {f'{GUS}|1793-04-04|1': 'This issue is filed under 4 April 1793; its masthead reads Saturday, May 4, 1793 (Whole No. 419), and the paper appeared on Wednesdays and Saturdays.',
            f'{GUS}|1793-07-23|1': 'This issue is filed under 23 July 1793; its masthead reads Saturday, July 13, 1793 (Whole No. 439), and the paper appeared on Wednesdays and Saturdays.'}


def misfiled():
    """Page keys whose RevX slot holds another scan page's text (shifted, two pages off or repeated), from the base release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith('1793')}


MISFILED = misfiled()

# Story groups, as for 1776, 1807 and 1808. 'printings' lists each printing's page; a tuple adds overrides for that printing:
# core (regexes for the item's first words), role, field, note, words, dateline (include a dateline or heading directly
# before), back (start at the beginning of the sentence that holds the core, for quoted documents).
STORIES = [
 # --- January: news of autumn 1792 ------------------------------------------------------------------------------------
 dict(id='emigrant-armies-disbanded', kind='message_group', label="Brussels, 17 October 1792: the emigrant princes' armies disbanded", role='report', words=55,
      core=[r'We\s+hear\s+from\s+the\s+[Pp]rovinces\s+of\s+Namur'],
      definition=("Printings of a Brussels paragraph of 17 October 1792, printed in American papers in January and February 1793: word from the "
                  "provinces of Namur and Luxembourg that the army of the French princes, Monsieur and the Count (or Duke) d'Artois, and that "
                  "under the Duke de Bourbon were disbanded, and that their men wandered in great distress. A report ('We hear')."),
      first="Brussels, 17 October 1792: the armies of the French princes and of the Duke de Bourbon are reported disbanded, their men in great distress.", what='the Brussels paragraph',
      printings=[k(NGZ, '01-05', 2),
                 (k(GUS, '01-05', 2), dict(words=44, note=("The RevX transcription stops after 'the Duke de Bourbon;' and runs on into the next paragraph; the older "
                                                            "CA transcription has the rest of the paragraph, so the excerpt ends at 'Bourbon;'."))),
                 k(PG, '01-14', 2), k(NHGA, '01-16', 2), k(NHGR, '01-16', 2), k(MIR, '01-21', 4), k(KG, '02-09', 1)]),
 dict(id='dumouriez-letter-brussels', kind='message_group', label="Dumouriez's letter on entering Brussels, 14 November 1792", role='report', words=55,
      core=[r'(?:["“]\s*B\s?russels,?\s+Nov\w*\.?\s+\d{1,2}[.,]?\s*(?:1792\.?)?["“]?\s*)?(?:["“]\s*)?C\s?ITIZEN\s+P\s?RESIDENT[,.]?\s*["“]?\s*'
            r'I\s+[Yy]esterday\s+presented\s+myself\s+before\s+Brussels'],
      definition=("Printings of General Dumouriez's letter to the President of the National Convention, dated Brussels, 14 November 1792, and read "
                  "in the Convention on 22 November: the Austrians had disputed the heights of Anderlecht with his advanced guard, and he had "
                  "entered Brussels. One army's own account."),
      first="Dumouriez writes to the Convention from Brussels (14 November 1792) that he has entered the city after the Austrians disputed the heights of Anderlecht.", what="Dumouriez's letter",
      printings=[(k(NGZ, '01-12', 2), dict(core=[r'This\s+evening\s+the\s+following\s+letter\s+from\s+Gen\.?\s+Dumourier'])),
                 k(GUS, '01-12', 3), k(NHGA, '01-23', 3), k(NHGR, '01-23', 2), k(MIR, '01-28', 3), k(PG, '01-28', 2), k(KG, '03-02', 2)]),
 # --- Dumouriez's defection ---------------------------------------------------------------------------------------------
 dict(id='dumouriez-defection-1793', kind='context_group', label="Dumouriez's defection, April 1793",
      definition=("News of General Dumouriez's break with the National Convention in April 1793, as American papers printed it from late May: "
                  "Clairfayt's letter that Dumouriez had sent the Convention's commissioners to the Austrian camp as prisoners, a London rumour "
                  "that he had left his army, his own address to the French nation, and the Prince of Saxe-Cobourg's proclamation in support "
                  "of it. Contains those four groups."),
      children=['clairfayt-letter-tournay', 'sun-rumour-dumouriez-left-army', 'dumouriez-address-french-nation', 'cobourg-proclamation-5-april']),
 dict(id='clairfayt-letter-tournay', parent='dumouriez-defection-1793', kind='message_group', label="Clairfayt's letter from Tournay: the commissioners sent as prisoners", role='report', words=55,
      core=[r'(?:(?:A\s+)?[Ll]etter\s+from\s+(?:his\s+Excellency\s+)?Gen\w*\.?\s+Clair[\s\-]?f\w+.{0,170}?dated,?\s+Tour\w+\s*,?\s+(?:March|April)\s+\d{1,2}[.,]?\s*(?:1793\.?)?\s*["“]?\s*)?'
            r'I\s+lose\s+not\s+a\s+[Mm]oment\s+in\s+communicating\s+to\s+your\s+Excellency'],
      definition=("Printings of a letter of the Austrian general Clairfayt to Count Starhemberg, the Imperial minister at The Hague (dated Tournay, "
                  "31 March 1793; some papers date it 3 April): Dumouriez had written to him that he had sent to the Austrian camp, as prisoners, "
                  "General Bournonville and the commissioners whom the Convention had sent to arrest him. One side's account of what Dumouriez wrote."),
      first="General Clairfayt writes from Tournay (31 March 1793) that Dumouriez has sent the Convention's commissioners to the Austrian camp as prisoners.", what="Clairfayt's letter",
      printings=[k(NGZ, '05-29', 1), k(GUS, '05-29', 2), k(PG, '06-03', 2), k(NHG, '06-04', 3), k(AHL, '06-04', 3),
                 (k(MIR, '06-05', 1), dict(note="Printed in an Extra of Wednesday 5 June; the paper appeared on Mondays.")),
                 (k(MIR, '06-10', 1), dict(note='Printed again in the regular number of 10 June, after the Extra of 5 June.')), k(KG, '06-29', 2)]),
 dict(id='sun-rumour-dumouriez-left-army', parent='dumouriez-defection-1793', kind='message_group', label="The Sun of 10 April: Dumouriez rumoured to have left his army", role='report', words=55,
      core=[r'In\s+[Tt]he\s+Sun\s*,?\s+of\s+the\s+1\d(?:th)?\s+(?:of\s+)?April', r'It\s+is\s+(?:now\s+)?rumou?red,?\s+that\s+D\s?UMOURIER'],
      definition=("Printings of a paragraph of the London Sun of 10 April 1793: it was rumoured that Dumouriez, having found reason to doubt his "
                  "army's promises to support his plan of marching to Paris and placing young Louis on the throne, had left it at the head of a "
                  "regiment of cavalry. A rumour, labelled as one. Several papers print it with a New York introduction ('In the Sun, of the 10th "
                  "April, which is the latest paper received'), the others among London paragraphs."),
      first="London, 10 April 1793: it is rumoured that Dumouriez, doubting his army, has left it and gone over to the Austrians.", what='the Sun paragraph',
      printings=[k(NGZ, '05-29', 1), k(GUS, '05-29', 3),
                 (k(NGZ, '06-01', 1), dict(note='Printed again three days later, now with the New York introduction.')),
                 k(PG, '06-03', 3), k(NHG, '06-04', 3), k(AHL, '06-04', 3), k(MIR, '06-10', 3), k(KG, '06-29', 2)]),
 dict(id='dumouriez-address-french-nation', parent='dumouriez-defection-1793', kind='document_group', label="Dumouriez's address to the French nation, 2 April 1793", role='published_document', words=55,
      core=[r'(?:(?:S\s?TATE\s+P\s?APERS?\.?\s+)?G\s?ENERAL\s+D\s?UMOURIER\s*,?\s+TO\s+THE\s+F\s?RENCH\s+N\s?ATION\.?\s+'
            r'|Gen\.?\s+D\s?UMOURIER.?S\s+L\s?ETTER\s+to\s+the\s+French\s+Nation,?\s+dated\s+Baths\s+of\s+St\.?\s*Amand\s*,?\s+April\s+2,?\s+1793\.?\s+)?'
            r'S\s?INCE\s+the\s+[Cc]ommencement\s+of\s+the\s+[Rr]evolution'],
      definition=("Printings of General Dumouriez's address 'to the French Nation', dated the Baths of St. Amand, 2 April 1793, printed from London "
                  "papers: his services since the Revolution, his charges against the Convention and the Jacobins, his plan to restore the "
                  "constitution with his army, and his oath to give up every public function afterwards. One side's account and a policy argument."),
      first="Dumouriez addresses the French nation (St. Amand, 2 April 1793): he will restore the constitution and then give up every public function.", what="Dumouriez's address",
      printings=[(k(NGZ, '06-05', 2), dict(note="Printed in two parts; the second part is on page 1 of the issue of 8 June.")), k(GUS, '06-05', 2),
                 (k(PG, '06-17', 1), dict(note='Continues on page 2.')), (k(NHG, '06-18', 1), dict(note='Continues on page 2.')), k(AHL, '06-18', 1),
                 (k(MIR, '07-01', 1), dict(note='Continues on page 4.'))]),
 dict(id='cobourg-proclamation-5-april', parent='dumouriez-defection-1793', kind='document_group', label="The Prince of Saxe-Cobourg's proclamation to the French, 5 April 1793", role='published_document', words=55, dateline=False,
      core=[r'T\s?he\s+M\S+\s+P\s?rince\s+of\s+S\s?axe.{0,160}?T\s?O\s+THE\s+F\s?RENCH\.?\s+T\s?HE\s+G\s?eneral,?\s+(?:in\s+)?[Cc]hief,?\s+D\s?UMOURIER,?\s+has\s+communicated'],
      definition=("Printings of the proclamation 'to the French' of the Austrian commander, the Prince of Saxe-Cobourg (Mons, 5 April 1793): he "
                  "supported Dumouriez's declaration to the French nation, would act only as an auxiliary, and would hold any fortress handed to "
                  "him only as a sacred trust. He withdrew these pledges in a proclamation of 9 April, which the same papers printed beside it."),
      first="The Prince of Saxe-Cobourg tells the French (5 April 1793) that he supports Dumouriez's declaration and will act only as an auxiliary.", what="Saxe-Cobourg's proclamation",
      printings=[k(NGZ, '06-05', 1), (k(GUS, '06-05', 2), dict(note='Continues on page 3.')), k(PG, '06-17', 2), k(AHL, '06-18', 2), k(MIR, '06-24', 1)]),
 # --- Genet and the President -------------------------------------------------------------------------------------------
 dict(id='genet-appeal-to-the-people-1793', kind='context_group', label="Genêt and the President: the 'appeal to the people', 1793",
      definition=("One affair in three printed documents, as the papers printed them from mid-August to early September 1793: John Jay and Rufus "
                  "King's statement that the French minister, Genêt, had said he would appeal to the people from certain decisions of the "
                  "President; Genêt's letter to the President asking him to declare that he had never said so to him; and the Secretary of "
                  "State's answer for the President. Contains those three groups. The statement is an allegation and the letter the minister's "
                  "own account; whether he said it is not settled here."),
      children=['jay-king-statement-on-genet', 'genet-letter-to-the-president-13-august', 'jefferson-answer-to-genet-16-august']),
 dict(id='jay-king-statement-on-genet', parent='genet-appeal-to-the-people-1793', kind='message_group', label="Jay and King: Genêt said he would appeal to the people", role='report', words=55,
      core=[r'(?:M\w*\.?\s+P\s?RINTERS,?\s+)?C\s?ERTAIN\s+late\s+publications\s+render\s+it\s+proper'],
      definition=("Printings of a card of John Jay and Rufus King to the printers of the New York Diary (August 1793): a report having reached New "
                  "York from Philadelphia that Mr. Genêt, the French minister, had said he would appeal to the people from certain decisions of "
                  "the President, they had been asked on their return whether he had said so, and 'we answered, that he had'. An allegation by "
                  "two named men."),
      first="John Jay and Rufus King state in New York (August 1793) that Genêt said he would appeal to the people from the President's decisions.", what="Jay and King's statement",
      printings=[k(NGZ, '08-17', 2), k(GUS, '08-17', 3), k(PG, '08-26', 3), k(NHG, '08-27', 2), k(AHL, '08-27', 2)]),
 dict(id='genet-letter-to-the-president-13-august', parent='genet-appeal-to-the-people-1793', kind='document_group', label="Genêt's letter to the President, 13 August 1793", role='published_document', words=55,
      core=[r"(?:N\w*[\s\-]?Y\w*,?\s+13th\s+Aug\w*\.?,?\s+(?:'93|1793)[.,]?\s+(?:2d|Second)\s+Year\s+of\s+the\s+Republic[.,]?\s+)?"
            r"C\s?itizen\s+G\s?ENET\s*,?\s+Minister\s+Plenipotentiary\s+from\s+the\s+French\s+Republic"],
      definition=("Printings of the letter of Citizen Genêt, minister plenipotentiary of the French Republic, to President Washington (New York, "
                  "13 August 1793), printed with the Secretary of State's answer, as published in New York (the National Gazette credits the New "
                  "York Diary of 21 August): persons were saying that "
                  "he had threatened to appeal to the people from the President's decisions, and he asked the President for an explicit "
                  "declaration that he had never intimated such an intention to him. The minister's own account."),
      first="Genêt writes to President Washington (New York, 13 August 1793) asking him to declare that Genêt never spoke to him of appealing to the people.", what="Genêt's letter",
      printings=[(k(GUS, '08-24', 2), dict(note='Begins at the foot of page 2 and continues on page 3, where the answer follows.')), k(NGZ, '08-28', 1), k(PG, '09-02', 2),
                 k(NHG, '09-03', 4), k(AHL, '09-03', 2), k(CI, '09-04', 2), k(EAG, '09-09', 2)]),
 dict(id='jefferson-answer-to-genet-16-august', parent='genet-appeal-to-the-people-1793', kind='document_group', label="Jefferson's answer for the President, 16 August 1793", role='published_document', words=55,
      core=[r"(?:M\s?r\.?\s+J\s?EFFERSON.?S\s+A\s?NSWER\.?\s+)?(?:P\s?HILADELPHIA,?\s+A\w*\.?\s+1[69],?\s*(?:'93|1793)?\.?\s+)?"
            r"S\s?IR,?\s+T\s?HE\s+President\s+of\s+the\s+United\s+States,?\s+has\s+received\s+the\s+letter"],
      definition=("Printings of the Secretary of State's answer to Genêt for the President (Philadelphia, 16 August 1793): the diplomatic characters "
                  "residing here should not correspond directly with the President, the Secretary of State being the organ of their "
                  "communications, and the President did not think it within the line of propriety or duty to bear evidence against a "
                  "declaration, so he declined to interfere. An official document."),
      first="Jefferson answers Genêt for the President (Philadelphia, 16 August 1793): ministers do not write to the President directly, and he declines to interfere.", what="the Secretary of State's answer",
      printings=[k(GUS, '08-24', 3), k(NGZ, '08-28', 1), k(PG, '09-02', 2), k(NHG, '09-03', 4), k(AHL, '09-03', 2),
                 (k(CI, '09-04', 3), dict(core=[r'has\s+received\s+the\s+letter\s+which\s+you\s+addressed\s+to\s+him'], dateline=False,
                                          note=("The answer begins at the foot of page 2 ('Mr. JEFFERSON'S ANSWER. PHILADELPHIA, Aug. 16, 1793. SIR, THE "
                                                "President of the United States') and continues on page 3, where the excerpt begins."))),
                 k(EAG, '09-09', 2)]),
 # --- August: a sea serpent, and a battle reported from Madeira ---------------------------------------------------------
 dict(id='sea-serpent-captain-crabtree', kind='message_group', label="Captain Crabtree's sea serpent", role='report', words=55,
      core=[r'(?:(?:P\w+LAND|Periland),?\s+(?:\(Mass\.?\)\s+)?Aug\w*\.?\s+3\.?\s+)?(?:S\s?EA\s+M\s?ONSTER\.?\s+)?(?:P\w+LAND,?\s+Aug\w*\.?\s+3\.?\s+)?Capt\w*\.?\s+C\s?RABTREE'],
      definition=("Printings of a Portland (District of Maine) paragraph of 3 August 1793 headed 'Sea Monster': Captain Crabtree, lately arrived "
                  "at Frenchman's Bay, says that on 20 June, on his passage from the West Indies and in sight of Mount Desert island, he watched "
                  "for nearly an hour a serpent of enormous size, which he judged to be 55 to 60 feet long, its head raised six or eight feet "
                  "out of the water. One man's account, which the paper says 'may be depended on'."),
      first="Portland, 3 August 1793: Captain Crabtree tells of a sea serpent of enormous size seen on his passage from the West Indies.", what="Captain Crabtree's account",
      printings=[k(NHG, '08-13', 2), k(NGZ, '08-17', 2), k(GUS, '08-17', 2), k(MIR, '08-19', 2), k(AHL, '08-20', 3), k(CI, '09-04', 4), k(EAG, '09-09', 3)]),
 dict(id='madeira-report-battle-near-lisle', kind='message_group', label="By the brig Molly from Madeira: a battle near Lisle reported", role='report', words=55,
      core=[r'(?:P\s?HILADELPHIA,?\s+Aug\w*\.?\s+1[46]\.?\s+)?By\s+the\s+brig\s+Molly,?\s+Capt'],
      definition=("Printings of a Philadelphia paragraph of 14 August 1793: by the brig Molly, Capt. Morris, from Madeira, word that a frigate from "
                  "Falmouth had brought English papers to about 24 June with an account of a very bloody battle near Lisle, to the advantage of "
                  "the French, in which 17,000 men fell; Morris said the account was believed at Madeira. A report at third hand of what "
                  "newspapers said; the Gazette of the United States and the American Herald of Liberty add that the consul's letter from "
                  "Madeira of 4 July said there was nothing new."),
      first="Philadelphia, 14 August 1793: the brig Molly from Madeira brings word of English papers telling of a bloody battle near Lisle in which 17,000 men fell.", what='the Madeira report',
      printings=[k(NGZ, '08-17', 3), k(GUS, '08-17', 3), k(PG, '08-26', 2), k(NHG, '08-27', 2),
                 (k(AHL, '08-27', 3), dict(note=("The RevX transcription shortens the paragraph with '...' after 'nine days from Falmouth', dropping the "
                                                 "account of the battle; the older CA transcription has it."))),
                 k(MIR, '09-02', 3), k(CI, '09-04', 3)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline or heading directly before the item, after a sentence boundary (as for 1776, 1807 and 1808): "BRUSSELS, Oct. 17."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*179[23])?\.\s*(?:[—-]+\s*)?)$")


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
        if key.split('|')[1].startswith('1793'):
            out.setdefault(key, []).append(a['family_id'])
    return {key: sorted(v) for key, v in out.items()}


def second_copy_note(pages, key, cores):
    """Kentucky Gazette issues were mostly scanned twice: say so when the other copy's page also holds the item."""
    lccn, date, ed, page = key.split('|')
    if lccn != KG:
        return ''
    other = f"{lccn}|{date}|{2 if ed == '1' else 1}|{page}"
    if other not in pages:
        return ''
    texts = pages[other]['texts']
    if any(re.search(core, texts.get(f) or '', re.I) for core in cores for f in (REVX, CA)):
        return f"A second scanned copy of this issue (edition {other.split('|')[2]}) also holds the item."
    return f"A second scanned copy of this issue (edition {other.split('|')[2]}) exists; the item was not found in its transcriptions."


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
        issue = key.rsplit('|', 1)[0]
        if issue in MISDATED:
            note = (note+' ' if note else '') + MISDATED[issue]
        copy = second_copy_note(pages, key, cores)
        if copy:
            note = (note+' ' if note else '') + copy
        rows.append({'story': story, 'page_key': key, 'field': field, 'excerpt_start': first, 'excerpt_end': last, 'excerpt': excerpt,
                     'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['page_key'].split('|')[1], r['page_key'], r['story']))
    for n, r in enumerate(rows, 1):
        r['id'] = f'S93-{n:03}'
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
               'admission_rule': 'Reviewed 1793 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    return {
        'ledger_id': 'ledger:stories-1793', 'ledger_version': 1, 'base_release': BASE, 'target_release': TARGET,
        'recorded_date': '2026-11-10', 'namespace': 'expansion-1793', 'evidence_dir': 'outputs/story_discovery_1793/evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1793 (long-running ones included), phrase searches on all 1,751 '
                   'pages in both transcriptions, reading of every hit, and scan checks of each admitted passage'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             'outputs/story_discovery_1793/items.json': 'retrieval_candidates', 'outputs/story_discovery_1793/items_from_1792.json': 'retrieval_candidates',
                             'outputs/story_discovery_1793/phrase_patterns.json': 'retrieval_patterns', 'outputs/story_discovery_1793/phrase_hits.json': 'retrieval_candidates',
                             'outputs/story_discovery_1793/masthead_dates.csv': 'date_check', 'outputs/story_discovery_1793/check_mastheads_1793.py': 'analysis_code',
                             'outputs/story_discovery_1793/page_date_flags.csv': 'date_check', 'outputs/story_discovery_1793/check_duplicate_pages_1793.py': 'analysis_code',
                             'work/archive_data/ledgers/make_stories_1793.py': 'ledger_code', 'work/archive_data/ledgers/stories_1793_review.json': 'scan_review',
                             'outputs/story_discovery_1793/SCAN_PROTOCOL.md': 'review_protocol', 'outputs/story_discovery_1793/scan_points.json': 'review_protocol'},
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
