"""Write ledgers/stories_1802.json: reviewed stories of 1802, round one.

1802 is read by the one admission rule the other reviewed years follow (outputs/story_discovery_1809/README.md, "Selection
rule"; docs/rules-and-exceptions.md, R-01): every single printed item in 9 or more newspapers is admitted, except digests;
items in 7 or 8 papers are chosen to cover the months and the kinds of news; items are counted one by one; a sub-story may
have fewer papers when its parent reaches 7. The automatic families first printed in 1802 that reach 3 or more papers,
long-running ones included, were split into single printed items with work/story_items.py --long-running (items.json), and
again with year 1801 over the 1802 pages (items_from_1801.json); every item in 5 or more papers was checked for further
papers, every item in 6 or more was read, and the counts were checked item by item with phrase searches over all 2,968
pages of 1802 in both transcriptions (work/story_phrase_search.py). See outputs/story_discovery_1802/README.md.

The 1802 pages are those whose issue the data release dates to 1802 (work/year_search_pages.py 1802 ... --printed-dates); no
1802 issue has a corrected date in the releases. Three papers have two catalogue numbers in 1802, each counted once: Jenks's
Portland Gazette (sn83016063 to 20 September, sn83016072 from 27 September), the Recorder of Richmond (sn84024678 to 27
October, sn84024679 from 3 November) and E. Russell's paper at Concord, New Hampshire (sn84022876, the Republican Gazette, to
3 August; sn90062293, the American Republican Gazette, from 10 August).

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-80 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1802_review.json after the scan
check. Eleven 1802 pages have their RevX transcriptions filed off from the scans (derived/revx_page_map.parquet); no
printing here stands on one of them, and a printing on such a page would take its excerpt from the CA transcription of its
scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened. The report of the New York fire of November names the sufferers
after its opening; the excerpts end before their names (C-12).

The base and target releases are set when the ledger is applied (a 1803 review runs at the same time and may take the next
number first):
    python work/archive_data/ledgers/make_stories_1802.py [--table] [--base 0.11.10 --target 0.11.11]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1802/search_pages.json). The excerpts are cut from
the 1802 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1802'
D = PROJECT/'outputs/story_discovery_1802'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1802_review.json'
OUT = HERE/'stories_1802.json'
BASE, TARGET = '0.11.10', '0.11.11'   # defaults; see the docstring
DATA_RELEASE = '0.11.10'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-23'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

KG, ALX, ORA, NI, NHG, RL, RIR, VA = ('sn82014782', 'sn84024011', 'sn83025545', 'sn83045242', 'sn83025588', 'sn84023379',
                                      'sn83021188', 'sn84024710')
POR1, POR2, REC1, REC2, CRG1, CRG2 = 'sn83016063', 'sn83016072', 'sn84024678', 'sn84024679', 'sn84022876', 'sn90062293'
POR, REC, CRG = 'POR', 'REC', 'CRG'   # papers whose catalogue number depends on the date
PAPER = {KG: 'The Kentucky Gazette', ALX: 'The Alexandria Advertiser', ORA: 'The United States Oracle',
         NI: 'The National Intelligencer', NHG: 'The New Hampshire Gazette', RL: 'The Republican Ledger',
         RIR: 'The Rhode-Island Republican', VA: 'The Virginia Argus', POR1: "Jenks's Portland Gazette",
         POR2: "Jenks' Portland Gazette", REC1: 'The Recorder', REC2: 'The Recorder', CRG1: 'The Republican Gazette',
         CRG2: 'The American Republican Gazette'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper, date (MM-DD in 1802), page and edition."""
    if paper == POR:
        paper = POR1 if date <= '09-20' else POR2
    elif paper == REC:
        paper = REC1 if date <= '10-27' else REC2
    elif paper == CRG:
        paper = CRG1 if date <= '08-03' else CRG2
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
 dict(id='breckenridge-speech-on-repealing-the-judiciary-act-january-1802', kind='document_group',
      label="Mr. Breckenridge's speech in the Senate, 8 January 1802, on his motion to repeal the judiciary act of 1801",
      definition="Printings of the speech with which Mr. Breckenridge, senator from Kentucky, opened the Senate's debate of 8 January 1802 on his resolution to repeal the act of the last session 'for a new organization of the Judiciary System' (the act of 13 February 1801, which had created sixteen circuit judges): 'It will be expected of me, I presume, Sir, as I introduced the resolution now under consideration, to assign my reasons for wishing a repeal of this law. This I shall do; and shall endeavour to shew, 1. That the law is unnecessary and improper, and was so at its passage'. Most papers print it under the heading 'Judiciary Establishment', from the National Intelligencer's report of the Senate's debates. A senator's own argument, as the papers reported the debate.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:J\s?UDICIARY\s+E\s?STABLISHMENT\.?\s+)?M[Rr]\.?\s+B\s?R[AE]CKENRIDGE\.?\s*[—-]*\s*It\s+will\s+be\s+expected',
            r'J\s?UDICIARY\s+E\s?STABLISHMENT\.?\s+M[Rr]\.?\s+B\s?r\w+\.?\s+It\s+will\s+be\s+ex',
            r'It\s+will\s+be\s+expected\s+of\s+me,?\s+I\s+presume'],
      first="Mr. Breckenridge opens the Senate's debate of 8 January 1802 on repealing the judiciary act of 1801.",
      what="Mr. Breckenridge's speech",
      printings=[k(NI, '01-11', 3),
                 k(ALX, '01-13', 2),
                 (k(NHG, '01-26', 2), {'note': 'This page has no RevX transcription, so the excerpt comes from the older CA transcription, which is garbled in places.'}),
                 k(KG, '01-29', 2),
                 (k(RIR, '01-30', 1), {'note': "The Rhode-Island Republican heads the speech 'DEBATE On Mr. Breckenridge's motion to repeal the Act passed last Session, for a new organization of the Judiciary System'."}),
                 k(ORA, '01-30', 1),
                 k(POR, '02-01', 1),
                 k(RL, '02-02', 1)]),
 dict(id='havana-circular-ports-of-cuba-closed-december-1801', kind='document_group',
      label="The American consul at Havana's circular of 25 December 1801: the ports of Cuba closed to American and all foreign vessels",
      definition="Printings of a circular dated 'American Consulate, Havanna, December 25, 1801' and signed by the consul of the United States there: 'By an order of the government of this island, published this day, the admission of American, and all other foreign vessels into its ports, is prohibited from this date. You will be pleased, Sir, to give immediate publicity to this information, for the government of the merchants and traders of your district.' The papers print copies sent to the collectors of different ports (Baltimore, Philadelphia, New York); the Oracle's adds a postscript of 31 December. The American consul's own notice of a Spanish colonial order.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:\(?CIRCULAR\.?\)?\s+)?A\s?MERICAN\s+C\s?ONSULATE[.,]?\s+Hav\w*',
            r'B\s?Y\s+(?:an\s+)?[Oo]rder\s+of\s+the\s+[Gg]overnment\s+of\s+this\s+[Ii]sland'],
      first="The American consul at Havana reports that Cuba's ports are closed to American and all other foreign vessels from 25 December 1801.",
      what="the consul's circular from Havana",
      printings=[k(ALX, '01-19', 3),
                 k(NI, '01-20', 3),
                 k(NHG, '01-26', 3),
                 k(RIR, '01-30', 3),
                 (k(ORA, '01-30', 2), {'stop': r'P\.\s*S\.', 'note': "RevX leaves out the printed lines between 'prohibited from this date' and the paper's postscript (the request for publicity, the consul's signature and the address to the collector at New York); the excerpt ends before the gap."}),
                 k(RL, '02-02', 3),
                 k(KG, '02-12', 2)]),
 dict(id='baltimore-report-of-the-death-of-toussaint-january-1802', kind='message_group',
      label="Baltimore, January 1802: a letter from Alexandria reports that Toussaint 'is no more'",
      definition="Printings of a paragraph from the Baltimore Federal Gazette of 23 January 1802, headed 'Death of Toussaint' or 'Important' in several papers: 'A gentleman belonging to a respectable mercantile house of Alexandria, now in this town, received a letter from his partner last night, dated the 21st inst. which says, \"I am sorry to inform you Toussaint is no more. He has been caught by the blacks and burnt alive.\"' The Baltimore paper adds that the same report was current at Norfolk, 'tho' not generally credited', and gives its own guesses at how it happened. A report at third hand of a rumour; the papers of the following months print Toussaint as alive (his arrest in June is the story of Leclerc's proclamation, below).",
      role='report', words=60, dateline=True, back=False,
      core=[r'(?:(?:DEATH\s+OF\s+TOUSSAINT|IMPORTANT)!?\.?\s+)?A\s+gentleman\s+belonging\s+to\s+a\s+respectable\s+merc\w+\s+house\s+of\s+Alexandria'],
      first="Baltimore, 23 January 1802: a merchant's letter from Alexandria says Toussaint has been killed; the paper adds that the report was not generally credited.",
      what='the Baltimore report on Toussaint',
      printings=[(k(ALX, '01-26', 3), {'note': "The Alexandria Advertiser prints the paragraph 'From the Baltimore Fed. Gaz. of Saturday last' under the heading 'IMPORTANT'."}),
                 k(RIR, '02-06', 3),
                 (k(ORA, '02-06', 2), {'stop': r'Toussaint\s+was\s+probably', 'note': "RevX leaves out about 60 printed words after the letter's words (where the report came from, and that it was current at Norfolk); the excerpt ends before the gap."}),
                 k(POR, '02-08', 2),
                 k(NHG, '02-09', 3),
                 k(RL, '02-09', 2),
                 (k(KG, '02-12', 3), {'stop': r'A\s+bill\s+for\s+repealing', 'note': "The Kentucky Gazette prints the report only to the end of the letter's words, and goes on with another paragraph."})]),
 dict(id='french-army-arrives-at-st-domingo-february-1802', kind='context_group',
      label='The French army arrives at St. Domingo, February 1802: the Consuls\' proclamation and a report of the burning of the Cape',
      children=['consuls-proclamation-to-the-inhabitants-of-st-domingo-november-1801', 'baltimore-report-conflagration-of-the-cape-march-1802'],
      definition="Two items of March 1802 on the French expedition under General Leclerc, which reached St. Domingo (Saint-Domingue, now Haiti) early in February: the proclamation of the Consuls of the French Republic to the inhabitants of the island, which Leclerc published on landing, and a Baltimore report, from a ship's captain, of the burning of Cape François. Contains those two groups."),
 dict(id='consuls-proclamation-to-the-inhabitants-of-st-domingo-november-1801', parent='french-army-arrives-at-st-domingo-february-1802', kind='document_group',
      label="The Consuls of the French Republic to the inhabitants of St. Domingo, 8 November 1801: 'Whatever may be your origin and your colour, you are all Frenchmen'",
      definition="Printings of the proclamation of the Consuls of the Republic dated Paris, 17 Brumaire, year 10 (8 November 1801), which General Leclerc published at St. Domingo in February 1802: 'Inhabitants of St. Domingo, Whatever may be your origin and your colour, you are all Frenchmen, you are all free and all equal before God and the Republic. France, like St. Domingo, has been a prey to factions'; it announces the Captain General sent with the army and warns those who would not rally to him. The papers print it in two translations: four that begin 'Inhabitants of St. Domingo, Whatever may be your origin, and your colour, you are all Frenchmen' and go on 'But an entire change has taken place', and three that read 'ye are all Frenchmen, ye are all free' and 'But all is changed'; counted together as one item in two printed forms. Several papers print it after Leclerc's own short proclamation, which is not counted here (5 papers). The French government's own proclamation, as the papers translated it.",
      role='published_document', words=60, dateline=False,
      core=[r'The\s+Consuls\s+of\s+the\s+Republic,?\s+to\s+the\s+[Ii]nhabitants\s+of\s+St\.?\s+Domingo'],
      first="The Consuls of the French Republic's proclamation to the inhabitants of St. Domingo, published by General Leclerc in February 1802.",
      what="the Consuls' proclamation to St. Domingo",
      printings=[k(NI, '03-10', 3),
                 k(ALX, '03-11', 3),
                 k(REC, '03-20', 2),
                 (k(ORA, '03-20', 2), {'note': "The other translation ('ye are all Frenchmen')."}),
                 (k(POR, '03-22', 2), {'note': "The other translation ('ye are all Frenchmen')."}),
                 (k(NHG, '03-23', 1), {'note': "The other translation ('ye are all Frenchmen')."}),
                 k(KG, '03-26', 3)]),
 dict(id='baltimore-report-conflagration-of-the-cape-march-1802', parent='french-army-arrives-at-st-domingo-february-1802', kind='message_group',
      label="Baltimore, March 1802: 'Conflagration of the Cape', from the captain of the schooner Nelly",
      definition="Printings of a report from Baltimore, dated 3 March 1802 in some papers and 4 March in others, headed 'Conflagration of the Cape' in most: 'Arrived last evening, capt. Rogers of the Schooner Nelly, from Cape-Francois, which he left on the 14th February. The news by capt. R. is most distressing; both on account of the American property which has been destroyed at the Cape, and the scenes of horror and bloodshed which have and will take place.' It goes on, in the Baltimore paper's words, with the arrival of the French fleet off the Cape on 3 February, the negotiations, the firing of the town on the night of the 4th and the killings that followed. A ship captain's report at second hand, in the Baltimore paper's words.",
      role='report', words=75, dateline=True, stop=r'It\s+appears\s+that',
      core=[r'(?:(?:CONFLAGRATION\s+OF\s+THE\s+CAPE|Conflagration\s+&\s+Massacre\.\s+Burning\s+of\s+Cape\s+Francois)\.?\s+)?A\s?RRIVED\s+last\s+evening,?\s+[Cc]apt\w*\.?\s+Rogers'],
      first="Baltimore, March 1802: the captain of the schooner Nelly, from Cape François, reports the burning of the Cape.",
      what='the Baltimore report of the burning of the Cape',
      printings=[k(NI, '03-08', 3),
                 k(RIR, '03-13', 3),
                 (k(REC, '03-13', 2), {'note': "The Recorder prints the report 'From the BALTIMORE FEDERAL GAZETTE of March 3'."}),
                 k(NHG, '03-16', 2),
                 k(RL, '03-16', 3),
                 (k(ORA, '03-20', 4), {'stop': r'CHEAP\s+GOODS', 'note': "The Oracle heads the report 'DREADFUL Conflagration & Massacre. Burning of Cape Francois.' RevX runs from its first sentence into an advertisement; the excerpt ends before it."}),
                 k(POR, '03-22', 2)]),
 dict(id='act-fixing-the-military-peace-establishment-1802', kind='document_group',
      label='The act of 16 March 1802 fixing the military peace establishment of the United States',
      definition="Printings, among the laws of the first session of the Seventh Congress, of 'An Act Fixing the military peace establishment of the United States': 'That the military peace establishment of the United States, from and after the first of June next, shall be composed of one regiment of artillerists and two regiments of infantry, with such officers, military agents, and engineers, as are hereinafter mentioned'. Among its sections, the President is empowered to organise a corps of engineers, which 'shall be stationed at West Point in the State of New-York, and shall constitute a military academy'. Congress's own act, printed 'By Authority'.",
      role='published_document', words=55, dateline=False,
      core=[r'A[Nn]\s+A\s?CT\s*,?\s+[Ff]ixing\s+the\s+[Mm]ilitary\s+[Pp]eace\s+[Ee]stablishment'],
      first="The act of 16 March 1802 fixing the military peace establishment: one regiment of artillerists and two of infantry from 1 June.",
      what='the act fixing the military peace establishment',
      printings=[k(NI, '03-22', 2),
                 k(VA, '04-02', 1),
                 k(KG, '04-09', 1),
                 k(RIR, '04-10', 1),
                 k(RL, '04-27', 1),
                 k(NHG, '05-11', 1),
                 k(ORA, '05-29', 1)]),
 dict(id='treaty-of-madrid-21-march-1801-printed-1802', kind='document_group',
      label="The treaty signed at Madrid on 21 March 1801 by Lucien Bonaparte and the Prince of Peace, printed in 1802 as proof that 'Spain has ceded Louisiana to the French'",
      definition="Printings of a treaty 'Signed at Madrid, 21st March, 1801, by the Prince of Peace and Lucien Bonaparte' (the dates vary from paper to paper), from the Paris Journal des Débats of January 1802: 'The First Consul of the French republic and his Catholic Majesty, desirous of permanently determining the states which the son of the Infant of Parma shall receive, as an equivalent for the Duchy of Parma, have agreed to the following articles'; the Grand Duchy of Tuscany is given to the Prince of Parma, who will be acknowledged King of Tuscany. The National Intelligencer's headnote, which most papers repeat, says that the document 'establishes the fact, that Spain has ceded Louisiana to the French'. The two governments' treaty, as a Paris paper gave it, with the American paper's headnote.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:T\s?REATY[.,]?\s+)?Signed\s+at\s+Madrid,?\s+\d+\w*\s+March,?\s+1801'],
      first="The treaty of Madrid of 21 March 1801, printed from a Paris paper as proof that Spain has ceded Louisiana to France.",
      what='the treaty of Madrid',
      printings=[k(NI, '03-24', 2),
                 (k(ALX, '03-26', 3), {'core': [r'Madrid,?\s+December\s+16,?\s+1801\.?\s+Signed\s+at\s+Madrid'],
                                       'note': "The Alexandria Advertiser dates the signing 'at Madrid 31st March, 1801'."}),
                 k(KG, '04-09', 3),
                 k(ORA, '04-10', 2),
                 k(RL, '04-13', 2),
                 k(POR, '04-19', 1),
                 k(NHG, '04-20', 1)]),
 dict(id='definitive-treaty-of-amiens-1802', kind='document_group',
      label='The definitive treaty of peace signed at Amiens, 27 March 1802',
      definition="Printings of the text of the 'Definitive Treaty of Peace, between the French Republic, the King of Spain, and the Batavian Republic, on the one part, and His Majesty the King of the United Kingdom of Great-Britain and Ireland on the other', signed at Amiens on 27 March 1802 and brought to America in May from London and Havre papers: 'The First Consul of the French Republic, in the name of the French Nation, and His Majesty the King of the United Kingdom of Great-Britain and Ireland, being equally animated with a desire to put an end to the calamities of war'. Among its articles, Spain cedes the island of Trinidad and the Batavian Republic its possessions in Ceylon to Great Britain, and Malta is to be restored to the Knights of St. John. The powers' own treaty, as the papers printed it.",
      role='published_document', words=60, dateline=False,
      core=[r'D\s?EFINITIVE\s+T\s?REATY,?\s+OF\s+P\s?EACE,?\s+(?:B|b)etween\s+the\s+French\s+[Rr]epublic',
            r'Definitive\s+Treaty\s+of\s+Peace,?\s+between\s+the\s+French\s+[Rr]epublic'],
      first="The definitive treaty of peace between France, Spain, the Batavian Republic and Great Britain, signed at Amiens on 27 March 1802.",
      what='the definitive treaty of peace',
      printings=[k(NI, '05-19', 3),
                 k(ALX, '05-20', 2),
                 k(ORA, '05-22', 1),
                 k(POR, '05-24', 1),
                 k(NHG, '05-25', 2),
                 k(RL, '05-25', 2),
                 k(RIR, '05-29', 1),
                 k(KG, '06-04', 3)]),
 dict(id='leclerc-proclamation-on-the-arrest-of-toussaint-june-1802', kind='document_group',
      label="General Leclerc to the citizens of St. Domingo, June 1802: 'I have thought proper to cause him to be arrested'",
      definition="Printings of the proclamation of the French general in chief at St. Domingo, dated at the Cape, 20 Prairial, year 10 (8 June 1802), and signed by Leclerc, in two translations. Six papers print the one that begins 'General Toussaint not being contented with enjoying the amnesty which had been granted him, attempted again to kindle the flames of civil war. I have thought proper to cause him to be arrested'; three print another: 'Gen. Toussaint did not wish to enjoy the amnesty which had been granted to him; he has continued to conspire; he was just going to rekindle a civil war. I thought it necessary to have him arrested'. Both promise that the proofs will be published and that the measure should not alarm those who have laid down their arms. Counted together as one item in two printed forms. The French commander's own proclamation, as the papers translated it.",
      role='published_document', words=55, dateline=False,
      core=[r'A\s?RMY\s+OF\s+S\w*\.?\s+D\s?OMINGO\.?\s+The\s+[Gg]eneral\s+in\s+[Cc]hief'],
      first="General Leclerc's proclamation of 8 June 1802 at the Cape: Toussaint has been arrested.",
      what="General Leclerc's proclamation on Toussaint's arrest",
      printings=[k(ALX, '06-23', 3),
                 k(NI, '06-25', 3),
                 (k(NHG, '06-29', 3), {'note': "The other translation ('Gen. Toussaint did not wish to enjoy the amnesty')."}),
                 k(ORA, '07-03', 2),
                 (k(RIR, '07-03', 3), {'note': "The other translation ('Gen. Toussaint did not wish to enjoy the amnesty')."}),
                 k(POR, '07-05', 2),
                 k(RL, '07-06', 3),
                 k(KG, '07-09', 2),
                 (k(CRG, '07-13', 4), {'note': "The other translation ('Gen. Toussaint did not wish to enjoy the amnesty')."})]),
 dict(id='new-york-report-algerine-cruisers-take-a-portuguese-frigate-1802', kind='message_group',
      label="New York, July 1802: from Captain Dawson, 'an engagement between two Algerine cruisers and a Portuguese man of war off Malaga'",
      definition="Printings of a report from the New York Gazette of 16 July 1802, from the captain of a schooner arrived in 38 days from Gibraltar: 'From Capt. Dawson we have received an account of an engagement between two Algerine cruisers and a Portuguese man of war off Malaga, wherein the former were victorious. The force of the Algerines was a frigate of 32 guns (the same which was presented by the American government to the Dey) and a xebec'; the Portuguese frigate struck after an action of three hours and was carried into Algiers. The Virginia Argus prints a Philadelphia form of the report that opens in other words ('The Captain of an American vessel arrived at New-York from Gibraltar, has given an account of the engagement') and goes on in the same words; counted with the others as a printed form. A ship captain's report at second hand.",
      role='report', words=60, dateline=False,
      core=[r'From\s+[Cc]apt\w*\.?\s+D\s?AWSON,?\s+we\s+have\s+received\s+an\s+account'],
      first="New York, July 1802: a captain from Gibraltar reports that two Algerine cruisers, one of them the frigate the United States gave the Dey, have taken a Portuguese frigate off Malaga.",
      what='the report of the Algerine cruisers and the Portuguese frigate',
      printings=[k(NI, '07-23', 3),
                 k(ORA, '07-24', 1),
                 k(POR, '07-26', 2),
                 k(NHG, '07-27', 2),
                 k(RL, '07-27', 2),
                 (k(REC, '07-28', 3), {'stop': r'the\s+number\s+of\s+their\s+crews', 'note': "RevX runs a note from another column ('NOTE. * There is an error in printing some of these figures') into this paragraph; the excerpt ends before it."}),
                 (k(VA, '07-31', 2), {'core': [r'The\s+Captain\s+of\s+an\s+American\s+vessel\s+arrived\s+at\s+New.York\s+from\s+Gibraltar'],
                                      'note': "The Virginia Argus prints a Philadelphia form of the report, dated July 20, which opens in other words ('The Captain of an American vessel arrived at New-York from Gibraltar, has given an account of the engagement') and goes on in the same words as the others; counted with them as a printed form of the report."}),
                 k(CRG, '08-03', 3)]),
 dict(id='paine-returns-to-america-1802', kind='context_group',
      label="Thomas Paine returns to America, 1802: the President's letter to him, and his letters 'To the Citizens of the United States'",
      children=['jefferson-letter-to-paine-published-august-1802', 'paine-letter-the-first-to-the-citizens-november-1802',
                'paine-letter-the-second-to-the-citizens-november-1802'],
      definition="Three documents on the return of Thomas Paine, author of 'Common Sense' and 'The Rights of Man', who had lived in Europe since 1787 and landed at Baltimore at the end of October 1802: the President's letter of 1801 offering him a passage in a national ship, published in August 1802 from a London paper, and the first two of Paine's letters 'To the Citizens of the United States', which the National Intelligencer published in November. Contains those three groups."),
 dict(id='jefferson-letter-to-paine-published-august-1802', parent='paine-returns-to-america-1802', kind='document_group',
      label="'You expressed a wish in your letter to return to America by a national ship': the President's letter to Thomas Paine, published August 1802",
      definition="Printings of a letter from Thomas Jefferson, President of the United States, to Thomas Paine, which a New York paper took from a London paper in August 1802 ('about which so much has been said'): 'You expressed a wish in your letter to return to America by a national ship; Mr. Dawson, who brings over the treaty, and who will present you this letter, is charged with orders to the Captain of the Maryland to receive and accommodate you back, if you can be ready to depart at such a short warning'; it ends with the wish that Paine 'may long live to continue your useful labours, and to reap their reward in the thankfulness of nations'. Papers of both parties printed it, some with hostile introductions; two printed it again in essays and columns of the President's letters. The President's own letter, as the papers printed it.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:Y\s?OU|You)\s+express(?:ed)?\s+a\s+w\w+,?\s+in\s+your\s+letter,?\s+to\s+return\s+to\s+America'],
      first="The President's letter to Thomas Paine offering him a passage in a national ship, published in August 1802 from a London paper.",
      what="the President's letter to Thomas Paine",
      printings=[k(ALX, '08-13', 2),
                 k(POR, '08-16', 2),
                 k(NI, '08-16', 3),
                 (k(ORA, '08-21', 1), {'note': 'The Oracle prints the letter after an introduction of its own that attacks it.'}),
                 k(CRG, '08-24', 3),
                 (k(RL, '08-31', 3), {'field': CA, 'note': "RevX abridges this paragraph with '...' and gives only the letter's first words; the older CA transcription has the whole letter, so the excerpt comes from the CA text, which is garbled in places."}),
                 k(KG, '09-03', 3),
                 k(REC, '09-15', 3),
                 (k(ALX, '10-12', 2), {'note': "Printed again, whole, inside an essay headed 'TOM PAINE, Invited to this country by his Right Worthy and affectionate Friend, T. JEFFERSON. No. II.', 'as we find it published in the London papers'."}),
                 (k(POR, '12-06', 2), {'note': "Printed again, whole, under the heading 'From Jefferson to Paine', among letters of the President that the paper prints against him."})]),
 dict(id='paine-letter-the-first-to-the-citizens-november-1802', parent='paine-returns-to-america-1802', kind='document_group',
      label="Thomas Paine, 'To the Citizens of the United States', Letter the First: 'After an absence of almost fifteen years, I am again returned'",
      definition="Printings of the first of Thomas Paine's letters 'To the Citizens of the United States', first published in the National Intelligencer of 15 November 1802: 'After an absence of almost fifteen years, I am again returned to the country in whose dangers I bore my share, and to whose greatness I contributed my part. When I sailed for Europe in the spring of 1787 it was my intention to return to America the next year'. He quotes a letter of his own of about 1789 on the principles of the revolution 'expiring on the soil that produced them', and closes by declaring 'the line of conduct I shall pursue'. Papers of both parties printed it, some with introductions for or against him. Paine's own public letter, a political argument.",
      role='published_document', words=55, dateline=False,
      core=[r'T\s?HOMAS\s+P\s?AINE?[,.]?\s+(?:TO|To)\s+the\s+(?:C\s?ITIZENS|[Cc]itizens)\s+of\s+the\s+United\s+States[.:]?\s+L\s?ETTER\s+(?:THE|the)\s+F\s?IRST',
            r'L\s?ETTER\s+(?:THE|the)\s+F\s?IRST\.?\s+A\s?F\s?TER\s+an\s+absence', r'[BL]\s?ETTER\s+THE\s+FIRST\.?\s+A\s?F\s?TER\s+an\s+absence'],
      first="Thomas Paine's first letter 'To the Citizens of the United States', published in the National Intelligencer on 15 November 1802.",
      what="Paine's first letter to the citizens",
      printings=[k(NI, '11-15', 3),
                 k(RIR, '11-27', 3),
                 k(ORA, '11-27', 2),
                 k(POR, '11-29', 2),
                 k(NHG, '11-30', 2),
                 k(RL, '11-30', 2),
                 k(ALX, '12-01', 2),
                 (k(CRG, '12-07', 1), {'field': CA, 'note': "RevX leaves out the letter's opening (from its heading to 'the scaffold') and runs on from the editor's introduction; the older CA transcription has the opening, so the excerpt comes from the CA text, which is garbled."}),
                 k(KG, '12-14', 2)]),
 dict(id='paine-letter-the-second-to-the-citizens-november-1802', parent='paine-returns-to-america-1802', kind='document_group',
      label="Thomas Paine, 'To the Citizens of the United States', Letter the Second: on the ex-president John Adams and the Federalists",
      definition="Printings of the second of Thomas Paine's letters 'To the Citizens of the United States', first published in the National Intelligencer of 22 November 1802: 'As the affairs of the country to which I am returned are of more importance to the world, and to me, than of that I have lately left (for it is through the new world the old must be regenerated, if regenerated at all) I shall not take up the subject of the French revolution'. It turns on 'the ex-president John Adams', whom it accuses, in Paine's words, of having projects 'to overturn the liberties of America, and the representative system of government'. Paine's own public letter: a political argument with allegations against a named public man.",
      role='published_document', words=55, dateline=False,
      core=[r'T\s?HOMAS\s+P\s?AINE?[,.]?\s+(?:TO|To)\s+the\s+(?:C\s?ITIZENS|[Cc]itizens)\s+of\s+the\s+United\s+States[.:]?\s+L\s?ETTER\s+(?:THE|the)\s+S\s?ECOND',
            r'L\s?ETTER\s+(?:THE|the)\s+S\s?ECOND\.?\s+A\s?S\s+the\s+affairs'],
      first="Thomas Paine's second letter 'To the Citizens of the United States', published in the National Intelligencer on 22 November 1802.",
      what="Paine's second letter to the citizens",
      printings=[k(NI, '11-22', 2),
                 (k(ALX, '12-01', 2), {'note': 'The Alexandria Advertiser prints the second letter directly after the first, in one column.'}),
                 k(RIR, '12-04', 3),
                 k(NHG, '12-07', 2),
                 k(RL, '12-07', 2),
                 k(CRG, '12-16', 1),
                 k(ORA, '12-18', 1),
                 k(KG, '12-21', 2)]),
 dict(id='french-senate-proclaims-bonaparte-consul-for-life-august-1802', kind='document_group',
      label="Paris, August 1802: the president of the Conservative Senate addresses Bonaparte, proclaimed First Consul for life, and the First Consul replies",
      definition="Printings of the account from the Paris papers of 3 and 4 August 1802, in two translations, of the Conservative Senate's audience with the First Consul: its president, Barthélemy, 'addressed Bonaparte in a speech of which the following are extracts: \"Citizen First Consul, The French, grateful for the immense services you have rendered to them, wish that the First Magistracy of the State should be irrevocably placed in your hands\"' ('A new career commences for the First Consul'), read the Senate's decree that, as the papers print it, 3,568,885 of 3,577,259 citizens had voted for Napoleon Bonaparte as Consul for life, and the First Consul replied. Five papers print the translation that begins 'At the Levee yesterday'; three print another ('The French people, as a mark of gratitude'), which the Alexandria Advertiser takes from the New York Mercantile Advertiser. Counted together as one item in two printed forms. The French Senate's and the First Consul's own words, as the papers translated them.",
      role='published_document', words=60, dateline=True, back=True,
      core=[r'(?:A\s?T\s+the\s+Levee\s+ye\w+,?\s+)?[Cc]itizen\s+B\s?AR\s?TH\S*MY', r'At\s+the\s+Levee\s+ye\w+,?\s+Citizen\s+Bar'],
      first="Paris, August 1802: the president of the French Senate addresses Bonaparte on his election as First Consul for life.",
      what="the French Senate's address to the First Consul for life",
      printings=[k(NHG, '09-28', 2),
                 k(RL, '09-28', 2),
                 (k(ALX, '09-30', 2), {'note': 'The other translation, from the New York Mercantile Advertiser.'}),
                 k(ORA, '10-02', 1),
                 (k(POR, '10-04', 2), {'field': CA, 'back': False, 'note': "RevX abridges the address with '...'; the older CA transcription has it whole, so the excerpt comes from the CA text, which is garbled in places."}),
                 k(CRG, '10-05', 2),
                 (k(NI, '10-10', 3), {'note': 'The other translation.'}),
                 (k(KG, '10-19', 2), {'note': 'The other translation.'})]),
 dict(id='washington-report-letters-from-algiers-of-7-july-1802', kind='message_group',
      label="Washington, 13 October 1802: 'letters have been received in this country from Algiers, as late as the 7th of July'",
      definition="Printings of a paragraph from Washington of 13 October 1802: 'We understand that letters have been received in this country from Algiers, as late as the 7th of July, which furnish the following information: The Dey of Algiers has demanded of the American Consul to direct the United States frigate the George Washington, to be brought to Algiers, for the purpose of being sent by the Dey to Constantinople'; the Dey later turned to the consuls of nearer nations; a Tripolitan corsair brought the American brig Franklin into Algiers as a prize; Spain bought off a threatened war. A report at second hand, from letters the paragraph does not name.",
      role='report', words=60, dateline=True,
      core=[r'(?:W\s?E|We)\s+understand\s+that\s+letters\s+have\s+been\s+received\s+in\s+this\s+country\s+from\s+Algiers'],
      first="Washington, 13 October 1802: letters from Algiers report that the Dey demanded the United States frigate George Washington, and that a Tripolitan corsair brought in the American brig Franklin.",
      what='the Washington report of letters from Algiers',
      printings=[k(NI, '10-13', 3),
                 k(ALX, '10-14', 3),
                 k(ORA, '10-23', 2),
                 k(KG, '10-26', 3),
                 k(NHG, '10-26', 3),
                 k(RL, '10-26', 2),
                 k(RIR, '10-30', 2),
                 k(CRG, '11-02', 3)]),
 dict(id='madrid-letter-convention-with-spain-on-claims-august-1802', kind='message_group',
      label="Madrid, August 1802: 'the plenipotentiaries of the United States and Spain signed a convention' for a board of commissioners on losses",
      definition="Printings of a short letter from Madrid dated in August 1802 (15 August in most papers), which some papers call a circular of the American consul general at Madrid and others a letter 'from an official character at the Spanish court': 'On the 11th instant the plenipotentiaries of the United States and Spain signed a convention for the appointment of commissioners who are to form a board, and sit at Madrid, for the indemnification of those who have sustained losses, damages, or injuries in consequence of the excesses of individuals of either nation, during the late war, contrary to the existing treaty or the law of nations. The convention to have no force or effect, until it be ratified by the contracting parties.' An official's letter, as the papers printed it.",
      role='report', words=60, dateline=False, back=True,
      core=[r'(?:S\s?IR[,.—\s]+)?["“]?On\s+the\s+11th\s+inst\w*\.?,?\s+the\s+[Pp]lenipotentiaries'],
      first="Madrid, August 1802: a letter reports that the United States and Spain have signed a convention for a board to settle claims for losses in the late war.",
      what='the Madrid letter on the convention with Spain',
      printings=[k(ALX, '10-18', 3),
                 k(NI, '10-20', 3),
                 k(ORA, '10-23', 2),
                 k(POR, '10-25', 3),
                 k(RIR, '10-30', 3),
                 (k(KG, '11-02', 3), {'note': "The Kentucky Gazette dates the letter '5th August'."}),
                 k(CRG, '11-09', 2)]),
 dict(id='new-york-report-fire-of-2-november-1802', kind='message_group',
      label="New York, 3 November 1802: 'one of the most alarming Fires that has ever happened in this city'",
      definition="Printings of a New York report of 3 November 1802, in two forms: 'One of the most alarming Fires that has ever happened in this city, within our recollection, broke out last evening, between 8 & 9 o'clock, in a stable in Bridge-street, between Whitehall & Broad-streets' (two papers), or 'Last evening one of the most alarming Fires that has ever happened in this city, broke out in a stable in Bride-street, between Whitehall and Broad-streets' (five papers; the street is printed 'Bride-street' in some papers and 'Bridge-street' in others); in less than an hour and a half about fifty buildings, mostly dwelling houses, were burnt, pulled down or gutted. The report goes on to name some of the sufferers; the excerpts end before their names. Counted together as one report in two printed forms. A New York paper's report.",
      role='report', words=55, dateline=True,
      core=[r'(?:Last\s+evening\s+)?one\s+of\s+(?:\S+\s+)?the\s+most\s+alarming\s+F\s?IRES?'],
      first="New York, 3 November 1802: a fire in a stable near Whitehall destroys about fifty buildings.",
      what='the New York report of the fire',
      printings=[(k(ALX, '11-08', 2), {'dateline': False, 'core': [r'November\s+3\.\s+One\s+of\s+the\s+most\s+alarming\s+F'], 'note': "The other form ('One of the most alarming Fires that has ever happened in this city, within our recollection'), under the date 'November 3.' without a place; the name 'LA CROSSE' printed above it is the signature of the item before."}),
                 k(NHG, '11-09', 3),
                 k(RL, '11-09', 3),
                 k(RIR, '11-13', 3),
                 (k(ORA, '11-13', 3), {'field': CA, 'note': "RevX abridges this report with '...'; the older CA transcription has it, so the excerpt comes from the CA text, which is garbled in places."}),
                 k(CRG, '11-16', 3),
                 (k(KG, '11-23', 3), {'note': "The other form ('One of the most alarming FIRES that ever happened in this city, within our recollection')."})]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797, 1800 and 1804):
