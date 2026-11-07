# Publication pulses: newspaper nodes, observed appearances

Updated 3 November 2026 following the user's clarification. **This display records appearances. It does not build reprint relationships.**

The observation unit is a newspaper series, a publication date, and an identified passage assigned to a selected message/event group. Each appearance produces a pulse at that newspaper's fixed node. Every observed repeat remains visible. No connecting edge or origin-to-destination movement is needed. Determining who copied whom is not a prerequisite.

The observable fact is that the newspaper printed the passage. Its contents may be reports, claims, commentary or challenges; the pulse does not certify the truth of the reported event.

## An immediately usable first sequence

| Publication date | Newspaper | Observed content |
|---|---|---|
| 16 March 1797 | Patowmac Guardian | Boyd fleet report |
| 25 March 1797 | New Hampshire Gazette | Corresponding report with an appended CHRONICLE challenge |
| 12 April 1797 | Kentucky Gazette | Corresponding core report |
| 19 April 1797 | Kentucky Gazette | Later related account describing the main body's return to Brest |

These give three newspaper nodes and four dated observations. The 25 March item contains a report and a challenge together. The 19 April item is not an explicit retraction. Store historical phases as unassigned unless suitable evidence is later added.

## Visual rules

- Keep newspaper positions fixed; advance a visible publication-date cursor.
- Pulse the node for each admitted appearance. Use equal initial brightness for the first prototype; a short fade is a playback aid, not an estimate of attention or event duration.
- In a multi-event view, color can identify the selected message group. In a focused view, a ring or small label can distinguish report, commentary, challenge or explicit correction where these have been inspected. Avoid encoding both group and phase in the same color scale.
- Clicking a pulse opens its passage, publication date and original scan. Keep a persistent list of appearances alongside playback so viewers can pause and compare.
- Provide daily stepping, next-appearance stepping, speed control, and a static view showing all admitted appearances.
- Show archive availability separately. An unavailable date and an available page with no selected passage are different states. Neither automatically means the historical newspaper was silent.

The remaining prerequisite is reliable grouping: deciding which passages concern the selected event or message. This is different from deciding copying direction. Begin with the inspected four-observation sequence; do not turn the 24 broad model topics or every automated shared-text pair directly into a unique event.

[Prepared observations and coverage dates](pulse_seed.json) · [Research reading notebook](reading_notebook.html)

The seed contains three nodes, four observations, no edges, and 35 newspaper/date cells with observed eligible pages during March–April 1797. An animated prototype has now been built, followed by a [standalone dark pulse page](../newspaper_pulses_space/index.html) with faster playback. The separate reuse sensitivity study is retained as a research note, not a dependency of this display. See the [4 November research plan](../research_plan_2026-11-04.en.md) for the proposed expansion and current status.
