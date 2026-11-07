"""Download pinned scans for every observation in a ledger and crop each passage for review.

General form of scan_expansion_1797.py. Usage (project root, Codex Python 3.12 with pdfplumber/pypdf):
    python work/scan_ledger.py work/archive_data/ledgers/<ledger>.json
Writes <evidence_dir>/<id>.jpg (or <id>-1.jpg, <id>-2.jpg when the passage crosses a column)
and <evidence_dir>/crop_manifest.json. The crops are review evidence; nothing here admits anything.
"""
from pathlib import Path
import difflib
import json
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
import pdfplumber
from pypdf import PdfReader
from PIL import Image

REV = '0b97906ad32e269376872934820357fc333151d8'
DATASET = 'RevolutionCrossroads/loc_chronicling_america_1770-1810'
SCANS = ROOT/'scans'


def norm(s):
    # Long s prints like f, and older OCR often reads it as f.
    return re.sub('[^a-z]', '', s.lower().replace('ſ', 's')).replace('f', 's')


def locate(words, phrase, start=0, window=None):
    target = ' '.join(norm(w) for w in phrase.split())
    n = len(phrase.split())
    best, score = None, 0.0
    stop = len(words) - n if window is None else min(len(words) - n, start + window)
    for j in range(start, max(start+1, stop)):
        cand = ' '.join(norm(w['text']) for w in words[j:j+n])
        r = difflib.SequenceMatcher(None, target, cand).ratio()
        if r > score:
            best, score = j, r
    return best, score


def main(ledger_path, only=None):
    ledger = json.loads(Path(ledger_path).read_text(encoding='utf8'))
    evidence = ROOT.parent/ledger['evidence_dir']
    evidence.mkdir(parents=True, exist_ok=True)
    SCANS.mkdir(exist_ok=True)
    manifest_path = evidence/'crop_manifest.json'
    previous = {r['id']: r for r in json.loads(manifest_path.read_text())} if manifest_path.exists() else {}
    report = []
    for o in ledger['observations']:
        if only and o['id'] not in only:
            if o['id'] in previous:
                report.append(previous[o['id']])
            continue
        lccn, date, ed, page = o['page_key'].split('|')
        stem = f'{lccn}_{date}_{ed}_{page}'
        pdf, png = SCANS/(stem+'.pdf'), SCANS/(stem+'.png')
        url = f'https://huggingface.co/datasets/{DATASET}/resolve/{REV}/media/{lccn}/{date}_{ed}_{page}.pdf?download=true'
        if not pdf.exists():
            with urllib.request.urlopen(url, timeout=120) as r:
                pdf.write_bytes(r.read())
        if not png.exists():
            max(PdfReader(pdf).pages[0].images, key=lambda x: x.image.width*x.image.height).image.save(png)
        for old in evidence.glob(o['id']+'*.jpg'):
            if re.fullmatch(re.escape(o['id'])+r'(-\d+)?\.jpg', old.name):
                old.unlink()
        im = Image.open(png)
        if o.get('scan_boxes'):
            # Manual boxes (image pixels) for pages whose text layer is too garbled to locate the passage.
            boxes, sa, sb, nwords, method = o['scan_boxes'], None, None, None, 'manual_box'
        else:
            first = ' '.join(o['excerpt_start'].split()[:8])
            last = ' '.join(o['excerpt_end'].split()[-6:])
            with pdfplumber.open(pdf) as doc:
                pg = doc.pages[0]
                words = pg.extract_words(use_text_flow=True)
                a, sa = locate(words, first)
                # Excerpts are at most ~130 words, so look for the end only shortly after the start.
                b, sb = locate(words, last, a or 0, window=300)
                chosen = words[a:b+len(last.split())+2]
            sx, sy = im.width/pg.width, im.height/pg.height
            runs, cur = [], [chosen[0]]
            for w in chosen[1:]:
                if w['top'] < cur[-1]['top'] - 30:  # text moved back up: a new column
                    runs.append(cur)
                    cur = [w]
                else:
                    cur.append(w)
            runs.append(cur)
            boxes = [[max(0, int((min(w['x0'] for w in run)-6)*sx)), max(0, int((min(w['top'] for w in run)-8)*sy)),
                      min(im.width, int((max(w['x1'] for w in run)+6)*sx)), min(im.height, int((max(w['bottom'] for w in run)+8)*sy))] for run in runs]
            nwords, method = len(chosen), 'pdf_text_layer'
        crops = []
        for k, box in enumerate(boxes):
            name = f"{o['id']}.jpg" if len(boxes) == 1 else f"{o['id']}-{k+1}.jpg"
            im.crop(box).convert('RGB').save(evidence/name, quality=90)
            crops.append({'file': name, 'box': box})
        report.append({'id': o['id'], 'key': o['page_key'], 'scan_url': url, 'method': method,
                       'start_match': round(sa, 3) if sa is not None else None, 'end_match': round(sb, 3) if sb is not None else None,
                       'words': nwords, 'crops': crops})
        print(o['id'], o['page_key'], method, 'start', sa and round(sa, 2), 'end', sb and round(sb, 2), 'words', nwords, [c['file'] for c in crops], flush=True)
    order = {o['id']: i for i, o in enumerate(ledger['observations'])}
    report.sort(key=lambda r: order.get(r['id'], 999))
    manifest_path.write_text(json.dumps(report, indent=2), encoding='utf8')


if __name__ == '__main__':
    main(sys.argv[1], set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None)
