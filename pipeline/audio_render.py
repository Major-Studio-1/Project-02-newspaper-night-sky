"""Speech for the radio, made once at build time with Kokoro (Apache 2.0), so visitors only play small audio files.

Run it with the audio environment, not the project's usual Python:
  <audio environment>/Scripts/python.exe work/audio_render.py sample
That environment holds kokoro-onnx, soundfile and lameenc (made with `python -m venv` from the Codex Python 3.12, then
`pip install kokoro-onnx soundfile lameenc`). The model files live outside the repository, in ~/.cache/nns-audio:
kokoro-v1.0.onnx and voices-v1.0.bin from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 .

`sample` renders about twenty clips in several voices into outputs/audio_sample/, with a page to compare them, so the
owner can choose the announcer and the readers before the full render. `manifest` writes work/audio_manifest.json:
every text to say, its voice, tier and pack. `render` makes the clips not made yet (resumable; kept in
~/.cache/nns-audio/clips). `pack` joins them into outputs/newspaper_pulses_space/audio/ with index.json, which the
radio in the browser reads. The text goes through the same cleaning as the
radio in the browser (radio.js, clean()), plus a few period abbreviations; misreadings in the transcriptions are read
as they are, as agreed. Clips are MP3, mono, 32 kbit/s (the encoder makes them 22 kHz).
"""
import argparse
import html
import json
import re
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'outputs' / 'newspaper_pulses_space'
MODELS = Path.home() / '.cache' / 'nns-audio'
SAMPLE = ROOT / 'outputs' / 'audio_sample'
RATE = 24000
# Kokoro's own overall grades for its English voices (VOICES.md in hexgrad/Kokoro-82M); the sample uses the better ones.
GRADES = {'af_heart': 'A', 'af_bella': 'A-', 'af_nicole': 'B-', 'bf_emma': 'B-', 'af_aoede': 'C+', 'af_kore': 'C+', 'af_sarah': 'C+', 'am_fenrir': 'C+',
          'am_michael': 'C+', 'am_puck': 'C+', 'bm_fable': 'C', 'bm_george': 'C', 'bf_isabella': 'C', 'af_alloy': 'C', 'af_nova': 'C'}

# Period abbreviations and forms that a modern voice would stumble on.
ABBR = [(r'\binst\.', 'instant'), (r'\bult\.', 'ultimo'), (r'\bviz\.', 'namely'), (r'\bCapt\.', 'Captain'), (r'\bcapt\.', 'captain'),
        (r'\bEsq\.', 'Esquire'), (r'\bGen\.', 'General'), (r'\bCol\.', 'Colonel'), (r'\bMaj\.', 'Major'), (r'\bLieut\.', 'Lieutenant'),
        (r'\bGov\.', 'Governor'), (r'\bPhilad\.', 'Philadelphia'), (r'\blat\.', 'latitude'), (r'\blong\.', 'longitude'),
        (r'\bJan\.', 'January'), (r'\bFeb\.', 'February'), (r'\bMar\.', 'March'), (r'\bApr\.', 'April'), (r'\bAug\.', 'August'),
        (r'\bSept?\.', 'September'), (r'\bOct\.', 'October'), (r'\bNov\.', 'November'), (r'\bDec\.', 'December'), (r'——+', ', ')]


def clean(text):
    """radio.js clean(), in Python: long s, cut marks, line-end hyphens, spaced capitals, capitals read as words."""
    t = (text or '').replace('ſ', 's')
    t = re.sub(r'&c\.?', 'et cetera', t).replace('&', ' and ')
    t = re.sub(r'(\w)-\s+(\w)', r'\1\2', t)
    t = re.sub(r'\s*(?:…|\.{3,})\s*', ' … ', t)
    t = re.sub(r'[*|•■¶§†‡_~^<>{}\[\]]', ' ', t)
    t = re.sub(r'\b[A-Z](?: [A-Z]){2,}\b', lambda m: m.group(0).replace(' ', ''), t)
    t = re.sub(r"\b([A-Z][A-Z'’-]{2,})\b", lambda m: m.group(1)[0] + m.group(1)[1:].lower(), t)
    for pat, rep in ABBR:
        t = re.sub(pat, rep, t)
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'^(?:…\s*)+', '', t)
    return re.sub(r'(?:\s*…)+$', '', t).strip()


