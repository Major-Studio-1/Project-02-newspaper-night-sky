"""Phrase search for chosen stories over one year's pages, in both transcriptions (RevX and CA).

Year-independent form of story_phrase_search_1797.py. It finds printings the reuse matcher and the
item finder miss: damaged OCR, abridged or reworded versions, repeats in the same paper.
Each pattern is a plain phrase or, prefixed with 're:', a regular expression. Plain phrases
tolerate older OCR: any run of spaces or punctuation between words, and s may be read as f or ſ.
Hits are candidates for reading, not admissions. Run from the project root with Python 3.12:

    python work/story_phrase_search.py <search_pages.json> <patterns.json> <hits.json>
"""
from pathlib import Path
import json
import re
import sys

FIELDS = ('RevX_OCR_text', 'ca_ocr_text')


def compile_pattern(p):
    if p.startswith('re:'):
        return re.compile(p[3:], re.I | re.S)
    words = re.findall(r"[A-Za-z0-9]+", p)
    tolerant = [''.join('[sfſ]' if ch in 'sS' else re.escape(ch) for ch in w) for w in words]
    return re.compile(r'\W+'.join(tolerant), re.I)


def main(pages_path, patterns_path, out_path):
    pages = json.loads(Path(pages_path).read_text(encoding='utf8'))
    patterns = json.loads(Path(patterns_path).read_text(encoding='utf8'))
    rx = {story: [(p, compile_pattern(p)) for p in pats] for story, pats in patterns.items()}
    hits = {story: [] for story in patterns}
    for page in pages:
        for story, regs in rx.items():
            found = []
            for field in FIELDS:
                t = page['texts'].get(field) or ''
                for raw, r in regs:
                    m = r.search(t)
                    if m:
                        found.append({'field': field, 'pattern': raw, 'pos': m.start(), 'snippet': t[max(0, m.start()-160):m.start()+240]})
            if found:
                hits[story].append({'key': page['key'], 'date': page['date'], 'paper': page['paper'], 'lccn': page['lccn'], 'page': page['page'], 'hits': found})
    Path(out_path).write_text(json.dumps({'patterns': patterns, 'pages_searched': len(pages), 'hits': hits}, ensure_ascii=False, indent=2), encoding='utf8')
    for story, rows in hits.items():
        print(f'{story:40} {len(rows):3} pages')


if __name__ == '__main__':
    main(*sys.argv[1:4])
