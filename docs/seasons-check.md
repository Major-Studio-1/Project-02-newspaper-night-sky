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

## Other cycle lengths (check of 11 November 2026)

Could the Orbit offer cycles other than the year (a week, a month, any number of days), or suggest the best one for a search? Script: `pipeline/check_cycle_lengths.py`.

- **Method.** For each kind of story above, every period from 6 to 400 days is scanned.
  - Each kind is compared with the archive's own stories within each year, so the newspapers' printing days (a weekly pattern of the archive) and the eras (more fever in the 1790s) cancel out.
  - The comparison is against 300 random draws with the same number of stories per year.
  - The best period's p-value is taken against the best period of each draw, which pays for scanning many periods.

| Kind of story | Stories | Strongest period | p | Week (7 days), p |
|---|---|---|---|---|
| Independence Day | 119 | 364 days | 0.003 | 0.96 |
| Fever | 124 | 358 days | 0.003 | 0.55 |
| President's speech | 87 | 364 days | 0.003 | 0.96 |
| Thanksgiving | 25 | 364 days | 0.003 | 0.42 |
| Elections | 769 | 366 days | 0.003 | 0.95 |
| Ice | 45 | 366 days | 0.043 | 0.79 |
| Congress | 1,486 | 364 days | 0.003 | 0.06 |
| Hurricanes | 152 | 150 days | 0.013 | 0.69 |
| Fire (control) | 126 | 8 days | 0.146 | 0.10 |
| Prices current | 23 | 8 days | 0.063 | 0.94 |

0.003 is the smallest p-value that 300 draws can give.

- **Every kind with a rhythm peaks at one year.** None has a weekly or monthly rhythm of its own.
- **The other periods that pass are echoes of the year.** These are half a year, a quarter, about two months, and a month for Independence Day. A sharp yearly peak, such as the Fourth of July, leaves its trace at a half, a third, and so on down to a twelfth of a year.
- **The hurricanes' 150 days is weak.** It is one result among ten kinds at p 0.013, as likely chance as not. Their yearly season is clear (p 0.007 at one year).
- **Fire, the control, has no rhythm.**
- **Four years.** The presidential term shows in the yearly share of election stories from 1800: 3.8% in 1800, 3.4% in 1804 and 3.8% in 1808, against 0.8–2.3% in the neighbouring years. Before 1800 it is weaker: 2.3% in 1792 and 1.4% in 1796. 1802 is also high, at 3.2%.
- **So:** a free choice of cycle length would mostly show the newspapers' printing days (a week) or echoes of the year, and a suggested best cycle would almost always be the year. The Orbit keeps the year.
