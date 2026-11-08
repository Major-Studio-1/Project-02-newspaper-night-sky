"""Random-sample audit of matched stories (2026-11-08).

Matched stories were found automatically by shared wording and nobody has checked them. This audit measures how far
they can be trusted: it draws a fixed random sample of matched stories (long-running ones excluded, as on the site)
and prepares each one to be checked the way the 1797 stories were.
  1. One item? Every printing's full matched passage, in original case, to read side by side.
  2. On the page? One printing per story, chosen at random, cropped from its pinned page scan, to compare with the
     transcription the matcher read.
The audit is blind to the automatic transcription cross-check (work/transcription_check.py), so the two can be
compared afterwards.

Usage (project root, Codex Python 3.12 with pdfplumber/pypdf):
    python work/audit_matched.py sample       # outputs/matched_audit/sample.json
    python work/audit_matched.py crops        # outputs/matched_audit/crops/*.jpg and crop_manifest.json
    python work/audit_matched.py batches      # outputs/matched_audit/batches/batch_NN.json, 25 stories each, for review
    python work/audit_matched.py summarise    # outputs/matched_audit/verdicts/*.json -> summary.json
"""
from pathlib import Path
import collections
import json
import math
import random
import re
import sys
import unicodedata
import urllib.request

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
sys.path.insert(0, str(ROOT))
import pyarrow.parquet as pq
from reuse_all import TOKEN

PROJECT = ROOT.parent
CURRENT = json.loads((PROJECT/'outputs/data_foundation/CURRENT.json').read_text(encoding='utf8'))
RELEASE = PROJECT/'outputs/data_foundation'/CURRENT['path']
OUT = PROJECT/'outputs/matched_audit'
SEED, N, MAX_WORDS = 20261108, 200, 450
REV = '0b97906ad32e269376872934820357fc333151d8'
DATASET = 'RevolutionCrossroads/loc_chronicling_america_1770-1810'
SCANS = ROOT/'scans'


def passage(raw, x0, x1):
    """The matched passage in original case, cut by the matcher's token offsets (as in reuse_families_all.py)."""
    raw = unicodedata.normalize('NFKC', raw or '').replace('ſ', 's')
    raw = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', raw)
    spans = [m.span() for m in TOKEN.finditer(raw)]
    x1 = min(x1, len(spans))
    cut = lambda a, b: re.sub(r'\s+', ' ', raw[spans[a][0]:spans[b - 1][1]]).strip()
    if x1 - x0 <= MAX_WORDS:
        return cut(x0, x1)
    # Long passages keep their opening and their end, where a joined-on neighbouring item would show.
    return f'{cut(x0, x0 + 300)} … [{x1 - x0 - 450:,} words left out] … {cut(x1 - 150, x1)}'


