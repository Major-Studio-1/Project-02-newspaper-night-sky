"""Write ledgers/stories_1798.json: reviewed stories of 1798, round one.

1798 is read by the thin-year rule the owner chose on 23 November 2026 (docs/rules-and-exceptions.md, Y-THIN), as amended the
same night (the owner's choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the
newspapers that survive for its weeks, and by at least 4 newspapers; digests are not. The newspapers that survive for an item's
weeks are those with an eligible issue between its first and last printing, and at least in the three weeks from its first
printing. As in R-01, the eligible items printed by every newspaper that survives for their weeks are admitted, and the other
eligible items are chosen to cover the months and the kinds of news (a target, not a quota); one affair's items are handled as
in X-1800-01. Sub-stories (C-01), private persons (R-04) and the list of items read and not admitted (R-03) apply as in every
year (outputs/story_discovery_1798/README.md).

The automatic families first printed in 1798 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1797 over the 1798 pages
(items_from_1797.json); every item in 3 or more papers was counted by machine, by about 100 words of its text from the finder's
position, over every page, and the counts were joined into documents; the candidates were counted again by about 70 words from
their own opening, the acts of Congress by their first section (counts_1798.json). The 1798 pages are those whose issue the
data release dates to 1798 (work/year_search_pages.py 1798 ... --printed-dates). 1798 has 8 catalogue series, which are 8
papers: the Gazette of the United States (Philadelphia), the Kentucky Gazette, the New Hampshire Gazette, the Mirror (Concord),
the Gazette (Portland, from April), the Virginia Argus (10 issues), the Wilmington Mercury (September and October) and the
Eagle (Hanover, 2 issues).

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1798_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1798.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1798/search_pages.json).
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1798'
D = PROJECT/'outputs/story_discovery_1798'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1798_review.json'
OUT = HERE/'stories_1798.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

LCCN = {'GUS': 'sn83025881', 'KG': 'sn82014782', 'NHG': 'sn83025588', 'MIR': 'sn83025525', 'PGZ': 'sn83045634', 'VA': 'sn84024710',
        'WM': 'sn88053099', 'EAG': 'sn90062451'}
PAPER = {'sn83025881': 'The Gazette of the United States', 'sn82014782': 'The Kentucky Gazette', 'sn83025588': 'The New Hampshire Gazette',
         'sn83025525': 'The Mirror', 'sn83045634': 'The Gazette (Portland)', 'sn84024710': 'The Virginia Argus',
         'sn88053099': 'The Wilmington Mercury', 'sn90062451': 'The Eagle'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, filed date (MM-DD in 1798), page and edition."""
    return f'{LCCN[paper]}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()
