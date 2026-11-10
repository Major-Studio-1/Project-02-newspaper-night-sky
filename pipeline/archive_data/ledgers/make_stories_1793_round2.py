"""Write ledgers/stories_1793_round2.json: round two of the reviewed stories of 1793, at a 6-paper threshold.

Round one (make_stories_1793.py, release v0.10.0) admitted the stories with an item printed in 7 or more newspapers and
proposed a 6-paper threshold for 1793, because the year has only 6 to 8 papers in print at a time
(outputs/story_discovery_1793/README.md). The owner agreed on 2026-11-10. Round two admits the candidates that README
listed for 6 papers, counted item by item with the renamed titles of one paper counted once, under the same rules:
items that need framing stay out (the treaty commissioners' report, the German Creek letter, the Saint-Domingue
reports), and so do the candidates the README did not recommend (the Rome and Paris digest paragraphs and Captain
Hacket's rumour in two wordings). Dumouriez's address, in 6 papers, is already a sub-story of round one.

Each candidate's printings were found with phrase searches over all 1,751 pages of 1793 in both transcriptions
(phrase_patterns_round2.json, phrase_hits_round2.json), and every hit was read. Excerpts are cut as in round one, with
its functions; scan findings, crops and hand-drawn boxes are merged from stories_1793_round2_review.json after the scan
check. Observation ids continue round one's: S93-075 onwards, in the same namespace.

Run from the project root with Python 3.12 (needs outputs/story_discovery_1793/search_pages.json):
    python work/archive_data/ledgers/make_stories_1793_round2.py [--table]
"""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_stories_1793 as R1
from make_stories_1793 import NGZ, GUS, KG, PG, MIR, NHG, AHL, CI, EAG, k, REVX, CA

PROJECT = R1.PROJECT
REVIEW = HERE/'stories_1793_round2_review.json'
OUT = HERE/'stories_1793_round2.json'
BASE, TARGET = '0.10.0', '0.10.1'
FIRST_ID = 75   # round one used S93-001 to S93-074