def sample():
    fams = pq.read_table(RELEASE/'derived/reuse_families.parquet', columns=['family_id', 'newspapers', 'appearances', 'first_date', 'long_running']).to_pylist()
    pool = sorted(f['family_id'] for f in fams if not f['long_running'])
    rng = random.Random(SEED)
    chosen = rng.sample(pool, N)
    fam = {f['family_id']: f for f in fams}
    titles = {r['family_id']: r['title'] for r in pq.read_table(RELEASE/'derived/reuse_family_titles.parquet', columns=['family_id', 'title']).to_pylist()}
    papers = {}
    for line in (RELEASE/'tables/newspapers.jsonl').open(encoding='utf8'):
        r = json.loads(line)
        papers[r['lccn']] = (r['titles'][0] if r['titles'] else r['lccn'], r['places'][0] if r['places'] else '')
    apps = collections.defaultdict(list)
    wanted = set(chosen)
    for r in pq.read_table(RELEASE/'derived/reuse_family_appearances.parquet',
                           columns=['family_id', 'seq', 'page_id', 'publication_date', 'lccn', 'page_number', 'span_start', 'span_end', 'transcription']).to_pylist():
        if r['family_id'] in wanted:
            apps[r['family_id']].append(r)
    audit = {r['key']: r for r in pq.read_table(ROOT/'page_audit.parquet', columns=['key', 'file', 'file_row', 'selected_source', 'pdf_url']).to_pylist()}
    key_of = lambda pid: '|'.join(pid.split(':')[1:])
    need = collections.defaultdict(lambda: collections.defaultdict(list))
    for fid in chosen:
        for a in apps[fid]:
            r = audit[key_of(a['page_id'])]
            need[r['file']][r['file_row']].append(a)
    for shard, rows in need.items():
        pf, offset = pq.ParquetFile(ROOT/'data'/shard), 0
        for g in range(pf.num_row_groups):
            n = pf.metadata.row_group(g).num_rows
            hit = [rw for rw in rows if offset <= rw < offset + n]
            if hit:
                table = pf.read_row_group(g, columns=['RevX_OCR_text', 'ca_ocr_text'])
                for rw in hit:
                    for a in rows[rw]:
                        field = 'RevX_OCR_text' if a['transcription'] == 'RevX' else 'ca_ocr_text'
                        a['passage'] = passage(table[field][rw - offset].as_py(), a['span_start'], a['span_end'])
            offset += n
    stories = []
    for k, fid in enumerate(chosen):
        printings = sorted(apps[fid], key=lambda a: (a['publication_date'], int(a['seq'])))
        check = rng.randrange(len(printings))   # the printing to compare with its scan, chosen at random
        stories.append({'n': k + 1, 'family_id': fid, 'title': titles.get(fid, ''), 'newspapers': fam[fid]['newspapers'],
                        'printings': [{'seq': a['seq'], 'date': a['publication_date'], 'paper': papers.get(a['lccn'], (a['lccn'], ''))[0],
                                       'place': papers.get(a['lccn'], ('', ''))[1], 'page': a['page_number'], 'page_key': key_of(a['page_id']),
                                       'transcription': a['transcription'], 'words': a['span_end'] - a['span_start'], 'passage': a['passage']}
                                      for a in printings],
                        'scan_check': check})
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {'seed': SEED, 'size': N, 'population': len(pool), 'population_rule': 'matched stories that are not long-running',
            'release': CURRENT['version'], 'scan_check_rule': 'one printing per story, chosen at random with the same seed'}
    (OUT/'sample.json').write_text(json.dumps({'meta': meta, 'stories': stories}, ensure_ascii=False, indent=1), encoding='utf8')
    sizes = collections.Counter(min(s['newspapers'], 6) for s in stories)
    print(f"sampled {N} of {len(pool):,} stories; newspapers 2/3/4/5/6+: {[sizes[k] for k in (2, 3, 4, 5, 6)]}; printings {sum(len(s['printings']) for s in stories)}")


