"""The Findings page (findings.html): what the archive shows, tested.

Each finding has its claim in plain words, one chart drawn from the data at build time, how sure it is, what it does
not say, and doors into the instruments that show it. The numbers come from the build's own data (the sky's stars,
the year index) and from the checks' outputs (outputs/matched_audit/summary.json, outputs/story_discovery_all/
cycle_lengths.json), never typed by hand, so they stay right when the data changes.

Charts are inline SVG: thin bars with rounded data ends and 2-pixel gaps, recessive axes, a tooltip (<title>) on every
mark, and the numbers in a table under each chart. Colours: gold for what a finding is about, slate for the rest, as on
the telescope's timeline. The pair is a highlight, not a set of categories (the validator's colour-blind separation,
dE 37, and contrast, 3:1 or more, pass; slate is meant to read as grey)."""
import datetime, html, math, re, statistics
from urllib.parse import quote

GOLD, SLATE, SOFT, INK, MUTED, GRID, SURFACE = '#ffd27a', '#56698f', '#8b98b5', '#e8edf7', '#8b98b5', '#1a2338', '#0b1222'
EPOCH = datetime.date(1770, 1, 1)
YEARS = list(range(1770, 1811))
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
esc = html.escape


def search(stars, query):
    """The telescope's search rule: commas separate alternatives, words of one alternative must all appear, at the start
    of a word, and "quotes" keep a phrase. Returns the matching stars."""
    groups = []
    for part in re.split(r'\s*,\s*', query.lower()):
        terms = [a or b for a, b in re.findall(r'"([^"]+)"|(\S+)', part)]
        groups.append([re.compile(r'(^|[^a-z])' + re.escape(t).replace(r'\ ', r'[\s-]+')) for t in terms])
    return [s for s in stars if any(all(rx.search(s['text']) for rx in g) for g in groups)]


def poisson_tail(k, lam):
    if lam <= 0: return 0.0
    term, cdf = math.exp(-lam), 0.0
    for j in range(k): cdf += term; term *= lam / (j + 1)
    return max(0.0, 1 - cdf)


def runs_of(years):
    out = []
    for y in years:
        if out and y == out[-1][1] + 1: out[-1][1] = y
        else: out.append([y, y])
    return out


def run_text(runs):
    return '; '.join(str(a) if a == b else f'{a}–{b}' for a, b in runs)


# ---- marks ----
def bar(x, base, w, h, fill, tip, outline=False):
    if h <= 0: return ''
    r = min(2, w / 2, h)
    path = (f'M{x:.1f},{base:.1f}V{base - h + r:.1f}Q{x:.1f},{base - h:.1f} {x + r:.1f},{base - h:.1f}'
            f'H{x + w - r:.1f}Q{x + w:.1f},{base - h:.1f} {x + w:.1f},{base - h + r:.1f}V{base:.1f}Z')
    style = f'fill="none" stroke="{fill}" stroke-width="1" stroke-dasharray="2 2"' if outline else f'fill="{fill}"'
    return f'<path d="{path}" {style}><title>{esc(tip)}</title></path>'


def bars(values, cats, colour, tip, ymax, unit='', W=900, H=170, tick_every=5, ref=None, notes=(), thin=(), label=str, title=''):
    """A bar chart: one bar per category, a recessive grid, every bar with its tooltip. notes: (category, value, text,
    on_top) direct labels for a few bars; on_top puts the text at the top with a thin leader down to the bar."""
    L, R, T, B = 44, 8, 22, 24
    pw, ph = W - L - R, H - T - B; slot = pw / len(values); base = T + ph
    out = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="{esc(title)}">']
    for k in range(5):
        v = ymax * k / 4; y = base - ph * k / 4
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>'
                   f'<text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end" fill="{MUTED}" font-size="11">{v:g}{unit}</text>')
    for j, (c, v) in enumerate(zip(cats, values)):
        x = L + j * slot + 1
        if c in thin: out.append(bar(x, base, slot - 2, max(ph * .08, 2), MUTED, f'{label(c)}: too little archive to judge', outline=True))
        else: out.append(bar(x, base, slot - 2, ph * min(v, ymax) / ymax, colour(c), tip(c, v)))
        if j % tick_every == 0:
            out.append(f'<text x="{x + (slot - 2) / 2:.1f}" y="{H - 6}" text-anchor="middle" fill="{MUTED}" font-size="11">{label(c)}</text>')
    if ref is not None:
        y = base - ph * ref / ymax
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="{MUTED}" stroke-dasharray="4 3"/>')
    for c, v, text, *top in notes:
        j = cats.index(c); x = L + j * slot + slot / 2; y = base - ph * min(v, ymax) / ymax - 6
        if top and top[0]:
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{T + 4:.1f}" y2="{y + 2:.1f}" stroke="{MUTED}"/>'); y = T - 2
        half = len(text) * 3.1
        anchor, tx = ('end', x + slot / 2) if x + half > W - R else ('start', x - slot / 2) if x - half < L else ('middle', x)
        out.append(f'<text x="{tx:.1f}" y="{max(T - 6, y):.1f}" text-anchor="{anchor}" fill="{INK}" font-size="11">{esc(text)}</text>')
    out.append('</svg>')
    return ''.join(out)


