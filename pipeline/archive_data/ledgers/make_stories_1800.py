"""Write ledgers/stories_1800.json: reviewed stories of 1800, round one.

1800 is read by the one admission rule the other reviewed years follow (outputs/story_discovery_1809/README.md, "Selection
rule"; docs/rules-and-exceptions.md, R-01): every single printed item in 9 or more newspapers is admitted, except digests;
items in 7 or 8 papers are chosen to cover the months and the kinds of news; items are counted one by one; a sub-story may
have fewer papers when its parent reaches 7. The automatic families first printed in 1800 that reach 3 or more papers,
long-running ones included, were split into single printed items with work/story_items.py --long-running (items.json), and
again with year 1799 over the 1800 pages (items_from_1799.json); every item in 6 or more papers was read, and the counts were
checked item by item with phrase searches over all 2,575 pages of 1800 in both transcriptions (work/story_phrase_search.py).
See outputs/story_discovery_1800/README.md.

The 1800 pages are those whose issue the data release dates to 1800 (work/year_search_pages.py 1800 ... --printed-dates); no
1800 issue has a corrected date. The Gazette of the United States has two catalogue numbers in 1800 (sn83025881 to 7 May,
sn84026272 from 1 July): one paper, counted once.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-80 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1800_review.json after the scan
check. Twenty-three 1800 pages have their RevX transcriptions filed off from the scans (derived/revx_page_map.parquet); a
printing on such a page would take its excerpt from the CA transcription of its scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened. The papers of February 1800 name the seaman delivered to the
British under the 27th article of the treaty with Great Britain; the excerpts here end before his name, and the
descriptions do not give it (C-12).

The base and target releases are set when the ledger is applied (a 1804 review runs at the same time and may take the next
number first):
    python work/archive_data/ledgers/make_stories_1800.py [--table] [--base 0.11.8 --target 0.11.9]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1800/search_pages.json). The excerpts are cut from
the 1800 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1800'
D = PROJECT/'outputs/story_discovery_1800'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1800_review.json'
OUT = HERE/'stories_1800.json'
BASE, TARGET = '0.11.8', '0.11.9'   # defaults; see the docstring
DATA_RELEASE = '0.11.8'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-23'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

GUS1, GUS2, KY, NH, PJ, ORA = 'sn83025881', 'sn84026272', 'sn82014782', 'sn83025588', 'sn83021629', 'sn83025544'
POR, RL, NI, VA, ALX, ULS, DOV = 'sn83016063', 'sn84023378', 'sn83045242', 'sn84024710', 'sn84024011', 'sn83031193', 'sn88053159'
PAPER = {GUS1: 'The Gazette of the United States', GUS2: 'The Gazette of the United States', KY: 'The Kentucky Gazette',
         NH: 'The New Hampshire Gazette', PJ: 'The Providence Journal', ORA: 'The United States Oracle of the Day',
         POR: "Jenks's Portland Gazette", RL: 'The Republican Ledger', NI: 'The National Intelligencer', VA: 'The Virginia Argus',
         ALX: 'The Alexandria Advertiser', ULS: 'The Ulster County Gazette', DOV: 'The Dover Herald'}
GUS = 'GUS'   # the Gazette of the United States: its catalogue number depends on the date


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper, date (MM-DD in 1800), page and edition."""
    if paper == GUS:
        paper = GUS1 if date < '06' else GUS2
    return f'{paper}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()

