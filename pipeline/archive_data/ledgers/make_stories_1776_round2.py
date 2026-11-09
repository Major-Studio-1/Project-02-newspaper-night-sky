"""Write ledgers/stories_1776_round2.json (v0.7.1 -> v0.7.2): round two of the reviewed stories of 1776.

Round two takes the candidates that round one read but did not admit (outputs/story_discovery_1776/README.md,
"Candidates for a later round"), except the Cherokee and Creek reports, which need framing first. Each was read again
with phrase searches over all 2,319 pages of 1776 in both transcriptions (phrase_patterns_round2.json,
phrase_hits_round2.json), and every hit was read. Where a candidate turned out to be several printed items, each item is
its own group under a parent story, as in round one.

Excerpts are cut as in make_stories_1776.py (the opening of the printed item, about 40-60 words, with its dateline or
heading when one stands directly before it), from text normalized exactly as apply_ledger.py does. Scan findings, crops
and hand-drawn boxes are merged from stories_1776_round2_review.json after the scan check. Observation ids continue
round one's: S76-247 onwards, in the same namespace.

Run from the project root with Python 3.12 (needs outputs/story_discovery_1776/search_pages.json, made by
work/year_search_pages.py):
    python work/archive_data/ledgers/make_stories_1776_round2.py [--table]
"""
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PAGES = PROJECT/'outputs/story_discovery_1776/search_pages.json'
REVIEW = HERE/'stories_1776_round2_review.json'
OUT = HERE/'stories_1776_round2.json'
RELEASE = PROJECT/'outputs/data_foundation/v0.7.1'
REVX, CA = 'RevX_OCR_text', 'ca_ocr_text'
FIRST_ID = 247   # round one used S76-001 to S76-246

PEP, VGB, VGA, PP, PG, PL, PJ = 'sn83025894', 'sn84024742', 'sn84024739', 'sn83021126', 'sn84026371', 'sn83025898', 'sn85047530'
FJ, NYP, NEC, NYG = 'sn83025583', 'sn83030135', 'sn83020482', 'sn83030493'
PAPER = {PEP: 'The Pennsylvania Evening Post', VGB: "Purdie's Virginia Gazette", VGA: "Dixon and Hunter's Virginia Gazette",
         PP: "Dunlap's Pennsylvania Packet", PG: 'The Pennsylvania Gazette', PL: 'The Pennsylvania Ledger', PJ: 'The Pennsylvania Journal',
         FJ: "The Freeman's Journal", NYP: 'The New-York Packet', NEC: 'The New-England Chronicle', NYG: 'The New-York Gazette'}
k = lambda paper, date, page, ed=1: f'{paper}|1776-{date}|{ed}|{page}'
CONGRESS = r'(?:I\s?N\s+)?C\s?O\s?N\s?G\s?R\s?E\s?S\s?S[.,]?\s+'