def table(rows, head):
    return ('<details class="numbers"><summary>The numbers</summary><div class="tbl"><table><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr>'
            + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) + '</table></div></details>')


SUMMARY = []   # (n, kind, title, first door's label, its link) for each finding of the last render(), for Home


def year_counts(stars):
    """Stories in the sky per year of first printing (long-running stories left out), and the years with too little
    archive to judge: under a fifth of a typical year's stories."""
    per_year = {y: 0 for y in YEARS}
    for s in stars:
        if not s['long']: per_year[s['year']] += 1
    typical = statistics.median(per_year.values())
    return per_year, [y for y in YEARS if per_year[y] < typical / 5]


def finding(n, kind, title, claim, body, sure, not_say, doors, numbers=''):
    SUMMARY.append((n, kind, title, *doors[0]))
    links = ''.join(f'<a href="{esc(h)}">{esc(t)}</a>' for t, h in doors)
    return (f'<section class="finding" id="f{n}"><div class="n">{n} · {esc(kind)}</div><h2>{title}</h2><p class="claim">{claim}</p>{body}'
            f'<div class="facts"><div><b>How sure</b>{sure}</div><div><b>What it does not say</b>{not_say}</div></div>'
            f'<div class="doors">{links}</div>{numbers}</section>')


def key(*items):
    return '<p class="cap">' + ''.join(f'<span class="key"><i style="background:{c}"></i>{esc(t)}</span>' for c, t in items) + '</p>'


