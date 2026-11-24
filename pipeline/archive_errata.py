"""What reading the papers turned up wrong in the archive itself, gathered for the people who keep it.

The archive is the dataset RevolutionCrossroads/loc_chronicling_america_1770-1810: the Library of Congress's scans of
the surviving newspapers, each page with the Library's own OCR (CA) and an AI transcription made for the Smithsonian's
Revolution Crossroads (RevX). This script reads the evidence of the project's checks and the scan verdicts of the
reviewed years, and writes outputs/archive_errata/:

  filing.csv         every issue whose transcriptions or date are filed in the wrong place, one row per issue
  transcription.csv  every reviewed printing whose transcription changes what was printed, with the reviewer's notes
  summary.json       the counts and the examples the Findings page shows (work/findings_parts.py)

Inputs: outputs/revx_page_shift_check/ (shifted_issues.csv, summary.json, impact.json), outputs/kentucky_gazette_dates/
issues.csv, outputs/story_discovery_1793/ (masthead_dates.csv, page_date_flags.csv), outputs/filing_corrections/ and
outputs/filing_corrections_1802/ (corrections.json), the scan verdicts of the reviewed
years (outputs/story_discovery_YEAR/scan_verdicts/, later files win), the site's data.json (newspapers, dates and pages of
the reviewed printings), the matched audit's summary, and outputs/errata_1784_1786/ (filing_part_b.csv: the filing problems
not corrected yet; sample.json and scan_verdicts/: the sample of 1784-1786; range_dates.csv: the range-dated runs). Run from the project root with Python 3.12:
    python work/archive_errata.py
"""
import csv, datetime, glob, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'outputs' / 'archive_errata'
SITE = ROOT / 'outputs' / 'newspaper_pulses_space'
# The reviewed years whose scan checks left structured verdicts, in the year's folder or in a later round's subfolder
# (1797's first two readings left notes only; its third reading, in round3/, left verdicts). After a new reviewed year:
# rebuild the site (this script reads its data.json), run this script, and build again for the Findings page.
YEARS = tuple(sorted({int(p.parent.name.rsplit('_', 1)[1]) for p in ROOT.glob('outputs/story_discovery_[0-9]*/scan_verdicts')}
                     | {int(p.parent.parent.name.rsplit('_', 1)[1]) for p in ROOT.glob('outputs/story_discovery_[0-9]*/*/scan_verdicts')}))


def read_csv(path):
    with open(path, encoding='utf8', newline='') as f: return list(csv.DictReader(f))


def verdicts(year):
    """A reviewed year's scan verdicts: batches, hand boxes, then rechecks (sorted by name). A later file's fields win; a
    recheck that gives only a new grade and finding keeps the errors listed before it."""
    v = {}
    for f in sorted(glob.glob(str(ROOT / f'outputs/story_discovery_{year}/scan_verdicts/*.json'))
                    + glob.glob(str(ROOT / f'outputs/story_discovery_{year}/*/scan_verdicts/*.json'))):
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
# Data release v0.11.7 dates them as printed (work/archive_data/correct_filing.py, outputs/filing_corrections/).
GUS_DONE = {'sn83030483|1793-04-04|1|1': 'Dated as printed in data release v0.11.7 (its ids keep the filed date); no reviewed printing stands on it.',
            'sn83030483|1793-07-23|1|1': ('Dated as printed in data release v0.11.7 (its ids keep the filed date). One reviewed printing stands on it, '
                                          "Captain Fanning's account (S93-117), which now carries 13 July, the date its note records.")}
for key, printed, number in GUS:
    m = mast[key]; assert m['masthead_date'] == printed, key
    filing.append({'problem': 'Issue filed under the wrong date', 'lccn': 'sn83030483', 'newspaper': m['paper'], 'filed_date': m['filed_date'], 'edition': '1',
                   'page': '', 'what_is_wrong': f'Filed under {m["filed_date"]}; printed {printed}.',
                   'how_it_was_found': f'The masthead reads "{m["masthead"]}" ({number}); confirmed on the scan. The paper appeared on Wednesdays and Saturdays.',
                   'in_this_project': GUS_DONE[key]})

