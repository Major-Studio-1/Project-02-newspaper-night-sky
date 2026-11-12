"""Write ledgers/stories_1807_round2.json: round two of the reviewed stories of 1807, the stories once held back for framing.

Round one (make_stories_1807.py) left out five widely printed items "for framing" and listed them for the owner to decide
(outputs/story_discovery_1807/README.md): the act to prohibit the importation of slaves, the news from Hayti, Robert
MacDonald's funeral, the National Intelligencer on the seamen demanded by the Leopard, and General Wilkinson's speech in
the court at New Orleans. On 11 November 2026 the owner set the rule "every story alike": a reviewed story is described by
what kind of text it is and whose account, in the papers' own words, with no special treatment. This round reads those
candidates again and admits each item that reaches the year's rule (7 or more newspapers, counted item by item), exactly
as round one did:
  - the Baltimore report of 3 February on the republic of Hayti (9 papers; the Enquirer's printing survives only in the
    older CA transcription);
  - General Wilkinson's speech in the court at New Orleans, as a letter of 18 December 1806 reports it (8 papers);
  - Robert MacDonald's death and funeral at Norfolk, 29 June (7 papers);
  - the National Intelligencer's statement of 29 July on the seamen the Leopard sought (8 papers).
Not admitted, by the rule: the act to prohibit the importation of slaves, whose enacting text is in 5 papers (its title is
also in the list of acts and in debates, which are not the item), and the act continuing the suspension of trade with
parts of St. Domingo (3 to 4 papers by its text). These stories are new top-level stories: the parent stories of round one
(Burr's conspiracy, the Chesapeake affair) list their children in their definitions and stay as released.

Each item's printings were found with phrase searches over all 4,167 pages of 1807 in both transcriptions
(phrase_patterns_round2.json, phrase_hits_round2.json); every hit was read, and the papers in print in the items' weeks
without a hit were searched with loose keywords. Excerpts are cut with round one's functions; scan findings, crops and
hand-drawn boxes are merged from stories_1807_round2_review.json after the scan check. Observation ids continue round
one's: S07-251 onwards, in the same namespace. As in round one, an excerpt ends before the names of people arrested on
suspicion: Wilkinson's speech is excerpted from its first words, after the papers' sentence that names the man held.

The base and target releases are set when the ledger is applied (the 1806 review owns the next release number):
    python work/archive_data/ledgers/make_stories_1807_round2.py [--table] [--base 0.11.2 --target 0.11.3]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1807/search_pages.json).
"""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_stories_1807 as R1
from make_stories_1807 import ADA, NG, NI, EN, VA, NHG, PGZ, BJ, HUS, k

PROJECT = R1.PROJECT
REVIEW = HERE/'stories_1807_round2_review.json'
OUT = HERE/'stories_1807_round2.json'
LOOKUP = PROJECT/'outputs/data_foundation/v0.10.2'   # matched families as corrected in v0.8.1 and v0.10.2
BASE, TARGET = '0.11.2', '0.11.3'                       # defaults; see the docstring
FIRST_ID = 251   # round one used S07-001 to S07-250
RECORDED = '2026-11-12'

