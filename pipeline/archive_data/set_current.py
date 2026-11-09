"""Point outputs/data_foundation/CURRENT.json at a released version.

A release cut with `apply_ledger.py ... --keep-current` leaves CURRENT.json where it was, so the site and the other
consumers stay on the previous release until it is switched on purpose (for example once the site has categories for
the new stories). This script switches it, after checking that the release is complete and unchanged.

Usage (project root, Python 3.12):
    python work/archive_data/set_current.py 0.7.2
"""
from pathlib import Path
import hashlib
import json
import sys

FOUNDATION = Path(__file__).resolve().parents[2]/'outputs/data_foundation'


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main(version):
    release = FOUNDATION/('v'+version)
    manifest = json.loads((release/'manifest.json').read_text(encoding='utf8'))
    if manifest.get('status') != 'released' or manifest.get('version') != version:
        raise SystemExit(f'{release} is not a released v{version}.')
    for entry in manifest['files']:
        path = release/entry['path']
        if not path.is_file() or path.stat().st_size != entry['bytes'] or file_sha(path) != entry['sha256']:
            raise SystemExit('Release file missing or changed: '+entry['path'])
    before = json.loads((FOUNDATION/'CURRENT.json').read_text(encoding='utf8'))['version']
    (FOUNDATION/'CURRENT.json').write_text(json.dumps({'version': version, 'path': 'v'+version, 'manifest_sha256': file_sha(release/'manifest.json')}, indent=2), encoding='utf8')
    print(f'CURRENT.json: {before} -> {version} ({len(manifest["files"])} files checked)')


if __name__ == '__main__':
    main(sys.argv[1])
