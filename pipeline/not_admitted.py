"""Items read in the story reviews and not admitted: check the list and publish it.

Reads work/not_admitted.json (curated by hand) and every reviewed-year ledger,
work/archive_data/ledgers/stories_YEAR[_roundN].json (not the *_review.json
scan findings, the corrections ledgers or expansion_1797.json).

Checks, and stops without writing anything if one fails:
- every key of not_admitted, for_the_owner and for_user_decision in the
  dispositions_summary of every ledger is the source of at least one entry
  or accounted record, so nothing read is silently dropped;
- every source names an existing ledger key in those sections, or an existing
  heading of a year's README with the phrase under it;
- every accounted record has a known status: 'admitted later' names groups of a
  later round of the same year, 'duplicate of X' names a source that an entry
  lists, and every group named exists;
- 1797: every candidate family that was read (3 or more papers in
  outputs/story_discovery_1797/families.json) is either admitted by a 1797
  ledger or listed by exactly one entry.

Writes outputs/not_admitted/not_admitted.csv and outputs/not_admitted/README.md
(UTF-8, LF line endings).

Run from the project root, with the Codex Python 3.12 (standard library only):
    python work/not_admitted.py
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURATED = ROOT / 'work' / 'not_admitted.json'
LEDGERS = ROOT / 'work' / 'archive_data' / 'ledgers'
OUTPUTS = ROOT / 'outputs'
OUT_DIR = OUTPUTS / 'not_admitted'

SECTIONS = ('not_admitted', 'for_the_owner', 'for_user_decision')
KINDS = ('below the rule', 'not chosen: month and kind covered', 'digest, list or proceedings',
         'private persons', 'other')
KIND_HEADINGS = {
    'below the rule': 'Below the rule',
    'not chosen: month and kind covered': 'Not chosen: month and kind covered',
    'digest, list or proceedings': 'Digests, lists and proceedings',
    'private persons': 'Private persons',
    'other': 'Other',
}
KIND_COLUMNS = ('Below the rule', 'Not chosen', 'Digests, lists, proceedings', 'Private persons', 'Other')
ADMITTED_LATER = 'admitted later'
STATUSES = (ADMITTED_LATER, 'counting decision about admitted stories', 'note on admitted stories')
DUPLICATE = 'duplicate of '

RULE_7 = ("An item printed in 9 or more papers is admitted, except digests; items in 7 or 8 papers are "
          "chosen to cover the months and the kinds of news.")
RULES = {
    1776: RULE_7,
    1793: ("A story needs one printed item in 6 or more papers, because few papers of 1793 survive; "
           "items in 6 are chosen as items in 7 or 8 are in other years."),
    1797: ("Read on 6 November 2026, before the one rule: candidate families of 3 to 5 papers were read and "
           "some were chosen, and its stories reach 2 to 5 papers. Read again by the one rule on 22 November 2026 "
           "(round three): no item of 1797 reaches 7 papers, or 6, so 1797 uses a threshold of 4 papers, adopted "
           "on 23 November 2026 because fewer papers survive; the stories of the first reading that do not "
           "reach it stay reviewed, an exception kept that day. Its list holds the pages set aside while counting the "
           "stories of the first two rounds, the candidate families read on 6 November and not chosen, and the "
           "items round three read and did not admit."),
}
# The thin years (Y-THIN as amended on 23 November 2026, B1), released from 24 November 2026: the rule, then the year's
# own sentence where its review proposed one.
RULE_THIN = ("Read by the thin-year rule (register Y-THIN, chosen by the owner on 23 November 2026 and amended the "
             "same night, B1): an item, counted by its own words, is eligible when it was printed by more than half of "
             "the papers that survive for its weeks, and by at least 4, except digests; items printed by every paper that "
             "survives for their weeks are admitted, and the other eligible items are chosen to cover the months and the "
             "kinds of news, about as many stories as a standard year. The eligible items not chosen are listed with "
             "their counts, made by machine on their openings and not checked on the scans.")
THIN_OWN = {
    1770: "With four papers, an item reaches the bar only when all four print it.",
    1771: "Four papers survive only in some weeks, so an item reaches the bar only when all four print it in those weeks.",
    1772: "Four papers survive in most weeks, so an item reaches the bar only when all four print it.",
    1773: "Four papers survive in most weeks, so an item printed by all four is admitted.",
    1782: "From September only the four year-round papers survive, so the items all four printed are admitted.",
    1789: "With four papers, an item reaches the bar only when all four print it, and all such items are admitted.",
    1790: "Items printed by every paper of their weeks are admitted; the two other eligible items are chosen.",
    1799: "Four papers survive in July and August, so an item printed by all four is admitted.",
}
for _year in (1770, 1771, 1772, 1773, 1774, 1775, 1777, 1778, 1779, 1780, 1781, 1782, 1783, 1787, 1788, 1789, 1790, 1791, 1792, 1794, 1795, 1796, 1798, 1799):
    RULES[_year] = RULE_THIN + (' ' + THIN_OWN[_year] if _year in THIN_OWN else '')
STATUS_PHRASES = {
    ADMITTED_LATER: 'items that a later round admitted',
    'duplicate': 'repeats of an item listed from another key',
    'counting decision about admitted stories': 'counting decisions about admitted stories',
    'note on admitted stories': 'notes on admitted stories',
}

LEDGER_NAME = re.compile(r'stories_(\d{4})(?:_round(\d+))?\.json')
README_SOURCE = re.compile(r'story_discovery_(\d{4})/README\.md')
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')

problems = []


def problem(message):
    problems.append(message)


def load_ledgers():
    ledgers = {}
    for path in sorted(LEDGERS.glob('stories_*.json')):
        if path.name.endswith('_review.json'):
            continue
        match = LEDGER_NAME.fullmatch(path.name)
        if not match:
            problem(f'{path.name}: not a ledger name this script knows (stories_YEAR[_roundN].json)')
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        ledgers[path.name] = {
            'year': int(match[1]),
            'round': int(match[2] or 1),
            'ds': data.get('dispositions_summary') or {},
            'groups': {group['id'] for group in data.get('new_groups') or []},
        }
    return ledgers


def required_keys(ledgers):
    keys = set()
    for name, ledger in ledgers.items():
        for section in SECTIONS:
            value = ledger['ds'].get(section)
            if value is None:
                continue
            if not isinstance(value, dict):
                problem(f'{name}: dispositions_summary.{section} is not a dict keyed by title')
                continue
            keys.update(f'{name}#{section}/{key}' for key in value)
    return keys


_readmes = {}


def readme_sections(year):
    """(heading, text) for every heading of a year's README; a section runs to the next
    heading of the same or a higher level. Lines inside fenced code are not headings."""
    if year not in _readmes:
        path = OUTPUTS / f'story_discovery_{year}' / 'README.md'
        if not path.exists():
            _readmes[year] = None
            return None
        lines = path.read_text(encoding='utf-8').split('\n')
        heads, fenced = [], False
        for number, line in enumerate(lines):
            if line.lstrip().startswith('```'):
                fenced = not fenced
                continue
            match = None if fenced else HEADING.match(line)
            if match:
                heads.append((number, len(match[1]), match[2]))
        sections = []
        for index, (number, level, title) in enumerate(heads):
            end = next((n for n, lv, _ in heads[index + 1:] if lv <= level), len(lines))
            sections.append((title, '\n'.join(lines[number + 1:end])))
        _readmes[year] = sections
    return _readmes[year]


def source_year(source, ledgers, required):
    """The year a source belongs to, or None (with a problem recorded) if it names nothing."""
    head, hash_, rest = source.partition('#')
    if not hash_:
        problem(f'source without "#": {source}')
        return None
    if head in ledgers:
        if source not in required:
            problem(f'source is not a key of {", ".join(SECTIONS)} in {head}: {source}')
            return None
        return ledgers[head]['year']
    match = README_SOURCE.fullmatch(head)
    if match:
        year = int(match[1])
        heading, slash, phrase = rest.partition('/')
        sections = readme_sections(year)
        if sections is None:
            problem(f'no README for {year}: {source}')
            return None
        bodies = [body for title, body in sections if title == heading]
        if not slash or not phrase:
            problem(f'README source needs "#heading/phrase": {source}')
            return None
        if not bodies:
            problem(f'no heading "{heading}" in story_discovery_{year}/README.md: {source}')
            return None
        if not any(phrase in body for body in bodies):
            problem(f'phrase not found under "{heading}": {source}')
            return None
        return year
    problem(f'source names no ledger or README: {source}')
    return None


def check_entries(entries, ledgers, required):
    seen = set()
    for number, entry in enumerate(entries, 1):
        where = f'entry {number} ({entry.get("item", "?")[:60]})'
        year, item, kind = entry.get('year'), entry.get('item'), entry.get('kind')
        if not isinstance(year, int):
            problem(f'{where}: year must be an integer')
        if not isinstance(item, str) or not item.strip():
            problem(f'{where}: item is empty')
        if kind not in KINDS:
            problem(f'{where}: unknown kind {kind!r}')
        reason = entry.get('reason')
        if not isinstance(reason, str) or not reason.strip():
            problem(f'{where}: reason is empty')
        papers = entry.get('papers')
        if not (papers is None or (isinstance(papers, int) and not isinstance(papers, bool) and papers >= 0)
                or (isinstance(papers, str) and papers.strip())):
            problem(f'{where}: papers must be a number, a short text or null')
        families = entry.get('families')
        if families is not None and (year != 1797 or not isinstance(families, list) or not families):
            problem(f'{where}: families is only for 1797 candidate families, as a non-empty list')
        extra = set(entry) - {'year', 'item', 'papers', 'kind', 'reason', 'source', 'families'}
        if extra:
            problem(f'{where}: unknown fields {sorted(extra)}')
        if (year, item) in seen:
            problem(f'{where}: the same item is listed twice for {year}')
        seen.add((year, item))
        source = entry.get('source')
        if not isinstance(source, str):
            problem(f'{where}: source is missing')
            continue
        found = source_year(source, ledgers, required)
        if found is not None and found != year:
            problem(f'{where}: year {year} but the source is of {found}')


def check_group(reference, year, ledgers, later_than=None):
    ledger_name, hash_, group = reference.partition('#')
    ledger = ledgers.get(ledger_name)
    if not hash_ or ledger is None:
        problem(f'"where" names no ledger: {reference}')
        return
    if ledger['year'] != year:
        problem(f'"where" is in a ledger of {ledger["year"]}, not {year}: {reference}')
    if group not in ledger['groups']:
        problem(f'"where" names a group that {ledger_name} does not hold: {reference}')
    if later_than is not None and ledger['round'] <= later_than:
        problem(f'"admitted later" must name a later round: {reference}')


def check_accounted(accounted, entries, ledgers, required):
    listed = {entry.get('source') for entry in entries}
    for number, record in enumerate(accounted, 1):
        where = f'accounted {number} ({record.get("item", "?")[:60]})'
        source, status = record.get('source'), record.get('status')
        year = record.get('year')
        if not isinstance(record.get('item'), str) or not record['item'].strip():
            problem(f'{where}: item is empty')
        if not isinstance(record.get('note'), str) or not record['note'].strip():
            problem(f'{where}: note is empty')
        if not isinstance(source, str) or source.partition('#')[0] not in ledgers:
            problem(f'{where}: an accounted record must name a ledger key: {source!r}')
            continue
        found = source_year(source, ledgers, required)
        if found is not None and found != year:
            problem(f'{where}: year {year} but the source is of {found}')
        refs = record.get('where') or []
        if not isinstance(refs, list):
            problem(f'{where}: "where" must be a list of ledger#group')
            refs = []
        source_round = ledgers[source.partition('#')[0]]['round']
        if status == ADMITTED_LATER:
            if not refs:
                problem(f'{where}: "admitted later" needs "where"')
            for reference in refs:
                check_group(reference, year, ledgers, later_than=source_round)
        elif status in STATUSES:
            for reference in refs:
                check_group(reference, year, ledgers)
        elif isinstance(status, str) and status.startswith(DUPLICATE):
            target = status[len(DUPLICATE):]
            if target == source:
                problem(f'{where}: a key cannot be a duplicate of itself')
            elif source_year(target, ledgers, required) is not None and target not in listed:
                problem(f'{where}: no entry lists the source it duplicates: {target}')
        else:
            problem(f'{where}: unknown status {status!r}')


def check_1797(entries, ledgers):
    path = OUTPUTS / 'story_discovery_1797' / 'families.json'
    if not path.exists() or 'stories_1797.json' not in ledgers:
        problem('1797: families.json or the 1797 ledger is missing')
        return
    families = json.loads(path.read_text(encoding='utf-8'))['families']
    read = {family['family_id'] for family in families if family['newspapers'] >= 3}
    admitted = set()
    for name, ledger in ledgers.items():
        if ledger['year'] == 1797:
            admitted.update(ledger['ds'].get('families_reviewed') or [])
            admitted.update(ledger['ds'].get('families_admitted') or [])
    listed = Counter(fid for entry in entries if entry.get('year') == 1797 for fid in entry.get('families') or [])
    for fid, count in sorted(listed.items()):
        if count > 1:
            problem(f'1797: {fid} is listed {count} times')
    if admitted & set(listed):
        problem(f'1797: admitted families also listed as not admitted: {sorted(admitted & set(listed))}')
    if set(listed) - read:
        problem(f'1797: listed families that are not among those read: {sorted(set(listed) - read)}')
    if read - admitted - set(listed):
        problem(f'1797: families read but neither admitted nor listed: {sorted(read - admitted - set(listed))}')


def papers_text(papers):
    return '' if papers is None else str(papers)


def write_csv(entries):
    with open(OUT_DIR / 'not_admitted.csv', 'w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['year', 'item', 'papers', 'kind', 'reason', 'source'])
        for entry in entries:
            writer.writerow([entry['year'], entry['item'], papers_text(entry['papers']), entry['kind'],
                             entry['reason'], entry['source']])


def write_readme(entries, accounted):
    years = sorted({entry['year'] for entry in entries})
    by_year = {year: [entry for entry in entries if entry['year'] == year] for year in years}
    out = [
        '# Items read and not admitted',
        '',
        "The reviews read the widely printed items of each reviewed year and admitted those that meet the "
        "year's rule. This list holds every item a review read and did not admit, each with its reason, so "
        'that no part of the archive drops out of view.',
        '',
        '- The candidates came from the automatic families, so most of these items stay in the sky as matched '
        'stars; only the reviewed label is withheld.',
        '- 1797 was read on 6 November 2026, before the one rule existed, so its stories reach 2 to 5 papers; '
        'it was read again by the one rule on 22 November, at a threshold of 4 papers adopted on 23 November '
        'because fewer papers survive (see 1797 below).',
        '- Since 11 November 2026 every item is counted by the same rule whatever its subject. Items once held '
        'back for framing were read again by that rule; those that reach it are admitted, and the others are '
        'listed here with the rest.',
        '- Items that turn on private persons are described without names.',
        '- An item that a later round admitted is not listed. `work/not_admitted.json` records it under '
        '`accounted`, with the ledger and the group.',
        '- **Papers** is the number of newspapers that printed the item, as the review counted it. **Source** '
        'is the ledger key it comes from (`stories_YEAR.json#section/key`, in `work/archive_data/ledgers/`) '
        'or a section of the year\'s review notes (`story_discovery_YEAR/README.md#heading/phrase`), which are '
        'kept with the project\'s working files.',
        '',
        '`work/not_admitted.py` writes this page and `not_admitted.csv` (the same list) from '
        '`work/not_admitted.json`. It checks that every key of `not_admitted`, `for_the_owner` and '
        '`for_user_decision` in every ledger is listed here or accounted for, and that every family of 1797 '
        'that was read is admitted or listed.',
        '',
        '## Counts',
        '',
        '| Year | Items | ' + ' | '.join(KIND_COLUMNS) + ' |',
        '|---|---:|' + '---:|' * len(KIND_COLUMNS),
    ]
    totals = Counter()
    for year in years:
        counts = Counter(entry['kind'] for entry in by_year[year])
        totals.update(counts)
        out.append(f'| [{year}](#{year}) | {len(by_year[year])} | '
                   + ' | '.join(str(counts[kind]) for kind in KINDS) + ' |')
    out.append(f'| **All years** | **{len(entries)}** | '
               + ' | '.join(f'**{totals[kind]}**' for kind in KINDS) + ' |')
    out += [
        '',
        '**Kinds.** *Below the rule*: counted by its own words, the item is in fewer papers than the year\'s '
        'rule. *Not chosen*: it reaches the rule, but its months and kind of news were already covered. '
        '*Digests, lists and proceedings*: not one printed item. *Private persons*: it turns on private '
        'persons. *Other*: a different item from the one admitted, a quotation, or another reason given.',
    ]
    status_counts = Counter('duplicate' if record['status'].startswith(DUPLICATE) else record['status']
                            for record in accounted)
    parts = [f'{status_counts[status]} {phrase}' for status, phrase in STATUS_PHRASES.items() if status_counts[status]]
    if parts:
        listed = parts[0] if len(parts) == 1 else ', '.join(parts[:-1]) + ' and ' + parts[-1]
        out += ['', f'Besides these, `work/not_admitted.json` holds {len(accounted)} records for ledger keys, or '
                    f'parts of keys, that are not items left out: {listed}.']
    for year in years:
        out += ['', f'## {year}', '', RULES.get(year, RULE_7)]
        for kind in KINDS:
            items = [entry for entry in by_year[year] if entry['kind'] == kind]
            if not items:
                continue
            out += ['', f'### {KIND_HEADINGS[kind]} ({len(items)})', '']
            for entry in items:
                papers = '' if entry['papers'] is None else f' Papers: {entry["papers"]}.'
                out.append(f'- **{entry["item"]}.**{papers} {entry["reason"]} Source: `{entry["source"]}`')
    (OUT_DIR / 'README.md').write_text('\n'.join(out) + '\n', encoding='utf-8', newline='\n')


def main():
    curated = json.loads(CURATED.read_text(encoding='utf-8'))
    entries, accounted = curated.get('entries') or [], curated.get('accounted') or []
    if tuple(curated.get('kinds') or ()) != KINDS:
        problem(f'kinds in {CURATED.name} differ from the script: {curated.get("kinds")}')
    ledgers = load_ledgers()
    required = required_keys(ledgers)

    check_entries(entries, ledgers, required)
    check_accounted(accounted, entries, ledgers, required)
    check_1797(entries, ledgers)
    covered = {entry.get('source') for entry in entries} | {record.get('source') for record in accounted}
    for key in sorted(required - covered):
        problem(f'ledger key neither listed nor accounted for: {key}')

    if problems:
        print(f'{len(problems)} problem(s); nothing written:', file=sys.stderr)
        for message in problems:
            print('  - ' + message, file=sys.stderr)
        return 1

    entries = sorted(entries, key=lambda entry: entry['year'])  # stable: curated order within a year
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(entries)
    write_readme(entries, accounted)

    per_year = Counter(entry['year'] for entry in entries)
    statuses = Counter('duplicate of ...' if record['status'].startswith(DUPLICATE) else record['status']
                       for record in accounted)
    print(f'{len(required)} ledger keys in {len(ledgers)} ledgers: every one listed or accounted for.')
    print(f'{len(entries)} items not admitted: '
          + ', '.join(f'{year} {count}' for year, count in sorted(per_year.items())))
    print(f'{len(accounted)} accounted records: '
          + ', '.join(f'{status} {count}' for status, count in sorted(statuses.items())))
    print(f'Wrote {(OUT_DIR / "not_admitted.csv").relative_to(ROOT).as_posix()} and '
          f'{(OUT_DIR / "README.md").relative_to(ROOT).as_posix()}.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
