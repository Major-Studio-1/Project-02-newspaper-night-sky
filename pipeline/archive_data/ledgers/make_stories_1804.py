"""Write ledgers/stories_1804.json: reviewed stories of 1804, round one.

1804 is read by the one admission rule of the other reviewed years (make_stories_1809.py,
outputs/story_discovery_1809/README.md): every single printed item in 9 or more newspapers is admitted, except digests;
items in 7 or 8 papers are chosen to cover the months and the kinds of news; a sub-story may have fewer papers when its
parent reaches 7; counts are made item by item. The automatic families first printed in 1804 that reach 3 or more
papers, long-running ones included, were split into single printed items with work/story_items.py --long-running
(items.json), and again with year 1803 over the 1804 pages (items_from_1803.json); the items in 7 or more papers were
read, every chosen item and every candidate set aside was counted with phrase searches over all 3,472 pages of 1804 in
both transcriptions (work/story_phrase_search.py, phrase_patterns.json, phrase_hits.json), and every hit was read.
See outputs/story_discovery_1804/README.md.

The 1804 pages are those whose issue the data release dates to 1804 (work/year_search_pages.py 1804 … --printed-dates).
Seven Kentucky Gazette issues of 13 November to 25 December 1804 are filed under 1806 and dated as printed since release
v0.10.2: their page keys keep the filed date (k() below), as page ids do.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as
apply_ledger.py does: the excerpt is the opening of the printed item (about 40-60 words), starting with its
dateline or heading when one stands directly before it. Scan findings, crops and hand-drawn boxes are merged from
stories_1804_review.json after the scan check.

Seventeen 1804 pages have their RevX transcriptions filed one page off from the scans (derived/revx_page_map.parquet). A
printing on a page whose RevX slot holds another page's text names the scan page and takes its excerpt from the CA
transcription of that page, which is numbered as the scans are (one printing here: the Natchez report in Jenks' Portland
Gazette of 24 September).

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied. The defaults assume it follows v0.11.8; a review of
1800 ran at the same time and may take v0.11.9 first, in which case rerun with the real numbers:
    python work/archive_data/ledgers/make_stories_1804.py [--table] [--base 0.11.8 --target 0.11.9]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1804/search_pages.json). The excerpts are cut
from the 1804 pages, which no release since v0.10.2 changes, so the ledger is the same whatever the base, except for its
two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1804'
PAGES = PROJECT/'outputs/story_discovery_1804/search_pages.json'
REVIEW = HERE/'stories_1804_review.json'
OUT = HERE/'stories_1804.json'
BASE, TARGET = '0.11.8', '0.11.9'   # defaults; see the docstring
DATA_RELEASE = '0.11.8'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-23'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

NI, NHG, OP, KG, ADA, BJ, JPG = 'sn83045242', 'sn83025588', 'sn84023351', 'sn84038147', 'sn84024012', 'sn85059525', 'sn83016081'
RIR, VA, MIR, EN, NG = 'sn83021188', 'sn84024710', 'sn84020402', 'sn84024736', 'sn85025815'
PAPER = {NI: 'The National Intelligencer', NHG: 'The New Hampshire Gazette', OP: 'The Oracle Post',
         KG: 'The Kentucky Gazette and General Advertiser', ADA: 'The Alexandria Daily Advertiser',
         BJ: 'The Berkeley and Jefferson Intelligencer', JPG: "Jenks' Portland Gazette", RIR: 'The Rhode-Island Republican',
         VA: 'The Virginia Argus', MIR: 'The Mirror of the Times', EN: 'The Enquirer', NG: 'The Norfolk Gazette and Publick Ledger'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper, printed date (MM-DD in 1804), page and edition. The Kentucky Gazette's issues of
    13 November to 25 December 1804 are filed under 1806 (dated as printed since v0.10.2); their keys keep the filed date."""
    filed = '1806' if paper == KG and date >= '11-13' else YEAR
    return f'{paper}|{filed}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR) or key(r['page_id']).startswith(KG+'|1806-1')}


MISFILED = misfiled()

