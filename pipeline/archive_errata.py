"""What reading the papers turned up wrong in the archive itself, gathered for the people who keep it.

The archive is the dataset RevolutionCrossroads/loc_chronicling_america_1770-1810: the Library of Congress's scans of
the surviving newspapers, each page with the Library's own OCR (CA) and an AI transcription made for the Smithsonian's
Revolution Crossroads (RevX). This script reads the evidence of the project's checks and the scan verdicts of the
reviewed years, and writes outputs/archive_errata/:

  filing.csv         every issue whose transcriptions or date are filed in the wrong place, one row per issue
  transcription.csv  every reviewed printing whose transcription changes what was printed, with the reviewer's notes
  summary.json       the counts and the examples the Findings page shows (work/findings_parts.py)

Inputs: outputs/revx_page_shift_check/ (shifted_issues.csv, summary.json, impact.json), outputs/kentucky_gazette_dates/
issues.csv, outputs/story_discovery_1793/ (masthead_dates.csv, page_date_flags.csv), the scan verdicts of the reviewed
years (outputs/story_discovery_YEAR/scan_verdicts/, later files win), the site's data.json (newspapers, dates and pages of
the reviewed printings) and the matched audit's summary. Run from the project root with Python 3.12:
    python work/archive_errata.py
"""
import csv, datetime, glob, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'outputs' / 'archive_errata'
SITE = ROOT / 'outputs' / 'newspaper_pulses_space'
# The reviewed years whose scan checks left structured verdicts (1797's review left notes only). After a new reviewed
# year: rebuild the site (this script reads its data.json), run this script, and build again for the Findings page.
YEARS = tuple(sorted(int(p.parent.name.rsplit('_', 1)[1]) for p in ROOT.glob('outputs/story_discovery_[0-9]*/scan_verdicts')))


def read_csv(path):
    with open(path, encoding='utf8', newline='') as f: return list(csv.DictReader(f))


def verdicts(year):
    """A reviewed year's scan verdicts: batches, hand boxes, then rechecks (sorted by name). A later file's fields win; a
    recheck that gives only a new grade and finding keeps the errors listed before it."""
    v = {}
    for f in sorted(glob.glob(str(ROOT / f'outputs/story_discovery_{year}/scan_verdicts/*.json'))):
        d = json.loads(Path(f).read_text(encoding='utf8'))
        for r in (d if isinstance(d, list) else d.get('verdicts', d.get('items', []))):
            if isinstance(r, dict) and 'id' in r: v[r['id']] = {**v.get(r['id'], {}), **r}
    return v


def day(iso):
    d = datetime.date.fromisoformat(iso); return f'{d.day} {d.strftime("%B %Y")}'


filing = []

# 1 · Transcriptions filed under another page of their issue (the RevX page-shift check of 10 November 2026).
shift = read_csv(ROOT / 'outputs/revx_page_shift_check/shifted_issues.csv')
shift_sum = json.loads((ROOT / 'outputs/revx_page_shift_check/summary.json').read_text(encoding='utf8'))
impact = json.loads((ROOT / 'outputs/revx_page_shift_check/impact.json').read_text(encoding='utf8'))
assert len(shift) == 133, len(shift)
for r in shift:
    moves = re.findall(r'RevX (\d+) = scan (\d+) \(([\d.]+) vs ([\d.]+) own\)', r['pattern'])
    assert moves or r['kind'] == 'shifted', r['issue']
    repeated = r['kind'] == 'duplicate'
    what = '; '.join(f'the RevX transcription filed as page {a} is the text of scan page {b}' for a, b, *_ in moves) or r['pattern']
    if repeated: what += ' (the same text is also filed under its own page)'
    filing.append({
        'problem': 'RevX transcription repeated under another page' if repeated else 'RevX transcriptions filed under the wrong page',
        'lccn': r['lccn'], 'newspaper': r['newspaper'], 'filed_date': r['date'], 'edition': r['edition'], 'page': '',
        'what_is_wrong': what[0].upper() + what[1:] + '.',
        'how_it_was_found': ('Each page\'s RevX text compared with the Library\'s OCR of every page of its issue (shares of 4-word phrases): '
                             + '; '.join(f'RevX {a} shares {float(s):.0%} with scan {b}, {float(o):.0%} with its own page' for a, b, s, o in moves)
                             + (f'. {r["mechanism"][0].upper() + r["mechanism"][1:]}.' if r['mechanism'] != 'irregular' else '. An irregular order.')),
        'in_this_project': 'Re-filed under the scan pages in data release v0.8.1 (the automatically matched stories).'})