STORIES = [
 dict(id='powers-at-war-with-france-list', kind='message_group', label='The kings, princes and states at war with France', role='report', words=55,
      core=[r'(?:A\s?N\s+)?[Aa]ccount\s+of\s+the\s+[Kk]ings,?\s+[Pp]rinces,?\s+and\s+[Ss]tates,?\s+engaged\s+against',
            r'The\s+following\s+is\s+a\s+[Ll]ist\s+of\s+the\s+[Cc]ombination\s+of\s+[Kk]ings'],
      definition=("Printings of a list from a London paper of early April 1793 of the powers combined against France, from the King of Great "
                  "Britain and the Empress of Russia to the princes of the Empire. Three papers print it as 'An account of the Kings, Princes, and "
                  "States engaged against the Republic of France', three as 'a list of the combination of Kings, Princes, and States, at war with "
                  "France', a combination 'without example in the annals of mankind'; the list is counted as one item. A report."),
      first="A London list of April 1793 names the kings, princes and states at war with France.", what='the list of the powers at war with France',
      printings=[k(GUS, '05-08', 2), k(NGZ, '05-11', 3), k(NHG, '05-14', 1), k(AHL, '05-14', 2), k(MIR, '05-27', 1),
                 (k(PG, '05-27', 3), dict(back=True, words=70, note="Introduced in the paper's own words: 'we think it may not be unpleasing to our readers, if we lay before them an account of the Kings, Princes, and States, engaged against the Republic of France'."))]),
 dict(id='tournai-bulletin-3-may', kind='message_group', label='The London Gazette from Tournai, 3 May: the French attacks repulsed', role='report', words=55,
      core=[r'O\s?[Nn]\s+the\s+1st\s+inst\w*\.?,?\s+the\s+French\s+attacked\s+the\s+advanced\s+posts'],
      definition=("Printings of a bulletin from the London Gazette, dated Tournai, 3 May 1793: on the 1st the French attacked the advanced posts "
                  "of the left wing and of the centre of the combined army and were repulsed, with the loss of men and cannon. The British "
                  "government's own account. Four papers print it after another Tournai paragraph on the preparations against Condé."),
      first="London Gazette, Tournai, 3 May 1793: the French attacks on the advanced posts of the combined army are repulsed.", what='the Tournai bulletin',
      printings=[k(NGZ, '06-29', 2), k(GUS, '06-29', 1), k(NHG, '07-09', 3), k(AHL, '07-09', 2), k(MIR, '07-15', 2), k(PG, '07-22', 2),
                 (k(PG, '08-05', 1), dict(note='Printed again two weeks after its first printing in this paper.'))]),
 dict(id='treasury-circular-rules-on-neutrality', kind='document_group', label="Hamilton's circular to the collectors, with the President's rules on neutrality", role='published_document', words=60,
      core=[r'The\s+following\s+(?:[Ll]etters?|[Pp]apers)\s+ha(?:s|ve)\s+been\s+transmitted\s+by\s+the\s+Secretary\s+of\s+the\s+Treasury',
            r'C\s?IRCULAR\s+(?:to|of)\s+the\s+C\s?OLLECTORS\s+of\s+the\s+C\s?USTOMS'],
      definition=("Printings of the circular of the Secretary of the Treasury to the collectors of the customs (Philadelphia, 4 August 1793): as "
                  "repeated contraventions of neutrality had taken place in American ports, the collectors were to watch for vessels arming or "
                  "equipping for the powers at war, with the schedule of 'Rules adopted by the President' on arming, equipping and prizes. The "
                  "circular and its rules are one publication. An official document."),
      first="Hamilton's circular of 4 August 1793 tells the collectors to watch the ports for breaches of neutrality, with the President's rules.", what="Hamilton's circular and the rules",
      printings=[k(NGZ, '08-17', 1), k(GUS, '08-17', 2), (k(NHG, '08-27', 1), dict(note='The rules continue on page 2.')), k(AHL, '08-27', 3), k(MIR, '09-02', 2),
                 (k(EAG, '09-09', 1), dict(note='The rules follow on page 2.'))]),
 dict(id='convention-president-declaration-plot', kind='document_group', label="The President of the National Convention's declaration of a plot", role='published_document', words=55,
      core=[r'D\s?ECLARATION\.?\s+[Mm]ade\s+by\s+the\s+P\s?RESIDENT\s+of\s+the\s+N\s?ATIONAL\s+C\s?ONVENTION'],
      definition=("Printings of the 'Declaration made by the President of the National Convention to the French Nation' (Paris, May 1793): after "
                  "a scandalous scene in the galleries, he declared his conviction of a conspiracy, revealed to him by good citizens, to destroy "
                  "the Convention, and his resolve to wait the event at his post. One man's declaration of an alleged plot."),
      first="Paris, May 1793: the President of the National Convention declares to the nation that a plot against the Convention exists.", what="the President's declaration",
      printings=[k(GUS, '08-03', 2), k(MIR, '08-19', 3), k(PG, '08-19', 2), (k(NHG, '08-20', 1), dict(note='Continues on page 2.')), k(AHL, '08-20', 2), k(CI, '08-21', 2)]),
 dict(id='cadiz-letter-24-june', kind='message_group', label="A letter from Cadiz, 24 June: 'a hot war with the Spaniards and French'", role='report', words=55,
      core=[r'Ex\w*\.?\s+of\s+a\s+[Ll]etter\s+from\s+a\s+[Gg]entleman\s+(?:in|at)\s+Cadiz'],
      definition=("Printings of an extract of a letter from a gentleman at Cadiz to his brother in New York, dated 24 June 1793 (New York, 12 August): "
                  "'a hot war with the Spaniards and French', a battle near Malaga reported won by the French, and news of the fleets. One "
                  "writer's account, partly hearsay ('We had accounts')."),
      first="A letter from Cadiz (24 June 1793) reports 'a hot war with the Spaniards and French' and a French victory near Malaga.", what='the Cadiz letter',
      printings=[k(GUS, '08-14', 3), k(NGZ, '08-17', 3), k(NHG, '08-20', 3), k(AHL, '08-20', 2), k(MIR, '08-26', 3), k(PG, '08-26', 2)]),
 dict(id='death-of-general-dampierre', kind='message_group', label="The commissioners' letter on General Dampierre's death", role='report', words=55,
      core=[r'(?:(?:Another\s+l|L)etter\s+from\s+the\s+(?:same\s+)?[Cc]ommissioners?(?:\s+with\s+the\s+army\s+in\s+the\s+North)?[.,]?\s+(?:dated\s+)?)?'
            r'Valenciennes,?\s+May\s+9\.?\s*["“]?\s*General\s+D\w+,?\s+who\s+had\s+his\s+thigh'],
      definition=("Printings of a letter from the commissioners of the National Convention with the army of the North, Valenciennes, 9 May 1793, "
                  "read in the Convention: General Dampierre, whose thigh was carried away by a ball the day before, died that morning, regretted "
                  "by the whole army. The French government's commissioners' own account."),
      first="Valenciennes, 9 May 1793: the Convention's commissioners report that General Dampierre died of his wound that morning.", what="the commissioners' letter",
      printings=[k(NHG, '07-16', 2), k(MIR, '07-22', 2), k(GUS, '07-27', 2), k(AHL, '07-30', 2), k(PG, '08-05', 2), k(KG, '09-14', 2)]),
]