def crops():
    import pdfplumber
    from pypdf import PdfReader
    from PIL import Image
    from scan_ledger import locate
    data = json.loads((OUT/'sample.json').read_text(encoding='utf8'))
    (OUT/'crops').mkdir(parents=True, exist_ok=True)
    SCANS.mkdir(exist_ok=True)
    manifest = []
    for s in data['stories']:
        p = s['printings'][s['scan_check']]
        lccn, date, ed, page = p['page_key'].split('|')
        stem = f'{lccn}_{date}_{ed}_{page}'
        pdf, png = SCANS/(stem + '.pdf'), SCANS/(stem + '.png')
        url = f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/{lccn}/{date}_{ed}_{page}.pdf?download=true'
        entry = {'n': s['n'], 'family_id': s['family_id'], 'seq': p['seq'], 'page_key': p['page_key'], 'scan_url': url, 'crops': []}
        try:
            if not pdf.exists():
                with urllib.request.urlopen(url, timeout=180) as r:
                    pdf.write_bytes(r.read())
            if not png.exists():
                max(PdfReader(pdf).pages[0].images, key=lambda x: x.image.width * x.image.height).image.save(png)
            im = Image.open(png)
            words_in = re.sub(r' … \[[\d,]+ words left out\] … ', ' ', p['passage']).split()
            first, last = ' '.join(words_in[:8]), ' '.join(words_in[-6:])
            with pdfplumber.open(pdf) as doc:
                pg = doc.pages[0]
                words = pg.extract_words(use_text_flow=True)
                a, sa = locate(words, first)
                # Search for the end over the passage's full length (long passages show only their head and tail).
                b, sb = locate(words, last, a or 0, window=p['words'] + 150)
            entry.update(start_match=round(sa, 3), end_match=round(sb, 3))
            if a is None or b is None or sa < .55 or b < a:
                entry['located'] = False
            else:
                chosen = words[a:b + len(last.split()) + 2]
                sx, sy = im.width / pg.width, im.height / pg.height
                runs, cur = [], [chosen[0]]
                for w in chosen[1:]:
                    if w['top'] < cur[-1]['top'] - 30:   # text moved back up: a new column
                        runs.append(cur); cur = [w]
                    else:
                        cur.append(w)
                runs.append(cur)
                k = 0
                for run in runs:
                    box = [max(0, int((min(w['x0'] for w in run) - 8) * sx)), max(0, int((min(w['top'] for w in run) - 10) * sy)),
                           min(im.width, int((max(w['x1'] for w in run) + 8) * sx)), min(im.height, int((max(w['bottom'] for w in run) + 10) * sy))]
                    # Tall column crops are cut into pieces, so each piece can be read at full size.
                    for top in range(box[1], box[3], 1300):
                        piece = [box[0], top, box[2], min(box[3], top + 1400)]
                        if piece[3] - piece[1] < 40:
                            continue
                        k += 1
                        name = f"{s['n']:03d}_{s['family_id']}_{k}.jpg"
                        im.crop(piece).convert('RGB').save(OUT/'crops'/name, quality=88)
                        entry['crops'].append(name)
                entry['located'] = bool(entry['crops'])
        except Exception as e:   # a failed download or an unreadable PDF is recorded, not fatal
            entry['located'], entry['error'] = False, f'{type(e).__name__}: {e}'
        manifest.append(entry)
        print(s['n'], s['family_id'], p['page_key'], 'located' if entry['located'] else 'NOT LOCATED',
              entry.get('start_match'), entry.get('end_match'), len(entry['crops']), flush=True)
    (OUT/'crop_manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf8')
    print('located', sum(m['located'] for m in manifest), 'of', len(manifest))


def batches(size=25, first=3):
    """Split the sample into review batches (stories before `first` were the pilot): one small file per batch."""
    data = json.loads((OUT/'sample.json').read_text(encoding='utf8'))
    crops_by_n = {m['n']: m for m in json.loads((OUT/'crop_manifest.json').read_text(encoding='utf8'))}
    (OUT/'batches').mkdir(exist_ok=True)
    stories = [s for s in data['stories'] if s['n'] >= first]
    for b, k in enumerate(range(0, len(stories), size), start=1):
        chunk = []
        for s in stories[k:k + size]:
            m = crops_by_n[s['n']]
            chunk.append({**{key: s[key] for key in ('n', 'family_id', 'title', 'newspapers', 'printings', 'scan_check')},
                          'scan_check_printing': {key: s['printings'][s['scan_check']][key] for key in ('seq', 'date', 'paper', 'page')},
                          'crops': [f'outputs/matched_audit/crops/{c}' for c in m['crops']],
                          'locator': {'located': m['located'], 'start_match': m.get('start_match'), 'end_match': m.get('end_match'), 'error': m.get('error')}})
        (OUT/'batches'/f'batch_{b:02d}.json').write_text(json.dumps(chunk, ensure_ascii=False, indent=1), encoding='utf8')
        print(f"batch_{b:02d}: stories {chunk[0]['n']}-{chunk[-1]['n']}, {sum(len(c['crops']) for c in chunk)} crops")


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def shares(vs, key, values):
    n = len(vs)
    out = {}
    for value in values:
        k = sum(v[key] == value for v in vs)
        out[value] = {'count': k, 'share': round(k / n, 3) if n else None, 'ci95': wilson(k, n)}
    return out