# "BALTIMORE, JAN. 23."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False):
    for core in cores:
        m = re.search(core, text, re.I | re.S)
        if m:
            start = m.start()
            if back:   # start at the beginning of the sentence that introduces the item
                cuts = [(text.rfind(b, 0, start), len(b)) for b in ('. ', '.] ', '] ', '." ', '.” ', '? ', '— ', '—', ': ')]
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
            problems.append((s['id'], key, 'page not in the 1802 pages'))
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
        elif field == CA and 'field' not in over and 'RevX' not in note and 'no RevX' not in note:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'printed': pages[key]['date'], 'field': field, 'excerpt_start': first, 'excerpt_end': last,
                     'excerpt': excerpt, 'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['printed'], r['page_key'], r['story']))
    for n, r in enumerate(rows, 1):   # numbered in order of printed date
        r['id'] = f'S02-{n:03}'
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
               'admission_rule': 'Reviewed 1802 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1802/'
    return {
        'ledger_id': 'ledger:stories-1802', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1802', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1802, and of 1801 where they reach the 1802 pages (long-running ones '
                   'included), phrase searches on all 2,968 pages of 1802 in both transcriptions, reading of every hit, and scan checks of each '
                   'admitted passage, by the one admission rule (9 or more papers admitted, 7 or 8 chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1801.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1802.py': 'ledger_code', 'work/archive_data/ledgers/stories_1802_review.json': 'scan_review',
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