# 3 · A second scan filed under another date (American Herald of Liberty, 1793), found by datelines later than the issue.
flags = {r['page']: r for r in read_csv(ROOT / 'outputs/story_discovery_1793/page_date_flags.csv')}
ahl = flags['sn84023134|1793-07-02|1|3']
assert ahl['closest_later_page'] == 'sn84023134|1793-07-09|1|3' and float(ahl['share4']) > .9
filing.append({'problem': 'Second scan filed under another date', 'lccn': 'sn84023134', 'newspaper': ahl['paper'], 'filed_date': '1793-07-02', 'edition': '1',
               'page': '3-4', 'what_is_wrong': 'Pages 3 and 4 filed under 2 July 1793 are a second scan of pages 3 and 4 of the issue of 9 July 1793.',
               'how_it_was_found': (f'Page 3 prints "BOSTON, JULY 3" and the heading "EXETER, TUESDAY, JULY 9, 1793", and its text shares '
                                    f'{float(ahl["share4"]):.0%} of its 4-word phrases with the page filed under 9 July (different images of the same printed page).'),
               'in_this_project': ('Left out of the analysis in data release v0.11.7 (77,749 pages in use became 77,747); '
                                   "the scans stay in the archive's list of pages.")})

# 3b · Pages filed in each other's issues (National Intelligencer, 1806), found by the 1806 dateline and neighbour checks and
# filed under the issues they belong to by data release v0.11.7 (outputs/filing_corrections/corrections.json).
corr = json.loads((ROOT / 'outputs/filing_corrections/corrections.json').read_text(encoding='utf8'))
swapped = {}
for c in corr['page_issues']:
    swapped.setdefault(c['filed_issue'], []).append(c)
for filed_issue, cs in sorted(swapped.items()):
    cs = sorted(cs, key=lambda c: c['page_id']); lccn, filed, edition = filed_issue.split(':')[1:4]
    assert len({c['printed_issue'] for c in cs}) == 1, filed_issue
    filing.append({'problem': 'Pages filed in another issue', 'lccn': lccn, 'newspaper': cs[0]['newspaper'], 'filed_date': filed, 'edition': edition,
                   'page': '-'.join(c['page_id'].split(':')[-1] for c in cs),
                   'what_is_wrong': f'Pages filed under {filed} belong to the issue of {cs[0]["printed_issue"].split(":")[2]}.',
                   'how_it_was_found': ' '.join(c['evidence'] for c in cs),
                   'in_this_project': 'Filed under the issue they belong to in data release v0.11.7 (page ids keep the filed issue).'})

# 3c · The National Intelligencer of 1802: seven issues filed under the wrong dates and the four pages of a second scan,
# found by the review of 1802 and corrected by data release v0.11.13 (outputs/filing_corrections_1802/corrections.json).
ni = json.loads((ROOT / 'outputs/filing_corrections_1802/corrections.json').read_text(encoding='utf8'))
NI_DONE = {'issue:sn83045242:1802-10-10:1': (" One reviewed printing stands on it, the French Senate's address to the First Consul "
                                            '(S02-090), which now carries 1 October, the date its note records.')}
for c in ni['issue_dates']:
    lccn, filed, edition = c['issue_id'].split(':')[1:4]
    filing.append({'problem': 'Issue filed under the wrong date', 'lccn': lccn, 'newspaper': c['newspaper'], 'filed_date': filed, 'edition': edition,
                   'page': '', 'what_is_wrong': f'Filed under {filed}; printed {c["printed_date"]}.', 'how_it_was_found': c['evidence'],
                   'in_this_project': 'Dated as printed in data release v0.11.13 (its ids keep the filed date).' + NI_DONE.get(c['issue_id'], '')})
