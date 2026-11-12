"""Write ledgers/stories_1776_round3.json: round three of the reviewed stories of 1776, the stories once held back for framing.

Rounds one and two (make_stories_1776.py, make_stories_1776_round2.py) left the reports of Cherokee and Creek plans for a
later round, because they were thought to need careful framing first (outputs/story_discovery_1776/README.md). On
11 November 2026 the owner set the rule "every story alike": a reviewed story is described by what kind of text it is and
whose account, in the papers' own words, with no special treatment. This round reads those two candidates again and
admits each item that reaches the year's rule (7 or more newspapers, counted item by item), exactly as rounds one and two
did. Both reach 8 papers:
  - the letter to the frontier inhabitants signed by Henry Stuart, British deputy superintendent of Indian affairs
    (June to September 1776, printed first from Virginia and again among papers sent from Augusta, Georgia), and
  - the extract of a letter from Savannah River of 13 May 1776 on the Creek chiefs and the Cherokee towns (July 1776).

Each item's printings were found with phrase searches over all 2,319 pages of 1776 in both transcriptions
(phrase_patterns_round3.json, phrase_hits_round3.json); every hit was read, and the papers in print in the items' weeks
without a hit were searched with loose keywords (no missed printing). Excerpts are cut with round two's functions; scan
findings, crops and hand-drawn boxes are merged from stories_1776_round3_review.json after the scan check. Observation ids
continue round two's: S76-334 onwards, in the same namespace.

The base and target releases are set when the ledger is applied (the 1806 review owns the next release number):
    python work/archive_data/ledgers/make_stories_1776_round3.py [--table] [--base 0.11.0 --target 0.11.1]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1776/search_pages.json).
"""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_stories_1776_round2 as R1
from make_stories_1776_round2 import PEP, VGB, PP, PG, PL, PJ, FJ, NYP, NEC, NYG, VGA, k

PROJECT = R1.PROJECT
REVIEW = HERE/'stories_1776_round3_review.json'
OUT = HERE/'stories_1776_round3.json'
LOOKUP = PROJECT/'outputs/data_foundation/v0.10.2'   # matched families as corrected in v0.8.1 and v0.10.2
BASE, TARGET = '0.11.0', '0.11.1'                       # defaults; see the docstring
FIRST_ID = 334   # round two used S76-247 to S76-333
RECORDED = '2026-11-12'

STUART = (r'(?:["“]\s*)?Gentlemen,?\s*["“]?\s*Some\s*time\s+ago\s+M\s?r\.?\s+Cameron\s+and\s+myself')
SECOND_SETTING = ("Printed again among papers sent from Augusta, Georgia, to the Governor of Georgia (a covering letter of 3 July 1776 with "
                  "two sworn depositions), where it is called 'a copy of an intercepted letter from Henry Stuart, to the frontier "
                  "inhabitants of North-Carolina and Virginia'.")

