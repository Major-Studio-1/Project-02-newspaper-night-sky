"""Make the public repository of Newspaper Night Sky from the working project.

The working project keeps everything: the raw dataset, every release, the review ledgers and
the intermediate outputs. The public repository keeps what a reader needs, in five folders:

  site/      the website, as built by work/build_pulse_explorer.py
  data/      the current data release, without its largest copies (see data/README.md)
  pipeline/  the scripts, as they are in work/
  docs/      the process, the seasons check and the site plan
  process/   from the proposal to the site

The files written by hand for the public repository live in work/public/, in their final places.
This script fills the placeholders in their Markdown (__REPO__, __PAGES_URL__, __PROPOSAL_URL__,
__RELEASE__, __N_STORIES__, __N_MATCHED__, __N_PRINTINGS__).

Usage, from the project root (Python 3.12, like the other scripts):
    python work/export_public_repo.py [target]

The target (default: publish/<repository name>, from REPO in site_parts.py) should be new, or a
git clone of the public repository. Everything in it except .git is replaced, so the copy always
matches the working project. Nothing is committed or pushed.
"""
import gzip
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
PROJECT = WORK.parent
sys.path.insert(0, str(WORK))
from site_parts import PAGES, PROPOSAL, REPO  # noqa: E402

PUBLISH = PROJECT / 'publish'
TARGET = (Path(sys.argv[1]) if len(sys.argv) > 1 else PUBLISH / REPO.rstrip('/').rsplit('/', 1)[-1]).resolve()
if PUBLISH.resolve() not in TARGET.parents:
    sys.exit(f'Refusing to write outside {PUBLISH}: {TARGET}')
if TARGET.exists() and any(TARGET.iterdir()) and not (TARGET / '.git').is_dir():
    sys.exit(f'{TARGET} is not empty and is not a git clone, so it is left alone')

SITE = PROJECT / 'outputs' / 'newspaper_pulses_space'
CURRENT = json.loads((PROJECT / 'outputs/data_foundation/CURRENT.json').read_text(encoding='utf8'))
RELEASE = PROJECT / 'outputs/data_foundation' / CURRENT['path']
VERSION = CURRENT['version']
MANIFEST = json.loads((RELEASE / 'manifest.json').read_text(encoding='utf8'))
HASHES = {entry['path']: entry['sha256'] for entry in MANIFEST['files']}
PROPOSAL_FILES = PROPOSAL.replace('/tree/', '/blob/')   # single files of the proposal, at the same commit

