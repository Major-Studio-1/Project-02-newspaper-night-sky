"""Write ledgers/stories_1796.json: reviewed stories of 1796, round one.

1796 is read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN) as the owner amended it on 23 November 2026 (B1): an
item, counted by its own words, is eligible when it was printed by more than half of the newspapers that survive for its weeks,
and by at least 4 newspapers; digests are not. Items printed by every newspaper that survives for their weeks are admitted; the
other eligible items are chosen to cover the months and the kinds of news, about as many stories as a standard year (20 to 35, a
target, not a quota); one affair's items as in X-1800-01. Sub-stories (C-01), private persons (R-04) and the list of items read
and not admitted (R-03) apply as in every year.

The automatic families first printed in 1796 that reach 3 or more papers, long-running ones included, were split into single
printed items with work/story_items.py --long-running (items.json), and again with year 1795 over the 1796 pages
(items_from_1795.json); every item in 3 or more papers was counted by its own opening over all 1,552 pages of 1796 in both
transcriptions and merged into text units, a sweep of passages shared word for word by 4 or more papers found short items the
families miss, and every unit that meets the bar was read (outputs/story_discovery_1796/README.md). 1796 has 7 catalogue series,
which are 6 papers: the Gazette of the United States (Philadelphia) stands under two catalogue numbers, the second from 1 July
(C-04); the others are the New Hampshire Gazette (Portsmouth), the Kentucky Gazette (Lexington), the Federal Mirror (Concord, to
November), the Patowmac Guardian (29 issues) and six issues of the Eagle, or, Dartmouth Centinel (Hanover). 4 or 5 papers survive
for most weeks; the bar is 4. The New Hampshire Gazette of 16 April is filed twice (also under 9 April); the ledger uses the
16 April keys.

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 25-60 words), starting with its dateline or heading when one
stands directly before it. Scan findings, crops and hand-drawn boxes are merged from stories_1796_review.json after the
scan check.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The base and target releases are set when the ledger is applied (other thin years are reviewed at the same time and may take
the next number first):
    python work/archive_data/ledgers/make_stories_1796.py [--table] [--base 0.11.35 --target 0.11.36]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1796/search_pages.json). The excerpts are cut from
the 1796 pages, which no release changes, so the ledger is the same whatever the base, except for its two release fields.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1796'
D = PROJECT/'outputs/story_discovery_1796'
PAGES = D/'search_pages.json'
REVIEW = HERE/'stories_1796_review.json'
OUT = HERE/'stories_1796.json'
BASE, TARGET = '0.11.35', '0.11.36'   # defaults (v0.11.35 is current since the second thin years were released, 24 November); see the docstring
DATA_RELEASE = '0.11.15'   # the release whose families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-24'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn84026273': 'The Gazette of the United States', 'sn83025881': 'The Gazette of the United States, & Philadelphia Daily Advertiser',
         'sn83025588': 'The New Hampshire Gazette', 'sn82014782': 'The Kentucky Gazette', 'sn83025524': 'The Federal Mirror',
         'sn84038410': 'The Potomac Guardian, & Berkeley Advertiser', 'sn84023150': 'The Eagle, or, Dartmouth Centinel'}
ONE = {'NHG': 'sn83025588', 'KG': 'sn82014782', 'FM': 'sn83025524', 'PG': 'sn84038410', 'EAG': 'sn84023150'}
# C-04: the Gazette of the United States stands under two catalogue numbers: (first date of the second number, first, second)
SWITCH = {'GUS': ('1796-07-01', 'sn84026273', 'sn83025881')}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def k(paper, date, page, ed=1):
    """Page key of a printing: paper code, date (MM-DD in 1796), page and edition; for a paper under two catalogue numbers, the
    number it has on that date."""
    full = f'{YEAR}-{date}'
    if paper in SWITCH:
        cut, before, after = SWITCH[paper]
        lccn = before if full < cut else after
    else:
        lccn = ONE[paper]
    return f'{lccn}|{full}|{ed}|{page}'


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
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
 dict(id='boston-report-schooner-industry-from-st-malo-oral-intelligence-from-france-1796', kind='message_group',
      label="Boston, January 1796: the schooner Industry, 51 days from St. Malo, brings no newspapers; her captain's oral intelligence from France 'is melancholy'",
      definition="Printings of a Boston paragraph of early January 1796: 'On Sunday last arrived in this harbour Schooner Industry, Capt. Atkins, in 51 days from St. Maloes, in France'; he brought no newspapers, and 'His oral intelligence is melancholy': the exchange of assignats and the distress of the common people. A report of a ship's news.",
      role='report', words=50, dateline=False,
      core=['On\\s+Sunday\\s+last\\s+arrived\\s+in\\s+this\\s+harbou?r'],
      first='Boston, January 1796: oral news from France.',
      what='the Boston report of the Industry',
      printings=[k('NHG', '01-09', 3), k('GUS', '01-14', 3), k('PG', '01-28', 2), k('KG', '02-20', 1)]),
 dict(id='paris-papers-borders-of-the-rhine-changes-in-the-french-army-november-1795', kind='message_group',
      label="Paris papers, November 1795, from the borders of the Rhine: 'There are yet changes in the disposition of the French army'",
      definition="Printings of an article of the Paris papers dated from the borders of the Rhine, 8 November 1795: 'There are yet changes in the disposition of the French army'; the movements of the divisions follow. A report from the Paris papers, in translation.",
      role='report', words=50, dateline=False,
      core=['T\\s?HERE\\s+are\\s+yet\\s+changes\\s+in\\s+the\\s+disposition'],
      first="The Rhine, November 1795: the French army's disposition.",
      what="the Paris papers' article from the Rhine",
      printings=[k('GUS', '02-22', 3), k('PG', '03-10', 2), k('NHG', '03-12', 2), k('FM', '03-29', 2)]),
 dict(id='charleston-paper-forms-of-ratification-of-the-treaty-with-great-britain-1796', kind='document_group',
      label='Charleston, February 1796: the forms of ratification of the treaty between the United States and Great Britain, by the King and by the President',
      definition="Printings of a Charleston paper's copy of the forms of ratification of the treaty of amity, commerce and navigation between the United States and Great Britain: 'We have been favored with a Copy of the treaty between the United States and Great Britain, as ratified by the President and the British King'; His Majesty's ratification ('George the third, by the grace of God king of Great Britain'), with the additional article, and the President's. The Kentucky Gazette prints the ratifications without the Charleston paper's words (C-02). The two governments' own acts, as a paper printed them.",
      role='published_document', words=55, dateline=False,
      head='(?:His\\s+Majesty.s\\s+Ratification\\.?\\s*)?(?:G\\s?EORGE,?\\s+R\\.?\\s*)?',
      core=['We\\s+have\\s+been\\s+favou?red\\s+with\\s+a\\s+[Cc]opy\\s+of\\s+the\\s+treaty', 'G\\s?EORGE\\s+the\\s+[Tt]hird,?\\s+by\\s+the\\s+[Gg]race\\s+of\\s+God,?\\s+[Kk]ing\\s+of\\s+Great\\s+Britain'],
      first='The British treaty, 1796: its ratifications.',
      what='the forms of ratification of the British treaty',
      printings=[k('GUS', '02-23', 3), k('NHG', '03-05', 3), k('PG', '03-10', 1), (k('KG', '03-19', 3), {'note': "Printed without the Charleston paper's words, from His Majesty's ratification (C-02); the President's ratification follows on 26 March."})]),
 dict(id='house-of-representatives-mr-blount-resolutions-on-treaties-april-1796', kind='document_group',
      label="House of Representatives, 6 April 1796: Mr. Blount's resolutions that the House claims no agency in making treaties, but that treaties touching the powers of Congress depend on its laws",
      definition='Printings of the resolutions Mr. Blount moved in the committee of the whole on the President\'s message, 6 April 1796: \'Resolved, That, it being declared by the second section of the second article of the constitution, "That the President shall have power, by and with the advice and consent of the Senate, to make treaties, provided two thirds of the Senate present concur," the House of Representatives do not claim any agency in making treaties; but that when a treaty stipulates regulations on any of the subjects submitted by the constitution to the power of Congress, it must depend for its execution, as to such stipulations, on a law or laws to be passed by Congress\'. The House\'s resolutions as moved, printed within its proceedings.',
      role='published_document', words=55, dateline=False,
      core=['R\\s?ESOLVED,?\\s+[Tt]hat,?\\s+it\\s+being\\s+declared\\s+by\\s+the\\s+(?:second|2d)\\s+section'],
      first="The House, April 1796: Mr. Blount's resolutions on treaties.",
      what="Mr. Blount's resolutions",
      printings=[k('GUS', '04-07', 3), k('PG', '04-14', 3), k('NHG', '04-23', 1), k('KG', '04-30', 3), (k('GUS', '05-20', 2), {'note': "Printed again, as the resolutions were entered on the House's journals (C-08)."})]),
 dict(id='port-au-prince-letter-unsuccessful-attack-on-leogane-1796', kind='message_group',
      label='Port-au-Prince, March 1796: a letter tells that the British fleet came back after an unsuccessful attack on Leogane',
      definition="Printings of an extract of a letter from Port-au-Prince of 27 March 1796: 'The inhabitants here were much disappointed by the arrival of the fleet yesterday, after an unsuccessful attack on Leogane—The French forces there prove to be stronger than was expected'. A letter printed at second hand.",
      role='report', words=50, dateline=False,
      core=['E\\s?xtract\\s+of\\s+a\\s+letter\\s+from\\s+Port', 'T\\s?HE\\s+inhabitants\\s+here\\s+were\\s+much\\s+disappointed'],
      first='Port-au-Prince, March 1796: the attack on Leogane.',
      what='the letter from Port-au-Prince',
      printings=[k('GUS', '04-13', 3), k('PG', '04-21', 3), k('NHG', '04-23', 2), k('FM', '04-26', 3)]),
 dict(id='treaty-of-friendship-limits-and-navigation-with-spain-1795', kind='document_group',
      label='The treaty of friendship, limits and navigation between the United States and his Catholic Majesty, signed in October 1795',
      definition="Printings of the treaty between the United States and Spain: 'His Catholic Majesty and the United States of America desiring to consolidate on a permanent basis, the friendship and good correspondence which happily prevails between the two parties, have determined to establish by a Convention, several points'; the boundaries, the navigation of the Mississippi and the articles that follow. The two governments' own treaty.",
      role='published_document', words=55, dateline=False,
      head='(?:A\\s+)?T\\s?\\s?R\\s?\\s?E\\s?\\s?A\\s?\\s?T\\s?\\s?Y,?\\s+[Bb]\\s?ETWEEN\\s+the\\s+U\\s?NITED\\s+S\\s?TATES\\s+[Aa]nd\\s+his\\s+C\\s?ATHOLIC\\s+M\\s?AJESTY\\.?\\s*',
      core=['H\\s?IS\\s+Catholic\\s+Majesty\\s+and\\s+the\\s+United\\s+States\\s+of\\s+America,?\\s+desiring'],
      first='The treaty with Spain, 1795.',
      what='the treaty with Spain',
      printings=[k('PG', '04-14', 1), (k('NHG', '04-16', 1), {'note': 'The New Hampshire Gazette of 16 April 1796 (No. 2055) is filed again under 9 April; this printing uses the 16 April key.'}),
                 k('EAG', '04-25', 1), k('FM', '05-31', 1)]),
 dict(id='philadelphia-paragraph-the-ship-america-brings-home-an-elephant-1796', kind='message_group',
      label="Philadelphia, April 1796: the ship America has brought home an elephant from Bengal, 'the first ever seen in America'",
      definition="Printings of a Philadelphia paragraph of April 1796: 'The America has brought home an ELEPHANT, from Bengal, in perfect health. It is the first ever seen in America, and a great curiosity.' The Patowmac Guardian prints it in its own words, naming the ship's captain ('Capt. Crowninshield, of the ship America, arrived from the Isle of France, brought home an ELEPHANT', C-02). A report of a ship's arrival.",
      role='report', words=35, dateline=False,
      core=['The\\s+America,?\\s+has\\s+brought\\s+home\\s+an', 'Capt\\.?\\s+Crownfield,?\\s+of\\s+the\\s+ship\\s+America'],
      first='Philadelphia, April 1796: an elephant from Bengal.',
      what='the paragraph on the elephant',
      printings=[k('GUS', '04-18', 3), (k('PG', '04-28', 3), {'note': "Printed in the paper's own words: 'Capt. Crowninshield, of the ship America, arrived from the Isle of France, brought home an ELEPHANT' (C-02). The captain's name is read from the scan; RevX reads it 'Crownfield'."}),
                 k('NHG', '04-30', 2), k('FM', '05-03', 3)]),
 dict(id='london-paragraph-the-paris-papers-to-the-6th-march-1796', kind='message_group',
      label='London, 13 March 1796: the Paris papers to the 6th bring nothing important, except that a restraint is to be put on the liberty of the press',
      definition="Printings of a London paragraph of 13 March 1796: 'The Paris papers to the 6th, were received in town on Thursday, which brought nothing important: They only mention, that a restraint is going to be put on the liberty of the press'. A report from the London papers.",
      role='report', words=40, dateline=False,
      core=['The\\s+Paris\\s+papers\\s+to\\s+the\\s+6th'],
      first='London, March 1796: the Paris papers and the press.',
      what='the London paragraph on the Paris papers',
      printings=[k('GUS', '04-27', 3), k('NHG', '04-30', 2), k('FM', '05-03', 3), k('KG', '05-21', 2)]),
 dict(id='albany-paragraph-express-with-lord-dorchester-dispatches-western-posts-1796', kind='message_group',
      label="Albany, 11 April 1796: an express with Lord Dorchester's dispatches for the President, said to include his proclamation for surrendering the Western Posts",
      definition="Printings of an Albany paragraph of 11 April 1796: 'An express passed through this city last week, with dispatches for THE PRESIDENT of the United States, from Lord Dorchester—it is reported his Lordship's Proclamation for the surrender of the Western Posts, was among these dispatches'. A report of what is reported.",
      role='report', words=45, dateline=False,
      core=['An\\s+express\\s+passed\\s+through\\s+this\\s+city'],
      first='Albany, April 1796: dispatches on the western posts.',
      what="the Albany paragraph on Lord Dorchester's dispatches",
      printings=[k('NHG', '04-30', 2), k('FM', '05-03', 3), k('KG', '05-07', 3), k('PG', '06-23', 2)]),
 dict(id='new-york-paragraph-london-paper-probability-of-war-between-spain-and-england-1796', kind='message_group',
      label='New York, May 1796: a London paper of March, by the ship Assistance, brings accounts of the probability of a war between Spain and England',
      definition="Printings of a New York paragraph of early May 1796: 'A London paper of the 19th March, received by the ship Assistance, brings accounts of the probability of a War between Spain and England. It is believed at Paris that it is an agreed point between France and Spain, that Spain shall break with Great Britain'. A report from a London paper.",
      role='report', words=40, dateline=False,
      core=['A\\s+London\\s+paper\\s+of\\s+the\\s+\\d+th\\s+(?:of\\s+)?March'],
      first='New York, May 1796: Spain and England.',
      what='the New York paragraph on Spain and England',
      printings=[k('GUS', '05-05', 3), (k('PG', '05-12', 3), {'note': "The RevX transcriptions of this issue are shifted by one page (the RevX text filed as page 2 is page 3's), which the release's map of misfiled pages does not list; the item stands on page 3, and its excerpt is cut from page 3's CA text.", 'field': 'ca_ocr_text', 'core': ['i\\\\\\s+London\\s+p\\S*\\s+of']}),
                 k('NHG', '05-14', 3), k('KG', '05-28', 2)]),
 dict(id='paris-paragraph-pichegru-resigns-the-command-of-the-army-of-the-rhine-1796', kind='message_group',
      label="Paris, 24 March 1796: 'A public misfortune is announced': Pichegru has sent in his resignation of the command of the army of the Rhine and the Moselle",
      definition="Printings of a Paris paragraph of 24 March 1796: 'A public misfortune is announced: it appears, alas! to be too true. Pichegru has sent in his resignation of the command of the army of the Rhine and the Mozelle'. A report from the Paris papers, in translation.",
      role='report', words=40, dateline=False,
      core=['A\\s+public\\s+misfortune\\s+is\\s+announced'],
      first='Paris, March 1796: Pichegru resigns.',
      what='the Paris paragraph on Pichegru',
      printings=[k('GUS', '05-13', 3), k('PG', '05-19', 2), k('NHG', '05-21', 2), k('FM', '05-31', 2)]),
 dict(id='new-york-paragraph-letter-from-paris-on-a-conspiracy-against-the-british-treaty-1796', kind='message_group',
      label='New York, May 1796: a letter from Paris said to disclose an attempt of certain American citizens to instigate the French government to oppose the British treaty',
      definition="Printings of a New York paragraph of May 1796 (the Kentucky Gazette names the New-York Minerva): 'We have put into our hands a letter from Paris, disclosing a nefarious conspiracy—no less than an attempt of certain American citizens to instigate the French government to take a decided part in opposing the execution of the British treaty'. The paper's allegation, from a letter.",
      role='report', words=45, dateline=False,
      core=['We\\s+have\\s+put\\s+into\\s+our\\s+hands?\\s+a\\s+letter\\s+from\\s+Paris'],
      first='New York, May 1796: a letter from Paris on the British treaty.',
      what='the New York paragraph on the letter from Paris',
      printings=[k('GUS', '05-18', 3), k('NHG', '05-28', 2), k('FM', '05-31', 3), k('KG', '06-11', 1)]),
 dict(id='london-papers-communicated-by-lord-grenville-on-a-general-pacification-1796', kind='document_group',
      label="London, April 1796: the papers Lord Grenville communicated to the foreign ministers: Mr. Wickham's note to M. Barthelemy on a general pacification, and the answers",
      definition="Printings of a London article of 11 April 1796: 'Late last night we received the following very important papers, which were yesterday communicated by lord Grenville to all the foreign ministers resident at this court': Mr. Wickham's note to M. Barthelemy of 8 March on the dispositions of France toward a general pacification, the French answer and the British court's reply. The governments' own papers, as a London paper printed them.",
      role='published_document', words=50, dateline=False,
      core=['Late\\s+last\\s+night\\s+we\\s+received\\s+the\\s+following\\s+very\\s+important\\s+papers', 'The\\s+following\\s+very\\s+IMPORTANT\\s+PAPERS'],
      first='London, April 1796: notes on a general peace.',
      what='the papers on a general pacification',
      printings=[k('GUS', '06-04', 2), k('PG', '06-09', 2), (k('FM', '06-14', 3), {'note': "Printed under the paper's own heading, 'Prospect of Peace terminated. London, April 14.', and in its own words: 'The following very IMPORTANT PAPERS, were yesterday communicated by Lord Grenville' (C-02).", 'head': 'Prospect\\s+of\\s+Peace\\s+terminated\\.?\\s*London,?\\s+April\\s+14\\.?'}),
                 k('KG', '07-02', 1)]),
 dict(id='albany-paragraph-gentleman-from-niagara-british-preparing-to-evacuate-the-garrisons-1796', kind='message_group',
      label='Albany, June 1796: a gentleman who left Niagara reports that the British are preparing to evacuate the garrisons',
      definition="Printings of an Albany paragraph of June 1796: 'A gentleman who left Niagara the 15th ult. informs, that every preparation was making by the British for evacuating the garrisons'. A report at second hand.",
      role='report', words=35, dateline=False,
      core=['A\\s+gentleman\\s+who\\s+left\\s+Niagara'],
      first='Albany, June 1796: the British preparing to leave Niagara.',
      what='the Albany paragraph on Niagara',
      printings=[k('GUS', '06-11', 3), k('FM', '06-21', 3), k('PG', '06-23', 3), k('KG', '07-02', 3)]),
 dict(id='london-oracle-mr-grey-notice-of-resolutions-impeaching-ministers-1796', kind='message_group',
      label="London, April 1796, from the Oracle: Mr. Grey gives notice of resolutions leading to an impeachment of His Majesty's ministers for misapplying public money",
      definition="Printings of a London report of April 1796 (from the Oracle of 23 April): 'Mr. GREY gave notice, that as the papers which he lately moved for were now before the house, he should on Thursday se'nnight, move some resolutions' leading to 'an IMPEACHMENT AGAINST HIS MAJESTY'S MINISTERS, for illegal misapplication of the public money'. A report of Parliament's proceedings.",
      role='report', words=45, dateline=False,
      core=['Mr\\.?\\s+G\\s?REY\\s+gave\\s+notice'],
      first="London, April 1796: Mr. Grey's notice.",
      what="the London report of Mr. Grey's notice",
      printings=[k('GUS', '06-14', 2), k('NHG', '06-25', 2), k('FM', '06-28', 1), k('PG', '06-30', 3)]),
 dict(id='paris-paragraph-royalist-assemblages-in-the-department-of-cher-1796', kind='message_group',
      label="Paris, 10 April 1796: 'Afflicting news' from the Department of Cher: the assemblages of Royalists have become more numerous",
      definition="Printings of a Paris paragraph of 10 April 1796: 'Afflicting news has been received from the Department of Cher. The assemblages of Royalists which have been formed there are become more numerous'; the town of Sancerre is said to be in their hands. A report from the Paris papers, in translation.",
      role='report', words=45, dateline=False,
      core=['A\\s?FFLICTING\\s+news\\s+has\\s+been\\s+received'],
      first='Paris, April 1796: Royalists in the Cher.',
      what='the Paris paragraph on the Cher',
      printings=[k('GUS', '06-16', 3), k('PG', '06-23', 2), k('NHG', '07-02', 2), k('KG', '07-09', 1), k('FM', '07-12', 2)]),
 dict(id='philadelphia-paragraph-brig-sophia-sails-for-algiers-with-the-means-of-the-treaty-1796', kind='message_group',
      label='Philadelphia, 30 June 1796: the United States brig Sophia has sailed for Lisbon and Algiers with the means of fulfilling the treaty with the Dey',
      definition="Printings of a Philadelphia paragraph of 30 June 1796: 'The United States brig Sophia, sailed a few days ago from this port to Europe—She is to touch at Lisbon, for a short time, and from thence proceed to Algiers'; she 'has on board the means of fulfilling the terms of our treaty with the Dey and Regency'. A news paragraph.",
      role='report', words=45, dateline=False,
      core=['The\\s+United\\s+States.?\\s+brig\\s+Sophia,?\\s+\\S*ailed'],
      first='Philadelphia, June 1796: the Sophia sails for Algiers.',
      what='the paragraph on the Sophia',
      printings=[k('GUS', '07-01', 3), k('NHG', '07-09', 3), k('FM', '07-12', 3), k('PG', '07-14', 3), k('KG', '07-23', 2)]),
 dict(id='paris-army-of-italy-buonaparte-letter-tortona-taken-1796', kind='message_group',
      label='Paris, May 1796, Army of Italy: a letter from General Buonaparte to the Directory says the army has taken possession of Tortona',
      definition="Printings of a Paris article of May 1796: 'ARMY OF ITALY. A letter from Gen. Buonaparte, of the 17th Floreal, addressed to the Executive Directory', mentions that the army of Italy has taken possession of Tortona, 'a very fine fortress'. A report of a general's letter, from the Paris papers.",
      role='report', words=45, dateline=False,
      head='(?:A\\s?RMY\\s+OF\\s+I\\s?TALY\\.?\\s*)?',
      core=['A\\s+letter\\s+from\\s+[Gg]en(?:eral|\\.)?\\s+Buonaparte'],
      first='Italy, May 1796: Tortona taken.',
      what="the Paris article on Buonaparte's letter",
      printings=[k('NHG', '07-16', 2), k('GUS', '07-18', 2), k('PG', '07-28', 2), k('KG', '08-13', 2)]),
 dict(id='baltimore-report-brig-harriot-from-cape-francois-fleet-from-brest-1796', kind='message_group',
      label='Baltimore, July 1796: the brig Harriot, from Cape Francois, reports that a fleet of five sail from Brest arrived there, with captures made on the passage',
      definition="Printings of a Baltimore paragraph of mid-July 1796: 'Yesterday arrived the brig Harriot, Capt. Atkinson, 15 days from Cape Francois'; 'a few days before he sailed, a fleet of 5 sail arrived from Brest', which had captured three British transports and a Portuguese vessel on the passage. The Patowmac Guardian prints it in its own words (C-02). A report of a ship's news.",
      role='report', words=45, dateline=False,
      core=['Yesterday\\s+arrived,?\\s+the\\s+brig\\s+Harriot', 'Capt\\.?\\s+Atkinson,?\\s+from\\s+Cape'],
      first='Cape Francois, July 1796: a fleet from Brest.',
      what='the Baltimore report from Cape Francois',
      printings=[(k('PG', '07-28', 3), {'note': "Printed in the paper's own words: 'Capt. Atkinson, from Cape Francois, informs, that' (C-02)."}),
                 k('NHG', '07-30', 2), k('KG', '08-13', 2), k('FM', '08-16', 3)]),
 dict(id='newburyport-report-capt-seward-from-bermuda-attachments-expected-1796', kind='message_group',
      label='Newburyport, 23 July 1796: Captain Seward, from Bermuda, reports that its people expect attachments on their estates to refund American property condemned there',
      definition="Printings of a Newburyport paragraph of 23 July 1796: 'Important—and true. Last Wednesday Capt. Seward arrived here, 9 days from Bermuda, bringing information that the inhabitants of that place were expecting attachments from the Court of Great-Britain, on their private Estates', to refund American property illegally condemned by their vice-admiralty court. The Patowmac Guardian prints it in its own words (C-02). A report of a ship's news.",
      role='report', words=45, dateline=False,
      core=['(?:Important\\W+and\\s+true\\.?\\s+)?Last\\s+Wednesday,?\\s+Capt\\.?\\s+Seward', 'Capt\\.?\\s+Seward,?\\s+in\\s+\\d+\\s+days\\s+from\\s+Bermuda'],
      first='Bermuda, July 1796: attachments expected.',
      what='the Newburyport report from Bermuda',
      printings=[k('GUS', '07-29', 3), k('NHG', '07-30', 3), (k('PG', '08-04', 2), {'note': "Printed in the paper's own words: 'Capt. Seward, in 8 days from Bermuda, brings information' (C-02)."}),
                 k('KG', '08-27', 2)]),
 dict(id='captain-bruff-letter-to-the-secretary-of-war-fort-oswego-delivered-1796', kind='document_group',
      label='Captain Bruff to the Secretary of War, Fort Oswego, 15 July 1796: the British commandant of Fort Ontario has given up the post',
      definition="Printings of an extract of a letter from Captain James Bruff to the Secretary of War, Fort Oswego or Ontario, 15 July 1796, published at Philadelphia under 'IMPORTANT. PLEASING. AUTHENTIC. The western posts taken possession of': 'I have the pleasure to announce that the British commandant of Fort Ontario wrote to me on the 13th inst.' that the post was to be given up. An officer's own letter.",
      role='published_document', words=50, dateline=False,
      head='(?:IMPORTANT\\.?\\s+PLEASING\\.?\\s+AUTHENTIC\\.?\\s*(?:The\\s+western\\s+posts\\s+taken\\s+possession\\s+of\\.?\\s*)?)?',
      core=['E\\s?xtra\\w*\\s+of\\s+a\\s+[Ll]etter\\s+from\\s+Capt(?:ain|\\.)?\\s+James\\s+Bruff'],
      first='Fort Oswego, July 1796: the post given up.',
      what="Captain Bruff's letter",
      printings=[k('GUS', '08-03', 2), k('NHG', '08-13', 2), k('PG', '08-18', 3), k('FM', '08-23', 2)]),
 dict(id='new-york-report-brig-baron-de-carondelet-plundered-by-french-privateers-1796', kind='message_group',
      label='New York, August 1796: the brig Baron de Carondelet, from Leghorn, was boarded and plundered by two French privateers; her captain brings dispatches on the Algerine treaty',
      definition="Printings of a New York paragraph of 4 August 1796: the brig Baron de Carondelet, Capt. James M'Call, 80 days from Leghorn, 'was boarded, 3 leagues to the westward of the road, by two French privateers' and plundered; 'Capt. M'Call has brought dispatches from the American Consul to the Secretary of State, relating to the Algerine Treaty'. The Kentucky Gazette prints it in its own words ('Capt. M'Call sailed from Leghorn', C-02). A report of a ship's news.",
      role='report', words=45, dateline=False,
      core=['(?:Tuesday|Yesterday)\\s+arrived\\s+the\\s+brig\\s+Baron', 'Capt\\.?\\s+M.Call\\s+sailed\\s+from\\s+Leghorn'],
      first='Leghorn, 1796: the Baron de Carondelet plundered.',
      what='the New York report of the Baron de Carondelet',
      printings=[k('GUS', '08-05', 3), k('NHG', '08-13', 2), k('FM', '08-23', 3), (k('KG', '09-03', 1), {'note': "Printed in the paper's own words: 'Capt. M'Call sailed from Leghorn, on the 10th May last, and was boarded' (C-02)."})]),
 dict(id='paris-report-the-emperor-requests-an-armistice-june-1796', kind='message_group',
      label='Paris, June 1796: it is reported in the Council of Five Hundred that a courier has come from the Emperor to ask an armistice',
      definition="Printings of a Paris article of June 1796, translated at New York: 'It is generally reported in the Council of 500, that a courier is arrived who in the name of the Emperor requests an ARMISTICE', and 'that the PRELIMINARY OF PEACE is signed between the Directory and the Envoys of the Cabinet of Vienna'. A report of what is reported.",
      role='report', words=45, dateline=False,
      core=['It\\s+is\\s+generally\\s+reported\\s+in\\s+the\\s+[Cc]ouncil'],
      first='Paris, June 1796: an armistice asked.',
      what='the Paris report of an armistice',
      printings=[k('GUS', '08-17', 3), k('PG', '08-25', 2), k('NHG', '08-27', 3), k('KG', '09-17', 1)]),
 dict(id='boston-report-fort-dauphin-delivered-to-the-french-1796', kind='message_group',
      label='Boston, 1796: Captain Nason reports that Fort Dauphin was delivered to the French under the treaty that cedes Spanish Hispaniola',
      definition="Printings of a Boston paragraph: 'From FORT DAUPHIN. Capt. Nason informs us, Fort Dauphin was delivered to the French, just previous to his sailing, in pursuance of the Article in the French and Spanish Treaty, which cedes Spanish Hispaniola to the French'. A report of a ship's news.",
      role='report', words=45, dateline=False,
      head='(?:From\\s+F\\s?ORT\\s+D\\s?AUPHIN\\.?\\s*)?',
      core=['Capt(?:ain|\\.)\\s+N\\w+son\\s+informs\\s+us'],
      first='Hispaniola, 1796: Fort Dauphin delivered.',
      what='the Boston report of Fort Dauphin',
      printings=[k('NHG', '08-20', 3), k('FM', '08-23', 3), k('GUS', '08-24', 3), k('KG', '09-17', 2)]),
 dict(id='madrid-the-prince-of-peace-declaration-to-lord-bute-1796', kind='message_group',
      label='Madrid, 1 June 1796: the Prince of Peace declares to Lord Bute that Spain would compel England to a general peace by force of arms',
      definition='Printings of a Madrid paragraph of 1 June 1796: \'The Prince of Peace has declared to lord Bute that "if the English government should persist in rejecting all propositions for the conclusion of a general peace"\', Spain would \'determine to compel them to it by force of arms\'. A report from the European papers.',
      role='report', words=45, dateline=False,
      core=['The\\s+[Pp]rince\\s+of\\s+[Pp]eace\\s+has\\s+declared'],
      first='Madrid, June 1796: the Prince of Peace and Lord Bute.',
      what='the Madrid paragraph',
      printings=[k('GUS', '08-30', 3), k('NHG', '09-10', 2), k('KG', '09-24', 2), k('EAG', '09-26', 2)]),
 dict(id='st-croix-report-english-ships-carried-into-guadaloupe-1796', kind='message_group',
      label='Christiansted, St. Croix, 17 August 1796: by an arrival from Guadaloupe, 24 English ships have been carried into that port within three weeks',
      definition="Printings of a St. Croix paragraph of 17 August 1796: 'By an arrival yesterday from Guadaloupe, we learn, that 24 valuable English ships have been, within these three weeks, carried into that port. By a vessel from Antigua this morning, we are informed of the arrival of a reinforcement of seven thousand troops, at Barbados'. A report of ships' news.",
      role='report', words=38, dateline=False,
      core=['By\\s+an\\s+arrival\\s+yest(?:erday|\\.)\\s+from\\s+G\\w+'],
      first='Guadaloupe, August 1796: English ships taken.',
      what='the St. Croix report',
      printings=[k('PG', '09-22', 3), k('NHG', '09-24', 3), k('FM', '09-27', 3), k('KG', '10-15', 2)]),
 dict(id='general-moreau-official-details-of-the-action-at-neresheim-august-1796', kind='document_group',
      label="General Moreau to the Executive Directory, 13 August 1796: official details of the attack on the enemy's positions at Neresheim",
      definition="Printings of General Moreau's report to the Executive Directory, headquarters at Amiens, 26 Thermidor (13 August 1796), printed as 'OFFICIAL DETAILS': 'On the 21st inst. (August 8) we attacked the enemy in their positions at Neresheim'. The Federal Mirror prints it as 'the following letter From Gen. MOREAU. AMIENS, Aug. 15.' (C-02). The general's own report, in translation.",
      role='published_document', words=50, dateline=False,
      head='(?:(?:A\\s?RMY\\s+of\\s+the\\s+[A-Za-z]+\\s+(?:and|&)\\s+[A-Za-z]+\\.?\\s*)?O\\s?FFICIAL\\s+D\\s?ETAILS\\.?\\s*(?:A\\s?RMY\\s+of\\s+the\\s+[A-Za-z]+\\s+(?:and|&)\\s+[A-Za-z]+\\.?\\s*)?)?',
      core=['Moreau,?\\s+Commander\\s+in\\s+Chief,?\\s+to\\s+the\\s+Executive\\s+Directory', 'A\\s?MIENS,?\\s+Aug(?:ust|\\.)?\\s+15'],
      first="Neresheim, August 1796: General Moreau's report.",
      what="General Moreau's report",
      printings=[k('GUS', '10-14', 2), k('NHG', '10-22', 3), (k('FM', '10-25', 3), {'note': "Printed as 'the following letter From Gen. MOREAU. AMIENS, Aug. 15.' (C-02)."}),
                 k('PG', '10-27', 3), k('KG', '11-12', 2)]),
 dict(id='proclamation-of-sir-john-wentworth-at-halifax-on-hostilities-with-spain-1796', kind='document_group',
      label="Halifax, October 1796: the proclamation of Sir John Wentworth, lieutenant governor of Nova Scotia, on the King's orders against Spain",
      definition="Printings of a proclamation by Sir John Wentworth, lieutenant governor of Nova Scotia, at Halifax, October 1796: 'WHEREAS information has been communicated to me by his Grace the Duke of Portland' that 'the most indubitable proofs of the hostile intentions of the court of Spain against Great Britain' have determined the King to order his naval officers to seize Spanish ships. A governor's own proclamation.",
      role='published_document', words=55, dateline=False,
      head='(?:P\\s?ROCLAMATION\\.?\\s*)?(?:By\\s+his\\s+[Ee]xcellency\\s+Sir\\s+John\\s+W\\w+,?\\s+[Bb]aronet[^W]{0,260}?)?',
      core=['W\\s?HEREAS,?\\s+information\\s+has\\s+been\\s+communicated\\s+to\\s+me'],
      first='Halifax, October 1796: a proclamation against Spain.',
      what="Sir John Wentworth's proclamation",
      printings=[k('GUS', '10-28', 3), k('NHG', '10-29', 3), k('FM', '11-01', 3), k('KG', '12-17', 3)]),
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
            problems.append((s['id'], key, 'page not in the 1796 pages'))
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
        r['id'] = f'S96-{n:03}'
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
               'admission_rule': 'Reviewed 1796 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = 'outputs/story_discovery_1796/'
    return {
        'ledger_id': 'ledger:stories-1796', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': 'expansion-1796', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('Single printed items split from the automatic families of 1796, and of 1795 where they reach the 1796 pages (long-running ones '
                   'included), counts of every item in 3 or more papers by its own opening over all 1,552 pages of 1796 in both transcriptions, '
                   'a sweep of word-for-word passages shared by 4 or more papers for short items the families miss, reading of every item that '
                   'meets the bar, and scan checks of each admitted and chosen passage, by the thin-year rule as amended (register Y-THIN, B1: '
                   'more than half of the papers that survive for the item\'s weeks, and at least 4, make an item eligible; items printed by '
                   'every paper in print are admitted, the others chosen to cover the months and the kinds of news)'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'work/story_items.py': 'retrieval_code', 'work/story_phrase_search.py': 'retrieval_code',
                             d+'items.json': 'retrieval_candidates', d+'items_from_1795.json': 'retrieval_candidates',
                             d+'phrase_patterns.json': 'retrieval_patterns', d+'phrase_hits.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1796.py': 'ledger_code', 'work/archive_data/ledgers/stories_1796_review.json': 'scan_review',
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
