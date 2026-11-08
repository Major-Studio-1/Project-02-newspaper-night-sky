"""One printing per matched story and page (data release v0.6.0).

The all-years matcher (run:reuse-all-v1) could list the same page more than once for one story. Overlapping matches
with different partner pages each became a row, and so did separate blocks of the page that join the same story:
neighbouring items of a news digest, a continuing report, or a passage repeated on the page. v0.5.2 has 179,966 rows
for 163,926 distinct pages (3,945 stories list a page more than once). A printing is one page, so merge() keeps one
row per (family_id, page_id):

- seq: the smallest seq of the page's rows. Rows of one page have consecutive seqs, so ids built from seq stay
  stable, but seq is no longer contiguous within a story;
- blocks_json: the page's matched spans, with overlapping or touching spans (a gap of TOUCH words or less) joined,
  in page order;
- span_start, span_end: the first block on the page; excerpt: from the page's earliest row;
- segments: how many rows were merged; merged_seqs_json: their seqs.

merge() is deterministic and idempotent: rows that already carry blocks_json keep their blocks.
"""
import json

TOUCH = 5


def merge(rows):
    by_page = {}
    for r in rows:
        by_page.setdefault((r['family_id'], r['page_id']), []).append(r)
    out = []
    for rs in by_page.values():
        spans, seqs, segments = [], [], 0
        for r in rs:
            spans += json.loads(r['blocks_json']) if r.get('blocks_json') else [[r['span_start'], r['span_end']]]
            seqs += json.loads(r['merged_seqs_json']) if r.get('merged_seqs_json') else [r['seq']]
            segments += r.get('segments') or 1
        blocks = []
        for s, e in sorted(spans):
            if blocks and s <= blocks[-1][1] + TOUCH:
                blocks[-1][1] = max(blocks[-1][1], e)
            else:
                blocks.append([s, e])
        earliest = min(rs, key=lambda r: (r['span_start'], r['seq']))
        row = {k: v for k, v in min(rs, key=lambda r: r['seq']).items() if k not in ('blocks_json', 'merged_seqs_json', 'segments')}
        row.update(seq=min(seqs), span_start=blocks[0][0], span_end=blocks[0][1], excerpt=earliest['excerpt'],
                   segments=segments, merged_seqs_json=json.dumps(sorted(seqs)), blocks_json=json.dumps(blocks))
        out.append(row)
    out.sort(key=lambda r: (r['family_id'], r['seq']))
    return out
