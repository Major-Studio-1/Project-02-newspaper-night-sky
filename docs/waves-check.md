# Do stories come back in waves? (check of 11 November 2026)

The project began with the question of whether problems keep coming back. A check of cycle lengths, the same day ([the seasons check](seasons-check.md), "Other cycle lengths"), found that the year is the only fixed cycle in this archive. Many things come back irregularly instead, in waves. This check asks whether a plain rule can find those waves, using kinds of story whose history is known. Script: `pipeline/check_waves.py`.

## Method

- **Stories:** the telescope's stars, without the long-running texts, counted by year of first printing.
- **Shares:** each kind is matched by a keyword pattern on the title and opening words, then counted as a share of all stories of that year.
- **Thin years:** a year is judged only when it has at least 200 stories. The thinner years (1784–1786) are reported as "too little archive", never as quiet.
- **Wave year:** a year with at least 5 stories of the kind and a share at least twice the kind's usual share. The usual share is the median over the judged years in which the kind appears, so the waves do not raise their own bar.
- **Waves:** consecutive wave years form one wave.

## Results

| Kind | Stories | Waves found by the rule | History |
|---|---|---|---|
| Tripoli | 189 | 1801–1805 | the war, 1801–1805 |
| Embargo | 596 | 1794; 1796; 1798; 1801; 1808–1810 | the US embargoes of 1794 and 1807–1809 |
| Algiers | 292 | 1787–1788; 1794; 1796–1797; 1801–1802 (1784–1786: too little archive) | captures in 1785 and 1793, treaty 1795, release 1796–1797 |
| Yellow fever | 124 | 1793; 1798; 1801–1805 | epidemics in the northern ports 1793, 1795, 1797–1799, 1802–1803, 1805 |
| Fire (control) | 126 | 1773 (5 stories) | none expected |

- **The main waves are found.**
  - Tripoli is found exactly.
  - Both US embargoes are found, with 1808 the largest year: 267 stories, against 14 in 1807, when the act came only on 22 December.
  - So are the Algiers crisis of 1793–1797 and the great fever years of 1793, 1798 and 1802–1805.
- **The extra embargo waves are real news, not noise.**
  - 1796: Spain laid embargoes on British and Dutch ships after going to war with Britain.
  - 1798: French embargoes on American ships were feared.
  - 1801: Russia embargoed British ships, and Britain answered with an embargo on Russian, Swedish and Danish ships.
  - So the word came back with each European crisis. The rule traces the word, not the policy.
- **The control is flat.** The one stray year, 1773, has 5 stories. With at least 8 stories required, the control shows no wave, but the fever wave of 1798 (5 stories) and the embargo year 1798 (7) drop too.
- **Thin years are named as such.** Algiers stories exist in 1784–1786, but too few stories of any kind survive from those years to judge.

### Settings tried

| Setting | Effect |
|---|---|
| at least 5 stories, twice the usual share (above) | the main waves, and one stray control year |
| at least 8 stories | the control is clean; small waves (fever 1798, embargo 1798) drop |
| three times the usual share | too strict: fever keeps only 1802, and the Tripoli war splits |
| at least 300 stories to judge a year | the same waves |

## Reading it with care

- **Stories, not events.** It counts stories that were reprinted, not events. The smaller fever epidemics (1795, 1797, 1799) left too few reprinted stories to stand out.
- **The year is coarse.** Neighbouring waves merge: fever in 1801–1805 is one wave here, though the great epidemics were 1802–1803 and 1805.
- **Steady kinds have no waves.** A kind that is always present, such as Congress, has no waves by this rule. For the question "does it come back?" that is right.
- **Patterns are words.** The keyword pattern decides what counts; the stories themselves show what each wave was about.

## The rule the telescope uses (built 11 November 2026)

The first rule has fixed numbers (200 stories a year, 5 stories of the kind). Under "3+ newspapers" every count is about a third as large, so the telescope uses a rule that adapts to the filters ("counted" in `pipeline/check_waves.py`):

- **Judged years:** a year is judged when it holds at least a fifth of a typical (median) year's stories in view, so the same thin years stay thin under any filter.
- **Wave years:** a wave year has at least 3 matches, twice the usual share, and more than chance would give: P(X ≥ count) < .05, for a Poisson count with the usual share of that year's stories as its mean.
- **Usual share:** the lower of two measures, the median share over the judged years in which the kind appears, and its overall share. The median keeps a steady kind's background. The overall share serves a kind that appears only in bursts: with the median alone, Tripoli in 3+ newspapers kept only 1804, because its usual share was a war-year share.

| Kind | 2+ newspapers (all stories) | 3+ newspapers |
|---|---|---|
| Tripoli | 1801–1805 | 1801–1805 |
| Embargo | 1794; 1796; 1798; 1801; 1808–1810 | 1794; 1808–1809 |
| Algiers | 1787–1788; 1794; 1796–1797; 1801–1802 (1784–1786: too little archive) | 1787; 1794; 1801–1802 |
| Yellow fever | 1793; 1798; 1801–1805 | 1802; 1804 (35 stories) |
| Fire (control) | 1773 (5 stories, P just under .05) | none |

- **With all stories,** the waves are those of the first rule, and the control keeps its one borderline year. With 5 stories and a P near .05, that year cannot be told from a small real wave, such as fever in 1798 (5 stories, P .04).
- **With 3+ newspapers,** the counts are smaller, so only the strongest waves remain, and the control is clean.

Fewer stories means fewer waves can be told from chance, and the card always says which filter it counts.

On the telescope, a search's card now says how it comes back. Examples:

- "comes back in waves: 1794; 1796; 1801; 1808–1810";
- "no clear waves";
- "too few stories to judge waves" (fewer than 12 matches).

The thin years in which it has matches are named "too little archive to judge". A gold line above the timeline's yearly shares marks each wave, in each search's own colour when searches are compared. Pointing at a year on the timeline says when it is a wave year.
