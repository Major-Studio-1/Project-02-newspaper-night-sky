"""Evidence check behind the telescope's Orbit and Topic views (2026-11-07).

Results: outputs/story_discovery_all/cycles_check.md (and cycles_check.json).
Run from the project root with Python 3.12:  python work/check_cycles_topics.py

1. Yearly cycles: do some kinds of matched stories cluster at the same time of year, beyond what the archive's
   monthly page coverage would produce? Circular statistics on day of year, coverage-weighted month index.
2. Four-year cycle: do election stories peak in presidential election years?
3. Content layout: do printings of the same story get the same topic from the project's frozen 24-topic model?
Reads the pulse page's year files (outputs/newspaper_pulses_space/years/) and the current data release.
"""
from pathlib import Path
import collections, datetime, json, math, random, re, sqlite3, sys

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / 'work' / 'python_packages'))
import numpy as np

stories = []
for f in sorted((PROJ / 'outputs/newspaper_pulses_space/years').glob('*.json')):
    d = json.loads(f.read_text(encoding='utf8'))
    obs = {o['id']: o for o in d['observations']}
    for g in d['groups']:
        if g['long_running']:
            continue
        ex = [obs[m]['excerpt'] for m in g['members']]
        stories.append({'id': g['id'], 'first': g['first'], 'papers': g['newspapers'], 'title': g['label'], 'excerpts': ex,
                        'text': (g['label'] + ' ' + ex[0]).lower()})
print('stories (not long-running):', len(stories))

# Archive coverage: surviving pages by month of year (all years), to normalise counts.
REL = PROJ / 'outputs/data_foundation' / json.loads((PROJ / 'outputs/data_foundation/CURRENT.json').read_text())['path']
db = sqlite3.connect((REL / 'research.sqlite').as_uri() + '?mode=ro', uri=True)
pages_m = collections.Counter()
for date, pages in db.execute('SELECT publication_date, SUM(observed_pages) FROM newspaper_date_coverage GROUP BY publication_date'):
    pages_m[int(date[5:7])] += pages
tot_pages = sum(pages_m.values())


def doy_angle(date):
    d = datetime.date.fromisoformat(date)
    start = datetime.date(d.year, 1, 1); n = (datetime.date(d.year + 1, 1, 1) - start).days
    return 2 * math.pi * (d - start).days / n


def rayleigh(angles):
    n = len(angles)
    if n < 5:
        return 0, 1, None
    C, S = sum(math.cos(a) for a in angles), sum(math.sin(a) for a in angles)
    Rn = math.hypot(C, S); R = Rn / n
    p = math.exp(math.sqrt(1 + 4 * n + 4 * (n * n - Rn * Rn)) - (1 + 2 * n))
    return R, p, math.atan2(S, C) % (2 * math.pi)


# Coverage's own concentration (what a story stream would show if it simply followed surviving pages).
cov_angles = []
for date, pages in db.execute('SELECT publication_date, SUM(observed_pages) FROM newspaper_date_coverage GROUP BY publication_date'):
    cov_angles += [doy_angle(date)] * int(pages)
R_cov, _, mean_cov = rayleigh(random.Random(1).sample(cov_angles, 20000))
print(f'archive pages: R={R_cov:.3f} (how uneven surviving pages are over the year)')


def month_index(sel):
    m = collections.Counter(int(s['first'][5:7]) for s in sel)
    n = len(sel)
    return {k: round((m[k] / n) / (pages_m[k] / tot_pages), 2) for k in range(1, 13)}


all3 = [s for s in stories if s['papers'] >= 3]
print('\nALL stories in 3+ papers, month index (1.0 = as expected from surviving pages):')
print(month_index(all3))

