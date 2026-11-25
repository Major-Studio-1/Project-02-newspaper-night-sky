"""Threads (stories.html, called Stories until 24 November 2026): the storylines of the ledger work/stories.json, checked
and rendered. On the site each storyline is a thread (the owner, 24 November 2026): one affair followed through several
reviewed stories, the stars of the Telescope, in the order the papers printed them; a reviewed story is told in one piece
or in several (a parent's sub-stories), each piece a printed text with its own card.

A storyline puts the printed pieces of one affair in the order the papers printed them. The ledger is written for each affair, not generated;
this module checks it against the reviewed data of the site build (from the current release) and the scan verdicts
(outputs/story_discovery_YEAR/scan_verdicts/), then renders the page. The checks:
  - each piece is a reviewed group of the storyline's year, and the pieces are exactly the sub-stories of its parents
    ('parents') and its single stories ('stories', stories with no parent, told whole); every piece is told in one act;
  - each piece's quoted printing is one of its printings, located on its scan, with a transcription the scan check found
    faithful, and every crop shown is one of that printing's evidence crops;
  - every phrase in single curly quotes is printed text, or the scan check's record of it: in a 'says' line, an act's
    paragraph or the title, it appears in the group's definition, a printing's excerpt or a scan verdict of that piece
    (or of the act's pieces); in a setting note or a note on the machine's reading, it appears in that printing's
    verdict, review note or excerpt;
  - numbers and dates in the paragraphs come from the data ({A.papers} and the like, filled here);
  - the towns of 'reach' are towns of the printing papers, and every Pulses door opens a reviewed group of its year.
Used by work/build_pulse_explorer.py: check() before the pages boot (links() gives Pulses and the telescope their
'Read the thread' links), render() for the page."""
import glob, html, json, math, re, unicodedata
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

esc = html.escape
D = date.fromisoformat
WORDS = 'zero one two three four five six seven eight nine ten eleven twelve'.split()
SKY_EPOCH = date(1770, 1, 1)     # day 0 of the Telescope's stars ('first')


def words(n):
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


def day(d, year=False):
    d = D(d) if isinstance(d, str) else d
    return f'{d.day} {d:%B}' + (f' {d.year}' if year else '')


def span(a, b, year=False):
    a, b = D(a), D(b)
    if a == b:
        return day(a, year)
    if a.year != b.year:
        return f'{day(a, True)} – {day(b, True)}'
    if (a.year, a.month) == (b.year, b.month):
        return f'{a.day}–{b.day} {b:%B}' + (f' {b.year}' if year else '')
    return f'{day(a)} – {day(b, year)}'


def norm(s):
    """Letters and digits only, for matching a quoted phrase against its sources ('ſ' is 's'; accents and markup go)."""
    s = unicodedata.normalize('NFKD', re.sub(r'<[^>]+>', ' ', s).replace('ſ', 's'))
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return ' ' + re.sub(r'[^0-9a-z]+', ' ', s).strip() + ' '


QUOTE = re.compile(r'‘([^‘’]+)’')


def quoted(text):
    """The phrases in single curly quotes, split at '…' (each part must be found on its own)."""
    return [part for q in QUOTE.findall(text) for part in q.split('…') if norm(part).strip()]


def verdict_text(v):
    return ' '.join((v or {}).get('printed_differences', []) + (v or {}).get('transcription_errors', []) + [(v or {}).get('finding', '')])


def verdicts(year, root):
    """The scan verdicts of a reviewed year: batches, then hand boxes, then rechecks (sorted by name; a later file wins)."""
    out = {}
    for f in sorted(glob.glob(str(Path(root) / f'outputs/story_discovery_{year}/scan_verdicts/*.json'))):
        for v in json.loads(Path(f).read_text(encoding='utf8')):
            if isinstance(v, dict) and 'id' in v:
                out[v['id']] = v
    return out


