# Do stories come back at the same season? (check of 7 November 2026)

This check sits behind the telescope's **Orbit** and **Topic** views. Script: [`pipeline/check_cycles_topics.py`](../pipeline/check_cycles_topics.py). Numbers: [`seasons-check.json`](seasons-check.json).

## Method

- **Stories:** the 47,601 matched stories that are not long-running. Each is classed by a transparent keyword pattern on its title and opening words.
- **Rhythm test:** circular statistics on the day of year of first printing. R runs from 0 (spread evenly over the year) to 1 (all on one day); the Rayleigh p-value tests whether the clustering could be chance.
- **Coverage check:** the archive's surviving pages are spread almost perfectly evenly over the year (R = 0.007). So a rhythm here is not produced by which months survive.

## Results

| Kind of story | Stories | Rhythm (R) | When | Years following the season |
|---|---|---|---|---|
| Independence Day | 119 | 0.71 | 81% in Jul–Sep | 25 of 30 |
| Thanksgiving | 25 | 0.72 | Oct–Jan | 12 of 15 |
| President's annual speech or message | 84 | 0.50 | Nov–Jan | 17 of 17 |
| Ice, frozen rivers | 45 | 0.48 | winter–spring | 15 of 25 |
| Fever, epidemic | 122 | 0.43 | Jul–Sep | 17 of 26 |
| Congress proceedings | 1,474 | 0.33 | Dec–May high, Aug–Oct low | 37 of 41 |
| Hurricanes, gales | 150 | 0.28 | Sep–Oct | 24 of 36 |
| Elections | 764 | 0.16 | Nov–Dec, weak | 34 of 40 |
| **Fire** (control) | 124 | 0.05, no rhythm | — | — |

- **All stories together (3+ papers):** a mild summer rise. August runs at 1.18 times what the surviving pages would predict, and winter at about 0.9.
- **Four-year rhythm:** words about the presidential election, October–December, per 1,000 surviving pages:

  | | 1792 | 1796 | 1800 | 1804 | 1808 |
  |---|---|---|---|---|---|
  | Election year | 11.9 | 4.7 | 35.0 | 13.7 | 16.5 |
  | Year before / after | 2.6 / 0.0 | 10.6 / 0.0 | 2.8 / 11.7 | 6.6 / 6.7 | 1.0 / 0.8 |

  The rhythm is clear from 1800, weak or absent earlier, and rests on small counts.
- **Topics as a layout:** in a sample of 4,000 stories with 3 or more printings, printings of the same story share their story's top topic 76% of the time; chance would be about 7%. Across all stories with 2 or more printings it is 89%.

## Reading it with care

- The keyword classes are simple patterns. They catch some unrelated uses, such as "epidemic folly", and miss printings whose wording differs.
- The test is about when stories were **first printed in this archive**, not when events happened.
- A strong rhythm says something comes back at the same season. It does not say why.
