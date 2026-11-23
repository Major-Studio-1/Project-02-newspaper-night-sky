"""Write ledgers/stories_1803.json: reviewed stories of 1803, round one.

1803 is read by the one admission rule the other reviewed years follow (outputs/story_discovery_1809/README.md, "Selection
rule"; docs/rules-and-exceptions.md, R-01): every single printed item in 9 or more newspapers is admitted, except digests;
items in 7 or 8 papers are chosen to cover the months and the kinds of news; items are counted one by one; a sub-story may
have fewer papers when its parent reaches 7. The automatic families first printed in 1803 that reach 3 or more papers,
long-running ones included, were split into single printed items with work/story_items.py --long-running (items.json), and
again with year 1802 over the 1803 pages (items_from_1802.json); every item in 7 or more papers, and every item in 5 or 6
that a deeper comparison put in more papers, was counted again by its own words, and a sweep of word-for-word passages
shared by 7 or more papers found short items the families miss. Every chosen item and every candidate set aside was
counted with phrase searches over all 3,250 pages of 1803 in both transcriptions (work/story_phrase_search.py). See
outputs/story_discovery_1803/README.md.

The 1803 pages are those whose issue the data release dates to 1803 (work/year_search_pages.py 1803 ... --printed-dates);
no 1803 issue has a corrected date. 1803 has 17 catalogue series, which are 12 papers (C-04): the Alexandria Advertiser
(sn84024011 to 16 September, then sn84024012, the Alexandria Daily Advertiser), the Kentucky Gazette (sn82014782 on 4 and
11 January, then sn84038147), the Portsmouth Oracle (sn83025545 to 15 October, then sn84023351, the Oracle Post, its
country edition, which continues its volume numbering) and Jenks' Portland Gazette (sn83016072 to 4 July, sn83021505 from
11 July, sn83016081 from 31 October). k() below picks the catalogue number from the date.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-70 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1803_review.json after the
scan check. Eleven 1803 pages have their RevX transcriptions filed off from the scans (derived/revx_page_map.parquet); a
printing on such a page takes its excerpt from the CA transcription of its scan page (none of the printings here stands on
one).

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened. The report of gold found in North Carolina names the landowner;
its excerpts end before his name (C-12).

The base and target releases are set when the ledger is applied (a review of 1802 runs at the same time and may take the
next number first):
    python work/archive_data/ledgers/make_stories_1803.py [--table] [--base 0.11.10 --target 0.11.11]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1803/search_pages.json). The excerpts are cut from
the 1803 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1803'
D = PROJECT/'outputs/story_discovery_1803'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1803_review.json'
OUT = HERE/'stories_1803.json'
BASE, TARGET = '0.11.10', '0.11.11'   # defaults; see the docstring
DATA_RELEASE = '0.11.10'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-23'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn84024011': 'The Alexandria Advertiser', 'sn84024012': 'The Alexandria Daily Advertiser',
         'sn83045242': 'The National Intelligencer', 'sn83025588': 'The New Hampshire Gazette',
         'sn84038147': 'The Kentucky Gazette', 'sn82014782': 'The Kentucky Gazette', 'sn84023379': 'The Republican Ledger',
         'sn85059525': 'The Berkeley and Jefferson Intelligencer', 'sn83021188': 'The Rhode-Island Republican',
         'sn83025545': 'The United States Oracle', 'sn84023351': 'The Oracle Post', 'sn84024679': 'The Recorder',
         'sn83016072': "Jenks' Portland Gazette", 'sn83021505': "Jenks' Portland Gazette", 'sn83016081': "Jenks' Portland Gazette",
         'sn90062293': 'The American Republican Gazette', 'sn84024710': 'The Virginia Argus'}
ONE = {'NI': 'sn83045242', 'NHG': 'sn83025588', 'RL': 'sn84023379', 'BJ': 'sn85059525', 'RIR': 'sn83021188',
       'REC': 'sn84024679', 'ARG': 'sn90062293', 'VA': 'sn84024710'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1803), page and edition. Four papers have more than one
    catalogue number in 1803 (C-04); the date picks it."""
    if paper == 'ALX':
        lccn = 'sn84024011' if date < '09-17' else 'sn84024012'
    elif paper == 'KG':
        lccn = 'sn82014782' if date < '01-15' else 'sn84038147'
    elif paper == 'ORA':
        lccn = 'sn83025545' if date < '10-20' else 'sn84023351'
    elif paper == 'POR':
        lccn = 'sn83016072' if date < '07-08' else ('sn83021505' if date < '10-28' else 'sn83016081')
    else:
        lccn = ONE[paper]
    return f'{lccn}|{YEAR}-{date}|{ed}|{page}'


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
 dict(id='deposit-at-new-orleans-before-congress-1802-1803', kind='context_group',
      label='The right of deposit at New Orleans withdrawn, before Congress: the President\'s message of 22 December 1802 and the resolutions of the two houses, January and February 1803',
      children=['president-message-22-december-1802-on-the-deposit-at-new-orleans', 'house-resolution-7-january-1803-on-the-mississippi',
                'senate-resolutions-for-80000-militia-february-1803'],
      definition="Three documents of Congress on the suspension of the right of deposit at New Orleans by the Spanish Intendant there in October 1802, as the papers of 1803 printed them: the President's message of 22 December 1802 sending the Secretary of State's report, the House of Representatives' resolution of 7 January 1803, and the resolutions the Senate adopted in February 1803 on Mr. Breckenridge's motion. Contains those three groups."),
 dict(id='president-message-22-december-1802-on-the-deposit-at-new-orleans', parent='deposit-at-new-orleans-before-congress-1802-1803', kind='document_group',
      label="The President's message of 22 December 1802 sending the Secretary of State's report on the violation of the treaty with Spain at New Orleans",
      definition="Printings of the President's message to the House of Representatives of 22 December 1802: 'I now transmit a report from the Secretary of State, with the information requested in your resolution of the 17th instant. In making this communication, I deem it proper to observe, that I was led by the regard due to the rights and interests of the United States, and to the just sensibility of the portion of our fellow-citizens more immediately affected by the irregular proceeding at New Orleans, to lose not a moment in causing every step to be taken which the occasion claimed from me'. Several papers head it as transmitting the information requested 'relative to the violation on the part of Spain, of the twenty-second article of the Treaty of Friendship, Limits and Navigation', and print the Secretary of State's report with it; others give it in the House's proceedings of 22 December. The National Intelligencer and the Alexandria Advertiser printed it in December 1802; this group holds the printings of 1803 (C-11). The President's own message.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:["“]\s*)?Gentlemen\s+of\s+the\s+[Hh]ouse\s+of\s+Representatives[,.]?\s*["”]?\s*,?\s*["“]?\s*I\s+(?:NOW|now)\s+transmit\s+a\s+report',
            r'I\s+(?:NOW|now)\s+transmit\s+a\s+report\s+(?:from|of)\s+the\s+Secretary\s+of\s+State'],
      first="The President's message of 22 December 1802 sends the House the Secretary of State's report on the suspension of the right of deposit at New Orleans.",
      what="the President's message of 22 December 1802",
      printings=[k('ALX', '01-06', 2),
                 k('BJ', '01-07', 2),
                 k('RIR', '01-08', 2),
                 k('ORA', '01-08', 4),
                 k('POR', '01-10', 3),
                 k('KG', '01-11', 2),
                 k('NHG', '01-11', 1),
                 k('ARG', '01-13', 2),
                 k('RL', '01-18', 2)]),
 dict(id='house-resolution-7-january-1803-on-the-mississippi', parent='deposit-at-new-orleans-before-congress-1802-1803', kind='document_group',
      label="The House of Representatives' resolution of 7 January 1803 on the navigation of the Mississippi",
      definition="Printings of the resolution that the House of Representatives agreed to with closed doors on 7 January 1803, on a motion Mr. Randolph had made on the 5th: 'Resolved, That this House receive with great sensibility the information of a disposition in certain officers of the Spanish government at New Orleans to obstruct the navigation of the river Mississippi, as secured to the United States by the most solemn stipulations'; 'willing, at the same time, to ascribe this breach of compact to the unauthorized misconduct of certain individuals, rather than to a want of good faith on the part of his Catholic Majesty', the House will wait the issue of the executive's measures, and declares 'their unalterable determination to maintain the boundaries, and the rights of navigation and commerce through the river Mississippi, as established by existing treaties'. Printed in the papers' reports of the House's proceedings. Pages that quote it later in essays and reviews of the session are not counted (C-07). The House's own resolution.",
      role='published_document', words=60, dateline=False,
      core=[r'R\s?ESOLVED,?\s+(?:T|t)hat\s+this\s+House\s+receive\s+with\s+great\s+sensi\w+', r'receive\s+with\s+great\s+sensi\w+\s+the\s+information\s+of\s+a\s+disposition'],
      first="The House of Representatives' resolution of 7 January 1803: it will wait the issue of the executive's measures on the obstruction of the Mississippi at New Orleans.",
      what="the House's resolution of 7 January",
      printings=[k('NI', '01-10', 3),
                 k('ALX', '01-11', 3),
                 k('ORA', '01-22', 2),
                 k('RIR', '01-22', 2),
                 k('POR', '01-24', 2),
                 k('NHG', '01-25', 2),
                 k('KG', '02-01', 3),
                 k('RL', '02-08', 2)]),
 dict(id='senate-resolutions-for-80000-militia-february-1803', parent='deposit-at-new-orleans-before-congress-1802-1803', kind='document_group',
      label="The Senate's resolutions of February 1803, on Mr. Breckenridge's motion: 80,000 militia to be held in readiness",
      definition="Printings of the resolutions that Mr. Breckenridge moved in the Senate in February 1803, 'striking out from the word Resolved' in Mr. Ross's resolutions on the navigation of the Mississippi, and that the Senate adopted (by 25 votes, the National Intelligencer reports): 'That the President of the United States be, and he is hereby authorized, whenever he shall judge it expedient, to require of the executives of the several states to take effectual measures to organize, and equip, according to law, and hold in readiness to march at a moment's warning, 80,000 effective militia, officers included' (the Oracle, the Republican Ledger and Jenks' Portland Gazette print 'organize, arm and equip', and the Portland Gazette 'including officers'), that volunteer corps may be accepted as part of the detachment, and that sums be appropriated for the troops and for arsenals on the western waters. Most papers print them after Mr. Ross's resolutions, which would have authorized the President to take possession of places on the island of New Orleans and to call 50,000 militia into service (7 papers; not admitted on their own, see the README). The National Intelligencer printed them as moved on 25 February and as adopted on the 28th. The Senate's resolutions, as the papers reported its proceedings.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:T|t)hat\s+the\s+[Pp]resident\s+of\s+the\s+(?:United\s+States|U\.\s?States)\s+be,?\s+and\s+he\s+is\s+hereby\s+authori[sz]ed,?\s+whenever\s+he\s+shall\s+judge\s+it\s+expedient,?\s+to\s+require\s+of\s+the\s+[Ee]xecutives\s+of\s+the\s+(?:several|federal)'],
      first="The Senate's resolutions of February 1803: the President may require the states to hold 80,000 militia ready to march.",
      what="the Senate's resolutions on 80,000 militia",
      printings=[k('NI', '02-25', 2),
                 (k('NI', '02-28', 3), {'note': 'Printed again with the vote by which the Senate adopted the resolutions.'}),
                 k('ALX', '02-26', 3),
                 k('BJ', '03-04', 2),
                 k('POR', '03-07', 3),
                 (k('ORA', '03-12', 3), {'field': CA, 'core': [r'R\w{2,6},?\s+That\s+the\s+Pre\w*\s+of\s+the\s+U\.\s?States\s+be,?\s+and\s+he\s+is\s+hereby\s+authori[sz]ed'],
                                         'note': 'RevX lacks the resolutions on this page; the older CA transcription has them, so the excerpt comes from the CA text.'}),
                 k('RL', '03-15', 2),
                 k('KG', '03-15', 2),
                 k('ARG', '03-17', 2)]),
 dict(id='spanish-and-french-ministers-on-the-deposit-1803', kind='context_group',
      label="The Spanish and French ministers on the deposit at New Orleans, March and April 1803",
      children=['yrujo-letter-to-the-secretary-of-state-10-march-1803', 'pichon-letter-to-the-governor-of-louisiana-11-march-1803',
                'yrujo-letter-on-the-deposit-restored-19-april-1803'],
      definition="Three letters on the Intendant's suspension of the right of deposit at New Orleans, by the Spanish minister to the United States, the Marquis de Casa Yrujo, and by the chargé d'affaires of the French Republic, Mr. Pichon, as the National Intelligencer published them in March and April 1803. Contains those three groups."),
 dict(id='yrujo-letter-to-the-secretary-of-state-10-march-1803', parent='spanish-and-french-ministers-on-the-deposit-1803', kind='document_group',
      label="The Marquis de Casa Yrujo's letter to the Secretary of State, 10 March 1803: the Intendant's proclamation 'an act purely personal'",
      definition="Printings of the translation, published by the National Intelligencer as official, of the Spanish minister's letter to the Secretary of State of 10 March 1803: 'When you represented to me towards the end of November last, that the port of New Orleans had been shut against the citizens of the United States, without the assignment of any equivalent place of deposit for their merchandise on the Banks of the Mississippi'; 'I have now the satisfaction of informing you that my first opinion has been verified, and of declaring in the most positive terms, that the proclamation of the Intendant is an act purely personal, without the sanction and even without the knowledge of his Catholic Majesty'. The National Intelligencer printed it again on 30 March ('We, therefore, re-insert it'). The Spanish minister's own letter.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:S\s?IR|Sir),?\s*[—-]*\s*(?:W\s?HEN|When)\s+you\s+(?:re)?presented\s+to\s+me', r'(?:W\s?HEN|When)\s+you\s+(?:re)?presented\s+to\s+me,?\s+towards\s+the\s+end'],
      first="The Spanish minister's letter of 10 March 1803 declares the Intendant's proclamation at New Orleans an act without the sanction of his King.",
      what="the Spanish minister's letter of 10 March",
      printings=[k('NI', '03-14', 3),
                 k('ALX', '03-15', 3),
                 k('BJ', '03-18', 3),
                 k('RIR', '03-26', 3),
                 k('NHG', '03-29', 2),
                 k('RL', '03-29', 2),
                 k('KG', '03-29', 3),
                 (k('NI', '03-30', 2), {'note': "Printed again in an editorial: 'We, therefore, re-insert it as a full answer'."}),
                 k('ARG', '03-31', 2),
                 k('ORA', '04-02', 2)]),
 dict(id='pichon-letter-to-the-governor-of-louisiana-11-march-1803', parent='spanish-and-french-ministers-on-the-deposit-1803', kind='document_group',
      label="Mr. Pichon's letter to the Governor of Louisiana, 11 March 1803",
      definition="Printings of the letter of the chargé d'affaires of the French Republic to the Spanish governor of Louisiana, dated at Georgetown on 11 March 1803 and communicated to the Secretary of State: 'The Marquis d'Yrujo has communicated to me the contents of the dispatches, which he has just received from your Excellency, and from the Intendant of his Catholic Majesty in the province under your command, in answer to those which he wrote to you in relation to the late suspension of the right of deposit conceded to the United States at New Orleans'; it begs the governor, 'in the name of the French government, whose interests are implicated in this case', to consider the consequences if the Intendant should persist. The French chargé d'affaires' own letter.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:Letter\s+from\s+)?M\s?r\.?\s+P\s?(?:ICHON|ichon),?\s+[Cc]harg', r'(?:S\s?IR|Sir),?\s*[—-]*\s*(?:T\s?HE|The)\s+Marquis\s+d\W*\s?Yrujo\s+has\s+communicated',
            r'(?:T\s?HE|The)\s+Marquis\s+d\W*\s?Yrujo\s+has\s+communicated'],
      first="The French chargé d'affaires' letter of 11 March 1803 asks the Governor of Louisiana to prevent the consequences of the Intendant's measures.",
      what="Mr. Pichon's letter",
      printings=[k('NI', '03-16', 3),
                 k('ALX', '03-17', 3),
                 k('BJ', '03-25', 2),
                 k('NHG', '03-29', 2),
                 k('RIR', '04-02', 3),
                 k('ORA', '04-02', 1),
                 k('POR', '04-04', 2),
                 k('RL', '04-05', 2),
                 k('KG', '04-05', 4)]),
 dict(id='yrujo-letter-on-the-deposit-restored-19-april-1803', parent='spanish-and-french-ministers-on-the-deposit-1803', kind='document_group',
      label="The Marquis de Casa Yrujo's letter to the Secretary of State, 19 April 1803: the deposit to continue at New Orleans",
      definition="Printings of the Spanish minister's letter to the Secretary of State of 19 April 1803, which the National Intelligencer published as an important letter 'sent by Express to New-Orleans': 'I have the pleasure to impart to you, without a moment's delay, that by dispatches which I have just received from my government, brought by a Brig of war of the King my master, dispatched for this purpose alone, I see confirmed all the assurances which I gave you'; his Catholic Majesty 'has provided that the deposit should continue at New-Orleans until the two governments shall come to an agreement about another equivalent place', and the orders to the Intendant and the Captain-General of Louisiana are enclosed for forwarding. The Spanish minister's own letter.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:S\s?IR|Sir),?\s+I\s+(?:HAVE|have)\s+the\s+pleasure\s+to\s+impart', r'I\s+(?:HAVE|have)\s+the\s+pleasure\s+to\s+impart\s+to\s+you'],
      first="The Spanish minister's letter of 19 April 1803: his King has provided that the deposit continue at New Orleans.",
      what="the Spanish minister's letter of 19 April",
      printings=[k('NI', '04-20', 3),
                 k('ALX', '04-20', 3),
                 k('REC', '04-27', 2),
                 k('BJ', '04-29', 3),
                 k('RIR', '04-30', 3),
                 k('ORA', '04-30', 2),
                 k('POR', '05-02', 2),
                 k('NHG', '05-03', 2),
                 k('RL', '05-03', 3),
                 k('KG', '05-10', 3)]),
 dict(id='samuel-adams-and-thomas-paine-letters-1802-1803', kind='document_group',
      label="Samuel Adams's letter to Thomas Paine of 30 November 1802, and Paine's answer, as Paine published them",
      definition="Printings of the two letters that Thomas Paine sent to the National Intelligencer in January 1803 ('I therefore send you the original letter of Mr. Adams and my own copy of the answer'): Samuel Adams's letter from Boston of 30 November 1802, 'I have frequently with pleasure reflected on your services to my native, and your adopted country. Your Common Sense, and your Crisis unquestionably awakened the public mind, and led the people loudly to call for a declaration of our national independence ... But when I heard, that you had turned your mind to a defence of infidelity, I felt myself much astonished', and Paine's answer, 'To Samuel Adams. My dear and venerable friend'. Each writer's own letter, in a public dispute over religion and politics.",
      role='published_document', words=60, dateline=True,
      core=[r'(?:S\s?IR|Sir),?\s+I\s+(?:HAVE|have)\s+frequently\s+with\s+pleasure\s+reflected', r'I\s+(?:HAVE|have)\s+frequently\s+with\s+pleasure\s+reflected'],
      first="Samuel Adams's letter to Thomas Paine of 30 November 1802, with Paine's answer.",
      what="the letters of Samuel Adams and Thomas Paine",
      printings=[k('NI', '01-26', 1),
                 k('RIR', '02-12', 2),
                 k('POR', '02-14', 1),
                 k('NHG', '02-15', 1),
                 k('RL', '02-15', 2),
                 k('KG', '02-22', 2),
                 k('ARG', '04-07', 1)]),
 dict(id='despard-speech-on-the-scaffold-21-february-1803', kind='message_group',
      label="Colonel Despard's speech on the scaffold, London, 21 February 1803, as the papers reported his execution for high treason",
      definition="Printings of the speech that Colonel Edward Marcus Despard, convicted with six others of high treason for a conspiracy against the King and the government, made to the crowd before his execution in London on 21 February 1803: 'Fellow citizens, I come here, as you see, after having served my country faithfully, honorably and usefully for thirty years and upwards, to suffer death upon a scaffold for a crime of which I protest I am not guilty'. The papers print it within three different London accounts of the execution; the speech, printed in nearly the same words, is counted as the item, and accounts that do not print it (the Alexandria Advertiser, the Kentucky Gazette) are not counted. The National Intelligencer printed it on 8 and 13 April, in two of the accounts. A condemned man's own words, as the London papers reported them.",
      role='report', words=60, dateline=False,
      core=[r'(?:["“]\s*)?Fellow[\s-]*[Cc]itizens\W+I\s+come\s+here,?\s+as\s+you\s+see', r'I\s+come\s+here,?\s+as\s+you\s+see,?\s+after\s+having\s+served'],
      first="Colonel Despard's speech on the scaffold, London, 21 February 1803.",
      what="Colonel Despard's speech",
      printings=[k('NI', '04-08', 3),
                 k('RL', '04-12', 2),
                 (k('NI', '04-13', 1), {'note': 'Printed again in another London account of the execution.'}),
                 k('BJ', '04-15', 2),
                 k('RIR', '04-16', 3),
                 k('ORA', '04-16', 2),
                 k('REC', '04-16', 4),
                 k('POR', '04-18', 1),
                 k('ARG', '04-28', 2)]),
 dict(id='gascoigne-letter-war-expected-march-1803', kind='message_group',
      label="New York, April 1803: the ship Mercury brings Mr. Gascoigne's letter of 8 March from London, 'War is expected'",
      definition="Printings of a letter from Mr. Gascoigne, Member of Parliament for Liverpool, to the Mayor of Liverpool, dated London, 8 March 1803, which the ship Mercury, Captain Sterling, brought to New York in 31 days from Liverpool: 'War is expected—a message this day from the King to the House to that tendency—Militia expected to be called out to guard against invasion—Stocks down four per cent.—Mr. Pitt, it is supposed, will return soon to power'. The papers print it within two different New York reports of the Mercury's arrival (one from the New-York Gazette, 'Strong probability of a renewal of the War between Great-Britain and France', the other headed 'Symptoms of war in Europe'), and the New Hampshire Gazette within a third; the letter, which all of them print, is counted as the item. A Member of Parliament's letter, printed at second hand.",
      role='report', words=50, dateline=False,
      core=[r'(?:The\s+following\s+is\s+a\s+)?[Cc]opy\s+of\s+a\s+[Ll]etter\s+from\s+(?:Mr\.?\s+|J\.\s+)?G\w+', r'(?:D\s?EAR|Dear)\s+(?:S\s?IR|Sir)\W+(?:W\s?AR|War)\s+is\s+expected'],
      first="A letter from London of 8 March 1803, brought to New York by the ship Mercury: 'War is expected'.",
      what="Mr. Gascoigne's letter",
      printings=[k('ALX', '04-18', 3),
                 k('NI', '04-20', 3),
                 k('BJ', '04-22', 2),
                 k('RIR', '04-23', 3),
                 k('ORA', '04-23', 2),
                 k('REC', '04-23', 2),
                 k('POR', '04-25', 3),
                 (k('NHG', '04-26', 3), {'note': "The New Hampshire Gazette prints the letter within its own New York report of the Mercury's arrival, from 'Isaac Galscoyne, Esq.'"}),
                 k('RL', '04-26', 2),
                 k('KG', '05-10', 3)]),
 dict(id='laussat-proclamation-to-the-louisianians-1803', kind='document_group',
      label="Proclamation of Laussat, French colonial prefect, to the Louisianians, 1803",
      definition="Printings of a translation of the proclamation that Laussat, the colonial prefect sent by the French Republic to take over Louisiana from Spain, addressed to its inhabitants in 1803: 'Your separation from France marks one of the most shameful epochs of her annals, under an enfeebled and corrupt government, after an ignominious war, and a disgraceful peace'; it praises the First Consul and announces the mission of 'your captain general Victor, your colonial prefect and your chief judge'. The French prefect's own proclamation, in translation.",
      role='published_document', words=60, dateline=False,
      core=[r'P\s?ROCLAMATION\.?\s+(?:I\s?N|In)\s+(?:THE|the)\s+(?:NAME|name)\s+(?:OF|of)\s+(?:THE|the)\s+(?:FRENCH|French)\s+(?:REPUBLIC|Republic)',
            r"(?:L\W?\s?)?A\s?ussat,?\s+[Cc](?:OLONIAL|olonial)\s+[Pp](?:REFECT|refect)", r'(?:Y\s?OUR|Your|T\s?HE|The)\s+separation\s+from\s+France\s+(?:marks|forms)'],
      first="The French colonial prefect's proclamation to the inhabitants of Louisiana, 1803.",
      what="Laussat's proclamation",
      printings=[k('ALX', '05-05', 3),
                 k('NI', '05-06', 3),
                 k('KG', '05-10', 3),
                 k('REC', '05-11', 2),
                 k('BJ', '05-13', 3),
                 k('ORA', '05-14', 1),
                 k('POR', '05-16', 2)]),
 dict(id='louisiana-expedition-suspended-rotterdam-april-1803', kind='message_group',
      label="Rotterdam, April 1803: 'By an express order from the First Consul, the Louisiana expedition is definitively suspended'",
      definition="Printings of a paragraph of news from Rotterdam of April 1803, in runs of European news (dated 12 April in four papers and 8 April, under the heading 'Expedition to Louisiana', in three): 'By an express order from the First Consul, the Louisiana expedition is definitively suspended. The French General began the day before yesterday to debark the troops that were on board the vessels; they will proceed, with the other troops newly arrived in this Republic, to different destinations both on the frontiers and elsewhere'. The Kentucky Gazette gives it in shorter words ('By an express order of Bonaparte, the Louisiana expedition is suspended, and the troops are debarked'), counted with the others. A report at second hand.",
      role='report', words=50, dateline=True,
      core=[r'By\s+an\s+express\s+order\s+(?:from|of)\s+(?:the\s+First\s+Consul|Bonaparte),?\s+the\s+Louisiana\s+expedition'],
      stop=r'BANKS\s+OF|In\s+several\s+of|The\s+celebrated|BRUSSELS|A\s+Chilli',
      first="Rotterdam, April 1803: the French expedition to Louisiana is suspended by the First Consul's order.",
      what="the Rotterdam paragraph on the Louisiana expedition",
      printings=[k('NI', '05-30', 2),
                 k('ALX', '05-30', 2),
                 k('NHG', '05-31', 2),
                 k('RL', '05-31', 3),
                 k('BJ', '06-03', 2),
                 k('RIR', '06-04', 2),
                 k('ORA', '06-04', 2),
                 (k('KG', '06-14', 3), {'note': "The Kentucky Gazette gives the paragraph in shorter words: 'By an express order of Bonaparte, the Louisiana expedition is suspended, and the troops are debarked'."})]),
 dict(id='monroe-received-at-paris-april-1803', kind='message_group',
      label="Paris, 16 April 1803: a letter from a gentleman in Mr. Monroe's suite, 'Mr. Monroe was presented to the Minister for foreign affairs on the 14th'",
      definition="Printings of an extract of a letter from a gentleman in the suite of Mr. Monroe, the envoy extraordinary sent to France early in 1803, to a friend in New York, dated Paris, 16 April 1803: 'Mr. Monroe was presented to the Minister for foreign affairs on the 14th, by whom he was received with every mark of attention ... Mr. M. will not be presented to the First Consul until ten days hence'; it adds that General Bernadotte had left Paris to embark for the United States as the French minister, and that 'It is the general opinion that war is at no great distance'. A private letter's account, as a New York paper printed it.",
      role='report', words=55, dateline=False,
      core=[r'Extract\s+of\s+a\s+letter\s+from\s+a\s+[Gg]entleman\s+in\s+the\s+[Ss]uite\s+of\s+Mr\.?\s+Monroe', r'Mr\.?\s+Monroe\s+was\s+presented\s+to\s+the\s+[Mm]inister\s+for\s+[Ff]oreign'],
      first="A letter from Paris of 16 April 1803: the American envoy Mr. Monroe is received by the French minister for foreign affairs.",
      what="the letter from Mr. Monroe's suite",
      printings=[k('NI', '06-13', 3),
                 k('ALX', '06-13', 3),
                 k('BJ', '06-17', 2),
                 k('RIR', '06-18', 3),
                 (k('ORA', '06-18', 2), {'core': [r'EXTRACT\s+OF\s+A\s+LETTER\s+FROM\s+PARIS,?\s+APRIL\s+20'],
                                         'note': "The Oracle heads the letter 'Extract of a Letter from Paris, April 20.' (the other papers date it 16 April) and prints 'by whom he received every mark of attention'."}),
                 k('POR', '06-20', 2),
                 k('KG', '06-28', 2)]),
 dict(id='national-intelligencer-on-the-treaty-of-cession-july-1803', kind='message_group',
      label="Washington, July 1803: 'Dispatches from the American ministers at Paris ... contain the Treaty signed April 30th which conveys Louisiana to the United States', with its terms",
      definition="Printings of the National Intelligencer's paragraph of 18 July 1803, printed after the President's proclamation of 16 July: 'Dispatches from the American ministers at Paris were received by the Executive on Thursday evening. They were brought by Mr. Hughes of Baltimore, as confidential bearer, and contain the Treaty signed April 30th which conveys Louisiana to the United States. The extent of the territory ceded is defined by a general reference to that in which Louisiana was ceded to France'; the terms follow: '11,250,000 dollars to be paid to France in six per cent stock', the assumption of the debts and captures due by France to citizens of the United States, not to go beyond 3,750,000 dollars, and privileges for French and Spanish vessels in the ports of the ceded territory. The Oracle heads it 'Louisiana—[Official.]'. The government paper's statement, before the treaty was published.",
      role='report', words=60, dateline=False,
      core=[r'(?:Dispatches|Despatches|DISPATCHES)\s+from\s+the\s+American\s+[Mm]inisters?\s+at\s+Paris,?\s+were\s+received'],
      first="The National Intelligencer, 18 July 1803: dispatches from Paris contain the treaty of 30 April which conveys Louisiana to the United States, and its terms.",
      what="the National Intelligencer's paragraph on the treaty",
      printings=[k('NI', '07-18', 3),
                 k('ALX', '07-18', 3),
                 k('BJ', '07-22', 3),
                 k('RIR', '07-23', 3),
                 k('NHG', '07-26', 2),
                 k('RL', '07-26', 3),
                 k('ORA', '07-30', 3),
                 k('KG', '08-02', 3)]),
 dict(id='proclamation-convening-congress-16-july-1803', kind='document_group',
      label="The President's proclamation of 16 July 1803 convening Congress on 17 October",
      definition="Printings of the President's proclamation: 'WHEREAS great and weighty matters, claiming the consideration of the Congress of the United States, form an extraordinary occasion for convening them; I do by these presents appoint Monday the 17th day of October next for their meeting at the City of Washington', signed at Washington on 16 July 1803 by the President and the Secretary of State. Most papers print it with the National Intelligencer's paragraph on the treaty of cession. The President's own proclamation.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:A\s+)?P\s?ROCLAMATION\.?\s+(?:W\s?HEREAS|Whereas)\s+great\s+and\s+weighty', r'(?:W\s?HEREAS|Whereas)\s+great\s+and\s+weighty\s+matters'],
      first="The President's proclamation of 16 July 1803 calls Congress to meet on 17 October.",
      what="the proclamation convening Congress",
      printings=[k('NI', '07-18', 3),
                 k('ALX', '07-18', 3),
                 k('BJ', '07-22', 3),
                 k('RIR', '07-23', 3),
                 k('NHG', '07-26', 2),
                 k('RL', '07-26', 3),
                 k('ORA', '07-30', 3),
                 k('KG', '08-02', 3)]),
 dict(id='french-note-to-the-british-ambassador-13-may-1803', kind='document_group',
      label="The French minister for foreign affairs' note to the British ambassador, 13 May 1803, as communicated to the Conservative Senate",
      definition="Printings of a translation of the note that the minister for foreign affairs of the French Republic addressed to the ambassador of his Britannic Majesty on 23 Floreal (13 May 1803), and that orators of the government communicated to the Conservative Senate: 'In the important and serious circumstances, in which the two nations find themselves, the undersigned the minister for foreign affairs of the French Republic, has received an order to place under the eyes of the British government the following note'; it answers the King's message to Parliament of March 1803 on 'formidable armaments ... preparing in the ports of France and Holland', and gives the French government's account of the negotiation over Malta. The papers print two translations ('are situated', 'find themselves'). The French government's own note.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:I\s?N|In|U\s?NDER|Under)\s+(?:the\s+)?important\s+and\s+serious\s+circumstances'],
      first="The French government's note to the British ambassador of 13 May 1803, before the war.",
      what="the French note of 13 May",
      printings=[k('NI', '07-18', 2),
                 k('ALX', '07-18', 2),
                 k('POR', '07-18', 2),
                 k('RIR', '07-23', 2),
                 k('ORA', '07-23', 2),
                 k('NHG', '07-26', 1),
                 k('RL', '07-26', 3)]),
 dict(id='fifteen-millions-the-price-of-louisiana-1803', kind='message_group',
      label="'Fifteen millions of dollars (the price of Louisiana) ... would require 375 waggons to carry it': a calculation against the purchase, 1803",
      definition="Printings of a paragraph credited by some papers to the Lancaster Journal and by others to the Washington Federalist: 'Fifteen millions of dollars (the price of Louisiana) calculating more than a ton to every waggon, would require 375 waggons to carry it; and (allowing 4 horses to each team) it would require fifteen hundred horses, they would make a string of five miles in length. The money would support 25 thousand soldiers for seven years and a half'. The National Intelligencer, the Republican Ledger and the New Hampshire Gazette follow it with a 'Counter statement' on what the territory contains. A policy argument against the price, as the papers printed it.",
      role='report', words=55, dateline=False,
      core=[r'(?:F\s?IFTEEN|Fifteen)\s+(?:MILLIONS?|millions?)\s+(?:OF|of)\s+(?:DOLLARS|dollars),?\s*\(?\s*(?:the|THE)\s+price\s+of\s+Louisiana'],
      first="A paragraph on the price of Louisiana: fifteen millions of dollars would fill 375 waggons and support 25,000 soldiers for seven years and a half.",
      what="the paragraph on the fifteen millions",
      printings=[k('ALX', '08-09', 3),
                 k('BJ', '08-19', 3),
                 k('ORA', '09-10', 2),
                 k('NI', '09-14', 3),
                 k('RL', '09-27', 2),
                 k('NHG', '10-04', 2),
                 k('KG', '10-04', 2),
                 k('RIR', '10-13', 2)]),
 dict(id='convention-of-suhlingen-for-hanover-june-1803', kind='document_group',
      label="The convention of June 1803 for the occupation of Hanover by the French army",
      definition="Printings of the convention between the civil and military deputies of the Regency of Hanover and Lieutenant-General Mortier, commander in chief of the French army, signed at Suhlingen on 14 Prairial, year 11 (3 June 1803): 'Art. 1. Hanover shall be occupied by the French army, as well as the forts dependent on it. 2. The Hanoverian troops shall retire behind the Elbe; they shall engage on their parole of honor not to commit any hostilities'. The papers print it in two translations, after General Mortier's letter to the minister of war (8 papers, not admitted on its own; see the README). The parties' agreement, in translation.",
      role='published_document', words=55, dateline=False,
      core=[r'C\s?ONVENTION[,.]?\s+(?:Signed|signed|SIGNED)\s+between', r'Convention\s+agreed\s+upon\s+between\s+the\s+[Cc]ivil'],
      first="The convention of June 1803: Hanover to be occupied by the French army, the Hanoverian troops to retire behind the Elbe.",
      what="the convention for the occupation of Hanover",
      printings=[k('ORA', '08-13', 2),
                 k('NHG', '08-16', 2),
                 k('RL', '08-16', 2),
                 k('ALX', '08-16', 3),
                 k('NI', '08-17', 2),
                 k('RIR', '08-20', 1),
                 k('BJ', '08-26', 2),
                 k('KG', '09-06', 2)]),
 dict(id='king-message-on-the-batavian-republic-1803', kind='document_group',
      label="The King's message to the House of Commons on the Batavian republic, 1803",
      definition="Printings of the message that Lord Hawkesbury presented to the House of Commons: 'His Majesty thinks it right to inform the House of Commons, that, from an anxious desire to prevent the calamities of war being extended to the Batavian Republic, he communicated to that Government his disposition to respect their neutrality, provided that a similar disposition was manifested on the part of the French Government', and that, this not having been admitted, he directed his minister to leave the Hague and gave orders for letters of marque and reprisals. The Oracle heads it 'War with Holland'. The King's own message.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:GEORGE\s+(?:R|III)\.?\s+)?(?:H\s?IS|His)\s+Majesty\s+thinks\s+it\s+right\s+to\s+inform\s+the\s+House\s+of\s+Commons'],
      first="The King's message to the House of Commons, 1803: the French forces not withdrawn from the Batavian republic, his minister leaves the Hague.",
      what="the King's message on the Batavian republic",
      printings=[k('ORA', '08-13', 2),
                 k('POR', '08-15', 2),
                 k('NHG', '08-16', 3),
                 k('RL', '08-16', 3),
                 k('ALX', '08-17', 2),
                 k('NI', '08-19', 3),
                 (k('RIR', '08-20', 2), {'field': CA, 'core': [r'His\s+Maj\w+\s+thinks\s+it\s+right\s+to\s+inform\s+the\s+Hou\w+\s+of\s+Commons'], 'note': 'RevX lacks the message on this page; the older CA transcription has it, so the excerpt comes from the CA text.'}),
                 k('KG', '09-06', 2)]),
 dict(id='london-report-american-claims-paid-july-1803', kind='message_group',
      label="London, 20 July 1803: the first instalment of the awards on American claims for captures paid",
      definition="Printings of a London paragraph of 20 July 1803: 'It is with pleasure we are enabled to state, that the long pending discussions between our government and the United States, respecting the claims of the American citizens for captures by British cruizers during the last war, are now brought very nearly to a conclusion. Last Friday, the first awards upon the instalments of the commissioners, amounting to about 400,000 pounds, became due and was punctually paid by this government'; it puts the whole at 1,200,000 and praises the three commissioners. The Oracle heads it 'American Claims' and begins 'The long pending discussions between this government'. A London paper's report.",
      role='report', words=55, dateline=True,
      core=[r'(?:I\s?T|It)\s+is\s+with\s+pleasure\s+we\s+are\s+enabled\s+to\s+state', r'(?:T\s?HE|The)\s+long\s+pend\w+\s+discussions?\s+between'],
      first="London, 20 July 1803: the British government pays the first instalment of the awards on American claims for captures.",
      what="the London paragraph on the claims",
      printings=[k('ALX', '09-06', 3),
                 k('NI', '09-07', 2),
                 k('ORA', '09-10', 2),
                 k('POR', '09-12', 2),
                 k('NHG', '09-13', 2),
                 k('RL', '09-13', 3),
                 k('BJ', '09-16', 3),
                 k('KG', '09-20', 2)]),
 dict(id='dublin-letter-of-24-july-1803-on-the-rising', kind='message_group',
      label="A letter from Dublin of 24 July 1803 on the rising of the 23rd: 'You will be shocked to hear that we are at this moment in a more alarming situation than at any period during the unfortunate rebellion'",
      definition="Printings of a copy of a letter from Dublin, dated Sunday 11 o'clock, 24 July 1803, to a merchant in Liverpool, published at Liverpool on 28 July and headed 'Rebellion in Ireland' in several papers: 'You will be shocked to hear that we are at this moment in a more alarming situation than at any period during the unfortunate rebellion: At an early hour yesterday evening, a variety of inflammatory proclamations were distributed in every part of the town, calling on people to unite, as before, in opposition to English oppression'; it reports a general engagement in the streets and the officers, soldiers and yeomen killed. The New Hampshire Gazette prints the letter without its first sentence. A letter-writer's account at second hand.",
      role='report', words=60, dateline=True,
      core=[r'Copy\s+of\s+a\s+[Ll]etter\s+(?:from\s+Dublin,?\s+)?dated\s+Sunday', r'(?:["“]\s*)?(?:D\s?EAR|Dear)\s+(?:S\s?IR|Sir)\W+(?:["“]\s*)?You\s+will\s+be\s+shocked\s+to\s+hear'],
      first="A letter from Dublin of 24 July 1803 on the rising in the town the evening before.",
      what="the letter from Dublin",
      printings=[k('NI', '09-16', 2),
                 k('ALX', '09-16', 2),
                 k('ORA', '09-17', 2),
                 k('POR', '09-19', 2),
                 k('RL', '09-20', 2),
                 (k('NHG', '09-20', 2), {'note': "The New Hampshire Gazette prints the letter from its second sentence ('At an early hour yesterday evening'), headed 'Copy of a letter dated Sunday, 11 o'clock'."}),
                 k('BJ', '09-23', 2),
                 k('KG', '09-27', 3)]),
 dict(id='havre-letters-on-the-invasion-flotilla-august-1803', kind='message_group',
      label="London, 8 August 1803: 'From Havre de Grace, say letters, 70,000 men, on board a fleet ... for the Sussex Coast'",
      definition="Printings of a London paragraph of 8 August 1803 on French preparations to invade England, headed 'Invasion of England' in the Portland Gazette: 'From Havre de Grace, say letters, 70,000 men, on board a fleet consisting of gun-boats and other vessels of various denominations, sail in a direction, as nearly as possible, for the Sussex Coast. They are to land, if possible near Brighton. From Boulogne, Calais, Dunkirk, Ostend, and Holland, the several flotillas are to proceed to the opposite shores'. A report at second hand, from letters.",
      role='report', words=55, dateline=True,
      core=[r'(?:F\s?ROM|From)\s+Havre[\s-]+de[\s-]+Grace,?\s+(?:say|says|fly)\s+letters'],
      first="London, 8 August 1803: letters from Havre say that a French flotilla with 70,000 men is to sail for the coast of Sussex.",
      what="the London paragraph on the flotillas",
      printings=[k('NI', '09-21', 2),
                 k('ORA', '09-24', 3),
                 k('POR', '09-26', 2),
                 k('NHG', '09-27', 2),
                 k('RL', '09-27', 2),
                 k('BJ', '09-30', 2),
                 k('KG', '10-04', 3)]),
 dict(id='president-message-17-october-1803', kind='document_group',
      label="The President's message to Congress, 17 October 1803",
      definition="Printings of the message delivered to the two houses at the opening of the session the President had called for 17 October 1803: 'In calling you together, fellow citizens, at an earlier day than was contemplated by the act of the last session of Congress, I have not been insensible to the personal inconveniences necessarily resulting from an unexpected change in your arrangements; but matters of great public concernment have rendered this call necessary'; it recalls 'the extraordinary agitation produced in the public mind by the suspension of our right of deposit, at the port of New Orleans', announces the conventions with France for the cession of Louisiana, and speaks of the war in Europe, neutrality, the finances and the Indian tribes. The President's own message.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:T\s?O|To)\s+the\s+Senate\s+and\s+House\s+of\s+Representatives\s+of\s+the\s+United\s+States[:.,]?\s+(?:I\s?N|In)\s+calling\s+you\s+together',
            r'(?:I\s?N|In)\s+calling\s+you\s+together,?\s+(?:fellow|Fellow)'],
      first="The President's message of 17 October 1803 opens the session called early for the treaty with France.",
      what="the President's message of 17 October",
      printings=[k('NI', '10-17', 3),
                 k('ALX', '10-18', 2),
                 k('VA', '10-19', 1),
                 k('BJ', '10-21', 2),
                 k('RIR', '10-27', 3),
                 k('POR', '10-31', 1),
                 k('NHG', '11-01', 1),
                 k('ORA', '11-01', 2),
                 k('KG', '11-01', 3)]),
 dict(id='treaty-and-conventions-for-the-cession-of-louisiana-1803', kind='context_group',
      label="The treaty and two conventions of 30 April 1803 between the United States and the French Republic, printed after the Senate's vote",
      children=['louisiana-treaty-of-cession-30-april-1803', 'convention-for-sixty-million-francs-30-april-1803',
                'convention-on-debts-due-to-american-citizens-30-april-1803'],
      definition="The three instruments signed at Paris on 30 April 1803 for the cession of Louisiana, as the papers printed them from 21 October 1803, after the Senate's vote of 20 October advising their ratification: the treaty of cession, the convention for the payment of sixty million francs, and the convention for the payment of debts due by France to citizens of the United States. Most papers print the three together. Contains those three groups."),
 dict(id='louisiana-treaty-of-cession-30-april-1803', parent='treaty-and-conventions-for-the-cession-of-louisiana-1803', kind='document_group',
      label="The treaty for the cession of Louisiana, signed at Paris on 30 April 1803",
      definition="Printings of the treaty between the United States of America and the French Republic: 'The President of the United States of America, and the First Consul of the French Republic, in the name of the French people, desiring to remove all source of misunderstanding relative to objects of discussion mentioned in the second and fifth articles of the convention of the 8th Vendemiaire, an. 9, (30th September, 1800.) relative to the rights claimed by the United States, in virtue of the treaty concluded at Madrid'; its articles cede Louisiana as the French Republic acquired it from Spain. The National Intelligencer printed it on 21 October and again on 2 November with the President's proclamation. The two governments' treaty, as printed after the Senate's vote.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:T\s?HE|The)\s+President\s+of\s+the\s+United\s+States\s+of\s+America,?\s+and\s+the\s+First\s+Consul\s+of\s+the\s+French\s+Republic,?\s+in\s+the\s+name\s+of\s+the\s+French\s+people,?\s+desiring'],
      first="The treaty of 30 April 1803 by which the French Republic cedes Louisiana to the United States.",
      what='the treaty of cession',
      printings=[k('NI', '10-21', 3),
                 k('ALX', '10-24', 2),
                 (k('NI', '11-02', 1), {'note': "Printed again with the President's proclamation of the treaty."}),
                 k('BJ', '11-04', 1),
                 k('POR', '11-07', 1),
                 k('NHG', '11-08', 1),
                 k('KG', '11-08', 2),
                 k('ORA', '11-15', 1),
                 k('RL', '11-15', 1)]),
 dict(id='convention-for-sixty-million-francs-30-april-1803', parent='treaty-and-conventions-for-the-cession-of-louisiana-1803', kind='document_group',
      label="The convention of 30 April 1803 for the payment of sixty million francs",
      definition="Printings of the convention signed the same day: 'The President of the United States of America, and the First Consul of the French Republic, in the name of the French people, in consequence of the treaty of cession of Louisiana, which has been signed this day, wishing to regulate definitively every thing which has relation to the said cession'; by it the United States are to create a stock of eleven millions two hundred and fifty thousand dollars bearing an interest of six per cent. The two governments' convention.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:T\s?HE|The)\s+President\s+of\s+the\s+United\s+States\s+of\s+America,?\s+and\s+the\s+First\s+Consul\s+of\s+the\s+French\s+Republic,?\s+in\s+the\s+name\s+of\s+the\s+French\s+people,?\s+in\s+consequence\s+of\s+the\s+treaty\s+of\s+cession'],
      first="The convention of 30 April 1803 for the payment of sixty million francs.",
      what='the convention for sixty million francs',
      printings=[k('NI', '10-21', 3),
                 k('ALX', '10-24', 2),
                 (k('NI', '11-02', 1), {'note': "Printed again with the President's proclamation of the treaty."}),
                 k('BJ', '11-04', 2),
                 k('POR', '11-07', 1),
                 k('NHG', '11-08', 1),
                 k('ORA', '11-08', 1),
                 k('RL', '11-08', 1),
                 k('KG', '11-08', 2)]),
 dict(id='convention-on-debts-due-to-american-citizens-30-april-1803', parent='treaty-and-conventions-for-the-cession-of-louisiana-1803', kind='document_group',
      label="The convention of 30 April 1803 for the payment of debts due by France to citizens of the United States",
      definition="Printings of the second convention signed the same day: 'The President of the United States of America, and the First Consul of the French Republic, in the name of the French people, having by a treaty of this date terminated all difficulties relative to Louisiana, and established on a solid foundation the friendship which unites the two nations, and being desirous, in compliance with the second and fifth articles of the convention of the 8th Vendemiaire, ninth year of the French Republic (30th September, 1800) to secure the payment of the sums due by France to the citizens of the United States'. The two governments' convention.",
      role='published_document', words=60, dateline=False,
      core=[r'(?:T\s?HE|The)\s+President\s+of\s+the\s+United\s+States\s+of\s+America,?\s+and\s+the\s+First\s+Consul\s+of\s+the\s+French\s+Republic,?\s+in\s+the\s+name\s+of\s+the\s+French\s+people,?\s+having\s+by\s+a\s+treaty'],
      first="The convention of 30 April 1803 for the payment of debts due by France to American citizens.",
      what='the convention on the debts',
      printings=[k('NI', '10-21', 3),
                 k('ALX', '10-24', 2),
                 (k('NI', '11-02', 1), {'note': "Printed again with the President's proclamation of the treaty."}),
                 k('BJ', '11-04', 2),
                 k('POR', '11-07', 1),
                 k('NHG', '11-08', 2),
                 k('ORA', '11-08', 1),
                 k('RL', '11-08', 1),
                 k('KG', '11-08', 2)]),
 dict(id='treasury-report-25-october-1803', kind='document_group',
      label="The Secretary of the Treasury's reports and estimates laid before the House of Representatives, 25 October 1803",
      definition="Printings of the report that the Secretary of the Treasury, Albert Gallatin, laid before the House of Representatives on 25 October 1803: 'In obedience to the directions of the act supplementary to the act entitled An act to establish the Treasury Department, the Secretary of the Treasury respectfully submits the following Reports and Estimates. The annual nett proceeds of the duties on merchandise and tonnage had, in former reports, been estimated at nine millions five hundred thousand dollars'; it estimates the revenue and the expenses of 1804 and considers whether new revenue is wanted for the debt that the treaty with France would create. The Secretary of the Treasury's own report.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:I\s?N|In)\s+obedience\s+to\s+the\s+(?:directions?|provisions?)\s+of\s+the\s+act\s+supplement\w+', r'(?:T\s?HE|The)\s+annual\s+net\w*\s+proceeds\s+of\s+the\s+duties\s+on\s+merchandise'],
      first="The Secretary of the Treasury's report of 25 October 1803 on the revenue, the expenses of 1804 and the new debt.",
      what="the Treasury report of October 1803",
      printings=[k('NI', '10-28', 2),
                 k('ALX', '11-02', 2),
                 k('NHG', '11-15', 1),
                 k('KG', '11-15', 2),
                 k('RIR', '11-17', 1),
                 k('BJ', '11-18', 1),
                 k('ORA', '11-22', 1),
                 k('RL', '11-22', 1)]),
 dict(id='president-message-on-morocco-november-1803', kind='document_group',
      label="The President's message of November 1803 on an act of hostility by an armed ship of the Emperor of Morocco",
      definition="Printings of the President's message to the two houses: 'By the copy now communicated, of a letter from Captain Bainbridge of the Philadelphia frigate to our Consul at Gibraltar, you will learn that an act of hostility has been committed on a merchant vessel of the United States, by an armed ship of the Emperor of Morocco. This conduct, on the part of that power, is without cause and without explanation. It is fortunate that Captain Bainbridge fell in with, and took the capturing vessel and her prize'; it reports that a squadron was arriving near Gibraltar and leaves it to Congress 'to consider the provisional authorities which may be necessary to restrain the depredations of this power'. The President's own message.",
      role='published_document', words=55, dateline=False,
      core=[r'(?:["“]\s*)?By\s+the\s+copy,?\s+now\s+communicated'],
      first="The President's message of November 1803: an armed ship of the Emperor of Morocco has taken an American merchant vessel.",
      what="the President's message on Morocco",
      printings=[k('NI', '11-07', 3),
                 k('ALX', '11-08', 2),
                 k('RIR', '11-17', 3),
                 k('BJ', '11-18', 3),
                 k('POR', '11-19', 3),
                 k('NHG', '11-22', 2),
                 k('KG', '11-22', 3)]),
 dict(id='calamity-at-madeira-9-october-1803', kind='message_group',
      label="'Calamity at Madeira': an account of the storm and flood of 9 October 1803",
      definition="Printings of an account of a storm and flood at Funchal, Madeira, headed 'Calamity at Madeira' in several papers: 'This extraordinary event, which we briefly noticed in our paper of yesterday, happened on Sunday the 9th of October, at eight in the evening. The day had been previously very cloudy and a continual rain had fallen'; it tells of torrents from the mountains carrying 'churches, convents, streets, trees, bridges, battlements and eight hundred human beings into the bottom of the deep'. A report at second hand, from a daily paper.",
      role='report', words=55, dateline=False,
      core=[r'(?:C\s?ALAMITY\s+AT\s+M\s?ADEIRA\.?\s+)?(?:T\s?HIS|This)\s+extraordinary\s+event,?\s*\(?\s*which\s+we\s+briefly\s+noticed', r'happened\s+on\s+Sunday\s+the\s+9th\s+of\s+October'],
      first="An account of the storm and flood at Madeira on 9 October 1803.",
      what='the account of the flood at Madeira',
      printings=[k('ALX', '12-14', 2),
                 k('NI', '12-16', 3),
                 k('NHG', '12-20', 2),
                 k('ORA', '12-20', 3),
                 k('RL', '12-20', 2),
                 k('BJ', '12-23', 3),
                 k('POR', '12-24', 4)]),
 dict(id='gold-ore-found-in-cabarrus-county-december-1803', kind='message_group',
      label="Raleigh, December 1803: 'A bed of Gold Ore has been lately discovered in Cabarrus County'",
      definition="Printings of a report from Raleigh, North Carolina, of early December 1803 (a Raleigh paragraph of 5 December in most papers, a letter dated 8 December in the National Intelligencer): 'A bed of Gold Ore has been lately discovered in Cabarrus County, in this state, in a Creek running through the land of' a farmer, 'which promises to be a source of great riches to the proprietor'; his children found the first pieces while fishing. The papers name the landowner; the excerpts end before his name. A report at second hand.",
      role='report', words=40, dateline=True, back=False, stop=r'in\s+a\s+[Cc]reek\s+running|(?:of\s+)?(?:Mr\.?\s+)?John\s+Reed',
      core=[r'(?:A\s+)?(?:B\s?ED|Bed|bed)\s+of\s+(?:G\s?OLD|Gold|gold)\s+(?:O\s?RE|Ore|ore)\s+has'],
      first="Raleigh, December 1803: a bed of gold ore has been found in Cabarrus County, North Carolina.",
      what='the report of gold in Cabarrus County',
      printings=[k('ALX', '12-19', 2),
                 k('NI', '12-23', 3),
                 k('BJ', '12-23', 2),
                 k('POR', '12-24', 2),
                 k('NHG', '12-27', 2),
                 k('ORA', '12-27', 2),
                 k('RIR', '12-29', 2)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797 and 1800): "BOSTON, Nov. 30th, 1802."
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
            problems.append((s['id'], key, 'page not in the 1803 pages'))
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
        r['id'] = f'S03-{n:03}'
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
               'admission_rule': 'Reviewed 1803 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1803/'
    return {
        'ledger_id': 'ledger:stories-1803', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1803', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1803, and of 1802 where they reach the 1803 pages (long-running ones '
                   'included), a sweep of word-for-word passages shared by 7 or more papers for short items the families miss, phrase searches on '
                   'all 3,250 pages of 1803 in both transcriptions, reading of every hit, and scan checks of each admitted passage, by the one '
                   'admission rule (9 or more papers admitted, 7 or 8 chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1802.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1803.py': 'ledger_code', 'work/archive_data/ledgers/stories_1803_review.json': 'scan_review',
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