def check(ledger, reviewed, children, root):
    """Check every storyline of the ledger; return them with their printings, papers and filled paragraphs.
    reviewed: year -> the build's reviewed data (as in data.json); children: year -> {parent: [sub-stories]} (REVIEWED)."""
    lines, ids = [], set()
    for s in ledger['storylines']:
        sid, y = s['id'], s['year']
        assert re.fullmatch(r'[a-z0-9-]+', sid) and sid not in ids, f'{sid}: a storyline needs a unique id'
        ids.add(sid)
        years = s.get('years') or [y]          # a thread may cross years ('years'; 24 November 2026); 'year' is its first
        assert years[0] == y and years == sorted(set(years)), f'{sid}: "years" runs from its "year", in order'
        multi = len(years) > 1
        obs, groups, papers, V = {}, {}, {}, {}
        for yy in years:      # each printing and group keeps the reviewed year it was read in
            r = reviewed[yy]
            obs.update({o['legacy_id']: {**o, '_year': yy} for o in r['observations']})
            groups.update({g['id']: {**g, '_year': yy} for g in r['groups']})
            papers.update({p['lccn']: p for p in r['newspapers']})
            Vy = verdicts(yy, root)
            assert Vy, f'{sid}: no scan verdicts for {yy} (outputs/story_discovery_{yy}/scan_verdicts/)'
            V.update(Vy)

        def own(oid):   # what the scan check recorded about one printing, and its text
            o = obs[oid]
            return [norm(verdict_text(V.get(oid))), norm(o.get('note', '')), norm(o.get('summary', '')), norm(o['excerpt'])]

        def crop_ok(oid, crop, where):
            assert f'assets/story_discovery_{obs[oid]["_year"]}__evidence__{crop}.jpg' in obs[oid]['scans'], f'{sid} {where}: {crop} is not an evidence crop of {oid}'

        def phrases_in(text, sources, where):
            for q in quoted(text):
                assert any(norm(q) in src for src in sources), f'{sid} {where}: ‘{q}’ is not in its sources'

        by = {}
        for p in s['pieces']:
            k, g = p['key'], groups.get(p['group'])
            assert re.fullmatch(r'[A-Z]', k) and k not in by, f'{sid}: piece keys are single capitals, once each ({k})'
            assert g, f'{sid} {k}: {p["group"]} is not a reviewed group of {", ".join(map(str, years))}'
            prints = sorted((obs[m['id'].split(':')[-1]] for m in g['members']), key=lambda o: (o['date'], o['legacy_id']))
            pids = {o['legacy_id'] for o in prints}
            q, v = p['quote'], V.get(p['quote'])
            assert q in pids, f'{sid} {k}: the quoted printing {q} is not a printing of {p["group"]}'
            assert v and v.get('located') == 'yes' and v.get('transcription') == 'faithful', f'{sid} {k}: {q} is not a located printing with a faithful transcription'
            crop_ok(q, p.get('crop') or q, k)
            if p.get('second'):
                assert p['second']['printing'] in pids, f'{sid} {k}: the second scan is not a printing of the piece'
                crop_ok(p['second']['printing'], p['second']['crop'], k)
            for oid, note in p['set']:
                assert oid in pids, f'{sid} {k}: setting note on {oid}, which is not a printing of the piece'
                phrases_in(note, own(oid), f'{k} setting note on {oid}')
            sources = [norm(g['definition'])] + [src for o in prints for src in (norm(o['excerpt']), norm(verdict_text(V.get(o['legacy_id']))))]
            phrases_in(p['says'], sources, f'{k} says')
            by[k] = {**p, 'prints': prints, 'label': g['label'], 'sources': sources,
                     'papers': len({o['node'] for o in prints})}
        singles = s.get('stories', [])
        for st in singles:
            assert st.split(':', 1)[1] not in children[groups[st]['_year']], f'{sid}: {st} has sub-stories; name it under parents'
        kids = {'group:' + c for par in s['parents'] for c in children[groups[par]['_year']].get(par.split(':', 1)[1], [])} | set(singles)
        assert kids == {p['group'] for p in by.values()}, f'{sid}: the pieces must be the sub-stories of its parents and its single stories'
        told = [k for a in s['acts'] for k in a['pieces']]
        assert sorted(told) == sorted(by), f'{sid}: every piece is told in one act ({"".join(told)})'

        def fill(text):
            def one(m):
                assert m.group(1) in by, f'{sid}: {m.group(0)} names no piece'
                p, what = by[m.group(1)], m.group(2)
                first, last = p['prints'][0], p['prints'][-1]
                d = D(first['date'])
                known = {'first': lambda: day(first['date'], multi), 'last': lambda: day(last['date'], multi), 'signed': lambda: day(p['signed'], multi),
                         'firstwd': lambda: f'{d:%A} {d.day} {d:%B}', 'papers': lambda: words(p['papers']), 'more': lambda: words(p['papers'] - 1),
                         'weeks': lambda: words((d - D(p['signed'])).days // 7), 'firstpaper': lambda: esc(papers[first['node']]['name'])}
                assert what in known, f'{sid}: unknown placeholder {m.group(0)}'
                return known[what]()
            out = re.sub(r'\{([A-Z])\.(\w+)\}', one, text)
            assert '{' not in out, f'{sid}: an unknown placeholder in ‘{text[:60]}…’'
            return out

        acts = []
        for a in s['acts']:
            ps = [by[k] for k in a['pieces']]
            text = fill(a['text'])
            phrases_in(text, [src for p in ps for src in p['sources']], f'act {a["num"]}')
            m = a.get('machine')
            if m:
                assert any(m['printing'] in {o['legacy_id'] for o in p['prints']} for p in ps), f'{sid} act {a["num"]}: the machine note is not on a printing of the act'
                phrases_in(m['text'], own(m['printing']), f'act {a["num"]} machine note')
                if m.get('crop'):
                    crop_ok(m['printing'], m['crop'], f'act {a["num"]}')
            acts.append({**a, 'text': text, 'ps': ps})
        phrases_in(s['title'], [src for p in by.values() for src in p['sources']], 'title')
        every = sorted({o['legacy_id']: o for p in by.values() for o in p['prints']}.values(), key=lambda o: (o['date'], o['legacy_id']))
        places = {papers[o['node']]['place'] for o in every}
        for town in s.get('reach', []):
            assert any(pl.startswith(town) for pl in places), f'{sid}: {town} is not a town of the printing papers'
        for _, href in [d for a in s['acts'] for d in a.get('doors', [])] + s.get('after', {}).get('doors', []):
            u = urlsplit(href)
            assert u.path in ('pulses.html', 'telescope.html', 'radio.html', 'findings.html') and not u.netloc, f'{sid}: door {href} leaves the site'
            qs = parse_qs(u.query)
            if u.path == 'pulses.html' and 'focus' in qs:
                yy = int(qs['year'][0])
                assert qs['focus'][0] in {g['id'] for g in reviewed[yy]['groups']}, f'{sid}: door {href} opens no reviewed group of {yy}'
            if u.path == 'telescope.html' and 'story' in qs:
                assert qs['story'][0] in groups, f'{sid}: door {href} opens no reviewed story of {y}'
        kids_of = {par: {'group:' + c for c in children[groups[par]['_year']].get(par.split(':', 1)[1], [])} for par in s['parents']}
        parent_of = {'group:' + c: 'group:' + par for yy in years for par, cs in children[yy].items() for c in cs}
        top_of = {p['group']: parent_of.get(p['group'], p['group']) for p in by.values()}   # the reviewed story (a star) each piece is or belongs to
        top_label = {t: groups[t]['label'] for t in set(top_of.values())}
        lines.append({**s, 'years': years, 'year_papers': {yy: len(reviewed[yy]['newspapers']) for yy in years}, 'by': by, 'acts': acts, 'every': every, 'papers': papers, 'obs': obs, 'kids_of': kids_of,
                      'top_of': top_of, 'top_label': top_label})
    return lines


def links(lines):
    """Group id -> [href, storyline] for 'Read the storyline': a piece goes to its card, a parent to the act that tells
    all of it (or to the storyline, when its pieces are spread over several acts). A story told whole goes to its card."""
    out = {}
    for s in lines:
        sid = s['id']
        for k, p in s['by'].items():
            out[p['group']] = [f'stories.html#{sid}-{k}', s['short']]
        for par, kids in s['kids_of'].items():
            act = (next((a for a in s['acts'] if {p['group'] for p in a['ps']} == kids), None)
                   or next((a for a in s['acts'] if kids <= {p['group'] for p in a['ps']}), None))
            out[par] = [f'stories.html#{sid}-act-{act["num"]}' if act else f'stories.html#{sid}', s['short']]
    return out


# ---- Rendering ----
def _img(src, alt, sizes):
    w, h = sizes(src)
    return f'<img src="{esc(src)}" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{esc(alt)}">'


def _figure(s, oid, crop, sizes, note=''):
    o = s['obs'][oid]
    p = s['papers'][o['node']]
    src = f'assets/story_discovery_{o["_year"]}__evidence__{crop}.jpg'
    return (f'<figure class="scan">{_img(src, f"Scan of the {p["name"]}, {day(o["date"], True)}, page {o["page"]}", sizes)}'
            f'<figcaption>Scan · <i>{esc(p["name"])}</i>, {esc(p["place"])}, {day(o["date"], True)}, page {o["page"]}'
            f'{(" · " + esc(note)) if note else ""} · <a href="{esc(o["source_url"])}">the whole page (PDF)</a></figcaption></figure>')


def _printed_by(s, p):
    chips = ''.join(f'<li><span>{esc(s["papers"][o["node"]]["name"])}</span> {D(o["date"]).day} {D(o["date"]):%b}</li>' for o in p['prints'])
    focus = 'pulses.html?year=%d&amp;focus=%s' % (p['prints'][0]['_year'], p['group'].replace(':', '%3A'))
    return (f'<div class="by"><details><summary>Printed by {p["papers"]} newspapers, {span(p["prints"][0]["date"], p["prints"][-1]["date"])}</summary>'
            f'<ul>{chips}</ul></details><a href="{focus}">Follow it in Pulses</a></div>')


def _setting(s, p):
    if not p['set']:
        return ''
    rows = []
    for oid, text in p['set']:
        o = s['obs'][oid]
        pp = s['papers'][o['node']]
        rows.append(f'<li><b>{esc(pp["name"])}</b> <span class="d">{esc(pp["place"].split(",")[0])}, {day(o["date"])}</span> {text}</li>')
    return f'<div class="set"><h4>How the papers set it</h4><ul>{"".join(rows)}</ul></div>'


def stars(s):
    """The reviewed stories a storyline holds (each a star of the Telescope), in the order of their pieces."""
    return list(dict.fromkeys(s['top_of'][p['group']] for p in sorted(s['by'].values(), key=lambda p: p['key'])))


def _star_line(s, p):
    """Which reviewed story a piece is, or belongs to, with the way to its star (the words Pulses uses: 'See it in the sky')."""
    top = s['top_of'][p['group']]
    sky = f'<a href="telescope.html?story={quote(top)}">See it in the sky</a>'
    if top == p['group']:
        return f'<p class="star">A reviewed story · {sky}</p>'
    n = sum(1 for q in s['by'].values() if s['top_of'][q['group']] == top)
    return f'<p class="star">One of {words(n)} pieces of a reviewed story: {esc(s["top_label"][top])} · {sky}</p>'


def _piece(s, p, sizes):
    o = s['obs'][p['quote']]
    name = s['papers'][o['node']]['name']
    second = _figure(s, p['second']['printing'], p['second']['crop'], sizes, p['second']['note']) if p.get('second') else ''
    return (f'<article class="piece" id="{s["id"]}-{p["key"]}" aria-label="{esc(p["label"])}"><div class="meta"><span class="kind">{esc(p["kind"])}</span>'
            f'<span class="when">{p.get("dated", "Dated")} {day(p["signed"], D(p["signed"]).year != p["prints"][0]["_year"])}</span><span class="who">{esc(p["who"])}</span></div>'
            f'{_star_line(s, p)}<p class="says">{p["says"]}</p>'
            f'<div class="evidence"><blockquote>{esc(o["excerpt"].strip())}<cite>The opening as printed in the <i>{esc(name)}</i>, {day(o["date"])}. '
            f'The transcription matches the scan.</cite></blockquote>{_figure(s, p["quote"], p.get("crop") or p["quote"], sizes)}{second}</div>'
            f'{_setting(s, p)}{_printed_by(s, p)}</article>')


def _star_order(s):
    """The thread's reviewed stories in the order the papers first printed them, with each one's first printing and card."""
    first = {}
    for p in s['by'].values():
        t = s['top_of'][p['group']]
        first[t] = min(first.get(t, (p['prints'][0]['date'], p['key'])), (p['prints'][0]['date'], p['key']))
    return sorted(first, key=lambda t: first[t]), first


def _jit(k):
    """A fixed spread in -0.5..0.5 for the k-th star of the sky, so the chart is the same at every build."""
    x = math.sin((k + 1) * 3.3) * 43758.5453
    return x - math.floor(x) - .5


def _head(s, sky, order, first):
    """The thread's reviewed stories on the time axis of its chart (x as in _chart): up, how many newspapers printed each;
    numbered and joined in the order they were first printed. Faint behind them, the other stories of the same months in
    three or more newspapers, in the Telescope's colours (long-running texts left out, as there). sky: the build's stars."""
    W, L, top, bottom = 960, 222, 30, 14
    x0, x1 = D(s['chart']['from']), D(s['chart']['to'])
    w = W - L - 18
    X = lambda d: L + (d - x0).days / (x1 - x0).days * w
    at = {st['id']: st for st in sky}
    own = set(order)
    back = [(k, st, SKY_EPOCH + timedelta(days=st['first'])) for k, st in enumerate(sky)
            if st['year'] in s['years'] and st['kind'] in (0, 1) and not st.get('long') and st['papers'] >= 3 and st['id'] not in own]
    back = [(k, st, d) for k, st, d in back if x0 <= d <= x1]
    pmax = max([at[t]['papers'] for t in order] + [st['papers'] for _, st, _ in back])
    H = top + bottom + 22 * (pmax - 2)
    band = (H - top - bottom) / (pmax - 2)
    Y = lambda n: top + (pmax - n + .5) * band
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="{s["id"]}-hc"><title id="{s["id"]}-hc">{esc(s["short"])}: its {len(order)} '
           f'reviewed stories by the day each was first printed and how many newspapers printed it, among the other stories of those months</title>']
    m = date(x0.year, x0.month, 1)
    while m <= x1:
        if m >= x0:
            x = X(m)
            new_year = m.month == 1 and len(s['years']) > 1
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top - 6}" y2="{H - bottom}" class="{"hc-year" if new_year else "grid"}"/>')
            if new_year:
                out.append(f'<text x="{x + 4:.1f}" y="{top - 12}" class="hc-yl">{m.year}</text>')
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    for n in range(3, pmax + 1, 1 if pmax <= 8 else 2):
        out.append(f'<text x="{L - 12}" y="{Y(n) + 4:.1f}" class="row" text-anchor="end">{n} newspapers</text>')
    for k, st, d in sorted(back, key=lambda b: b[1]['kind']):      # reviewed over matched
        out.append(f'<circle cx="{X(d):.1f}" cy="{Y(st["papers"]) + _jit(k) * band * .7:.1f}" r="{2.3 if st["kind"] else 1.9}" '
                   f'class="{"hc-rev" if st["kind"] else "hc-back"}"/>')
    pts = [[X(SKY_EPOCH + timedelta(days=at[t]['first'])), Y(at[t]['papers'])] for t in order]
    for a in range(len(pts)):     # two marks that would cover each other part up and down within their band
        for b in range(a + 1, len(pts)):
            if abs(pts[a][0] - pts[b][0]) < 17 and abs(pts[a][1] - pts[b][1]) < 1:
                pts[a][1] -= .4 * band
                pts[b][1] += .4 * band
    out.append('<polyline points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts) + '" class="hc-line"/>')
    rows = {p['group']: p['row'] for p in s['by'].values()}
    for n, (t, (x, y)) in enumerate(zip(order, pts), 1):
        tip = (f'{n}. {rows.get(t) or s["top_label"][t]}: first printed {day(first[t][0], True)}, by {at[t]["papers"]} newspapers '
               f'in {at[t]["prints"]} printings')
        out.append(f'<a href="#{s["id"]}-{first[t][1]}"><circle cx="{x:.1f}" cy="{y:.1f}" r="8" class="hc-star"><title>{esc(tip)}</title></circle>'
                   f'<text x="{x:.1f}" y="{y + 3.6:.1f}" class="hc-num" text-anchor="middle">{n}</text></a>')
    out.append('</svg>')
    n_rev = sum(1 for _, st, _ in back if st['kind'])
    counts = [(s['year_papers'][y], y) for y in s['years']]
    held = f'{counts[0][0]} newspapers in {counts[0][1]}' + ''.join(f'{" and" if k == len(counts) - 1 else ","} {n} in {y}' for k, (n, y) in enumerate(counts[1:], 1))
    key = (f'<figcaption class="key"><i class="rk">1</i> a reviewed story of this thread, placed by the day it was first printed, on the same time '
           f'line as the chart below, and by how many newspapers printed it; the line joins them in that order and shows order only, not that one '
           f'caused the next. The rows below carry the same numbers. Faint: the other stories first printed in these months in three or more '
           f"newspapers, in the Telescope's colours, <i class=\"k-rev\">●</i> reviewed · read and checked against the scans ({n_rev}), "
           f'<i class="k-back">●</i> matched by shared wording · not checked ({len(back) - n_rev}); stories with the same count are spread a little up '
           f'and down so that none hides another, and that spread means nothing. The archive holds {held}, by catalogue number.</figcaption>')
    return f'<figure class="chart hc"><div class="cw">{"".join(out)}</div>{key}</figure>'


def _chart(s, num=None):
    ps = s['pieces']
    by = s['by']
    W, L, top, RH = 960, 222, 34, 27
    x0, x1 = D(s['chart']['from']), D(s['chart']['to'])
    w = W - L - 18
    X = lambda d: L + ((D(d) if isinstance(d, str) else d) - x0).days / (x1 - x0).days * w
    H = top + RH * len(ps) + 34
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="{s["id"]}-ch"><title id="{s["id"]}-ch">{esc(s["short"])} as it reached the page: '
           f'one row per printed piece, in the order the papers first printed it; one dot per printing</title>']
    m = date(x0.year, x0.month, 1)
    while m <= x1:
        if m >= x0:
            x = X(m)
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top - 8}" y2="{H - 26}" class="grid"/><text x="{x + 3:.1f}" y="{H - 10}" class="tick">{m.year if (m.month == 1 and len(s["years"]) > 1) else format(m, "%b")}</text>')
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    mk = s['chart'].get('mark')
    if mk:
        xa = X(mk['date'])
        out.append(f'<line x1="{xa:.1f}" x2="{xa:.1f}" y1="{top - 16}" y2="{H - 26}" class="mark"><title>{esc(mk["title"])}</title></line>'
                   f'<text x="{xa + 4:.1f}" y="{top - 18}" class="mark-l">{esc(mk["label"])}</text>')
    for i, p0 in enumerate(sorted(ps, key=lambda p: (by[p['key']]['prints'][0]['date'], p['key']))):
        p = by[p0['key']]
        y = top + i * RH + RH / 2
        if num:      # the number of the reviewed story the piece belongs to, as in the head chart above
            out.append(f'<circle cx="{L - 15}" cy="{y:.1f}" r="7" class="rn-c"/><text x="{L - 15}" y="{y + 3.4:.1f}" class="rn" text-anchor="middle">{num[p["key"]]}</text>')
        out.append(f'<text x="{L - 28 if num else L - 12}" y="{y + 4:.1f}" class="row" text-anchor="end"><a href="#{s["id"]}-{p["key"]}">{esc(p["row"])}</a></text>')
        first = p['prints'][0]['date']
        if p.get('sat'):
            a, b = X(p['sat'][0]), X(p['sat'][1])
            out.append(f'<rect x="{a:.1f}" y="{y - 2.5:.1f}" width="{b - a:.1f}" height="5" rx="2.5" class="sat"><title>The court sat from {day(p["sat"][0])} to {day(p["sat"][1], True)}</title></rect>')
        xs = X(p['signed'])
        if p['signed'] != first:
            out.append(f'<line x1="{xs:.1f}" x2="{X(first):.1f}" y1="{y:.1f}" y2="{y:.1f}" class="lag"/>')
        out.append(f'<path d="M{xs:.1f} {y - 6:.1f}l6 6-6 6-6-6z" class="signed"><title>{esc(p["row"])}: {p.get("dated", "dated").lower()} {day(p["signed"], True)}</title></path>')
        same = {}
        for o in p['prints']:
            same.setdefault(o['date'], []).append(o)
        for d0, os_ in same.items():
            for k, o in enumerate(os_):
                dy = (k - (len(os_) - 1) / 2) * 6.5
                pp = s['papers'][o['node']]
                out.append(f'<circle cx="{X(d0):.1f}" cy="{y + dy:.1f}" r="4.3" class="dot"><title>{esc(pp["name"])}, {esc(pp["place"])}: {day(d0, True)}</title></circle>')
    out.append('</svg>')
    return ''.join(out)