# The site must be built from the current release, and not changed since.
receipt = json.loads((SITE / 'build_validation.json').read_text(encoding='utf8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
stale = [name for name, digest in receipt['pages_sha256'].items() if sha(SITE / name) != digest]
if receipt['release_version'] != VERSION or stale:
    sys.exit(f'Rebuild the site first (python work/build_pulse_explorer.py): {stale or receipt["release_version"]}')

# The matched-story totals come from the release's own metadata table: every release since v0.5.0 records them there,
# while a manifest made by apply_ledger.py (v0.7.0 on) does not repeat them.
METADATA = {row['key']: row['value'] for row in (json.loads(line) for line in (RELEASE / 'tables/metadata.jsonl').read_text(encoding='utf8').splitlines() if line.strip())}
REUSE = METADATA.get('reuse_layer') or MANIFEST['reuse_layer']
FILL = {'__REPO__': REPO, '__PAGES_URL__': PAGES, '__PROPOSAL_URL__': PROPOSAL, '__RELEASE__': VERSION,
        '__N_STORIES__': f"{receipt['telescope_stars']:,}", '__N_MATCHED__': f"{REUSE['families']:,}",
        '__N_PRINTINGS__': f"{REUSE['family_appearances']:,}"}


def fill(text, where):
    for key, value in FILL.items():
        text = text.replace(key, value)
    left = [key for key in FILL if key in text]
    assert not left, f'{where}: unfilled {left}'
    return text


def write(rel, text):
    path = TARGET / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf8', newline='\n')


def copy(src, rel):
    path = TARGET / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, path)


def replace(text, old, new, where):
    """Replace a passage that must be there, so a changed source fails loudly instead of slipping through."""
    assert old in text, f'{where}: expected text not found: {old[:60]}'
    return text.replace(old, new)


# 0 · Start clean, keeping only the git history.
TARGET.mkdir(parents=True, exist_ok=True)
for child in TARGET.iterdir():
    if child.name == '.git':
        continue
    shutil.rmtree(child) if child.is_dir() else child.unlink()

# 1 · The hand-written files: READMEs, screenshots, the Pages workflow, .gitignore.
PUBLIC = WORK / 'public'
for src in sorted(p for p in PUBLIC.rglob('*') if p.is_file()):
    rel = src.relative_to(PUBLIC)
    if src.suffix == '.md':
        write(rel, fill(src.read_text(encoding='utf8'), rel))
    else:
        copy(src, rel)

# 2 · The site, exactly as built.
shutil.copytree(SITE, TARGET / 'site')

# 3 · The data release, without research.sqlite, assets/ and sources/ (listed in the manifest).
#     The three largest tables are gzipped with a fixed timestamp, so an unchanged table gives an unchanged file.
BIG = {'pages.jsonl', 'page_assessments.jsonl', 'page_versions.jsonl'}
for name in ['manifest.json', 'validation.json', 'examples.sql']:
    copy(RELEASE / name, f'data/{name}')
copy(RELEASE / 'README.md', 'data/release-notes.md')
for folder in ['schemas', 'views', 'derived']:
    shutil.copytree(RELEASE / folder, TARGET / 'data' / folder)
for src in sorted((RELEASE / 'tables').glob('*.jsonl')):
    if src.name in BIG:
        raw = src.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == HASHES[f'tables/{src.name}'], src.name
        with (TARGET / 'data/tables' / f'{src.name}.gz').open('wb') as out, \
                gzip.GzipFile(filename='', mode='wb', fileobj=out, mtime=0, compresslevel=9) as stream:
            stream.write(raw)
    else:
        copy(src, f'data/tables/{src.name}')

# 4 · The pipeline: the scripts and templates that made the release and the site.
SCRIPTS = ['audit_dataset.py', 'discover_topics.py', 'recheck_full_corpus.py',
           'search_chains.py', 'search_pilot_1797.py', 'reuse_1797.py', 'reuse_families_1797.py', 'story_phrase_search_1797.py', 'scan_ledger.py',
           'year_search_pages.py', 'story_items.py', 'story_phrase_search.py',
           'reuse_all.py', 'reuse_families_all.py', 'reuse_titles_all.py', 'story_topics_all.py', 'check_cycles_topics.py', 'check_cycle_lengths.py', 'check_waves.py',
           'transcription_check.py', 'audit_matched.py',
           'build_pulse_explorer.py', 'site_parts.py', 'site.css', 'glass.js', 'radio.js', 'home.html', 'telescope.html', 'pulse_explorer.html', 'radio.html', 'exhibit.html', 'method.html', 'notes.html', 'findings.html', 'findings_parts.py', 'notebook.html', 'notebook_parts.py', 'notebook.json', 'stories.html', 'stories_parts.py', 'stories.json',
           'export_public_repo.py', 'audio_render.py', 'audio_manifest.json']
ARCHIVE = ['build.py', 'migrate_v0_2_0.py', 'apply_ledger.py', 'apply_corrections.py', 'add_reuse_layer.py', 'add_reuse_titles.py',
           'add_story_topics.py', 'merge_printings.py', 'add_checks_layer.py', 'add_reviewed_topics.py', 'refile_revx_pages.py', 'redate_issues.py', 'set_current.py', 'validate.py', 'consumer.py', 'check_consumers.py', 'README.md']
for name in SCRIPTS:
    copy(WORK / name, f'pipeline/{name}')
for name in ARCHIVE:
    copy(WORK / 'archive_data' / name, f'pipeline/archive_data/{name}')
# The checks behind the correction releases v0.8.1 and v0.10.2 live with their findings in outputs/; only the scripts go here.
for rel in ['revx_page_shift_check/check_page_shift.py', 'kentucky_gazette_dates/check_dates.py', 'kentucky_gazette_dates/rematch.py']:
    copy(PROJECT / 'outputs' / rel, f'pipeline/{rel}')
# Only files committed in the working repository: a ledger still being written (another session's work in progress,
# for example) stays out of the public repository until it is committed.
import subprocess  # noqa: E402
for folder in ['ledgers', 'baselines']:
    src = WORK / 'archive_data' / folder
    listed = subprocess.run(['git', 'ls-files', '-z', '--', '.'], cwd=src, capture_output=True, check=True).stdout.decode('utf8').split('\0')
    for rel in filter(None, listed):
        copy(src / rel, f'pipeline/archive_data/{folder}/{rel}')

# 5 · Documents. Working paths become this repository's paths.
process = (PROJECT / 'docs/process-intro.md').read_text(encoding='utf8')
process = process.replace('`work/archive_data/', '`pipeline/archive_data/').replace('`work/', '`pipeline/')
process = replace(process, '(`outputs/data_foundation/`)', '([`data/`](../data))', 'process.md')
process = replace(process, 'see `outputs/story_discovery_all/cycles_check.md`', 'see [the seasons check](seasons-check.md)', 'process.md')
process = replace(process, '`outputs/story_discovery_all/waves_check.md`', '[the waves check](waves-check.md)', 'process.md')
head, found, _ = process.partition('## Where to find things')
assert found, 'process.md: the "Where to find things" section is missing'
process = head + f'''## Where to find things

| What | Where |
|---|---|
| Topic model and sampling | `pipeline/audit_dataset.py`, `pipeline/discover_topics.py` |
| Full-collection scoring and trend checks | `pipeline/recheck_full_corpus.py` |
| Story searches | `pipeline/search_chains.py`, `pipeline/search_pilot_1797.py`, `pipeline/story_phrase_search_1797.py` |
| Text-reuse families, 1797 | `pipeline/reuse_1797.py` (matching), `pipeline/reuse_families_1797.py` (grouping) |
| Reviewed stories, 1776 | `pipeline/year_search_pages.py` (the year's pages), `pipeline/story_items.py` (single printed items), `pipeline/story_phrase_search.py`; the ledger is written by `pipeline/archive_data/ledgers/make_stories_1776.py`, and `pipeline/archive_data/add_reviewed_topics.py` adds the new groups' topics |
| Matched stories, all years | `pipeline/reuse_all.py`, `pipeline/reuse_families_all.py`, `pipeline/reuse_titles_all.py`, `pipeline/story_topics_all.py`; added to the release by `pipeline/archive_data/add_reuse_layer.py`, `add_reuse_titles.py` and `add_story_topics.py` |
| Seasons check | `pipeline/check_cycles_topics.py`, with results in [seasons-check.md](seasons-check.md) |
| Cycle lengths and waves | `pipeline/check_cycle_lengths.py` (every period from 6 to 400 days; in [seasons-check.md](seasons-check.md)) and `pipeline/check_waves.py` (how a word comes back, against known history; [waves-check.md](waves-check.md)) |
| Checks of the matched stories | `pipeline/transcription_check.py` (every printing against the page's other transcription), `pipeline/audit_matched.py` (the 200-story audit); added to the release, one printing per page, by `pipeline/archive_data/add_checks_layer.py` with `merge_printings.py` |
| Review decisions and corrections | `pipeline/archive_data/ledgers/`, applied by `pipeline/archive_data/apply_ledger.py`; scan crops made by `pipeline/scan_ledger.py` |
| Data release | [`data/`](../data) (v{VERSION}) |
| Website | [`site/`](../site), built by `pipeline/build_pulse_explorer.py` from the templates beside it |
'''
leftover = re.findall(r'`(?:work|outputs)/[^`]*`', process)
assert not leftover, f'process.md: working paths left: {leftover}'
write('docs/process.md', process)

seasons = (PROJECT / 'outputs/story_discovery_all/cycles_check.md').read_text(encoding='utf8')
seasons = replace(seasons, 'Script: `work/check_cycles_topics.py`. Numbers: `cycles_check.json`.',
                  'Script: [`pipeline/check_cycles_topics.py`](../pipeline/check_cycles_topics.py). Numbers: [`seasons-check.json`](seasons-check.json).', 'seasons-check.md')
seasons = seasons.replace('`work/', '`pipeline/')
write('docs/seasons-check.md', seasons)
copy(PROJECT / 'outputs/story_discovery_all/cycles_check.json', 'docs/seasons-check.json')
waves = (PROJECT / 'outputs/story_discovery_all/waves_check.md').read_text(encoding='utf8').replace('`work/', '`pipeline/')
waves = replace(waves, '(`cycles_check.md`, "Other cycle lengths")', '([the seasons check](seasons-check.md), "Other cycle lengths")', 'waves-check.md')
assert not re.findall(r'`(?:work|outputs)/[^`]*`', waves), 'waves-check.md: working paths left'
write('docs/waves-check.md', waves)

plan = (PROJECT / 'docs/site-plan.md').read_text(encoding='utf8').replace('`work/', '`pipeline/')
write('docs/site-plan.md', plan)

# 6 · The proposal, as submitted, with its links pointed at this layout and at the course repository that keeps the old files.
proposal = (PROJECT / 'outputs/project-02/README.md').read_text(encoding='utf8')
title = '# Project 02 — Newspapers, Attention, and Connected Events'
proposal = replace(proposal, title, f'''{title}

> The proposal as submitted on 1 November 2026, unchanged except for its links. [From proposal to site](README.md) tells how the project developed from here. The original files are in the course repository, [Major-Studio-1/Project-02-newspapers]({PROPOSAL}).''', 'proposals.md')
proposal = replace(proposal, ' · [Selected claim/version ledger](research/chain-pilot.json) · [Relation ledger](research/relations.json) · [Chinese overview](README.zh-CN.md).',
                   f'. The [claim/version ledger]({PROPOSAL_FILES}/research/chain-pilot.json) and [relation ledger]({PROPOSAL_FILES}/research/relations.json) of this stage are in the course repository.', 'proposals.md')
proposal = replace(proposal, '(research/field-notes.md)', '(field-notes.md)', 'proposals.md')
proposal = replace(proposal, 'Sketches are provided as PNG previews and editable SVG files in [`sketches/`](sketches/).',
                   f'Sketches are in [`sketches/`](sketches/); the editable SVG files are in the [course repository]({PROPOSAL}/sketches).', 'proposals.md')
proposal = replace(proposal, '(reports/attention_pilot_report.md)', f'({PROPOSAL_FILES}/reports/attention_pilot_report.md)', 'proposals.md')
proposal = replace(proposal, '(reports/attention_pilot_report.html)', f'({PAGES}notes/attention/attention_pilot_report.html)', 'proposals.md')
proposal = replace(proposal, '(reports/README.md)', f'({PROPOSAL_FILES}/reports/README.md)', 'proposals.md')
proposal = replace(proposal, '(reports/)', f'({PROPOSAL}/reports)', 'proposals.md')
write('process/proposals.md', proposal)
copy(PROJECT / 'outputs/project-02/research/field-notes.md', 'process/field-notes.md')
for src in sorted((PROJECT / 'outputs/project-02/sketches').glob('*.png')):
    copy(src, f'process/sketches/{src.name}')

# 7 · Checks: every relative Markdown link resolves, no file is too big for GitHub, no working path leaks.
broken = []
for md in sorted(TARGET.rglob('*.md')):
    if '.git' in md.parts or md.is_relative_to(TARGET / 'site'):
        continue
    for link in re.findall(r'\]\(([^)\s]+)\)', md.read_text(encoding='utf8')):
        if re.match(r'^(?:[a-z]+:|#)', link):
            continue
        if not (md.parent / link.split('#')[0]).exists():
            broken.append(f'{md.relative_to(TARGET).as_posix()} → {link}')
files = [p for p in TARGET.rglob('*') if p.is_file() and '.git' not in p.relative_to(TARGET).parts]
too_big = [f'{p.relative_to(TARGET).as_posix()} ({p.stat().st_size / 1e6:.0f} MB)' for p in files if p.stat().st_size > 50e6]
leaks = [p.relative_to(TARGET).as_posix() for p in files if p.suffix in {'.md', '.py', '.html', '.yml', '.txt'}
         and re.search(r'C:[\\/]+Users|\.codex[\\/]', p.read_text(encoding='utf8', errors='ignore'))]
sizes = {}
for p in files:
    top = p.relative_to(TARGET).parts[0] if len(p.relative_to(TARGET).parts) > 1 else '(top level)'
    sizes[top] = sizes.get(top, 0) + p.stat().st_size
print(json.dumps({'target': str(TARGET), 'release': VERSION, 'files': len(files),
                  'mb_by_folder': {k: round(v / 1e6, 1) for k, v in sorted(sizes.items())},
                  'mb_total': round(sum(sizes.values()) / 1e6, 1),
                  'broken_links': broken, 'files_over_50_mb': too_big, 'personal_paths': leaks}, indent=2, ensure_ascii=False))
if broken or too_big or leaks:
    sys.exit('Export checks failed')