# ---- the findings ----
def render(*, years, stars, decl_printings, audit, cycles, repo):
    """years: [(year, newspapers, pages)]; stars: the sky's stars (year, first, long, papers, text); decl_printings:
    [(newspaper, 'YYYY-MM-DD', town, lat, lon)] for the Declaration; audit: the matched audit's summary; cycles: the cycle-length check
    (or None); repo: the public repository's URL."""
    arch = {y: (p, pg) for y, p, pg in years}
    keep = [s for s in stars if not s['long']]
    per_year, thin = year_counts(stars)
    judged = [y for y in YEARS if y not in thin]
    out = []; SUMMARY.clear()

    # 1 · the source: what survives
    t0, t1 = thin[0], thin[-1]
    c1a = bars([arch[y][0] for y in YEARS], YEARS, lambda y: GOLD if y in thin else SLATE,
               lambda y, v: f'{y}: {v} newspapers survive ({arch[y][1]:,} pages)', 20, H=150, title='Newspapers that survive, each year',
               notes=[(thin[len(thin) // 2], arch[thin[len(thin) // 2]][0], ' and '.join(str(y) for y in thin if arch[y][0] == min(arch[t][0] for t in thin)) + f': {min(arch[t][0] for t in thin)} newspapers each', True)])
    c1b = bars([per_year[y] for y in YEARS], YEARS, lambda y: GOLD if y in thin else SLATE,
               lambda y, v: f'{y}: {v:,} stories in the sky first printed', 3000, H=150, title='Stories in the sky, each year')
    after = [arch[y][0] for y in range(1800, 1811)]
    out.append(finding(1, 'The source', 'A thin sky is a gap in the archive, not silence',
        f'Only {", ".join(f"{arch[y][0]} newspapers survive for {y}" for y in thin[:1])}'
        + (f' and {min(arch[y][0] for y in thin[1:])} for each of {" and ".join(str(y) for y in thin[1:])}' if len(thin) > 1 else '')
        + f', against {arch[t1 + 1][0]} in {t1 + 1} and {min(after)} to {max(after)} a year after 1800, and the stories in the sky nearly vanish with them. The low years show what was kept, not how much was printed.',
        f'<div class="cap"><b>Newspapers that survive, each year</b></div>{c1a}<div class="cap"><b>Stories in the sky, by year of first printing</b> (each row its own scale)</div>{c1b}'
        + key((GOLD, f'{t0}–{t1}: less than a fifth of a typical year\'s stories'), (SLATE, 'other years')),
        f'Counts from the dataset itself: {sum(arch[y][1] for y in YEARS):,} pages of 110 newspapers. A fact about the source, not a test.',
        'Nothing about what those papers printed, only how much of them survives. A full year is full because more papers survive, not because more happened.',
        [(f'Follow {t0 - 2}–{t1 + 2} in Pulses', f'pulses.html?years={t0 - 2}-{t1 + 2}'), ('See the thin sky', f'telescope.html?year={t1 + 2}&lookback=10')],
        table([(y, arch[y][0], f'{arch[y][1]:,}', f'{per_year[y]:,}') for y in YEARS], ['Year', 'Newspapers', 'Pages', 'Stories'])))

    # 2 · the source: how far the machine's reading can be trusted
    tr, raw = audit['transcription'], audit['raw_reviewer_counts']['transcription']
    located = tr['faithful']['count'] + tr['minor_errors']['count'] + tr['major_problem']['count']
    own, strict = raw['major_problem'], tr['major_problem']['count']
    rows = [('Reviewers’ own calls', raw['faithful'], raw['minor_errors'], own), ('One strict rule for all', tr['faithful']['count'], tr['minor_errors']['count'], strict)]
    W, L, rh = 900, 170, 30; svg = [f'<svg viewBox="0 0 {W} {len(rows) * (rh + 14) + 8}" class="chart" role="img" aria-label="Misreadings in the audit">']
    for k, (name, f_, m_, x_) in enumerate(rows):
        y = 6 + k * (rh + 14); svg.append(f'<text x="{L - 10}" y="{y + rh / 2 + 4}" text-anchor="end" fill="{INK}" font-size="12">{esc(name)}</text>'); x = L
        for cnt, col, what in ((f_, SLATE, 'faithful'), (m_, SOFT, 'minor errors'), (x_, GOLD, 'a fact-changing misreading')):
            w = (W - L - 8) * cnt / located
            svg.append(f'<rect x="{x:.1f}" y="{y}" width="{max(0, w - 2):.1f}" height="{rh}" rx="2" fill="{col}"><title>{esc(name)}: {cnt} of {located} passages, {what} ({100 * cnt / located:.0f}%)</title></rect>')
            if w > 60: svg.append(f'<text x="{x + 8:.1f}" y="{y + rh / 2 + 4}" fill="#050711" font-size="12" font-weight="600">{100 * cnt / located:.0f}%</text>')
            x += w
    svg.append('</svg>')
    out.append(finding(2, 'The source', 'About one passage in five has a misreading that changes a fact',
        f'The archive’s machine transcriptions are good enough to find stories, not to quote them. In a random sample of {audit["audited"]} matched stories, {own} of the {located} passages found on their scans ({100 * own / located:.0f}%) had a misreading that changes a fact by the reviewers’ own calls, and {strict} ({100 * strict / located:.0f}%) under one strict rule for all. In 1776 the machine read “slaves” in 8 of the 9 printings of the resolution opening the ports, where the papers printed “ſtaves”.',
        f'<div class="cap"><b>{located} passages checked against their scans</b></div>{"".join(svg)}'
        + key((SLATE, 'faithful'), (SOFT, 'minor errors'), (GOLD, 'a misreading that changes a fact: a number, a date, a name or a word with another meaning')),
        f'A random sample (seed {audit["meta"]["seed"]}) of {audit["meta"]["population"]:,} matched stories, read against the scans by eight reviewers under one written rule, with a blind second reader for 30 of them. All {audit["on_page"]["yes"]["count"]} passages found were on their pages. The range runs from the reviewers’ own calls to the strict rule.',
        'Which passages are wrong: it is a rate over a sample, not a mark on each passage. The automatic check that every printing gets (is the passage in both transcriptions of its page?) does not predict these errors, so check the scan before quoting.',
        [('Read the ports resolution, with its scans', 'pulses.html?year=1776&focus=' + quote('group:congress-opens-ports')), ('How the stories were checked', 'method.html#checks')],
        table([(name, f'{f_} ({100 * f_ / located:.0f}%)', f'{m_} ({100 * m_ / located:.0f}%)', f'{x_} ({100 * x_ / located:.0f}%)') for name, f_, m_, x_ in rows], ['', 'Faithful', 'Minor errors', 'Fact-changing'])))

    # 3 · how a story travels: the Declaration, each printing by its date and by its town's distance from the town that
    # printed it first. Both axes are measures, so any slope in the dots is in the data (not made by sorting the rows).
    pr = sorted((datetime.date.fromisoformat(dt), name, place, lat, lon) for name, dt, place, lat, lon in decl_printings)
    d0, d1 = pr[0][0], pr[-1][0]; span = (d1 - d0).days; home = pr[0][2].split(',')[0]
    def km(a, b):
        la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
        return 6371 * 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))
    pts = [(dt, name, place.split(',')[0], km((pr[0][3], pr[0][4]), (lat, lon))) for dt, name, place, lat, lon in pr]
    first_of = {}
    for dt, name, town, dist in pts: first_of.setdefault(name, (dt, dist))
    def ranks(a):
        order = sorted(range(len(a)), key=lambda i: a[i]); r = [0.0] * len(a); i = 0
        while i < len(a):
            j = i
            while j + 1 < len(a) and a[order[j + 1]] == a[order[i]]: j += 1
            for k in range(i, j + 1): r[order[k]] = (i + j) / 2
            i = j + 1
        return r
    xs, ys = [v[1] for v in first_of.values()], [(v[0] - d0).days for v in first_of.values()]
    rx, ry = ranks(xs), ranks(ys); mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    rho = sum((u - mx) * (v - my) for u, v in zip(rx, ry)) / math.sqrt(sum((u - mx) ** 2 for u in rx) * sum((v - my) ** 2 for v in ry))
    top = math.ceil(max(d for *_, d in pts) / 100) * 100
    W, L, R, T, B = 900, 64, 24, 18, 30; H = 270; pw, ph = W - L - R, H - T - B
    xd = lambda dt: L + pw * ((dt - d0).days + .5) / (span + 1); yd = lambda d: T + ph - ph * d / top
    svg = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="Each printing of the Declaration by date and by distance from {esc(home)}">']
    for v in range(0, top + 1, 100):
        svg.append(f'<line x1="{L}" x2="{W - R}" y1="{yd(v):.1f}" y2="{yd(v):.1f}" stroke="{GRID}"/><text x="{L - 8}" y="{yd(v) + 4:.1f}" text-anchor="end" fill="{MUTED}" font-size="11">{v} km</text>')
    for k in range(0, span + 1, 5):
        dd = d0 + datetime.timedelta(days=k)
        svg.append(f'<text x="{xd(dd):.1f}" y="{H - 8}" text-anchor="middle" fill="{MUTED}" font-size="11">{dd.day} {dd.strftime("%b")}</text>')
    seen, dots = {}, []
    for dt, name, town, dist in pts:   # printings on the same day in the same town stand one above the other
        k = seen.get((dt, round(dist)), 0); seen[(dt, round(dist))] = k + 1; cx, cy = xd(dt), yd(dist) - 9 * k; dots.append((cx, cy))
        svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{GOLD}" stroke="{SURFACE}" stroke-width="2"><title>{esc(name)}, {esc(town)}, {dt.day} {dt.strftime("%B %Y")} ({dist:.0f} km from {esc(home)})</title></circle>')
    towns = {}
    for dt, name, town, dist in pts: towns.setdefault(town, [dt, dist, set()])[2].add(name)
    # Each town is named once, beside its first printing: the first of right, above, below or left that touches no dot,
    # no other name and no edge (text width estimated at 6.2 pixels a character).
    boxes = [(cx - 6, cy - 6, cx + 6, cy + 6) for cx, cy in dots]
    hit = lambda b: b[0] < L or b[2] > W - R or b[1] < 2 or b[3] > T + ph + 2 or any(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3] for o in boxes)
    for town, (dt, dist, names) in towns.items():
        label = town + (f' \u00b7 {len(names)} papers' if len(names) > 1 else ''); w = 6.2 * len(label); cx, cy = xd(dt), yd(dist)
        for x0, y0, anchor in ((cx + 9, cy + 4, 'start'), (cx - 4, cy - 11, 'start'), (cx - 4, cy + 19, 'start'), (cx - 9, cy + 4, 'end')):
            b = (x0 - (w if anchor == 'end' else 0), y0 - 10, x0 + (0 if anchor == 'end' else w), y0 + 2)
            if not hit(b): break
        boxes.append(b)
        svg.append(f'<text x="{x0:.1f}" y="{y0:.1f}" text-anchor="{anchor}" fill="{INK}" font-size="11">{esc(label)}</text>')
    svg.append('</svg>')
    out.append(finding(3, 'A story travels', f'The Declaration reached {len(first_of)} newspapers in {span + 1} days: the farther, the later',
        f'Adopted on 4 July 1776, the Declaration of Independence was first printed in this archive on {d0.day} {d0.strftime("%B")} in {esc(home)}. By {d1.day} {d1.strftime("%B")} it had appeared in {len(first_of)} of its newspapers, and the farther a paper\u2019s town from {esc(home)}, the later it printed it.',
        f'<div class="cap"><b>Each dot is one printing</b>: across, its date; up, how far its town is from {esc(home)}, as the crow flies</div>{"".join(svg)}',
        f'A reviewed story: each printing was found, read and checked against its scan. Distance and delay agree closely: a rank correlation of {rho:.2f} over its {len(first_of)} newspapers, as travel by post road and ship would make them. It is one story, so it shows how this one travelled.',
        'Who copied whom. A paper may have taken the text from any earlier paper, a handbill or a letter; the dots show when and where each printed it, not the road the text took. The distances are straight lines; the roads and the sea were longer.',
        [('Watch it pulse from paper to paper', 'pulses.html?year=1776&focus=' + quote('group:declaration-of-independence')), ('See it in the sky', 'telescope.html?story=' + quote('group:declaration-of-independence'))],
        table([(f'{dt.day} {dt.strftime("%b")}', esc(name), esc(town), f'{dist:.0f} km') for dt, name, town, dist in pts], ['Date', 'Newspaper', 'Town', f'From {esc(home)}'])))

    # 4 · coming back: the embargo's waves (the telescope's wave rule)
    emb_y = {y: 0 for y in YEARS}
    for s in search(keep, 'embargo'): emb_y[s['year']] += 1
    share = {y: emb_y[y] / per_year[y] if per_year[y] else 0 for y in YEARS}
    usual = min(statistics.median([share[y] for y in judged if emb_y[y]]), sum(emb_y[y] for y in judged) / sum(per_year[y] for y in judged))
    waves = [y for y in judged if emb_y[y] >= 3 and share[y] >= 2 * usual and poisson_tail(emb_y[y], usual * per_year[y]) < .05]
    wr = runs_of(waves)
    top = max(share.values()) * 100; ymax = math.ceil(top / 2) * 2
    last = wr[-1]
    c4 = bars([100 * share[y] for y in YEARS], YEARS, lambda y: GOLD if y in waves else SLATE,
              lambda y, v: f'{y}: {emb_y[y]} of {per_year[y]:,} stories mention “embargo” ({v:.1f}%)' + (' · a wave year' if y in waves else ''), ymax, '%', H=200,
              notes=[(1794, 100 * share[1794], '1794: the American embargo'), (last[0], 100 * share[last[0]], f'{last[0]}–{str(last[1])[2:]}: the Embargo Act')], thin=set(thin),
              title='Share of the year’s stories that mention embargo')
    out.append(finding(4, 'Coming back', 'The embargo came back with every crisis',
        f'Stories mentioning an embargo rose in {len(wr)} waves: {run_text(wr)}. Two are American, the embargo of 1794 and the Embargo Act of 1807–1809, whose year {last[0]} alone holds {emb_y[last[0]]} stories; between them come three European crises.',
        f'<div class="cap"><b>Share of the year’s stories that mention “embargo”</b> · gold: wave years · dashed outline: too little archive to judge</div>{c4}'
        '<p class="cap">The three small waves between are European: 1796, Spain’s embargoes on British and Dutch ships; 1798, French embargoes on American ships feared; 1801, Russia and Britain embargo each other’s ships.</p>',
        'A wave year has 3 or more such stories, twice the word’s usual share and P &lt; .05. The same rule finds the war with Tripoli (1801–1805) exactly, both American embargoes, the Algiers crisis and the great fever years; fire, the control, stays flat but for one borderline year.',
        'It follows the word, not one policy: 1796, 1798 and 1801 are Spanish, French, Russian and British embargoes. It counts reprinted stories, not events.',
        [('Trace it in the sky', 'telescope.html?q=embargo&lookback=all'), (f'Follow {last[0]} in Pulses', f'pulses.html?year={last[0]}')],
        table([(y, emb_y[y], f'{per_year[y]:,}', f'{100 * share[y]:.2f}%', 'wave' if y in waves else 'too little archive' if y in thin else '') for y in YEARS if emb_y[y] or y in thin],
              ['Year', 'Stories mentioning it', 'All stories', 'Share', ''])))

    # 5 · seasons: fever against fire
    def by_month(found):
        m = [0] * 12; C = S = 0.0
        for s in found:
            dt = EPOCH + datetime.timedelta(days=s['first']); m[dt.month - 1] += 1
            doy = (dt - datetime.date(dt.year, 1, 1)).days / (366 if dt.year % 4 == 0 and (dt.year % 100 or dt.year % 400 == 0) else 365)
            C += math.cos(2 * math.pi * doy); S += math.sin(2 * math.pi * doy)
        n = len(found); Rn = math.hypot(C, S)
        return m, n, Rn / n, math.exp(math.sqrt(1 + 4 * n + 4 * (n * n - Rn * Rn)) - (1 + 2 * n))
    FEVER, FIRE = 'yellow fever, malignant fever, prevailing fever', '"fire broke out", conflagration, "was consumed by fire", "destroyed by fire"'
    fever, fire = by_month(search(keep, FEVER)), by_month(search(keep, FIRE))
    def month_chart(res, hot, title):
        m, n, *_ = res
        return bars([100 * v / n for v in m], list(range(12)), lambda k: GOLD if k in hot else SLATE, lambda k, v: f'{MONTHS[k]}: {m[k]} of {n} stories ({v:.0f}%)',
                    40, '%', W=440, H=170, tick_every=1, ref=100 / 12, label=lambda k: MONTHS[k][0], title=title)
    jas = 100 * sum(fever[0][6:9]) / fever[1]
    p_text = 'P &lt; .001' if fever[3] < .001 else f'P {fever[3]:.3f}'
    out.append(finding(5, 'Seasons', 'Fever came back each late summer; fire kept no season',
        f'{jas:.0f}% of fever stories were first printed in July to September. Fires, which were reported all year, are the control: they keep to no month.',
        f'<div class="pair"><div><div class="cap"><b>Yellow, malignant or prevailing fever</b> · {fever[1]} stories · R {fever[2]:.2f}</div>{month_chart(fever, {6, 7, 8}, "Fever stories by month")}</div>'
        f'<div><div class="cap"><b>Fire broke out, conflagration…</b> · {fire[1]} stories · R {fire[2]:.2f}</div>{month_chart(fire, set(), "Fire stories by month")}</div></div>'
        '<p class="cap">Share of each kind’s stories first printed in each month · dashed line: no season (8.3% a month)</p>',
        f'Circular statistics on the day of first printing: fever R {fever[2]:.2f} (Rayleigh {p_text}), fire R {fire[2]:.2f}. The archive’s surviving pages are spread evenly over the year (R 0.007), so the season is not made by which months survive.',
        'When stories were first printed in this archive, not when epidemics began; and only these three phrases, so a report that says “the sickness” is missed.',
        [('Compare them by season in the sky', 'telescope.html?q=' + quote(f'{FEVER} vs {FIRE}') + '&view=orbit&lookback=all')]))

    # 6 · the year is the only cycle (from the cycle-length check)
    if cycles:
        ks = cycles['kinds']; W, L, R, T, rh = 900, 170, 16, 16, 22; H = T + rh * len(ks) + 30; pw = W - L - R
        lo, hi = math.log(6), math.log(400); xp = lambda d: L + pw * (math.log(d) - lo) / (hi - lo)
        at_year = lambda k: abs(k['best_days'] - 365.24) / 365.24 < .05
        svg = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="Strongest cycle of each kind of story">']
        for d, t in ((7, 'a week'), (30.44, 'a month'), (91.3, 'a quarter'), (182.6, 'half a year'), (365.24, 'a year')):
            svg.append(f'<line x1="{xp(d):.1f}" x2="{xp(d):.1f}" y1="{T - 6}" y2="{H - 24}" stroke="{GRID if d != 365.24 else MUTED}"/>'
                       f'<text x="{xp(d):.1f}" y="{H - 8}" text-anchor="middle" fill="{MUTED}" font-size="11">{t}</text>')
        for k, kd in enumerate(ks):
            y = T + rh * k + rh / 2; col = GOLD if at_year(kd) else SLATE
            svg.append(f'<text x="{L - 10}" y="{y + 4:.1f}" text-anchor="end" fill="{INK}" font-size="12">{esc(kd["kind"])}</text>'
                       f'<circle cx="{xp(kd["best_days"]):.1f}" cy="{y:.1f}" r="5" fill="{col}" stroke="{SURFACE}" stroke-width="2"><title>{esc(kd["kind"])}: {kd["stories"]} stories; strongest period {kd["best_days"]:g} days (P {kd["p_best"]:.3f}); a week, P {kd["p_at"]["week"]:.2f}</title></circle>')
        svg.append('</svg>')
        yearly = [kd for kd in ks if at_year(kd)]; others = [kd for kd in ks if not at_year(kd)]
        out.append(finding(6, 'Seasons', 'The year is the only cycle this archive keeps',
            f'Scanning every cycle from 6 to 400 days, {len(yearly)} of the {len(ks)} kinds of story tested have their strongest cycle at one year, and none has a weekly or monthly rhythm of its own. A month or half a year shows only as an echo of a sharp yearly date, such as the Fourth of July.',
            f'<div class="cap"><b>The strongest cycle of each kind</b>, on a scale from 6 to 400 days · gold: at one year</div>{"".join(svg)}',
            f'Each kind is compared with the archive’s own stories within each year, which removes the newspapers’ printing days, and against {cycles["draws"]} random draws, with the scan of many cycles paid for. The others peak elsewhere: '
            + '; '.join(f'{esc(kd["kind"].lower())} at {kd["best_days"]:g} days (P {kd["p_best"]:.2f})' for kd in others) + '; none convincingly once ten kinds are tested together.',
            'Why things come back at a season, and nothing about cycles longer than a year, such as elections every four years (below).',
            [('Independence Day by season, in the sky', 'telescope.html?q=' + quote('anniversary of independence, fourth of july, 4th of july') + '&view=orbit&lookback=all')],
            table([(esc(kd['kind']), kd['stories'], f'{kd["best_days"]:g} days', f'{kd["p_best"]:.3f}', f'{kd["p_at"]["week"]:.2f}') for kd in ks], ['Kind', 'Stories', 'Strongest cycle', 'P', 'A week, P'])))

    # 7 · every four years, from 1800
    ELECT = 'election, electors'
    el_y = {y: 0 for y in YEARS}
    for s in search(keep, ELECT): el_y[s['year']] += 1
    span_y = list(range(1789, 1811)); terms = [1792, 1796, 1800, 1804, 1808]
    esh = {y: 100 * el_y[y] / per_year[y] for y in span_y}
    near = [esh[y] for y in span_y if y not in terms]
    c7 = bars([esh[y] for y in span_y], span_y, lambda y: GOLD if y in terms else SLATE,
              lambda y, v: f'{y}: {el_y[y]} of {per_year[y]:,} stories mention an election ({v:.1f}%)' + (' · a presidential election' if y in terms else ''),
              math.ceil(max(esh.values())), '%', H=170, tick_every=1, label=lambda y: f"'{str(y)[2:]}", title='Share of stories that mention an election')
    late = [esh[y] for y in (1800, 1804, 1808)]
    out.append(finding(7, 'Coming back', 'Every four years, from 1800',
        f'Stories about elections peak in the presidential years 1800, 1804 and 1808 ({min(late):.1f}–{max(late):.1f}% of the year’s stories); before 1800 the rhythm is weak ({esh[1792]:.1f}% in 1792, {esh[1796]:.1f}% in 1796)' + (f', and 1802 is high too ({esh[1802]:.1f}%).' if esh[1802] >= .8 * min(late) else '.'),
        f'<div class="cap"><b>Share of the year’s stories that mention an election</b> · gold: presidential election years</div>{c7}',
        f'Shares of all stories each year; the other years from 1789 run from {min(near):.1f}% to {max(near):.1f}%. Five election years make a short series, so this is a pattern to read, not a tested cycle.',
        'Which elections: state and congressional elections fill the other years, and the words cannot tell them apart.',
        [('Trace elections in the sky', 'telescope.html?q=' + quote(ELECT) + '&lookback=all')],
        table([(y, el_y[y], f'{per_year[y]:,}', f'{esh[y]:.1f}%', 'presidential' if y in terms else '') for y in span_y], ['Year', 'Election stories', 'All stories', 'Share', ''])))
    return '\n'.join(out)


def archive(e, repo):
    """What reading found wrong in the archive itself, for the people who keep it: the counts and examples of
    outputs/archive_errata/summary.json (work/archive_errata.py), every case in the two tables in the public repository."""
    p, d, t, x = e['pages'], e['dates'], e['transcription'], e['examples']
    a, k, base = t['audit'], d['kentucky'], f'{repo}/blob/main/docs/archive-errata/'
    pct = lambda n, of: f'{100 * n / of:.0f}%'
    years = t['years']; yt = ', '.join(map(str, years[:-1])) + f' and {years[-1]}'
    n_filing = p['issues'] + d['issues'] + e['second_scan']['issues']
    rep = p['by_kind'].get('duplicate', 0)
    items = [
        ('Transcriptions filed under the wrong page',
         f'In {p["issues"]} issues of {p["newspapers"]} newspapers, {p["years"][0]} to {p["years"][1]}, the machine transcription (RevX) of a page '
         f'is filed under another page of its issue. Mostly one scan page has no transcription and the later pages’ text sits one page early; '
         f'in {rep} issues a page’s text is filed twice. In all, {p["pages_without_revx"]:,} of the archive’s {p["all_pages"]:,} pages have no RevX transcription.',
         'Each page’s RevX text compared with the Library of Congress OCR of every page of its issue.',
         f'Moved to the true pages in data release v{p["release"]}: {p["matched_printings_on_a_wrong_page"]} printings of the matched stories.',
         ('filing.csv', f'{p["issues"]} issues')),
        ('Issues filed under the wrong date',
         f'{k["issues"]} issues of the Kentucky Gazette and General Advertiser filed under 1806 to 1808 were printed two years earlier: '
         f'the {k["by_year"].get("1808 -> 1806", 0)} filed under 1808 are of 1806. Two issues of the Gazette of the United States are filed away from their '
         'mastheads: 4 April 1793 for 4 May, and 23 July for 13 July.',
         f'Reading the masthead of every front page: {k["by_basis"]["masthead"]} by their dates, {k["by_basis"]["two-year rule"]} by the paper’s '
         f'publication days, {k["by_basis"]["scan"]} on the scans.',
         f'The Kentucky Gazette is dated as printed in data release v{d["release"]}; the two issues of 1793 are not corrected.',
         ('filing.csv', f'{d["issues"]} issues')),
        ('A second scan filed under another day',
         'Pages 3 and 4 filed under the American Herald of Liberty of 2 July 1793 are a second scan of the pages of 9 July: '
         'page 3 prints the heading ‘EXETER, TUESDAY, JULY 9, 1793’.',
         'Datelines later than the issue a page is filed under.',
         'Not corrected; no reviewed printing stands on it.',
         ('filing.csv', '1 issue')),
        ('Transcriptions that change what was printed',
         f'Of {t["checked"]} printings read against their scans in {yt}, {t["changes_what_was_printed"]} ({pct(t["changes_what_was_printed"], t["checked"])}) '
         f'carry a misreading or a gap that changes what the text says; in a random sample of the matched stories, '
         f'{pct(a["own_calls"], a["located"])} to {pct(a["strict_rule"], a["located"])} of passages (finding 2). The machine read ‘slaves’ for ‘ſtaves’ in '
         f'{len(x["staves"]["printings"])} of the {x["staves"]["of"]} printings of the resolution opening the ports (1776), ‘NECESSARY INFORMATION!!’ '
         'for ‘WAR INEVITABLE!!!’ (1807), and ‘Juan’ for Junot and ‘MANUEL’ for Murat (1808).',
         'Each printing read against its scan, under one written rule.',
         'The reviewed passages keep the machine’s text, and their notes name each error. The matched stories carry an automatic check only.',
         ('transcription.csv', f'{t["changes_what_was_printed"]} printings, with the reviewers’ notes')),
        ('Printed text left out',
         f'{t["leaves_out_text"]} of those {t["changes_what_was_printed"]} leave printed text out, often behind a bare ‘...’. In the King’s speech of '
         f'October 1775, as the {x["leaves_out"]["name"]} printed it on {x["leaves_out"]["day"]}, the transcription stops at ‘the true constitution of the '
         'colonies...’, where the print goes on ‘and to their subordinate relation to Great-Britain, now openly avow their revolt, hostility and rebellion’.',
         'The same reading against the scans.',
         'Marked in the table.',
         ('transcription.csv', f'{t["leaves_out_text"]} printings')),
        ('Printers’ slips silently corrected',
         f'The transcription tidies what the printer set wrong: ‘U. STAES’ in the {x["staes"]["name"]} of {x["staes"]["day"]} becomes ‘U. STATES’, '
         'and ‘Andersecht’, as the papers printed it in 1793, ‘Anderlecht’. A tidied text reads well, but it cannot show a misprint, '
         'or tell one printing from another by its slips.',
         'Noticed while reading; not counted.',
         'Listed among the minor errors in the reviewers’ notes.',
         None)]
    cards = ''.join(
        f'<article><h3>{esc(title)}</h3><p>{esc(text)}</p><dl><dt>Found by</dt><dd>{esc(found)}</dd><dt>Here</dt><dd>{esc(here)}</dd></dl>'
        + (f'<a class="csv" href="{esc(base + lst[0])}">{esc(lst[0])} · {esc(lst[1])}</a>' if lst else '') + '</article>'
        for title, text, found, here, lst in items)
    return (f'<section class="errata" id="archive" aria-labelledby="archive-title"><h2 class="part" id="archive-title">What we found wrong in the archive</h2>'
            '<p class="lede-s">Reading the papers against their scans turned up errors in the archive itself, in where pages and issues are filed and in what '
            'the machine transcriptions say. They are set out here for the people who keep the archive, with every case in a table that can be checked '
            f'on its scan.</p><div class="ecards">{cards}</div>'
            f'<p class="lede-s">The tables: <a href="{esc(base)}filing.csv">filing.csv</a> ({n_filing} issues) and '
            f'<a href="{esc(base)}transcription.csv">transcription.csv</a> ({t["changes_what_was_printed"]} printings), described in '
            f'<a href="{esc(base)}README.md">their README</a>.</p></section>')