moved_pages = sum(int(r['pages_moved']) for r in shift)
pages_block = {'issues': len(shift), 'pages': moved_pages, 'newspapers': len({r['lccn'] for r in shift}),
               'years': [min(int(r['year']) for r in shift), max(int(r['year']) for r in shift)],
               'by_kind': dict(Counter(r['kind'] for r in shift)), 'by_mechanism': dict(Counter(r['mechanism'] for r in shift)),
               'pages_without_revx': shift_sum['pages_not_tested']['no RevX text'], 'all_pages': shift_sum['pages'],
               'matched_printings_on_a_wrong_page': sum(impact['appearances']['printings_on_a_wrong_page'].values()), 'release': '0.8.1'}

# 2 · Issues filed under the wrong date: the Kentucky Gazette and General Advertiser of 1806-1808 (redated in v0.10.2)...
kg = [r for r in read_csv(ROOT / 'outputs/kentucky_gazette_dates/issues.csv') if r['printed_date'] != r['filed_date']]
assert len(kg) == 106, len(kg)
kg_title = next(r['newspaper'] for r in shift if r['lccn'] == 'sn84038147')
KG_NAME = 'Kentucky Gazette and General Advertiser'   # the catalogue title, in the site's capitals
assert kg_title.lower() == KG_NAME.lower(), kg_title
for r in kg:
    lccn, filed, edition = r['issue_id'].split(':')[1:4]
    if r['basis'] == 'masthead': how = f'The masthead reads "{r["masthead"]}"' + (f', issue No. {r["issue_number"]}' if r['issue_number'] else '') + '.'
    elif r['basis'] == 'scan': how = 'Read on the scan' + (f': {r["scan_note"]}' if r['scan_note'] else '') + '.'
    else: how = ('No masthead could be read; the filed date less two years falls on one of the paper\'s publication days, '
                 'as for every readable issue of the run.')
    filing.append({'problem': 'Issue filed under the wrong date', 'lccn': lccn, 'newspaper': kg_title, 'filed_date': filed, 'edition': edition,
                   'page': '', 'what_is_wrong': f'Filed under {filed}; printed {r["printed_date"]}, two years earlier.', 'how_it_was_found': how,
                   'in_this_project': 'Dated as printed in data release v0.10.2 (its ids keep the filed date).'})
kg_years = Counter(f'{r["filed_date"][:4]} -> {r["printed_date"][:4]}' for r in kg)

# ...and two issues of the Gazette of the United States in 1793, read on their mastheads and confirmed on the scans.
mast = {r['key']: r for r in read_csv(ROOT / 'outputs/story_discovery_1793/masthead_dates.csv')}
GUS = [('sn83030483|1793-04-04|1|1', '1793-05-04', 'Whole No. 419'), ('sn83030483|1793-07-23|1|1', '1793-07-13', 'No. 439')]
for key, printed, number in GUS:
    m = mast[key]; assert m['masthead_date'] == printed, key
    filing.append({'problem': 'Issue filed under the wrong date', 'lccn': 'sn83030483', 'newspaper': m['paper'], 'filed_date': m['filed_date'], 'edition': '1',
                   'page': '', 'what_is_wrong': f'Filed under {m["filed_date"]}; printed {printed}.',
                   'how_it_was_found': f'The masthead reads "{m["masthead"]}" ({number}); confirmed on the scan. The paper appeared on Wednesdays and Saturdays.',
                   'in_this_project': 'Not corrected; no reviewed printing stands on it.'})

