"""Write ledgers/stories_1773_round2.json: reviewed stories of 1773, round two.

1773 was read by the thin-year rule (docs/rules-and-exceptions.md, Y-THIN as amended on 23 November 2026, the owner's choice
B1) in round one (stories_1773.json): an item, counted by its own words, is eligible when it was printed by more than half of
the newspapers that survive for its weeks, and by at least 4; items printed by every newspaper that survives for their weeks
are admitted; the other eligible items are chosen to cover the months and the kinds of news; digests are not admitted. Single
paragraphs from runs of news are counted by their own words (C-09).

The sweep check of 24 and 25 November 2026 (outputs/story_discovery_1779/sweep_check_25nov.md; X-THIN-SWEEP) read every passage
of the year shared word for word by 4 or more papers that no counted opening explains, and found an item printed by every paper
that survives for its weeks, which round one's lists did not name. At the owner's word of 25 November 2026 ("按规则收录":
admit them as the rule reads), it is admitted by the rule's first part (X-1773-08). This ledger adds it as new groups; it adds
nothing to round one's groups (C-15).

Each printing names its page. The excerpt anchors are cut here from the page text, normalized exactly as apply_ledger.py
does: the excerpt is the opening of the printed item (about 25-70 words), starting with its dateline or heading when one
stands directly before it. A paragraph printed in a run of news is counted, and its excerpt cut, by its own opening sentence.
Scan findings, crops and hand-drawn boxes are merged from stories_1773_round2_review.json after the scan check. A printing
on a page whose RevX transcription is filed under another scan page (derived/revx_page_map.parquet), or empty, takes its
excerpt from the CA transcription of its scan page.

Every story alike (the owner's rule of 11 November 2026): each group is described by what kind of text it is and whose
account, in the papers' own words, never as what happened.

The printings are numbered on from round one and the corrections of v0.11.41 (S73-209 onwards). The base and target
releases are set when the ledger is applied; the defaults chain the five round-two ledgers of 25 November (1773, 1775, 1783,
1798, 1799) on top of v0.11.41, one release each:
    python work/archive_data/ledgers/make_stories_1773_round2.py [--table] [--base 0.11.41 --target 0.11.42]
Run from the project root with Python 3.12 (needs outputs/story_discovery_1773/round2/search_pages.json, made by
work/year_search_pages.py 1773 outputs/story_discovery_1773/round2/search_pages.json --printed-dates). Without that file,
an existing ledger only takes the new --base and --target: its excerpts are cut from the 1773 pages of v0.11.41, and the
ledger is otherwise the same.
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
YEAR = '1773'
D = PROJECT/'outputs/story_discovery_1773'
PAGES = D/'round2/search_pages.json'
REVIEW = HERE/'stories_1773_round2_review.json'
OUT = HERE/'stories_1773_round2.json'
BASE, TARGET = '0.11.41', '0.11.42'   # defaults; see the docstring
DATA_RELEASE = '0.11.41'   # the release whose pages, families and misfiled-page map were read
RELEASE = PROJECT/f'outputs/data_foundation/v{DATA_RELEASE}'
RECORDED = '2026-11-25'
PREFIX, FIRST = 'S73', 209
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'

PAPER = {'sn83025582': 'The New-Hampshire Gazette', 'sn84024739': 'The Virginia Gazette (Purdie and Dixon)',
         'sn84024741': 'The Virginia Gazette (Rind)', 'sn83021194': 'The Massachusetts Spy'}
# Printings found by the scan check not to be the item: they keep their number but are not observations.
NOT_PRINTINGS = {}


def releases():
    base, target = BASE, TARGET
    if '--base' in sys.argv:
        base = sys.argv[sys.argv.index('--base')+1]
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target')+1]
    return base, target


def misfiled():
    """Page keys whose RevX slot holds another scan page's text, from the data release."""
    sys.path.insert(0, str(PROJECT/'work/python_packages'))
    import pyarrow.parquet as pq
    key = lambda page_id: page_id.split(':', 1)[1].replace(':', '|')
    return {key(r['page_id']): key(r['revx_text_of']) for r in pq.read_table(RELEASE/'derived/revx_page_map.parquet', columns=['page_id', 'revx_text_of']).to_pylist()
            if key(r['page_id']).split('|')[1].startswith(YEAR)}


def S(id, label, definition, core, first, what, printings, role='report', words=40, dateline=True, back=True, **kw):
    """One story group (a message_group), written compactly. The excerpt starts at the beginning of the sentence that holds
    the core (back=True), then takes the dateline standing directly before it."""
    return dict(id=id, kind='message_group', label=label, definition=definition, role=role, words=words, dateline=dateline,
                back=back, core=core, first=first, what=what, printings=printings, **kw)


