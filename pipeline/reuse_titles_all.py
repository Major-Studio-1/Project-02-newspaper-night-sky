"""Better titles for automatic matched stories (reuse families), read from the text printed just before them.

A matched story's shared wording often starts a few words into a sentence, and its heading or dateline is
printed just above it ("NEW-YORK, August 8.", "HOUSE OF REPRESENTATIVES.", "PORTUGAL.--"). For every printed
appearance this script reads the selected transcription in the pinned shard and finds:
- the dateline (place, month, day) at the start of the item, if any;
- otherwise a short heading line directly above the item (mostly capitals);
- the opening words of the item: the text from the start of its paragraph (after any dateline) to the shared
  wording, when that is short, so the title begins where the item begins.
The family title takes the heading or dateline that most of its printings agree on, then the opening words of
its earliest printing. Everything is automatic and stays labelled "not checked".

Usage (project root, Python 3.12):
    python work/reuse_titles_all.py sample 1776,1797,1808 300   # measure on a sample, print examples
    python work/reuse_titles_all.py all                           # all families -> outputs/story_discovery_all/titles.json
"""
from pathlib import Path
import collections
import json
import random
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'python_packages'))
import pyarrow.parquet as pq

TOKEN = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")
MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b\.?"
NOT_PLACES = {'extract', 'copy', 'from', 'letter', 'the', 'in', 'on', 'at', 'dated', 'after', 'since', 'last', 'by', 'of'}
WEEKDAYS = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
# "NEW-YORK, August 8."  "LONDON May 3."  "Philadelphia, 19th June, 1797."  "CORK, May 9."
DATELINE = re.compile(r"^\s*(?:\(?From [^)]{3,40}\)?\s*)?([A-Z][A-Za-z'\-]+(?:[ .]+[A-Z][A-Za-z'\-]+){0,2})[,.]?\s+(?:\d{1,2}(?:st|nd|rd|th)?,?\s+)?" + MONTH + r"\s*\d{0,2}")
OPEN_MAX_WORDS = 30   # back up to the item's start only if it is this close to the shared wording
WINDOW = 600          # characters read before the shared wording


def clean(raw):
    raw = unicodedata.normalize('NFKC', raw or '').replace('ſ', 's')
    return re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', raw)


def caps_ratio(s):
    letters = [c for c in s if c.isalpha()]
    return sum(c.isupper() for c in letters) / len(letters) if letters else 0


def place_of(dateline_match):
    place = dateline_match.group(1).strip(' .,')
    if place.lower() in WEEKDAYS or len(place) < 3 or place.split()[0].lower() in NOT_PLACES:
        return None
    return ' '.join(w if w.isupper() is False else w.title() for w in place.split()).replace('New York', 'New-York')


def analyse(raw, start_char):
    """Heading, dateline place and item opening for the shared wording starting at start_char."""
    before = raw[max(0, start_char - WINDOW):start_char]
    lines = before.split('\n')
    own = lines[-1]                      # text on the same line, before the shared wording
    above = [l.strip() for l in lines[:-1] if l.strip()]
    found = {'place': None, 'heading': None, 'opening': None}
    m = DATELINE.match(own)
    if m:
        found['place'] = place_of(m)
        own_rest = own[m.end():].lstrip(' .,:;—-')
    else:
        own_rest = own
        if above:
            m2 = DATELINE.match(above[-1])
            if m2 and len(above[-1].split()) <= 8:
                found['place'] = place_of(m2)
                above = above[:-1]
    # A short, mostly capital line directly above the item is its heading ("HOUSE OF REPRESENTATIVES.", "PORTUGAL.").
    if above:
        h = above[-1].strip(' .—-:')
        if 1 <= len(h.split()) <= 8 and len(h) <= 60 and caps_ratio(h) >= .6 and not re.search(r'\d{4}', h):
            found['heading'] = re.sub(r'\s+', ' ', h)
    # Same-line headings such as "PORTUGAL.—The fate of ..." or "Capt. Aydelott from ..." before the shared wording.
    inline = re.match(r"^\s*([A-Z][A-Z .'\-]{3,40})[.:]?\s*[—-]", own_rest)
    if inline and not found['heading']:
        found['heading'] = inline.group(1).strip(' .')
        own_rest = own_rest[inline.end():]
    words = own_rest.split()
    if 0 < len(words) <= OPEN_MAX_WORDS:
        found['opening'] = ' '.join(words)
    elif not words:
        found['opening'] = ''
    return found


def norm(s):
    return re.sub(r'[^a-z]', '', (s or '').lower())