# 3 · A second scan filed under another date (American Herald of Liberty, 1793), found by datelines later than the issue.
flags = {r['page']: r for r in read_csv(ROOT / 'outputs/story_discovery_1793/page_date_flags.csv')}
ahl = flags['sn84023134|1793-07-02|1|3']
assert ahl['closest_later_page'] == 'sn84023134|1793-07-09|1|3' and float(ahl['share4']) > .9
filing.append({'problem': 'Second scan filed under another date', 'lccn': 'sn84023134', 'newspaper': ahl['paper'], 'filed_date': '1793-07-02', 'edition': '1',
               'page': '3-4', 'what_is_wrong': 'Pages 3 and 4 filed under 2 July 1793 are a second scan of pages 3 and 4 of the issue of 9 July 1793.',
               'how_it_was_found': (f'Page 3 prints "BOSTON, JULY 3" and the heading "EXETER, TUESDAY, JULY 9, 1793", and its text shares '
                                    f'{float(ahl["share4"]):.0%} of its 4-word phrases with the page filed under 9 July (different images of the same printed page).'),
               'in_this_project': 'Not corrected; no reviewed printing stands on it.'})

# 4 · Transcriptions that change what was printed: every reviewed printing the scan check found with a fact-changing
# problem (a misreading, or printed text left out), in the four reviewed years with structured verdicts.
data = json.loads((SITE / 'data.json').read_text(encoding='utf8'))
YEARS = tuple(y for y in YEARS if y in {r['year'] for r in data['reviewed']})   # a review still under way has verdicts but no stories yet
obs, names = {}, {}
for y in data['reviewed']:
    for p in y['newspapers']: names[p['lccn']] = p['title']
    for o in y['observations']: obs[o['id'].rsplit(':', 1)[1]] = o
LEAVES = re.compile(r"\bdrop|\bomit|left out|leaves out|transcription '[^']*(?:\.\.\.|…)'", re.I)
trans, by_year, all_verdicts = [], {}, {}
for year in YEARS:
    v = verdicts(year); all_verdicts.update(v)
    checked = [r for r in v.values() if r.get('transcription') in ('faithful', 'minor_errors', 'major_problem')]
    major = sorted((r for r in checked if r['transcription'] == 'major_problem'), key=lambda r: r['id'])
    for r in major:
        o = obs[r['id']]; errors = r.get('transcription_errors') or []
        assert errors, r['id']
        trans.append({'year': year, 'printing': r['id'], 'lccn': o['node'], 'newspaper': names[o['node']], 'date': o['date'], 'page': o['page'],
                      'transcription': o['transcription'], 'leaves_out_text': 'yes' if any(LEAVES.search(e) for e in errors) else '',
                      'reviewer_notes': ' | '.join(errors)})
    by_year[year] = {'checked': len(checked), 'changes_what_was_printed': len(major),
                     'by_transcription': dict(Counter(obs[r['id']]['transcription'] for r in major))}


shown = {p['lccn']: p['name'] for y in data['reviewed'] for p in y['newspapers']}


def example(vid, *phrases):
    """An example the page quotes: the phrases must be in that printing's verdict."""
    text = json.dumps(all_verdicts[vid], ensure_ascii=False)
    for p in phrases: assert p in text, (vid, p)
    o = obs[vid]
    return {'printing': vid, 'newspaper': names[o['node']], 'name': shown[o['node']], 'date': o['date'], 'day': day(o['date']), 'transcription': o['transcription']}