ni_second = sorted(ni['second_scans'], key=lambda c: c['page_id'])
lccn, filed, edition = ni_second[0]['page_id'].split(':')[1:4]
of_issue = ni_second[0]['scan_of'].split(':')[2]
assert all(c['scan_of'].split(':')[2] == of_issue for c in ni_second)
filing.append({'problem': 'Second scan filed under another date', 'lccn': lccn, 'newspaper': ni_second[0]['newspaper'], 'filed_date': filed,
               'edition': edition, 'page': '-'.join(c['page_id'].split(':')[-1] for c in ni_second),
               'what_is_wrong': f'The pages filed under {filed} are a second scan of the issue of {of_issue}.',
               'how_it_was_found': ('The masthead of the first page reads "FRIDAY, DECEMBER 24th, 1802". The CA text of each page is the CA text '
                                    'of the same page of the issue filed under 24 December word for word, and the RevX texts share 92% to 100% '
                                    'of their 4-word phrases (other pages of the two issues 1% or less).'),
               'in_this_project': ('Left out of the analysis in data release v0.11.13 (77,747 pages in use became 77,743); '
                                   "the scans stay in the archive's list of pages.")})

# 3d · Filing problems found by the reviews of the years with few surviving papers (23-24 November 2026), the 1801 review's
# misdated Monitor and the errata check of 1784-1786: outputs/errata_1784_1786/filing_part_b.csv, in this file's columns
# (made by outputs/errata_1784_1786/make_part_b.py). Data release v0.11.40 corrects most of them
# (work/archive_data/correct_filing_thin.py); its 'correction' column says which wait.
THIN = ROOT/'outputs/errata_1784_1786'
THIN_RELEASE = '0.11.40'
FIELDS = ['problem', 'lccn', 'newspaper', 'filed_date', 'edition', 'page', 'what_is_wrong', 'how_it_was_found', 'in_this_project']
thin = read_csv(THIN/'filing_part_b.csv') if (THIN/'filing_part_b.csv').exists() else []
filing += [{k: r[k] for k in FIELDS} for r in thin]
PLURAL = {'Second copy filed as another edition': ('second copies of an issue filed as another edition', 'second copy of an issue filed as another edition'),
          'Second scan filed under another date': ('second scans filed under another date', 'second scan filed under another date'),
          'Second scan filed under another title': ('second scans filed under another title', 'second scan filed under another title'),
          'Issue filed under the wrong date': ('issues filed under the wrong date', 'issue filed under the wrong date'),
          'Issue filed under the first day of its range': ('issues filed under the first day of the range of days their mastheads print',
                                                           'issue filed under the first day of the range of days its masthead prints'),
          'Pages filed in another issue': ('issues holding pages of another issue or sheet', 'issue holding pages of another issue or sheet'),
          'RevX transcriptions filed under the wrong page': ('issues whose RevX transcriptions are filed under the wrong page',
                                                             'issue whose RevX transcriptions are filed under the wrong page')}
waiting = [r for r in thin if r.get('correction') == 'not_in_this_release']
thin_block = {'issues': len(thin), 'by_problem': dict(Counter(r['problem'] for r in thin)), 'corrected_in': THIN_RELEASE,
              'corrected': len(thin) - len(waiting), 'not_corrected': len(waiting),
              'years': sorted({int(r['filed_date'][:4]) for r in thin}), 'source': 'outputs/errata_1784_1786/README.md'}

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

# 4b · 1784, 1785 and 1786, which no review read, checked on a sample for the errata only: the printings chosen by the rule
# in outputs/errata_1784_1786/README.md (sample.json, stated before any checking) and their scan_verdicts/. Their rows join
# transcription.csv (printing ids E84-, E85-, E86-); their counts stay apart from the reviewed years' totals.
reviewed_trans = list(trans)
sample = {s['id']: s for s in json.loads((THIN/'sample.json').read_text(encoding='utf8'))} if (THIN/'sample.json').exists() else {}
sv = {}
for f in sorted(glob.glob(str(THIN/'scan_verdicts/*.json'))):
    for r in json.loads(Path(f).read_text(encoding='utf8')):
        if isinstance(r, dict) and r.get('id') in sample:
            sv[r['id']] = {**sv.get(r['id'], {}), **r}
