"""Write ledgers/stories_1793_round3.json: round three of the reviewed stories of 1793, the stories once held back for framing.

Rounds one and two (make_stories_1793.py, make_stories_1793_round2.py) left out several widely printed items "for
framing": the War Office paragraph on the treaty commissioners, the German Creek letter, the Saint-Domingue reports and the
Fugitive Slave Act (outputs/story_discovery_1793/README.md). On 11 November 2026 the owner set the rule "every story
alike": a reviewed story is described by what kind of text it is and whose account, in the papers' own words, with no
special treatment. This round reads those candidates again and admits each item that reaches the year's rule (6 or more
newspapers, counted item by item, the two titles of a renamed paper once), exactly as rounds one and two did:
  - the War Office paragraph on the commissioners for treating with the Indian nations north of the Ohio (6 papers);
  - the letter from German Creek, Territory South of the Ohio, 16 August 1793 (6 papers);
  - two accounts from Cap Francais, June 1793, under one parent story: Captain Fanning's (6 papers) and the brig Mary's
    passengers' (6 papers).
Not admitted, by the rule: the civil commissioners' proclamation of 21 June (4 papers), the letter of Polverel and
Sonthonax to Genet (4) and the text of the Fugitive Slave Act (2), as for the 4-paper documents of Dumouriez's defection.

Each item's printings were found with phrase searches over all 1,751 pages of 1793 in both transcriptions
(phrase_patterns_round3.json, phrase_hits_round3.json); every hit was read, and the papers in print in the items' weeks
without a hit were searched with loose keywords (no missed printing). Excerpts are cut with round one's functions; scan
findings, crops and hand-drawn boxes are merged from stories_1793_round3_review.json after the scan check. Observation ids
continue round two's: S93-112 onwards, in the same namespace.

The base and target releases are set when the ledger is applied (the 1806 review owns the next release number):
    python work/archive_data/ledgers/make_stories_1793_round3.py [--table] [--base 0.11.1 --target 0.11.2]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1793/search_pages.json).
"""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_stories_1793 as R1
from make_stories_1793 import NGZ, GUS, PG, MIR, NHG, AHL, CI, k

PROJECT = R1.PROJECT
REVIEW = HERE/'stories_1793_round3_review.json'
OUT = HERE/'stories_1793_round3.json'
LOOKUP = PROJECT/'outputs/data_foundation/v0.10.2'   # matched families as corrected in v0.8.1 and v0.10.2
BASE, TARGET = '0.11.1', '0.11.2'                       # defaults; see the docstring
FIRST_ID = 112   # rounds one and two used S93-001 to S93-111
RECORDED = '2026-11-12'