staves = sorted(r['printing'] for r in trans if "scan 'ſtaves' / transcription 'slaves'" in r['reviewer_notes'])
audit = json.loads((ROOT / 'outputs/matched_audit/summary.json').read_text(encoding='utf8'))
tr = audit['transcription']; located = tr['faithful']['count'] + tr['minor_errors']['count'] + tr['major_problem']['count']
summary = {
    'made': datetime.date.today().isoformat(), 'script': 'work/archive_errata.py',
    'archive': {'dataset': 'RevolutionCrossroads/loc_chronicling_america_1770-1810', 'pages': shift_sum['pages'], 'issues': shift_sum['issues']},
    'pages': pages_block,
    'dates': {'issues': len(kg) + len(GUS), 'kentucky': {'lccn': 'sn84038147', 'newspaper': kg_title, 'issues': len(kg),
              'pages': sum(int(r['pages']) for r in kg), 'by_year': dict(kg_years), 'by_basis': dict(Counter(r['basis'] for r in kg))},
              'gus_1793': len(GUS), 'release': '0.10.2'},
    'second_scan': {'issues': 1, 'pages': 2},
    'transcription': {'years': list(YEARS), 'checked': sum(b['checked'] for b in by_year.values()),
                      'changes_what_was_printed': len(trans), 'leaves_out_text': sum(1 for r in trans if r['leaves_out_text']),
                      'by_year': by_year,
                      'audit': {'stories': audit['audited'], 'located': located, 'own_calls': audit['raw_reviewer_counts']['transcription']['major_problem'],
                                'strict_rule': tr['major_problem']['count']}},
    'examples': {
        'staves': {'printings': staves, 'of': 9, **example(staves[0], 'ſtaves', 'slaves')},
        'war_inevitable': example('S07-110', 'WAR INEVITABLE!!!', 'NECESSARY INFORMATION!!'),
        'junot': example('S08-065', "'Junot'", "'Juan'"),
        'murat': example('S08-202', '(MURAT.)', '(MANUEL.)'),
        'leaves_out': example('S76-004', 'the true constitution of the colonies, and to their subordinate relation to Great-Britain, now openly avow their revolt, hostility and rebellion', "transcription 'the true constitution of the colonies...'"),
        'staes': example('S07-102', "'U. STAES'", "'U. STATES'", 'silently corrected'),
        'andersecht': example('S93-003', "'Andersecht'", "'Anderlecht'"),
    },
    'files': {'filing': 'filing.csv', 'transcription': 'transcription.csv'},
}
assert len(staves) == 8, staves