sample_by_year = {}
for year in sorted({s['year'] for s in sample.values()}):
    checked = [r for i, r in sorted(sv.items()) if sample[i]['year'] == year and r.get('transcription') in ('faithful', 'minor_errors', 'major_problem')]
    major = [r for r in checked if r['transcription'] == 'major_problem']
    for r in major:
        s, errors = sample[r['id']], r.get('transcription_errors') or []
        assert errors, r['id']
        trans.append({'year': year, 'printing': r['id'], 'lccn': s['lccn'], 'newspaper': s['catalogue_title'], 'date': s['date'], 'page': s['page'],
                      'transcription': s['transcription'], 'leaves_out_text': 'yes' if any(LEAVES.search(e) for e in errors) else '',
                      'reviewer_notes': 'Checked for the errata only (a sample of 1784-1786): ' + ' | '.join(errors)})
    sample_by_year[year] = {'sample': sum(1 for s in sample.values() if s['year'] == year), 'checked': len(checked),
                            'changes_what_was_printed': len(major)}


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
    'dates': {'issues': len(kg) + len(GUS) + len(ni['issue_dates']), 'ni_1802': len(ni['issue_dates']), 'ni_release': '0.11.13', 'kentucky': {'lccn': 'sn84038147', 'newspaper': kg_title, 'issues': len(kg),
              'pages': sum(int(r['pages']) for r in kg), 'by_year': dict(kg_years), 'by_basis': dict(Counter(r['basis'] for r in kg))},
              'gus_1793': len(GUS), 'release': '0.10.2', 'gus_release': '0.11.7'},
    'second_scan': {'issues': 2, 'pages': 2 + len(ni_second), 'release': '0.11.7', 'releases': ['0.11.7', '0.11.13']},
    'swapped_pages': {'issues': len(swapped), 'pages': sum(len(v) for v in swapped.values()), 'release': '0.11.7'},
    'thin_years': thin_block,
    'transcription': {'years': list(YEARS), 'checked': sum(b['checked'] for b in by_year.values()),
                      'changes_what_was_printed': len(reviewed_trans), 'leaves_out_text': sum(1 for r in reviewed_trans if r['leaves_out_text']),
                      'by_year': by_year,
                      'audit': {'stories': audit['audited'], 'located': located, 'own_calls': audit['raw_reviewer_counts']['transcription']['major_problem'],
                                'strict_rule': tr['major_problem']['count']},
                      'sample_1784_1786': {'by_year': sample_by_year, 'checked': sum(b['checked'] for b in sample_by_year.values()),
                                           'changes_what_was_printed': sum(b['changes_what_was_printed'] for b in sample_by_year.values()),
                                           'rule': 'outputs/errata_1784_1786/README.md#the-transcription-sample'}},
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
# A year whose structured verdicts cover only a later round (1797: its third reading) says so.
n_printings = {r['year']: len(r['observations']) for r in data['reviewed']}
PARTIAL = ''.join(f' For {y} the count is the {b["checked"]} printings of its later reading; its other {n_printings[y] - b["checked"]} were '
                  'checked against their scans before verdicts were recorded in this form.'
                  for y, b in by_year.items() if b['checked'] < .9 * n_printings[y])
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
  both confirmed on the scans (`outputs/story_discovery_1793/check_mastheads_1793.py`). The review of 1802 found seven
  issues of the *National Intelligencer* filed away from their mastheads, read on the scans
  (`outputs/filing_corrections_1802/check_ni_1802.py`).
- **Second scans filed under another date.** Found by looking for datelines later than the issue a page is filed under
  (1793; `outputs/story_discovery_1793/check_duplicate_pages_1793.py`), and by the masthead of an issue filed under
  24 November 1802 that prints 24 December (1802; `outputs/filing_corrections_1802/check_ni_1802.py`).
