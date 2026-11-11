"""Check of 11 November 2026 (outputs/story_discovery_all/waves_check.md). Run from the project root:
    python work/check_waves.py [MIN_PAPERS]

Do stories come back in waves, and can a plain rule find the waves? For a few kinds of story whose history is known
(yellow fever epidemics, the embargoes, the Barbary captives and war), plus fire as a control, this counts the stories
first printed each year (the telescope's stars, long-running texts left out), as a share of all stories of that year,
and marks the years a rule calls a wave. Two rules are compared with the known history:

- fixed (the first try): a year is judged when it has at least 200 stories; a wave year has at least 5 stories of the
  kind and a share at least twice the kind's usual share (the median over the judged years in which it appears).
- counted (the rule the telescope uses): a year is judged when it has at least a fifth of a typical year's stories
  (the median year), so the same thin years stay thin under any filter; a wave year has at least 3 stories of the kind,
  twice the usual share, and more than chance would give: P(X >= count) < .05 for a Poisson count with the usual share
  of that year's stories as its mean. Its usual share is the lower of the median share over the judged years in which
  the kind appears and its overall share: the first keeps a steady kind's background, the second a kind that appears
  only in bursts (with the median alone, Tripoli in 3+ papers kept only 1804). The telescope's search card and
  timeline use this rule (wavesOf in telescope.html)."""
import json, re, statistics, sys, math

SITE = 'outputs/newspaper_pulses_space'
d = json.load(open(SITE + '/telescope.json', encoding='utf-8'))
TEXT = json.load(open(SITE + '/telescope-text.json', encoding='utf-8'))['text']
MIN_PAPERS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
YEARS = range(1770, 1811)
keep = [i for i in range(d['count']) if not d['long'][i] and d['papers'][i] >= MIN_PAPERS]
all_y = {y: 0 for y in YEARS}
for i in keep: all_y[d['year'][i]] += 1

KINDS = {   # pattern on the title and opening words; the years history gives (for the comparison only)
    'Yellow fever': (r'yellow fever|malignant fever|prevailing fever|the fever|epidemic', '1793; 1795; 1797-1799; 1802-1803; 1805'),
    'Embargo': (r'\bembargo', '1794; 1807-1809 (US); foreign embargoes in the news 1796, 1798, 1801'),
    'Algiers': (r'\balgiers\b|\balgerine', '1785; 1793-1797'),
    'Tripoli': (r'\btripoli', '1801-1805'),
    'Fire (control)': (r'fire broke out|conflagration|was consumed by fire|destroyed by fire', 'none expected'),
}

def poisson_tail(k, lam):   # P(X >= k)
    if lam <= 0: return 0.0 if k > 0 else 1.0
    term, cdf = math.exp(-lam), 0.0
    for i in range(k): cdf += term; term *= lam / (i + 1)
    return max(0.0, 1 - cdf)

def runs(years):
    out = []
    for y in years:
        if out and y == out[-1][1] + 1: out[-1][1] = y
        else: out.append([y, y])
    return '; '.join(f'{a}' if a == b else f'{a}-{b}' for a, b in out) or 'none'

def waves(n_y, judge_min, min_n, test):
    judged = [y for y in YEARS if all_y[y] >= judge_min]
    share = {y: n_y[y] / all_y[y] for y in judged}
    usual = statistics.median([share[y] for y in judged if n_y[y]] or [0])
    if test: usual = min(usual, sum(n_y[y] for y in judged) / sum(all_y[y] for y in judged))   # the counted rule: also a kind that comes only in bursts
    wave = [y for y in judged if n_y[y] >= min_n and share[y] >= 2 * usual and (not test or poisson_tail(n_y[y], usual * all_y[y]) < .05)]
    thin = [y for y in YEARS if all_y[y] < judge_min and n_y[y]]
    return wave, thin, usual

typical = statistics.median(all_y.values())
print(f'stories in {MIN_PAPERS}+ papers: {len(keep)}; typical year {typical:.0f}; counted rule judges years with >= {typical / 5:.0f}\n')
for name, (pat, history) in KINDS.items():
    rx = re.compile(pat); n_y = {y: 0 for y in YEARS}
    for i in keep:
        if rx.search(TEXT[i]): n_y[d['year'][i]] += 1
    w1, t1, _ = waves(n_y, 200 * len(keep) / sum(1 for i in range(d['count']) if not d['long'][i]), 5, False)
    w2, t2, usual = waves(n_y, typical / 5, 3, True)
    print(f'{name}: {sum(n_y.values())} stories, usual share {100 * usual:.2f}%')
    print(f'  fixed:   {runs(w1)}' + (f'   (too little archive: {runs(t1)})' if t1 else ''))
    print(f'  counted: {runs(w2)}' + (f'   (too little archive: {runs(t2)})' if t2 else ''))
    print(f'  history: {history}\n')