def opening(text, words):
    """The first `words` words, ending at the last full stop (or else comma) inside them, so the voice ends a sentence."""
    w = clean(text).split()
    if len(w) <= words:
        return ' '.join(w)
    for marks in ('.!?', ',;:'):
        for k in range(words, int(words * .55), -1):
            if w[k - 1][-1] in marks:
                return ' '.join(w[:k]).rstrip(',;:') + ('' if marks == '.!?' else '.')
    return ' '.join(w[:words]) + '.'


def lang_of(voice):
    return 'en-gb' if voice.startswith('b') else 'en-us'


def render(kokoro, text, voice, speed=1.0):
    samples, rate = kokoro.create(text, voice=voice, speed=speed, lang=lang_of(voice))
    assert rate == RATE, rate
    a = np.asarray(samples, dtype=np.float32)
    # Trim the model's silence at either end (keep 80 ms), level the clip (RMS -20 dBFS, peaks under -1 dBFS), and
    # fade 10 ms in and out so no clip starts or ends with a click.
    loud = np.flatnonzero(np.abs(a) > .01)
    if loud.size:
        a = a[max(0, loud[0] - int(.08 * RATE)):loud[-1] + int(.08 * RATE)]
    rms = float(np.sqrt(np.mean(a ** 2))) or 1e-6
    a = a * (10 ** (-20 / 20) / rms)
    peak = float(np.max(np.abs(a))) or 1e-6
    if peak > .89:
        a = a * (.89 / peak)
    f = int(.01 * RATE)
    a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
    return a


def mp3(a, kbps=32):
    import lameenc
    enc = lameenc.Encoder()
    enc.set_bit_rate(kbps); enc.set_in_sample_rate(RATE); enc.set_channels(1); enc.set_quality(2)
    pcm = (np.clip(a, -1, 1) * 32767).astype('<i2').tobytes()
    return bytes(enc.encode(pcm) + enc.flush())


def sample_set():
    """About twenty clips: announcers, readers on the Declaration, titles from four years, Peace and Plenty, towns."""
    data = json.loads((SITE / 'data.json').read_text(encoding='utf8'))
    obs = {o['id']: o for r in data['reviewed'] for o in r['observations']}
    decl = next(o for o in obs.values() if 'Declaration by the Representatives' in (o.get('excerpt') or ''))
    peace = next(o for o in obs.values() if 'Peace and Plenty' in (o.get('excerpt') or ''))
    tel = json.loads((SITE / 'telescope.json').read_text(encoding='utf8'))
    titles = []
    for year in (1785, 1793, 1800, 1808):
        best = max((i for i, y in enumerate(tel['year']) if y == year and not tel['kind'][i]), key=lambda i: tel['papers'][i])
        titles.append((year, tel['papers'][best], tel['title'][best]))
    hello = ('This is the Night Sky radio. You are tuned to seventeen seventy-six. '
             'Good morning, Philadelphia! It is Saturday, the sixth of July, seventeen seventy-six. From the Pennsylvania Evening Post.')
    clips = []
    for v in ('af_heart', 'af_bella', 'bf_emma', 'am_michael'):
        clips.append(('Announcer', v, hello, .95))
    for v in ('af_nicole', 'af_sarah', 'af_aoede', 'af_kore', 'am_fenrir', 'am_puck', 'bm_fable', 'bm_george'):
        clips.append(('Reader · the Declaration, Pennsylvania Evening Post, 6 July 1776', v, opening(decl['excerpt'], 62), .95))
    for (year, papers, title), v in zip(titles, ('bf_isabella', 'am_michael', 'af_bella', 'bm_fable')):
        clips.append((f'Title · the most printed matched story of {year} ({papers} papers)', v, opening(title, 22), 1.0))
    for v in ('af_heart', 'am_puck'):
        clips.append(('Reader · Peace and Plenty, 13 October 1797', v, opening(peace['excerpt'], 55), .95))
    for v in ('af_heart', 'bf_emma'):
        clips.append(('Announcer · towns and a year', v, 'Boston. New York. Philadelphia. Baltimore. Richmond. Charleston. Seventeen ninety-seven.', .95))
    return clips