- **Pages filed in another issue.** Pages 3 and 4 of the *National Intelligencer* of 9 July and 8 September 1806 are filed
  in each other's issues: found by their datelines and by comparing each page with its neighbours (1806;
  `outputs/story_discovery_1806/check_duplicate_pages_1806.py`, `outputs/story_discovery_1806/check_page_neighbours_1806.py`).
''' + (f'''- **Found by the reviews of the years with few surviving papers ({thin_block["issues"]} issues).** The reviews of 1770 to 1799
  (read on 23 and 24 November 2026), the review of 1801 and a check of every masthead of 1784, 1785 and 1786 on the scans
  found {"; ".join(f"{n} {PLURAL[p][1] if n == 1 else PLURAL[p][0]}" for p, n in sorted(thin_block["by_problem"].items(), key=lambda kv: -kv[1]))}.
  Two papers, the *Connecticut Courant* of 1773-74 and the *Royal Gazette* of Charleston of 1781-82, head each issue with a
  range of days and are filed under its first day, though each appeared on its last; the collection files other such papers
  under the last day. Data release v{thin_block["corrected_in"]} corrects {thin_block["corrected"]} of these issues; {thin_block["not_corrected"]} wait: second copies whose
  pages are to be read on their scans, and RevX pages too garbled for the page check's rule (`outputs/errata_1784_1786/`).
''' if thin else '') + f'''
## `transcription.csv`: {len(trans)} printings whose transcription changes what was printed

Every printing of the reviewed stories of {", ".join(map(str, YEARS[:-1]))} and {YEARS[-1]} was read against its scan:
{t["checked"]} printings, of which {t["changes_what_was_printed"]} ({pct(t["changes_what_was_printed"], t["checked"])}) carry a misreading
that changes a fact (a number, a date, a name, or a word with another meaning) or leave printed text out.{PARTIAL} One row per
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
''' + (f'''
No review read 1784, 1785 or 1786 (too few papers survive for any item to reach the bar), so these years were checked on a
sample, for this list only: every printing of the eleven texts the count of 1784 found in two or three papers, and for each
month of 1785 and 1786 the first passage both surviving papers printed, chosen by that rule before any checking
(`outputs/errata_1784_1786/`). It is a sample of reprinted items, chosen so that each month and both papers are covered, not
every page, so its rate is not the archive's. Its rows in `transcription.csv` have printing ids E84-, E85- and E86-, and
their notes say "Checked for the errata only"; they are not in the counts above.

| Year | Sample | Printings read | Changes what was printed |
|---|---|---|---|
''' + ''.join(f'| {y} | {b["sample"]} | {b["checked"]} | {b["changes_what_was_printed"]} |\n' for y, b in sample_by_year.items()) if sample_by_year else '') + f'''
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
- Release v0.11.7 dates the two 1793 issues as printed, files the 1806 pages under the issues they belong to, and leaves the
  second scan out of the analysis (77,747 usable pages rather than 77,749). One reviewed printing stands on a corrected
  page: Captain Fanning's account of 1793, which takes its issue's printed date, 13 July.
''' + (f'''- Release v{thin_block["corrected_in"]} dates 169 issues as printed or issued (162 of them dated by the last day of their ranges),
  files 16 pages with the issues they belong to (12 of them in four issues the collection did not hold), and leaves 347
  pages of second scans and second copies out of the analysis (77,743 usable pages become 77,396). The reviewed printings
  on corrected pages take their issues' dates.
''' if thin else '') + f'''- The reviewed passages keep the transcription as it is, and their notes name each error.

`summary.json` holds the counts and the examples the site's Findings page shows.
''', encoding='utf8')
print(json.dumps({k: summary[k] for k in ('pages', 'dates', 'second_scan', 'swapped_pages', 'thin_years')}, indent=1))
print('sample 1784-1786:', summary['transcription']['sample_1784_1786'])
print('transcription:', {k: v for k, v in summary['transcription'].items() if k != 'by_year'}, {y: (b['checked'], b['changes_what_was_printed']) for y, b in by_year.items()})
print('rows:', len(filing), 'filing,', len(trans), 'transcription')