STORIES = [
 # --- July and August: Cap Francais ----------------------------------------------------------------------------------
 dict(id='news-from-cap-francais-1793', kind='context_group', label="News from Cap Français, June 1793",
      definition=("Two accounts of events at Cap Français, in the French colony of Saint-Domingue, from 18 to 23 June 1793, as American papers "
                  "printed them in July and August from arrivals at New York: Captain Fanning's account, and the report of the passengers of "
                  "the brig Mary, who put the dead at six to nine hundred, 'instead of 10 thousand as we heard', as most papers print it. "
                  "Contains those two groups; the wider coverage is not included. Each is an account at second hand."),
      children=['fanning-account-cap-francais', 'brig-mary-passengers-cap-francais']),
 dict(id='fanning-account-cap-francais', parent='news-from-cap-francais-1793', kind='message_group', label="Captain Fanning's account of Cap Français",
      role='report', words=60,
      core=[r'Capt\w*\.?\s+(?:John\s+)?F\s?ANNING,?\s+of\s+the\s+[Bb]rig\s+Union'],
      definition=("Printings of the account given at New York by Captain John Fanning of the brig Union, 14 days from Cap Français (New York, "
                  "9 July 1793): on 18 June the civil commissioners Sonthonax and Polverel arrived at the Cape and suspended the governor, "
                  "Galbaud; by his account they then encouraged 'a number of mulattoes' to come into town, who armed the enslaved people of the "
                  "town 'to assist in destroying all the whites'; between 8 and 10 thousand people were killed from 20 June; and the town was "
                  "plundered and burnt, with not more than 50 houses standing when he sailed on the 23rd with a fleet of 250 sail. One ship "
                  "captain's account. Three papers print it under the heading 'HORRID NEWS!'."),
      first="Captain Fanning of the brig Union, 14 days from Cap Français, gives an account at New York of the commissioners' arrival at the Cape on 18 June 1793 and of the killing and burning that followed.",
      what="Captain Fanning's account",
      printings=[(k(NGZ, '07-10', 3), dict(note="Introduced as 'copied from a New-York paper of last Monday'.")),
                 (k(GUS, '07-23', 3), dict(note="Under the dateline 'NEW-YORK, July 9.'")),
                 (k(NHG, '07-16', 3), dict(note="Under 'BOSTON, July 15. HORRID NEWS!'")),
                 (k(AHL, '07-16', 3), dict(note="Under 'BOSTON JULY 13. HORRID NEWS!'")),
                 (k(MIR, '07-22', 2), dict(note="Under 'HORRID NEWS! BOSTON, July 15.' The account begins at the foot of page 2 and continues on page 3.")),
                 k(PG, '07-22', 2)]),
 dict(id='brig-mary-passengers-cap-francais', parent='news-from-cap-francais-1793', kind='message_group', label="The brig Mary's passengers on Cap Français",
      role='report', words=62,
      core=[r'(?:On\s+Sunday\s+)?[Tt]he\s+[Bb]rig\s+Mary,?\s+Capt\w*\.?\s+Lang'],
      definition=("Printings of a New York report of late July 1793 on the brig Mary, Captain Langdon, from Cap Français, which she left on "
                  "9 July: her forty passengers said that from six to nine hundred people lost their lives 'in the affair of the 20th' (most "
                  "papers add 'instead of 10 thousand as we heard'; the Patowmac Guardian prints 'two thousand'), that not more than two thirds "
                  "of the town was burnt, that 'upwards of 20,000 mulattoes and blacks are now under arms there', that 'the negroes never came "
                  "in from the country on the late occasion', and that the Spaniards had taken a town and were on the march. The passengers' "
                  "account, at second hand."),
      first="New York: the passengers of the brig Mary, from Cap Français on 9 July 1793, say that from six to nine hundred people lost their lives on 20 June, not ten thousand.",
      what="the brig Mary's report",
      printings=[k(GUS, '07-27', 3), k(NGZ, '07-31', 3), k(PG, '08-05', 2), k(NHG, '08-06', 3), k(AHL, '08-06', 2), k(CI, '08-14', 3)]),
 # --- September: the frontier ------------------------------------------------------------------------------------------
 dict(id='war-office-treaty-commissioners-1793', kind='message_group', label="The War Office on the treaty commissioners, September 1793",
      role='report', words=65,
      core=[r'(?:On\s+the\s+3d\s+inst\w*\.?,?\s+)?(?:By\s+)?[Aa]n\s+[Ee]xpress\s+arrived\s+(?:\w+\s+)?at\s+the\s+War.?Office'],
      definition=("Printings of a Philadelphia paragraph of early September 1793: by an express to the War Office from the commissioners for "
                  "treating with the Indian nations north of the Ohio, they 'were not able even to effect a meeting' with the nations assembled "
                  "at the rapids of the Miami river; the nations' deputation 'insisted upon the Ohio as the boundary between them and the United "
                  "States', and, 'as so extensive a concession was inadmissible', the commissioners left on 17 August. It names the Wyandots, "
                  "Delawares, Shawanese and Miamis as 'determined for war', says that a considerable part of them were for peace, and that the "
                  "Six Nations, with Captain Brandt (Brant) and his Mohawks, urged peace. The United States government's account, as the papers "
                  "printed it."),
      first="Philadelphia, September 1793: an express to the War Office reports that the commissioners could not meet the nations assembled at the rapids of the Miami, who insisted on the Ohio as the boundary.",
      what="the War Office paragraph",
      printings=[k(NGZ, '09-04', 3), k(GUS, '09-07', 3), k(PG, '09-16', 3), k(NHG, '09-17', 2), k(AHL, '09-17', 3),
                 (k(CI, '09-25', 3), dict(note="Under the dateline 'PHILADELPHIA, Sept. 4.' and the paper's own heading 'INDIAN WAR INEVITABLE!'"))]),
 dict(id='german-creek-letter-1793', kind='message_group', label="A letter from German Creek, 16 August 1793: an expedition across the Tennessee",
      role='report', words=68,
      core=[r'Ex\w*\.?\s+of\s+a\s+[Ll]etter\s+from\s+(?:a\s+correspondent|the\s+Territory\s+South|German\w*\s+Creek)'],
      definition=("Printings of an extract of a letter dated German Creek, Territory South of the Ohio, 16 August 1793, written to the editor of "
                  "a Winchester paper (2 September) and printed from it: the writer reports that on 4 August Colonel Daugherty of Jefferson "
                  "county crossed the Tennessee with 180 men to 'the valley Indian towns', where by his account they killed nine men and two "
                  "women, took seven prisoners, burnt twenty towns and villages and destroyed crops, with five of their own men wounded. He "
                  "adds that the frontier inhabitants are 'in close forts', and argues for a large company raised 'under the sanction of "
                  "government' to give the towns, in his words, 'a severe flogging, in order to bring them to a sense of their duty, and teach "
                  "them to pay some respect to treaties'. One writer's account."),
      first="A letter from German Creek, Territory South of the Ohio (16 August 1793), reports an expedition of 180 men under Colonel Daugherty across the Tennessee to the valley towns.",
      what='the German Creek letter',
      printings=[k(NGZ, '09-11', 3), k(GUS, '09-11', 3), k(PG, '09-16', 3), k(NHG, '09-24', 2), k(AHL, '09-24', 2),
                 (k(CI, '10-02', 3), dict(note="Under the paper's own heading 'INDIAN NEWS.'"))]),
]


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def build_rows(pages):
    R1.STORIES = STORIES      # round one's functions read the story list and the release from their module
    R1.RELEASE = LOOKUP
    rows, problems = R1.build_rows(pages)
    for n, r in enumerate(rows, FIRST_ID):
        r['id'] = f'S93-{n:03}'
    return rows, problems