# Story groups. A parent ('children') holds sub-stories ('parent'). 'printings' lists each printing's page; a tuple adds
# overrides for that printing: core (regexes for the item's first words), role, field, note, words, dateline (include a
# dateline directly before), back (start at the beginning of the sentence that holds the core), stop (a regex: the excerpt
# ends before it, to end before private persons' names).
STORIES = [
 dict(id='haitian-proclamation-of-independence-29-november-1803', kind='document_group',
      label="The proclamation of Dessalines, Christophe and Clerveaux, chiefs of St. Domingo, 29 November 1803: 'The independence of St. Domingo is proclaimed'",
      definition="Printings of the proclamation done 'at the head-quarters, Fort Dauphin, November 29, 1803' and signed by Dessalines, Christophe and Clerveaux, under the heading 'PROCLAMATION of Dessalines, Christophe and Clerveaux, Chiefs of St. Domingo': 'In the name of the black people and men of colour of St. Domingo. The independence of St. Domingo is proclaimed. Restored to our primitive dignity, we have claimed our rights; we swear never to yield them to any power on earth.' The three generals' own words, in the English translation the papers received from New York and Philadelphia.",
      role='published_document', words=55, dateline=False,
      core=[r'P\s?ROCLAMATION\.?,?\s+(?:OF|of|Of|or)\s+D\s?ESSALINES'],
      first="The proclamation of the chiefs of St. Domingo, 29 November 1803: 'The independence of St. Domingo is proclaimed.'",
      what='the proclamation of the chiefs of St. Domingo',
      printings=[k(ADA, '01-09', 3),
                 k(NI, '01-13', 2),
                 k(JPG, '01-14', 2),
                 k(OP, '01-17', 3),
                 k(RIR, '01-19', 2),
                 k(BJ, '01-20', 1),
                 k(KG, '02-14', 2)]),
 dict(id='louisiana-taken-into-possession-december-1803', kind='context_group',
      label="The United States take possession of Louisiana, December 1803: General Wilkinson's orders and Governor Claiborne's proclamation",
      children=['wilkinson-orders-before-new-orleans-17-december-1803', 'claiborne-proclamation-at-new-orleans-20-december-1803'],
      definition="Two documents of the handing over of New Orleans and Louisiana to the United States in December 1803, as the papers printed them in January 1804: General Wilkinson's orders to the American troops before New Orleans, 17 December 1803, and Governor Claiborne's proclamation that the government of Spain and France over the province has ceased. Contains those two groups."),
 dict(id='wilkinson-orders-before-new-orleans-17-december-1803', parent='louisiana-taken-into-possession-december-1803', kind='document_group',
      label="General Wilkinson's orders at the camp near New Orleans, 17 December 1803: 'The operation before us, however simple or safe, will require much self denial and restraint'",
      definition="Printings of an extract from the orders of General Wilkinson 'given at the camp of the American troops, on the left bank of the Mississippi, near the city of New Orleans, Dec. 17, 1803', with the parole 'Columbia': 'The operation before us, however simple or safe, will require much self denial and restraint'; the orders tell the troops how they are to conduct themselves on entering the city. A commander's orders, as printed.",
      role='published_document', words=55, dateline=True,
      core=[r'Extra\w*\s+from\s+the\s+(?:orders?|[Ll]etters?)\s+of\s+Gen'],
      first="General Wilkinson's orders before New Orleans, 17 December 1803: 'The operation before us, however simple or safe, will require much self denial and restraint.'",
      what="General Wilkinson's orders",
      printings=[k(NI, '01-16', 3),
                 k(ADA, '01-17', 3),
                 k(KG, '01-24', 2),
                 k(RIR, '01-26', 2),
                 k(JPG, '01-28', 2),
                 k(NHG, '01-31', 2),
                 k(OP, '01-31', 3)]),
 dict(id='claiborne-proclamation-at-new-orleans-20-december-1803', parent='louisiana-taken-into-possession-december-1803', kind='document_group',
      label="Governor Claiborne's proclamation at New Orleans, December 1803: the government of Louisiana under Spain and France has ceased",
      definition="Printings of the proclamation 'By his Excellency William C. C. Claiborne, Governor of the Mississippi Territory, exercising the powers of Governor-General and Intendant of the province of Louisiana', issued at New Orleans on taking possession in December 1803: it recites the cession of Louisiana from Spain to France and from France to the United States, and declares that 'the government heretofore exercised over the said Province of Louisiana, as well under the authority of Spain as of the French republic' has ceased and that of the United States is established. The governor's own words; Jenks' Portland Gazette prints only its beginning ('It begins:').",
      role='published_document', words=55, dateline=True,
      core=[r'(?:P\s?ROCLAMATION\.\s+)?B\s?(?:Y|y)\s+(?:his|His|HIS)\s+(?:Excellency|excellency|EXCELLENCY)\s+W\w*\.?\s+C\.\s+(?:C\.\s+)?C\s?(?:LAIBORNE|laiborne)'],
      first="Governor Claiborne's proclamation at New Orleans, December 1803: the government of Louisiana under Spain and France has ceased, and that of the United States is established.",
      what="Governor Claiborne's proclamation",
      printings=[k(NI, '01-16', 3),
                 k(ADA, '01-17', 3),
                 k(KG, '01-24', 2),
                 k(RIR, '01-26', 2),
                 k(BJ, '01-27', 2),
                 (k(JPG, '01-28', 2), {'note': "Prints the proclamation's beginning after its own summary ('It begins:')."}),
                 k(NHG, '01-31', 2),
                 k(OP, '01-31', 3)]),
 dict(id='norfolk-report-of-the-fire-of-22-february-1804', kind='message_group',
      label="A Norfolk report of 25 February 1804: 'DEPLORABLE AND DISTRESSING FIRE!!'",
      definition="Printings of a Norfolk report dated 25 February 1804 of the fire that broke out there on the night of Wednesday 22 February: 'On Wednesday night, about eleven o'clock, the inhabitants were roused from their beds with the repeated cry of FIRE!'; houses were blown up to stop its progress, and the report gives the losses. Five papers print it under the heading 'Deplorable and Distressing Fire!!', two in a shorter form. A local paper's report. The excerpts end before the name of the owner of the warehouse where the fire began.",
      role='report', words=45, dateline=False, stop=r'which\s+was\s+(?:perceived|received)|in\s+the\s+ware\s*-?\s*house',
      core=[r'(?:From\s+)?N\s?ORFOLK[,.]?\s+(?:\(V\w*\.?\)\s+)?F(?:EB|eb)\w*\.?\s+2[59]\.', r'F(?:EBRUARY|ebruary)\s+25\.\s+D\s?EPLORABLE'],
      first="A Norfolk report of 25 February 1804: a fire on the night of Wednesday 22 February.",
      what='the Norfolk report of the fire',
      printings=[k(VA, '02-29', 3),
                 k(ADA, '03-03', 3),
                 k(NI, '03-07', 2),
                 k(BJ, '03-09', 2),
                 (k(JPG, '03-17', 2), {'note': 'The shorter form of the report, under the heading "Particulars of the late Destructive Fire at Norfolk".'}),
                 (k(NHG, '03-20', 2), {'note': 'The shorter form of the report, under the heading "GREAT FIRE".'}),
                 k(KG, '03-20', 3)]),
 dict(id='frigate-philadelphia-lost-and-burned-1804', kind='context_group',
      label='The frigate Philadelphia, lost before Tripoli and burned in its harbour, 1804',
      children=['bainbridge-letter-with-the-presidents-message-march-1804', 'preble-letter-to-the-consul-at-gibraltar-on-the-philadelphia',
                'decatur-letter-to-preble-17-february-1804', 'decatur-made-captain-official-notice-may-1804'],
      definition="Four documents on the United States frigate Philadelphia, as the 1804 papers printed them: the President's message of 20 March sending Captain Bainbridge's letter, dated Tripoli, 1 November 1803, on the frigate's wreck on rocks near Tripoli and its capture; Commodore Preble's letter to the American consul at Gibraltar on its burning; Lieutenant Decatur's own report of 17 February 1804 that his party set the frigate on fire in the harbour of Tripoli; and the official notice of his promotion. Contains those four groups."),
 dict(id='bainbridge-letter-with-the-presidents-message-march-1804', parent='frigate-philadelphia-lost-and-burned-1804', kind='document_group',
      label="The President's message of 20 March 1804 with Captain Bainbridge's letter on the loss of the frigate Philadelphia",
      definition="Printings of the President's message delivered to both Houses on 20 March 1804 by Mr. Harvie: 'I communicate to Congress a letter received from captain Bainbridge, commander of the Philadelphia frigate, informing us of the wreck of that vessel on the coast of Tripoli, and that himself, his officers and men, have fallen into the hands of the Tripolitans'; it asks for an addition to the naval appropriation. Most papers print with it the captain's letter, dated Tripoli, 1 November 1803: 'Misfortune necessitates me to make a communication the most distressing of my life'. The Kentucky Gazette printed the letter in its next issue. The President's message, and the captain's own account.",
      role='published_document', words=50, dateline=False,
      core=[r'T\s?o\s+the\s+Senate\s+and\s+House\s+of\s+Representatives\s+of\s+the\s+United\s+States[.,;:]?\s+["“]?I\s+communicate\s+to\s+Congress'],
      first="The President's message of 20 March 1804 sends Congress Captain Bainbridge's letter on the wreck and capture of the frigate Philadelphia before Tripoli.",
      what="the President's message with Captain Bainbridge's letter",
      printings=[k(NI, '03-21', 2),
                 k(VA, '03-28', 2),
                 k(BJ, '03-30', 2),
                 (k(KG, '04-03', 3), {'note': "The message alone; the Kentucky Gazette printed Captain Bainbridge's letter in its next issue (10 April, page 2: 'Letter accompanying the President's message to congress, published in our last')."}),
                 k(RIR, '04-05', 2),
                 (k(JPG, '04-07', 4), {'field': CA, 'core': [r'Yef\w+\s+the\s+following\s+Mef'], 'note': 'RevX has no text for this page, so the excerpt comes from the older CA transcription.'}),
                 k(NHG, '04-10', 2),
                 k(OP, '04-10', 2)]),
 dict(id='preble-letter-to-the-consul-at-gibraltar-on-the-philadelphia', parent='frigate-philadelphia-lost-and-burned-1804', kind='message_group',
      label="Commodore Preble's letter to the American consul at Gibraltar on the burning of the frigate Philadelphia, published May 1804",
      definition="Printings of a letter from Commodore Preble, dated on board the frigate Constitution in Syracuse harbour in February 1804, to John Gavino, the American consul at Gibraltar, reporting that the frigate Philadelphia had been boarded in the harbour of Tripoli and set on fire, and 'left ... in a blaze'. It came by Captain Calver (or Calvert) of the ship Maria from Cadiz: seven papers print it after a Philadelphia paragraph of 16 May ('By the politeness of capt. Calver, of the ship Maria, arrived last night from Cadiz, we are favored with a copy of the following important letter'), two after a Boston paragraph ('Official account of the destruction of the United States frigate Philadelphia'). The commodore's own report, as a newspaper obtained it.",
      role='report', words=55, dateline=True,
      core=[r'(?:IMPORTANT[!.]?\s+)?P\s?HILADELPHIA,?\s+M(?:ay|AY)\s+16', r'Official\s+account\s+of\s+the\s+[Dd]estruction'],
      first="Philadelphia, 16 May 1804: by the ship Maria from Cadiz, a copy of Commodore Preble's letter to the consul at Gibraltar on the burning of the frigate Philadelphia.",
      what="Commodore Preble's letter to the consul at Gibraltar",
      printings=[k(NI, '05-18', 3),
                 k(VA, '05-23', 3),
                 k(EN, '05-23', 2),
                 (k(RIR, '05-24', 3), {'field': CA, 'core': [r'May\s+16\W+By\s+th\w\s+polite'], 'stop': r'Extra.\s+of\s+a\s+letter\s+frem',
                                        'note': 'RevX has no text for this page, so the excerpt comes from the older CA transcription; its reading order runs into a neighbouring column, so the excerpt stops at the end of the opening paragraph.'}),
                 k(BJ, '05-25', 2),
                 (k(JPG, '05-28', 4), {'note': "With a Boston paragraph of 21 May ('Official account of the destruction of the United States frigate Philadelphia')."}),
                 k(NHG, '05-29', 2),
                 (k(OP, '05-29', 2), {'note': "With a Boston paragraph of 25 May ('Official account of the Destruction of the United States frigate Philadelphia')."}),
                 k(KG, '06-05', 3)]),
 dict(id='decatur-letter-to-preble-17-february-1804', parent='frigate-philadelphia-lost-and-burned-1804', kind='document_group',
      label="Lieutenant Decatur's letter to Commodore Preble, 17 February 1804: the frigate Philadelphia destroyed in the harbour of Tripoli",
      definition="Printings of Lieutenant Decatur's report to Commodore Preble, dated 'On board the ketch Intrepid, at sea, February 17th, 1804': 'I have the honor to inform you, that in pursuance of your orders of the 1st inst. to proceed with this ketch off the harbour of Tripoli, there to endeavour to effect the destruction of the late frigate Philadelphia', he went in with the brig Syren in company, boarded the frigate and set her on fire. Published by the government in Washington on 23 May with other letters of the squadron. The officer's own account.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:Copy\s+of\s+a\s+)?[Ll]etter\s+from\s+L(?:ieu)?t\.?\s+Decatur\s+to\s+Com', r'On\s+board\s+(?:of\s+)?the\s+(?:KETCH|Ketch|ketch)\s+I\s?NTREPID'],
      first="Lieutenant Decatur reports to Commodore Preble, 17 February 1804, that his party destroyed the frigate Philadelphia in the harbour of Tripoli.",
      what="Lieutenant Decatur's letter",
      printings=[k(NI, '05-23', 3),
                 k(EN, '05-26', 3),
                 k(VA, '05-30', 2),
                 k(RIR, '05-31', 3),
                 k(JPG, '06-04', 2),
                 k(OP, '06-05', 2),
                 (k(BJ, '06-08', 1), {'field': CA, 'core': [r'On\s+board\s+thr'], 'note': 'RevX has no text for this page, so the excerpt comes from the older CA transcription.'})]),
 dict(id='decatur-made-captain-official-notice-may-1804', parent='frigate-philadelphia-lost-and-burned-1804', kind='document_group',
      label="'As a testimonial of the President's high opinion': the official notice of 25 May 1804 that Lieutenant Decatur is made a captain",
      definition="Printings of a paragraph headed 'OFFICIAL' in the National Intelligencer of 25 May 1804: 'As a testimonial of the President's high opinion of the gallant conduct of Lieutenant Decatur, in taking and destroying the frigate the Philadelphia, a commission to him as Captain in the Navy has been duly issued, and will without delay be transmitted to Commodore Preble.' The government paper's notice.",
      role='published_document', words=50, dateline=True, stop=r'Official\.\s+Extract\s+of\s+a\s+letter',
      core=[r'(?:OFFICIAL\.\s+)?As\s+a\s+testimonial\s+of\s+the\s+P\s?(?:RESIDENT|resident)'],
      first="The official notice of 25 May 1804: Lieutenant Decatur is given a captain's commission for taking and destroying the frigate Philadelphia.",
      what='the official notice of Decatur\'s commission',
      printings=[k(NI, '05-25', 2),
                 k(VA, '05-30', 2),
                 k(EN, '05-30', 3),
                 k(BJ, '06-01', 3),
                 k(JPG, '06-04', 2),
                 k(OP, '06-05', 2),
                 k(RIR, '06-07', 3),
                 k(KG, '06-12', 3)]),
 dict(id='impeachment-of-judge-chase-1804', kind='context_group',
      label="The impeachment of Judge Chase, 1804: the articles reported to the House, and the judge's memorial",
      children=['chase-articles-reported-26-march-1804', 'chase-memorial-on-the-impeachment-april-1804', 'chase-articles-reported-30-november-1804'],
      definition="Documents of the House of Representatives' impeachment of Samuel Chase, one of the associate justices of the Supreme Court, as the 1804 papers printed them: the articles of impeachment its committee reported on 26 March 1804, the judge's memorial on the proceedings, published in April, and the articles its committee reported again on 30 November 1804. His trial before the Senate in 1805 is a reviewed story of 1805. Contains those three groups."),
 dict(id='chase-articles-reported-26-march-1804', parent='impeachment-of-judge-chase-1804', kind='document_group',
      label='The articles of impeachment against Judge Chase reported to the House, 26 March 1804',
      definition="Printings of the report of the committee appointed to prepare articles of impeachment against Samuel Chase, laid on the table of the House on 26 March 1804: 'Articles exhibited by the House of Representatives of the United States, in the name of themselves and of all the people of the United States, against Samuel Chase, one of the associate justices of the Supreme Court of the United States, in maintenance and support of their impeachment against him, for high crimes and misdemeanors', the first article on his conduct at the trial of John Fries. The House's charges as its committee drafted them (allegations). The articles reported again on 30 November are a group of their own.",
      role='published_document', words=60, dateline=False,
      core=[r'R\s?EPORT\s+Of\s+the\s+[Cc]ommittee\s+appointed\s+to\s+prepare', r'Articles\s+of\s+impeachment\.\s+Articles\s+exhibited'],
      first="The articles of impeachment against Samuel Chase, as the House's committee reported them on 26 March 1804.",
      what='the articles of impeachment of March',
      printings=[(k(NI, '03-28', 3), {'field': CA, 'stop': r'On\s+Sunday\s+evening',
                                       'note': 'RevX has no text for this page, so the excerpt comes from the older CA transcription; its reading order runs into a neighbouring column after the heading, so the excerpt is the heading alone.'}),
                 k(ADA, '03-30', 3),
                 k(VA, '04-04', 2),
                 k(NHG, '04-17', 2),
                 k(OP, '04-24', 1),
                 k(KG, '05-01', 5)]),
 dict(id='chase-memorial-on-the-impeachment-april-1804', parent='impeachment-of-judge-chase-1804', kind='document_group',
      label="Judge Chase's memorial on the impeachment, with his letter to the Federal Gazette, April 1804",
      definition="Printings of a letter from Samuel Chase to the editors of the (Baltimore) Federal Gazette that opens 'As soon as there appeared reason for believing, that the house of representatives intended to adjourn, without preferring articles before the senate, in support of the impeachment voted against me, the inclosed memorial was prepared, and transmitted (on Saturday last) to a member', with the memorial itself, addressed to the House. The accused judge's own argument.",
      role='published_document', words=55, dateline=False,
      core=[r'G\s?ENTLEMEN,\s+A\s?S\s+soon\s+as\s+there\s+appeared'],
      first="Judge Chase's letter to the Federal Gazette, with his memorial on the impeachment voted against him.",
      what="Judge Chase's letter and memorial",
      printings=[k(ADA, '04-03', 2),
                 k(NI, '04-04', 1),
                 k(VA, '04-11', 5),
                 k(OP, '04-17', 1),
                 k(BJ, '04-20', 1),
                 k(JPG, '04-21', 1),
                 k(KG, '04-24', 2)]),
 dict(id='chase-articles-reported-30-november-1804', parent='impeachment-of-judge-chase-1804', kind='document_group',
      label='The articles of impeachment against Judge Chase reported to the House again, 30 November 1804',
      definition="Printings of the report of the committee to which the House referred, on 6 November 1804, the report of March: 'The committee to whom was referred, on the sixth instant, the report of a select committee appointed on the thirteenth of March last, \"to prepare and report articles of impeachment against Samuel Chase ...\" submit to the House the following REPORT. Articles exhibited by the House of Representatives ...'. These are the articles the House adopted in December and carried to the Senate, which tried the judge in 1805. The House's charges (allegations).",
      role='published_document', words=60, dateline=False,
      core=[r'T\s?HE\s+committee\s+to\s+whom\s+was\s+referred,?\s+on\s+the\s+sixth', r'R\s?EPORT\.\s+Articles\s+exhibited\s+by'],
      first="The articles of impeachment against Samuel Chase, reported to the House again on 30 November 1804.",
      what='the articles of impeachment of November',
      printings=[k(NI, '12-05', 2),
                 k(EN, '12-11', 1),
                 k(VA, '12-12', 1),
                 k(NG, '12-14', 2),
                 k(BJ, '12-21', 1),
                 k(JPG, '12-24', 1)]),
 dict(id='preble-letter-from-malta-17-january-1804', kind='document_group',
      label="Commodore Preble's letter from Malta, 17 January 1804: 'The coast of Tripoli is extremely dangerous at this season of the year'",
      definition="Printings of an extract of a letter from Commodore Preble to the Secretary of the Navy, dated Malta Harbour, 17 January 1804, published by the government in Washington on 7 May: 'The coast of Tripoli is extremely dangerous at this season of the year, but I could not avoid paying it a visit', with what he met there in December. The commodore's own report.",
      role='published_document', words=55, dateline=True,
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+Com\w+\.?\s+Preble,?\s+to\s+the\s+[Ss]ecretary\s+of\s+the\s+Navy,?\s+dated\s+Malta', r'From\s+Commodore\s+Preble,?\s+to\s+the\s+Secretary\s+of\s+the\s+Navy\.\s+Malta'],
      first="Commodore Preble writes from Malta, 17 January 1804: 'The coast of Tripoli is extremely dangerous at this season of the year.'",
      what="Commodore Preble's letter from Malta",
      printings=[k(NI, '05-07', 3),
                 k(ADA, '05-10', 3),
                 k(VA, '05-12', 3),
                 k(EN, '05-12', 2),
                 k(RIR, '05-17', 3),
                 k(BJ, '05-18', 2),
                 k(JPG, '05-21', 4),
                 k(OP, '05-22', 1),
                 k(KG, '05-22', 3)]),
 dict(id='general-moreau-in-the-papers-1804', kind='context_group',
      label='General Moreau in the papers, 1804: a letter attributed to him, a Paris newsletter\'s correction, and his banishment',
      children=['letter-attributed-to-moreau-nouvelles-a-la-main-march-1804', 'nouvelles-a-la-main-no-3-letters-of-madame-bonaparte-and-madame-moreau',
                'moniteur-announces-moreau-banished-to-america'],
      definition="Three items on General Moreau, held in the Temple at Paris in 1804 as an accomplice of Georges and Pichegru, as the American papers printed them: a letter to Bonaparte that the newsletter Les Nouvelles à la Main (No. II, 9 March 1804) attributed to him; the same newsletter's No. III (20 March), which says that letter was authentic with one exception and prints letters it says passed between Madame Bonaparte and Madame Moreau; and a London paragraph reporting that the Paris Moniteur had announced his banishment to America. Contains those three groups."),
 dict(id='letter-attributed-to-moreau-nouvelles-a-la-main-march-1804', parent='general-moreau-in-the-papers-1804', kind='message_group',
      label="A letter to Bonaparte 'from the dungeon of the Temple', attributed to General Moreau by Les Nouvelles à la Main, March 1804",
      definition="Printings of an item from the newsletter Les Nouvelles à la Main, No. II, Paris, 9 March 1804, under headings such as 'Letter from Moreau to Bonaparte': 'The letter which we now publish, has been circulated all over Paris for this week, and many thousand copies have been sent into the departments'; the letter, 'addressed to Monsieur Bonaparte, the First Consul, by Citizen Moreau', is dated from the dungeon of the Temple and opens 'Since your ambition requires more victims, strike, but do not calumniate those you butcher.' A letter the newsletter attributes to Moreau; its No. III (another group) qualifies it.",
      role='report', words=60, dateline=False,
      core=[r'(?:LETTER\s+FROM\s+)?MOREAU(?:.s\s+LETTER)?\s+TO\s+B\w+\W{0,3}\s+Le\w?\W?\s+Nouvelles', r'Le\w?\W?\s+Nouvelles\s+[aà]\s+la\s+Main'],
      first="Les Nouvelles à la Main, Paris, 9 March 1804, prints a letter to Bonaparte 'from the dungeon of the Temple' that it attributes to General Moreau.",
      what='the letter attributed to Moreau',
      printings=[k(JPG, '05-12', 2),
                 k(OP, '05-15', 2),
                 (k(NI, '05-18', 2), {'field': CA, 'note': 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'}),
                 k(EN, '05-19', 2),
                 k(VA, '05-23', 2),
                 k(BJ, '05-25', 2),
                 k(KG, '06-05', 3)]),
 dict(id='nouvelles-a-la-main-no-3-letters-of-madame-bonaparte-and-madame-moreau', parent='general-moreau-in-the-papers-1804', kind='message_group',
      label="Les Nouvelles à la Main, No. III, March 1804: the letter attributed to Moreau 'authentic, with the exception' of one passage, and letters it says passed between Madame Bonaparte and Madame Moreau",
      definition="Printings of the newsletter's No. III, Paris, 20 March 1804, under headings such as 'Letters between Madame Bonaparte and Madame Moreau': 'In a preceding number we published a letter from General Moreau to the First Consul. We are now informed from good authority, that it was authentic, with the exception that General Moreau, instead of acknowledging himself guilty of the pretended conspiracy, says, that had he conspired ...', followed by two letters it attributes to Madame Bonaparte and Madame Moreau. The newsletter's own correction of its earlier item, and letters it attributes to the two women; the Berkeley and Jefferson Intelligencer prints the letters without the correction.",
      role='report', words=60, dateline=False,
      core=[r'(?:Interesting\s+Correspondence,?\s+)?(?:LETTERS\s+)?BETWEEN\s+MADA?ME?\s+B\w+,?\s+AND\s+MADAME\s+MOREAU'],
      first="Les Nouvelles à la Main, No. III: the letter attributed to Moreau was 'authentic, with the exception' of one passage; and letters said to pass between Madame Bonaparte and Madame Moreau.",
      what="the Nouvelles à la Main's No. III",
      printings=[k(NI, '08-17', 2),
                 k(EN, '08-18', 2),
                 k(JPG, '08-20', 2),
                 k(NG, '08-21', 3),
                 k(VA, '08-22', 2),
                 k(BJ, '08-24', 2),
                 k(KG, '09-11', 2)]),
 dict(id='moniteur-announces-moreau-banished-to-america', parent='general-moreau-in-the-papers-1804', kind='message_group',
      label="'It has been announced in the Paris Moniteur ... that this General has been banished to America': a London paragraph on Moreau, 1804",
      definition="Printings of a paragraph headed 'MOREAU' in most papers, from a London paper: 'It has been announced in the Paris Moniteur, (the government paper) that this General has been banished to America—to what part is not suggested. Other papers mention that he left his prison on the 21st June, and proceeded for Perpignan'. A report at second hand of the French government paper's announcement.",
      role='report', words=50, dateline=False,
      core=[r'(?:M\w*\s?\w*\.?\s*[—-]+\s*)?It\s+has\s+been\s+announced\s+in\s+the\s+Paris\s+Moni'],
      first="A London paragraph: the Paris Moniteur has announced that General Moreau has been banished to America.",
      what='the paragraph on Moreau\'s banishment',
      printings=[k(ADA, '08-28', 3),
                 k(NI, '08-29', 3),
                 k(VA, '09-01', 3),
                 k(EN, '09-01', 2),
                 k(NG, '09-01', 2),
                 k(JPG, '09-03', 2),
                 k(NHG, '09-04', 2),
                 k(KG, '09-11', 3)]),
 dict(id='new-york-report-massacre-at-cape-francois-june-1804', kind='message_group',
      label="A New York report by the pilot boat Grey-Hound, June 1804: 'MASSACRE OF ALL THE WHITES AT CAPE FRANCOIS'",
      definition="Printings of a New York report of 3 or 4 June 1804 under the heading 'MASSACRE OF ALL THE WHITES AT CAPE FRANCOIS' (in some papers 'AT ST. DOMINGO', in one 'OF CAPE-FRANCOIS'): 'By the Pilot Boat Grey-Hound, Capt. Sandford, in 16 days from Cape Francois we have a confirmation of the massacre and pillage at that and other places of the Island by Gen. Dessalines' troops, which commenced on the 19th of April' (the Rhode-Island Republican prints the 10th; the captain's name is also printed Sanford and Stanford). A report at second hand, from the people who arrived on the pilot boat, in the New York paper's words. Dessalines's own proclamation on these events, printed in four papers, is listed among the items not admitted.",
      role='report', words=55, dateline=True,
      core=[r'M\s?ASSACRE\s+OF\s+ALL\s+THE\s+WHITES'],
      first="A New York report, June 1804: by the pilot boat Grey-Hound from Cape François, 'a confirmation of the massacre and pillage' there.",
      what='the New York report from Cape François',
      printings=[k(NI, '06-08', 2),
                 k(VA, '06-09', 3),
                 k(NHG, '06-12', 2),
                 k(OP, '06-12', 3),
                 k(EN, '06-13', 1),
                 k(RIR, '06-14', 2),
                 k(BJ, '06-15', 2),
                 k(KG, '07-03', 6)]),
 dict(id='osage-chiefs-visit-the-president-1804', kind='context_group',
      label='Chiefs of the Osage nation visit the President, 1804',
      children=['lexington-report-osage-chiefs-on-their-way-to-washington', 'presidents-address-to-the-osage-chiefs-1804'],
      definition="Two items on a delegation of Osage chiefs who travelled to Washington in 1804: a Lexington report of their passing through on their way, and the President's address to them, published in October. Contains those two groups."),
 dict(id='lexington-report-osage-chiefs-on-their-way-to-washington', parent='osage-chiefs-visit-the-president-1804', kind='message_group',
      label="Lexington, June 1804: 'twelve Chiefs, deputed from the Osage Nation of Indians, and two boys' on their way to the President",
      definition="Printings of a report from the Kentucky Gazette of 12 June 1804: 'On Saturday evening last twelve Chiefs, deputed from the Osage Nation of Indians, and two boys, arrived in this town, on their way to the City of Washington, on a visit to the President of the United States'; it names the trader who came with them at Captain Lewis's request, and says their object was said to be a treaty. A local paper's report.",
      role='report', words=50, dateline=True,
      core=[r'O\s?N\s+Saturday\s+evening\s+last,?\s+twelve\s+[Cc]hiefs'],
      first="Lexington, June 1804: twelve Osage chiefs and two boys pass through on their way to visit the President.",
      what='the Lexington report of the Osage chiefs',
      printings=[k(KG, '06-12', 3),
                 k(ADA, '06-26', 3),
                 k(NI, '06-29', 2),
                 k(EN, '07-04', 4),
                 k(BJ, '07-06', 2),
                 k(VA, '07-07', 3),
                 k(JPG, '07-09', 2)]),
 dict(id='presidents-address-to-the-osage-chiefs-1804', parent='osage-chiefs-visit-the-president-1804', kind='document_group',
      label="The President's address to the Osage chiefs: 'My Children, White hairs, Chiefs and Warriors of the Osage Nation'",
      definition="Printings of the President's address to the Osage delegation in Washington, which the National Intelligencer published in October 1804 saying that the talks 'will afford as much pleasure to the reader, as they confer honor on the government': 'My Children, White hairs, Chiefs and Warriors of the Osage Nation, I repeat to you assurances of the satisfaction it has given me to receive you here.' The President's own words; the Norfolk Gazette prints it after its own comment.",
      role='published_document', words=50, dateline=False,
      core=[r'M\s?y\s+[Cc]hildren,?\s+White\s+[Hh]airs'],
      first="The President to the Osage chiefs: 'My Children, White hairs, Chiefs and Warriors of the Osage Nation, I repeat to you assurances of the satisfaction it has given me to receive you here.'",
      what="the President's address to the Osage chiefs",
      printings=[k(NI, '10-03', 2),
                 k(VA, '10-10', 1),
                 k(EN, '10-10', 2),
                 k(RIR, '10-11', 2),
                 k(NG, '10-13', 3),
                 k(KG, '10-23', 2),
                 k(NHG, '11-06', 2)]),
 dict(id='london-report-pitt-returns-to-office-may-1804', kind='message_group',
      label="London, May 1804: 'The political views of Mr. Pitt have been at length gratified'",
      definition="Printings of a London paragraph dated May 11–14, 1804, which came by an arrival at New Bedford, under headings such as 'Change of Ministry in England': 'The political views of Mr. Pitt have been at length gratified, and he is now replaced in those situations to which the greatest ambition of any subject, however superior to all others in ability, rank and opulence can aspire.' (Two papers print 'eloquence', and two 'can inspire'.) A London paper's report, in its own words.",
      role='report', words=55, dateline=False,
      core=[r'L\s?(?:ONDON|ondon),?\s+M(?:AY|ay)\s+11'],
      first="London, May 1804: Mr. Pitt is 'now replaced' at the head of the British ministry.",
      what='the London paragraph on Mr. Pitt',
      printings=[k(JPG, '07-16', 1),
                 k(ADA, '07-17', 2),
                 k(NHG, '07-17', 2),
                 k(RIR, '07-19', 2),
                 k(NG, '07-19', 2),
                 k(NI, '07-20', 2),
                 k(VA, '07-21', 2),
                 k(EN, '07-21', 1)]),
 dict(id='death-of-general-hamilton-1804', kind='context_group',
      label='The death of General Hamilton after the duel with Colonel Burr, July and August 1804',
      children=['bishop-moore-letter-on-general-hamilton', 'gouverneur-morris-funeral-oration-over-general-hamilton', 'hamilton-burr-correspondence-published-july-1804',
                'general-hamilton-will-july-1804', 'general-hamilton-statement-on-the-expected-interview', 'coroners-jury-verdict-on-general-hamilton-august-1804'],
      definition="Documents printed after Alexander Hamilton died on 12 July 1804 of a wound received in a duel with Aaron Burr, the Vice President, on the morning of the 11th, as the papers date them: Bishop Moore's letter on his last hours, Gouverneur Morris's funeral oration, the correspondence between Hamilton and Burr, Hamilton's will, Hamilton's own statement written before the meeting, and the coroner's jury's verdict as the papers reported it. Contains those six groups."),
 dict(id='bishop-moore-letter-on-general-hamilton', parent='death-of-general-hamilton-1804', kind='message_group',
      label="Bishop Moore's letter to the Evening Post, 12 July 1804, on General Hamilton's last hours",
      definition="Printings of a letter from Bishop Moore, dated Thursday evening, 12 July 1804, to Mr. Coleman of the New York Evening Post: 'The public mind being extremely agitated by the melancholy fate of that great man, Alexander Hamilton, I have thought it would be grateful to my fellow citizens, would provide against misrepresentation, and, perhaps, be conducive to the advancement of the cause of religion, were I to give a narrative of some facts which have fallen under my own observation, during the time which elapsed between the fatal duel and his departure out of this world.' The bishop's own account of his visits and of the communion he gave.",
      role='report', words=55, dateline=False,
      core=[r'Thursday\s+[Ee]vening,?\s+July\s+12', r'M\s?[Rr]\.?\s+C\.?\s?OLE?MAN,?\s+The\s+public\s+mind', r'The\s+public\s+mind\s+being\s+extremely'],
      first="Bishop Moore's letter of 12 July 1804 to the Evening Post: a narrative of General Hamilton's last hours.",
      what="Bishop Moore's letter",
      printings=[k(ADA, '07-18', 3),
                 k(RIR, '07-19', 3),
                 k(NI, '07-20', 2),
                 k(EN, '07-21', 3),
                 k(JPG, '07-23', 2),
                 (k(OP, '07-24', 2), {'field': CA, 'note': 'RevX lacks this item, so the excerpt comes from the older CA transcription.'}),
                 k(VA, '07-25', 2),
                 k(BJ, '07-27', 2),
                 k(NHG, '07-31', 1)]),
 dict(id='gouverneur-morris-funeral-oration-over-general-hamilton', parent='death-of-general-hamilton-1804', kind='document_group',
      label="Gouverneur Morris's oration at General Hamilton's funeral: 'If on this sad, this solemn occasion'",
      definition="Printings of the oration Gouverneur Morris delivered at General Hamilton's funeral in New York, as the Evening Post gave it, saying that those who heard it 'all agree that it comes near enough to what was actually delivered, to be presented as the oration at length': 'Fellow-citizens, If on this sad, this solemn occasion, I should endeavour to move your commiseration, it would be doing injustice to that sensibility which has been so generally and so justly manifested.' The speaker's words as reported; two papers name him 'Governor Morris'.",
      role='published_document', words=50, dateline=False,
      core=[r'F\s?ELLOW[\s-]*C\s?ITIZENS\s*[!,.—-]*\s*I\s?[Ff]\s+(?:ON|on|On)\s+this\s+sad'],
      first="Gouverneur Morris's oration at General Hamilton's funeral: 'If on this sad, this solemn occasion, I should endeavour to move your commiseration'.",
      what="Gouverneur Morris's funeral oration",
      printings=[k(ADA, '07-21', 3),
                 k(JPG, '07-23', 2),
                 k(NI, '07-25', 2),
                 k(EN, '07-25', 3),
                 k(RIR, '07-26', 2),
                 k(NG, '07-26', 2),
                 k(OP, '07-31', 2),
                 k(BJ, '08-03', 2),
                 k(KG, '08-14', 2)]),
 dict(id='hamilton-burr-correspondence-published-july-1804', parent='death-of-general-hamilton-1804', kind='document_group',
      label='The correspondence between General Hamilton and Colonel Burr, published at New York, July 1804',
      definition="Printings of the publication that began in the New York Evening Post of 16 July 1804: an address 'TO THE AMERICAN PUBLIC' ('The shocking catastrophe which has recently occurred, terminating the life of Alexander Hamilton, and which has spread a gloom over our city that will not be speedily dissipated, demands that the circumstances which led to it, or were intimately connected with it, should not be concealed from the world'), then 'the correspondence that passed between General Hamilton and Colonel Burr', the letters numbered from No. 1 (Burr's letter of 18 June 1804: 'I send for your perusal a letter signed Charles D. Cooper'), with the statement agreed by the two seconds. Most papers printed it over one or two issues; the National Intelligencer and the New Hampshire Gazette begin with the correspondence itself. The two men's own letters, and the seconds' account.",
      role='published_document', words=55, dateline=True,
      core=[r'T\s?O\s+THE\s+(?:AMERICAN\s+)?PUBLICK?\.\s+T\s?HE\s+shocking', r'T\s?he\s+following\s+is\s+the\s+[Cc]orrespondence\s+that\s+passed'],
      first="New York, July 1804: the correspondence between General Hamilton and Colonel Burr is published, with an address 'To the American Public'.",
      what='the Hamilton–Burr correspondence',
      printings=[k(NI, '07-23', 2),
                 k(NG, '07-24', 1),
                 k(NHG, '07-24', 2),
                 k(VA, '07-25', 5),
                 k(EN, '07-25', 2),
                 k(RIR, '07-26', 1),
                 k(JPG, '07-30', 1),
                 k(OP, '07-31', 1),
                 k(BJ, '08-03', 1)]),
 dict(id='general-hamilton-will-july-1804', parent='death-of-general-hamilton-1804', kind='document_group',
      label="General Hamilton's will, signed 9 July 1804",
      definition="Printings of Alexander Hamilton's will: 'In the name of God, Amen. I, Alexander Hamilton, of the city of New-York, Counsellor at Law, do make this my last Will and Testament', which names three executors, is signed on the ninth day of July 1804 and is certified at the New York Surrogate's Office on 16 July. Most papers print it after Hamilton's statement and the Evening Post's note 'On the foregoing letters and papers, the Editor will make no comment'. The document itself; the excerpts end before the executors' names.",
      role='published_document', words=45, dateline=False, stop=r'F\s?(?:IRST|irst)\W{0,4}I\s+appoint',
      core=[r'I\s?n\s+the\s+name\s+of\s+G\s?OD,?\s+Amen'],
      first="General Hamilton's will, signed 9 July 1804: 'In the name of God, Amen. I, Alexander Hamilton, of the city of New-York, Counsellor at Law'.",
      what="General Hamilton's will",
      printings=[k(JPG, '07-23', 2),
                 k(NG, '07-24', 3),
                 k(NI, '07-25', 1),
                 k(VA, '07-25', 6),
                 k(EN, '07-25', 3),
                 k(RIR, '07-26', 2),
                 k(OP, '07-31', 1),
                 k(BJ, '08-03', 5)]),
 dict(id='general-hamilton-statement-on-the-expected-interview', parent='death-of-general-hamilton-1804', kind='document_group',
      label="General Hamilton's statement 'On my expected interview with Col. Burr', found with his will",
      definition="Printings of the paper General Hamilton left with his will, numbered No. 12 in the publication (No. 13 in the National Intelligencer, No. XII in Jenks' Portland Gazette): 'On my expected interview with Col. Burr, I think it proper to make some remarks explanatory of my conduct, motives and views', beginning 'My religious and moral principles are strongly opposed to the practice of duelling'. Most papers introduce it as 'inclosed with his will and some other papers in a packet addressed to one of his executors'. Hamilton's own words, written before the meeting.",
      role='published_document', words=55, dateline=False,
      core=[r'N\s?o\.?\s+(?:1[23]|XII|I2|l2)\.\s+O\s?n\s+my\s+expected\s+interview', r'O\s?n\s+my\s+expected\s+interview'],
      first="General Hamilton's statement found with his will: 'On my expected interview with Col. Burr, I think it proper to make some remarks explanatory of my conduct, motives and views.'",
      what="General Hamilton's statement",
      printings=[k(OP, '07-24', 3),
                 k(NG, '07-24', 2),
                 k(NI, '07-25', 1),
                 k(VA, '07-25', 6),
                 k(EN, '07-25', 3),
                 k(RIR, '07-26', 2),
                 k(JPG, '07-30', 2),
                 k(NHG, '07-31', 1),
                 k(BJ, '08-03', 2)]),
 dict(id='coroners-jury-verdict-on-general-hamilton-august-1804', parent='death-of-general-hamilton-1804', kind='message_group',
      label="The coroner's jury on General Hamilton's death, August 1804: a verdict of murder against Aaron Burr, as the papers reported it",
      definition="Printings of the New York reports, dated 3, 4 and 13 August 1804, of the verdict of the jury of inquest that the coroner summoned on General Hamilton's death: most quote it, 'That Aaron Burr, Esq. Vice President of the United States, was guilty of the murder of Alexander Hamilton' (three papers print 'is guilty'), and name the two seconds as accessaries; a shorter New York paragraph says the inquest 'brought in a verdict of MURDER by AARON BURR', and the Norfolk Gazette gives it in its own words. The accounts are counted together, as 1805 counted the accounts of Judge Chase's acquittal and 1807 the Burr verdict; the Berkeley and Jefferson Intelligencer printed two accounts and the Enquirer three. An inquest's verdict, which accuses a named public man; the excerpts end before the seconds' names.",
      role='report', words=55, dateline=True, stop=r'[—-]*\s*(?:and|And)\s+that\s+Will?\w*\s+P',
      core=[r'T\s?he\s+[Cc]oroner.?s\s+[Ii]nquest', r'We\s+are\s+informed,?\s+from\s+an\s+official\s+source', r'MURDER!\s*[—-]*\s*The\s+Coroner', r'After\s+a\s+long\s+and\s+laborious\s+session'],
      first="New York, August 1804: the coroner's jury on General Hamilton's death brings in a verdict of murder against Aaron Burr, as the papers report it.",
      what="a report of the coroner's jury's verdict",
      printings=[(k(ADA, '08-06', 3), {'note': "The shorter New York paragraph ('brought in a verdict of MURDER by AARON BURR')."}),
                 k(NI, '08-08', 3),
                 (k(BJ, '08-10', 2), {'note': "The shorter New York paragraph ('brought in a verdict of MURDER by AARON BURR')."}),
                 k(VA, '08-11', 2),
                 (k(EN, '08-11', 3), {'note': "The shorter New York paragraph, 'taken from Lang's (N. Y.) Gazette of Friday last'; the paper printed fuller accounts on 15 and 22 August."}),
                 (k(NG, '08-11', 2), {'note': "The Norfolk Gazette's own paragraph ('MURDER!—The Coroner's Jury which sat on the body of Alexander Hamilton')."}),
                 (k(JPG, '08-13', 2), {'note': "The shorter New York paragraph ('brought in a verdict of MURDER BY AARON BURR')."}),
                 (k(NHG, '08-14', 3), {'stop': r'The\s+New[\s-]+York\s+Evening\s+Post\s+is', 'note': "The shorter New York paragraph, credited to the New-York Gazette."}),
                 k(OP, '08-14', 2),
                 k(EN, '08-15', 2),
                 k(RIR, '08-16', 2),
                 (k(BJ, '08-17', 3), {'note': "A second account, from the New York Daily Advertiser, quoting the verdict; the paper had printed the shorter paragraph on 10 August."}),
                 (k(EN, '08-22', 2), {'note': "A third account, dated New York, 13 August, quoting the verdict; the paper had printed others on 11 and 15 August."})]),
 dict(id='wythe-court-house-letter-the-clinch-mountain-sunk', kind='message_group',
      label="A letter from Wythe Court-House, Virginia, 30 July 1804: 'the Clinch Mountain had sunk'",
      definition="Printings of an extract of a letter from a gentleman at Wythe Court-House, Virginia, to his friend in Frederick-Town, Maryland, dated 30 July 1804: 'We have for 12 days been clouded with a dark smoke, and this day I was informed by a gentleman from Kentucky that the Clinch Mountain had sunk for many miles to the depth of 50 feet'; the writer supposes it 'occasioned by the burning of the stone coal which is in the mountain'. Two papers print a shorter form headed 'Singular Phenomenon', without the date and with 'for ten days'; the Rhode-Island Republican also prints 'ten days', and the Norfolk Gazette 'twelve days' in words. A report at second hand: the writer passes on what a traveller told him.",
      role='report', words=55, dateline=False,
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+a\s+gen\W?\w?leman\s+at\s+Wythe', r'(?:Singular\s+Phenomenon\.?\s*[—-]*\s*)?A\s+letter\s+from\s+a\s+gentleman\s+at\s+Wh?y\w+'],
      first="A letter from Wythe Court-House, Virginia, 30 July 1804: a traveller says 'the Clinch Mountain had sunk for many miles'.",
      what='the letter from Wythe Court-House',
      printings=[k(ADA, '08-22', 3),
                 k(NI, '08-24', 3),
                 k(VA, '08-29', 3),
                 k(NG, '09-01', 2),
                 (k(NHG, '09-04', 2), {'note': "The shorter form, under the heading 'Singular Phenomenon'."}),
                 k(RIR, '09-06', 3),
                 (k(JPG, '09-10', 2), {'note': 'The shorter form.'}),
                 k(KG, '09-18', 3)]),
 dict(id='west-florida-rising-august-1804', kind='context_group',
      label='An armed party marches against the Spanish fort of Baton Rouge in West Florida, August 1804: two reports from Natchez',
      children=['natchez-letter-of-7-august-armed-men-near-bayou-sara', 'natchez-report-of-14-august-a-party-marches-on-baton-rouge'],
      definition="Two reports from Natchez, in the Mississippi Territory, of an armed party that marched from near the line with Spanish West Florida against the fort of Baton Rouge in August 1804 and posted a paper declaring West Florida free. Contains those two groups."),
 dict(id='natchez-letter-of-7-august-armed-men-near-bayou-sara', parent='west-florida-rising-august-1804', kind='message_group',
      label='Natchez, August 1804: a letter of 7 August on armed men with a flag near Bayou Sara',
      definition="Printings of an extract of a letter dated 7 August 1804, published at Natchez on 10 August: 'Returning this morning from the vicinity of Little Bayou-Sara, I met not far from the line, 21 armed men;—on passing a house within my view, they sounded a French horn, and unfurled a flag composed of four white and three blue stripes'. Two papers print it under the heading 'Unpleasant Symptoms'. An unsigned letter-writer's own account.",
      role='report', words=55, dateline=True,
      core=[r'Extract\s+(?:of|from)\s+a\s+[Ll]etter,?\s+(?:dated\s+)?Aug\w*\.?\s+7'],
      first="Natchez, August 1804: a letter of 7 August reports 21 armed men with a striped flag near Bayou Sara.",
      what='the Natchez letter of 7 August',
      printings=[k(KG, '09-04', 2),
                 k(NI, '09-07', 3),
                 k(VA, '09-12', 3),
                 k(EN, '09-12', 3),
                 k(NG, '09-15', 2),
                 k(JPG, '09-17', 1),
                 k(OP, '09-18', 2)]),
 dict(id='natchez-report-of-14-august-a-party-marches-on-baton-rouge', parent='west-florida-rising-august-1804', kind='message_group',
      label="Natchez, 14 August 1804: 'Mr. Nathan Kemper, with a party of about 30 men, with colors flying and horns sounding' marches on Baton Rouge",
      definition="Printings of a Natchez report of 14 August 1804: 'By a gentleman arrived here yesterday from the neighbourhood of Bayou Sarah, we have been favored with the following information. That Mr. Nathan Kemper, with a party of about 30 men, with colors flying and horns sounding, marched from the neighbourhood of the line of demarcation between this Territory and West-Florida, on the 7th inst. against the fort of Baton Rouge' (the wording varies a little between papers); it gives a paper posted at the party's headquarters: 'For a people to be free, it is sufficient that they will it.' A report at second hand from a traveller, with the party's own declaration.",
      role='report', words=55, dateline=True,
      core=[r'B\s?[Yy]\s+a\s+gentleman\s+(?:who\s+)?arrived\s+here\s+yesterday', r'by\s+a\s+gentleman\s+\w*rived\s+here\s+ye\w+'],
      first="Natchez, 14 August 1804: an armed party marches from near the West Florida line against the fort of Baton Rouge, and posts a declaration.",
      what='the Natchez report of 14 August',
      printings=[k(KG, '09-11', 3),
                 k(NI, '09-12', 3),
                 k(VA, '09-19', 2),
                 k(EN, '09-19', 3),
                 k(JPG, '09-24', 3),
                 k(NHG, '09-25', 2),
                 k(OP, '09-25', 2),
                 k(RIR, '09-27', 3)]),
 dict(id='spanish-minister-yrujo-and-w-jackson-1804', kind='context_group',
      label='The Spanish minister Yrujo and W. Jackson of the Political Register, September and October 1804',
      children=['w-jackson-statement-in-the-political-register-september-1804', 'yrujo-letter-to-the-secretary-of-state-october-1804'],
      definition="Two publications in a dispute between the Marquis de Casa Yrujo, the Spanish minister to the United States, and W. Jackson of the Philadelphia Political Register, in September and October 1804: Jackson's statement with a deposition and letters, and the minister's letter to the Secretary of State in reply. Each side's own account. Contains those two groups."),
 dict(id='w-jackson-statement-in-the-political-register-september-1804', parent='spanish-minister-yrujo-and-w-jackson-1804', kind='document_group',
      label="W. Jackson's statement in the Political Register, September 1804, with a deposition and letters concerning the Spanish minister",
      definition="Printings of a publication from the Philadelphia Political Register, dated 20 September 1804 in two papers: 'In the discharge of an important, and to myself an indispensable duty, the subjoined statement was communicated, in the first instance, to the government.—In a respectful solicitude for the rights and interest of our country the deposition and letters are now made public. W. Jackson.' The statement, deposition and letters that follow concern the Marquis de Casa Yrujo, the Spanish minister. One side's own account.",
      role='published_document', words=55, dateline=True,
      core=[r'I\s?n\s+the\s+discharge\s+of\s+an\s+important'],
      first="W. Jackson publishes, from the Political Register, a statement, deposition and letters concerning the Spanish minister, which he says were first communicated to the government.",
      what="W. Jackson's statement",
      printings=[k(NI, '09-24', 2),
                 k(RIR, '09-27', 2),
                 k(VA, '09-29', 2),
                 k(EN, '09-29', 3),
                 k(NG, '09-29', 2),
                 k(JPG, '10-01', 2),
                 k(NHG, '10-02', 2)]),
 dict(id='yrujo-letter-to-the-secretary-of-state-october-1804', parent='spanish-minister-yrujo-and-w-jackson-1804', kind='document_group',
      label="The Marquis de Casa Yrujo's letter to the Secretary of State, published at his request, October 1804",
      definition="Printings of a letter from the Spanish minister to the Secretary of State, published in the National Intelligencer of 5 October 1804 'at the request of the Marquis de Casa Yrujo': 'Having been absent from Philadelphia for these 18 days past and travelled far into a part of Virginia where I had no opportunity to see the late newspapers from the Northward', he answers the publication in the Political Register (the other group). The minister's own account; the New Hampshire Gazette and the Kentucky Gazette misprint his name 'Trujo' (their transcriptions read 'Trujillo'), and the Oracle Post prints the letter over two issues.",
      role='published_document', words=55, dateline=True,
      core=[r'T\s?he\s+following\s+letter,?\s+communicated\s+to\s+the\s+Secretary\s+of\s+State'],
      first="The Spanish minister's letter to the Secretary of State, published at his request: his answer to the Political Register.",
      what="the Spanish minister's letter",
      printings=[k(NI, '10-05', 2),
                 k(VA, '10-10', 2),
                 k(NG, '10-13', 2),
                 k(NHG, '10-16', 2),
                 k(OP, '11-06', 1),
                 k(KG, '11-06', 2),
                 k(RIR, '11-08', 2)]),
 dict(id='notice-that-the-amendment-on-electing-the-president-is-ratified-1804', kind='document_group',
      label="The Secretary of State's notice that the amendment on electing the President and Vice-President has been ratified, 1804",
      definition="Printings of a public notice 'By James Madison, Secretary of State of the United States', given 'in pursuance of the Act of Congress passed on the 26th March last' (the act supplementary to the act relative to the election of a President and Vice-President): 'That the amendment proposed, during the last session of Congress, to the Constitution of the United States, respecting the manner of voting for President and Vice-President of the United States, has been ratified by the Legislatures of three fourths of the several states', which it names. Several papers ran it in successive issues, and each printing counts, as 1807 counted the proclamation calling Congress. The government's notice.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:By\s+)?J\s?AMES\s+M\s?ADISON\s*,?\s+Secretary\s+of\s+State\s+of\s+the\s+United\s+States\.\s+PUBLICK?\s+NOTICE'],
      first="The Secretary of State gives notice that the amendment on the manner of voting for President and Vice-President has been ratified by three fourths of the states.",
      what="the Secretary of State's notice",
      printings=[k(NI, '10-01', 2),
                 k(NI, '10-03', 3),
                 k(NI, '10-05', 3),
                 k(VA, '10-06', 3),
                 k(EN, '10-06', 3),
                 k(NI, '10-10', 3),
                 k(VA, '10-10', 3),
                 k(EN, '10-10', 4),
                 k(RIR, '10-11', 2),
                 k(VA, '10-13', 1),
                 k(NHG, '10-16', 1),
                 k(RIR, '10-18', 3),
                 k(NG, '10-18', 3),
                 k(KG, '10-23', 2),
                 k(RIR, '10-25', 4),
                 k(KG, '10-30', 3),
                 k(KG, '11-06', 3)]),
 dict(id='ursuline-nuns-memorial-and-the-presidents-answer-1804', kind='document_group',
      label="The Ursuline nuns of New Orleans to the President, and his answer, 1804",
      definition="Printings of a letter to the editor of the Moniteur (the Louisiana Monitor) of New Orleans, dated 12 September 1804: 'The following memorial was addressed by the Ursuline Nuns of this city to the President of the United States', with the memorial ('Emboldened by the favourable mention you have been pleased to make of their Order, the Nuns of Ursula ...') and the President's answer ('I have received, holy Sisters, the letter you have written me, wherein you express anxiety for the property vested in your institution, by the former governments of Louisiana'). Jenks' Portland Gazette prints the memorial and the answer without the letter to the editor. The nuns' and the President's own words.",
      role='published_document', words=55, dateline=False,
      core=[r'T\s?[Oo]\s+(?:THE|the)\s+E\s?(?:DITOR|ditor)\s+of\s+the\s+(?:Louisiana\s+)?M\w+', r'T\s?he\s+following\s+memorial\s+(?:was|has\s+been)\s+addressed', r'T\s?o\s+THOMAS\s+JEFFERSON,?\s+President'],
      first="New Orleans, 12 September 1804: the Ursuline nuns' memorial to the President on their property, and his answer.",
      what="the Ursuline nuns' memorial and the President's answer",
      printings=[k(NI, '10-26', 3),
                 k(VA, '11-07', 3),
                 k(EN, '11-07', 2),
                 k(RIR, '11-08', 2),
                 k(NG, '11-08', 2),
                 k(JPG, '11-12', 2),
                 k(NHG, '11-20', 2),
                 k(KG, '11-20', 2)]),
 dict(id='preble-letter-off-tripoli-14-june-1804', kind='document_group',
      label="Commodore Preble's letter off Tripoli, 14 June 1804: Mr. O'Brien sent on shore 'to endeavour to ransom our unfortunate countrymen'",
      definition="Printings of an extract of a letter from Commodore Preble to the Secretary of the Navy, dated 14 June 1804, on board the frigate Constitution off Tripoli, published by the government in Washington on 2 November: 'Yesterday I anchored off the harbour, and sent Mr. O'Brien on shore under a flag of truce, to endeavour to ransom our unfortunate countrymen'. The commodore's own report.",
      role='published_document', words=55, dateline=True,
      core=[r'Extra\w*\s+of\s+a\s+letter\s+from\s+Com\w*\.?\s+P\s?(?:REBLE|reble),?\s+to\s+the\s+[Ss]ecretary\s+of\s+the\s+[Nn]avy\s*,?\s+dated\s+(?:the\s+)?(?:14\w*\s+(?:of\s+)?June|June\s+14)'],
      first="Commodore Preble writes off Tripoli, 14 June 1804: Mr. O'Brien has been sent on shore under a flag of truce to try to ransom the prisoners.",
      what="Commodore Preble's letter off Tripoli",
      printings=[k(NI, '11-02', 3),
                 k(VA, '11-07', 3),
                 k(BJ, '11-09', 1),
                 k(EN, '11-10', 1),
                 k(NG, '11-10', 3),
                 k(RIR, '11-15', 2),
                 k(JPG, '11-19', 2),
                 k(OP, '11-20', 2),
                 k(KG, '11-20', 2)]),
 dict(id='house-motion-on-drawbacks-at-new-orleans-12-november-1804', kind='document_group',
      label="A motion in the House, 12 November 1804: Mr. Griswold asks for an inquiry into drawbacks of duties on goods shipped on from New Orleans",
      definition="Printings of a paragraph of the House of Representatives' proceedings of Monday 12 November 1804, in the National Intelligencer's words: 'Mr. Griswold stated that some inconvenience had been felt by some of the merchants of the Atlantic ports in making shipments to New Orleans, as they were not authorized to obtain drawbacks on a re-shipment from that port to a foreign country', and moved 'That the committee of Commerce and Manufactures be instructed to enquire into the expediency of allowing, under proper regulations, a drawback of duties on goods, wares and merchandise, imported into the port of New Orleans from any port of the United States, and from thence exported to any foreign port or place'; 'The resolution was carried nem. con.' The papers printed it inside their reports of the House's proceedings; it is counted as an item, as 1806 counted Mr. Gregg's resolution and 1800 Mr. Livingston's. A member's motion and the House's vote, as reported.",
      role='published_document', words=55, dateline=False,
      core=[r'Mr\.?\s+Griswold\s+stated,?\s+that\s+some\s+inconvenience',r'Resolved,?\s+That\s+the\s+committee\s+of\s+Commerce\s+and\s+Manufactures,?\s+be\s+instructed\s+to\s+(?:en|in)quire\s+into\s+the\s+expediency\s+of\s+allowing'],
      first="In the House, 12 November 1804: Mr. Griswold moves an inquiry into allowing drawbacks of duties on goods shipped on from New Orleans to foreign ports; carried.",
      what="the House's proceedings on Mr. Griswold's motion",
      printings=[k(NI, '11-14', 3),
                 k(ADA, '11-15', 3),
                 k(VA, '11-17', 3),
                 k(NG, '11-19', 2),
                 k(EN, '11-21', 3),
                 k(NHG, '11-27', 2),
                 (k(RIR, '11-28', 3), {'note': "Prints the resolution at the head of page 3, without Mr. Griswold's remarks."}),
                 k(JPG, '12-03', 2),
                 k(OP, '12-04', 2)]),
 dict(id='presidents-message-8-november-1804', kind='document_group',
      label="The President's message to Congress, 8 November 1804",
      definition="Printings of the President's annual message delivered to both Houses on 8 November 1804 by his secretary: 'To a people, fellow citizens, who sincerely desire the happiness and prosperity of other nations; to those who justly calculate that their own well being is advanced by that of the nations with which they have intercourse, it will be a satisfaction to observe that the war which was lighted up in Europe a little before our last meeting, has not yet extended its flames to other nations'. It speaks of the irregularities on the ocean, Louisiana and Spain, the Indian tribes, the Barbary powers and the revenue. Policy arguments in the President's own words.",
      role='published_document', words=55, dateline=False,
      core=[r'T\s?O\s+THE\s+S\s?ENATE\s+AND\s+House\s+of\s+Representatives\s+OF\s+THE\s+U\s?NITED\s+S\s?TATES\W+T\s?O\s+a\s+people'],
      first="The President's message to Congress of 8 November 1804: 'To a people, fellow citizens, who sincerely desire the happiness and prosperity of other nations'.",
      what="the President's message",
      printings=[k(NI, '11-09', 3),
                 k(NG, '11-14', 2),
                 k(VA, '11-14', 2),
                 k(EN, '11-14', 2),
                 k(NHG, '11-20', 2),
                 k(RIR, '11-22', 2),
                 k(BJ, '11-23', 1),
                 k(JPG, '11-26', 1),
                 k(KG, '11-27', 2)]),
 dict(id='documents-on-spain-and-louisiana-sent-to-congress-november-1804', kind='document_group',
      label="The documents sent to Congress with the President's message, November 1804: Spain's minister of state on the cession of Louisiana",
      definition="Printings of the documents that accompanied a message from the President to Congress in November 1804, published in the National Intelligencer of 14 November as 'DOCUMENT No. I' and onward, counted by the first: an extract of a letter from Don Pedro Cevallos, minister of state of his Catholic Majesty, to Charles Pinckney, dated at the Pardo, 10 February 1804, in translation: 'his majesty has thought fit to renounce his opposition to the alienation of Louisiana made by France'. The documents that follow include the correspondence on the act of Congress that allowed the President to erect the shores and waters of the bay and river of Mobile into a collection district. The Spanish government's and the two governments' ministers' own words.",
      role='published_document', words=60, dateline=False,
      core=[r'D\s?OCUMENTS?\.?\s+N\s?[Oo]\.?\s*[—-]*\s*(?:I|1)\.?\s+A\s?(?:ccompanying|CCOMPANYING)', r'D\s?OCUMENTS\s+Accompanying\s+a\s+message'],
      first="The documents sent to Congress with the President's message, November 1804: Spain's minister of state says the King renounces his opposition to the cession of Louisiana.",
      what='the documents on Spain and Louisiana',
      printings=[k(NI, '11-14', 1),
                 k(ADA, '11-16', 2),
                 k(NG, '11-19', 2),
                 k(VA, '11-21', 1),
                 k(EN, '11-21', 1),
                 k(NHG, '11-27', 2),
                 k(RIR, '11-28', 1),
                 k(BJ, '11-30', 1),
                 k(KG, '12-04', 3)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808 and 1809): "NATCHEZ, August 10, 1804."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*18(?:03|04))?\.\s*(?:[—-]+\s*)?)$")


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
    stop: a regex; the excerpt ends before its first match (to end before private persons' names). Unlike the cut of
    1809, the extension to the end of a clause never runs past the stop either."""
    tokens = list(re.finditer(r'\S+', text[start:]))
    n = min(words, len(tokens))
    stopped, stop_n = False, len(tokens)
    if stop:
        m = re.search(stop, text[start:])
        if m:
            stop_n = max(1, sum(1 for t in tokens if t.end() <= m.start()))
            if stop_n < n:
                n, stopped = stop_n, True
    for j in range(15, n):   # RevX sometimes abridges with an ellipsis; end before it.
        if '...' in tokens[j].group() or '…' in tokens[j].group():
            n = j if tokens[j].group().startswith(('...', '…')) else j+1
            break
    else:
        j = None
    limit = n if (j is not None or stopped) else min(n+15, len(tokens), stop_n)
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
            problems.append((s['id'], key, 'page not in the 1804 pages'))
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
            note = (note+' ' if note else '') + ('The RevX transcriptions of this issue are filed one page off from the scans, so the excerpt '
                                                 'comes from the older CA transcription of this scan page.')
        elif field == CA and 'field' not in over:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'printed': pages[key]['date'], 'field': field, 'excerpt_start': first, 'excerpt_end': last,
                     'excerpt': excerpt, 'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['printed'], r['page_key'], r['story']))
    for n, r in enumerate(rows, 1):
        r['id'] = f'S04-{n:03}'
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
               'admission_rule': 'Reviewed 1804 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1804/'
    return {
        'ledger_id': 'ledger:stories-1804', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1804', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1804, and of 1803 where they reach the 1804 pages (long-running ones '
                   'included), phrase searches on all 3,472 pages of 1804 in both transcriptions, reading of every hit, and scan checks of each '
                   'admitted passage'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1803.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1804.py': 'ledger_code', 'work/archive_data/ledgers/stories_1804_review.json': 'scan_review',
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
            print(f"{r['id']} {r['story'][:26]:26} {r['page_key']:30} {r['field'][:4]} {r['roles'][0][:9]:9} | {r['excerpt'][:110]} … {r['excerpt'][-50:]}")
    review = json.loads(REVIEW.read_text(encoding='utf8')) if REVIEW.exists() else {}
    if problems and '--force' not in sys.argv:
        raise SystemExit(f'{len(problems)} printings without anchors')
    OUT.write_text(json.dumps(build(rows, review), ensure_ascii=False, indent=2), encoding='utf8')
    print('wrote', OUT, len(rows), 'observations,', len(STORIES), 'groups')