def _table(s):
    rows = ''.join(f'<tr><th scope="row"><a href="#{s["id"]}-{p["key"]}">{esc(p["row"])}</a></th><td>{p.get("dated", "Dated")} {day(p["signed"], D(p["signed"]).year != p["prints"][0]["_year"])}</td>'
                   f'<td>{day(p["prints"][0]["date"], len(s["years"]) > 1)}</td><td>{day(p["prints"][-1]["date"], len(s["years"]) > 1)}</td><td>{p["papers"]}</td><td>{len(p["prints"])}</td></tr>'
                   for p in sorted(s['by'].values(), key=lambda p: (p['prints'][0]['date'], p['key'])))
    return (f'<details class="numbers"><summary>The pieces as a table</summary><div class="tw"><table><thead><tr><th scope="col">Piece</th><th scope="col">Written or signed</th>'
            f'<th scope="col">First printed</th><th scope="col">Last printed</th><th scope="col">Newspapers</th><th scope="col">Printings</th></tr></thead><tbody>{rows}</tbody></table></div></details>')


def _act(s, a, sizes):
    ps = a['ps']
    when = span(min(o['date'] for p in ps for o in p['prints']), max(o['date'] for p in ps for o in p['prints']))
    m = a.get('machine')
    machine = ''
    if m:
        head = 'Found while reading' if m['kind'] == 'found' else 'Read by the machine'
        machine = (f'<aside class="machine"><h4>{head}</h4><p>{m["text"]}</p>'
                   + (_figure(s, m['printing'], m['crop'], sizes) if m.get('crop') else '') + '</aside>')
    doors = ''.join(f'<a href="{esc(h)}">{esc(t)}</a>' for t, h in a.get('doors', []))
    if a.get('voices'):   # two voices that answered each other in print, side by side in date order
        cells = ''.join(f'<div class="cell {p["side"]}"><p class="vhead">{s["voices"][p["side"]]}</p>{_piece(s, p, sizes)}</div>' for p in ps)
        body = f'<div class="voices">{cells}</div>'
    else:
        body = ''.join(_piece(s, p, sizes) for p in ps)
    return (f'<section class="act" id="{s["id"]}-act-{a["num"]}" aria-labelledby="{s["id"]}-act-{a["num"]}-h"><header><span class="num">Act {a["num"]}</span>'
            f'<h3 id="{s["id"]}-act-{a["num"]}-h">{esc(a["title"])}</h3><span class="span">{when}</span></header>'
            f'<p class="tell">{a["text"]}</p>{body}{machine}<p class="doors">{doors}</p></section>')