def build(rows, review):
    R1.STORIES = STORIES
    out = R1.build(rows, review)
    base, target = releases()
    out.update({
        'ledger_id': 'ledger:stories-1793-round3', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED,
        'method': ("Round three of 1793, under the rule 'every story alike' (11 November 2026): the items that rounds one and two held back for "
                   "framing, counted item by item at the year's rule of 6 newspapers with phrase searches on all 1,751 pages in both "
                   "transcriptions, reading of every hit, loose keyword searches of the papers in print without a hit, and scan checks of each "
                   "admitted passage"),
        'supporting_files': {'work/story_phrase_search.py': 'retrieval_code', 'outputs/story_discovery_1793/items.json': 'retrieval_candidates',
                             'outputs/story_discovery_1793/phrase_patterns_round3.json': 'retrieval_patterns',
                             'outputs/story_discovery_1793/phrase_hits_round3.json': 'retrieval_candidates',
                             'outputs/story_discovery_1793/masthead_dates.csv': 'date_check',
                             'work/archive_data/ledgers/make_stories_1793.py': 'ledger_code',
                             'work/archive_data/ledgers/make_stories_1793_round3.py': 'ledger_code',
                             'work/archive_data/ledgers/stories_1793_round3_review.json': 'scan_review',
                             'outputs/story_discovery_1793/SCAN_PROTOCOL.md': 'review_protocol',
                             'outputs/story_discovery_1793/scan_points_round3.json': 'review_protocol'},
    })
    for g in out['new_groups']:
        g['admission_rule'] = 'Reviewed 1793 printings, checked against the scan (round three: stories once held back for framing, at the 6-paper threshold for 1793).'
    return out


if __name__ == '__main__':
    pages = {p['key']: p for p in json.loads(R1.PAGES.read_text(encoding='utf8'))}
    rows, problems = build_rows(pages)
    for p in problems:
        print('PROBLEM', *p)
    if '--table' in sys.argv:
        for r in rows:
            print(f"{r['id']} {r['story'][:26]:26} {r['page_key']:30} {r['field'][:4]} {r['roles'][0][:9]:9} | {r['excerpt']} || {r['note']}")
    review = json.loads(REVIEW.read_text(encoding='utf8')) if REVIEW.exists() else {}
    if problems and '--force' not in sys.argv:
        raise SystemExit(f'{len(problems)} printings without anchors')
    OUT.write_text(json.dumps(build(rows, review), ensure_ascii=False, indent=2), encoding='utf8')
    print('wrote', OUT, len(rows), 'observations,', len(STORIES), 'groups')