# Story groups, as in round one. 'printings' lists each printing's page; a tuple adds overrides for that printing:
# core (regexes for the item's first words), role, field, note, dateline (include a dateline or heading directly before).
STORIES = [
 dict(id='wilkes-speech-commons', kind='document_group', label="Wilkes's speech in the Commons", role='published_document', words=88,
      core=[r'(?:T\s?HE\s+)?S\s?PEECH\s+of\s+the\s+L\s?ORD\s+M\s?AYOR'],
      definition="Printings of the speech of John Wilkes, Lord Mayor of London, in the House of Commons on the motion for an address to the King at the opening of the session in October 1775, against the war in America.",
      first="John Wilkes, Lord Mayor of London, speaks in the Commons against the address to the King: every man ought now to speak out.", what="Wilkes's speech",
      printings=[k(PEP, '01-18', 1), k(NYP, '01-18', 1), k(PL, '01-20', 2), k(PP, '01-22', 4), k(PG, '01-24', 1), k(PJ, '01-24', 1), k(VGA, '02-10', 4), k(VGB, '02-16', 5)]),
 dict(id='penn-before-the-lords', kind='context_group', label='Governor Penn before the Lords',
      definition="Reports of the examination of Richard Penn, former governor of Pennsylvania, who had carried Congress's petition to the King, in the House of Lords in November 1775, as the American papers printed them from February 1776: a short London report, and a long account with the questions and answers. Contains those two groups; the wider coverage is not included.",
      children=['penn-examined-report', 'penn-examination-lords']),
 dict(id='penn-examined-report', parent='penn-before-the-lords', kind='message_group', label='A London report: Penn examined', role='report', words=50,
      core=[r'On\s+Friday,?\s+in\s+the\s+[Uu]pper\s+[Aa]ssembly'],
      definition="Printings of a London paragraph of November 1775: on Friday Governor Penn was examined in the Upper Assembly and 'gave very satisfactory answers', and a member then proposed Congress's last petition to the King as the basis of an accommodation.",
      first="A London report: Governor Penn was examined in the House of Lords and gave very satisfactory answers.", what='the report',
      printings=[k(PEP, '02-01', 1), k(PL, '02-03', 2), k(PP, '02-05', 6), k(NYG, '02-05', 3), k(PG, '02-07', 2), k(NYP, '02-08', 2), k(VGB, '02-16', 2)]),
 dict(id='penn-examination-lords', parent='penn-before-the-lords', kind='message_group', label="The Lords examine Governor Penn", role='report', words=55,
      core=[r'(?:BRITISH\s+)?H\s?OUSE\s+(?:of\s+)?L\s?ORDS[,.]?\s+S\s?ATURDAY'],
      definition="Printings of a London account of the House of Lords on 10 November 1775: the examination of Richard Penn, with the questions put to him and his answers, and the Duke of Richmond's motion grounded on them.",
      first="A London account of the House of Lords: the Lords assemble to examine Governor Penn on the Duke of Richmond's motion.", what='the account',
      printings=[k(PEP, '02-20', 1), k(PG, '02-21', 2), k(PJ, '02-21', 2), k(PL, '02-24', 1), k(PP, '02-26', 4), k(NYP, '02-29', 2), k(VGB, '03-15', 1), k(VGA, '03-16', 1)]),
 dict(id='prohibitory-bill-commons', kind='context_group', label='The Prohibitory bill in the Commons',
      definition="Reports from London of the bill to prohibit all trade and intercourse with the colonies (the Prohibitory Act) in the House of Commons in December 1775, as printed in February and March 1776: the debate in committee, which printed the clause on captures with blanks for its dates, and the clause as settled. Contains those two groups; the wider coverage is not included.",
      children=['prohibitory-bill-committee', 'prohibitory-clause-settled']),
 dict(id='prohibitory-bill-committee', parent='prohibitory-bill-commons', kind='message_group', label='The Commons in committee on the bill', role='report', words=55,
      core=[r'When\s+the\s+order\s+of\s+the\s+day\s+was\s+read\s+yesterday'],
      definition="Printings of a London report (6 December 1775) of the House of Commons in committee on the bill to prohibit all trade and intercourse with the colonies: the divisions, Lord North's remark on the clause that gives American ships time, and that clause printed with blanks for its dates, 'that the friends of America may have an opportunity' to have them filled with distant ones.",
      first="A London report: the Commons go into committee on the bill to prohibit all trade with the colonies, and the clause on captures is printed with its dates left blank.", what='the report',
      printings=[k(PJ, '02-21', 2), k(PL, '02-24', 2), k(PP, '02-26', 2), k(NYP, '02-29', 2), k(VGB, '03-08', 2), k(VGA, '03-09', 2)]),
 dict(id='prohibitory-clause-settled', parent='prohibitory-bill-commons', kind='message_group', label='The clause on captures settled', role='report', words=60,
      core=[r'The\s+clause\s+in\s+the\s+American\s+restraining\s+bill'],
      definition="Printings of a London report (8 December 1775) that the clause of the bill which caused the greatest debate was settled: American ships to be captured from 1 January 1776, and all ships trading with the colonies from 1 June 1776.",
      first="A London report: the clause on captures is settled, with American ships liable from 1 January 1776.", what='the report',
      printings=[k(PEP, '02-27', 3), k(PG, '02-28', 2), k(PJ, '02-28', 2), k(PL, '03-02', 1), k(PP, '03-04', 4)]),
 dict(id='congress-bills-of-credit', kind='document_group', label='Congress on refusing Continental bills', role='published_document', words=85,
      core=[CONGRESS+r'Jan\w*\.?,?\s+11', r'W\s?HEREAS\s+it\s+appears\s+to\s+this\s+Congress,?\s+that\s+several'],
      definition="Printings of Congress's resolution of 11 January 1776 that anyone who refused the Continental bills of credit, or discouraged their circulation, should be treated as an enemy of his country.",
      first="Congress's resolution of 11 January 1776: whoever refuses the Continental bills of credit is to be treated as an enemy of his country.", what='the resolution',
      printings=[k(PEP, '01-13', 1), k(PP, '01-15', 3), k(PG, '01-17', 3), k(PJ, '01-17', 2), k(NYP, '01-18', 3), k(NYG, '01-22', 1), k(VGB, '02-02', 2)]),
 dict(id='congress-fast-day-1776', kind='document_group', label="Congress's fast day of 17 May", role='published_document', words=55,
      core=[CONGRESS+r'S\s?ATURDAY,?\s+M\s?ARCH\s+16', r'I\s?N\s+times\s+of\s+impending\s+calamity'],
      definition="Printings of Congress's resolution of 16 March 1776 recommending that Friday 17 May be kept throughout the colonies as a day of humiliation, fasting and prayer. Includes a one-sentence notice of it and a New York committee's notice that quotes it.",
      first="Congress's resolution of 16 March 1776: Friday 17 May to be kept as a day of humiliation, fasting and prayer.", what='the resolution',
      printings=[k(PP, '03-18', 3), k(PEP, '03-19', 1), k(PG, '03-20', 3), k(PJ, '03-20', 1), k(NYP, '03-21', 3),
                 (k(VGB, '03-29', 2), dict(core=[r'Friday\s+the\s+17th\s+of\s+May\s+is\s+appointed'], role='condensed_report', words=30,
                                          note='A one-sentence notice of the fast, before an address to the readers; the same paper printed the resolution a week later.')),
                 k(VGB, '04-05', 1), k(VGA, '05-11', 2),
                 (k(PJ, '05-15', 1), dict(note='Printed again two days before the fast, eight weeks after its first printing in this paper.')),
                 (k(NYP, '05-16', 3), dict(core=[r'W\s?HEREAS\s+the\s+Hono?u?rable\s+Continental\s+Congress\s+have\s+appointed'], role='quoted_document',
                                          note="Quoted in the New York committee's notice of 16 May on keeping the fast the next day."))]),
 dict(id='barry-takes-edward', kind='message_group', label='Barry takes the Edward', role='report', words=55,
      core=[r'In\s+[sf]ight\s+of\s+the\s+[Cc]apes\s+of\s+V'],
      definition="Printings of Captain John Barry's letter to John Hancock or the Marine Committee ('In sight of the Capes of Virginia, April 7, 1776'): he fell in with the sloop Edward, belonging to the Liverpool frigate, and took her after a fight of near two glasses.",
      first="Captain John Barry writes from off the Capes of Virginia that he has fought and taken the sloop Edward, a tender of the Liverpool frigate.", what="Barry's letter",
      printings=[k(PEP, '04-11', 2), k(PL, '04-13', 3), k(PP, '04-15', 5), k(PG, '04-17', 3), k(NYP, '04-18', 2), k(VGB, '04-26', 6), k(VGA, '04-27', 4)]),
 dict(id='sloop-liberty-gunpowder', kind='message_group', label="The sloop Liberty's gunpowder taken", role='report', words=75,
      core=[r'(?:ON\s+)?Sunday\s+the\s+30th\s+ult'],
      definition="Printings of a Williamsburg report (13 April 1776) that on 30 March the sloop Liberty of Perth Amboy, from St. Eustatius with 83 barrels of gunpowder, dry goods and medicines, was taken by a British tender off the capes and carried into Norfolk, with what her mate, who escaped, said of British troops at Antigua.",
      first="A Williamsburg report: the sloop Liberty, from St. Eustatius with 83 barrels of gunpowder, has been taken by a tender and carried into Norfolk.", what='the report',
      printings=[k(VGA, '04-13', 3), k(PEP, '04-23', 2), k(PG, '04-24', 3), k(PJ, '04-24', 2), k(NYP, '04-25', 3), k(PL, '04-27', 3), k(PP, '04-29', 3),
                 (k(NYP, '05-02', 3), dict(core=[r'The\s+30th\s+of\s+March\s+last,?\s+a\s+sloop'], role='condensed_report', words=45,
                                          note="A shorter, reworded report a week after this paper printed the Williamsburg report; it says 'off the Capes of Delaware'."))]),
 dict(id='howe-declarations-1776', kind='context_group', label="The Howe brothers' declarations",
      definition="The declarations of Lord Howe and General William Howe as the King's commissioners for restoring peace, as the American papers printed them: Lord Howe's declaration of June 1776, published by order of Congress in July, and the brothers' declaration of 19 September. Contains those two groups; their declaration of 14 July (printed in the New-York Gazette) and their proclamation of 30 November (printed in the Freeman's Journal) are not included.",
      children=['howe-declaration-published-by-congress', 'howe-declaration-september']),
 dict(id='howe-declaration-published-by-congress', parent='howe-declarations-1776', kind='document_group', label="Lord Howe's declaration, published by Congress", role='published_document', words=55,
      core=[CONGRESS+r'July\s+19', r'R\s?ESOLVED,?\s+[Tt]hat\s+a\s+copy\s+of\s+the\s+circular\s+letters'],
      definition="Printings of Congress's resolution of 19 July 1776 ordering that Lord Howe's circular letter to the former royal governors (20 June 1776) and the declaration it enclosed be published, 'that the good people of these United States may be informed of what nature are the Commissioners, and what the terms', followed by the letter and the declaration offering pardons.",
      first="Congress orders Lord Howe's circular letter and declaration published, so that the people may see what the commissioners offer.", what='the resolution, letter and declaration',
      printings=[k(PEP, '07-20', 1), k(PL, '07-20', 2), k(PP, '07-22', 3), k(PG, '07-24', 3), k(PJ, '07-24', 1), k(NYG, '07-29', 1), k(VGA, '08-03', 1)]),
 dict(id='howe-declaration-september', parent='howe-declarations-1776', kind='document_group', label='The declaration of 19 September', role='published_document', words=55,
      core=[r'By\s+R\s?ICHARD\s+V\w*\s+H\s?OWE(?:(?!D\s?E\s?C\s?L\s?A\s?R\s?A\s?T\s?I\s?O\s?N).){0,500}D\s?E\s?C\s?L\s?A\s?R\s?A\s?T\s?I\s?O\s?N\.?\s+A\s?LTHOUGH'],
      definition="Printings of the declaration of Lord Howe and General William Howe, the King's commissioners, of 19 September 1776: Congress had disavowed every purpose of reconciliation, the King would revise his instructions and the acts complained of, and the inhabitants were invited to consider whether to trust their fate to Congress.",
      first="Lord Howe and General Howe declare that the King will revise the acts complained of, and invite the inhabitants to look to their own peace.", what='the declaration',
      printings=[k(NYG, '09-30', 1),
                 (k(PG, '10-02', 3), dict(core=[r'The\s+following\s+Declaration\s+of\s+Lord\s+and\s+General\s+Howe'], words=85,
                                          note='Introduced as printed in a handbill at New York.')),
                 (k(PL, '10-05', 1), dict(core=[r'The\s+following\s+Declaration\s+was\s+circulated'], words=95,
                                          note='Introduced as circulated about the city in handbills on the Tuesday before.')),
                 (k(NYG, '10-07', 1), dict(note='Printed again a week after its first printing in this paper.')),
                 k(VGA, '10-11', 3), k(VGB, '10-11', 1),
                 (k(FJ, '10-22', 2), dict(core=[r'The\s+following\s+Declaration\s+of\s+Lord\s+and\s+General\s+Howe'], words=85,
                                          note='Introduced as printed in a handbill at New York.'))]),
 dict(id='gates-carleton-retreat', kind='message_group', label="Gates on Carleton's retreat", role='report', words=55,
      core=[r'Copy\s+of\s+a\s+[Ll]etter\s+to\s+the\s+President,?\s+from\s+(?:Major|Maj\.)'],
      definition="Printings of General Gates's letter to the President of Congress (Ticonderoga, 5 November 1776), published by order of Congress, reporting that General Carleton's fleet and army had withdrawn from Crown Point.",
      first="General Gates writes from Ticonderoga that Carleton's fleet and army have withdrawn from Crown Point.", what="Gates's letter",
      printings=[k(PEP, '11-14', 4), k(PL, '11-16', 3), k(PP, '11-19', 3), k(PG, '11-20', 2), k(VGA, '11-29', 2), k(VGB, '11-29', 1), k(FJ, '12-10', 2)]),
]

