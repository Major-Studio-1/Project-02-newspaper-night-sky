"""Supplementary phrase search for the 8 shortlisted 1797 stories (both OCR fields, all 1,587 pages).

Finds printings the reuse matcher missed (damaged OCR, same-paper repeats, reworded versions).
Output: outputs/story_discovery_1797/phrase_hits.json. Hits are candidates for reading.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT/'outputs/pilot_expansion_2026-11-05/search_pages.json'
OUT = ROOT/'outputs/story_discovery_1797/phrase_hits.json'

PATTERNS = {
    'tenerife': [r'christians?\W{0,3}haven', r'patrick\s+corran', r'teneriff?e?.{0,400}santa\s+cruz', r'santa\s+cruz.{0,400}teneriff?e?'],
    'adams_speech': [r'personal\s+inconveniences\s+to\s+the\s+members', r'convention\s+of\s+congress\s+indispensable'],
    'adams_farewell': [r'excused\s+from\s+further\s+attendance', r'centre\s+of\s+our\s+union', r'on\s+his\s+retir\w+\s+from\s+the\s+senate'],
    'camperdown': [r'rose\s+cutter', r'adam\s+duncan', r'admiral\s+duncan', r'de\s+winter'],
    'algerine_battle': [r'most\s+terrible\s+battle', r'algerine\s+cruiser', r'two\s+sicilies.{0,300}algerine|algerine.{0,300}two\s+sicilies'],
    'blount': [r'sitgreaves', r'blount.{0,300}carey|carey.{0,300}blount', r'william\s+blount|wm\.?\s+blount'],
    'brothers_kennard': [r'kennard'],
    'brown_fire': [r'printer\s+of\s+the\s+philadelphia\s+gazette', r'family\s+of\s+mr\.?\s+brown', r'mr\.?\s+(?:andrew\s+)?brown.{0,80}(?:fire|printer|smoke)'],
}


def norm(t):
    t = (t or '').replace('ſ', 's')
    t = re.sub(r'(?<=\w)-\s+(?=\w)', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def main(patterns=None, out=None):
    # Optional: a JSON file of {story: [patterns]} and an output path, for later search rounds.
    global PATTERNS, OUT
    if patterns:
        PATTERNS = json.loads(Path(patterns).read_text(encoding='utf8'))
        OUT = Path(out)
    pages = json.loads(PAGES.read_text(encoding='utf8'))
    rx = {story: [re.compile(p, re.I | re.S) for p in pats] for story, pats in PATTERNS.items()}
    hits = {story: [] for story in PATTERNS}
    for p in pages:
        texts = {field: norm(p['texts'].get(field)) for field in ('RevX_OCR_text', 'ca_ocr_text')}  # clean once per page
        for story, regs in rx.items():
            found = []
            for field in ('RevX_OCR_text', 'ca_ocr_text'):
                t = texts[field]
                for r in regs:
                    m = r.search(t)
                    if m:
                        found.append({'field': field, 'pattern': r.pattern, 'pos': m.start(), 'snippet': t[max(0, m.start()-120):m.start()+260]})
            if found:
                hits[story].append({'key': p['key'], 'date': p['date'], 'paper': p['paper'], 'lccn': p['lccn'], 'page': p['page'], 'hits': found})
    OUT.write_text(json.dumps({'patterns': PATTERNS, 'pages_searched': len(pages), 'hits': hits}, ensure_ascii=False, indent=2), encoding='utf8')
    for story, rows in hits.items():
        print(story, len(rows), 'pages')


if __name__ == '__main__':
    import sys
    main(*sys.argv[1:3])