# Story groups. A parent ('context_group') lists its children and has no printings. 'printings' lists each printing's page;
# a tuple adds overrides for that printing: core (regexes for the item's first words), role, field, note, words, dateline
# (include a dateline directly before), back (start at the beginning of the sentence that holds the core), stop (a regex:
# the excerpt ends before it).
STORIES = [
 dict(id='congress-honours-washington-1799-1800', kind='context_group',
      label='Congress and the President honour Washington, December 1799 to January 1800',
      children=['joint-resolutions-23-december-1799-on-washington', 'president-message-8-january-1800-mrs-washington-letter'],
      definition="Two documents on the honours paid to George Washington, who died on 14 December 1799, as the 1800 papers printed them: the joint resolutions of Congress of 23 December 1799, and the President's message of 8 January 1800 sending Congress Mrs. Washington's answer. Contains those two groups."),
 dict(id='joint-resolutions-23-december-1799-on-washington', parent='congress-honours-washington-1799-1800', kind='document_group',
      label='The joint resolutions of Congress of 23 December 1799 on the death of Washington',
      definition="Printings of the resolutions that the joint committee of Congress reported through Mr. Marshall and both houses passed: 'That a Marble Monument be erected by the United States, in the Capitol, at the City of Washington, and that the family of General Washington be requested to permit his body to be deposited under it'; that there be a funeral procession and an oration before both houses on 26 December; that the people be recommended to wear crape on the left arm for thirty days; that the President send a copy to Mrs. Washington; and that he issue a proclamation. The weekly papers printed them in January 1800 with the proceedings; three papers printed them again from July to October among the laws and resolutions of the session. Congress's own resolutions.",
      role='published_document', words=80, dateline=False, stop=r'(?:And|An\.?)\s+(?:\S+\s+){0,2}further\s+[Rr]esolved',
      core=[r'R\s?ESOLVED\s*,?\s+(?:B|b)y\s+the\s+Senate\s+and\s+House\s+of\s+Representatives\s+of\s+the\s+United\s+States[^.]{0,60}?That\s+a\s+(?:M|m)arble\s+(?:M|m)onument',
            r'That\s+a\s+(?:M|m)arble\s+(?:M|m)onument\s+be\s+erected'],
      first='The joint resolutions of Congress of 23 December 1799: a marble monument to Washington in the Capitol, a funeral procession and oration, and crape to be worn for thirty days.',
      what='the joint resolutions of Congress on Washington',
      printings=[k(PJ, '01-01', 2),
                 k(ORA, '01-04', 3),
                 k(POR, '01-06', 2),
                 k(NH, '01-08', 2),
                 k(RL, '01-08', 2),
                 k(KY, '01-23', 2),
                 (k(GUS, '07-22', 2), {'note': 'Printed again among the laws and resolutions of the session.'}),
                 (k(PJ, '09-10', 1), {'note': 'Printed again among the laws and resolutions of the session.'}),
                 (k(ORA, '10-11', 1), {'note': 'Printed again among the laws and resolutions of the session.'}),
                 (k(KY, '10-13', 11), {'note': 'Printed again among the laws and resolutions of the session.'})]),
 dict(id='president-message-8-january-1800-mrs-washington-letter', parent='congress-honours-washington-1799-1800', kind='document_group',
      label="The President's message of 8 January 1800 with Mrs. Washington's letter",
      definition="Printings of the President's message to both houses, sent on 8 January 1800: 'In compliance with the request in one of the resolutions of Congress of the 21st of December last, I transmitted a copy of those resolutions, by my secretary, Mr. Shaw, to Mrs. Washington', with her answer from Mount Vernon of 31 December 1799: 'Taught by the great example which I have so long had before me, never to oppose my private wishes to the public will—I must consent to the request made by Congress'. The President's message and Mrs. Washington's letter, in their own words.",
      role='published_document', words=60, dateline=False,
      core=[r'Gentlemen\s+of\s+the\s+(?:S|s)enate,?\s+and\s+(?:G|g)entlemen\s+of\s+the\s+(?:H|h)ouse\s+of\s+(?:R|r)epresentatives[.,]?\s+(?:IN|In)\s+compliance\s+with\s+the\s+request',
            r'(?:IN|In)\s+compliance\s+with\s+the\s+request\s+in\s+one\s+of\s+the\s+(?:R|r)esolutions'],
      first="The President's message of 8 January 1800 lays before Congress Mrs. Washington's consent to the resolutions on her husband's remains.",
      what="the President's message with Mrs. Washington's letter",
      printings=[k(GUS, '01-10', 3),
                 k(ORA, '01-18', 3),
                 k(POR, '01-20', 3),
                 k(PJ, '01-22', 3),
                 k(NH, '01-22', 3),
                 k(RL, '01-22', 3),
                 k(KY, '02-06', 2)]),
 dict(id='convention-of-alkmaar-october-1799', kind='document_group',
      label='The convention of October 1799 between the Duke of York and General Brune for the British and Russian army to leave Holland',
      definition="Printings of the articles 'agreed upon between Major General Knox, duly authorised by his Royal Highness the Duke of York, Commander in Chief of the combined English and Russian Army, and Citizen Rostollant ... duly authorised by Citizen Brune, General and Commander in Chief of the French and Batavian Armies' (the names vary from paper to paper): 'From the date of this convention, all hostilities shall cease between the two armies'; the combined army 'shall evacuate the territory, coasts, islands, and internal navigation of the Dutch Republic, by the 30th of November, 1799', and 'Eight thousand prisoners of war, French and Batavians ... now detained in England, shall be restored'. The London Gazette of 26 October 1799 published it with the Duke of York's dispatch of 20 October, and most papers printed the two together; the Portland Gazette printed the articles alone. The two commanders' agreement, as the British government published it.",
      role='published_document', words=70, dateline=False,
      core=[r'ARTICLES\.?\s+\d?\s*(?:A|a)greed\s+upon\s+between\s+(?:M|m)aj\w*\.?[\s-]+(?:G|g)en\w*\.?\s+Knox',
            r'(?:THE\s+)?(?:ARMISTICE|ARTICLES)\.?\s+Art\.?\s+(?:1|I)\.\s+From\s+the\s+date\s+of\s+this\s+(?:C|c)onvention',
            r'ARMISTICE\.\s+1\.\s+From\s+the\s+date\s+of\s+this\s+Convention'],
      first="The convention of October 1799 with General Brune: hostilities cease, and the British and Russian army is to leave Holland.",
      what='the convention for the evacuation of Holland',
      printings=[k(GUS, '01-10', 2),
                 k(PJ, '01-15', 2),
                 k(DOV, '01-16', 1),
                 k(ORA, '01-18', 2),
                 (k(POR, '01-20', 2), {'note': "The Portland Gazette prints the articles alone, introduced as the armistice inclosed in the Duke of York's letter."}),
                 k(NH, '01-22', 3),
                 k(RL, '01-22', 2),
                 k(KY, '02-13', 2)]),
 dict(id='congress-and-the-27th-article-february-1800', kind='context_group',
      label='Congress asks for the papers on a seaman delivered to the British under the 27th article of the treaty, February 1800',
      children=['livingston-resolutions-3-february-1800', 'president-message-7-february-1800-papers-on-the-27th-article'],
      definition="Two documents of February 1800 on a seaman held at Charleston in 1799 whom the British minister claimed under the 27th article of the treaty of 1794 with Great Britain (the article on delivering up persons charged with murder or forgery). In the words of Mr. Livingston's later resolutions (20 February, not admitted), he was a person 'claiming to be a citizen of the United States, impressed on board a British ship of war', committed for trial for 'piracy and murder' alleged to have been committed on board the British frigate Hermione, and delivered up to the British consul on the President's advice. The papers name him; the excerpts and these descriptions do not. Contains those two groups."),
 dict(id='livingston-resolutions-3-february-1800', parent='congress-and-the-27th-article-february-1800', kind='document_group',
      label="Mr. Livingston's resolutions of 3 February 1800 on the 27th article of the treaty with Great Britain",
      definition="Printings of the resolutions that Mr. Livingston laid on the table of the House of Representatives on 3 February 1800: 'Resolved, That provision ought to be made by law for carrying into effect the 27th article of the treaty of amity, commerce and navigation between the United States and the king of Great Britain'; and that the President be requested to lay before the House copies of the requisition for, and the papers on, the seaman's apprehension and delivery. The excerpts end before the second resolution, which names him. A member's motions, as the papers reported the proceedings.",
      role='published_document', words=70, dateline=False, back=True, stop=r'(?:\b\w\s+)?Re\w{3,6}\s*,?\s+That\s+the\s+[Pp]r\w+',
      core=[r'Livingston\s+(?:laid|read|offered)\s+the\s+following\s+resolutions?', r'read\s+the\s+following\s+resolutions,?\s+which,?\s+if\s+seconded',
            r'Resolved\s*,?\s+That\s+provisions?\s+ought\s+to\s+be\s+made\s+by\s+(?:law|Jaw)\s+for\s+carrying\s+into\s+eff\w*\s+the\s+27th'],
      first="Mr. Livingston's resolutions of 3 February 1800: provision ought to be made by law for carrying the 27th article of the British treaty into effect, and the papers on the delivery of a seaman are asked for.",
      what="Mr. Livingston's resolutions",
      printings=[k(GUS, '02-04', 2),
                 k(PJ, '02-12', 3),
                 (k(ORA, '02-15', 3), {'field': CA, 'core': [r'Livingston\s+laid\s+the\s+following\s+resolutions'],
                                       'note': 'RevX leaves out the two resolutions after the sentence that introduces them; the older CA transcription has them, so the excerpt comes from the CA text.'}),
                 k(POR, '02-17', 2),
                 k(NH, '02-19', 2),
                 k(RL, '02-19', 3),
                 k(KY, '03-06', 2)]),
 dict(id='president-message-7-february-1800-papers-on-the-27th-article', parent='congress-and-the-27th-article-february-1800', kind='document_group',
      label="The President's message of 7 February 1800 sending the Secretary of State's report and papers",
      definition="Printings of the President's message to the House of 7 February 1800: 'In consequence of your request to me, conveyed in your resolution of the fourth of this month, I directed the Secretary of State to lay before me copies of the papers intended. These copies, together with his report, I now transmit to the House of Representatives' (the Portland Gazette prints 'IN conformity to your request'), and in most papers the Secretary of State's report and the letters that followed it: the British minister's requisition, the Secretary of State's letter to the district judge at Charleston, and the judge's answer. The President's message; the papers are each official's own letters.",
      role='published_document', words=60, dateline=False, stop=r'J\s?OHN\s+A\s?DAMS',
      core=[r'Gentlemen\s+of\s+the\s+(?:H|h)ouse\s+of\s+(?:R|r)epresentatives,?\s+(?:IN|In)\s+(?:consequence|conformity)\s+(?:of|to)\s+your\s+request',
            r'(?:IN|In)\s+(?:consequence|conformity)\s+(?:of|to)\s+your\s+request\s+to\s+me'],
      first="The President's message of 7 February 1800 sends the House the Secretary of State's report and the papers it asked for on the 4th.",
      what="the President's message of 7 February",
      printings=[k(GUS, '02-08', 3),
                 k(PJ, '02-19', 2),
                 k(ORA, '02-22', 3),
                 (k(POR, '02-24', 2), {'note': "The Portland Gazette prints 'IN conformity to your request to me' where the others have 'In consequence of'."}),
                 k(NH, '02-26', 1),
                 k(RL, '02-26', 2),
                 k(KY, '03-20', 1)]),
 dict(id='bonaparte-letter-to-the-king-and-grenville-answer', kind='document_group',
      label="Bonaparte's letter to the King of Great Britain, 25 December 1799, and Lord Grenville's answer",
      definition="Printings of the first part of the correspondence on Bonaparte's offer of peace, as the British government published it: Talleyrand's letter to Lord Grenville sending a messenger ('I dispatch by order of General Buonaparte, first Consul of the French Republic, a messenger to London'), the First Consul's letter to the King ('Called by the wishes of the French nation to occupy the first magistracy of the Republic, I think it proper, on entering into office, to make a direct communication of it to your Majesty'), and Lord Grenville's note of 4 January 1800 in answer ('The King has given frequent proofs of his sincere desire for the re-establishment of secure and permanent tranquillity in Europe'), which declines to negotiate. The same papers printed the second part, Talleyrand's reply of 14 January and Lord Grenville's of 20 January, a week or two later (not admitted; see the README). Each government's own letters.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:I|1)\s+D\s?ISPATCH,?\s+by\s+(?:the\s+)?order\s+of\s+Gen(?:eral|\.)?\s+Bu?o?naparte'],
      first="Talleyrand's letter to Lord Grenville of 25 December 1799 sends the First Consul's letter to the King, with Lord Grenville's answer of 4 January 1800.",
      what="the letters of the First Consul and Lord Grenville",
      printings=[k(GUS, '03-22', 2),
                 k(PJ, '03-26', 3),
                 k(ORA, '03-29', 2),
                 k(POR, '03-31', 2),
                 k(NH, '04-02', 2),
                 k(RL, '04-02', 2),
                 k(KY, '04-10', 2)]),
 dict(id='spanish-order-against-trade-with-gibraltar-1800', kind='document_group',
      label="The King of Spain's order of February 1800 against trade with Gibraltar",
      definition="Printings of a Spanish royal order, published at Cadiz on 28 February 1800 and sent by the American consul there, headed 'Blockade of Gibraltar' in most papers (the Republican Ledger heads it 'Blockade of Cadiz'): 'His Catholic Majesty desirous of lessening as far as possible the injuries resulting to the Nation by the shameful trade carried on by many of his subjects with Gibraltar' orders that vessels bound to or from Gibraltar be treated as enemies. The Spanish government's order, as the consul sent it.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:B\s?LOCKADE\s+OF\s+G\s?IBRALTAR\.\s+)?(?:H\s?IS|His)\s+Catholic\s+Majesty,?\s+desirous\s+of\s+lessening',
            r'lessening,?\s+as\s+far\s+as\s+possible,?\s+the\s+injuries\s+resulting'],
      first="A Spanish royal order of February 1800, sent by the American consul at Cadiz: vessels trading with Gibraltar are to be treated as enemies.",
      what="the Spanish order on Gibraltar",
      printings=[(k(GUS, '04-25', 3), {'field': CA, 'core': [r'H\w{1,2}\s+Catholic\s+M\S+\s+del\w+\s+of\s+lef+en'],
                                       'note': 'The excerpt comes from the older CA transcription, which is garbled; RevX lacks this item.'}),
                 k(POR, '05-05', 2),
                 k(NH, '05-06', 3),
                 k(PJ, '05-07', 3),
                 (k(ORA, '05-10', 2), {'field': CA, 'core': [r'B\s?LOCKADE\s+OF\s+G\s?IBRALTAR\.\s+His\s+Catholic\s+Majesty'],
                                       'note': 'RevX gives the order twice on this page; the CA transcription has it once, so the excerpt comes from the CA text.'}),
                 k(RL, '05-13', 3),
                 k(KY, '05-15', 3)]),
 dict(id='siege-and-evacuation-of-genoa-1800', kind='context_group',
      label="The siege and evacuation of Genoa, 1800: Melas's summons and Massena's report",
      children=['melas-summons-to-massena-genoa', 'massena-report-evacuation-of-genoa-7-june-1800'],
      definition="Two documents on the Austrian siege of Genoa, held by the French general Massena from April to June 1800, as the American papers printed them in July and August: the Austrian commander Melas's letter summoning Massena to surrender, and Massena's report to the First Consul of 7 June on the evacuation of the city under a convention. Contains those two groups."),
 dict(id='melas-summons-to-massena-genoa', parent='siege-and-evacuation-of-genoa-1800', kind='document_group',
      label="General Melas's letter summoning Massena to surrender Genoa, 1800",
      definition="Printings of the letter in which the Austrian general Melas, 'on summoning Massena to surrender the city of Genoa, wrote to him in the following terms: General, Fortune has not crowned your bravery, which entitles you to my esteem, and to that of the whole world'. The Austrian commander's own letter, as the London papers gave it.",
      role='published_document', words=60, dateline=False, back=True,
      core=[r'Melas,?\s+on\s+summoning\s+Massena', r'["“]?\s*(?:G\s?ENERAL,?\s+)?["“]?\s*Fortune\s+has\s+not\s+crowned\s+your\s+bravery'],
      first="General Melas's letter summoning Massena to surrender Genoa: 'Fortune has not crowned your bravery'.",
      what="Melas's letter to Massena",
      printings=[k(ORA, '07-19', 2),
                 k(GUS, '07-19', 3),
                 k(POR, '07-21', 2),
                 k(NH, '07-22', 1),
                 k(RL, '07-22', 1),
                 k(PJ, '07-23', 2),
                 k(KY, '08-14', 2)]),
 dict(id='massena-report-evacuation-of-genoa-7-june-1800', parent='siege-and-evacuation-of-genoa-1800', kind='document_group',
      label="Massena's report to the First Consul on the evacuation of Genoa, 7 June 1800",
      definition="Printings of General Massena's letter to General Bonaparte dated Genoa, 7 June 1800: 'MY GENERAL, I HAVE the honour to give you an account of the evacuation of Genoa, conformable to the annexed convention. I hope you will find it worthy of the obstinate resistance of the brave army you have entrusted to me', in most papers with the convention for the evacuation and his letter to the Consuls. A commander's own report.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:From\s+Gen\w*\.?,?\s+)?MASSENA,?\s+to\s+Gen\w*\.?\s+BU?O?NAPARTE', r'(?:MY\s+GENERAL,?\s+)?I\s+HAVE\s+the\s+hono\w+\s+to\s+give\s+you\s+an\s+account\s+of\s+the\s+evacuation\s+of\s+Genoa'],
      first="Massena's report to Bonaparte of 7 June 1800 on the evacuation of Genoa under a convention.",
      what="Massena's report on Genoa",
      printings=[(k(ORA, '08-09', 2), {'stop': r'Operations\s+in\s+ITALY',
                                       'note': "RevX leaves out the rest of the letter after its first sentences and runs into the next item ('Operations in ITALY'), so the excerpt ends with 'shut up there.'"}),
                 k(POR, '08-11', 1),
                 k(GUS, '08-11', 3),
                 k(NH, '08-12', 1),
                 k(RL, '08-12', 2),
                 k(PJ, '08-13', 2),
                 k(KY, '09-01', 2)]),
 dict(id='ratisbon-report-vienna-answer-to-first-consul', kind='message_group',
      label="Ratisbon, 15 July 1800: Vienna's answer to the First Consul's proposals for peace",
      definition="Printings of a paragraph dated Ratisbon, 15 July 1800 (the Oracle's dateline reads 10 July in its transcription), in the London papers: 'We are assured that the Court of Vienna, has returned an answer to the First Consul's proposals for peace, importing \"the Emperor wishes for peace not less than France, but for one that should be general and durable\"'. A correspondent's report at second hand.",
      role='report', words=60, dateline=True,
      core=[r'(?:We\s+are\s+\w+\s+that\s+)?the\s+(?:C|c)ourt\s+of\s+Vienna,?\s+has\s+returned\s+an\s+\w+\s+to\s+the\s+First\s+Consul'],
      first="Ratisbon, 15 July 1800: the Court of Vienna has answered the First Consul that the Emperor wishes for a general and durable peace.",
      what='the Ratisbon report',
      printings=[k(PJ, '09-10', 2),
                 (k(ORA, '09-13', 2), {'field': CA, 'note': 'RevX lacks this paragraph, so the excerpt comes from the older CA transcription.'}),
                 k(GUS, '09-13', 2),
                 k(POR, '09-15', 1),
                 k(NH, '09-16', 1),
                 k(RL, '09-16', 2),
                 k(KY, '10-06', 2),
                 (k(KY, '10-13', 2), {'note': 'Printed again.'})]),
 dict(id='paris-6-august-1800-conferences-with-american-envoys', kind='message_group',
      label="Paris, 6 August 1800: 'The conferences opened at Paris with the envoys of the United States are at present suspended'",
      definition="Printings of a paragraph from the Paris papers headed 'France and America' and dated 18 Thermidor (6 August 1800): 'The conferences opened at Paris with the envoys of the United States are at present suspended; and there is little hope of their being successfully resumed'; it goes on to give what it calls the French view of the dispute over the treaties of 1778. A report and argument from the French side, as the London papers gave it.",
      role='report', words=60, dateline=True,
      core=[r'(?:France\s+and\s+America\.\s+)?(?:PARIS,?\s+)?\S*\s*Thermidor,?\s+Aug\w*\.?\s+6\.?\s+(?:T|t)he\s+conferences\s+opened',
            r'(?:T|t)he\s+conferences\s+opened\s+at\s+Paris\s+with\s+the\s+(?:E|e)nvoys'],
      first="Paris, 6 August 1800: the conferences with the American envoys are suspended, with little hope of their being resumed.",
      what='the Paris paragraph of 6 August',
      printings=[k(GUS, '09-30', 2),
                 k(NH, '09-30', 3),
                 k(ORA, '10-04', 1),
                 k(POR, '10-06', 1),
                 k(RL, '10-07', 1),
                 (k(VA, '10-07', 2), {'field': CA, 'core': [r'f\s*hr\s+conferences\s+opened', r'conferences\s+opened\s+at\s+Pari'],
                                      'note': 'RevX lacks this paragraph, so the excerpt comes from the older CA transcription, which is garbled.'}),
                 k(KY, '10-27', 1)]),
 dict(id='constantinople-letter-28-july-1800-kleber-murdered', kind='message_group',
      label="A letter from Constantinople, 28 July 1800: 'General Kleber has been murdered'",
      definition="Printings of a paragraph of London news quoting a letter from Constantinople dated 28 July 1800: 'A few days ago fresh intelligence reached us from Egypt. General Kleber has been murdered, and General Menou has succeeded him in command'; it adds what was reported of the killer and of reprisals at Cairo, and the writer's view that suspicions fell on Menou. A report at second and third hand.",
      role='report', words=60, dateline=False, back=True,
      core=[r'(?:Extract\s+of\s+a\s+)?letter\s+from\s+Constantinople,?\s+(?:dated\s+)?July\s+28', r'CONSTANTINOPLE,?\s+July\s+28\.\s+(?:\W?A\s+few\s+days\s+ago\s+)?\W?(?:F|f)resh\s+intelligence',
            r'General\s+Kleber\s+has\s+been\s+murdered'],
      first="A letter from Constantinople of 28 July 1800: General Kleber has been murdered in Egypt and General Menou has succeeded him.",
      what='the letter from Constantinople',
      printings=[k(POR, '10-13', 2),
                 k(ORA, '10-18', 2),
                 k(NH, '10-21', 3),
                 k(RL, '10-21', 2),
                 k(PJ, '10-22', 2),
                 k(GUS, '10-22', 3),
                 k(VA, '10-31', 2),
                 k(KY, '11-10', 2)]),
 dict(id='london-report-floods-in-china-1800', kind='message_group',
      label="London, 1800: an overland dispatch from Canton reports floods in China",
      definition="Printings of a paragraph of London news: 'An overland dispatch brought recent accounts from Canton, stating that an uncommon succession of rain had laid entire districts in China under water. The great river Hoambo had been swollen to such excess, as totally to wash from its banks' towns and villages. A report at second hand.",
      role='report', words=55, dateline=False, back=True,
      core=[r'(?:The\s+late\s+|An\s+)?overland\s+dispatch\w*\s+brought\s+recent\s+accounts\s+from\s+Canton', r'Recent\s+accounts\s+from\s+Canton,?\s+state'],
      first='An overland dispatch from Canton, reported in London: floods have laid whole districts of China under water.',
      what='the report of floods in China',
      printings=[k(POR, '10-13', 2),
                 k(ORA, '10-18', 2),
                 k(NH, '10-21', 2),
                 k(RL, '10-21', 2),
                 k(GUS, '10-21', 2),
                 k(PJ, '10-22', 2),
                 k(VA, '10-31', 2),
                 k(KY, '11-10', 2)]),
 dict(id='whitworth-convention-with-denmark-1800', kind='message_group',
      label="London, September 1800: Lord Whitworth's convention with Denmark, and his note",
      definition="Printings of a paragraph of London news: 'It was on the 29th ult. that Lord Whitworth signed the Convention with Count Bernstorff, the Danish Minister. The following is a note written by his Lordship to one of our Ministers abroad on the subject', followed by the note ('I have the satisfaction to acquaint you that I yesterday signed a convention with the Danish Minister, on terms satisfactory to his Majesty') and, in most papers, what the London paper gives as its principal articles: 'The Danish frigate and convoy, carried into Deal, shall be repaired at the expense of Great-Britain, and then released', and the question of the right to visit convoys adjourned to a negotiation in London. A London paper's report with the British envoy's own note.",
      role='report', words=60, dateline=False, back=True,
      core=[r'(?:It\s+was\s+)?on\s+the\s+\d+(?:st|d|th)\s+ult\w*\.?,?\s+that\s+(?:L|l)ord\s+Whitworth\s+signed', r'Lord\s+Whitworth\s+signed\s+the\s+(?:C|c)onvention'],
      first="London, September 1800: Lord Whitworth has signed a convention with the Danish minister, with his note on it.",
      what="the report of Lord Whitworth's convention",
      printings=[k(GUS, '10-21', 3),
                 k(ORA, '10-25', 2),
                 k(POR, '10-27', 2),
                 k(NH, '10-28', 2),
                 (k(RL, '10-28', 2), {'field': CA, 'core': [r'(?:It\s+was\s+)?on\s+the\s+\d+(?:st|d|th)\s+ult\w*\.?,?\s+that\s+(?:L|l)ord\s+Whit\s?worth\s+signed'],
                                      'note': "The Republican Ledger misprints 'Count' as 'Cunot'; RevX reads the misprint as an offensive word, so the excerpt comes from the older CA transcription, which keeps the printed spelling."}),
                 k(PJ, '10-29', 2),
                 (k(NI, '11-03', 4), {'note': "The National Intelligencer prints 'the 9th ult.' where the others have the 29th."}),
                 k(KY, '11-10', 3)]),
 dict(id='convention-prolonging-the-armistice-in-germany-1800', kind='document_group',
      label='The convention of September 1800 prolonging the armistice in Germany',
      definition="Printings of the convention 'For the prolongation of the suspension of arms between the French army of the Rhine and the army of his Imperial Majesty in Germany', agreed by the Count de Lehrbach and the Baron de Lauer for the Emperor and a general of brigade for the French army of the Rhine in September 1800: the Emperor 'consents that the places of Philippsburg, Ulm, and the fortresses which depend upon it, with the place of Ingolstadt ... shall be given up to the disposition of the French army, as a pledge of his intentions'. Most papers print it after General Moreau's letter announcing it. The two sides' agreement, as the papers printed it.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:C\s?ONVENTION\s+)?(?:F\s?OR|for)\s+(?:the|a)\s+(?:P|p)rolongation\s+of\s+the\s+(?:S|s)uspension\s+of\s+(?:A|a)rms'],
      first='The convention of September 1800 prolonging the armistice between the French army of the Rhine and the Emperor\'s army in Germany.',
      what='the convention prolonging the armistice',
      printings=[k(GUS, '11-07', 2),
                 k(ORA, '11-08', 2),
                 k(POR, '11-10', 1),
                 k(NI, '11-10', 2),
                 k(NH, '11-11', 2),
                 k(PJ, '11-12', 1),
                 k(KY, '12-08', 2)]),
 dict(id='congress-meets-in-washington-november-1800', kind='context_group',
      label="Congress meets in Washington, November 1800: the President's speech, the answers of the two houses and his replies",
      children=['president-speech-22-november-1800', 'senate-address-25-november-1800', 'president-reply-to-the-senate-november-1800',
                'house-address-november-1800', 'president-reply-to-the-house-november-1800'],
      definition="The President's speech at the opening of the second session of the Sixth Congress, the first held in the new city of Washington, on 22 November 1800, the addresses of the Senate and the House of Representatives in answer, and his replies, as the papers printed them. Contains those five groups."),
 dict(id='president-speech-22-november-1800', parent='congress-meets-in-washington-november-1800', kind='document_group',
      label="The President's speech to Congress, 22 November 1800",
      definition="Printings of the President's speech to both houses in the Senate chamber on 22 November 1800: 'Immediately after the adjournment of Congress, at their last session in Philadelphia, I gave directions, in compliance with the laws, for the removal of the public offices, records and property'; it speaks of the new seat of government, the District of Columbia, the convention with France, the army and navy, and the finances. The President's own speech.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:G\s?ENTLEMEN|Gentlemen)\s+of\s+the\s+Senate,?\s+and\s+(?:G|g)entlemen\s+of\s+the\s+House\s+of\s+Representatives[.,]?\s+(?:I\s?MMEDIATELY|Immediately)\s+after\s+the\s+adjournment',
            r'(?:I\s?MMEDIATELY|Immediately)\s+after\s+the\s+adjournment\s+of\s+(?:C|c)ongress,?\s+at\s+their\s+last\s+session'],
      first="The President's speech of 22 November 1800, the first to Congress in the city of Washington.",
      what="the President's speech",
      printings=[k(NI, '11-24', 1),
                 k(PJ, '12-03', 2),
                 k(ORA, '12-06', 2),
                 k(POR, '12-08', 1),
                 k(ALX, '12-08', 1),
                 k(NH, '12-09', 2),
                 k(RL, '12-09', 2),
                 k(KY, '12-15', 2)]),
 dict(id='senate-address-25-november-1800', parent='congress-meets-in-washington-november-1800', kind='document_group',
      label="The Senate's address of 25 November 1800 in answer to the President's speech",
      definition="Printings of the address agreed to in the Senate on 25 November 1800: 'Impressed with the important truth, that the hearts of Rulers and People are in the hand of the Almighty, the Senate of the United States most cordially join in your invocations for appropriate blessings upon the government and people of this Union'. The Senate's own address.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:SIR,?\s+)?(?:I\s?MPRESSED|Impressed)\s+with\s+the\s+important\s+truth,?\s+(?:that\s+)?the\s+hearts\s+of\s+(?:R|r)ulers'],
      first="The Senate's address of 25 November 1800 answers the President's speech.",
      what="the Senate's address",
      printings=[k(NI, '11-26', 2),
                 k(GUS, '11-29', 3),
                 k(RL, '12-09', 2),
                 k(PJ, '12-10', 2),
                 k(ALX, '12-10', 1),
                 k(ORA, '12-13', 2),
                 k(POR, '12-15', 1),
                 k(NH, '12-16', 2),
                 k(KY, '12-29', 2)]),
 dict(id='president-reply-to-the-senate-november-1800', parent='congress-meets-in-washington-november-1800', kind='document_group',
      label="The President's reply to the Senate, November 1800",
      definition="Printings of the President's reply to the Senate's address: 'For this excellent address, so respectful to the memory of my illustrious predecessor, which I receive from the Senate of the United States at this time, and in this place, with peculiar satisfaction, I pray you to accept of my unfeigned acknowledgments'. The President's own reply.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:Mr\.?\s+President,?\s+and\s+Gentlemen\s+of\s+the\s+Senate[.,]?\s+)?(?:F\s?OR|For)\s+this\s+excellent\s+address'],
      first="The President's reply to the Senate's address, November 1800.",
      what="the President's reply to the Senate",
      printings=[k(NI, '11-28', 1),
                 k(GUS, '12-01', 2),
                 k(PJ, '12-10', 2),
                 k(ALX, '12-10', 4),
                 k(ORA, '12-13', 2),
                 k(POR, '12-15', 1),
                 k(NH, '12-16', 2),
                 k(RL, '12-16', 1),
                 k(KY, '12-29', 2)]),
 dict(id='house-address-november-1800', parent='congress-meets-in-washington-november-1800', kind='document_group',
      label="The House of Representatives' address in answer to the President's speech, November 1800",
      definition="Printings of the address of the House of Representatives in answer to the speech: 'The House of Representatives have received with great respect, the communication which you have been pleased to make to the two Houses of Congress, at the commencement of the present session'. The House's own address.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:SIR,?\s+)?(?:T\s?HE|The)\s+House\s+of\s+Representatives\s+have\s+received,?\s+with\s+great\s+respect'],
      first="The House of Representatives' address answers the President's speech, November 1800.",
      what="the House's address",
      printings=[k(NI, '11-28', 1),
                 k(GUS, '12-01', 2),
                 k(PJ, '12-10', 2),
                 k(ALX, '12-11', 1),
                 k(ORA, '12-13', 2),
                 k(KY, '12-15', 3),
                 k(POR, '12-15', 1),
                 k(NH, '12-16', 2),
                 k(RL, '12-16', 1)]),
 dict(id='president-reply-to-the-house-november-1800', parent='congress-meets-in-washington-november-1800', kind='document_group',
      label="The President's reply to the House of Representatives, November 1800",
      definition="Printings of the President's reply to the House's address: 'Compelled by the habits of a long life, as well as by all the principles of society and government, which I could ever understand and believe, to consider a firm adherence to the constitution, the laws, and the national faith, as the only principle that can deserve the confidence of the people'. The President's own reply.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:M\s?R\.?\s+S\s?PEAKER|Mr\.?\s+Speaker),?\s+(?:A|a)nd\s+(?:G|g)entlemen\s+of\s+the\s+House\s+of\s+Representatives[.,]?\s+\w+,?\s+by\s+the\s+habits\s+of\s+a\s+long\s+life',
            r'(?:C\s?OMPELLED|Compelled),?\s+by\s+the\s+habits\s+of\s+a\s+long\s+life'],
      first="The President's reply to the House's address, November 1800.",
      what="the President's reply to the House",
      printings=[k(NI, '11-28', 1),
                 k(GUS, '12-03', 2),
                 k(ALX, '12-12', 1),
                 k(ORA, '12-13', 2),
                 k(POR, '12-15', 2),
                 k(NH, '12-16', 2),
                 k(RL, '12-16', 1),
                 k(PJ, '12-17', 2),
                 k(KY, '12-29', 2)]),
 dict(id='salem-report-ship-brutus-from-algiers-december-1800', kind='message_group',
      label="Salem, December 1800: the ship Brutus brings word that the Dey of Algiers made the frigate George Washington carry his presents to Constantinople",
      definition="Printings of a report from Salem, Massachusetts, headed 'Latest from Algiers and Gibraltar' in several papers: the ship Brutus, William Brown, commander, had arrived in 32 days from Gibraltar and 40 from Algiers, and 'Capt. Brown informs, that the United States frigate George Washington, capt. Bainbridge, sailed for Constantinople the 19th of Oct. having on board the Algerine General of Marine and suite, with presents, &c. for the Grand Seignior'; by the captain's account the Dey compelled Captain Bainbridge to do so and threatened war if he refused. Most papers go on with the captain's news of Lord Keith's fleet, and seven add a 'Sketch of Algerine Spoliations for the last two years'. The New Hampshire Gazette prints another Salem account of the arrival, dated 12 December, in other words ('By the information of Capt. Brown, it appears that the American Consul and flag are treated with more respect by the Dey of Algiers, than any European nation whatever'), followed by the same paragraphs; it is counted with the others as a printed form of the report. A ship captain's report at second hand.",
      role='report', words=65, dateline=True, back=True,
      core=[r'(?:Latest|Late)\s+from\s+Algiers\s+(?:and|&)\s+Gibralt\w+', r'From\s+ALGIERS\s+(?:and|&)\s+GIBRALT\w+',
            r'arrived\s+(?:at\s+this\s+port|at\s+Salem|here),?\s+the\s+[Ss]hip\s+Brutus', r'[Ss]hip\s+Brutus,?\s+(?:capt\.?\s+)?William\s+Brown'],
      first="Salem, December 1800: the ship Brutus reports that the Dey of Algiers compelled the frigate George Washington to carry his envoy and presents to Constantinople.",
      what='the Salem report of the Brutus',
      printings=[k(ORA, '12-13', 2),
                 k(POR, '12-15', 2),
                 (k(NH, '12-16', 2), {'note': "The New Hampshire Gazette prints another Salem account of the same arrival (dated 12 December), in other words, and goes on with the same paragraphs on Lord Keith's fleet and the Algerine captures; counted with the others as a printed form of the report."}),
                 k(RL, '12-16', 2),
                 k(PJ, '12-17', 2),
                 k(GUS, '12-18', 2),
                 k(NI, '12-24', 3),
                 k(ALX, '12-24', 3),
                 k(VA, '12-30', 3)]),
 dict(id='king-george-speech-11-november-1800', kind='document_group',
      label="The King's speech to Parliament, 11 November 1800",
      definition="Printings of the speech with which King George III opened Parliament on 11 November 1800: 'My tender concern for the welfare of my Subjects, and a sense of the difficulties with which the poorer classes particularly have to struggle, from the present high price of provisions, have induced me to call you together at an earlier period than I had otherwise intended'; it speaks of the scarcity of grain, the negotiations for peace, and the war. The papers give two different introductions. The King's own speech.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:My\s+Lords\s+and\s+Gentlemen,?\s+)?(?:M|m)y\s+tender\s+concern\s+for\s+the\s+welfare\s+of\s+my\s+(?:S|s)ubjects'],
      first="The King's speech of 11 November 1800 calls Parliament early because of the high price of provisions.",
      what="the King's speech",
      printings=[k(POR, '12-22', 2),
                 k(ORA, '12-22', 2),
                 k(NH, '12-23', 5),
                 k(RL, '12-23', 2),
                 k(GUS, '12-24', 2),
                 k(NI, '12-29', 2),
                 k(ALX, '12-29', 2),
                 k(PJ, '12-31', 2)]),
 dict(id='convention-between-france-and-the-united-states-1800', kind='document_group',
      label='The convention between France and the United States, signed 30 September 1800',
      definition="Printings of the text of the convention signed at Paris on 30 September 1800 by the French plenipotentiaries and the American envoys, before the Senate had acted on it, in two translations. Six papers print the one that begins 'The First Consul of the French Republic, in the name of the French people, and the President of the United States of America, equally animated with a desire to put an end to the differences which have arisen between the two States' and whose first article reads 'There shall be a firm, inviolable and universal peace' (the National Intelligencer gives its opening in somewhat different words: 'The Premier Consul of the French Republic in the name of the people of France, and the President of the United States of America, equally desirous to terminate the differences'); the Alexandria Advertiser and the Virginia Argus print another, from the Paris papers, whose first article reads 'There shall be a sincere and universal Peace, and inviolable Friendship between the two countries'. Counted together as one item in two printed forms. The two governments' agreement, as printed before ratification.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:T\s?HE\s+)?(?:First|Premier)\s+Consul\s+of\s+the\s+French\s+Republic,?\s+in\s+the\s+name\s+of\s+the\s+(?:French\s+)?(?:P|p)eople(?:\s+of\s+France)?,?\s+and\s+the\s+President',
            r'(?:T\s?HE\s+)?(?:First|Premier)\s+Consul\s+of\s+the\s+French\s+Republic.{0,300}?sister\s+Republics'],
      first='The convention of 30 September 1800 between France and the United States, printed before ratification.',
      what='the convention with France',
      printings=[k(ORA, '12-22', 1),
                 (k(NI, '12-22', 2), {'note': "The National Intelligencer gives the opening of this translation in somewhat different words ('The Premier Consul ... equally desirous to terminate the differences')."}),
                 k(NH, '12-23', 2),
                 k(RL, '12-23', 2),
                 (k(ALX, '12-23', 2), {'note': 'The other translation, from the Paris papers.'}),
                 k(PJ, '12-24', 2),
                 (k(VA, '12-26', 5), {'note': 'The other translation, from the Paris papers.'}),
                 k(POR, '12-29', 1)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809 and 1797): "SALEM, DEC. 11."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False):
    for core in cores:
        m = re.search(core, text, re.I | re.S)
        if m:
            start = m.start()
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
            problems.append((s['id'], key, 'page not in the 1800 pages'))
            continue
        text_fields = pages[key]['texts']
        cores = over.get('core', s['core'])
        if key in MISFILED:     # this page's RevX slot holds another scan page's text: read the CA text of the scan page
            fields = [CA]
        else:
            fields = [over['field']] if 'field' in over else [REVX, CA]
        for field in fields:
            text = text_fields.get(field) or ''
            start = item_start(text, cores, over.get('dateline', s.get('dateline', True)), over.get('back', s.get('back', False)))
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
        r['id'] = f'S00-{n:03}'
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
               'admission_rule': 'Reviewed 1800 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1800/'
    return {
        'ledger_id': 'ledger:stories-1800', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1800', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1800, and of 1799 where they reach the 1800 pages (long-running ones '
                   'included), phrase searches on all 2,575 pages of 1800 in both transcriptions, reading of every hit, and scan checks of each '
                   'admitted passage, by the one admission rule (9 or more papers admitted, 7 or 8 chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1799.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1800.py': 'ledger_code', 'work/archive_data/ledgers/stories_1800_review.json': 'scan_review',
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