MONTHS = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
# A dateline or heading directly before the item, after a sentence boundary (as in round one).
WEEKDAY = r"(?!(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\b)"
PLACE = WEEKDAY + r"(?:(?:[A-Z]{1,2}\s){2,}[A-Z]{1,2}|[A-Z][A-Za-z'\-]+(?:[\s\-][A-Z][A-Za-z'\-]+){0,2})(?:,?\s*\([A-Za-z ,]+\))?"
DATELINE = re.compile(r"(?:^|[.;:!?\]\"”)]\s+)(" + PLACE + r",?\s+" + MONTHS + r"\.?,?\s*\d{1,2}(?:st|d|th|nd|rd)?(?:,?\s*1776)?\.\s*)$")


def item_start(text, cores, dateline=True):
    for core in cores:
        m = re.search(core, text, re.I)
        if m:
            start = m.start()
            if dateline:
                d = DATELINE.search(text[max(0, start-90):start])
                if d:
                    start -= len(d.group(1))
            return start
    return None


def cut_excerpt(text, start, words):
    """Round one's cut, except that the start anchor may run to 45 words (a heading can repeat on the page)."""
    tokens = list(re.finditer(r'\S+', text[start:]))
    n = min(words, len(tokens))
    for j in range(15, n):   # RevX sometimes abridges with an ellipsis; end before it.
        if '...' in tokens[j].group() or '…' in tokens[j].group():
            n = j if tokens[j].group().startswith(('...', '…')) else j+1
            break
    else:
        j = None
    limit = n if j is not None else min(n+15, len(tokens))
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
    for a in pq.read_table(RELEASE/'derived/reuse_family_appearances.parquet', columns=['family_id', 'page_id']).to_pylist():
        if a['family_id'].startswith('R1776-'):
            out.setdefault(a['page_id'].split(':', 1)[1].replace(':', '|'), []).append(a['family_id'])
    return {key: sorted(v) for key, v in out.items()}


