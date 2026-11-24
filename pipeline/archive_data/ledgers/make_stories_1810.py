"""Write ledgers/stories_1810.json: reviewed stories of 1810, round one.

1810 is read by the one admission rule the other reviewed years follow (outputs/story_discovery_1809/README.md, "Selection
rule"; docs/rules-and-exceptions.md, R-01): every single printed item in 9 or more newspapers is admitted, except digests;
items in 7 or 8 papers are chosen to cover the months and the kinds of news; items are counted one by one; a sub-story may
have fewer papers when its parent reaches 7. The automatic families first printed in 1810 that reach 3 or more papers,
long-running ones included, were split into single printed items with work/story_items.py --long-running (items.json), and
again with year 1809 over the 1810 pages (items_from_1809.json); every item in 7 or more papers, and every item in 5 or 6
that a deeper comparison put in more papers, was counted again by its own words, and a sweep of word-for-word passages
shared by 7 or more papers found short items the families miss. Every chosen item and every candidate set aside was
counted with phrase searches over all 3,933 pages of 1810 in both transcriptions (work/story_phrase_search.py). See
outputs/story_discovery_1810/README.md.

1810 is the collection's last year; only printings dated 1810 are counted. The 1810 pages are those whose issue the data
release dates to 1810 (work/year_search_pages.py 1810 ... --printed-dates); no 1810 issue has a corrected date, and the
release's map of misfiled RevX pages (derived/revx_page_map.parquet) lists none for 1810. 1810 has 11 catalogue series,
which are 11 papers; no paper appears under two catalogue numbers.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1810_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (a review of 1801 runs at the same time and may take the
next number first):
    python work/archive_data/ledgers/make_stories_1810.py [--table] [--base 0.11.13 --target 0.11.14]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1810/search_pages.json). The excerpts are cut from
the 1810 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1810'
D = PROJECT/'outputs/story_discovery_1810'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1810_review.json'
OUT = HERE/'stories_1810.json'
BASE, TARGET = '0.11.13', '0.11.14'   # defaults; see the docstring
DATA_RELEASE = '0.11.13'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-23'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn82014385': 'The Delaware Gazette', 'sn83016082': 'The Portland Gazette', 'sn83025442': 'The Rhode-Island American',
         'sn83025519': 'The Constitutionalist', 'sn83025561': 'The Rhode-Island Republican', 'sn83025588': 'The New Hampshire Gazette',
         'sn84024013': 'The Alexandria Daily Gazette', 'sn84024710': 'The Virginia Argus', 'sn84024736': 'The Enquirer',
         'sn84038455': 'The Martinsburgh Gazette', 'sn85025815': 'The Norfolk Gazette'}
ONE = {'DEL': 'sn82014385', 'POR': 'sn83016082', 'RIA': 'sn83025442', 'CON': 'sn83025519', 'RIR': 'sn83025561', 'NHG': 'sn83025588',
       'ALX': 'sn84024013', 'VA': 'sn84024710', 'ENQ': 'sn84024736', 'MAR': 'sn84038455', 'NOR': 'sn85025815'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1810), page and edition (one catalogue number per paper)."""
    return f'{ONE[paper]}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release (none for 1810)."""
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
 dict(id='president-message-on-the-militia-3-january-1810', kind='document_group',
      label="The President's message of 3 January 1810: the act for a detachment of 100,000 militia will expire on 30 March",
      definition="Printings of the President's message to the Senate and House of Representatives of 3 January 1810: 'The act authorising the detachment of one hundred thousand men from the militia, will expire on the 30th of March next. Its early revival is recommended, in order that timely steps may be taken for arrangements, such as the act contemplated'; it asks Congress to consider a volunteer force and how far further provision may be expedient for putting into actual service any part of the naval armament not now employed. Printed in the papers' reports of Congress. The President's own message.",
      role='published_document', words=60, dateline=False,
      head=r'To\s+the\s+Senate\s+and\s+(?:the\s+)?House\s+of\s+Representatives\s+of\s+the\s+United\s+States\.?\s*[—-]*\s*',
      core=[r'(?:T\s?HE|The)\s+[Aa]ct\s+authori[sz]ing\s+(?:the|a)\s+(?:de|at)tachment\s+of\s+(?:one\s+hundred\s+thousand|100,000)\s+men'],
      first="The President's message of 3 January 1810: the act for a detachment of 100,000 militia will expire on 30 March; its early revival is recommended.",
      what="the President's message of 3 January on the militia",
      printings=[k('ALX', '01-04', 3), k('NOR', '01-08', 3), k('VA', '01-09', 2), k('RIR', '01-10', 3), k('RIA', '01-12', 2),
                 k('POR', '01-15', 2), k('NHG', '01-16', 2)]),
 dict(id='leib-resolutions-on-the-erskine-arrangement-march-1810', kind='document_group',
      label="Mr. Leib's resolutions in the Senate, 8 March 1810: the President to instruct our minister to demand of the British government compliance with the arrangement made by Mr. Erskine",
      definition="Printings of the resolutions that Mr. Leib submitted to the Senate for consideration on 8 March 1810, as the papers reported the Senate's proceedings: 'Resolved, That the President of the United States be required to instruct our minister at the court of Great Britain, to demand of the British government an immediate compliance with the arrangement made by their minister, Mr. Erskine, with this government, comprising atonement for the attack upon the frigate Chesapeake, and a relinquishment of the orders in council'; a further resolution concerns what is to follow the failure or refusal of the British government to carry the arrangement into effect. Counted as a paragraph of the proceedings by its own words (X-1800-08, X-1804-04). A senator's resolutions, submitted for consideration: a policy argument.",
      role='published_document', words=60, dateline=False,
      head=r'(?:Mr\.?\s+Leib\s+submitted\s+the\s+following\s+resolutions?\s+for\s+consideration[:.;,]?\s*[—-]*\s*|The\s+following\s+resolutions\s+were\s+offered\s+to\s+the\s+Senate[^:]{0,120}:\s*)',
      core=[r'(?:R\s?ESOLVED|Resolved),?\s+[Tt]hat\s+the\s+President\s+of\s+the\s+(?:United\s+States|U\.\s?States|U\.\s?S\.),?\s+be,?\s+required,?\s+to\s+instruct\s+our\s+[Mm]inister'],
      first="Mr. Leib's resolutions in the Senate of 8 March 1810: the British government to be asked to carry into effect the arrangement made by Mr. Erskine.",
      what="Mr. Leib's resolutions",
      printings=[k('ALX', '03-13', 3), k('DEL', '03-14', 2), k('RIA', '03-16', 3), k('VA', '03-16', 2), k('ENQ', '03-16', 2),
                 k('NOR', '03-16', 2), k('POR', '03-19', 2)]),
 dict(id='cadore-note-to-armstrong-14-february-1810', kind='document_group',
      label="The French minister of foreign relations' note to General Armstrong of 14 February 1810, as the papers printed it in April and May",
      definition="Printings of the note of the Duke of Cadore, the French minister of foreign relations, to General Armstrong, the American minister at Paris, in three translations: 'The undersigned has informed his Majesty, the Emperor and King, of the conversation, which he had with Mr. Armstrong, Minister Plenipotentiary of the United States of America. His Majesty authorises him to make the following reply: His Majesty would regard his Decrees of Berlin and Milan as violations of the principles of eternal justice, had they not been the necessary consequences of the British Orders in Council' (a second translation opens 'The undersigned having rendered an account to the Emperor and King, of the conversation'; the government's translation, printed late in May as an 'official copy', 'The undersigned has rendered an account to his majesty the emperor and king'). It offers that if the American minister will engage that American vessels shall not submit to the British Orders in Council of November 1807, the undersigned is authorized to conclude a convention tending to renew the treaty of commerce. Counted together (C-02). The French minister's own note.",
      role='published_document', words=60, dateline=False,
      head=r'(?:Note\s+of\s+the\s+[Mm]inister\s+of\s+[Ff]oreign\s+[Rr]elations[^.]{0,120}\.\s*|OFFICIAL\s+COPY\.\s*)',
      core=[r'(?:["“]\s*)?(?:T\s?HE|The)\s+undersigned\s+(?:has\s+informed|having\s+rendered\s+an\s+account|has\s+rendered\s+an\s+account)\s+(?:to\s+)?(?:his\s+[Mm]ajesty,?\s+)?the\s+[Ee]mperor\s+and\s+[Kk]ing'],
      first="The French minister of foreign relations' note to General Armstrong of 14 February 1810: the Emperor's reply on the decrees of Berlin and Milan.",
      what="the French minister's note of 14 February",
      printings=[k('NHG', '04-17', 2), k('ALX', '04-17', 3), k('DEL', '04-18', 2), k('NOR', '04-18', 3), k('RIA', '04-20', 2),
                 k('VA', '04-20', 2), k('ENQ', '04-20', 2), k('POR', '04-23', 1),
                 (k('ALX', '05-05', 3), {'note': 'Printed again, in the first translation.'}),
                 (k('ALX', '05-29', 2), {'note': "Printed again, in the government's translation ('Official copy')."}),
                 (k('VA', '05-29', 2), {'note': "Printed again, in the government's translation."}),
                 (k('ENQ', '05-29', 2), {'note': "Printed again, in the government's translation."})]),
 dict(id='act-concerning-commercial-intercourse-1-may-1810', kind='document_group',
      label="The act of 1 May 1810 concerning the commercial intercourse between the United States and Great Britain and France",
      definition="Printings of the act of Congress approved on 1 May 1810, 'An act concerning the commercial intercourse between the United States and Great Britain and France and their dependencies, and for other purposes': 'That from and after the passage of this act, no British or French armed vessel shall be permitted to enter the harbors or waters under the jurisdiction of the United States'; its fourth section provides that in case either Great Britain or France shall, before the third day of March next, so revoke or modify her edicts as that they shall cease to violate the neutral commerce of the United States, which fact the President shall declare by proclamation, and the other nation shall not within three months revoke hers, sections of the non-intercourse act of 1809 shall be revived against that other nation. Counted where the act is printed under its own title; the bill printed before it passed is not counted with it (X-1803-10). The act of Congress.",
      role='published_document', words=60, dateline=False,
      head=r'(?:\(?B\s?Y\s+A\s?UTHORITY\.?\)?\s*)',
      core=[r'(?:A\s?N\s+)?A\s?C\s?T[.,]?\s+[Cc](?:ONCERNING|oncerning)\s+the\s+commercial\s+intercourse'],
      first="The act of 1 May 1810 concerning the commercial intercourse with Great Britain and France: British and French armed vessels are forbidden American waters.",
      what='the act of 1 May 1810',
      printings=[k('ALX', '05-08', 2), k('VA', '05-08', 3), k('NOR', '05-09', 2),
                 (k('ENQ', '05-11', 2), {'field': CA, 'core': [r'A\s?N\s+A\s?C\s?T\s+\S{0,3}oncerning\s+the\s+commercial\s+intercourse'], 'note': 'RevX lacks the act on this page; the older CA transcription has it, so the excerpt comes from the CA text.'}), k('DEL', '05-12', 2),
                 k('POR', '05-14', 2), k('NHG', '05-15', 1)]),
 dict(id='correspondence-on-jacksons-recall-published-may-1810', kind='context_group',
      label="Mr. Pinkney and Lord Wellesley on the British minister Jackson, as the papers published their correspondence in May 1810",
      children=['pinkney-note-to-wellesley-2-january-1810', 'wellesley-answer-to-pinkney-14-march-1810'],
      definition="Two letters of the correspondence between the American minister in London, William Pinkney, and the British Secretary of State for Foreign Affairs, the Marquis Wellesley, on the conduct and recall of the British minister to the United States, Francis James Jackson, as the papers printed them from the National Intelligencer of 21 May 1810 with an extract of Mr. Pinkney's letter of 21 March to the Secretary of State. Contains those two groups."),
 dict(id='pinkney-note-to-wellesley-2-january-1810', parent='correspondence-on-jacksons-recall-published-may-1810', kind='document_group',
      label="Mr. Pinkney's letter to Lord Wellesley of 2 January 1810 on the correspondence with Mr. Jackson",
      definition="Printings of the American minister's letter to the Marquis Wellesley, dated Great Cumberland Place, 2 January 1810: 'In the course of the official correspondence, which has lately taken place between the American government and Mr. Jackson'; it sets out the American government's account of why it ceased to receive communications from Mr. Jackson and asks that he be recalled. Mr. Pinkney's own letter.",
      role='published_document', words=60, dateline=False,
      head=r'(?:Great\s+)?Cumberland\s+Place,?\s+2d\s+January,?\s+1810\.?\s*',
      core=[r'(?:M\s?Y|My)\s+(?:L\s?ORD|Lord),?\s*[—-]*\s*(?:I\s?N|In)\s+the\s+course\s+of\s+the\s+official\s+correspondence'],
      first="Mr. Pinkney's letter to Lord Wellesley of 2 January 1810: the American government's account of its correspondence with Mr. Jackson.",
      what="Mr. Pinkney's letter of 2 January",
      printings=[k('ALX', '05-21', 2), k('VA', '05-22', 2), k('ENQ', '05-22', 2), k('NOR', '05-23', 2), k('POR', '05-28', 2),
                 k('RIA', '05-29', 1), k('NHG', '05-29', 2), k('CON', '06-04', 1)]),
 dict(id='wellesley-answer-to-pinkney-14-march-1810', parent='correspondence-on-jacksons-recall-published-may-1810', kind='document_group',
      label="Lord Wellesley's answer to Mr. Pinkney, Foreign Office, 14 March 1810: Mr. Jackson to deliver over the charge of his Majesty's affairs",
      definition="Printings of the Marquis Wellesley's letter to Mr. Pinkney, dated Foreign Office, 14 March 1810: 'The letter which I had the honor to receive from you under date of the 2d of January, together with the additional paragraph received on the 24th January, has been laid before the king'; it says that Mr. Jackson 'does not appear, on the present occasion, to have committed any intentional offence against the government of the United States', and that 'Mr. Jackson is ordered to deliver over the charge of his Majesty's affairs in America, to a person properly qualified to carry on the ordinary intercourse between the two governments'. The Delaware Gazette prints it with remarks of its own. The British Secretary of State's own letter.",
      role='published_document', words=60, dateline=False,
      head=r'(?:Lord\s+Wellesl?e?y\s+to\s+Mr\.?\s+Pinkney\.?\s*|The\s+most\s+noble\s+The\s+Marquis\s+Wellesley,?\s+&c\.?\s+&c\.?\s*|The\s+Marquis\s+Wellesley,?\s+&c\.?\s+&c\.?\s*)?',
      core=[r'(?:F\s?OREIGN|Foreign)\s+(?:O\s?FFICE|Office),?\s+(?:M\s?ARCH|March)\s+14', r'(?:S\s?IR|Sir),?\s*[—-]*\s*(?:T\s?HE|The)\s+letter\s+which\s+I\s+had\s+the\s+hono\w+\s+to\s+receive\s+from\s+you'],
      first="Lord Wellesley's answer to Mr. Pinkney of 14 March 1810: Mr. Jackson is ordered to deliver over the charge of the British affairs in America.",
      what="Lord Wellesley's answer of 14 March",
      printings=[k('ALX', '05-21', 3), k('VA', '05-22', 3), k('ENQ', '05-22', 3), k('DEL', '05-23', 2), k('NOR', '05-23', 2),
                 k('RIA', '05-25', 3), k('POR', '05-28', 3), k('NHG', '05-29', 2), k('CON', '06-04', 2)]),
 dict(id='burdett-address-to-the-people-of-england-1810', kind='document_group',
      label="Sir Francis Burdett's address to the people of England on the power of the House of Commons to imprison, as the London papers printed it in March 1810",
      definition="Printings of the letter of Sir Francis Burdett, member of Parliament for Westminster, to his constituents, 'the People of England': 'The House of Commons having passed a vote, which amounts to a declaration, that an order of theirs is to be of more weight than Magna Charta and the Laws of the Land, I think it my duty to lay my sentiments before you'; it argues that the House has no power to imprison the people of England. The House of Commons committed him to the Tower for it in April 1810, which the papers reported in the same weeks. Sir Francis Burdett's own argument.",
      role='published_document', words=60, dateline=False,
      head=r'(?:To\s+the\s+[Pp]eople\s+of\s+England\.?\s*[—-]*\s*)',
      core=[r'(?:G\s?ENTLEMEN|Gentlemen)\W+(?:T\s?HE|The)\s+House\s+of\s+Commons\s+having\s+passed\s+a\s+vote'],
      first="Sir Francis Burdett's address to the people of England: the House of Commons claims a power to imprison that he denies.",
      what="Sir Francis Burdett's address",
      printings=[k('RIA', '05-22', 2), k('ENQ', '05-22', 3), k('RIR', '05-23', 1), k('NOR', '05-23', 3), k('ALX', '05-25', 2),
                 k('VA', '05-25', 1), k('NHG', '06-05', 2)]),
 dict(id='caracas-address-of-the-supreme-junta-1810', kind='document_group',
      label="The address of the supreme government of Caracas, 1810, as the papers printed it from New York in June: 'It has pleased Almighty God to grant to every country alike the natural right of its own sovereignty'",
      definition="Printings of a state paper of the supreme junta of Caracas, Venezuela, received at New York by the brig Thomas from Cumana and headed in several papers 'Spanish America—Declared Independent' or 'Declaration of Independence': 'It has pleased Almighty God to grant to every country alike the natural right of its own sovereignty. These provinces, planted by Spain, fostered and protected by her power, have, and of right ought to have, submitted to her guidance and direction during the period of infancy'; it declares that, the King being taken from Spain and the lawful government there destroyed, the provinces will not submit to the domination of any European or foreign power. The junta's own words, as the New York papers translated them.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:I\s?T|It)\s+has\s+pleased\s+Almighty\s+God\s+to\s+grant', r'(?:T\s?HESE|These)\s+provinces,?\s+planted\s+by\s+Spain'],
      first="The supreme government of Caracas declares that the provinces will submit to no European or foreign power.",
      what='the address of the government of Caracas',
      printings=[k('ALX', '06-13', 2), k('RIA', '06-15', 3), k('VA', '06-15', 2), k('ENQ', '06-15', 2), k('NOR', '06-15', 2),
                 k('CON', '06-18', 3), k('NHG', '06-19', 2), k('RIR', '06-20', 1)]),
 dict(id='despatches-received-by-the-john-adams-june-1810', kind='context_group',
      label="Despatches received by the frigate John Adams from Paris and London, published in June 1810: General Armstrong on the seizures of American property",
      children=['armstrong-despatch-of-10-march-1810-with-letter-to-cadore', 'armstrong-letter-of-7-april-1810'],
      definition="Two of the despatches that the frigate John Adams brought from France in June 1810 and the National Intelligencer published, as the papers reprinted them: General Armstrong's letter of 10 March 1810 to the Secretary of State, with his letter of that day to the Duke of Cadore, and his letter of 7 April. The publication holds about twenty letters of General Armstrong and Mr. Pinkney; the others are in 7 or 8 papers each (see the README). Contains those two groups."),
 dict(id='armstrong-despatch-of-10-march-1810-with-letter-to-cadore', parent='despatches-received-by-the-john-adams-june-1810', kind='document_group',
      label="General Armstrong to the Secretary of State, 10 March 1810: 'His Majesty has decided to sell the American property seized in Spain', with his letter of that day to the Duke of Cadore",
      definition="Printings of the extract of General Armstrong's letter to the Secretary of State of 10 March 1810: 'I have at length received a verbal message in answer to my note of the 21st ult. It was from the minister of foreign relations, and is in the following words:—\"His Majesty has decided to sell the American property seized in Spain, but the money arising therefrom shall remain in depot\"', followed by his letter of that day to the Duke of Cadore, which asks whether the seizures are reprisals for the non-intercourse law and argues that the law, operating only within the United States, gave France no ground for reprisal. The American minister's own letters.",
      role='published_document', words=60, dateline=False,
      head=r'(?:Extract\s+of\s+a\s+letter\s+(?:to\s+the\s+same\s+from\s+the\s+same|from\s+(?:General|Gen\.)\s+Armstrong\s+to\s+(?:Mr\.?\s+Smith|the\s+Secretary\s+of\s+State)[^.]{0,40})\.?\s*["“]?\s*(?:10th\s+March\.?\s*)?)',
      core=[r'I\s+have\s+at\s+length\s+received\s+a\s+verbal\s+message'],
      first="General Armstrong's letter of 10 March 1810: the French government will sell the American property seized in Spain and keep the money in deposit.",
      what="General Armstrong's letter of 10 March",
      printings=[k('ALX', '06-15', 2), k('NOR', '06-18', 2), k('VA', '06-19', 2), k('ENQ', '06-19', 2), k('RIA', '06-22', 1),
                 k('RIR', '06-27', 2), k('CON', '07-02', 1), k('POR', '07-02', 2), k('NHG', '07-03', 2)]),
 dict(id='armstrong-letter-of-7-april-1810', parent='despatches-received-by-the-john-adams-june-1810', kind='document_group',
      label="General Armstrong to the Secretary of State, 7 April 1810: 'The Emperor left Paris two days ago for St. Cloud'",
      definition="Printings of the extract of General Armstrong's letter to the Secretary of State dated Paris, 7 April 1810: 'The Emperor left Paris two days ago for St. Cloud, whence he goes to Compiegne, where he will remain till Easter. It is not probable that I shall have an answer to my propositions till he returns to Paris'; it reports what the minister told him the day before the Emperor set out. The American minister's own letter.",
      role='published_document', words=55, dateline=False,
      head=r'(?:Extract\s+of\s+a\s+letter\s+from\s+(?:General|Gen\.)\s+Armstrong\s+to\s+(?:Mr\.?\s+Smith|the\s+Secretary\s+of\s+State),?\s+dated\s+Paris,?\s+(?:the\s+)?7th\s+(?:of\s+)?April,?\s+1810\.?\s*["“]?\s*)',
      core=[r'(?:T\s?HE|The)\s+[Ee]mperou?r\s+left\s+Paris\s+two\s+days\s+ago'],
      first="General Armstrong's letter of 7 April 1810: no answer to his propositions is expected before the Emperor returns to Paris.",
      what="General Armstrong's letter of 7 April",
      printings=[k('ALX', '06-15', 3), k('NOR', '06-18', 2), k('VA', '06-19', 3), k('ENQ', '06-19', 3), k('RIA', '06-22', 2),
                 k('RIR', '06-27', 2), k('CON', '07-02', 1), k('POR', '07-02', 2), k('NHG', '07-17', 1)]),
 dict(id='rambouillet-decree-23-march-1810', kind='document_group',
      label="The Emperor's decree of Rambouillet, 23 March 1810, on American vessels, as the papers printed it in July",
      definition="Printings of the French imperial decree dated at Rambouillet, 23 March 1810: 'Taking into consideration that the Government of the United States has by an act of the 1st March, 1809, ordered, 1. That from the 20th of May next ensuing, vessels arriving in the United States, under the French flag, shall be seized and confiscated, together with their cargoes'; it decrees that all vessels under the American flag that have entered or shall enter the ports of France, her colonies or the countries occupied by French armies since 20 May 1809 shall be seized, and the proceeds of their sale deposited in the Caisse d'Amortissement. Some papers print it within a paragraph from the Bulletin des Lois that summarises it first; the Enquirer and the Norfolk Gazette print it again in December in the government's translation ('Translation of a decree, issued by the Emperor of the French, at Rambouillet'), with the documents sent to Congress with the President's message. The French government's own decree, in translation.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:T\s?HE|The)\s+last\s+number\s+of\s+the\s+B\s?ULLETIN\s+DES\s+LOIS', r'(?:R\s?AMBOUILLET|Rambouillet),?\s+(?:the\s+)?23d?\s+(?:of\s+)?(?:M\s?ARCH|March),?\s+1810', r'(?:T\s?AKING|Taking)\s+into\s+consideration\s+that\s+the\s+(?:G|g)overnment\s+of\s+the\s+United\s+States'],
      first="The Emperor's decree of Rambouillet of 23 March 1810: American vessels in the ports of France and her allies to be seized.",
      what='the decree of Rambouillet',
      printings=[k('ALX', '07-13', 2), k('NOR', '07-16', 2), k('RIA', '07-17', 2), k('NHG', '07-17', 2), k('VA', '07-17', 3),
                 k('ENQ', '07-17', 2), k('POR', '07-23', 2), k('CON', '07-23', 2),
                 (k('ENQ', '12-22', 1), {'core': [r'Translation\s+of\s+a\s+decree,?\s+issued\s+by\s+the\s+Emperor\s+of\s+the\s+French'], 'note': "Printed again, in the government's translation, with the documents sent to Congress with the President's message of 5 December."}),
                 (k('NOR', '12-24', 2), {'core': [r'Translation\s+of\s+a\s+decree,?\s+issued\s+by\s+the\s+Emperor\s+of\s+the\s+French'], 'note': "Printed again, in the government's translation, with the documents sent to Congress with the President's message of 5 December."})]),
 dict(id='vixen-fired-on-by-the-moselle-june-1810', kind='message_group',
      label="The brig Vixen fired on by the British brig Moselle near the Bahamas, 24 June 1810: a letter from a gentleman on board",
      definition="Printings of a letter from a gentleman on board the United States brig Vixen, Lieutenant Trippe, which the National Intelligencer published with its own account of the affair: 'On the 24th inst. [June] an occurrence took place, which was equally unpleasant and unexpected. The character of the affair however, corresponds with the treatment which we have so often received from the British naval commanders on former occasions. The Moselle, a 20 gun brig'; it tells how the Moselle fired at the Vixen near the Bahama bank, how her commander, Captain Boyce, answered that he 'was extremely sorry for having fired at us', and how the Vixen made sail. Eight papers print it after the Intelligencer's paragraph ('We are informed that on the 24th June, 1810, the United States brig Vixen ... was, in a wanton and unprovoked manner, fired into'); the Rhode-Island Republican prints the letter with remarks of its own. Counted by the letter, which every paper prints (X-1803-02). A report at second hand by a writer on board.",
      role='report', words=55, dateline=False,
      core=[r'(?:["“]\s*)?On\s+the\s+24th.{0,30}?an\s+occurrence\s+took\s+place', r'an\s+occurrence\s+took\s+place,?\s+which\s+was\s+equally\s+unpleasant'],
      first="A letter from on board the brig Vixen: the British brig Moselle fired on her near the Bahamas on 24 June 1810.",
      what='the letter from on board the Vixen',
      printings=[k('ALX', '07-25', 3), k('VA', '07-27', 3), k('ENQ', '07-27', 2), k('MAR', '07-27', 2), k('NOR', '07-27', 2),
                 k('RIA', '07-31', 2), k('RIR', '08-01', 2), k('CON', '08-06', 2), k('NHG', '08-07', 2)]),
 dict(id='gallatin-statement-on-erskine-despatch-1810', kind='document_group',
      label="The Secretary of the Treasury's statement on Mr. Erskine's despatch of 4 December 1808, published in July 1810",
      definition="Printings of Albert Gallatin's statement, signed by him and published in the National Intelligencer: 'Amongst the papers lately laid before the British Parliament, respecting American affairs, is a despatch from Mr. Erskine to Mr. Canning, dated 4th December, 1808, which principally relates to a conversation between Mr. Erskine and myself'; he says that the opinions the despatch ascribes to him were Mr. Erskine's own inference and that Mr. Erskine must have mistaken his meaning. Several papers print it after extracts of Mr. Erskine's despatches. The Secretary of the Treasury's own statement.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:A\s?MONGST|Amongst|AMONG|Among)\s+the\s+papers\s+lately\s+laid\s+before\s+the\s+British\s+Parliament'],
      first="The Secretary of the Treasury's statement that Mr. Erskine's despatch of 4 December 1808 mistakes his conversation.",
      what="Mr. Gallatin's statement",
      printings=[k('ALX', '07-21', 2), k('NOR', '07-23', 2), k('VA', '07-24', 3), k('ENQ', '07-24', 2), k('CON', '07-30', 2),
                 k('RIA', '07-31', 1), k('RIR', '08-15', 1)]),
 dict(id='brig-two-marias-seized-at-malaga-1810', kind='message_group',
      label="Boston, July 1810: the brig Enterprise from Algeziras brings an account of the seizure and sale of American vessels at Malaga in the name of the French government",
      definition="Printings of a Boston report: 'Last evening capt. Vinal, in the brig Enterprise, arrived here from Algeziras. He furnishes a detailed account of the seizure by a military force, and sale, without form or trial, but in the name of the French Imperial government, at Malaga, of the brig Two Marias' and other American vessels. The report names the masters of the seized vessels; the excerpts end before their names (C-12). A report at second hand, from the master of a vessel.",
      role='report', words=55, dateline=True, stop=r'(?<=Marias[,;.])\s|(?<=Marias)\s',
      core=[r'(?:V\s?ERY\s+L\s?ATE\s+FROM\s+S\s?PAIN\.?\s*)?(?:L\s?AST|Last|On\s+Friday)\s+[Ee]vening,?\s+[Cc]apt(?:ain|\.)?\s+\w+,?\s+in\s+the\s+brig\s+Enterpri[sz]e'],
      first="Boston, July 1810: the brig Enterprise from Algeziras reports American vessels seized and sold at Malaga in the name of the French government.",
      what='the Boston report from Algeziras',
      printings=[k('RIA', '07-31', 3), k('RIR', '08-01', 3), k('ALX', '08-03', 2), k('CON', '08-06', 3), k('NOR', '08-06', 3),
                 k('VA', '08-07', 2), k('ENQ', '08-07', 2)]),
 dict(id='cadore-letter-to-armstrong-5-august-1810', kind='document_group',
      label="The Duke of Cadore's letter to General Armstrong of 5 August 1810: 'the decrees of Berlin and Milan are revoked, and after the first of November they will cease to have effect'",
      definition="Printings of the letter of the French minister of foreign relations to General Armstrong, dated Paris, 5 August 1810: 'I have laid before his Majesty the Emperor and King, the Act of Congress of the 1st of May, extracted from the paper of the United States, which you had transmitted to me'; it declares that 'the decrees of Berlin and Milan are revoked, and that after the first of November they will cease to have effect; it being understood that, in consequence of this declaration, the English shall revoke their orders in council, and renounce the new principles of blockade, which they have wished to establish; or that the United States, conformably to the act you have just communicated, shall cause their rights to be respected by the English', and says 'His Majesty loves the Americans'. The Enquirer and the Norfolk Gazette print it again in December, in another translation, with the documents sent to Congress with the President's message. The French minister's own letter, in the translation of the New York papers.",
      role='published_document', words=60, dateline=False,
      head=r'(?:(?:PARIS,?\s+August\s+9\.?\s*)?Copy\s+of\s+a\s+letter\s+from\s+the\s+Minister\s+of\s+Foreign\s+Relations\s+to\s+Mr\.?\s+Armstrong\.?\s*)?(?:Paris,?\s+August\s+5(?:th)?,?\s+1810\.?\s*)?["“]?\s*(?:S\s?IR|Sir)\W*',
      core=[r'I\s+have\s+laid\s+before\s+his\s+[Mm]ajesty,?\s+the\s+[Ee]mperor\s+and\s+[Kk]ing,?\s+the\s+[Aa]ct\s+of\s+Congress'],
      first="The French minister's letter of 5 August 1810: the decrees of Berlin and Milan are revoked and will cease to have effect after 1 November.",
      what="the Duke of Cadore's letter of 5 August",
      printings=[k('RIA', '09-25', 3), k('ALX', '09-27', 2), (k('RIA', '09-28', 2), {'note': 'Printed again, three days later.'}),
                 k('ENQ', '09-28', 3), k('NOR', '09-28', 3), k('POR', '10-01', 2), k('CON', '10-01', 2), k('NHG', '10-02', 2),
                 k('VA', '10-02', 1), k('RIR', '10-03', 3),
                 (k('ENQ', '12-22', 1), {'note': "Printed again, in another translation, with the documents sent to Congress with the President's message of 5 December."}),
                 (k('NOR', '12-24', 2), {'note': "Printed again, in another translation, with the documents sent to Congress with the President's message of 5 December."})]),
 dict(id='pinkney-letter-with-wellesley-answer-on-the-decrees-1810', kind='document_group',
      label="Mr. Pinkney to the Secretary of State, September 1810, sending Lord Wellesley's answer on the revocation of the Berlin and Milan decrees, as the National Intelligencer published it on 20 October",
      definition="Printings of the American minister's letter from London: 'Lord Wellesley sent me, yesterday, his answer to my note of the 25th ult. respecting the Berlin and Milan Decrees. I hasten to transmit a copy of it. A copy shall be sent without delay to Gen. Armstrong', printed with its two enclosures, Mr. Pinkney's note of 25 August 1810 to Lord Wellesley, which informs him of the French minister's letter of 5 August, and Lord Wellesley's answer, which acknowledges that note: the British government will relinquish its system 'whenever the repeal of the French Decrees shall have actually taken effect, and the Commerce of neutral nations shall have been restored to the condition in which it stood previously to the promulgation of those decrees'. The covering letter and its enclosures, printed together, are counted as one item by the letter's opening (C-03). The two ministers' own letters.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:S\s?IR|Sir),?\s*[—-]*\s*Lord\s+Wellesl?e?y\s+sent\s+me,?\s+yesterday'],
      first="Mr. Pinkney sends Lord Wellesley's answer on the revocation of the French decrees.",
      what="Mr. Pinkney's letter with Lord Wellesley's answer",
      printings=[k('ALX', '10-22', 3), k('VA', '10-23', 3), k('ENQ', '10-23', 3), k('NOR', '10-24', 3), k('RIA', '10-26', 3),
                 k('MAR', '10-26', 2), k('POR', '10-29', 2), k('NHG', '10-30', 2), k('CON', '11-05', 1)]),
 dict(id='west-florida-september-december-1810', kind='context_group',
      label="West Florida, September to December 1810: the fort of Baton Rouge taken, the convention's declaration, a letter from the Mississippi Territory and the President's proclamation",
      children=['baton-rouge-fort-taken-natchez-report-september-1810', 'west-florida-declaration-26-september-1810',
                'letter-from-washington-mississippi-territory-30-october-1810', 'president-proclamation-on-west-florida-27-october-1810'],
      definition="Four texts on the Spanish province of West Florida, between the Mississippi and the Perdido, as the papers printed them from October to December 1810: a Natchez report of the taking of the Spanish fort of Baton Rouge, the declaration of the convention of West Florida of 26 September, a letter from Washington, Mississippi Territory, of 30 October, and the President's proclamation of 27 October directing that possession be taken of the territory as far as the Perdido. Contains those four groups."),
 dict(id='baton-rouge-fort-taken-natchez-report-september-1810', parent='west-florida-september-december-1810', kind='message_group',
      label="Natchez, 26 September 1810: 'about 150 men, under the command of General Thomas, entered the fort of Baton Rouge'",
      definition="Printings of a report from a Natchez paper of 26 September 1810: 'At a late hour last night we received the subjoined extract of a letter, viz.— \"Pinkneyville, September 25, 1810. We have information direct from Baton Rouge, that on Saturday night about 150 men, under the command of General Thomas, entered the fort of Baton Rouge\"'; the letter tells of the young officer who commanded the fort, wounded in the attack, and the Natchez paper's note before it says that the convention had heard it was betrayed. A report at second hand.",
      role='report', words=60, dateline=True,
      core=[r'(?:A\s?T|At)\s+a\s+late\s+hour\s+last\s+night,?\s+we\s+received\s+the\s+subjoined'],
      first="Natchez, 26 September 1810: a letter from Pinkneyville reports that about 150 men under General Thomas entered the fort of Baton Rouge.",
      what='the Natchez report from Baton Rouge',
      printings=[k('ALX', '10-23', 3), k('RIA', '10-26', 2), k('VA', '10-26', 3), k('ENQ', '10-26', 2), k('NOR', '10-26', 3),
                 k('POR', '10-29', 2), k('CON', '10-29', 2), k('MAR', '11-09', 2), k('RIR', '12-05', 2)]),
 dict(id='west-florida-declaration-26-september-1810', parent='west-florida-september-december-1810', kind='document_group',
      label="The declaration of the convention of West Florida, Baton Rouge, 26 September 1810",
      definition="Printings of the declaration that the representatives of the people of West Florida, in convention at Baton Rouge, signed on 26 September 1810: 'It is known to the world with how much fidelity the good people of this territory have professed and maintained allegiance to their legitimate sovereign while any hope remained of receiving from him protection for their property and lives'; it declares West Florida a free and independent state, and the representatives pledge themselves to support it with their lives and fortunes. Several papers print it again in December with other papers of the convention. A sub-story in 6 papers under a parent in 9 (C-01). The convention's own declaration.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:A\s+)?D\s?ECLARATION\.?\s*[—-]*\s*(?:I\s?T|It)\s+is\s+known\s+to\s+the\s+world\s+with\s+how\s+much\s+fidelity', r'(?:I\s?T|It)\s+is\s+known\s+to\s+the\s+world\s+with\s+how\s+much\s+fidelity'],
      first="The declaration of the convention of West Florida of 26 September 1810.",
      what='the declaration of the convention of West Florida',
      printings=[k('ALX', '10-30', 2), k('VA', '10-30', 2), k('ENQ', '10-30', 3), k('NOR', '10-31', 2), k('RIA', '11-02', 2),
                 k('NHG', '11-06', 2),
                 (k('ALX', '12-08', 2), {'note': 'Printed again, with other papers of the convention.'}),
                 (k('VA', '12-11', 2), {'note': 'Printed again, with other papers of the convention.'}),
                 (k('ENQ', '12-11', 1), {'note': 'Printed again, with other papers of the convention.'}),
                 (k('NOR', '12-12', 2), {'note': 'Printed again, with other papers of the convention.'})]),
 dict(id='letter-from-washington-mississippi-territory-30-october-1810', parent='west-florida-september-december-1810', kind='message_group',
      label="A letter from Washington, Mississippi Territory, 30 October 1810: 'The situation of Florida most certainly claims the earliest possible attention of our government'",
      definition="Printings of an extract of a letter 'from a gentleman of the first respectability at Washington, Mississippi Territory, to his friend in this city, bearing date October 30, 1810': 'The situation of Florida most certainly claims the earliest possible attention of our government, for, unless they are adopted into our family of governments, there is much room to fear that one of the great belligerents of Europe will attempt to lay violent hands on it'; it reports that men of the territory were crossing the line in expectation of military employment and that the convention would meet again at Baton Rouge. A private letter printed at second hand.",
      role='report', words=60, dateline=False,
      core=[r'(?:T\s?HE|The)\s+following\s+extract\s+of\s+a\s+letter\s+is\s+from\s+a\s+gentleman\s+of\s+the\s+first\s+respectability', r'(?:A\s+)?letter\s+from\s+a\s+gentleman\s+of\s+the\s+first\s+respectability\s+in\s+Washington', r'(?:T\s?HE|The)\s+situation\s+of\s+(?:the\s+)?Floridas?\s+most\s+certainly'],
      first="A letter from Washington, Mississippi Territory, of 30 October 1810: the situation of Florida claims the government's earliest attention.",
      what='the letter from the Mississippi Territory',
      printings=[k('VA', '11-30', 3), k('ENQ', '11-30', 3), k('ALX', '12-01', 3), k('NOR', '12-03', 2), k('RIR', '12-05', 2),
                 k('RIA', '12-07', 2), k('POR', '12-10', 2), k('CON', '12-10', 3), k('NHG', '12-11', 3)]),
 dict(id='president-proclamation-on-west-florida-27-october-1810', parent='west-florida-september-december-1810', kind='document_group',
      label="The President's proclamation of 27 October 1810 on the territory from the Mississippi to the Perdido",
      definition="Printings of the President's proclamation dated 27 October 1810: 'Whereas the territory south of the Mississippi territory and eastward of the river Mississippi, and extending to the river Perdido, of which possession was not delivered to the United States in pursuance of the treaty concluded at Paris on the 30th April, 1803, has at all times, as is well known, been considered and claimed by them as being within the colony of Louisiana conveyed by the said treaty'; it directs that possession be taken of the territory and that it be governed as part of the territory of Orleans. The papers printed it in December, after the President's message of 5 December. A sub-story in 6 papers under a parent in 9 (C-01). The President's own proclamation.",
      role='published_document', words=60, dateline=False,
      head=r'(?:A\s+P\s?ROCLAMATION\.?\s*)',
      core=[r'(?:W\s?HEREAS|Whereas)\s+the\s+territory\s+south\s+of\s+the\s+Mississippi\s+[Tt]erritory'],
      first="The President's proclamation of 27 October 1810: possession to be taken of the territory south of the Mississippi Territory as far as the Perdido.",
      what="the President's proclamation of 27 October",
      printings=[k('ALX', '12-07', 2), k('NOR', '12-10', 2), k('VA', '12-11', 1), k('ENQ', '12-11', 1), k('RIA', '12-14', 2),
                 k('RIR', '12-21', 2)]),
 dict(id='president-proclamation-of-2-november-1810-and-treasury-circular', kind='context_group',
      label="The President's proclamation of 2 November 1810 that the French edicts are revoked, and the Treasury's circular to the collectors",
      children=['president-proclamation-2-november-1810', 'treasury-circular-2-november-1810'],
      definition="The President's proclamation of 2 November 1810, under the fourth section of the act of 1 May, and the Secretary of the Treasury's circular of the same day to the collectors of the customs, which the papers printed together. Contains those two groups."),
 dict(id='president-proclamation-2-november-1810', parent='president-proclamation-of-2-november-1810-and-treasury-circular', kind='document_group',
      label="The President's proclamation of 2 November 1810: 'the edicts of France violating the neutral commerce of the United States have been so revoked as to cease to have effect on the first of the present month'",
      definition="Printings of the President's proclamation dated 2 November 1810: 'Whereas by the fourth section of the act of Congress, passed on the first day of May, 1810, entitled \"An act concerning the commercial intercourse between the United States and Great Britain and France and their dependencies, and for other purposes,\" it is provided'; 'And whereas it has been officially made known to this government that the edicts of France violating the neutral commerce of the United States have been so revoked as to cease to have effect on the first of the present month', the President proclaims it, so that the restrictions of the non-intercourse act will be revived against Great Britain after three months unless she revokes or modifies her edicts in like manner. The President's own proclamation.",
      role='published_document', words=60, dateline=False,
      head=r'(?:A\s+P\s?ROCLAMATION\.?\s*)',
      core=[r'(?:W\s?HEREAS|Whereas),?\s+by\s+the\s+(?:fourth|4th)\s+section\s+of\s+(?:the|an)\s+act'],
      first="The President's proclamation of 2 November 1810: the French edicts are revoked as of 1 November.",
      what="the President's proclamation of 2 November",
      printings=[k('ALX', '11-03', 3), k('NOR', '11-05', 2), k('VA', '11-06', 3), k('ENQ', '11-06', 2), k('RIA', '11-09', 2),
                 k('MAR', '11-09', 2), k('POR', '11-12', 2), k('CON', '11-12', 3), k('NHG', '11-13', 3), k('RIR', '11-14', 3)]),
 dict(id='treasury-circular-2-november-1810', parent='president-proclamation-of-2-november-1810-and-treasury-circular', kind='document_group',
      label="The Secretary of the Treasury's circular to the collectors of the customs, 2 November 1810",
      definition="Printings of Albert Gallatin's circular letter of 2 November 1810 to the collectors of the customs: 'You will herewith receive a copy of the Proclamation of the President of the United States, announcing the revocation of the edicts of France which violated the neutral commerce of the United States'; it explains that French armed vessels may now enter American waters, and that unless the collectors are notified before 2 February 1811 that Great Britain has revoked or modified her edicts, they are from that day to enforce the restrictions against British vessels and goods. The Secretary of the Treasury's own instructions.",
      role='published_document', words=60, dateline=False,
      head=r'(?:\(?C\s?IRCULAR\.?\)?\s*)?(?:T\s?REASURY\s+D\s?EPARTMENT,?\s+(?:N\s?OVEMBER|November|Nov\.?)\s+2d?,?\s+1810\.?\s*)?(?:S\s?IR|Sir)\W*',
      core=[r'(?:Y\s?OU|You)\s+will\s+herewith\s+receive\s+a\s+copy\s+of\s+the\s+[Pp]roclamation'],
      first="The Secretary of the Treasury's circular of 2 November 1810 to the collectors: what the proclamation means for French and British vessels.",
      what="the Treasury's circular of 2 November",
      printings=[k('ALX', '11-03', 3), k('NOR', '11-05', 2), k('VA', '11-06', 3), k('ENQ', '11-06', 2), k('RIA', '11-09', 2),
                 k('MAR', '11-09', 2), k('CON', '11-12', 3), k('NHG', '11-13', 3), k('RIR', '11-14', 3)]),
 dict(id='tunis-bey-and-american-consul-malta-august-1810', kind='message_group',
      label="Malta, 24 August 1810: 'A very unpleasant business has taken place between the Bey of Tunis and our Consul'",
      definition="Printings of a letter from Malta of 24 August 1810, headed 'Bad news from Tunis' in several papers: 'A very unpleasant business has taken place between the Bey of Tunis and our Consul. It seems an American ship was captured by a French privateer, and carried into Tunis, where she was purchased by a minister of the Bey'; it tells that the ship's former supercargo appealed at Malta to have her stopped, and that the Bey, hearing of it, confiscated the American property in Tunis. A report at second hand.",
      role='report', words=55, dateline=False,
      head=r'(?:(?:Bad\s+[Nn]ews\s+from\s+Tunis\.?\s*)?["“]?\s*MALTA,?\s+A\s?UG(?:UST|\.)?\s+24,?\s+1810\.?\s*)',
      core=[r'(?:A\s+)?very\s+unpleasant\s+business\s+has\s+taken\s+place\s+between\s+the\s+B[ae]y\s+of\s+Tunis'],
      first="Malta, 24 August 1810: a dispute between the Bey of Tunis and the American consul over a captured American ship.",
      what='the letter from Malta on Tunis',
      printings=[k('POR', '11-19', 2), k('CON', '11-19', 2), k('NHG', '11-20', 2), k('ALX', '11-21', 3), k('ENQ', '11-23', 3),
                 k('NOR', '11-23', 2), k('VA', '11-27', 2), k('RIR', '11-28', 3)]),
 dict(id='lucien-bonaparte-address-to-the-roman-citizens-1810', kind='document_group',
      label="Lucien Bonaparte's address to the citizens of Rome, 1810, as the papers printed it in November",
      definition="Printings of an address that Lucien Bonaparte, the Emperor's brother, is said to have had distributed at Rome after he sailed in 1810 and that, the papers say, was suppressed by an official order: 'To the Roman Citizens. In the bosom of retirement, occupied with no other cares than those of my family'; he says that he had no choice between unconditional submission and immediate flight. Lucien Bonaparte's own words, as the London papers gave them.",
      role='published_document', words=55, dateline=False,
      head=r'(?:To\s+the\s+Roman\s+Citizens\.?\s*["“]?\s*)',
      core=[r'(?:I\s?N|In)\s+the\s+bosom\s+of\s+retirement'],
      first="Lucien Bonaparte's address to the citizens of Rome: he had no choice between submission and flight.",
      what="Lucien Bonaparte's address",
      printings=[k('RIA', '11-23', 2), k('ALX', '11-24', 2), k('NOR', '11-26', 2), k('VA', '11-27', 3), k('ENQ', '11-27', 1),
                 k('MAR', '11-30', 3), k('POR', '12-03', 2), k('CON', '12-03', 2)]),
 dict(id='president-annual-message-5-december-1810', kind='document_group',
      label="The President's message to Congress, 5 December 1810",
      definition="Printings of the President's message at the opening of the third session of the Eleventh Congress, communicated on 5 December 1810: 'The embarrassments which have prevailed in our foreign relations, and so much employed the deliberations of Congress, make it a primary duty, in meeting you, to communicate whatever may have occurred in that branch of our national affairs'; it reports the revocation of the French decrees and the proclamation of 2 November, the occupancy of the territory west of the Perdido, the state of the revenue, and recommends a national seminary of learning in the District of Columbia. The President's own message.",
      role='published_document', words=60, dateline=False,
      head=r'(?:Fellow[\s-]*[Cc](?:iti[sz]ens|ITIZENS)\s+of\s+the\s+Senate,?\s+and\s+(?:of\s+the\s+)?House\s+of\s+Representatives[,.:]?\s*)',
      core=[r'(?:T\s?HE|The|the)\s+embarrassments\s+which\s+have\s+prevailed\s+in\s+our\s+foreign\s+relations'],
      first="The President's message to Congress of 5 December 1810.",
      what="the President's message of 5 December",
      printings=[k('ALX', '12-06', 3), k('VA', '12-07', 5), k('ENQ', '12-08', 2), k('NOR', '12-10', 2), k('RIA', '12-11', 2),
                 k('NHG', '12-11', 2), k('RIR', '12-12', 2), k('POR', '12-17', 2), k('CON', '12-17', 1)]),
 dict(id='treasury-report-december-1810', kind='document_group',
      label="The Secretary of the Treasury's report and estimates, December 1810",
      definition="Printings of the report that the Secretary of the Treasury, Albert Gallatin, sent to the House of Representatives in December 1810: 'In obedience to the directions of the act supplementary to the act entitled \"An act to establish the Treasury Department,\" the Secretary of the Treasury respectfully submits the following Report and Estimates'; it gives the revenue of 1808 and 1809, the receipts of the year and the estimates for 1811, and considers the provisions needed if the non-intercourse is revived against Great Britain. The Secretary of the Treasury's own report.",
      role='published_document', words=60, dateline=False,
      head=r'(?:R\s?EPORT\.?\s*)',
      core=[r'(?:I\s?N|In)\s+obedience\s+to\s+the\s+directions\s+of\s+the\s+act\s+supplementary'],
      first="The Secretary of the Treasury's report and estimates of December 1810.",
      what="the Treasury's report of December",
      printings=[k('VA', '12-18', 2), k('ENQ', '12-18', 2), k('NOR', '12-19', 3), k('ALX', '12-20', 2), k('RIA', '12-21', 2),
                 k('RIR', '12-26', 2), k('CON', '12-31', 1)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797 and 1800): "BOSTON, Nov. 30th, 1802."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False, head=None):
    for core in cores:
        m = re.search(core, text, re.I | re.S)
        if m:
            start = m.start()
            if head:   # a heading that ends directly before the core: the excerpt starts with it
                window = text[max(0, start-260):start]
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
            problems.append((s['id'], key, 'page not in the 1810 pages'))
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
        r['id'] = f'S10-{n:03}'
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
               'admission_rule': 'Reviewed 1810 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1810/'
    return {
        'ledger_id': 'ledger:stories-1810', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1810', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1810, and of 1809 where they reach the 1810 pages (long-running ones '
                   'included), a sweep of word-for-word passages shared by 7 or more papers for short items the families miss, phrase searches on '
                   'all 3,933 pages of 1810 in both transcriptions, reading of every hit, and scan checks of each admitted passage, by the one '
                   'admission rule (9 or more papers admitted, 7 or 8 chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1809.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1810.py': 'ledger_code', 'work/archive_data/ledgers/stories_1810_review.json': 'scan_review',
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