CLASSES = {
    'Independence day (4th of July)': r'anniversary of (?:american |our )?independence|fourth of july|4th of july|anniversary of the declaration',
    'Fever / epidemic': r'yellow fever|malignant fever|prevailing fever|the fever|epidemic',
    "President's annual speech / message": r'fellow.citizens of the senate and (?:of the )?house|gentlemen of the senate and (?:of the )?house|president.s (?:speech|message)',
    'Thanksgiving proclamation': r'thanksgiving',
    'Elections, electors': r'\belection|\belectors\b|\bpolls?\b',
    'Hurricane, gale': r'hurricane|violent gale|severe gale|tremendous gale',
    'Ice, frozen river / harbour': r'\bthe ice\b|frozen|navigation is (?:now )?(?:closed|obstructed)',
    'Fire': r'fire broke out|conflagration|was consumed by fire|destroyed by fire',
    'Congress proceedings': r'house of representatives|in senate|in congress',
    'Prices current / markets': r'prices current|price of flour|flour, per barrel',
}
results = {'archive_pages_R': round(R_cov, 4), 'classes': {}}
for name, rx in CLASSES.items():
    sel = [s for s in stories if re.search(rx, s['text'])]
    R, p, mean = rayleigh([doy_angle(s['first']) for s in sel])
    if mean is None:
        continue
    peak = int(mean / (2 * math.pi) * 12) % 12 + 1
    window = {((peak - 2) % 12) + 1, peak, (peak % 12) + 1}
    in_peak = [s for s in sel if int(s['first'][5:7]) in window]
    years_all = {s['first'][:4] for s in sel}; years_peak = {s['first'][:4] for s in in_peak}
    results['classes'][name] = dict(n=len(sel), R=round(R, 3), p=p, peak_month=peak, share_peak=round(len(in_peak) / len(sel), 2),
                                    years=len(years_all), years_with_peak=len(years_peak), month_index=month_index(sel), regex=rx)
    print(f"{name:38s} {len(sel):5d} R={R:.2f} p={p:.1e} peak={peak:2d} share3={len(in_peak) / len(sel):.2f} years {len(years_peak)}/{len(years_all)}")

# Four-year cycle: election stories in Oct-Dec, by year, against pages in Oct-Dec of that year.
pages_y = collections.Counter()
for date, pages in db.execute("SELECT publication_date, SUM(observed_pages) FROM newspaper_date_coverage WHERE substr(publication_date,6,2) IN ('10','11','12') GROUP BY publication_date"):
    pages_y[int(date[:4])] += pages
el = collections.Counter(int(s['first'][:4]) for s in stories if re.search(r'\belectors?\b|president(?:ial)? election|election of (?:a )?president', s['text']) and s['first'][5:7] in ('10', '11', '12'))
results['election_words_oct_dec_per_1000_pages'] = {y: round(1000 * el[y] / pages_y[y], 1) for y in range(1786, 1811) if pages_y[y]}
print('\nPresidential-election words in Oct-Dec, per 1,000 surviving pages:', results['election_words_oct_dec_per_1000_pages'])

# Content layout: do printings of the same story get the same top topic?
import joblib
tm = joblib.load(PROJ / 'work/topic_model.joblib')
vec, nmf = tm['vectorizer'], tm['model']
topics = json.loads((PROJ / 'outputs/topic_pilot.json').read_text(encoding='utf8'))['topics']
names = [t['topic_id'] + ' ' + '/'.join(t['top_terms'][:3]) for t in topics]
multi = [s for s in stories if len(s['excerpts']) >= 3]
sample = random.Random(5).sample(multi, min(4000, len(multi)))
agree, total = 0, 0
story_topic = collections.Counter()
for s in sample:
    top = nmf.transform(vec.transform(s['excerpts'])).argmax(axis=1)
    maj = collections.Counter(top.tolist()).most_common(1)[0][0]
    agree += int((top == maj).sum()); total += len(top); story_topic[maj] += 1
freqs = np.array([story_topic[k] for k in range(len(names))], float); freqs /= freqs.sum()
results['topic_agreement_3plus_printings_sample'] = round(agree / total, 3)
results['topic_agreement_chance'] = round(float((freqs ** 2).sum()), 3)
print(f"\nTopic agreement between printings of the same story: {agree / total:.2f} (chance about {float((freqs ** 2).sum()):.2f})")
(PROJ / 'outputs/story_discovery_all/cycles_check.json').write_text(json.dumps(results, indent=1, default=str), encoding='utf8')
