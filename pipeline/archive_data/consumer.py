"""Read the released foundation without depending on visualization HTML."""
from pathlib import Path
import argparse
import base64
import hashlib
import io
import json
import sqlite3

PROJECT=Path(__file__).resolve().parents[2]

def release_path():
    base=PROJECT/'outputs/data_foundation'
    current=json.loads((base/'CURRENT.json').read_text(encoding='utf8'))
    release=(base/current['path']).resolve()
    if not release.is_relative_to(base.resolve()): raise ValueError('Release path is outside the data foundation')
    raw=(release/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=current['manifest_sha256']: raise ValueError('Release manifest changed')
    if json.loads(raw)['status']!='released': raise ValueError('Unreleased data cannot be consumed')
    return release

def verified_file(relative, release=None):
    release=release or release_path()
    manifest=json.loads((release/'manifest.json').read_text(encoding='utf8'))
    entry=next((f for f in manifest['files'] if f['path']==relative),None)
    if entry is None: raise ValueError('File is not in the release manifest: '+relative)
    path=(release/relative).resolve()
    if not path.is_relative_to(release): raise ValueError('Artifact path escaped the release')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']: raise ValueError('Released artifact changed: '+relative)
    return path

def group_records(group_id):
    release=release_path()
    path=verified_file('research.sqlite',release)
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        group=db.execute('SELECT * FROM groups WHERE id=?',(group_id,)).fetchone()
        if group is None: raise KeyError(group_id)
        rows=[]
        for record in db.execute('SELECT * FROM group_publications WHERE group_id=? ORDER BY publication_date,newspaper_id,observation_id',(group_id,)):
            row=dict(record)
            row['excerpts']=json.loads(row.pop('excerpts_json'))
            row['roles']=json.loads(row.pop('roles_json'))
            rows.append(row)
    manifest=json.loads((release/'manifest.json').read_text(encoding='utf8'))
    return {'release_version':manifest['version'],'group':dict(group),'observations':rows}

def embedded_pulse_data():
    # Image compression preserves the existing prototype's presentation assets.
    from PIL import Image
    release=release_path()
    data=json.loads(verified_file('views/pulse_boyd.json',release).read_text(encoding='utf8'))
    records=[]
    for record in data['observations']:
        asset=verified_file(record['scan_asset'],release)
        with Image.open(asset) as im:
            im.thumbnail((850,1200));buf=io.BytesIO()
            im.convert('RGB').save(buf,format='JPEG',quality=68,optimize=True)
        row=dict(record)
        row['scan']='data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode('ascii')
        records.append(row)
    return {'schema_version':data['schema_version'],'release_id':data['release_id'],'observations':records}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Export an admitted group for independent analysis or visualization.')
    parser.add_argument('--group',required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    text=json.dumps(group_records(args.group),ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding='utf8')
        print(args.output)
    else: print(text)