def build_rows(pages):
    rows, problems = [], []
    families = page_families()
    seen = {}
    for s, key, over in printings():
        text_fields = pages[key]['texts']
        cores = over.get('core', s['core'])
        fields = [over['field']] if 'field' in over else [REVX, CA]
        for field in fields:
            text = text_fields.get(field) or ''
            start = item_start(text, cores, over.get('dateline', s.get('dateline', True)))
            if start is not None:
                break
        if start is None:
            problems.append((s['id'], key, 'item start not found'))
            continue
        excerpt, first, last = cut_excerpt(text, start, over.get('words', s['words']))
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
        if field == CA and 'field' not in over:
            note = (note+' ' if note else '') + 'RevX lacks the opening of this item, so the excerpt comes from the older CA transcription.'
        rows.append({'story': story, 'page_key': key, 'field': field, 'excerpt_start': first, 'excerpt_end': last, 'excerpt': excerpt,
                     'roles': [over.get('role', s['role'])], 'groups': groups, 'summary': summary, 'note': note,
                     'family': families.get(key, []), 'earliest': earlier == 0})
    rows.sort(key=lambda r: (r['page_key'].split('|')[1], r['page_key'], r['story']))
    for n, r in enumerate(rows, FIRST_ID):
        r['id'] = f'S76-{n:03}'
    return rows, problems