def build_rows(pages):
    R1.STORIES = STORIES     # round one's functions read the story list from their module
    rows, problems = R1.build_rows(pages)
    for n, r in enumerate(rows, FIRST_ID):
        r['id'] = f'S93-{n:03}'
    return rows, problems


def build(rows, review):
    R1.STORIES = STORIES
    out = R1.build(rows, review)
    out.update({
        'ledger_id': 'ledger:stories-1793-round2', 'ledger_version': 1, 'base_release': BASE, 'target_release': TARGET,
        'method': ("Round two of 1793, at the 6-paper threshold the owner agreed for this year: the candidates in 6 papers that round one listed, "
                   "read again with phrase searches on all 1,751 pages in both transcriptions, reading of every hit, and scan checks of each "
                   "admitted passage"),
        'supporting_files': {'work/story_phrase_search.py': 'retrieval_code', 'outputs/story_discovery_1793/items.json': 'retrieval_candidates',
                             'outputs/story_discovery_1793/phrase_patterns_round2.json': 'retrieval_patterns',
                             'outputs/story_discovery_1793/phrase_hits_round2.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1793.py': 'ledger_code',
                             'work/archive_data/ledgers/make_stories_1793_round2.py': 'ledger_code',
                             'work/archive_data/ledgers/stories_1793_round2_review.json': 'scan_review',
                             'outputs/story_discovery_1793/SCAN_PROTOCOL.md': 'review_protocol',
                             'outputs/story_discovery_1793/scan_points_round2.json': 'review_protocol'},
    })
    for g in out['new_groups']:
        g['admission_rule'] = 'Reviewed 1793 printings, checked against the scan (round two, 6-paper threshold for 1793).'
    return out


if __name__ == '__main__':
    pages = {p['key']: p for p in json.loads(R1.PAGES.read_text(encoding='utf8'))}
    rows, problems = build_rows(pages)
    for p in problems:
        print('PROBLEM', *p)
    if '--table' in sys.argv:
        for r in rows:
            print(f"{r['id']} {r['story'][:26]:26} {r['page_key']:30} {r['field'][:4]} {r['roles'][0][:9]:9} | {r['excerpt'][:110]} … {r['excerpt'][-50:]}")
    review = json.loads(REVIEW.read_text(encoding='utf8')) if REVIEW.exists() else {}
    if problems and '--force' not in sys.argv:
        raise SystemExit(f'{len(problems)} printings without anchors')
    OUT.write_text(json.dumps(build(rows, review), ensure_ascii=False, indent=2), encoding='utf8')
    print('wrote', OUT, len(rows), 'observations,', len(STORIES), 'groups')