def _storyline(s, sizes, sky=None):
    every = s['every']
    head, num = '', None
    if sky:      # the head chart, and the same numbers beside the rows of the chart below
        order, first = _star_order(s)
        head = _head(s, sky, order, first)
        num = {k: order.index(s['top_of'][p['group']]) + 1 for k, p in s['by'].items()}
    reach = (', ' + ' to '.join(s['reach'])) if s.get('reach') else ''
    after = s.get('after')
    epi = ''
    if after:
        doors = ''.join(f'<a href="{esc(h)}">{esc(t)}</a>' for t, h in after.get('doors', []))
        epi = f'<div class="epi"><h3>{esc(after["title"])}</h3><p>{after["text"]}</p><p class="doors">{doors}</p></div>'
    return (f'<section class="story" id="{s["id"]}" aria-labelledby="{s["id"]}-h"><p class="sk">Thread · {s["year"] if len(s["years"]) < 2 else str(s["years"][0]) + "–" + str(s["years"][-1])}</p>'
            f'<h2 id="{s["id"]}-h">{s["title"]}</h2><p class="stand">{s["standfirst"]}</p>'
            f'<p class="facts"><span><b>{len(stars(s))}</b> reviewed stories</span><span><b>{len(s["by"])}</b> printed pieces</span><span><b>{len(every)}</b> printings</span>'
            f'<span><b>{len({o["node"] for o in every})}</b> newspapers{esc(reach)}</span><span><b>{span(every[0]["date"], every[-1]["date"], True)}</b></span>'
            f'<span>every printing checked against its scan</span></p>{head}'
            f'<figure class="chart"><div class="cw">{_chart(s, num)}</div><figcaption class="key"><i>●</i> a newspaper\'s printing &nbsp; <em>◇</em> the day the piece was written or signed'
            + (' &nbsp; <em>▬</em> the days the court sat' if any(p.get('sat') for p in s['by'].values()) else '') +
            '. Rows go down in the order the pieces first appeared, so they step to the right by construction; what to read is the spread within each row '
            '(how long a piece stayed in print) and the gap between a diamond and its dots (how long a piece took to reach these papers). Point at a dot for the paper and the day.</figcaption></figure>'
            f'{_table(s)}'
            f'{"".join(_act(s, a, sizes) for a in s["acts"])}{epi}</section>')


def render(lines, sizes, sky=None):
    """The page's threads (the ledger's storylines). sizes(src) -> (width, height) of an image on the site; sky: the
    build's stars (as in telescope.json), for each thread's head chart (left out when None)."""
    shelf = ''
    if len(lines) > 1:
        shelf = '<nav class="shelf" aria-label="Threads">' + ''.join(
            f'<a href="#{s["id"]}"><span class="y">{s["year"] if len(s["years"]) < 2 else str(s["years"][0]) + "–" + str(s["years"][-1])}</span><b>{s["title"]}</b><span>{len(stars(s))} reviewed stories, {len(s["by"])} pieces, '
            f'{len(s["every"])} printings, {len({o["node"] for o in s["every"]})} newspapers</span></a>' for s in lines) + '</nav>'
    return shelf + ''.join(_storyline(s, sizes, sky) for s in lines)
