"""Write ledgers/stories_1794.json: reviewed stories of 1794, round one.

1794 is read by the thin-year rule the owner chose on 23 November 2026 (docs/rules-and-exceptions.md, Y-THIN), as amended the
same night (the owner's choice B1): an item, counted by its own words, is eligible when it was printed by more than half of the
newspapers that survive for its weeks, and by at least 4 newspapers; digests are not. The newspapers that survive for an item's
weeks are those with an eligible issue between its first and last printing, and at least in the three weeks from its first
printing. As in R-01, the eligible items printed by every newspaper that survives for their weeks are admitted, and the other
eligible items are chosen to cover the months and the kinds of news (a target, not a quota); one affair's items are handled as
in X-1800-01. Sub-stories (C-01), private persons (R-04) and the list of items read and not admitted (R-03) apply as in every
year (outputs/story_discovery_1794/README.md).

The automatic families first printed in 1794 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1793 over the 1794 pages
(items_from_1793.json); every item in 3 or more papers was counted by machine, by about 100 words of its text from the finder's
position, over every page, and the counts were joined into documents; the candidates were counted again by about 70 words from
their own opening (counts_1794.json). The 1794 pages are those whose issue the data release dates to 1794
(work/year_search_pages.py 1794 ... --printed-dates). 1794 has 9 catalogue series, which are 8 papers (C-04): the Gazette of the
United States under two catalogue numbers (sn83025878 to 11 June, sn84026271 from 12 June). The Eagle of Hanover (3 issues)
and the Phoenix of Dover (1 issue) survive only in a few weeks, and the Columbian Informer of Keene from February.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 40-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1794_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1794.py [--table] [--base 0.11.15 --target 0.11.16]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1794/search_pages.json).
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1794'
D = PROJECT/'outputs/story_discovery_1794'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1794_review.json'
OUT = HERE/'stories_1794.json'
BASE, TARGET = '0.11.15', '0.11.16'   # defaults; see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83025878': 'The Gazette of the United States', 'sn84026271': 'The Gazette of the United States',
         'sn84023134': 'The American Herald of Liberty', 'sn83025588': 'The New Hampshire Gazette', 'sn83025523': 'The Mirrour',
         'sn84038410': 'The Patowmac Guardian', 'sn84023313': 'The Columbian Informer', 'sn84023150': 'The Eagle',
         'sn84023045': 'The Phoenix'}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, filed date (MM-DD in 1794), page and edition. The Gazette of the United States has
    two catalogue numbers in 1794 (C-04); the date picks it."""
    if paper == 'GUS':
        lccn = 'sn83025878' if date <= '06-11' else 'sn84026271'
    else:
        lccn = {'AHL': 'sn84023134', 'NHG': 'sn83025588', 'MIR': 'sn83025523', 'PG': 'sn84038410', 'CI': 'sn84023313',
                'EAG': 'sn84023150', 'PHX': 'sn84023045'}[paper]
    return f'{lccn}|{YEAR}-{date}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