PAGE = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radio voices · sample</title>
<style>:root{color-scheme:dark}body{margin:0;background:#050711;color:#edf2ff;font:15px/1.5 system-ui,"Segoe UI",sans-serif}
main{max-width:980px;margin:auto;padding:28px 20px 60px}h1{font-size:24px;font-weight:500;margin:0 0 6px}h2{font-size:15px;font-weight:600;color:#ffd27a;margin:30px 0 10px;letter-spacing:.02em}
p{color:#a2afc8;margin:0 0 8px}.clip{display:grid;grid-template-columns:130px 1fr;gap:6px 16px;align-items:center;padding:12px 14px;border:1px solid #28334c;border-radius:10px;background:#0b1222;margin:8px 0}
.v{font-weight:600}.v small{display:block;font-weight:400;color:#a2afc8;font-size:12px}audio{width:100%}.t{grid-column:2;font:14px/1.5 Georgia,serif;color:#c7d0e2}
@media(max-width:600px){.clip{grid-template-columns:1fr}.t{grid-column:1}}</style></head><body><main>
<h1>Radio voices · a sample</h1>
<p>Kokoro voices (Apache 2.0), made on this computer. MP3, mono, 22 kHz, 32 kbit/s, as visitors would hear them, before the radio's filters. Words in the transcriptions are read as they are, misreadings included.</p>
<p>Grades are Kokoro's own, from its voice list; only the better voices are here. Choose one announcer and the readers you like (four to eight make good variety); the readers are given to newspapers by a fixed rule, so a paper always keeps its voice.</p>
__CLIPS__
</main></body></html>'''


def sample():
    from kokoro_onnx import Kokoro
    kokoro = Kokoro(str(MODELS / 'kokoro-v1.0.onnx'), str(MODELS / 'voices-v1.0.bin'))
    SAMPLE.mkdir(parents=True, exist_ok=True)
    for old in SAMPLE.glob('*.mp3'):
        old.unlink()   # an earlier sample
    rows, last, spoken, took = [], None, 0.0, 0.0
    for n, (group, voice, text, speed) in enumerate(sample_set(), 1):
        t = time.time(); a = render(kokoro, text, voice, speed); took += time.time() - t; spoken += len(a) / RATE
        name = f'{n:02d}-{voice}.mp3'; (SAMPLE / name).write_bytes(mp3(a))
        if group != last:
            rows.append(f'<h2>{html.escape(group)}</h2>'); last = group
        accent = {'a': 'American', 'b': 'British'}[voice[0]] + (' woman' if voice[1] == 'f' else ' man') + (f' · grade {GRADES[voice]}' if voice in GRADES else '')
        rows.append(f'<div class="clip"><div class="v">{voice}<small>{accent}</small></div><audio controls preload="none" src="{name}"></audio>'
                    f'<div class="t">{html.escape(text)}</div></div>')
        print(f'{n:2d} {voice:12s} {len(a) / RATE:5.1f} s  {group[:60]}', flush=True)
    (SAMPLE / 'index.html').write_text(PAGE.replace('__CLIPS__', '\n'.join(rows)), encoding='utf8')
    print(f'{spoken / 60:.1f} min of speech in {took / 60:.1f} min ({spoken / took:.2f} times real time); {SAMPLE / "index.html"}')


# ---------------------------------------------------------------------------------------------------------------------
# The full set: what to say (manifest), saying it (render, resumable), and the files the site loads (pack).
# The owner chose "the highest rated" (2026-11-10): the announcer af_heart (A), and the next nine as readers. Then, the same
# day, asked for variety rather than mostly women: two American women (af_aoede, af_kore) gave way to two British men
# (bm_george, bm_fable) in the same places of the list, so every other paper keeps its voice and its recordings.
# Readers: four women, five men; two British voices besides bf_emma. The announcer became am_michael at the owner's
# word ("Yes do am Michael"), so a man opens the station; he also reads for the papers the hash gives him. Then the owner
# asked for announcers of both kinds: am_michael ('a:' clips) and af_heart ('b:' clips) take turns, one whole
# introduction each (radio.js joinClips picks the host).
ANNOUNCER = 'am_michael'
HOSTS = [('a', 'am_michael'), ('b', 'af_heart')]
READERS = ['af_bella', 'af_nicole', 'bf_emma', 'bm_george', 'bm_fable', 'af_sarah', 'am_fenrir', 'am_michael', 'am_puck']
CLIPS = MODELS / 'clips'                      # rendered clips, kept outside the repository (rendering is slow)
AUDIO = SITE / 'audio'                        # what the site loads: index.json and the packs
MANIFEST = ROOT / 'work' / 'audio_manifest.json'
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
        'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
ORD = {'one': 'first', 'two': 'second', 'three': 'third', 'five': 'fifth', 'eight': 'eighth', 'nine': 'ninth', 'twelve': 'twelfth'}


def words(n):
    return ONES[n] if n < 20 else TENS[n // 10] + ('-' + ONES[n % 10] if n % 10 else '')


def ordinal(n):   # radio.js ordinal()
    parts = words(n).split('-'); last = parts.pop()
    return '-'.join(parts + [ORD.get(last) or (last[:-1] + 'ieth' if last.endswith('y') else last + 'th')])


def year_words(y):   # radio.js yearWords()
    return words(y // 100) + ' ' + ('hundred' if y % 100 == 0 else 'oh ' + words(y % 100) if y % 100 < 10 else words(y % 100))


def fnv(key):   # FNV-1a over the key (as radio.js once chose its eSpeak voices), so a paper or a town keeps one voice
    h = 2166136261
    for ch in str(key):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def reader_of(key):
    return READERS[fnv(key) % len(READERS)]


FEMALE = ['af_bella', 'af_nicole', 'bf_emma', 'af_sarah']
MALE = ['bm_george', 'bm_fable', 'am_fenrir', 'am_puck']   # am_michael is also a host, so he takes on no new titles


def house_of(town, busy):
    """A town's readers of titles: the voice it had when each town kept one (until 2026-11-10), one of the other kind,
    and for a busy town one more of each, so women and men read about equally often and old recordings mostly stay."""
    h, first = fnv(town), reader_of(town)
    same, other = (FEMALE, MALE) if first[1] == 'f' else (MALE, FEMALE)
    k = h % len(other); out = [first, other[k]]
    if busy:
        out.append(same[(same.index(first) + 1) % len(same)] if first in same else same[h % len(same)])
        out.append(other[(k + 1) % len(other)])
    return out


def town_of(place):   # radio.js town()
    return str(place or '').split(',')[0].replace('-', ' ').strip()


def paper_name(name):   # radio.js paperName() and the()
    n = re.sub(r'\s*·\s*sn\w+$', '', str(name or '')).strip()
    return re.sub(r'^the', 'The', n, flags=re.I) if re.match(r'the\s', n, re.I) else 'the ' + n


def manifest():
    data = json.loads((SITE / 'data.json').read_text(encoding='utf8'))
    tel = json.loads((SITE / 'telescope.json').read_text(encoding='utf8'))
    yi = json.loads((SITE / 'years' / 'index.json').read_text(encoding='utf8'))
    boot = json.loads(re.search(r'<script type="application/json" id="boot">(.*?)</script>', (SITE / 'telescope.html').read_text(encoding='utf8'), re.S).group(1))
    entries, seen = [], set()
    def add(cid, tier, pack, voice, text, speed):
        text = re.sub(r'\s+', ' ', text or '').strip()
        if text and cid not in seen:
            seen.add(cid); entries.append({'id': cid, 'tier': tier, 'pack': pack, 'voice': voice, 'speed': speed, 'text': text})
    # The announcers: the station, towns (plain and greeted), the parts of a date, and each newspaper's name, once for
    # each host ('a:' am_michael, 'b:' af_heart).
    towns = sorted({t['name'] for t in boot['towns']} | {town_of(p['place']) for p in yi['papers']} - {''})
    for h, host in HOSTS:
        add(f'{h}:station', 0, 'a', host, 'This is the Night Sky radio.', .95)
        add(f'{h}:tuned', 0, 'a', host, 'You are tuned to', .95)
        for t in towns:
            add(f'{h}:town:{t}', 0, 'a', host, f'{t}.', .95)
            add(f'{h}:hello:{t}', 0, 'a', host, f'Good morning, {t}!', .95)
        for y in range(1770, 1811):
            add(f'{h}:year:{y}', 0, 'a', host, year_words(y) + '.', .95)
        for m, name in enumerate(MONTHS, 1):
            add(f'{h}:month:{m}', 0, 'a', host, name, .95)
        for d in range(1, 32):
            add(f'{h}:day:{d}', 0, 'a', host, f'The {ordinal(d)} of', .95)
        for w in WEEKDAYS:
            add(f'{h}:weekday:{w}', 0, 'a', host, f'It is {w},', .95)
        for p in yi['papers']:
            add(f'{h}:paper:{p["lccn"]}', 0, 'a', host, f'From {paper_name(p["name"])}.', .95)
    # Clear stations: every reviewed passage, whole, in its newspaper's reader voice; one pack per reviewed story.
    for r in data['reviewed']:
        obs = {o['id']: o for o in r['observations']}; packed = set()
        for st in r['stories']:
            slug = re.sub(r'[^a-z0-9]+', '-', st['id'].split(':')[-1].lower()).strip('-')
            for oid in st['members']:
                if oid in obs and oid not in packed:
                    packed.add(oid); add('p:' + oid, 1, f'r/{r["year"]}-{slug}', reader_of(obs[oid]['node']), clean(obs[oid]['excerpt']), .95)
        for oid, o in obs.items():
            if oid not in packed:
                add('p:' + oid, 1, f'r/{r["year"]}-other', reader_of(o['node']), clean(o['excerpt']), .95)
    # Regional stations: the titles of every matched story printed in four or more newspapers, and of the forty most widely
    # printed of each year in three or more. Most widely printed first (the render follows this order). A title is read
    # by one of its first-printing town's house of readers (house_of), chosen by the story's id.
    town_at = {(t['lat'], t['lon']): t['name'] for t in boot['towns']}
    chosen = []
    for y in range(1770, 1811):
        idx = sorted((i for i, yy in enumerate(tel['year']) if yy == y and not tel['kind'][i] and tel['papers'][i] >= 3), key=lambda i: (-tel['papers'][i], tel['first'][i]))
        chosen += [i for k, i in enumerate(idx) if k < 40 or tel['papers'][i] >= 4]
    town_of_star = {i: town_at.get((tel['flat'][i], tel['flon'][i]), tel['id'][i]) for i in chosen}
    load = {}
    for i in chosen:
        load[town_of_star[i]] = load.get(town_of_star[i], 0) + 1
    busy = {t for t, n in load.items() if n >= 250}
    for i in sorted(chosen, key=lambda i: (-tel['papers'][i], tel['first'][i])):
        town = town_of_star[i]; readers = house_of(town, town in busy)
        add('t:' + tel['id'][i], 2, f"t/{tel['year'][i]}", readers[fnv(tel['id'][i]) % len(readers)], opening(tel['title'][i], 24), 1.0)
    MANIFEST.write_text(json.dumps({'announcers': [h for _, h in HOSTS], 'readers': READERS, 'entries': entries}, ensure_ascii=False, indent=0), encoding='utf8')
    tiers = {}
    for e in entries:
        tiers.setdefault(e['tier'], [0, 0]); tiers[e['tier']][0] += 1; tiers[e['tier']][1] += len(e['text'].split())
    print({k: f'{v[0]} clips, {v[1]} words, about {v[1] / 150 / 60:.1f} h' for k, v in sorted(tiers.items())}, '->', MANIFEST)


def clip_key(e):
    import hashlib
    return hashlib.sha1(f"{e['voice']}|{e['speed']}|{e['text']}".encode('utf8')).hexdigest()[:20]


def render_all(limit=None, shard=None):
    """Render every clip of the manifest that is not made yet. Safe to stop and start again: made clips are kept.
    shard 'k/n' takes every n-th entry from the k-th (0-based), so n renders can share one machine (one renderer uses
    about two cores). A clip counts as made once its .json is written (after the .mp3), and each render checks again
    just before making one, so shards and restarts never make a clip twice."""
    from kokoro_onnx import Kokoro
    entries = json.loads(MANIFEST.read_text(encoding='utf8'))['entries']
    if shard:
        k, m = map(int, shard.split('/')); entries = entries[k::m]
    CLIPS.mkdir(parents=True, exist_ok=True)
    made = lambda e: (CLIPS / (clip_key(e) + '.json')).exists()
    todo = [e for e in entries if not made(e)]
    print(f'{len(entries)} clips, {len(todo)} to make', flush=True)
    kokoro = Kokoro(str(MODELS / 'kokoro-v1.0.onnx'), str(MODELS / 'voices-v1.0.bin'))
    t0, spoken = time.time(), 0.0
    for n, e in enumerate(todo[:limit] if limit else todo, 1):
        if made(e):
            continue
        try:
            a = render(kokoro, e['text'], e['voice'], e['speed'])
        except Exception as err:   # one bad text must not stop the night's work
            print(f'  failed {e["id"]}: {err}', flush=True); continue
        k = clip_key(e)
        (CLIPS / (k + '.mp3')).write_bytes(mp3(a, 24 if e['tier'] == 2 else 32))
        (CLIPS / (k + '.json')).write_text(json.dumps({'seconds': round(len(a) / RATE, 3)}), encoding='utf8')
        spoken += len(a) / RATE
        if n % 25 == 0 or n == len(todo):
            el = time.time() - t0
            print(f'{n}/{len(todo)} made; {spoken / 60:.1f} min of speech in {el / 60:.1f} min; tier {e["tier"]}', flush=True)


def pack():
    """Join the made clips into packs (each clip a whole MP3, so a byte range of a pack plays alone) and write the index."""
    entries = json.loads(MANIFEST.read_text(encoding='utf8'))['entries']
    blobs, index, missing = {}, {}, 0
    for e in entries:
        f = CLIPS / (clip_key(e) + '.mp3')
        if not f.exists():
            missing += 1; continue
        b = f.read_bytes(); buf = blobs.setdefault(e['pack'], bytearray()); start = len(buf); buf += b
        index[e['id']] = [e['pack'], start, len(buf), json.loads((CLIPS / (clip_key(e) + '.json')).read_text(encoding='utf8'))['seconds'], e['tier']]
    AUDIO.mkdir(parents=True, exist_ok=True)
    names = sorted(blobs)
    for name in names:
        out = AUDIO / (name + '.mp3'); out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(bytes(blobs[name]))
    packs = {name: k for k, name in enumerate(names)}
    clips = {cid: [packs[v[0]], v[1], v[2], v[3], v[4]] for cid, v in index.items()}
    # A reviewed story speaks through its first printing: 's:<story id>' -> that printing's passage.
    data = json.loads((SITE / 'data.json').read_text(encoding='utf8')); alias = {}
    for r in data['reviewed']:
        date = {o['id']: o['date'] for o in r['observations']}
        for st in r['stories']:
            have = sorted((date[m], m) for m in st['members'] if m in date and 'p:' + m in clips)
            if have:
                alias['s:' + st['id']] = 'p:' + have[0][1]
    (AUDIO / 'index.json').write_text(json.dumps({'v': 1, 'packs': [n + '.mp3' for n in names], 'clips': clips, 'alias': alias}, separators=(',', ':')), encoding='utf8')
    size = sum(len(b) for b in blobs.values())
    print(f'{len(clips)} clips in {len(names)} packs, {size / 1e6:.1f} MB; {missing} not made yet -> {AUDIO}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('task', choices=['sample', 'manifest', 'render', 'pack'])
    ap.add_argument('--limit', type=int, help='render: make at most this many clips (a trial)')
    ap.add_argument('--shard', help="render: 'k/n', every n-th clip from the k-th, to run n renders at once")
    args = ap.parse_args()
    {'sample': sample, 'manifest': manifest, 'render': lambda: render_all(args.limit, args.shard), 'pack': pack}[args.task]()