STORIES = [
 dict(id='stuart-letter-to-frontier-inhabitants', kind='message_group', label="Henry Stuart's letter to the frontier inhabitants, May 1776",
      role='report', words=55,
      core=[r'Copy\s+of\s+a\s+[Ll]etter\s+addressed\s+to\s+the\s+[Ff]rontier\s+[Ii]nhabitants', STUART],
      definition=("Printings of a letter to the settlers on the Watauga and Nolachucky rivers, signed 'Henry Stuart, Deputy Superintendent', "
                  "for the British superintendent of Indian affairs in the southern district, with a sworn statement that a stranger delivered "
                  "it on 18 May 1776. The letter invites those 'willing to join his Majesty's forces, as soon as they arrive at the Cherokee "
                  "nation' to sign a paper of allegiance, and says that the King will land an army in West Florida and march it through the "
                  "Creek nation to the Chickasaws, 'where 500 warriors from each nation are to join them', and on by the Cherokees, 'who have "
                  "also promised their assistance'. The papers printed it in June and July as a letter delivered to the frontier inhabitants, "
                  "and from late August among papers sent from Augusta, Georgia, as 'an intercepted letter'. One side's letter, as printed."),
      first="A letter signed by Henry Stuart, British deputy superintendent of Indian affairs, delivered on 18 May 1776, invites the frontier settlers to join the King's forces when they reach the Cherokee nation.",
      what="Henry Stuart's letter",
      printings=[k(VGB, '06-07', 3),
                 (k(NYP, '06-20', 4), dict(note="The letter runs to the foot of page 4 and is continued in the next issue (27 June, page 3).")),
                 k(PL, '06-29', 2), k(PP, '07-01', 6), k(NYG, '07-01', 1), k(FJ, '07-13', 2),
                 (k(PEP, '08-31', 3), dict(core=[STUART], dateline=False, note=SECOND_SETTING + ' The papers begin on page 2.')),
                 (k(PG, '09-04', 3), dict(core=[STUART], dateline=False, note=SECOND_SETTING)),
                 (k(PL, '09-07', 2), dict(core=[STUART], dateline=False, note=SECOND_SETTING + ' This paper printed the letter for the second time.')),
                 (k(NYG, '09-09', 2), dict(core=[STUART], dateline=False, note=SECOND_SETTING + ' The papers begin on page 1. This paper printed the letter for the second time.'))]),
 dict(id='savannah-river-letter-13-may-1776', kind='message_group', label="A letter from Savannah River, 13 May 1776: the Creek chiefs and the Cherokee towns",
      role='report', words=72,
      core=[r'Ex\w*\.?\s+of\s+a\s+[Ll]etter\s+from\s+S\s?AVANN?AH?\s+[Rr]iver'],
      definition=("Printings of an extract of a letter from Savannah River dated 13 May 1776, printed from Charleston (31 May): the writer reports "
                  "that the Creek chiefs who were expected 'are down, and seem well disposed', and that letters from the Cherokees say the "
                  "middle and lower towns will have no hand in it 'if the Over-hills are for mischief with the white people'; Henry Stewart and "
                  "Captains Colbert and Gist (printed with the long s, 'Giſt', which the transcriptions read as 'Gift') are in the Over-hills "
                  "with ammunition brought up the Mississippi, and were attacked on the way by 'the northward Indians'. One writer's report."),
      first="A letter from Savannah River (13 May 1776) reports that the Creek chiefs who were expected have come down and seem well disposed, and what letters from the Cherokee towns say.",
      what='the Savannah River letter',
      printings=[k(NYP, '07-04', 4), k(VGA, '07-13', 1), k(PG, '07-17', 2), k(PJ, '07-17', 2), k(PL, '07-20', 2), k(PP, '07-22', 4),
                 k(NEC, '07-25', 3), k(FJ, '07-27', 2)]),
]


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def build_rows(pages):
    R1.STORIES = STORIES      # round two's functions read the story list and the release from their module
    R1.RELEASE = LOOKUP
    rows, problems = R1.build_rows(pages)
    for n, r in enumerate(rows, FIRST_ID):
        r['id'] = f'S76-{n:03}'
    return rows, problems


def build(rows, review):
    R1.STORIES = STORIES
    out = R1.build(rows, review)
    base, target = releases()
    out.update({
        'ledger_id': 'ledger:stories-1776-round3', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED,
        'method': ("Round three of 1776, under the rule 'every story alike' (11 November 2026): the reports of Cherokee and Creek plans that "
                   "rounds one and two held back for framing, counted item by item at the year's rule of 7 newspapers with phrase searches on "
                   "all 2,319 pages in both transcriptions, reading of every hit, loose keyword searches of the papers in print without a hit, "
                   "and scan checks of each admitted passage"),
        'supporting_files': {'work/story_phrase_search.py': 'retrieval_code', 'outputs/story_discovery_1776/items.json': 'retrieval_candidates',
                             'outputs/story_discovery_1776/phrase_patterns_round3.json': 'retrieval_patterns',
                             'outputs/story_discovery_1776/phrase_hits_round3.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1776_round2.py': 'ledger_code',
                             'work/archive_data/ledgers/make_stories_1776_round3.py': 'ledger_code',
                             'work/archive_data/ledgers/stories_1776_round3_review.json': 'scan_review',
                             'outputs/story_discovery_1776/SCAN_PROTOCOL.md': 'review_protocol',
                             'outputs/story_discovery_1776/scan_points_round3.json': 'review_protocol'},
    })
    for g in out['new_groups']:
        g['admission_rule'] = 'Reviewed 1776 printings, checked against the scan (round three: stories once held back for framing, at the year\'s 7-paper rule).'
    return out


if __name__ == '__main__':
    pages = {p['key']: p for p in json.loads(R1.PAGES.read_text(encoding='utf8'))}
    rows, problems = build_rows(pages)
    for p in problems:
        print('PROBLEM', *p)
    if '--table' in sys.argv:
        for r in rows:
            print(f"{r['id']} {r['story'][:26]:26} {r['page_key']:30} {r['field'][:4]} {r['roles'][0][:9]:9} | {r['excerpt']}")
    review = json.loads(REVIEW.read_text(encoding='utf8')) if REVIEW.exists() else {}
    if problems and '--force' not in sys.argv:
        raise SystemExit(f'{len(problems)} printings without anchors')
    OUT.write_text(json.dumps(build(rows, review), ensure_ascii=False, indent=2), encoding='utf8')
    print('wrote', OUT, len(rows), 'observations,', len(STORIES), 'groups')
