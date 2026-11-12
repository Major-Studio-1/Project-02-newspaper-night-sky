"""Write ledgers/stories_1808_round2.json: round two of the reviewed stories of 1808, the stories once held back for framing.

Round one (make_stories_1808.py) left out three widely printed items "for framing" (outputs/story_discovery_1808/README.md):
the Burlington report of a revenue cutter's crew fired on near the Canadian line ("Melancholy Event"), General Wilkinson's
correspondence with Robert Goodloe Harper, and Governor Sevier's letter on the Creeks. On 11 November 2026 the owner set
the rule "every story alike": a reviewed story is described by what kind of text it is and whose account, in the papers'
own words, with no special treatment. This round reads those candidates again and admits each item that reaches the year's
rule (7 or more newspapers, counted item by item), exactly as round one did. All three reach 7:
  - the Burlington report of 5 August (7 papers);
  - the Wilkinson-Harper correspondence of 26 and 27 October, as published from Baltimore (7 papers);
  - Governor Sevier's letter from Marble Springs, 14 May, printed from the Staunton Eagle (7 papers; round one's phrases
    found 5, missing the New Hampshire Gazette, whose transcription reads '140 Creeks', and the National Intelligencer's
    printing of 21 September).
These stories are new top-level stories: the parent story of round one on the charges against General Wilkinson lists its
children in its definition and stays as released.

Each item's printings were found with phrase searches over all 4,466 pages filed under 1808 in both transcriptions
(phrase_patterns_round2.json, phrase_hits_round2.json); every hit was read, and the papers in print in the items' weeks
without a hit were searched with loose keywords (no missed printing). Excerpts are cut with round one's functions (the
dateline may now carry a state abbreviation such as '(Ver.)'); scan findings, crops and hand-drawn boxes are merged from
stories_1808_round2_review.json after the scan check. Observation ids continue round one's: S08-299 onwards, in the same
namespace. As in round one, an excerpt ends before the names of private people: the Burlington excerpt ends before the
names of the dead.

The base and target releases are set when the ledger is applied (the 1806 review owns the next release number):
    python work/archive_data/ledgers/make_stories_1808_round2.py [--table] [--base 0.11.3 --target 0.11.4]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1808/search_pages.json).
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_stories_1808 as R1
from make_stories_1808 import NI, NG, ADA, ADG, EN, VA, PGZ, NHG, BJ, k

PROJECT = R1.PROJECT
REVIEW = HERE/'stories_1808_round2_review.json'
OUT = HERE/'stories_1808_round2.json'
LOOKUP = PROJECT/'outputs/data_foundation/v0.10.2'   # matched families as corrected in v0.8.1 and v0.10.2
BASE, TARGET = '0.11.3', '0.11.4'                       # defaults; see the docstring
FIRST_ID = 299   # round one used S08-001 to S08-298
RECORDED = '2026-11-12'

# Round one's dateline, allowing a full stop inside the parenthesis after the place: 'BURLINGTON, (Ver.) August 5.'
PLACE = R1.WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,.]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + R1.MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*180[78])?\.\s*(?:[—-]+\s*)?)$")

STAUNTON = "Printed from the Staunton (Virginia) Eagle."
STORIES = [
 dict(id='sevier-letter-marble-springs-1808', kind='message_group', label="Governor Sevier's letter from Marble Springs, May 1808",
      role='report', words=62,
      core=[r'(?:I\s?MPORTANT[!.]?\s+)?Ex\w*\.?\s+of\s+a\s+[Ll]etter\s+from\s+[Gg]ov\w*\.?\s+S\s?EVIER'],
      definition=("Printings of an extract of a letter of Governor Sevier of Tennessee to a friend at Staunton, Virginia, dated Marble Springs, "
                  "14 May 1808, first printed in the Staunton Eagle: an express from General Jackson had reported that '440 Creeks and 12 "
                  "whites' had taken a position on the south bank of the Tennessee near the mouth of Duck river and had killed about twenty "
                  "persons; 'If this be true we shall have warm work this summer'. The Eagle adds that two companies of West Tennessee militia "
                  "were on duty on the frontier. A report at second hand, which the governor passes on with a condition."),
      first="Staunton, 27 May 1808: a letter of Governor Sevier passes on a report from General Jackson that 440 Creeks and 12 whites have taken a position near the mouth of Duck river.",
      what="Governor Sevier's letter",
      printings=[k(ADA, '06-06', 3), (k(VA, '06-07', 2), dict(note=STAUNTON)), k(EN, '06-10', 2), k(BJ, '06-10', 2),
                 (k(PGZ, '06-20', 2), dict(note=STAUNTON)),
                 (k(NHG, '06-21', 3), dict(note="Under the paper's own heading 'The Allies of Britain COMMENCING HOSTILITIES!', credited to the Staunton Eagle.")),
                 (k(NI, '09-21', 2), dict(note='Printed in September, more than three months after the other papers.')),
                 (k(PGZ, '10-10', 3), dict(core=[r'A\s+L\s?ETTER\s+from\s+Gov\w*\.?\s+S\s?EVIER'], role='condensed_report', words=40, dateline=False,
                                          note="A one-sentence summary under 'Domestic Intelligence'; this paper printed the letter itself on 20 June."))]),
 dict(id='burlington-revenue-cutter-1808', kind='message_group', label="'Melancholy Event': Burlington, Vermont, August 1808",
      role='report', words=60,
      core=[r'(?:M\s?ELANCHOLY\s+E\s?VENT\.?\s*[—-]*\s*)?We\s+have\s+to\s+record\s+a\s+(?:very\s+)?melancholy\s+event'],
      definition=("Printings of a Burlington (Vermont) paragraph of 5 August 1808, headed 'Melancholy Event': a revenue cutter with a lieutenant, "
                  "a sergeant and twelve privates, sent by the collector of the customs after a large boat 'well known to have been some time "
                  "employed in smuggling', took her on Onion river; men on the bank then fired on the cutter's crew, and two of the crew and a "
                  "man of the town were killed. The report says that eight persons were taken and put in gaol, that a jury of inquest found "
                  "'wilful murder', and that 'all opinion' should be suspended until the facts were known. A local report."),
      first="Burlington, Vermont, 5 August 1808: a revenue cutter's crew, sent after a smuggling boat, is fired on from the shore of Onion river.",
      what='the Burlington report',
      printings=[k(PGZ, '08-15', 2), k(NHG, '08-16', 2), k(NG, '08-17', 3), k(ADG, '08-18', 3), k(NI, '08-19', 2), k(VA, '08-23', 2), k(EN, '08-26', 1)]),
 dict(id='wilkinson-harper-correspondence-1808', kind='message_group', label="General Wilkinson's challenge to Robert Goodloe Harper, October 1808",
      role='report', words=60,
      core=[r'(?:No\.?\s+I\.?\s+)?G\s?(?:ENERAL|EN\.?)\s+J\s?(?:AMES|AS\.?)\s+W\s?ILKINSON,?\s+the\s+[Cc]ommander\s+in\s+[Cc]hief'],
      definition=("Printings of notes exchanged at Baltimore on 26 and 27 October 1808, as published there: General James Wilkinson's note to "
                  "Captain Robert Goodloe Harper, commanding a company of volunteer artillery, charging that Harper had 'secretly assailed the "
                  "General's honour' and demanding 'the only admissible atonement'; Harper's refusal, which says that his advice to Mr. Clark to "
                  "lay before Congress documents on Wilkinson's 'connection with the Spanish government' gave no ground for a challenge; and "
                  "Wilkinson's reply. Each man's own words. The papers print them under their own introductions or headings, such as "
                  "'MODERN CHIVALRY' and '\"HECTOR\" AGAIN.'"),
      first="Baltimore, 26 October 1808: General Wilkinson's note to Captain Robert Goodloe Harper demands satisfaction; Harper refuses to meet him.",
      what='the Wilkinson-Harper notes',
      printings=[(k(NG, '10-31', 3), dict(note="Credited to the Baltimore North American: 'We are authorized to publish the following correspondence'.")),
                 (k(ADG, '11-01', 3), dict(note="Under an introduction from the Federal Gazette.")),
                 k(EN, '11-01', 2), k(NI, '11-04', 3),
                 (k(VA, '11-04', 2), dict(note="Under the paper's own heading 'MODERN CHIVALRY'.")),
                 (k(PGZ, '11-07', 2), dict(note="Under the paper's own heading '\"HECTOR\" AGAIN.'")),
                 (k(BJ, '11-11', 2), dict(note="Under an introduction from the Federal Gazette."))]),
]


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def build_rows(pages):
    R1.STORIES = STORIES      # round one's functions read the story list, release and dateline from their module
    R1.RELEASE = LOOKUP
    R1.DATELINE = DATELINE
    rows, problems = R1.build_rows(pages)
    for n, r in enumerate(rows, FIRST_ID):
        r['id'] = f'S08-{n:03}'
    return rows, problems


def build(rows, review):
    R1.STORIES = STORIES
    out = R1.build(rows, review)
    base, target = releases()
    out.update({
        'ledger_id': 'ledger:stories-1808-round2', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED,
        'method': ("Round two of 1808, under the rule 'every story alike' (11 November 2026): the items that round one held back for framing, "
                   "counted item by item at the year's rule of 7 newspapers with phrase searches on all 4,466 pages filed under 1808 in both "
                   "transcriptions, reading of every hit, loose keyword searches of the papers in print without a hit, and scan checks of each "
                   "admitted passage"),
        'supporting_files': {'work/story_phrase_search.py': 'retrieval_code', 'outputs/story_discovery_1808/items.json': 'retrieval_candidates',
                             'outputs/story_discovery_1808/phrase_patterns_round2.json': 'retrieval_patterns',
                             'outputs/story_discovery_1808/phrase_hits_round2.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1808.py': 'ledger_code',
                             'work/archive_data/ledgers/make_stories_1808_round2.py': 'ledger_code',
                             'work/archive_data/ledgers/stories_1808_round2_review.json': 'scan_review',
                             'outputs/story_discovery_1808/SCAN_PROTOCOL.md': 'review_protocol',
                             'outputs/story_discovery_1808/scan_points_round2.json': 'review_protocol'},
    })
    for g in out['new_groups']:
        g['admission_rule'] = 'Reviewed 1808 printings, checked against the scan (round two: stories once held back for framing, at the year\'s 7-paper rule).'
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