STORIES = [
 S('london-letter-from-the-lord-camden-a-pirate-brought-in-1773',
   "London, July 1773: a letter from on board the Lord Camden East-Indiaman: 'As we left the Cape of Good Hope, we met two Dutch men of war bringing in a pirate'",
   ("Printings of a paragraph of the London news of July 1773 on a letter from on board the Lord Camden East-Indiaman, lately arrived "
    "from China: 'As we left the Cape of Good Hope, we met two Dutch men of war bringing in a pirate, which proved to be the Aurora "
    "English frigate, with part of her crew, who had murdered the Captain and all the officers, and ran away with the ship.' A London "
    "report of a letter from a ship, as the papers reprinted it; the New-Hampshire Gazette introduces the letter in other words (C-02)."),
   [r'The\W+following\W+piece\W+of\W+intelligence\W+is\W+an\W+extract', r'A\W+letter\W+from\W+on\W+board\W+the\W+Lord\W+Cam'],
   "London, July 1773: a report of a letter from the Lord Camden East-Indiaman on a pirate brought in by two Dutch men of war.",
   "the London report of the letter from the Lord Camden",
   ['sn83021194|1773-09-02|1|2', 'sn83025582|1773-09-03|1|2', 'sn84024739|1773-09-09|1|2', 'sn84024741|1773-09-09|1|2'],
   words=60, back=False, dateline=False),
]

MONTHS = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?'
          r'|JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUNE?|JULY?|AUG(?:UST)?|SEPT?(?:EMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)')
# A dateline directly before the item, after a sentence boundary: "BOSTON, August 12.", a bare date ('Nov. 10.'), a place
# with 'St.' ("ST. JAMES'S, Sept. 1."), a bracketed state or island ('VIENNA, [Germany] May 25.'), as in round one.
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|(?:S[Tt]\.\s*)?[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*[\(\[][A-Za-z ,.\-]+[\)\]])?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)((?:" + PLACE + r"\s*,?\s+)?" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1[78]\d\d)?\.\s*(?:[—-]+\s*)?)$")


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
    """The opening of the item, ended at a clause boundary; the start anchor may run to 45 words.
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
    misfiled_pages = misfiled()
    seen = {}
    for s, key, over in printings():
        if key not in pages:
            problems.append((s['id'], key, f'page not in the {YEAR} pages'))
            continue
        text_fields = pages[key]['texts']
        cores = over.get('core', s['core'])
        if key in misfiled_pages:     # this page's RevX slot holds another scan page's text: read the CA text of the scan page
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
        if key in misfiled_pages:
            note = (note+' ' if note else '') + ('The RevX transcription of this page is filed under another page, so the excerpt '
                                                 'comes from the older CA transcription of this scan page.')
        elif field == CA and 'field' not in over:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'printed': pages[key]['date'], 'field': field, 'excerpt_start': first, 'excerpt_end': last,
                     'excerpt': excerpt, 'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['printed'], r['page_key'], r['story']))
    for n, r in enumerate(rows, FIRST):   # numbered in order of printed date, on from round one
        r['id'] = f'{PREFIX}-{n:03}'
    rows = [r for r in rows if (r['page_key'], r['story']) not in NOT_PRINTINGS]   # keep their number, not a row
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
               'admission_rule': (f'Reviewed {YEAR} printings, checked against the scan (round two: printed by every paper that survives '
                                  'for its weeks, found by the sweep check of 24-25 November 2026 and admitted at the owner\'s word).')}
              for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    d = f'outputs/story_discovery_{YEAR}/'
    return {
        'ledger_id': f'ledger:stories-{YEAR}-round2', 'ledger_version': 1, 'base_release': base, 'target_release': target,
        'recorded_date': RECORDED, 'namespace': f'expansion-{YEAR}', 'evidence_dir': d+'evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': ('A sweep of every page of the year for passages shared word for word by 4 or more papers that no counted opening of '
                   'round one explains; each passage read, looked up in the year\'s lists and counted by its own opening words against '
                   'every page in both transcriptions, by the thin-year rule (Y-THIN as amended on 23 November 2026: items printed by every '
                   'newspaper that survives for their weeks are admitted; single paragraphs from runs of news counted by their own words, '
                   'C-09); the items printed by every surviving paper admitted at the owner\'s word of 25 November 2026; scan checks of '
                   'each admitted passage'),
        'supporting_files': {'work/year_search_pages.py': 'retrieval_code', 'outputs/story_discovery_1779/sweep_check_25nov.md': 'retrieval_candidates',
                             d+f'not_admitted_pending/sweep_{YEAR}.json': 'retrieval_candidates',
                             f'work/archive_data/ledgers/make_stories_{YEAR}_round2.py': 'ledger_code',
                             f'work/archive_data/ledgers/stories_{YEAR}_round2_review.json': 'scan_review',
                             d+'SCAN_PROTOCOL.md': 'review_protocol'},
        'scan_scope': 'Each crop covers the excerpt, the opening of the printed item. Long documents were not proofread in full.',
        'observations': obs, 'new_groups': groups, 'new_hierarchy': hierarchy, 'added_memberships': [], 'new_relations': [],
        'dispositions_summary': review.get('dispositions', {}),
    }


if __name__ == '__main__':
    if not PAGES.exists():
        if OUT.exists() and ('--base' in sys.argv or '--target' in sys.argv):
            ledger = json.loads(OUT.read_text(encoding='utf8'))
            ledger['base_release'], ledger['target_release'] = releases()
            OUT.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf8')
            print('updated', OUT.name, 'to base', ledger['base_release'], 'target', ledger['target_release'], '(pages not on disk; excerpts kept)')
            raise SystemExit(0)
        raise SystemExit(f'{PAGES} is missing: make it with work/year_search_pages.py {YEAR} {PAGES} --printed-dates')
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