MISFILED = misfiled()
AGAIN = {'note': 'Printed again.'}
WI = r'West\W?Indies'
# Story groups ('printings' lists each printing's page; a tuple adds overrides for that printing: core, role, field, note,
# words, dateline, head, back, stop), as in make_stories_1778.py. A parent ('context_group') lists its children.
STORIES = [
 dict(id='madison-resolutions-on-the-commerce-of-foreign-nations-january-1794', kind='document_group',
      label="Congress, January 1794: Mr. Madison's resolutions for further restrictions and higher duties on the commerce of foreign nations",
      definition="Printings of the resolutions Mr. Madison read in the committee of the whole house: 'Resolved, as the opinion of this committee, that the interest of the United States would be promoted by further restrictions and higher duties, in certain cases, on the manufactures and navigation of foreign nations, employed in the commerce of the United States, than those now imposed'; later printings give the first resolution as the house debated it. Resolutions moved in Congress, as the papers printed them.",
      role='published_document', words=50, dateline=False,
      core=[r'Resolved\s*,?\s+as\s+the\s+opinion\s+of\s+this\s+committee,?\s+that\s+the\s+interest\s+of\s+the\s+United\s+States\s+would\s+be\s+promoted', r'That\s+the\s+interest\s+of\s+the\s+United\s+States\s+would\s+be\s+promoted\s+by\s+further\s+restrictions'],
      first="Congress, January 1794: Mr. Madison's resolutions on the commerce of foreign nations.",
      what="Mr. Madison's resolutions on the commerce of foreign nations",
      printings=[k('GUS', '01-04', 2), k('PG', '01-13', 2), k('NHG', '01-25', 1), (k('GUS', '02-03', 3), AGAIN), (k('GUS', '02-04', 3), AGAIN),
                 (k('PG', '02-10', 2), AGAIN), (k('NHG', '02-22', 1), AGAIN), k('MIR', '03-03', 1)]),
 dict(id='queen-of-portugal-proclamation-convoy-for-american-vessels-1794', kind='document_group',
      label="The Queen of Portugal's proclamation giving convoy to American vessels against the cruisers of Algiers",
      definition="Printings of a proclamation: 'A PROCLAMATION, By the QUEEN OF PORTUGAL. Her most Faithful Majesty wishing to manifest on every occasion justice and clemency ... has been pleased to order in consequence of the exposed situation, under which the American navigation labours, from the cruisers of Algiers in the ocean, to give a convoy to all the American vessels'. An act of the Portuguese crown, as the papers printed it.",
      role='published_document', words=50, dateline=False,
      core=[r'(?:A\s+)?PROCLAMATION\.?,?\s+By\s+the\s+Queen\s+of\s+Portugal'],
      first="The Queen of Portugal's proclamation giving convoy to American vessels against the cruisers of Algiers.",
      what="the Queen of Portugal's proclamation on a convoy for American vessels",
      printings=[k('GUS', '01-15', 2), k('NHG', '02-01', 3), k('PG', '02-03', 2), k('AHL', '02-04', 3)]),
 dict(id='fayetteville-letter-on-an-action-near-charleston-january-1794', kind='document_group',
      label="A letter from Fayetteville, North Carolina, of 6 January 1794: a report from Charleston of an action between a French and an English ship",
      definition="Printings of an extract of a letter from Fayetteville, dated the 6th: 'Two gentlemen just arrived here from Charleston (S. C.) report, that a French 20 gun ship, & an English 18 gun frigate had had a severe action near the harbour; that the English ship was taken and bro't into Charleston, in consequence of which a riot took place'. A report at second hand, as the letter-writer gives it.",
      role='report', words=50, dateline=False,
      core=[r'Extra\w*\s+of\s+a\s+letter\s+from\s+(?:a\s+gentleman\s+in\s+)?Fayette\W?ville'],
      first="A letter from Fayetteville of 6 January 1794 on a report from Charleston.",
      what="the letter from Fayetteville of 6 January",
      printings=[k('GUS', '01-20', 3), k('PG', '02-03', 3), k('AHL', '02-04', 3), k('NHG', '02-08', 3), k('MIR', '02-10', 3)]),
 dict(id='charleston-letter-from-georgia-on-enlisting-for-the-french-service-january-1794', kind='document_group',
      label="Charleston, 3 January 1794: a letter from Georgia on men enlisting for the French service against West Florida, St. Augustine and New Orleans",
      definition="Printings of an extract of a letter from a gentleman in Georgia to his friend in Charleston: 'The people here have got recruiting-mad, for the French service to go against West-Florida, Augustine, and New-Orleans'. A letter-writer's report, as the papers printed it.",
      role='report', words=50, dateline=True,
      core=[r'Extra\w*\s+of\s+a\s+letter\s+from\s+a\s+gentleman\s+in\s+Georgia', r'The\s+people,?\s+here\s+have\s+got\s+recruiting\W+mad'],
      first="Charleston, 3 January 1794: a letter from Georgia on enlisting for the French service.",
      what="the letter from Georgia on enlisting for the French service",
      printings=[k('GUS', '01-27', 2), k('PG', '02-10', 3), k('AHL', '02-11', 3), k('NHG', '02-15', 2), k('MIR', '02-17', 3)]),
 dict(id='norfolk-french-fleet-arrives-in-hampton-roads-february-1794', kind='document_group',
      label="Norfolk, February 1794: the French fleet arrives in Hampton Roads",
      definition="Printings of a Norfolk paragraph: 'On Saturday last arrived in Hampton Roads, the French frigate Charente, of 40 guns, from Rochefort, and on Monday the remainder of the French fleet', with the ships' names, and that they have brought out the new Minister of France. A report from Norfolk.",
      role='report', words=50, dateline=True, head=r'Late\s+news\s+from\s+France\.?\s*',
      core=[r'On\s+Saturday\s+last\s+arrived\s+in\s+Hampton\s+Roads'],
      first="Norfolk, February 1794: the French fleet arrives in Hampton Roads.",
      what="the Norfolk report of the French fleet",
      printings=[k('GUS', '02-24', 2), k('PG', '03-03', 3), k('NHG', '03-08', 2), k('MIR', '03-10', 4), k('AHL', '03-11', 4)]),
 dict(id='british-additional-instructions-of-november-1793', kind='document_group',
      label="Britain's additional instructions of November 1793 to the commanders of ships of war and privateers: ships with the produce of French colonies to be stopped",
      definition="Printings of the King's instructions: 'Additional instructions to the commanders of all ships of war and privateers that have, or may have letters of marque against France ... That they shall stop and detain all ships laden with goods, the produce of any colony belonging to France, or carrying provisions or other supplies for the use of any such colony'. An act of the British government, as the papers printed it from a Kingston (Jamaica) paper.",
      role='published_document', words=50, dateline=False, head=r'G\s?E\s?O\s?R\s?G\s?E\s+R(?:EX)?\.?\W*',
      core=[r'Additional\s+instructions\s+to\s+the\s+commanders\s+of\s+all\s+ships\s+of\s+war', r'ADDITIONAL\s+INSTRUCTIONS\W+(?:L\.?\s*S\.?\W+)?to\s+the\s+Commanders'],
      first="Britain's additional instructions of November 1793 to ships of war and privateers.",
      what="Britain's additional instructions of November 1793",
      printings=[k('NHG', '03-15', 3), k('AHL', '03-18', 3), k('MIR', '03-24', 2), k('PG', '03-31', 3), k('EAG', '04-07', 2)]),
 dict(id='havre-letter-on-the-retaking-of-toulon-december-1793', kind='document_group',
      label="A letter from Havre of 30 December 1793, received at Providence: the French celebrate the retaking of Toulon",
      definition="Printings of a letter 'from a gentleman now in France to his friend in this town, received by the brig Dolphin, just arrived at Providence, dated Havre, Dec. 30, 1793': 'I then told you of the success of the Armies of the Republic in the taking of Toulon and Valenciennes; this day, being the Decadi, we have been celebrating the event'. A letter-writer's account, as the papers printed it.",
      role='report', words=50, dateline=False,
      core=[r'(?:(?:Copy|Extra\w*)\s+of\s+a\s+)?letter\s+from\s+a\s+gentleman\s+now\s+in\s+France\s+to\s+his\s+friend'],
      first="A letter from Havre of 30 December 1793 on the retaking of Toulon.",
      what="the letter from Havre of 30 December 1793",
      printings=[k('NHG', '03-29', 3), (k('MIR', '03-31', 3), {'head': r'Glorious\s+for\s+the\s+French!\s*'}), k('GUS', '04-01', 1), k('EAG', '04-07', 3), k('AHL', '04-08', 1), k('PG', '04-14', 3)]),
 dict(id='report-of-a-british-order-on-american-prizes-april-1794', kind='document_group',
      label="April 1794: a report that a Barbados paper printed a British order of 20 January holding the proceeds of American prizes",
      definition="Printings of a paragraph: 'We are informed that a Barbadoes paper has been seen, containing an order of his Britannic Majesty's, under date of the 20th of January, that all monies arising from the sale of American prizes should be reserved in the hands of the agents of the ships of war by which they were captured, until it should be known what part the United States of America will take in the present war'. A report at second hand: printed from Baltimore, and in one paper from Basseterre.",
      role='report', words=50, dateline=True, back=True,
      core=[r'we\s+are\s+informed,?\s+that\s+a\s+Barbad\w+\s+paper\s+has\s+been\s+seen'],
      first="April 1794: a report of a British order of 20 January on the proceeds of American prizes.",
      what="the report of a British order on American prizes",
      printings=[k('GUS', '04-08', 3), (k('PG', '04-14', 3), {'head': 'April\\s+5\\.\\s*'}), k('NHG', '04-19', 3), (k('AHL', '04-22', 2), {'head': 'APRIL\\s+10\\.\\s*', 'back': False, 'core': [r'From\s+Bassaterre,?\s+March\s+10,?\s+we\s+are\s+informed']}), (k('MIR', '04-28', 2), {'head': r'Important\s+Intelligence\.\s+BALTIMORE,?\s+APRIL\s+5\.\W*'})]),
 dict(id='london-report-french-descent-put-off-for-jersey-march-1794', kind='document_group',
      label="London, March 1794: a report that the French have put off a descent on Great Britain for the conquest of Jersey",
      definition="Printings of a London paragraph: 'Intelligence is received, that the French have for the present changed their intentions of visiting Great Britain, first intending the conquest of the island of Jersey. The force is collected at St. Maloes'. A report from London papers.",
      role='report', words=50, dateline=True,
      core=[r'Intelligence\s+is\s+(?:just\s+)?received,?\s+that\s+the\s+French\s+have\s+for\s+the\s+present\s+changed'],
      first="London, March 1794: a report on a French descent on Jersey.",
      what="the London report on a French descent on Jersey",
      printings=[k('GUS', '05-06', 3), k('NHG', '05-10', 2), k('MIR', '05-19', 2), (k('PG', '05-19', 2), {'head': 'March\\s+15\\.\\s*'}), k('AHL', '05-20', 1), (k('GUS', '05-20', 3), AGAIN),
                 (k('PG', '06-02', 2), AGAIN), (k('NHG', '06-03', 2), AGAIN)]),
 dict(id='king-of-prussia-declaration-against-a-general-armament-1794', kind='document_group',
      label="London, 19 March 1794: the King of Prussia's declaration against a general armament of the inhabitants of the Empire",
      definition="Printings of a declaration: 'DECLARATION Of the King of Prussia against a general armament of the inhabitants of the empire. I. When the proposition for a general armament of the subjects of the empire was made at the assembly of the Diet, the king of Prussia represented such essential difficulties against this measure'. An act of the King of Prussia, as the papers printed it from London papers.",
      role='published_document', words=50, dateline=True,
      core=[r'DECLARATION\s+Of\s+the\s+King\s+of\s+Prussia,?\s+against\s+a\s+general\s+armament'],
      first="London, 19 March 1794: the King of Prussia's declaration against a general armament.",
      what="the King of Prussia's declaration against a general armament",
      printings=[k('GUS', '05-09', 2), k('MIR', '05-19', 3), k('PG', '05-19', 2), k('AHL', '05-20', 1), k('NHG', '05-20', 1)]),
 dict(id='boston-report-on-captain-talbot-under-a-french-commission-may-1794', kind='document_group',
      label="Boston, 2 May 1794: a report that Captain Talbot, an American whose brig was taken, cruises against British vessels under a French commission",
      definition="Printings of a Boston paragraph: 'A gentleman from the West-Indies informs us, that a Capt. Talbot, an American, after being taken and carried into New-Providence, losing his property and brig—abused and insulted by the British ... immediately proceeded to Guadalupe, was naturalized, procured a commission as a French privateer'. A report at second hand, in the papers' words.",
      role='report', words=50, dateline=True,
      core=[r'A\s+gentleman\s+from\s+the\s+' + WI + r',?\s+informs\s+us,?\s+that\s+a\s+Capt'],
      first="Boston, 2 May 1794: a report on Captain Talbot under a French commission.",
      what="the Boston report on Captain Talbot",
      printings=[k('GUS', '05-09', 3), k('NHG', '05-10', 3), k('AHL', '05-13', 4), (k('MIR', '05-19', 3), {'head': 'BOSTON\\.\\s*'}), k('PG', '05-19', 3)]),
 dict(id='london-thirty-one-sail-at-brest-march-1794', kind='document_group',
      label="London, 15 March 1794: thirty-one sail of the line ready at Brest",
      definition="Printings of a London paragraph: 'By an American Gentleman who left Brest on Friday last we learn, that there were one and thirty sail, besides a great number of frigates, lying at single anchor, ready to put to sea at the shortest warning'. A report from London papers.",
      role='report', words=50, dateline=True,
      core=[r'By\s+an\s+American\s+Gentleman,?\s+who\s+left\s+Brest'],
      first="London, 15 March 1794: thirty-one sail at Brest.",
      what="the London report of thirty-one sail at Brest",
      printings=[(k('NHG', '05-10', 2), {'head': 'MARCH\\s+15\\.\\s*'}), (k('MIR', '05-19', 2), {'head': 'MARCH\\s+15\\.\\s*'}), k('AHL', '05-20', 1), k('GUS', '05-20', 3), k('PG', '06-02', 2)]),
 dict(id='new-york-news-from-brest-by-the-brig-mary-may-1794', kind='document_group',
      label="New York, 19 May 1794: news from Brest by the brig Mary",
      definition="Printings of a New York paragraph: 'By the brig Mary, Capt. Haley, in 48 days from Brest, we have received the following important intelligence: About the 20th of March an engagement took place between the French and Prussian armies, which ended in a signal victory on the side of the Republicans'. A report brought by a ship, in the papers' words.",
      role='report', words=50, dateline=True,
      core=[r'By\s+the\s+brig\s+Mary\s*,?\s+Capt\.?\s+Haley'],
      first="New York, 19 May 1794: news from Brest by the brig Mary.",
      what="the news from Brest by the brig Mary",
      printings=[k('GUS', '05-20', 3), k('MIR', '05-26', 3), k('AHL', '05-27', 3), k('NHG', '05-27', 2), k('PG', '06-02', 2)]),
 dict(id='brussels-allied-armies-on-the-defensive-march-1794', kind='document_group',
      label="Brussels, 15 March 1794: the allied armies on the defensive until their reinforcements arrive",
      definition="Printings of a Brussels paragraph: 'All the motions and preparations which the combined armies have made on the frontiers are only on the defensive ... it has been agreed upon, that the combined armies shall not begin to act until the great reinforcements which are expected from Germany and England shall have arrived'. A report from Brussels, as the papers printed it.",
      role='report', words=50, dateline=True,
      core=[r'All\s+the\s+motions\s+and\s+preparations\s+which\s+the\s+combined\s+armies'],
      first="Brussels, 15 March 1794: the allied armies on the defensive.",
      what="the Brussels report of 15 March",
      printings=[k('GUS', '05-21', 3), k('PG', '06-02', 2), k('AHL', '06-03', 3), k('NHG', '06-03', 2), k('MIR', '06-09', 2)]),
 dict(id='london-king-of-prussia-to-give-no-more-assistance-march-1794', kind='document_group',
      label="London, 26 March 1794: a report that the King of Prussia will give no more assistance in the war against France",
      definition="Printings of a London paragraph: 'It may be depended upon as certain, that the King of Prussia, our great, faithful, humane, and good ally, will give no more assistance in the war against France'. A report from London papers, in their words.",
      role='report', words=50, dateline=True,
      core=[r'It\s+may\s+be\s+de\w+\s+(?:up)?on\s+as\s+certain,?\s+that\s+the\s+King\s+of\s+Prussia'],
      first="London, 26 March 1794: a report on the King of Prussia and the war.",
      what="the London report that the King of Prussia will give no more assistance",
      printings=[k('GUS', '05-28', 3), k('MIR', '06-09', 3), k('PG', '06-09', 2), k('AHL', '06-10', 3), k('NHG', '06-10', 1), k('PHX', '06-14', 3)]),
 dict(id='brussels-report-of-french-money-for-the-king-of-prussia-march-1794', kind='document_group',
      label="Brussels, 16 March 1794: a report that the French will pay the King of Prussia for a treaty of peace",
      definition="Printings of a Brussels paragraph: 'The French, it is positively asserted, have agreed to give a large sum of money to the King of P——, part of which has already passed their frontier, in consideration whereof, his P——n Majesty ... signs with them a treaty of peace and alliance'. A report, in the papers' words.",
      role='report', words=50, dateline=True,
      core=[r'The\s+French,?\s+it\s+is\s+positively\s+asserted,?(?:\s+have\s+agreed\s+to\s+give)?'],
      first="Brussels, 16 March 1794: a report of French money for the King of Prussia.",
      what="the Brussels report of French money for the King of Prussia",
      printings=[k('GUS', '05-29', 3), k('PG', '06-09', 2), k('AHL', '06-10', 2), k('NHG', '06-10', 1), k('PHX', '06-14', 3), k('MIR', '06-16', 1)]),
 dict(id='president-message-on-an-encroachment-by-british-troops-21-may-1794', kind='document_group',
      label="The President's message to Congress of 21 May 1794 on an encroachment by British troops, with the papers on it",
      definition="Printings of the President's message: 'Gentlemen of the Senate, and of the House of Representatives, I LAY before you certain information, whereby it would appear that some encroachment was about to be made on our territory by an officer and party of British troops'; the papers print with it the Secretary of State's letter of 20 May to the British minister on Lord Dorchester's speech to the Indians (one publication, X-1810-01). The President's own words.",
      role='published_document', words=50, dateline=False,
      head=r'(?:Important\s+State\s+Papers\.?\s+Communicated\s+to\s+Congress\s+May\s+23\.?|IMPORTANT\s+PAPER\.?\s+HOUSE\s+OF\s+REPRESENTATIVES\.?\s+MAY\s+20\.?|HOUSE\s+OF\s+REPRESENTATIVES\.?\s+Monday,?\s+May\s+21\.?)\s*',
      core=[r'United\s+States,?\s+(?:21st\s+May|May\s+21),?\s+1794\.?\s+Gentlemen\s+of\s+the\s+Senate', r'Gentlemen\s+of\s+the\s+Senate,?\s+and\s+of\s+the\s+House\s+of\s+Representatives,?\s+I\s+LAY\s+before\s+you'],
      first="The President's message of 21 May 1794 on an encroachment by British troops.",
      what="the President's message of 21 May 1794",
      printings=[k('GUS', '06-02', 2), k('NHG', '06-03', 3), k('MIR', '06-09', 2), k('PG', '06-09', 3), k('AHL', '06-10', 1), k('PHX', '06-14', 2)]),
 dict(id='duke-of-york-letter-from-tournay-13-may-1794', kind='document_group',
      label="Whitehall, May 1794: the Duke of York's letter from Tournay of 13 May (General Clairfayt's action at Courtrai)",
      definition="Printings of the letter, as the London Gazette gave it: 'A letter, dated Tournay, May 13, 1794, of which the following is an extract, was yesterday received from his Royal Highness the Duke of York ... Since my last letter no attempt has been made by the enemy to harass or molest any of my posts. On Sunday morning, however, they attacked in great force General Clairfayt's corps'. The British commander's own words.",
      role='published_document', words=50, dateline=False, head=r'(?:From\s+the\s+LONDON\s+GAZETTE\.?\s+)?WHITEHALL,?\s+May\s+1[56]\.?\s*',
      core=[r'A\s+letter,?\s+dated\s+Tournay,?\s+May\s+13,?\s+1794', r'Since\s+my\s+last\s+letter\s+no\s+attempt\s+has\s+been\s+made'],
      first="Whitehall, May 1794: the Duke of York's letter from Tournay of 13 May.",
      what="the Duke of York's letter of 13 May",
      printings=[k('GUS', '07-15', 2), k('PG', '07-28', 2), (k('AHL', '07-29', 2), {'head': 'From\\s+the\\s+DUKE\\s+of\\s+YORK\\s+to\\s+Mr\\.?\\s+DUND\\w+\\.?\\s+TOURNAY,?\\s+MAY\\s+13,?\\s+1794\\.?\\W*'}), k('CI', '07-29', 3), k('NHG', '07-29', 2), k('MIR', '08-04', 2)]),
 dict(id='tournay-account-of-the-british-column-18-may-1794', kind='document_group',
      label="Tournay, Sunday evening, 18 May 1794: an account of the British column's retreat",
      definition="Printings of an account dated 'Sunday Evening, 18th May': 'From the following detail, there is great reason to believe that the French permitted the column under the command of the Duke of York to advance yesterday further than force could have carried them'. An account from the British side, printed after the Duke of York's letter or the Tournay letter of 17 May.",
      role='report', words=50, dateline=False,
      head=r'(?:Further\s+corroborating\s+particulars\s+of\s+the\s+defeat\s+of\s+the\s+Duke\s+of\s+York\.?\s+)?(?:TOURNA[IY]|Tournay|Courtray),?\s*',
      core=[r'Sunday\s+Evening,?\s+18th\s+(?:of\s+)?May\.?,?\s+From\s+the\s+following\s+detail'],
      first="Tournay, 18 May 1794: an account of the British column's retreat.",
      what="the Tournay account of 18 May",
      printings=[k('AHL', '07-15', 1), k('CI', '07-15', 3), k('GUS', '07-15', 3), k('NHG', '07-15', 2), k('MIR', '07-21', 1), k('PG', '07-28', 2)]),
 dict(id='paris-another-action-near-tournay-21-may-1794', kind='document_group',
      label="Paris, 27 May 1794: another action near Tournay on 21 May",
      definition="Printings of a Paris paragraph: 'There has been another action on the 21st of May, near Tournay, between the republican army, commanded by Pichegru and the combined armies. These last were forced to cross the Scheldt, after a bloody action which lasted 24 hours'. A report from French papers.",
      role='report', words=50, dateline=True,
      core=[r'There\s+has\s+been\s+another\s+action\s+on\s+the\s+21st\s+(?:of\s+)?May'],
      first="Paris, 27 May 1794: another action near Tournay.",
      what="the Paris report of the action of 21 May",
      printings=[(k('GUS', '07-17', 2), {'head': r'From\s+a\s+paper\s+received\s+by\s+the\s+Maria,?\s+Capt\.?\s+Green,?\s+from\s+Brest\.\s+PARIS,?\s+May\s+27\.\s*'}), k('AHL', '07-29', 3), k('CI', '07-29', 3), k('NHG', '07-29', 3), k('MIR', '08-04', 2)]),
 dict(id='house-of-commons-on-the-american-embargo-26-may-1794', kind='document_group',
      label="House of Commons, 26 May 1794: the embargo laid by the American States (Mr. Sheridan's motion)",
      definition="Printings of a report of the debate: 'HOUSE OF COMMONS. May 26. Embargo laid on Foreign Ships by the AMERICAN STATES. Mr. Sheridan said, there was a paper which has created a general alarm, and on account of which the States of America had laid an Embargo on foreign ships. The paper he alluded to, purported to be an answer given by the Lord Dorchester to the Indians'. A report of a debate in Parliament.",
      role='report', words=50, dateline=False, head=r'HOUSE\s+OF\s+COMMONS\W+May\s+26\.?\s*',
      core=[r'Embargo\s+laid\s+on\s+Foreign\s+Ships\s+by\s+the\s+AMERICAN\s+STATES'],
      first="House of Commons, 26 May 1794: the American embargo.",
      what="the Commons debate of 26 May on the American embargo",
      printings=[k('GUS', '08-11', 3), k('AHL', '08-12', 2), k('NHG', '08-12', 2), k('MIR', '08-18', 1), k('CI', '08-19', 1), k('PG', '09-01', 2)]),
 dict(id='letter-from-an-officer-of-the-legion-near-greenville-28-july-1794', kind='document_group',
      label="A letter from an officer of the legion, dated near Greenville, 28 July 1794",
      definition="Printings of a letter 'from an officer in the legion of the United States, dated Camp, 12 miles advance of Greenville, 28th July': 'I hope by the time this reaches you that we shall be able to give a good account of the Indian war. We have about 1700 or 1800 Kentucky volunteers with us'. An officer's letter, as the papers printed it.",
      role='report', words=50, dateline=False,
      core=[r'(?:(?:Copy|Extract)\s+of\s+a\s+)?letter\s+from\s+an\s+officer\s+in\s+the\s+legion\s+of\s+the\s+United\s+States'],
      first="A letter from an officer of the legion of 28 July 1794.",
      what="the letter from an officer of the legion",
      printings=[k('GUS', '08-30', 3), k('PG', '09-08', 1), k('AHL', '09-16', 2), k('CI', '09-16', 3), k('NHG', '09-16', 2), k('EAG', '09-22', 2), (k('MIR', '09-22', 1), {'head': r'INDIAN\s+AFFAIRS\.\s*'})]),
 dict(id='the-insurrection-in-the-western-counties-of-pennsylvania-1794', kind='context_group',
      label="The insurrection in the western counties of Pennsylvania, September and October 1794: the President's proclamation and the meeting at Parkinson's Ferry",
      children=['president-proclamation-of-25-september-1794', 'pittsburgh-report-of-the-meeting-at-parkinsons-ferry-october-1794',
                'resolutions-of-the-meeting-at-parkinsons-ferry-2-october-1794'],
      definition="The President's proclamation of 25 September 1794 calling forth the militia against the combinations in the western counties of Pennsylvania, and the meeting of delegates at Parkinson's Ferry on 2 October, as the Pittsburgh paper reported it and as its resolutions were printed: one affair's separate public acts (X-1800-01)."),
 dict(id='president-proclamation-of-25-september-1794', parent='the-insurrection-in-the-western-counties-of-pennsylvania-1794', kind='document_group',
      label="The President's proclamation of 25 September 1794 on the insurrection in the western counties of Pennsylvania",
      definition="Printings of the proclamation: 'By the PRESIDENT of the UNITED STATES of America, A PROCLAMATION. WHEREAS from a hope, that the combinations against the Constitution and Laws of the United States, in certain of the Western counties of Pennsylvania would yield to time and reflection, I thought it sufficient, in the first instance, rather to take measures for calling forth the militia, than immediately to embody them'. The President's own words.",
      role='published_document', words=50, dateline=False,
      core=[r'By\s+the\s+PRESIDENT\s+of\s+the\s+UNITED\s+STATES\s+of\s+America\W+(?:A\s+)?P\s?R\s?O\s?C\s?L\s?A\s?M\s?A\s?T\s?I\s?O\s?N\W+WHEREAS\s+from\s+a\s+hope',
            r'WHEREAS\s+from\s+a\s+hope,?\s+that\s+(?:the\s+)?combinations\s+against\s+the\s+Constitution'],
      first="The President's proclamation of 25 September 1794.",
      what="the President's proclamation of 25 September 1794",
      printings=[k('GUS', '09-25', 3), (k('GUS', '09-27', 4), AGAIN), (k('GUS', '09-29', 4), AGAIN), k('PG', '10-06', 3), k('AHL', '10-14', 4), k('NHG', '10-21', 1)]),
 dict(id='boston-news-from-lisbon-by-marblehead-september-1794', kind='document_group',
      label="Boston, September 1794: news from Lisbon by a schooner arrived at Marblehead",
      definition="Printings of a Boston paragraph: 'By an arrival ... at Marblehead, of a schooner, owned by Colonel Orne, in 36 days from Lisbon, we have received the following intelligence, communicated by a gentleman of veracity', that news had been received at Lisbon that the French had taken St. Sebastian. A report at second hand, in the papers' words.",
      role='report', words=50, dateline=True, head=r'(?:Jacobins\s+Triumphant!\W*)?(?:LATEST\s+FROM\s+EUROPE\.?\s*)',
      core=[r'By\s+an\s+arrival\s+(?:yesterday\s+morning,?\s+|since\s+our\s+last\s+)?at\s+Marblehead,?\s+(?:from|of)\s+a\s+schooner'],
      first="Boston, September 1794: news from Lisbon by Marblehead.",
      what="the Boston report of news from Lisbon",
      printings=[k('AHL', '09-30', 3), k('CI', '09-30', 3), k('NHG', '09-30', 3), k('GUS', '10-03', 3), (k('MIR', '10-06', 3), {'core': [r'By\s+an\s+arrival\s+since\s+our\s+last\s+at\s+Marblehead'], 'head': 'Republicans\\s+Triumphant!\\W*BOSTON,?\\s+Sept\\.?\\s+29\\.?\\W*Latest\\s+from\\s+Europe\\.?\\s*'}), k('PG', '10-13', 3)]),
 dict(id='wayne-letter-on-the-action-of-20-august-1794', kind='document_group',
      label="General Wayne's letter of 28 August 1794 to the Secretary of War on the action of 20 August on the banks of the Miamis",
      definition="Printings of the general's letter: 'Head Quarters Grand Glaize, 28 Aug. 1794. Sir, It is with infinite pleasure that I now announce to you the brilliant success of the Federal army under my command, in a general action with the combined force of the hostile Indians, and a considerable number of the volunteers and militia of Detroit on the 20th instant on the banks of the Miamis'. The American commander's own words.",
      role='published_document', words=50, dateline=False,
      core=[r'(?:Head\W?Quarters\W*)?Grand\s+Glai[sz]e,?\s+(?:28\s*(?:th)?\s+Aug|Aug\w*\.?\s+28)', r'It\s+is\s+with\s+infinite\s+pleasure\s+that\s+I\s+now\s+announce'],
      first="General Wayne's letter of 28 August 1794 on the action of 20 August.",
      what="General Wayne's letter of 28 August 1794",
      printings=[k('GUS', '10-02', 2), (k('MIR', '10-10', 2), {'head': r'Head\s+Quarters,?\s+Grand\s+Glai[sz]e,?\s+2\dth\s+August,?\s+1794\.?\s+SIR,?\s*'}), k('PG', '10-13', 2), k('AHL', '10-14', 2), k('CI', '10-21', 1)]),
 dict(id='pittsburgh-report-of-the-meeting-at-parkinsons-ferry-october-1794', parent='the-insurrection-in-the-western-counties-of-pennsylvania-1794', kind='document_group',
      label="Pittsburgh, 4 October 1794: the meeting at Parkinson's Ferry for submission to the laws",
      definition="Printings of a Pittsburgh paragraph: 'We understand that at the meeting of Parkinson's Ferry, on Thursday last, there was a perfect unanimity for submission to the laws ... William Findley and David Reddick are appointed to wait on the President of the United States and the Governor of Pennsylvania'. A report from the Pittsburgh paper.",
      role='report', words=50, dateline=True,
      core=[r'We\s+understand\s+that\s+at\s+(?:the|a)\s+meeting\s+(?:of|at)\s+Parkin'],
      first="Pittsburgh, 4 October 1794: the meeting at Parkinson's Ferry.",
      what="the Pittsburgh report of the meeting at Parkinson's Ferry",
      printings=[k('GUS', '10-10', 3), k('PG', '10-20', 3), k('AHL', '10-21', 3), k('NHG', '10-21', 3), k('MIR', '10-24', 2)]),
 dict(id='order-in-council-on-appeals-of-american-ships-6-august-1794', kind='document_group',
      label="At the Court at St. James's, 6 August 1794: the order in council on appeals from condemnations of American ships in the West Indies",
      definition="Printings of the order in council: 'At the Court at St. James's, the 6th of August, 1794. Present, the King's most excellent Majesty in Council. WHEREAS in many of his majesty's vice admiralty courts in the West Indies, sentences of condemnation have passed against ships and goods belonging to the subjects of the United States of America'. An act of the British government.",
      role='published_document', words=50, dateline=False,
      core=[r'At\s+the\s+Court\s+(?:at|of)\s+St\.?\s+James\W?s,?\s+(?:the\s+)?6th\s+(?:of\s+)?Aug'],
      first="The British order in council of 6 August 1794 on appeals of American ships.",
      what="the order in council of 6 August 1794",
      printings=[k('GUS', '10-14', 3), k('AHL', '10-21', 3), k('CI', '10-21', 3), k('NHG', '10-21', 2), k('MIR', '10-24', 2), k('PG', '10-27', 2)]),
 dict(id='resolutions-of-the-meeting-at-parkinsons-ferry-2-october-1794', parent='the-insurrection-in-the-western-counties-of-pennsylvania-1794', kind='document_group',
      label="The resolutions of the delegates of townships at Parkinson's Ferry, 2 October 1794",
      definition="Printings of the resolutions: 'Resolutions of the Delegates of townships of the 14th of August, assembled at Parkinson's Ferry on the 2d of October ... Resolved, That it is the unanimous opinion of this meeting, that if the signature of the submission be not universal it is not so much owing to any existing disposition to oppose the laws'. The meeting's own words, as the Pittsburgh paper printed them.",
      role='published_document', words=50, dateline=True,
      core=[r'Resolutions,?\s+of\s+the\s+Delegates\s+of\s+(?:the\s+)?townships'],
      first="The resolutions of the meeting at Parkinson's Ferry, 2 October 1794.",
      what="the resolutions of the meeting at Parkinson's Ferry",
      printings=[k('GUS', '10-18', 2), k('PG', '10-27', 3), k('NHG', '10-28', 3), (k('AHL', '11-04', 1), {'head': 'PITTSBURG,?\\s+O\\w+\\.?\\s+11\\.\\s*'}), k('CI', '11-04', 2)]),
 dict(id='jay-memorial-to-lord-grenville-july-1794', kind='document_group',
      label="Mr. Jay's memorial to Lord Grenville of July 1794 on the captures of American vessels, with the answer",
      definition="Printings of the memorial: 'The undersigned Envoy of the United States of America has the honor of representing to the Right Honorable Lord Grenville, his Britannic Majesty's Secretary of State for the Department of foreign affairs. That a very considerable number of American vessels have been irregularly captured, and as improperly condemned'. The American envoy's own words, printed as official documents with the answer.",
      role='published_document', words=50, dateline=False,
      head=r'(?:Important\s+State\s+Papers\.?\s+We\s+have\s+been\s+favou?red\s+with\s+the\s+following\s+OFFICIAL\s+DOCUMENTS\s+for\s+Publication\.?|Official\s+State\s+Papers\.?|IMPORTANT\s+STATE\s+PAPER\.?\s+Mr\.?\s+JAY\s+to\s+LORD\s+GRENVILLE\.?|AUTHENTIC\.?)\s*',
      core=[r'The\s+under\s?signed\s+Envoy\s+(?:Extraordinary\s+)?of\s+the\s+United\s+States\s+of\s+America,?\s+has\s+the\s+hono'],
      first="Mr. Jay's memorial to Lord Grenville of July 1794.",
      what="Mr. Jay's memorial to Lord Grenville",
      printings=[k('GUS', '10-20', 3), k('PG', '11-03', 2), k('AHL', '11-04', 3), k('CI', '11-04', 2), k('NHG', '11-04', 2)]),
 dict(id='news-from-the-westward-general-wayne-november-1794', kind='document_group',
      label="Philadelphia, 11 November 1794: news from the westward (General Wayne's army at the Miami towns)",
      definition="Printings of a Philadelphia paragraph: 'NEWS FROM THE WESTWARD. A letter from General Wayne's Army states, that in five days from leaving Fort Defiance he had reached the Miami Towns—that Campbell had evacuated the Fort at the Rapids—that a Council of Indians had been held after their defeat on the 20th August'. A report from a letter, in the papers' words.",
      role='report', words=50, dateline=True, head=r'(?:NEWS\s+FROM\s+THE\s+WESTWARD|Western\s+News)\.?\s*',
      core=[r'A\s+letter\s+from\s+Gen(?:eral|\.)?\s+Wayne\W?s\s+Army,?\s+states'],
      first="Philadelphia, 11 November 1794: news from General Wayne's army.",
      what="the news from the westward of November",
      printings=[(k('GUS', '11-11', 2), {'dateline': False}), k('MIR', '11-21', 3), k('AHL', '11-22', 3), (k('CI', '11-25', 3), {'dateline': False}), k('NHG', '11-25', 2)]),
 dict(id='british-note-to-the-imperial-court-on-subsidies-1794', kind='document_group',
      label="A state paper: the British ministers' note to the Imperial court on subsidies for the war",
      definition="Printings of a state paper: 'The following is the copy of a note which has been transmitted by the English Ministers to the Imperial Court. Because it is not equitable that the states of Austria alone should bear the expenses of the war ... it is the intention of the King of Great Britain, I. That, during the present and the succeeding campaigns, subsidies will be granted'. A note of the British government, as the papers printed it.",
      role='published_document', words=50, dateline=False, head=r'(?:Important\s+)?STATE\s+PAPER\.?\s*',
      core=[r'\[?The\s+following\s+is\s+(?:the|a)\s+copy\s+of\s+a\s+note\s+which\s+has\s+been\s+transmitted'],
      first="The British ministers' note to the Imperial court on subsidies.",
      what="the British note to the Imperial court",
      printings=[k('GUS', '11-15', 2), k('AHL', '11-18', 2), k('NHG', '11-18', 2), k('MIR', '11-21', 2), k('CI', '11-25', 2)]),
 dict(id='house-of-representatives-address-to-the-president-29-november-1794', kind='document_group',
      label="The House of Representatives' address to the President, 29 November 1794, in answer to his speech",
      definition="Printings of the address: 'SIR, THE House of Representatives, calling to mind the blessings enjoyed by the people of the United States, and especially the happiness of living under constitutions and laws, which rest on their authority alone, could not learn, with other emotions than those you have expressed, that any part of our fellow-citizens should have shewn themselves capable of an insurrection'. The House's own words.",
      role='published_document', words=50, dateline=False, head=r'(?:HOUSE\s+OF\s+REPRESENTATIVES,?\s+November\s+28\.\s+)?(?:ANSWER,?\s+OF\s+THE\s+HOUSE\s+(?:of\s+Representatives\s+)?to\s+the\s+PRESIDENT\W?S\s+ADDRESS\.?|Answer\s+to\s+the\s+President\W?s\s+Address:?)\s*',
      core=[r'SIR,?\s+THE\s+House\s+of\s+Representatives,?\s+calling\s+to\s+mind'],
      first="The House of Representatives' address to the President of 29 November 1794.",
      what="the House's address to the President",
      printings=[k('GUS', '12-01', 3), k('MIR', '12-12', 3), k('AHL', '12-13', 3), k('CI', '12-16', 2), k('NHG', '12-16', 1)]),
 dict(id='london-dispatches-from-warsaw-retreat-of-the-king-of-prussia-october-1794', kind='document_group',
      label="London, 1 October 1794: dispatches from Warsaw confirm the retreat of the King of Prussia",
      definition="Printings of a London paragraph: 'The dispatches received on Monday from William Gardner, Esq. the British ambassador at Warsaw, confirm the retreat of the king of Prussia. It is also said, that his majesty has lost all the heavy artillery which he had collected for the siege of that capital'. A report from London papers.",
      role='report', words=50, dateline=True, head=r'THE\s+POLES\.?\s*',
      core=[r'The\s+dispatches\s+received\s+on\s+Monday,?\s+from\s+(?:William|Wm\.?|Mr\.?)\s+Gardner'],
      first="London, 1 October 1794: the retreat of the King of Prussia from Warsaw.",
      what="the London report of dispatches from Warsaw",
      printings=[k('GUS', '12-04', 2), k('CI', '12-16', 2), k('NHG', '12-16', 3), k('MIR', '12-19', 2), k('AHL', '12-20', 1)]),
 dict(id='vienna-retreat-of-the-prussians-from-warsaw-september-1794', kind='document_group',
      label="Vienna, 26 September 1794: the retreat of the Prussians from Warsaw",
      definition="Printings of a Vienna paragraph: 'Letters, and particularly the official accounts from Warsaw, of the 9th inst.—give the most ample details of the circumstances attending the retreat of the Prussians on the night between the 5th and 6th'. A report from Vienna, as the papers printed it.",
      role='report', words=50, dateline=True,
      core=[r'Letters,?\s+and\s+particularly\s+the\s+official\s+accounts\s+from\s+Warsaw'],
      first="Vienna, 26 September 1794: the retreat of the Prussians from Warsaw.",
      what="the Vienna report of the Prussians' retreat",
      printings=[k('GUS', '12-09', 3), k('CI', '12-23', 2), k('NHG', '12-23', 2), k('MIR', '12-26', 1), k('AHL', '12-27', 2)]),
 dict(id='london-duke-of-brunswick-to-command-the-allied-armies-october-1794', kind='document_group',
      label="London, October 1794: a report that the Duke of Brunswick will command the allied armies, after the Prince of Wales's marriage to his daughter",
      definition="Printings of a London paragraph: 'It has been said that in consequence of the Prince of Wales's intended marriage with the Princess of Brunswick, the Duke of Brunswick, her father, is once more to take the command of the Allied armies, and that the Duke of York has signified his readiness to serve under him'. A report from London papers, in their words.",
      role='report', words=50, dateline=True,
      core=[r'It\s+has\s+been\s+said,?\s+that\s+in\s+consequence\s+of\s+the\s+Prince\s+of\s+Wales'],
      first="London, October 1794: a report on the command of the allied armies.",
      what="the London report on the Duke of Brunswick",
      printings=[k('GUS', '12-09', 3), k('CI', '12-23', 2), k('NHG', '12-23', 2), k('MIR', '12-26', 2), k('AHL', '12-27', 1)]),
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
            problems.append((s['id'], key, 'page not in the 1794 pages'))
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
        r['id'] = f'S94-{n:03}'
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
               'admission_rule': 'Reviewed 1794 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1794/'
    return {
        'ledger_id': 'ledger:stories-1794', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1794', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1794, and of 1793 where they reach the 1794 pages (long-running ones '
                   'included), counted by machine over all 2,119 pages of 1794 in both transcriptions and joined into documents; the admitted '
                   'and chosen items counted again by their own opening, and scan checks of each admitted passage, by the thin-year rule '
                   "(Y-THIN, as amended with the owner's choice B1): eligible when printed by more than half of the papers that survive for "
                   "the item's weeks and by at least 4; eligible items printed by every paper that survives for their weeks admitted; the "
                   'others chosen to cover the months and the kinds of news'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1793.json': 'retrieval_candidates',
                             d+'counts_1794.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1794.py': 'ledger_code', 'work/archive_data/ledgers/stories_1794_review.json': 'scan_review',
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
