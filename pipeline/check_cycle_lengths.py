"""Check of 11 November 2026 (outputs/story_discovery_all/cycles_check.md, "Other cycle lengths"). Run from the project root.

Which cycle lengths does the data support? For each tested kind of story, scan every period from 6 to 400 days.

Each kind is compared with the archive's own stories within each year: the expected count on a day is that year's
number of stories of the kind, spread like all stories of that year. This removes the newspapers' printing days (a
weekly pattern of the archive, not of the news) and the eras (more fever in the 1790s). What remains is a rhythm of
the kind itself. The spectrum of the difference is compared with 300 random draws of the same number of stories per
year from all stories; the best period's p-value is taken against the best period of each draw, so scanning many
periods is paid for (no hunting in noise)."""
import sys, json, re, datetime
sys.path.insert(0, 'work/python_packages')
import numpy as np

SITE = 'outputs/newspaper_pulses_space'
d = json.load(open(SITE + '/telescope.json', encoding='utf-8'))
TEXT = json.load(open(SITE + '/telescope-text.json', encoding='utf-8'))['text']
first = np.array(d['first']); keep = np.array(d['long']) == 0
EPOCH = datetime.date(1770, 1, 1)
L = int(first.max()) + 1
year_of_day = np.array([(EPOCH + datetime.timedelta(days=int(t))).year for t in range(L)])
idx = np.flatnonzero(keep); days_all = first[idx]
base = np.bincount(days_all, minlength=L).astype(float)
yb = {y: base[year_of_day == y].sum() for y in range(1770, 1811)}
days_by_year = {y: days_all[year_of_day[days_all] == y] for y in range(1770, 1811)}

KINDS = {  # the cycles check's patterns (work/check_cycles_topics.py), on the title and opening words
    'Independence Day': r'anniversary of (?:american |our )?independence|fourth of july|4th of july|anniversary of the declaration',
    'Fever': r'yellow fever|malignant fever|prevailing fever|the fever|epidemic',
    "President's speech": r'fellow.citizens of the senate and (?:of the )?house|gentlemen of the senate and (?:of the )?house|president.s (?:speech|message)',
    'Thanksgiving': r'thanksgiving',
    'Elections': r'\belection|\belectors\b|\bpolls?\b',
    'Hurricanes': r'hurricane|violent gale|severe gale|tremendous gale',
    'Ice': r'\bthe ice\b|frozen|navigation is (?:now )?(?:closed|obstructed)',
    'Fire (control)': r'fire broke out|conflagration|was consumed by fire|destroyed by fire',
    'Congress': r'house of representatives|in senate|in congress',
    'Prices current': r'prices current|price of flour|flour, per barrel',
}
NFFT = 1 << 16
k_lo, k_hi = int(NFFT / 400), int(NFFT / 6) + 1          # periods 400 down to 6 days
named = {'week': 7, 'fortnight': 14, 'month': 30.4375, 'quarter': 91.31, 'half-year': 182.62, 'year': 365.2425}
kn = {k: int(round(NFFT / p)) for k, p in named.items()}
rng = np.random.default_rng(20261111)

def spectrum(counts, per_year):
    e = np.zeros(L)
    for y, n in per_year.items():
        if n: m = year_of_day == y; e[m] = n * base[m] / yb[y]
    return np.abs(np.fft.rfft(counts - e, n=NFFT)) ** 2

for name, pat in KINDS.items():
    rx = re.compile(pat)
    hit = [i for i in idx if rx.search(TEXT[i])]
    t = first[hit]; n = len(t)
    per_year = {y: int((year_of_day[t] == y).sum()) for y in range(1770, 1811)}
    obs = spectrum(np.bincount(t, minlength=L).astype(float), per_year)
    band = obs[k_lo:k_hi]; kbest = k_lo + int(band.argmax())
    null_max, null_at = [], {k: [] for k in kn}
    for _ in range(300):
        draw = np.concatenate([rng.choice(days_by_year[y], size=c, replace=True) for y, c in per_year.items() if c])
        s = spectrum(np.bincount(draw, minlength=L).astype(float), per_year)
        null_max.append(s[k_lo:k_hi].max())
        for k, j in kn.items(): null_at[k].append(s[j])
    null_max = np.array(null_max)
    p_best = (1 + (null_max >= band.max()).sum()) / 301
    # a peak counts if it beats the best of the random draws 95 times in 100: list the distinct ones
    thr = np.quantile(null_max, .95); peaks = []
    for j in np.argsort(band)[::-1]:
        if band[j] < thr or len(peaks) >= 4: break
        per = NFFT / (k_lo + j)
        if all(abs(per - q) / q > .03 for q in peaks): peaks.append(per)
    pts = {k: (1 + (np.array(null_at[k]) >= obs[j]).sum()) / 301 for k, j in kn.items()}
    print(f"{name:20} n={n:5}  best {NFFT / kbest:7.1f} d (p {p_best:.3f})  periods past the scan bar: "
          + (', '.join(f'{q:.1f}' for q in peaks) or 'none')
          + '  | single-period p: ' + ' '.join(f"{k} {v:.3f}" for k, v in pts.items()))