def build(rows, review):
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
               'admission_rule': 'Reviewed 1776 printings, checked against the scan.'} for s in STORIES]
    hierarchy = [{'parent': s['id'], 'child': c} for s in STORIES for c in s.get('children', [])]
    return {
        'ledger_id': 'ledger:stories-1776-round2', 'ledger_version': 1, 'base_release': '0.7.1', 'target_release': '0.7.2',
        'recorded_date': '2026-11-09', 'namespace': 'expansion-1776', 'evidence_dir': 'outputs/story_discovery_1776/evidence',
        'reviewer': 'Claude Code (AI assistant). Not an independent human review.',
        'method': "Round two of 1776: the candidates round one read but did not admit, read again with phrase searches on all 2,319 pages in both transcriptions, reading of every hit, and scan checks of each admitted passage",
        'supporting_files': {'work/story_phrase_search.py': 'retrieval_code', 'outputs/story_discovery_1776/items.json': 'retrieval_candidates',
                             'outputs/story_discovery_1776/phrase_patterns_round2.json': 'retrieval_patterns',
                             'outputs/story_discovery_1776/phrase_hits_round2.json': 'retrieval_candidates',
                             'work/archive_data/ledgers/make_stories_1776_round2.py': 'ledger_code',
                             'work/archive_data/ledgers/stories_1776_round2_review.json': 'scan_review',
                             'outputs/story_discovery_1776/SCAN_PROTOCOL.md': 'review_protocol',
                             'outputs/story_discovery_1776/scan_points_round2.json': 'review_protocol',
                             'outputs/story_discovery_1776/extra_crops_round2.json': 'review_protocol'},
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
            print(f"{r['id']} {r['story'][:26]:26} {r['page_key']:30} {r['field'][:4]} {r['roles'][0][:9]:9} | {r['excerpt'][:110]} … {r['excerpt'][-50:]}")
    review = json.loads(REVIEW.read_text(encoding='utf8')) if REVIEW.exists() else {}
    if problems and '--force' not in sys.argv:
        raise SystemExit(f'{len(problems)} printings without anchors')
    OUT.write_text(json.dumps(build(rows, review), ensure_ascii=False, indent=2), encoding='utf8')
    print('wrote', OUT, len(rows), 'observations,', len(STORIES), 'groups')