OUT.mkdir(parents=True, exist_ok=True)
for name, rows in (('filing.csv', filing), ('transcription.csv', trans)):
    with open(OUT / name, 'w', encoding='utf8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding='utf8')

problems = Counter(r['problem'] for r in filing)
t, k, x = summary['transcription'], summary['dates']['kentucky'], summary['examples']
pct = lambda a, b: f'{100 * a / b:.0f}%'
(OUT / 'README.md').write_text(f'''# Errors found in the archive

Reading the newspapers of the dataset [`{summary["archive"]["dataset"]}`](https://huggingface.co/datasets/{summary["archive"]["dataset"]})
against their page scans turned up errors in the archive itself: pages and issues filed in the wrong place, and machine
transcriptions that change what was printed. They are listed here for the people who keep the archive, so that each case
can be checked on its scan and corrected at the source. The archive holds {summary["archive"]["pages"]:,} pages in
{summary["archive"]["issues"]:,} issues and editions; each page has the Library of Congress's own OCR (called CA here) and
an AI transcription made for the Smithsonian's Revolution Crossroads (RevX).

Made by `work/archive_errata.py` from the project's checks, {summary["made"]}.

## `filing.csv`: {len(filing)} issues filed in the wrong place

One row per issue: the newspaper's LCCN and catalogue title, the date and edition the issue is filed under (and the
pages, where only some are concerned), what is wrong, how it was found, and what this project did about it.

| Problem | Issues |
|---|---|
''' + ''.join(f'| {name} | {n} |\n' for name, n in problems.most_common()) + f'''
- **Transcriptions filed under the wrong page.** Each page's RevX text was compared with the Library's OCR of every page
  of its issue, by the share of 4-word phrases they have in common; a page whose RevX text matches another page far
  better than its own is filed in the wrong place. Mostly one scan page has no RevX text, and every later page's text is
  filed one page early. In all, {pages_block["pages_without_revx"]:,} of the {pages_block["all_pages"]:,} pages have no RevX
  transcription. The check: `outputs/revx_page_shift_check/check_page_shift.py`.
- **Issues filed under the wrong date.** The masthead of every front page of the *{KG_NAME}* ({k["lccn"]}) was read:
  {k["issues"]} issues filed under 1806 to 1808 print a date two years earlier ({"; ".join(f"{n} filed under {a[:4]} and printed in {a[-4:]}" for a, n in sorted(k["by_year"].items(), key=lambda kv: -kv[1]))}):
  {k["by_basis"]["masthead"]} by their masthead dates, {k["by_basis"]["two-year rule"]} where no masthead could be read by the
  paper's publication days, {k["by_basis"]["scan"]} on the scans. The check: `outputs/kentucky_gazette_dates/check_dates.py`.
  Reading every front page of 1793 found two issues of the *Gazette of the United-States* filed away from their mastheads,
  both confirmed on the scans (`outputs/story_discovery_1793/check_mastheads_1793.py`).
- **A second scan filed under another date.** Found by looking for datelines later than the issue a page is filed under
  (1793; `outputs/story_discovery_1793/check_duplicate_pages_1793.py`).

## `transcription.csv`: {t["changes_what_was_printed"]} printings whose transcription changes what was printed

Every printing of the reviewed stories of {", ".join(map(str, YEARS[:-1]))} and {YEARS[-1]} was read against its scan:
{t["checked"]} printings, of which {t["changes_what_was_printed"]} ({pct(t["changes_what_was_printed"], t["checked"])}) carry a misreading
that changes a fact (a number, a date, a name, or a word with another meaning) or leave printed text out. One row per
printing: the newspaper, the date and page, which transcription the passage was taken from (RevX, or CA where RevX is
missing or misfiled), whether printed text is left out, and the reviewers' notes, mostly in the form
`scan '…' / transcription '…'`. A printing's notes may also list smaller errors beside the one that changes a fact.

| Year | Printings read | Changes what was printed |
|---|---|---|
''' + ''.join(f'| {y} | {b["checked"]} | {b["changes_what_was_printed"]} |\n' for y, b in by_year.items()) + f'''
Examples: "ſtaves" read as "slaves" in {len(staves)} of the {summary["examples"]["staves"]["of"]} printings of the resolution of
Congress opening the ports (1776); "WAR INEVITABLE!!!" read as "NECESSARY INFORMATION!!" (1807); "Junot" read as "Juan" and
"(MURAT.)" as "(MANUEL.)" (1808). {t["leaves_out_text"]} of the {t["changes_what_was_printed"]} leave printed text out, often
behind a bare "...".

The matched stories (found automatically, all years) were not read one by one. A random sample of {t["audit"]["stories"]} of
them was read against the scans: {t["audit"]["own_calls"]} of the {t["audit"]["located"]} passages found
({pct(t["audit"]["own_calls"], t["audit"]["located"])}) had a fact-changing misreading by the reviewers' own calls, and
{t["audit"]["strict_rule"]} ({pct(t["audit"]["strict_rule"], t["audit"]["located"])}) under one strict rule.

## Also noticed, not counted

- **Printers' misprints are silently corrected.** "U. STAES" in the *{x["staes"]["name"]}* of {x["staes"]["day"]} is
  transcribed "U. STATES", and "Andersecht" (1793) "Anderlecht". A tidied text reads well, but it cannot show a misprint,
  or tell one printing from another by its slips.

## What this project did

- Release v0.8.1 of the project's data moved the matched stories' printings to the pages their text is on
  ({pages_block["matched_printings_on_a_wrong_page"]} printings).
- Release v0.10.2 dates the *{KG_NAME}* as printed; its issue, page and scan ids keep the filed dates.
- The two 1793 issues and the second scan are not corrected; no reviewed printing stands on them.
- The reviewed passages keep the transcription as it is, and their notes name each error.

`summary.json` holds the counts and the examples the site's Findings page shows.
''', encoding='utf8')
print(json.dumps({k: summary[k] for k in ('pages', 'dates', 'second_scan')}, indent=1))
print('transcription:', {k: v for k, v in summary['transcription'].items() if k != 'by_year'}, {y: (b['checked'], b['changes_what_was_printed']) for y, b in by_year.items()})
print('rows:', len(filing), 'filing,', len(trans), 'transcription')
