"""Write ledgers/stories_1795.json: reviewed stories of 1795, round one.

1795 is a thin year: no item of 1795 reaches 7 papers by the release's matched stories, so it is read by the thin-year rule
(docs/rules-and-exceptions.md, Y-THIN, as amended on 23 November 2026, the owner's choice B1): an item, counted by its own
words, is eligible when it was printed by more than half of the newspapers that survive for its weeks (those with a
surviving issue between its first and its last printing, and at least in the three weeks from its first printing), and by
at least 4; as in R-01, the items printed by every newspaper that survives for their weeks are admitted, and the other
eligible items are chosen to cover the months and the kinds of news, about as many stories as a standard year; one
affair's items are treated as in X-1800-01; digests are not admitted. In 1795 4 to 8 papers survive for an item's weeks,
so the bar is 4 or 5.
The automatic families first printed in 1795 that reach 3 or more papers, long-running ones included, were split into
single printed items with work/story_items.py --long-running (items.json), and again with year 1794 over the 1795 pages
(items_from_1794.json); every item in 3 or more papers was compared by machine with every page and counted again by its
opening, a sweep of word-for-word passages shared by 4 or more papers found short items the families miss, and the
admitted and chosen items were counted by their own words over all 1,668 pages of 1795 in both transcriptions. See
outputs/story_discovery_1795/README.md and count_1795.md.

The 1795 pages are those whose issue the data release dates to 1795 (work/year_search_pages.py 1795 ... --printed-dates);
no 1795 issue has a corrected date. 1795 has 11 catalogue series, which are 9 papers (C-04): the Gazette of the United
States (Philadelphia, daily, 200 issues, under sn84026271 to 30 June and sn84026273 from 8 July, to 30 November), the
New-Hampshire Gazette (Portsmouth, 52), the Kentucky Gazette (Lexington, 49), the Concord paper (44: The Mirrour to 3 April,
The Federal Mirror from 10 April), the American Herald of Liberty (Exeter, 29), the Columbian Informer (Keene, 16, to 21
April), the Patowmac Guardian (Shepherdstown, 12), The Eagle (Hanover, 8, May to October) and The Phoenix (Dover, 1).
The release's map of misfiled RevX pages lists 5 pages of 1795 (the New-Hampshire Gazette of 3 February, the Gazette of the
United States of 11 June); no printing of this ledger is on them.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-85 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1795_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (reviews of other years run at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1795.py [--table] [--base 0.11.35 --target 0.11.36]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1795/search_pages.json). The excerpts are cut from
the 1795 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1795'
D = PROJECT/'outputs/story_discovery_1795'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1795_review.json'
OUT = HERE/'stories_1795.json'
BASE, TARGET = '0.11.35', '0.11.36'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn84026271': 'The Gazette of the United States', 'sn84026273': 'The Gazette of the United States', 'sn82014782': 'The Kentucky Gazette',
         'sn83025588': 'The New-Hampshire Gazette', 'sn84023134': 'The American Herald of Liberty', 'sn83025523': 'The Mirrour',
         'sn83025524': 'The Federal Mirror', 'sn84023313': 'The Columbian Informer', 'sn84038410': 'The Patowmac Guardian',
         'sn84023150': 'The Eagle, or Dartmouth Centinel', 'sn84023045': 'The Phoenix'}
ONE = {'GUS': 'sn84026271', 'GUS2': 'sn84026273', 'KG': 'sn82014782', 'NHG': 'sn83025588', 'AHL': 'sn84023134', 'MIR': 'sn83025523',
       'FM': 'sn83025524', 'CI': 'sn84023313', 'PG': 'sn84038410', 'EAG': 'sn84023150', 'PHX': 'sn84023045'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1795), page and edition."""
    return f'{ONE[paper]}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release (5 pages of 1795)."""
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
ACT = r'A\s?N\s+A\s?CT,?\s+'   # an act's excerpt starts with its title, as for 1808 and 1791
STORIES = [
 # ---- January and February: the thanksgiving proclamation, the insurgents, the King's speech, the news by the Chesapeake, the posts ----
 dict(id='presidents-proclamation-for-a-day-of-thanksgiving-1-january-1795', kind='document_group',
      label="The President's proclamation of 1 January 1795 appointing 19 February a day of public thanksgiving and prayer: 'When we review the calamities, which afflict so many other nations'",
      definition="Printings of the President's proclamation dated 1 January 1795: 'When we review the calamities, which afflict so many other nations, the present condition of the United States affords much matter of consolation and satisfaction. Our exemption hitherto from foreign war—an increasing prospect of the continuance of that exemption—the great degree of internal tranquility we have enjoyed—the recent confirmation of that tranquility by the suppression of an insurrection, which so wantonly threatened it'; it recommends Thursday, 19 February, as a day of public thanksgiving and prayer. The President's own proclamation.",
      role='published_document', words=60, dateline=True,
      head=r'(?:A\s+P\s?ROCLAMATION\s*[.,;:]?\s*)?B\s?Y\s+THE\s+P\s?RESIDENT\s+OF\s+THE\s+U\.?\s?(?:NITED)?\s*S\.?\s?(?:TATES)?\s+OF\s+A\s?MERICA[.,;]?\s*(?:A\s+P\s?ROCLAMATION\.?\s*)?',
      core=[r'W\s?HEN\s+we\s+review\s+the\s+calamities'],
      first="The President proclaims 19 February a day of public thanksgiving and prayer for the condition of the United States.",
      what="the President's proclamation of 1 January",
      printings=[k('CI', '01-13', 3), (k('MIR', '01-16', 3), {'core': [r'B\s?y\s+the\s+W\W+\s*present\s+condition'], 'dateline': False}),
                 k('PHX', '01-17', 2), k('AHL', '01-17', 3), k('NHG', '01-20', 1)]),
 dict(id='philadelphia-insurgents-from-the-westward-lodged-in-the-jail-december-1794', kind='message_group',
      label="Philadelphia, 26 December 1794: twenty of the insurgents, prisoners at Pittsburgh who were refused bail, are brought from the westward and lodged in the jail of the city",
      definition="Printings of a Philadelphia paragraph of 26 December 1794: 'Yesterday arrived from the westward, and were lodged in the goal of this city, 20 of the Insurgents. They are such of the prisoners confined in the garrison at Pittsburgh, as were refused bail; the residue (about 100) are admitted to bail.' A Philadelphia paper's report.",
      role='report', words=50, dateline=True,
      head=r'(?:T\s?HE\s+W\s?HISKY\s+B\s?OYS\.?\s*)?P\s?HILADELPHIA,?\s+D\s?EC(?:EMBER|\.)?\s+26\.?\s*',
      core=[r'Y\s?ESTERDAY\s+arrived\s+from\s+the\s+west\W*ward'],
      first="Twenty of the western insurgents refused bail at Pittsburgh are brought to Philadelphia and lodged in the jail.",
      what="the Philadelphia paragraph on the insurgents",
      printings=[k('MIR', '01-09', 3), k('AHL', '01-10', 3), k('NHG', '01-13', 3), k('CI', '01-13', 3), k('PHX', '01-17', 3)]),
 dict(id='baltimore-letter-french-ships-of-the-line-in-the-chesapeake-february-1795', kind='message_group',
      label="Baltimore, 3 February 1795: an extract of a letter, 'there are arrived in the Chesapeake two French line of battle ships and three frigates; that they have on board an ambassador'",
      definition="Printings of an extract of a letter from Baltimore dated 3 February 1795: 'There is nothing new here at present but the following which I have just received from the custom house—that there are arrived in the Chesapeake two French line of battle ships and three frigates; that they have on board an ambassador from the National Convention to the United States'. A letter writer's report of what the custom house had heard.",
      role='report', words=60, dateline=True,
      head=r'(?:(?:F\s?RENCH\s+A\s?MBASSADOR|N\s?ew\s+A\s?mbassador\s+from\s+F\s?rance)\.?\s*)?Extra(?:ct)?\s+of\s+a\s+[Ll]etter\s+from\s+Baltimore,?\s+dated\s+Feb(?:ruary|\.)?\s+3\.?\s*[\"“]?\s*',
      core=[r'T\s?HERE\s+is\s+nothing\s+new\s+here\s+at\s+present'],
      first="A letter from Baltimore reports two French ships of the line and three frigates arrived in the Chesapeake with an ambassador on board.",
      what="the Baltimore letter on the French ships",
      printings=[k('GUS', '02-06', 3), k('NHG', '02-17', 3), k('MIR', '02-20', 3), k('AHL', '02-21', 2), k('KG', '03-28', 2)]),
 dict(id='the-kings-speech-at-the-opening-of-parliament-30-december-1794', kind='document_group',
      label="The King's speech to both Houses of Parliament, 30 December 1794: 'After the uniform experience which I have had of your zealous regard for the interests of my people'",
      definition="Printings of the King's speech at the opening of the session of Parliament, 30 December 1794: 'My Lords and Gentlemen, After the uniform experience which I have had of your zealous regard for the interests of my people, it is a great satisfaction to me to recur to your advice and assistance'. The King's own speech, as the papers print it from the London papers.",
      role='published_document', words=60, dateline=False,
      head=r'(?:H\s?IS\s+M\s?AJESTY.S\s+S\s?PEECH,?\s+T\s?O\s+BOTH\s+H\s?OUSES\s+OF\s+P\s?ARLIAMENT:?\s*delivered\s+(?:the\s+)?30th\s+Dec(?:ember|\.)?,?\s*1794\.?\s*)?M\s?Y\s+L\s?ORDS,?\s+(?:and|&)\s+G\s?ENTLEMEN[,.]?\s*',
      core=[r'A\s?FTER\s+the\s+uniform\s+experience\s+which\s+I\s+have\s+had'],
      first="The King opens the session of Parliament with a speech on the war with France.",
      what="the King's speech of 30 December 1794",
      printings=[k('NHG', '02-10', 3), k('AHL', '02-14', 2), k('GUS', '02-16', 2), k('MIR', '02-20', 1), k('CI', '02-24', 2), k('PG', '03-02', 2), k('KG', '04-11', 4)]),
 dict(id='the-western-posts-to-be-delivered-up-in-june-1796-described-february-1795', kind='message_group',
      label="Boston, 18 February 1795: 'The Western Posts, which have so long been a bone of contention between the United States and Great Britain, and which are to be delivered up to the American arms, in June 1796, are four in number'",
      definition="Printings of a Boston paragraph of 18 February 1795 headed 'The Western Posts': 'The Western Posts, Which have so long been a bone of contention between the United States and Great Britain, and which are to be delivered up to the American arms, in June 1796, are four in number, viz. Oswego, at the entrance of lake Ontario, where the British have a company of foot; and a Custom House, to prevent illicit trade in furs, &c. Niagara, on the same lake'; it describes the four posts one by one. A Boston paper's description.",
      role='report', words=60, dateline=True,
      core=[r'(?:T\s?HE\s+)?W\s?ESTERN\s+P\s?OSTS,?\.?\s+W\s?hich\s+have\s+(?:so|to)\s+long\s+been'],
      first="A Boston paper describes the four western posts that the British are to deliver up in June 1796.",
      what="the paragraph on the Western Posts",
      printings=[k('MIR', '02-20', 3), k('AHL', '02-21', 2), k('NHG', '02-24', 2), k('CI', '02-24', 3), k('GUS', '03-02', 3), k('KG', '04-18', 4)]),
 dict(id='the-presidents-message-on-the-georgia-land-sales-february-1795', kind='message_group',
      label="February 1795: 'In the House of Representatives of Congress a message was received from the President of the United States, relative to the sales of the lands in the Indian country by the Legislature of Georgia'",
      definition="Printings of a paragraph of February 1795, in a Philadelphia form ('a message was yesterday received') and a New York form of 21 February ('a message was last Tuesday received'): 'In the House of Representatives of Congress a message was last Tuesday received from the President of the United States, relative to the sales of the lands in the Indian country by the Legislature of Georgia; this message represented the subject to be one of great importance involving the Peace and welfare of the United States.' A paper's report of the President's message.",
      role='report', words=55, dateline=True,
      core=[r'I\s?N\s+the\s+House\s+of\s+Representatives\s+of\s+Congress\s+a\s+message\s+was'],
      first="The President sends the House of Representatives a message on Georgia's sales of lands in the Indian country, a subject 'involving the Peace and welfare of the United States'.",
      what="the paragraph on the President's message about the Georgia land sales",
      printings=[k('GUS', '02-18', 3), k('MIR', '03-06', 3), k('AHL', '03-07', 3), k('NHG', '03-10', 2)]),
 dict(id='fort-washington-letter-the-indians-apply-for-a-treaty-of-peace-february-1795', kind='message_group',
      label="Philadelphia, 28 February 1795, 'Important and pleasing intelligence': an extract of a letter from Fort Washington of 2 February, 'The Indians have by their Deputies generally applied for a Treaty of Peace with the United States'",
      definition="Printings of an extract of a letter dated Fort Washington, 2 February 1795, which a Philadelphia paper printed on 28 February under 'Important and pleasing Intelligence. Received this Day by Express from Head Quarters': 'The Indians have by their Deputies generally applied for a Treaty of Peace with the United States; you will see by the official papers now transmitted, that preliminary articles are signed'. A letter writer's report from the army's headquarters.",
      role='report', words=60, dateline=True,
      head=(r'(?:I\s?MPORTANT\s+and\s+pleasing\s+(?:I\s?ntelligence|N\s?ews)\.?\s*)?(?:R\s?eceived\s+(?:this\s+[Dd]ay,?\s+)?by\s+[Ee]xpress\s+from\s+H\s?ead[\s\-]*[Qq]uarters\.?\s*)?'
            r'Extra(?:ct)?\s+of\s+(?:a|two)\s+[Ll]etters?,?\s+(?:dated|from)\s+Fort[\s\-]*Washington,?\s+Feb(?:ruary|\.)?\s+2,?\s*(?:17\d\d)?[,.]?\s*[—\-]*\s*to\s+(?:a|two)\s+[Gg]entlem[ae]n\s+in\s+this\s+[Cc]ity\.?\s*[\"“«]?\s*'),
      core=[r'(?:T\s?HE|qr\s+HE)\s+Indians\s*have\s+[Bb]y\s+their\s+[Dd]eputies'],
      first="A letter from Fort Washington reports that the Indians have generally applied by their deputies for a treaty of peace, and preliminary articles are signed.",
      what="the letter from Fort Washington",
      printings=[k('GUS', '02-28', 3), (k('NHG', '03-17', 2), {'dateline': False}), k('MIR', '03-20', 3), k('AHL', '03-21', 2), k('CI', '03-24', 2)]),
 # ---- March and April: Algiers, naturalization, the brig Lydia, Amsterdam, the Secretary of State's circular, St. Martins ----
 dict(id='a-correspondent-on-a-treaty-with-the-dey-of-algiers-march-1795', kind='message_group',
      label="March 1795: 'A correspondent assures us upon good authority ... that a treaty of some kind is either concluded or at least in forwardness with the Dey of Algiers for the redemption of our captive citizens'",
      definition="Printings of a paragraph of early March 1795: 'A correspondent assures us upon good authority, and the information must gladden many a heart, that a treaty of some kind is either concluded or at least in forwardness with the Dey of Algiers for the redemption of our captive citizens. He has refused, it appears, money in ransom'. A correspondent's report.",
      role='report', words=55, dateline=True,
      core=[r'A\s+[Cc]orrespondent\s+assures\s+(?:us,?\s+)?upon\s+good\s+authority'],
      first="A correspondent reports that a treaty with the Dey of Algiers for the redemption of the American captives is concluded or in forwardness.",
      what="the paragraph on a treaty with Algiers",
      printings=[k('GUS', '03-04', 3), k('NHG', '03-17', 2), k('MIR', '03-20', 3), k('AHL', '03-21', 2), k('KG', '04-18', 4)]),
 dict(id='act-to-establish-an-uniform-rule-of-naturalization-january-1795', kind='document_group',
      label="An Act to establish an uniform rule of naturalization, and to repeal the act heretofore passed on that subject (approved 29 January 1795)",
      definition="Printings of the act: 'An Act to establish an uniform rule of naturalization; and to repeal the act heretofore passed on that subject. For carrying into complete effect, the power given by the Constitution, to establish an uniform rule of naturalization throughout the United States: Be it enacted by the Senate and House of Representatives of the United States of America, in Congress assembled, That any alien, being a free white person, may be admitted to become a citizen of the United States, or any of them, on the following conditions'. The act itself, as the papers print it.",
      role='published_document', words=60, dateline=False,
      head=r'(?:N\s?ATURALIZATION\s+)?L\s?A\s?W,?\s+of\s+the\s+U\s?NITED\s+S\s?TATES\.?\s*',
      core=[ACT + r'to\s+establish\s+an?\s+uniform\s+rule\s+of\s+naturalization'],
      first="Congress sets a uniform rule of naturalization: a free white alien may become a citizen on the conditions the act lays down.",
      what="the naturalization act",
      printings=[k('AHL', '03-07', 1), k('NHG', '03-10', 2), k('GUS', '03-11', 3), k('MIR', '03-13', 1), k('KG', '04-25', 4)]),
 dict(id='new-york-the-brig-lydia-from-amsterdam-march-1795', kind='message_group',
      label="New York, 9 March 1795: 'On Saturday arrived the brig Lydia, Capt. Shackerly, in 56 days from Amsterdam. Letters have been received from thence as late as the 7th January'",
      definition="Printings of a New York paragraph of 9 March 1795: 'On Saturday arrived the brig Lydia, Capt. Shackerly, in 56 days from Amsterdam. Letters have been received from thence as late as the 7th January. We have seen those addressed to a respectable house in this city. They at different dates, state the progress of the French'. A New York paper's report of the letters a ship brought.",
      role='report', words=55, dateline=True,
      core=[r'O\s?N\s+Saturday\s+arrived\s+(?:the\s+)?brig\s+Lydia'],
      first="The brig Lydia arrives at New York from Amsterdam with letters on the progress of the French in Holland.",
      what="the New York paragraph on the brig Lydia",
      printings=[k('GUS', '03-11', 3), k('NHG', '03-17', 3), (k('MIR', '03-20', 3), {'head': r'[\"“]?\s*N\s?ew\s?york,?\s+March\s+9\.?\s*'}), k('AHL', '03-21', 2),
                 (k('CI', '03-24', 3), {'head': r'N\s?EW\s?YORK,?\s+M\s?ARCH\s+9\.?\s*'}), k('KG', '04-18', 4)]),
 dict(id='proclamation-of-the-revolutionary-committees-of-amsterdam-january-1795', kind='document_group',
      label="The proclamation of the Revolutionary Committees of Amsterdam, January 1795: 'Brave Citizens'",
      definition="Printings of the proclamation of the Revolutionary Committees of Amsterdam of January 1795, which opens 'Brave Citizens, We' and the names of the committee's members, 'forming your Revolutionary Committee, hail you with vows of health and fraternity'. The committee's own proclamation, in translation.",
      role='published_document', words=55, dateline=False,
      head=r'(?:P\s?ROCLAMATION[.,]?\s+(?:[Oo][Ff]|df\.)\s+THE\s+R\s?EVOLUTIONARY\s+C\s?OMMITTEES?\s+OF\s+A\s?MSTERDAM\s*\.?\s*)?[\"“]?\s*',
      core=[r'B\s?RAVE\s+C\s?ITIZENS'],
      first="The Revolutionary Committees of Amsterdam address the citizens in a proclamation.",
      what="the proclamation of the Revolutionary Committees of Amsterdam",
      printings=[k('NHG', '03-31', 2), k('MIR', '04-03', 3), (k('AHL', '04-04', 1), {'field': 'ca_ocr_text', 'head': r'P\s?ROCLAMATION,?\s+df\.\s+the\s+Revolutionary\s+Committees\s+of\s+Amjlerdam\.?.{0,16}?',
                                                                    'stop': r'give\w*\s+t\w\s+all\s+Holland'}), k('GUS', '04-04', 2), k('CI', '04-07', 3),
                 (k('KG', '05-09', 3), {'core': [r'P\s?ROCLAMATION\s+[Oo]f\s+the\s+R\s?evolutionary\s+C\s?ommittees?\s+of\s+A\s?msterdam'], 'head': None, 'dateline': False})]),
 dict(id='secretary-of-states-circular-of-16-april-1795-on-ships-of-war', kind='document_group',
      label="The Secretary of State's circular of 16 April 1795: ships of war of the belligerent powers not to take a station in the waters of the United States",
      definition="Printings of the circular of the Department of State dated 16 April 1795: 'As it is contrary to the law of Nations, that any of the Belligerent Powers should commit hostility on the waters, which are subject to the exclusive jurisdiction of the United States; so ought not the ships of war, belonging to any Belligerent Power, to take a station in those waters in order to carry on hostile expeditions from thence.' The Secretary of State's own circular.",
      role='published_document', words=60, dateline=False,
      head=r'(?:\(?\s*C\s?IRCULAR\.?\s*\)?\s*)?D\s?epartment\s+of\s+S\s?tate,?\s+April\s+16(?:th)?,?\s*1795\.?\s*S\s?I\s?R[.,]\s*',
      core=[r'A\s?S\s+it\s+is\s+contrary\s+to\s+the\s+[Ll]aw\s+of\s+[Nn]ations'],
      first="The Secretary of State's circular: belligerent ships of war are not to take a station in American waters to carry on hostile expeditions.",
      what="the Secretary of State's circular",
      printings=[k('GUS', '04-24', 3), k('NHG', '05-05', 3), k('AHL', '05-09', 2), k('KG', '05-23', 1)]),
 dict(id='the-sloop-delia-from-st-martins-the-island-taken-april-1795', kind='message_group',
      label="New York, April 1795: Capt. McIntire of the sloop Delia from St. Martins reports the island taken by the French and the Dutch Patriots on 3 April",
      definition="Printings of a paragraph of late April 1795, in a Philadelphia form ('has obligingly communicated to us the following information') and a New York form of 29 April ('informs'): 'Capt. McIntire, of the sloop Delia, which arrived yesterday from St. Martins, and left there the 11th inst. informs, that St. Martin's was taken possession of by the French and Dutch Patriots, on Sunday, the 3d inst.' A shipmaster's report.",
      role='report', words=50, dateline=False,
      head=r'(?:C\s?ONFIRMATION\.?\s*)?(?:From\s+)?N\s?EW[\s\-]*Y\s?ORK,?\s+A\s?PRIL\s+29\.?\s*',
      core=[r'Capt(?:ain|\.)\s+M[\'’c]\s?Intire,?\s+of\s+the\s+sloop\s+Delia'],
      first="The sloop Delia from St. Martins reports the island taken by the French and the Dutch Patriots on 3 April.",
      what="the report by the sloop Delia",
      printings=[k('GUS', '04-30', 3), k('NHG', '05-05', 3), k('FM', '05-08', 3), k('AHL', '05-09', 3), k('KG', '05-30', 1)]),
 # ---- May to July: the Port Mary, the treaty of Basel, Mr. Hastings, the Boston riot, Mr. Jay's treaty ----
 dict(id='from-the-argus-the-port-mary-from-liverpool-may-1795', kind='message_group',
      label="New York, May 1795, from the Argus: 'The Port Mary, Capt. Kennedy, arrived at this port on Saturday evening in 40 days from Liverpool', with a Corunna account of a battle in Roussillon",
      definition="Printings of a paragraph from the Argus, a new daily paper of New York, of 11 May 1795: 'The Port Mary, Capt. Kennedy, arrived at this port on Saturday evening in 40 days from Liverpool. Capt. Kennedy brought papers to March 25, which contain very little intelligence. A Liverpool paper of March 23, contains a Corunna account of a battle in Roussillon'. A New York paper's report of the papers a ship brought.",
      role='report', words=55, dateline=True,
      core=[r'T\s?HE\s+Port\s+Mary,?\s+Capt(?:ain|\.)\s+Kennedy'],
      first="The Port Mary arrives at New York from Liverpool with papers to 25 March and a Corunna account of a battle in Roussillon.",
      what="the paragraph on the Port Mary",
      printings=[k('GUS', '05-12', 3), k('AHL', '05-21', 3), k('FM', '05-22', 3), k('PG', '05-23', 3), k('NHG', '05-26', 2)]),
 dict(id='treaty-of-peace-between-the-french-republic-and-the-king-of-prussia-april-1795', kind='document_group',
      label="The treaty of peace between the French Republic and the King of Prussia, presented to the National Convention by Rewbell on 11 April 1795",
      definition="Printings of the National Convention's sitting of 11 April 1795, in which Rewbell, in the name of the Committee of Public Safety, presented the treaty of peace concluded with the King of Prussia, in two translations counted as one item (C-02): 'Treaty between Prussia and the French Republic, presented by Rewbel in the name of the Committee of Public Safety' (the New-Hampshire Gazette and the Gazette of the United States) and 'Reubel, in the name of the Committee of Public Safety, ascended the tribune; he said, Your Committee' (the American Herald of Liberty and the Federal Mirror). The Convention's report and the treaty, in translation.",
      role='published_document', words=55, dateline=False,
      head=r'(?:R\s?eport\s+of\s+a\s+T\s?REATY\s+with\s+P\s?RUSSIA\.?\s*)?S\s?ESSIONS?\s+OF\s+11\s?TH\s+A\s?PRIL\.?\s*',
      core=[r'T\s?REATY\s+between\s+P\s?RUSSIA\s+and\s+the\s+F\s?RENCH\s+R\s?EPUBLIC', r'R\s?\s?[EU]\s?[EU]\s?B\s?E\s?L,?\s+in\s+the\s+name\s+of\s+the\s+[Cc]ommittee\s+of\s+[Pp]ublic\s+[Ss]afety,?\s+ascended'],
      first="Rewbell presents to the National Convention the treaty of peace concluded with the King of Prussia.",
      what="the treaty with the King of Prussia",
      printings=[k('NHG', '06-09', 2), k('GUS', '06-10', 3), k('AHL', '06-11', 2), k('FM', '06-19', 1)]),
 dict(id='london-the-judgment-of-mr-hastings-in-westminster-hall-may-1795', kind='message_group',
      label="London, May 1795, 'Judgment of Mr. Hastings': the Lords' judgment in Westminster Hall on the impeachment of Warren Hastings",
      definition="Printings of a London report of 5 May 1795 headed 'Judgment of Mr. Hastings': 'About one o'clock the lords being come into the Hall, and the Commons with their managers seated the proceeding commenced. Mr. Hastings was called into court; and as soon as he had pled in the usual form, he was ordered to withdraw, while his judges determined on his case.' A London paper's report of the judgment.",
      role='report', words=55, dateline=True,
      head=r'(?:W\s?ESTMINSTER\s+H\s?ALL\.?\s*)?J\s?UDGMENT\s+OF\s+M\s?R\.?\s+H\s?ASTINGS\.?\s*',
      core=[r'A\s?BOUT\s+(?:one|nine)\s+o[\'’]?\s?clock,?\s+the\s+[Ll]ords\s+being\s+come'],
      first="A London report of the Lords' judgment on Mr. Hastings in Westminster Hall.",
      what="the London report of Mr. Hastings's judgment",
      printings=[k('GUS', '06-12', 3), k('PG', '06-20', 3), k('NHG', '06-23', 3), k('AHL', '06-25', 2)]),
 dict(id='boston-unwarrantable-proceedings-a-vessel-burned-at-the-long-wharf-june-1795', kind='message_group',
      label="Boston, 24 June 1795, 'Unwarrantable Proceedings': a Boston paper's account of the burning on Saturday night of a vessel said to be a privateer",
      definition="Printings of a Boston paragraph of 24 June 1795 headed 'Unwarrantable Proceedings': 'To record any transaction which reflects disgrace upon our fellow citizens, is a very disagreeable task—But silently to pass over the unlawful and vicious proceeding on Saturday night, would argue a gross deficiency of duty. Its rise and progress we shall endeavor to narrate with justice and impartiality.' A Boston paper's account, in its own words of censure.",
      role='report', words=60, dateline=True,
      head=r'(?:U\s?NWARRANTABLE\s+P\s?ROCEEDINGS\.?\s*(?:\[\s*F\s?ACTS\.?\s*\]\s*)?)?',
      core=[r'T\s?O\s+record\s+any\s+tran\w+\s+which\s+re.{0,6}?f\w*\s+disgrace'],
      first="A Boston paper records the burning of a vessel on Saturday night as 'unlawful and vicious proceeding'.",
      what="the Boston account of the burning of the vessel",
      printings=[k('FM', '06-26', 3), (k('GUS', '06-29', 3), {'field': 'ca_ocr_text', 'head': r'B\s?OSTON,?\s+June\s+24\.?\s*I?>?\s*UMIT\s+ARRANT\s+ABLR\s+PROCS.\w*\.?\s*\[\s*facts\.?\s*\]\s*e?\s*'}), k('NHG', '06-30', 2), k('AHL', '07-02', 2), k('EAG', '07-13', 1)]),
 dict(id='treaty-of-amity-commerce-and-navigation-with-great-britain-november-1794', kind='document_group',
      label="The treaty of amity, commerce and navigation between Great Britain and the United States, concluded at London on 19 November 1794 (Mr. Jay's treaty)",
      definition="Printings of the treaty, as the papers print it in July and August 1795: its preamble and 'Article I. There shall be a firm, inviolable and universal peace, and a true and sincere friendship between his Britannick Majesty, his heirs and successors, and the United States of America'. The Patowmac Guardian's printing, whose opening was in an issue that does not survive, and commentaries that quote its articles are not counted (C-06, C-07). The treaty itself, as the papers print it.",
      role='published_document', words=60, dateline=False,
      head=r'T\s?REATY(?:,?\s*&c\.?|\s+OF\s+A\s?MITY,?\s+C\s?OMMERCE,?\s+(?:AND|and)\s+N\s?AVIGATION,?\s+BETWEEN\s+H\s?IS\s+B\s?RITANNI\w*\s+M\s?AJESTY,?\s+AND\s+THE\s+U\s?NITED\s+S\s?TATES\s+OF\s+A\s?MERICA)\.?\s*',
      core=[r'H\s?IS\s+B\s?ritann\w*\s+M\s?ajesty\s+and\s+the\s+United\s+States\s+of\s+America,?\s+being\s+desirous'],
      first="The text of the treaty of amity, commerce and navigation between Great Britain and the United States.",
      what="the treaty with Great Britain",
      printings=[k('NHG', '07-14', 1), k('FM', '07-24', 1), k('EAG', '07-27', 1), k('KG', '08-01', 1)]),
 # ---- October to December: war with Holland, the schooner from Lake Erie, Commodore Warren ----
 dict(id='london-war-with-holland-august-1795', kind='message_group',
      label="London, August 1795, 'War with Holland': 'What was foreseen by many a long time ago, seems now to be quickly approaching—a state of actual hostilities between this country and Holland'",
      definition="Printings of a London paragraph of 21 or 22 August 1795 headed 'War with Holland': 'What was foreseen by many a long time ago, seems now to be quickly approaching—a state of actual hostilities between this country and Holland. That the Dutch have a fleet at sea, is now fully confirmed by the following notice which was yesterday stuck up at Lloyd's Coffee-House'. A London paper's report.",
      role='report', words=55, dateline=False,
      head=r'(?:W\s?AR\s+with\s+H\s?OLLAND[!.]?\s*)?(?:L\s?ONDON,?\s+)?A\s?UG(?:UST|\.)?\.?\s+2[12]\.?\s*(?:W\s?AR\s+with\s+H\s?OLLAND[!.]?\s*)?',
      core=[r'W\s?HAT\s+was\s+foreseen\s+by\s+many\s+a\s+long\s+time\s+ago'],
      first="A London paper reports that a state of actual hostilities with Holland is approaching, a Dutch fleet being at sea.",
      what="the London paragraph 'War with Holland'",
      printings=[k('FM', '10-16', 1), (k('NHG', '10-20', 2), {'stop': r'FOR\s+THE\s+GAZETTE'}), k('AHL', '10-22', 1), k('EAG', '10-26', 2)]),
 dict(id='philadelphia-the-schooner-white-fish-from-lake-erie-november-1795', kind='message_group',
      label="Philadelphia, 12 November 1795: 'On Tuesday last arrived here, after a passage of 7 weeks, the schooner White Fish, built last summer at Presqu'Isle on Lake Erie'",
      definition="Printings of a Philadelphia paragraph of 12 November 1795: 'On Tuesday last arrived here, after a passage of 7 weeks, the schooner White Fish, built last summer at Presqu'Isle on Lake Erie. The tediousness of the voyage was owing to the inclemency of the weather. She is only 17 and 1-2 feet keel, and 5 feet 7 inches beam.' A Philadelphia paper's report.",
      role='report', words=50, dateline=True,
      core=[r'O\s?N\s+Tuesday\s+last\s+arrived\s+here,?\s+after\s+a\s+passage\s+of\s+(?:7|seven)\s+weeks'],
      first="The schooner White Fish, built on Lake Erie, arrives at Philadelphia after a passage of seven weeks.",
      what="the paragraph on the schooner White Fish",
      printings=[(k('GUS2', '11-12', 3), {'head': r'P\s?hiladelphia,?\s+T\s?HURSDAY\s+E\s?VENING,?\s+N\s?OVEMBER\s+12,?\s*1795\.?\s*'}), k('NHG', '12-01', 2), k('FM', '12-11', 2), k('KG', '12-12', 3)]),
 dict(id='commodore-warrens-dispatches-from-quiberon-bay-september-1795', kind='message_group',
      label="London, September 1795: Commodore Sir John Borlase Warren's dispatches from Quiberon Bay, received at the Admiralty Office",
      definition="Printings of a London report of September 1795, in two forms counted together (C-02): 'On Saturday dispatches were received at the Admiralty Office, from Commodore Sir John B. Warren, dated Quiberon Bay, September 9' (the Gazette of the United States and the Kentucky Gazette) and 'Dispatches were received the 15th Sept. at the Admiralty-Office from Commodore Sir John Bourlace Warren, dated Quiberon Bay' (the New-Hampshire Gazette and the Federal Mirror). A London report of the commodore's dispatches.",
      role='report', words=55, dateline=True,
      core=[r'(?:O\s?N\s+Saturday\s+)?[Dd]ispatches\s+were\s+received\s+(?:the\s+15th\s+Sept\.?\s+)?at\s+the\s+Admiralty[\s\-]*Office,?\s+from\s+Commodore'],
      first="A London report of Commodore Warren's dispatches from Quiberon Bay.",
      what="the report of Commodore Warren's dispatches",
      printings=[k('GUS2', '11-19', 2), k('NHG', '11-24', 2), k('FM', '12-04', 2), k('KG', '12-26', 3)]),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary (as for 1776, 1807, 1808, 1809, 1797 and 1800): "BOSTON, Nov. 30th, 1802."
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}[\s\-]+){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:(?:\s|\s?-\s?)[A-Z][A-Za-z'\-]+){0,2})(?:,?\s*[\(\[][A-Za-z ,.]+[\)\]])?"
# As for 1774 (24 November): also a year after a stop ('Oct. 16. 1774.') and a date printed alone ('December 5.').
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”’)]\s+)((?:" + PLACE + r",?\s+)?" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:[,.]?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


def item_start(text, cores, dateline=True, back=False, head=None):
    for core in cores:
        m = re.search(core, text, re.I | re.S)
        if m:
            start = m.start()
            if head:   # a heading that ends directly before the core: the excerpt starts with it
                window = text[max(0, start-420):start]
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


# Openings compared side by side on 24 November 2026 (the 1780 review's cross-year check): where one printing of a group
# carried the heading printed above the item and another did not, the heading patterns above were widened, and the printings
# below take their own start. KEEP_WORDS keeps the end of every excerpt whose start moved where the scan check read it: it is
# the number of words from the new start to the old end.
OPENING_FIXES = {
}
KEEP_WORDS = {
}


def printings():
    for s in STORIES:
        for p in s.get('printings', []):
            key, over = (p, {}) if isinstance(p, str) else p
            over = dict(over, **OPENING_FIXES.get((s['id'], key), {}))
            if (s['id'], key) in KEEP_WORDS:
                over['words'] = KEEP_WORDS[(s['id'], key)]
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
            problems.append((s['id'], key, 'page not in the 1795 pages'))
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
        r['id'] = f'S95-{n:03}'
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
               'admission_rule': 'Reviewed 1795 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1795/'
    return {
        'ledger_id': 'ledger:stories-1795', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1795', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1795, and of 1794 where they reach the 1795 pages (long-running ones '
                   'included), every item in 3 or more papers compared by machine with every page and counted again by its opening, a sweep of '
                   'word-for-word passages shared by 4 or more papers for short items the families miss, phrase searches on all 1,668 pages of '
                   '1795 in both transcriptions, reading of every hit, and scan checks of each admitted passage, by the thin-year rule (Y-THIN, '
                   'as amended on 23 November 2026: an item printed by more than half of the papers that survive for its weeks, and by at '
                   'least 4, is eligible; the items printed by every paper that survives for their weeks are admitted, and the other eligible '
                   'items are chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1794.json': 'retrieval_candidates', d+'count_1795.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1795.py': 'ledger_code', 'work/archive_data/ledgers/stories_1795_review.json': 'scan_review',
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