AGAIN = {'note': 'Printed again.'}
GS = r'Gentlemen\s+of\s+the\s+Senat\w*,?\s+and\s+\W*Gentlemen\s+of\s+the\s+Hou\w*\s*of\s+Repre\w+\W+'
ENVOYS = 'the-envoys-dispatches-the-presidents-messages-march-and-april-1798'
GERRY = 'mr-gerry-and-the-french-minister-of-foreign-relations-july-1798'
NILE = 'the-action-off-the-mouth-of-the-nile-august-1798'
SPEECH = 'the-presidents-speech-of-8-december-1798-and-the-senates-answer'
# Story groups ('printings' lists each printing's page; a tuple adds overrides for that printing: core, role, field, note,
# words, dateline, head, back, stop), as in make_stories_1778.py. A parent ('context_group') lists its children.
STORIES = [
 dict(id='havre-letter-of-6-november-1797-a-project-of-a-descent-on-england', kind='document_group',
      label="A letter from Havre of 6 November 1797: 'a project of an absolute descent on England'",
      definition="Printings of an extract of a letter: 'Extract of a letter from a gentleman in Havre to a respectable mercantile house in this city, received by the Rosetta. Havre, 6th Nov. 1797. There is now a project of an absolute descent on England! The immortal Buonaparte is appointed commander in chief, on this expedition'. A letter of an unnamed writer, at second hand, as the papers printed it.",
      role='report', words=50, dateline=False,
      core=[r'(?:Extract\s+of\s+a\s+letter|Extra\W+A\s+letter)\s+from\s+a\s+gentleman\s+in\s+Havre'],
      first="A letter from Havre of 6 November 1797 on a descent on England.",
      what="the letter from Havre",
      printings=[k('GUS', '01-04', 3), k('VA', '01-12', 3), k('MIR', '01-16', 3), (k('KG', '01-31', 3), {'head': r'January\s+5\.\s*'})]),
 dict(id='paris-report-of-what-the-directory-demands-of-the-american-envoys-november-1797', kind='document_group',
      label="Paris, 10 November 1797: a report of what the Directory demands of the American envoys",
      definition="Printings of a paragraph of the Paris news of 10 November: 'It is said that the Directory demands of the American Plenipotentiaries: first, whether their instructions allow them to give satisfaction for the outrage offered to the French government, in the speech the President made on the 16th of May last, at the opening of Congress? And secondly, whether they are authorised to re-establish the respective position in which the states stood in 1778'. A report at second hand ('it is said'), as the papers printed it.",
      role='report', words=50, dateline=True, head=r'(?:PARIS,?\s+)?Nov\w*\.?\s+10\.\s*',
      core=[r'It\s+is\s+said,?\s+that\s+the\s+Directory\s+demands\s+of\s+the\s+American\s+Plenipotentiaries'],
      first="Paris, 10 November 1797: what the Directory demands of the American envoys.",
      what="the Paris report of the Directory's demands",
      printings=[k('VA', '01-12', 2), k('GUS', '01-15', 2), k('MIR', '01-30', 3), k('NHG', '01-31', 2), k('KG', '02-14', 3)]),
 dict(id='the-senate-on-a-motion-to-repeal-the-stamp-duty-january-1798', kind='document_group',
      label="The Senate, January 1798: the yeas and nays on Mr. Greene's motion for leave to bring in a bill to repeal the stamp duty",
      definition="Printings of a report of the Senate's proceedings: 'Yesterday in the Senate of the United States, upon a motion for leave to bring in a bill to repeal the law laying a duty on stamped vellum, &c. made by Mr. Greene, a member from Rhode-Island, in pursuance of instructions from that State—the yeas and nays were as follows'. A report of Congress's proceedings, with the senators' names as the papers printed them.",
      role='report', words=50, dateline=True, head=r'(?:STAMP\s+ACT\.|January\s+19\.|IN\s+SENATE\W+JAN\.?\s+20\.)\s*',
      core=[r'(?:Y\w+day|On\s+Thursday)\s+in\s+the\s+Senate\s+of\s+the\s+United\s+States,?\s+upon\s+a\s+motion',
            r'upon\s+a\s+motion\s+(?:for\s+leave\s+)?to\s+bring\s+in\s+a\s+bill\s+to\s+repeal\s+the\s+law\s+laying\s+a\s+duty'],
      first="The Senate, January 1798: the vote on repealing the stamp duty.",
      what="the report of the Senate's vote on the stamp duty",
      printings=[k('GUS', '01-19', 3), k('VA', '01-30', 2), k('NHG', '01-31', 3), k('MIR', '02-06', 2), k('KG', '03-14', 3)]),
 dict(id=ENVOYS, kind='context_group',
      label="The envoys' dispatches, March and April 1798: the President's messages to Congress and the Treasury's circular",
      children=['president-message-of-5-march-1798-the-first-dispatches-from-the-envoys', 'president-message-of-19-march-1798-on-the-dispatches-from-the-envoys',
                'treasury-circular-of-21-march-1798-to-the-collectors-of-the-customs', 'president-message-of-3-april-1798-laying-the-instructions-and-dispatches-before-congress'],
      definition="The President's messages to both Houses of 5 March (the first dispatches from the envoys at Paris), 19 March (the dispatches examined) and 3 April (the instructions and dispatches laid before Congress), and the Treasury's circular of 21 March to the collectors of the customs on vessels sailing armed: one affair's separate public acts (X-1800-01), as the papers printed them."),
 dict(id='president-message-of-5-march-1798-the-first-dispatches-from-the-envoys', parent=ENVOYS, kind='document_group',
      label="The President's message of 5 March 1798 on the first dispatches from the envoys at Paris",
      definition="Printings of the message: 'Gentlemen of the Senate and Gentlemen of the House of Representatives, The first dispatches from our envoys extraordinary since their arrival at Paris, were received at the Secretary of State's office, at a late hour the last evening—They are all in a character, which will require some days to be deciphered, except the last which is dated the 8th of January, 1798'. The President's own words, printed with the envoys' letter of 8 January.",
      role='published_document', words=50, dateline=False,
      core=[GS + r'THE\s+fir\w+\s+dispatches\s+from\s+our\s+envoys', r'THE\s+fir\w+\s+dispatches\s+from\s+our\s+envoys\s+extraordinary'],
      first="The President's message of 5 March 1798 on the first dispatches.",
      what="the President's message of 5 March 1798",
      printings=[k('GUS', '03-05', 3), (k('GUS', '03-06', 2), AGAIN), k('MIR', '03-20', 3), k('NHG', '03-21', 2), k('KG', '04-04', 2)]),
 dict(id='president-message-of-19-march-1798-on-the-dispatches-from-the-envoys', parent=ENVOYS, kind='document_group',
      label="The President's message of 19 March 1798 on the dispatches from the envoys",
      definition="Printings of the message: 'THE dispatches, from the Envoys Extraordinary of the United States to the French Republic, which were mentioned in my message, to both Houses of Congress, of the fifth instant, have been examined and maturely considered. While I feel a satisfaction in informing you, that their exertions, for the adjustment of the differences, between the two nations, have been sincere and unremitted, it is incumbent on me, to declare, that I perceive no ground of expectation, that the objects of their mission, can be accomplished, on terms compatible, with the safety, honor, or the essential interests of the nation'. The President's own words.",
      role='published_document', words=50, dateline=False,
      head=r'(?:PRESIDENT\W?S\s+Me\w+age|MESSAGE\s+TO\s+CONGRESS)\.\s*',
      core=[GS + r'THE\s+dispatches,?\s+from\s+the\s+Envoys\s+Extraordinary', r'THE\s+dispatches,?\s+from\s+the\s+Envoys\s+Extraordinary\s+of\s+the\s+United\s+States'],
      first="The President's message of 19 March 1798 on the envoys' dispatches.",
      what="the President's message of 19 March 1798",
      printings=[k('GUS', '03-19', 3), k('MIR', '04-03', 3), k('NHG', '04-04', 2), k('PGZ', '04-16', 2), k('KG', '04-18', 2)]),
 dict(id='treasury-circular-of-21-march-1798-to-the-collectors-of-the-customs', parent=ENVOYS, kind='document_group',
      label="The Treasury's circular of 21 March 1798 to the collectors of the customs: vessels no longer restrained from sailing armed",
      definition="Printings of the circular: 'Treasury Department, March 21. SIR, IT has been determined by the President of the United States, that under present circumstances, it has become necessary to modify the instructions issued from this department on the 8th day of April 1797, in such manner as no longer to restrain vessels of the United States from sailing in an armed condition, when destined to be employed in a regular and lawful commerce'. The Treasury's own words.",
      role='published_document', words=50, dateline=False,
      head=r'\[?C\s?I\s?R\s?C\s?U\s?L\s?A\s?R\W+(?:to\s+the\s+)?Co\w+\s+of\s+the\s+Cu\w+\W*',
      core=[r'Tre\w+\s+Department,?\s+March\W*2\w\W+SIR\W+IT\s+has\s+been\s+determined', r'IT\s+has\s+been\s+determined\s+by\s+the\s+Pres\w*\s*\w*\s+of\s+the\s+United\s+States,?\s+that\s+under'],
      first="The Treasury's circular of 21 March 1798 to the collectors of the customs.",
      what="the Treasury's circular of 21 March 1798",
      printings=[k('GUS', '03-22', 3), k('MIR', '04-10', 3), k('NHG', '04-11', 2), k('PGZ', '04-16', 2), k('KG', '04-18', 2)]),
 dict(id='president-proclamation-of-23-march-1798-for-a-day-of-humiliation-fasting-and-prayer', kind='document_group',
      label="The President's proclamation of 23 March 1798 for a day of solemn humiliation, fasting and prayer",
      definition="Printings of the proclamation: 'BY THE President of the United States of America, A PROCLAMATION. As the safety and prosperity of nations ultimately and essentially depend on the protection and the blessing of Almighty God; and the national acknowledgment of this truth is not only an indispensable duty which the people owe to him, but a duty whose natural influence is favorable to the promotion of that Morality and Piety, without which social Happiness cannot exist'. The President's own words.",
      role='published_document', words=50, dateline=False,
      core=[r'By\s+THE\s+President\s+of\s+the\s+United\s+States\W+of\s+America\W+A\s+P\s?R\s?O\s?C\s?L\s?A\s?M\s?A\s?T\s?I\s?O\s?N\W+A?S\s+the\s+[sf]a[fs]ety',
            r'A\s+P\s?R\s?O\s?C\s?L\s?A\s?M\s?A\s?T\s?I\s?O\s?N,?\s+By\s+THE\s+PRESIDENT\s+of\s+the\s+United\s+States\s+of\s+America\W+AS\s+the\s+safety',
            r'A?S\s+the\s+[sf]a[fs]ety\s+and\s+prosperity\s+of\W+(?:A\s+)?nations\s+ultimately'],
      first="The President's proclamation of 23 March 1798 for a day of fasting.",
      what="the President's proclamation of a fast",
      printings=[k('GUS', '03-27', 3), k('MIR', '04-10', 2), (k('NHG', '04-11', 2), {'head': r'United\s+States\W?\s+Fa\w+\.\s*'}), k('PGZ', '04-16', 2)]),
 dict(id='president-message-of-3-april-1798-laying-the-instructions-and-dispatches-before-congress', parent=ENVOYS, kind='document_group',
      label="The President's message of 3 April 1798 laying the envoys' instructions and dispatches before Congress",
      definition="Printings of the message: 'In compliance with the request of the House of Representatives, expressed in their resolution of the 2d of this month, I transmit to both Houses the instructions to and dispatches from the Envoys Extraordinary of the United States to the French Republic, which were mentioned in my message of the 19th of March last, omitting only some names, and a few expressions descriptive of the persons'. The President's own words.",
      role='published_document', words=50, dateline=False,
      core=[GS + r'\W*In\s+compliance\s+with\s+the\s+requ\w+', r'In\s+compliance\s+with\s+the\s+requ\w+\s+of\s+the\s+House\s+of\s+Representatives,?\s+expres'],
      first="The President's message of 3 April 1798 with the envoys' dispatches.",
      what="the President's message of 3 April 1798",
      printings=[k('GUS', '04-04', 2), k('NHG', '04-18', 3), k('MIR', '04-24', 2), k('KG', '04-25', 2)]),
 dict(id='the-senate-a-motion-on-removing-aliens-april-1798', kind='document_group',
      label="The Senate, April 1798: a motion for a committee on removing aliens who may be dangerous, and on returns of aliens landed",
      definition="Printings of a motion made in the Senate: 'Resolved, That a committee be appointed to consider whether any and what provision ought to be made by law, for removing from the territory of the United States, such aliens born, not entitled by the constitution and laws thereof, to the rights of citizenship, as may be dangerous to its peace and safety'. A motion in Congress, as the papers printed it.",
      role='published_document', words=50, dateline=False,
      core=[r'Resolved\W+that\s+a\s+committee\s+be\s+appointed\s+to\s+con\w+\s+whether\s+any,?\s+and\s+what\s+provision',
            r'that\s+a\s+committee\s+be\s+appointed\s+to\s+consider\s+whether\s+any,?\s+and\s+what\s+provision\s+ought\s+to\s+be\s+made\s+by\s+law'],
      first="The Senate, April 1798: a motion on removing aliens.",
      what="the Senate's motion on aliens",
      printings=[k('NHG', '05-08', 2), (k('PGZ', '05-14', 3), {'back': True}), k('MIR', '05-15', 2), k('KG', '05-16', 2)]),
 dict(id='berne-5-march-1798-general-schauenburgs-letter', kind='document_group',
      label="Berne, 5 March 1798: General Schauenburg's letter on the French troops' entry into the city",
      definition="Printings of a letter: 'Copy of a letter from General Schauenburg, commander of the French troops. Berne, March 5. We yesterday entered this city. An engagement took place, which continued for three hours, and was on both sides obstinately contested. The Swissers have lost many men. We have taken 20 cannon and 9 colours'. The French commander's own account, as the papers printed it.",
      role='published_document', words=50, dateline=False,
      core=[r'Copy\s+of\s+a\s+letter\s+from\s+Gen\w*\.?\s+Schauenb\w+rg'],
      first="Berne, 5 March 1798: General Schauenburg's letter.",
      what="General Schauenburg's letter from Berne",
      printings=[k('GUS', '05-04', 3), k('NHG', '05-15', 3), k('MIR', '05-22', 3), k('KG', '05-23', 2)]),
 dict(id='amsterdam-20-march-1798-the-american-consuls-letter-on-the-ship-america', kind='document_group',
      label="Amsterdam, 20 March 1798: the American consul's letter that the ship America, brought in by a French cruiser, has been released",
      definition="Printings of a letter: 'Consular Office of the United States of America, Amsterdam, March 20. Mr. Benjamin Russell, Boston, SIR, I AVAIL myself of the first opportunity to acquaint you that the ship America, Capt. Henshaw, from New-York, lately brought in here by a French cruiser, has been immediately released by the Consul of that nation'. The consul's own words, from a Boston paper.",
      role='published_document', words=50, dateline=False, head=r'\(?AUTHENTIC\.\)?\s*',
      core=[r'Consular\s+Office\s+of\s+the\s+United\s+States\s+of\s+America,?\s+Amsterdam', r'I\s+avail\s+myself\s+of\s+the\s+first\s+opportunity\s+to\s+acquaint\s+you\s+that\s+the\s+ship\s+America'],
      first="Amsterdam, 20 March 1798: the consul's letter on the ship America.",
      what="the consul's letter from Amsterdam",
      printings=[k('GUS', '05-21', 3), (k('PGZ', '05-21', 2), {'core': [r'Mr\.?\s+Bourne,?\s+Consul\s+at\s+Amsterdam'], 'head': r'Authentic\s+from\s+Amsterdam\.\s*'}), k('NHG', '05-22', 3), k('KG', '06-13', 2)]),
 dict(id='act-more-effectually-to-protect-the-commerce-and-coasts-may-1798', kind='document_group',
      label="The act of May 1798 more effectually to protect the commerce and coasts of the United States",
      definition="Printings of the act: 'AN ACT More effectually to protect the Commerce and Coasts of the United States. WHEREAS armed vessels, sailing under authority, or pretence of authority, from the Republic of France, have committed depredations on the commerce of the United States, and have recently captured the vessels and property of citizens thereof, on and near the coasts'. An act of Congress, as the papers printed it; the Senate's bill, printed earlier in other words ('armed vessels belonging to the Republic of France'), is counted apart (X-1809-07).",
      role='published_document', words=50, dateline=False,
      core=[r'AN\s+ACT,?\s+more\s+effectually\s+to\s+protect\s+the\s+Commerce\s+(?:and|&)\s+Coasts\s+of\s+the\s+U'],
      first="The act of May 1798 to protect the commerce and coasts.",
      what="the act to protect the commerce and coasts",
      printings=[k('GUS', '05-28', 3), (k('GUS', '05-30', 2), AGAIN), (k('PGZ', '06-11', 2), {'head': r'Captures\s+and\s+Reprisals!\s*'}), k('KG', '06-13', 3), (k('NHG', '06-19', 2), {'head': r'IMPORTANT\s+Laws\s+of\s+the\s+United\s+States\.\s*'})]),
 dict(id='the-house-6-june-1798-mr-fosters-resolutions-on-the-treaties-with-france', kind='document_group',
      label="The House, 6 June 1798: Mr. Dwight Foster's resolutions that the French Republic has violated the treaties",
      definition="Printings of the resolutions laid before the House of Representatives: 'WHEREAS the French Republic, regardless of those principles of good faith which ought to ensure a due observance of treaties, have, in various instances, violated the express stipulation of the treaties heretofore made or subsisting between the United States and the French nation ... Resolved, That it is expedient to make a legislative declaration'. Resolutions moved in Congress, as the papers printed them; Mr. Blount's resolutions in the same words on Great Britain are another text (C-07).",
      role='published_document', words=50, dateline=False,
      core=[r'WHEREAS,?\s+the\s+French\s+Republic,?\s+regardless\s+of\s+those\s+principles\s+of\s+good\s+faith'],
      first="The House, 6 June 1798: Mr. Foster's resolutions on the treaties with France.",
      what="Mr. Foster's resolutions",
      printings=[k('GUS', '06-06', 3), (k('GUS', '06-07', 3), AGAIN), k('VA', '06-15', 2), k('PGZ', '06-18', 2), k('NHG', '06-19', 2), k('KG', '06-27', 2)]),
 dict(id='president-message-of-21-june-1798-on-general-marshalls-arrival', kind='document_group',
      label="The President's message of 21 June 1798 on General Marshall's arrival, communicating Mr. Gerry's letter",
      definition="Printings of the message: 'WHILE I congratulate you on the arrival of General Marshall, one of our late Envoys Extraordinary to the French Republic, at a place of safety, where he is justly held in honor, I think it my duty to communicate to you a letter received by him from Mr. Gerry, the only one of the three who has not received a congé'. The President's own words.",
      role='published_document', words=50, dateline=False,
      core=[GS + r'\W*WHILE\s+[Il1]\s+congratulate', r'WHILE\s+[Il1]\s+congratulate\s+y\w+\s+on\s+the\s+arrival\s+of\s+G\w+\.?\s+Ma\w+'],
      first="The President's message of 21 June 1798 on General Marshall's arrival.",
      what="the President's message of 21 June 1798",
      printings=[k('VA', '06-29', 1), (k('PGZ', '07-02', 2), {'head': r'Q\w+\s+of\s+the\s+Senate,?\s+and\s+Gentlemen\s+of\s+the\s+H\w+\s+of\s+R\S+\W*'}), k('NHG', '07-03', 2), k('KG', '07-11', 2)]),
 dict(id='the-delaware-sloop-of-war-captain-decatur-and-a-french-privateer-july-1798', kind='document_group',
      label="Philadelphia, July 1798: reports that the Delaware sloop of war, Captain Decatur, has captured a French privateer schooner off Egg Harbour",
      definition="Printings of a Philadelphia paragraph in two forms: 'We have the satisfaction to announce to our readers that the Delaware sloop of war, capt. Decatur, (who only went out to sea on Friday) on Saturday evening captured a French privateer schooner of 12 guns and 70 men, close in with Egg-Harbour', and 'Yesterday Capt. Decatur, of the United States Sloop Delaware arrived at the Navy-Office. He informs, that the Delaware sailed on Friday last, and on Saturday evening captured a French privateer schooner of 12 guns and 70 men, close in with Egg Harbour'. Reports at second hand, in the papers' words.",
      role='report', words=50, dateline=True,
      core=[r'We\s+have\s+the\s+satisfaction\s+to\s+announce\s+to\s+our\s+readers,?\s+that\s+the\s+Delaware', r'Yesterday\s+Capt\.?\s+Decatur,?\s+of\s+the\s+United\s+States\s+[Ss]loop\s+Delaware',
            r'The\s+Delaware\s+sloop\s+of\s+war,?\s+capt\.?\s+Decatur'],
      first="Philadelphia, July 1798: the Delaware captures a French privateer.",
      what="the report of the Delaware's capture",
      printings=[k('GUS', '07-09', 3), (k('NHG', '07-17', 3), {'head': r'A\s+French\s+Pirate\s+captured\.\s+\[No\.?\s*1\.\]\s+PHILADELPHIA,?\s+JULY\s+9\.\s*'}),
                 (k('PGZ', '07-23', 3), {'head': r'Particulars\s+of\s+the\s+First\s+Capture:\s+Being\s+the\s+first\s+Installment\s+to\s+Talleyrand\W?s\s+Douceur!\s+From\s+Philad\.\s+July\s+9\.\s*'}),
                 (k('MIR', '07-24', 3), {'head': r'PHILADELPHIA,?\s+JULY\s+9\.\s+A\s+French\s+Pirate\s+Nabb\W?d\.\s+\[No\.?\s*1\.\]\s*'}), (k('KG', '08-01', 3), {'head': r'July\s+12\.\s*'})]),
 dict(id='president-message-of-18-july-1798-with-general-washingtons-letter', kind='document_group',
      label="The President's message to the Senate of 18 July 1798 with General Washington's letter accepting the command of the army",
      definition="Printings of the message: 'BELIEVING that the letter received this morning from General WASHINGTON will give high satisfaction to the Senate, I transmit them a copy of it, and congratulate them and the public on this great event, the General's acceptance of his appointment, as Lieutenant General and Commander in Chief of the army', with the General's letter from Mount-Vernon of 13 July. The President's and the General's own words.",
      role='published_document', words=50, dateline=False, head=r'S\s?E\s?N\s?A\s?T\s?E\s+OF\s+THE\s+UNITED\s+STATES[.,]?\s+JULY\s+18,?\s+1798\.\s*',
      core=[r'Gentlemen\s+of\s+the\s+Senate\W+BELIEVING\s+that\s+the\s+letter\s+received\s+this\s+morning'],
      first="The President's message of 18 July 1798 with General Washington's letter.",
      what="the President's message of 18 July 1798",
      printings=[k('PGZ', '07-30', 2), (k('MIR', '07-31', 2), {'head': r'GLORIOUS\s+TIDINGS!\s+S\s?E\s?N\s?A\s?T\s?E\s+OF\s+THE\s+UNITED\s+STATES[.,]?\s+JULY\s+18,?\s+1798\.\s*'}), k('NHG', '07-31', 1), k('KG', '08-08', 2)]),
 dict(id='act-for-the-punishment-of-certain-crimes-sedition-july-1798', kind='document_group',
      label="The act of 14 July 1798 in addition to the act for the punishment of certain crimes against the United States (sedition)",
      definition="Printings of the act: 'An Act in addition to the act, entitled \"An act for the punishment of certain crimes against the United States.\" Sec. 1. BE it enacted by the Senate and House of Representatives of the United States of America, in Congress assembled, That if any persons shall unlawfully combine or conspire together, with intent to oppose any measure or measures of the government of the United States, which are or shall be directed by proper authority'. An act of Congress, as the papers printed it; the Senate's bill, printed earlier in other words ('whether citizens or aliens'), is counted apart (X-1809-07), and essays quoting the act do not count (C-07).",
      role='published_document', words=50, dateline=False, head=r'S\s?E\s?D\s?I\s?T\s?I\s?O\s?N\s+B\s?I\s?L\s?L[;,]?\s+Or\s+a\s+GAG\s+for\s+JACOBINISM[.!]\s*',
      core=[r'An\s+Act,?\s+in\s+addition\s+to\s+(?:the|an)\s+act,?\s+entitled,?\W+an\s+act\s+for\s+the\s+punishment\s+of\s+certain\s+crimes'],
      first="The act of 14 July 1798 on sedition.",
      what="the act on sedition",
      printings=[k('PGZ', '07-30', 2), k('NHG', '08-07', 1), k('KG', '08-08', 1), k('MIR', '09-04', 2), k('GUS', '11-30', 2)]),
 dict(id='french-papers-of-june-1798-on-the-envoys-dispatches', kind='document_group',
      label="June 1798: a report from French papers that the French government has received the American envoys' dispatches, with Mr. Gerry's and M. Talleyrand's letters",
      definition="Printings of a paragraph: 'By the Clef du Cabinet des Souverains, of the 10th June, it appears that the French government had received an English paper containing the dispatches from the American envoys to the President of the U. S. which were communicated by the President to Congress the 3d April. In consequence thereof the following letters passed between Mr. Gerry & M. Talleyrand'. A report from French papers, at second hand.",
      role='report', words=50, dateline=False, back=True,
      core=[r'it\s+appears\s+that\s+the\s+French\s+government\s+had\s+received\s+an\s+English\s+paper'],
      first="June 1798: French papers on the envoys' dispatches.",
      what="the report from French papers",
      printings=[k('PGZ', '08-27', 2), k('NHG', '08-28', 3), k('GUS', '08-30', 3), k('MIR', '09-04', 3), k('KG', '09-19', 2)]),
 dict(id=GERRY, kind='context_group',
      label="Paris, July 1798: the French minister of foreign relations' letter to Mr. Gerry enclosing his passport, and Mr. Gerry's answer",
      children=['minister-of-foreign-relations-to-mr-gerry-12-july-1798', 'mr-gerrys-answer-to-the-minister-20-july-1798'],
      definition="The minister's letter of 12 July (24 Messidor) and Mr. Gerry's answer of 20 July, printed from London papers in September and October: one affair's separate public documents (X-1800-01), each in the writer's own words."),
 dict(id='minister-of-foreign-relations-to-mr-gerry-12-july-1798', parent=GERRY, kind='document_group',
      label="Paris, 12 July 1798: the French minister of foreign relations' letter to Mr. Gerry, enclosing his passport",
      definition="Printings of the letter: 'Letter, from the Minister of foreign relations, to Mr. Gerry, Envoy of the United States, enclosing him his Passports. As long, Sir, as I had room to flatter myself that I might fulfil the wishes of the Executive Directory, by endeavouring in concert with you'. The French minister's own words, in translation.",
      role='published_document', words=50, dateline=True, head=r'PARIS,?\s+(?:\(24\s+MESSIDOR\)\s+)?JULY\s+12[.,]\s*',
      core=[r'Letters?,?\s+from\s+the\s+Minister\s+of\s+Foreign\s+Relations,?\s+to\s+Mr\.?\s+Gerry'],
      first="Paris, 12 July 1798: the minister's letter to Mr. Gerry.",
      what="the minister's letter to Mr. Gerry",
      printings=[k('GUS', '09-29', 1), k('NHG', '10-02', 2), k('MIR', '10-08', 1), k('PGZ', '10-08', 1), k('EAG', '10-09', 2), k('KG', '10-24', 1)]),
 dict(id='mr-gerrys-answer-to-the-minister-20-july-1798', parent=GERRY, kind='document_group',
      label="Paris, 20 July 1798: Mr. Gerry's answer to the minister of foreign relations",
      definition="Printings of the letter: 'Citizen Minister, I RECEIVED on the 27th Messidor, your letter of the 24th, (the 12th July) on which permit me to make some observations. You alledge that in the United States the French Republic is accused of not wishing for peace'. Mr. Gerry's own words; most papers print it after his note of 25 July asking the minister to publish a translation of it (one publication, counted by the answer's opening, X-1810-01).",
      role='published_document', words=50, dateline=False,
      head=(r"(?:MR\.?\s+GERRY\W?S\s+ANSWER[.,]?\s+(?:To\s+the\s+(?:Minister\s+of\s+Foreign\s+Affairs\W?s?\s+Letter,?\s+of\s+the\s+24th\s+Messidor|letter\s+of\s+the\s+Minister\s+of\s+Foreign\s+Affairs)\.\s+)?"
            r"|Mr\.?\s+Gerry\W?s\s+answer\s+to\s+the\s+Minister\s+of\s+Foreign\s+Affairs\W?s?\s+Letter,?\s+of\s+the\s+24th\s+Messidor\.\s+)?(?:PARIS,?\s+JULY\s+20,?\s+'?(?:98|1798)\.\s*)?"),
      core=[r'C\w+\s+Minister,?\s+I\s+RECEIVED,?\s+on\s+the\s+27th\s+(?:of\s+)?Messidor'],
      first="Paris, 20 July 1798: Mr. Gerry's answer to the minister.",
      what="Mr. Gerry's answer",
      printings=[k('PGZ', '10-08', 1), k('NHG', '10-09', 1), k('VA', '10-12', 2), k('MIR', '10-15', 1), k('EAG', '10-16', 2), k('KG', '10-24', 2)]),
 dict(id='alexandria-letter-on-the-preparations-for-buonapartes-expedition-1798', kind='document_group',
      label="Alexandria, June 1798: a letter on the preparations made there for Buonaparte's expedition",
      definition="Printings of a letter from Alexandria, from a Paris paper: 'The magazines which have been forming here are all ready. We are taught to expect the arrival of 40,000 men; they now speak but of 20,000. The other 20,000 are to go by the Isle of Cyprus to Aleppo, and from thence to pass by the Euphrates to the Persian Gulf'. A letter of an unnamed writer, at second hand, as the papers printed it.",
      role='report', words=50, dateline=False,
      core=[r'The\s+(?:magazines|measures)\s+which\s+have\s+been\s+form\w+\s+here\s+are\s+all\s+ready', r'The\s+measures\s+which\s+have\s+been\s+adopt\w*\s+here\s+are\s+all\s+ready'],
      first="Alexandria, June 1798: the preparations for Buonaparte's expedition.",
      what="the letter from Alexandria",
      printings=[k('NHG', '10-09', 2), k('MIR', '10-15', 2), (k('PGZ', '10-15', 2), {'head': r'ALEXANDRIA\s+\(Egypt\)\s+JUNE\s+4\.'}), (k('VA', '10-16', 3), {'head': r'ALEXANDRIA,?\s+June\s+20\.\s*'}),
                 (k('KG', '11-07', 2), {'head': r'From\s+Alexandria,?\s+June\s+4\.\s*'})]),
 dict(id=NILE, kind='context_group',
      label="Off the mouth of the Nile, August 1798: Rear-Admiral Nelson's letter to the Earl of St. Vincent, and the minute of facts in the dispatches",
      children=['minute-of-facts-stated-in-the-dispatches-to-lord-st-vincent-1798', 'rear-admiral-nelsons-letter-of-3-august-1798'],
      definition="The 'minute of facts stated in the dispatches to Lord St. Vincent' and Rear-Admiral Nelson's letter of 3 August, printed from London papers in November and December: one affair's items (X-1800-01), a British summary and the British commander's own words."),
 dict(id='minute-of-facts-stated-in-the-dispatches-to-lord-st-vincent-1798', parent=NILE, kind='document_group',
      label="1798: the 'minute of facts stated in the dispatches to Lord St. Vincent' on the French at the Nile",
      definition="Printings of a minute: 'MINUTE OF FACTS Stated in the Dispatches to Lord St. Vincent. The French transports ran into the Nile, and Buonaparte landed with only a few days provisions on hand, with about thirty eight thousand men, two thousand having been cut to pieces on attempt to land at Alexandria'. A British summary of the dispatches, as the papers printed it.",
      role='report', words=50, dateline=False, head=r'MINUTE\s+OF\s+FACTS\s+Stated\s+in\s+the\s+D\w+\s+to\s+Lord\s+St\.?\s+Vincent\.?\s*',
      core=[r'The\s+French\s+transports\s+ran\s+into\s+the\s+Nile'],
      first="1798: the minute of facts in the dispatches to Lord St. Vincent.",
      what="the minute of facts",
      printings=[k('GUS', '11-22', 2), (k('GUS', '11-23', 2), AGAIN), k('VA', '11-30', 3), k('PGZ', '12-03', 3), k('NHG', '12-05', 3), k('KG', '12-19', 3)]),
 dict(id='rear-admiral-nelsons-letter-of-3-august-1798', parent=NILE, kind='document_group',
      label="Off the mouth of the Nile, 3 August 1798: Rear-Admiral Nelson's letter to the Earl of St. Vincent",
      definition="Printings of the letter: 'Vanguard, off the Mouth of the Nile, August 3, 1798. MY LORD, Almighty God has blessed his majesty's arms in the late battle, by a great victory over the fleet of the enemy, whom I attacked at sun-set on the 1st of August, off the mouth of the Nile'. The British commander's own words, from the London Gazette.",
      role='published_document', words=50, dateline=False,
      core=[r'MY\s+LORD,?\s+ALMIGHTY\s+GOD\s+has\s+blessed\s+his\s+majesty'],
      first="Off the mouth of the Nile, 3 August 1798: Rear-Admiral Nelson's letter.",
      what="Rear-Admiral Nelson's letter",
      printings=[(k('GUS', '12-01', 3), {'head': r'Vanguard,?\s+off\s+the\s+Mouth\s+of\s+the\s+Nile,?\s+August\s+3,?\s+1798\.\s*'}),
                 (k('PGZ', '12-03', 3), {'head': r'FROM\s+THE\s+LONDON\s+GAZETTE\W+OCT\.?\s+2\.\s+Copy\s+of\s+a\s+Letter\s+from\s+Rear\s+Admiral\s+Nelson.{0,120}?1798\.\s*'}),
                 (k('NHG', '12-05', 2), {'head': r'The\s+Official\s+Signature\.\s+From\s+the\s+LONDON\s+GAZETTE,?\s+October\s+2,?\s+1798\.\s+Copy\s+of\s+a\s+letter\s+from\s+Rear\s+Admiral\s+Nelson.{0,120}?1798\.\s*'}),
                 (k('MIR', '12-10', 1), {'head': r'OFFICIAL!\W+AUTHENTIC!\s+Nelson\W?s\s+Victory\s+From\s+the\s+LONDON\s+GAZETTE\W+October\s+2,?\s+1798\.\s+Copy\s+of\s+a\s+letter\s+from\s+Rear\s+Admiral\s+NELSON.{0,120}?1798\.\s*'})]),
 dict(id=SPEECH, kind='context_group',
      label="The opening of the session, December 1798: the President's speech to both Houses and the Senate's answer",
      children=['president-speech-to-both-houses-8-december-1798', 'the-senates-answer-to-the-presidents-speech-12-december-1798'],
      definition="The President's speech to both Houses of Congress of 8 December 1798 and the Senate's answer of 12 December: one affair's separate public acts (X-1800-01), each in its authors' own words."),
 dict(id='president-speech-to-both-houses-8-december-1798', parent=SPEECH, kind='document_group',
      label="The President's speech to both Houses of Congress, 8 December 1798",
      definition="Printings of the speech: 'Gentlemen of the Senate, and Gentlemen of the House of Representatives, WHILE with reverence and resignation we contemplate the dispensations of Divine Providence, in the alarming and destructive pestilence with which several of our cities and towns have been visited, there is cause for gratitude and mutual congratulations'. The President's own words.",
      role='published_document', words=50, dateline=False,
      core=[GS + r'WHILE,?\s+with\s+reverence\s+and\s+resignation', r'WHILE,?\s+with\s+reverence\s+and\s+resignation,?\s+we\s+contemplate'],
      first="The President's speech of 8 December 1798.",
      what="the President's speech of 8 December 1798",
      printings=[k('GUS', '12-08', 3), k('NHG', '12-19', 3), k('MIR', '12-24', 2), k('PGZ', '12-24', 1)]),
 dict(id='the-senates-answer-to-the-presidents-speech-12-december-1798', parent=SPEECH, kind='document_group',
      label="The Senate's answer of 12 December 1798 to the President's speech",
      definition="Printings of the answer: 'To the PRESIDENT of the United States. SIR, THE Senate of the United States join you in thanks to Almighty God for the removal of the late afflicting dispensations of his Providence, and for the patriotic spirit, and general prosperity of our country'. The Senate's own words.",
      role='published_document', words=50, dateline=False,
      core=[r'To\s+the\s+PRESIDENT\s+of\s+the\s+U\w*\.?\s+STATES\W+SIR,?\s+THE\s+Senate\s+of\s+the\s+United\s+States\s+join', r'SIR,?\s+THE\s+Senate\s+of\s+the\s+United\s+States\s+join\s+you\s+in\s+thanks'],
      first="The Senate's answer of 12 December 1798 to the President's speech.",
      what="the Senate's answer",
      printings=[k('GUS', '12-12', 3), k('PGZ', '12-24', 2), k('NHG', '12-26', 2), k('MIR', '12-31', 1)]),
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
            problems.append((s['id'], key, 'page not in the 1798 pages'))
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
        r['id'] = f'S98-{n:03}'
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
               'admission_rule': 'Reviewed 1798 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1798/'
    return {
        'ledger_id': 'ledger:stories-1798', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1798', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1798, and of 1797 where they reach the 1798 pages (long-running ones '
                   'included), counted by machine over all 1,656 pages of 1798 in both transcriptions and joined into documents; the admitted '
                   'and chosen items counted again by their own opening (the acts of Congress by their first section), and scan checks of each admitted passage, by the thin-year rule '
                   "(Y-THIN, as amended with the owner's choice B1): eligible when printed by more than half of the papers that survive for "
                   "the item's weeks and by at least 4; eligible items printed by every paper that survives for their weeks admitted; the "
                   'others chosen to cover the months and the kinds of news'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1797.json': 'retrieval_candidates',
                             d+'counts_1798.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1798.py': 'ledger_code', 'work/archive_data/ledgers/stories_1798_review.json': 'scan_review',
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