def summarise():
    verdicts = {}
    for f in sorted((OUT/'verdicts').glob('*.json')):
        for v in json.loads(f.read_text(encoding='utf8')):
            verdicts[v['family_id']] = v
    data = json.loads((OUT/'sample.json').read_text(encoding='utf8'))
    order = [s['family_id'] for s in data['stories']]
    missing = [fid for fid in order if fid not in verdicts]
    raw = [verdicts[fid] for fid in order if fid in verdicts]
    # Harmonised verdicts: the reviewers' verdicts with the written adjustments applied (adjustments.json).
    adj = json.loads((OUT/'adjustments.json').read_text(encoding='utf8')) if (OUT/'adjustments.json').exists() else {}
    vs = []
    for v in raw:
        h = dict(v)
        for field in ('one_item', 'transcription'):
            change = adj.get(field, {}).get(str(v['n']))
            if change:
                h[field] = change['to']
                if field == 'one_item' and change['to'] == 'yes':
                    h['joined'] = 'none'
        h['on_page'] = 'yes' if v['on_page'] == 'partly' else v['on_page']   # every 'partly' was a crop that stopped short
        vs.append(h)
    n = len(vs)
    located = [v for v in vs if v['on_page'] in ('yes', 'no')]
    sound = sum(v['one_item'] == 'yes' and v['on_page'] == 'yes' and v['transcription'] in ('faithful', 'minor_errors') for v in located)
    summary = {'meta': data['meta'], 'audited': n, 'not_yet_audited': missing,
               'rules': adj.get('rules'),
               'one_item': shares(vs, 'one_item', ['yes', 'no']),
               'joined': dict(collections.Counter(v['joined'] for v in vs if v['one_item'] == 'no')),
               'located_on_scan': len(located), 'not_located': n - len(located),
               'on_page': shares(located, 'on_page', ['yes', 'no']),
               'transcription': shares(located, 'transcription', ['faithful', 'minor_errors', 'major_problem']),
               'sound_among_located': {'count': sound, 'share': round(sound / len(located), 3) if located else None, 'ci95': wilson(sound, len(located))},
               'raw_reviewer_counts': {k: dict(collections.Counter(v[k] for v in raw)) for k in ['one_item', 'joined', 'on_page', 'transcription', 'confidence']},
               'adjusted': {field: sorted(int(k) for k in adj.get(field, {})) for field in ('one_item', 'transcription')}}
    # By story size: two-paper stories are two thirds of all matched stories.
    stories = {s['family_id']: s for s in data['stories']}
    for label, test in (('two_papers', lambda s: s['newspapers'] == 2), ('three_or_more', lambda s: s['newspapers'] >= 3)):
        group = [v for v in vs if test(stories[v['family_id']])]
        ok = sum(v['one_item'] == 'yes' for v in group)
        summary.setdefault('one_item_by_size', {})[label] = {'n': len(group), 'yes': ok, 'share': round(ok / len(group), 3), 'ci95': wilson(ok, len(group))}
    # The blind comparison: what the automatic transcription cross-check said about each scan-checked printing.
    checks_path = PROJECT/'outputs/transcription_check/checks.parquet'
    if checks_path.exists():
        status = {(r['family_id'], r['seq']): r['status'] for r in pq.read_table(checks_path, columns=['family_id', 'seq', 'status']).to_pylist()}
        table = collections.defaultdict(collections.Counter)
        for v in vs:
            s = stories[v['family_id']]
            table[status.get((v['family_id'], s['printings'][s['scan_check']]['seq']), 'unknown')][v['transcription'] if v['on_page'] != 'not_located' else 'not_located'] += 1
        summary['vs_transcription_check'] = {k: dict(c) for k, c in sorted(table.items())}
    (OUT/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    {'sample': sample, 'crops': crops, 'batches': batches, 'summarise': summarise}[sys.argv[1]]()
