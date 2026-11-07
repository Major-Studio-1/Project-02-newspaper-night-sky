"""Check independent consumers and the existing pulse display against a release."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import sqlite3

from consumer import PROJECT, embedded_pulse_data, group_records, release_path, verified_file


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    release = release_path()
    manifest = json.loads((release / 'manifest.json').read_text(encoding='utf8'))
    for entry in manifest['files']:
        path = release / entry['path']
        assert path.stat().st_size == entry['bytes'], entry['path']
        assert digest(path) == entry['sha256'], entry['path']

    # This existing inline prototype is deliberately not rebuilt before comparison.
    # A byte-identical copy of the 27 October 2026 prototype is kept beside this script.
    baseline = Path(__file__).resolve().parent / 'baselines' / 'pulse-prototype-2026-10-27.html'
    match = re.search(r'<script type="application/json" id="pulse-evidence-data">(.*?)</script>', baseline.read_text(encoding='utf8'), re.S)
    assert match, 'Existing pulse evidence payload missing'
    old = json.loads(match.group(1))['observations']
    payload = embedded_pulse_data()
    new = payload['observations']
    fields = ('id', 'node', 'publication_date', 'page', 'roles', 'excerpt', 'source_url', 'scan', 'summary')
    by_id = {row['id']: row for row in new}
    # Later releases may admit more selections; every prototype record must survive unchanged.
    assert all(row['id'] in by_id for row in old), 'A prototype pulse record is missing'
    for before in old:
        after = by_id[before['id']]
        for field in fields:
            assert before[field] == after[field], f"Pulse changed: {before['id']} / {field}"
    added = sorted(set(by_id) - {row['id'] for row in old})
    assert not payload.get('edges'), 'No inferred transmission edges should be introduced'

    peace = group_records('group:peace-seizure-report')
    assert {row['legacy_id'] for row in peace['observations']} == {'H012', 'X016'}
    with sqlite3.connect(verified_file('research.sqlite', release).as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        summaries = [dict(row) for row in db.execute('SELECT g.id,g.kind,g.label,s.* FROM groups g JOIN observed_group_summary s ON s.group_id=g.id ORDER BY g.id')]
        union = dict(db.execute('SELECT COUNT(*) AS memberships, COUNT(DISTINCT observation_id) AS distinct_selections FROM group_publications').fetchone())
        row = db.execute("SELECT value_json FROM metadata WHERE key='expected_counts'").fetchone()
    expected = json.loads(row[0]) if row else {'memberships': 16, 'distinct_current_members': 9}
    assert union == {'memberships': expected['memberships'], 'distinct_selections': expected['distinct_current_members']}, union
    output = PROJECT / 'outputs/data_foundation'
    examples = output / 'consumer_examples'
    examples.mkdir(exist_ok=True)
    (examples / 'peace_seizure.json').write_text(json.dumps(peace, ensure_ascii=False, indent=2), encoding='utf8')
    (examples / 'group_summaries.json').write_text(json.dumps({'release_version': manifest['version'], 'groups': summaries, 'union_counts': union}, ensure_ascii=False, indent=2), encoding='utf8')
    report = {
        'passed': True,
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'release_version': manifest['version'],
        'release_manifest_sha256': digest(release / 'manifest.json'),
        'release_files_verified': len(manifest['files']),
        'baseline_path': baseline.relative_to(PROJECT).as_posix(),
        'baseline_sha256': digest(baseline),
        'pulse_records_compared': len(old),
        'pulse_records_added_since_prototype': added,
        'exactly_preserved_fields': list(fields),
        'presentation_note_change': 'Shorter notes from the foundation projection; original review details remain in source snapshots.',
        'independent_group_export': {'group': peace['group']['id'], 'selections': len(peace['observations'])},
        'overlap_union_check': union,
        'checks': ['Every released file matches its recorded length and hash', 'Pulse evidence and compressed scan images match the existing prototype', 'No transmission edges introduced', 'A second group exports without reading visualization HTML', 'Overlapping memberships are counted distinctly in union summaries'],
    }
    (output / 'integration_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
