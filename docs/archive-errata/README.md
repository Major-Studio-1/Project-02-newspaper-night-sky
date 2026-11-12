# Errors found in the archive

Reading the newspapers of the dataset [`RevolutionCrossroads/loc_chronicling_america_1770-1810`](https://huggingface.co/datasets/RevolutionCrossroads/loc_chronicling_america_1770-1810)
against their page scans turned up errors in the archive itself: pages and issues filed in the wrong place, and machine
transcriptions that change what was printed. They are listed here for the people who keep the archive, so that each case
can be checked on its scan and corrected at the source. The archive holds 77,793 pages in
19,445 issues and editions; each page has the Library of Congress's own OCR (called CA here) and
an AI transcription made for the Smithsonian's Revolution Crossroads (RevX).

Made by `pipeline/archive_errata.py` from the project's checks, 2026-11-12.

## `filing.csv`: 242 issues filed in the wrong place

One row per issue: the newspaper's LCCN and catalogue title, the date and edition the issue is filed under (and the
pages, where only some are concerned), what is wrong, how it was found, and what this project did about it.

| Problem | Issues |
|---|---|
| RevX transcriptions filed under the wrong page | 123 |
| Issue filed under the wrong date | 108 |
| RevX transcription repeated under another page | 10 |
| Second scan filed under another date | 1 |

- **Transcriptions filed under the wrong page.** Each page's RevX text was compared with the Library's OCR of every page
  of its issue, by the share of 4-word phrases they have in common; a page whose RevX text matches another page far
  better than its own is filed in the wrong place. Mostly one scan page has no RevX text, and every later page's text is
  filed one page early. In all, 1,494 of the 77,793 pages have no RevX
  transcription. The check: `pipeline/revx_page_shift_check/check_page_shift.py`.
- **Issues filed under the wrong date.** The masthead of every front page of the *Kentucky Gazette and General Advertiser* (sn84038147) was read:
  106 issues filed under 1806 to 1808 print a date two years earlier (98 filed under 1808 and printed in 1806; 7 filed under 1806 and printed in 1804; 1 filed under 1807 and printed in 1805):
  91 by their masthead dates, 13 where no masthead could be read by the
  paper's publication days, 2 on the scans. The check: `pipeline/kentucky_gazette_dates/check_dates.py`.
  Reading every front page of 1793 found two issues of the *Gazette of the United-States* filed away from their mastheads,
  both confirmed on the scans (`pipeline/story_discovery_1793/check_mastheads_1793.py`).
- **A second scan filed under another date.** Found by looking for datelines later than the issue a page is filed under
  (1793; `pipeline/story_discovery_1793/check_duplicate_pages_1793.py`).

## `transcription.csv`: 173 printings whose transcription changes what was printed

Every printing of the reviewed stories of 1776, 1793, 1806, 1807 and 1808 was read against its scan:
1551 printings, of which 173 (11%) carry a misreading
that changes a fact (a number, a date, a name, or a word with another meaning) or leave printed text out. One row per
printing: the newspaper, the date and page, which transcription the passage was taken from (RevX, or CA where RevX is
missing or misfiled), whether printed text is left out, and the reviewers' notes, mostly in the form
`scan '…' / transcription '…'`. A printing's notes may also list smaller errors beside the one that changes a fact.

| Year | Printings read | Changes what was printed |
|---|---|---|
| 1776 | 350 | 50 |
| 1793 | 135 | 9 |
| 1806 | 464 | 51 |
| 1807 | 282 | 36 |
| 1808 | 320 | 27 |

Examples: "ſtaves" read as "slaves" in 8 of the 9 printings of the resolution of
Congress opening the ports (1776); "WAR INEVITABLE!!!" read as "NECESSARY INFORMATION!!" (1807); "Junot" read as "Juan" and
"(MURAT.)" as "(MANUEL.)" (1808). 33 of the 173 leave printed text out, often
behind a bare "...".

The matched stories (found automatically, all years) were not read one by one. A random sample of 200 of
them was read against the scans: 35 of the 187 passages found
(19%) had a fact-changing misreading by the reviewers' own calls, and
64 (34%) under one strict rule.

## Also noticed, not counted

- **Printers' misprints are silently corrected.** "U. STAES" in the *Enquirer* of 7 July 1807 is
  transcribed "U. STATES", and "Andersecht" (1793) "Anderlecht". A tidied text reads well, but it cannot show a misprint,
  or tell one printing from another by its slips.

## What this project did

- Release v0.8.1 of the project's data moved the matched stories' printings to the pages their text is on
  (532 printings).
- Release v0.10.2 dates the *Kentucky Gazette and General Advertiser* as printed; its issue, page and scan ids keep the filed dates.
- The two 1793 issues and the second scan are not corrected; no reviewed printing stands on them.
- The reviewed passages keep the transcription as it is, and their notes name each error.

`summary.json` holds the counts and the examples the site's Findings page shows.