def title_for(family, found_list):
    """found_list: analyse() results for the family's appearances, earliest first."""
    places = collections.Counter(norm(f['place']) for f in found_list if f['place'])
    heads = collections.Counter(norm(f['heading']) for f in found_list if f['heading'])
    pick = lambda key, counter: next((f[key] for f in found_list if f[key] and norm(f[key]) == counter.most_common(1)[0][0]), None) if counter else None
    place, heading = pick('place', places), pick('heading', heads)
    first = found_list[0] if found_list else {'opening': None}
    words = family['label'].rstrip(' …').split()
    opening = first['opening']
    text = ' '.join(((opening + ' ') if opening else '').split() + words)
    text = ' '.join(text.split()[:14]) + ' …'
    support = places.most_common(1)[0][1] if places else 0
    # Headings proved noisy (section names, signatures of the item above), so they are recorded but not shown.
    # A place is shown only when 2+ printings carry the same dateline, and not if the title already starts with it.
    show_place = place if support >= 2 and norm(place) not in norm(' '.join(text.split()[:4])) else None
    source = ('place + ' if show_place else '') + ('item opening' if opening is not None else 'shared words')
    return {'title': (show_place + ' · ' if show_place else '') + text, 'title_source': source, 'title_support': support,
            'heading': heading, 'place': place, 'starts_at_item': opening is not None}


def run(years=None, sample=None):
    rel = json.loads((ROOT.parent/'outputs/data_foundation/CURRENT.json').read_text())['path']
    derived = ROOT.parent/'outputs/data_foundation'/rel/'derived'
    fams = pq.read_table(derived/'reuse_families.parquet').to_pylist()
    if years:
        fams = [f for f in fams if f['first_date'][:4] in years and f['newspapers'] >= 3 and not f['long_running']]
    if sample:
        random.seed(11); fams = random.sample(fams, min(sample, len(fams)))
    want = {f['family_id'] for f in fams}
    apps = [a for a in pq.read_table(derived/'reuse_family_appearances.parquet', columns=['family_id', 'seq', 'page_id', 'span_start', 'transcription']).to_pylist()
            if a['family_id'] in want]
    audit = {'page:' + r['key'].replace('|', ':'): (r['file'], r['file_row']) for r in pq.read_table(ROOT/'page_audit.parquet', columns=['key', 'file', 'file_row']).to_pylist()}
    by_shard = collections.defaultdict(lambda: collections.defaultdict(list))
    for a in apps:
        shard, row = audit[a['page_id']]; by_shard[shard][row].append(a)
    found = {}
    for shard, rows in sorted(by_shard.items()):
        pf = pq.ParquetFile(ROOT/'data'/shard); offset = 0
        for g in range(pf.num_row_groups):
            cnt = pf.metadata.row_group(g).num_rows
            hit = [rw for rw in rows if offset <= rw < offset + cnt]
            if hit:
                tb = pf.read_row_group(g, columns=['RevX_OCR_text', 'ca_ocr_text'])
                for rw in hit:
                    cache = {}
                    for a in rows[rw]:
                        field = 'RevX_OCR_text' if a['transcription'] == 'RevX' else 'ca_ocr_text'
                        if field not in cache:
                            raw = clean(tb[field][rw - offset].as_py())
                            cache[field] = (raw, [m.start() for m in TOKEN.finditer(raw)])
                        raw, starts = cache[field]
                        s = starts[a['span_start']] if a['span_start'] < len(starts) else len(raw)
                        found[a['family_id'], a['seq']] = analyse(raw, s)
            offset += cnt
        print('read', shard, flush=True)
    out = {}
    for f in fams:
        lst = [found[f['family_id'], i] for i in range(f['appearances']) if (f['family_id'], i) in found]
        out[f['family_id']] = title_for(f, lst)
    return fams, out


if __name__ == '__main__':
    if sys.argv[1] == 'sample':
        fams, out = run(set(sys.argv[2].split(',')), int(sys.argv[3]))
        src = collections.Counter(v['title_source'] for v in out.values())
        print('families', len(out), dict(src))
        print('starts at the item (opening found):', sum(v['starts_at_item'] for v in out.values()))
        print('heading or place agreed by 2+ printings:', sum(v['title_support'] >= 2 for v in out.values()))
        for f in fams[:40]:
            print('-', f['family_id'], '| OLD:', f['label']); print('  NEW:', out[f['family_id']]['title'], f"[{out[f['family_id']]['title_source']}, {out[f['family_id']]['title_support']}]")
    else:
        fams, out = run()
        dest = ROOT.parent/'outputs/story_discovery_all/titles.json'
        dest.write_text(json.dumps(out, ensure_ascii=False), encoding='utf8')
        print('wrote', dest, len(out), dict(collections.Counter(v['title_source'] for v in out.values())))