STORIES = [
 dict(id='wilkinson-speech-new-orleans-1806', kind='message_group', label="General Wilkinson's speech in the court at New Orleans",
      role='quoted_document', words=55, dateline=False,
      core=[r'Called\s+to\s+account\s+for\s+an?\s+\w+,?\s+(?:in\s+)?which\s+I\s+glory'],
      definition=("Printings of General Wilkinson's address to the court at New Orleans, as a letter from that city of 18 December 1806 reports "
                  "it (Washington, 21 January 1807): appearing on a writ of habeas corpus for a man he had arrested, he said he was 'called to "
                  "account for an act in which I glory', warned that 'the artifices of the confederates' must no longer 'cheat the public "
                  "judgment' and that 'treason stalks abroad', and spoke of 'the friends of Burr and rebellion'. The report adds that he then "
                  "charged two lawyers with being parties to the conspiracy. The general's own words, as the letter gives them."),
      first="A letter from New Orleans (18 December 1806) reports General Wilkinson's address to the court: he is 'called to account for an act in which I glory'.",
      what="General Wilkinson's address",
      printings=[k(NI, '01-21', 3), k(ADA, '01-22', 3), k(VA, '01-27', 2), k(EN, '01-27', 2), k(NG, '01-28', 2), k(HUS, '01-31', 3),
                 k(PGZ, '02-02', 2), k(NHG, '02-10', 2)]),
 dict(id='hayti-news-baltimore-february-1807', kind='message_group', label="News from Hayti by way of St. Thomas, February 1807",
      role='report', words=60,
      core=[r'T\s?O\s+the\s+\w+\s+of\s+a\s+gentleman,?\s+j\w*\s+(?:arrived|ar\w*)\s+from'],   # the NHG's RevX reads 'proprietors' for 'politeness'
      definition=("Printings of a Baltimore paragraph of 3 February 1807: from papers brought by a gentleman from St. Thomas, an account of "
                  "'operations' in 'the republic of Hayti' down to 27 December 1806, 'on which day the new Republican Constitution was adopted'. "
                  "It says that General Christophe came before Port-au-Prince on 5 December with about 10,000 men 'to compel' the assembly to "
                  "make him emperor, fired on General 'Pichon', the commander there, who had come out to meet him, and was driven from the town; "
                  "and that news received at Jacmel on 15 January had him defeated and in flight. Six papers add, after the first sentences, "
                  "the editor's promise to give the constitution 'without further loss of time than is necessary for a correct translation'. "
                  "A report at second hand, from papers and news from the republic's side."),
      first="Baltimore, 3 February 1807: papers from St. Thomas report a republican constitution adopted in Hayti and General Christophe driven from Port-au-Prince.",
      what='the report from Hayti',
      printings=[k(NI, '02-04', 3), k(ADA, '02-04', 3), k(EN, '02-06', 3), k(NG, '02-09', 3), k(VA, '02-10', 3), k(HUS, '02-14', 3),
                 k(PGZ, '02-16', 3), k(NHG, '02-17', 2), (k(BJ, '02-20', 3), dict(note="Credited 'From the Baltimore Federal Gazette.'"))]),
 dict(id='macdonald-funeral-norfolk-1807', kind='message_group', label="Robert MacDonald's funeral at Norfolk, June 1807",
      role='report', words=55,
      core=[r'D\s?IED\W+(?:[Oo]n\s+Saturday\s+last|[Aa]t\s+Norfolk[^.]{0,20}\.?)[,.]?\s+(?:at\s+)?the\s+[Mm]arine\s+[Hh]ospital'],
      definition=("Printings of a Norfolk paragraph of 29 June 1807: Robert MacDonald, 'one of the seamen wounded on board the Chesapeake "
                  "frigate', died at the Marine Hospital, and his funeral the day before was 'attended by nearly four thousand citizens', with a "
                  "procession of boats, minute guns, colours at half mast and a sermon at Christ Church; the paper prints the order of the "
                  "procession. A local report of a public funeral."),
      first="Norfolk, 29 June 1807: Robert MacDonald, a seaman wounded on board the Chesapeake, has died, and nearly four thousand citizens attended his funeral.",
      what="the report of the funeral",
      printings=[k(NG, '06-29', 2), k(ADA, '07-03', 2), k(EN, '07-03', 2), k(NI, '07-08', 3), k(BJ, '07-10', 3), k(PGZ, '07-13', 3), k(NHG, '07-14', 2)]),
 dict(id='national-intelligencer-on-the-seamen-1807', kind='message_group', label="The National Intelligencer on the seamen the Leopard sought",
      role='report', words=55,
      core=[r'M\s?UCH\s+error\s+having\s+appeared'],
      definition=("Printings of a Washington paragraph of 29 July 1807 from the National Intelligencer: 'Much error having appeared in the accounts "
                  "circulated' of what passed between the government and the British minister, Erskine, 'in the case of the seamen, to obtain "
                  "whom the Leopard made the late attack on the Chesapeake', it states that his application for their surrender was refused, "
                  "that naval commanders had orders not to recruit British deserters, and that the government had reason to believe the seamen "
                  "were native citizens of the United States. The National Intelligencer's own account; it adds a note with the seamen's names "
                  "and particulars as Captain Barron reported them."),
      first="Washington, 29 July 1807: the National Intelligencer states what passed between the government and the British minister on the seamen the Leopard sought.",
      what="the National Intelligencer's statement",
      printings=[k(NI, '07-29', 3), k(ADA, '07-31', 2), k(NG, '08-03', 2), k(EN, '08-04', 2), k(VA, '08-05', 2),
                 (k(HUS, '08-08', 2), dict(note="Credited 'From the National Intelligencer.'")), k(PGZ, '08-10', 2), k(NHG, '08-11', 2)]),
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
        r['id'] = f'S07-{n:03}'
    return rows, problems


def build(rows, review):
    R1.STORIES = STORIES
    out = R1.build(rows, review)
    base, target = releases()
    out.update({
        'ledger_id': 'ledger:stories-1807-round2', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED,
        'method': ("Round two of 1807, under the rule 'every story alike' (11 November 2026): the items that round one held back for framing, "
                   "counted item by item at the year's rule of 7 newspapers with phrase searches on all 4,167 pages in both transcriptions, "
                   "reading of every hit, loose keyword searches of the papers in print without a hit, and scan checks of each admitted passage"),
        'supporting_files': {'work/story_phrase_search.py': 'retrieval_code', 'outputs/story_discovery_1807/items.json': 'retrieval_candidates',
                             'outputs/story_discovery_1807/phrase_patterns_round2.json': 'retrieval_patterns',
                             'outputs/story_discovery_1807/phrase_hits_round2.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1807.py': 'ledger_code',
                             'work/archive_data/ledgers/make_stories_1807_round2.py': 'ledger_code',
                             'work/archive_data/ledgers/stories_1807_round2_review.json': 'scan_review',
                             'outputs/story_discovery_1807/SCAN_PROTOCOL.md': 'review_protocol',
                             'outputs/story_discovery_1807/scan_points_round2.json': 'review_protocol'},
    })
    for g in out['new_groups']:
        g['admission_rule'] = 'Reviewed 1807 printings, checked against the scan (round two: stories once held back for framing, at the year\'s 7-paper rule).'
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
