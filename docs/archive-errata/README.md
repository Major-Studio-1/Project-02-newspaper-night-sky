# Errors found in the archive

Reading the newspapers of the dataset [`RevolutionCrossroads/loc_chronicling_america_1770-1810`](https://huggingface.co/datasets/RevolutionCrossroads/loc_chronicling_america_1770-1810)
against their page scans turned up errors in the archive itself: pages and issues filed in the wrong place, and machine
transcriptions that change what was printed. They are listed here for the people who keep the archive, so that each case
can be checked on its scan and corrected at the source. The archive holds 77,793 pages in
19,445 issues and editions; each page has the Library of Congress's own OCR (called CA here) and
an AI transcription made for the Smithsonian's Revolution Crossroads (RevX).

Made by `pipeline/archive_errata.py` from the project's checks, 2026-11-25.

## `filing.csv`: 571 issues filed in the wrong place

One row per issue: the newspaper's LCCN and catalogue title, the date and edition the issue is filed under (and the
pages, where only some are concerned), what is wrong, how it was found, and what this project did about it.

| Problem | Issues |
|---|---|
| Issue filed under the first day of its range | 162 |
| Second copy filed as another edition | 131 |
| RevX transcriptions filed under the wrong page | 124 |
| Issue filed under the wrong date | 122 |
| Second scan filed under another date | 13 |
| RevX transcription repeated under another page | 10 |
| Pages filed in another issue | 7 |
| Second scan filed under another title | 2 |

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
  both confirmed on the scans (`pipeline/story_discovery_1793/check_mastheads_1793.py`). The review of 1802 found seven
  issues of the *National Intelligencer* filed away from their mastheads, read on the scans
  (`pipeline/filing_corrections_1802/check_ni_1802.py`).
- **Second scans filed under another date.** Found by looking for datelines later than the issue a page is filed under
  (1793; `pipeline/story_discovery_1793/check_duplicate_pages_1793.py`), and by the masthead of an issue filed under
  24 November 1802 that prints 24 December (1802; `pipeline/filing_corrections_1802/check_ni_1802.py`).
- **Pages filed in another issue.** Pages 3 and 4 of the *National Intelligencer* of 9 July and 8 September 1806 are filed
  in each other's issues: found by their datelines and by comparing each page with its neighbours (1806;
  `pipeline/story_discovery_1806/check_duplicate_pages_1806.py`, `pipeline/story_discovery_1806/check_page_neighbours_1806.py`).
- **Found by the reviews of the years with few surviving papers (319 issues).** The reviews of 1770 to 1799
  (read on 23 and 24 November 2026), the review of 1801 and a check of every masthead of 1784, 1785 and 1786 on the scans
  found 162 issues filed under the first day of the range of days their mastheads print; 131 second copies of an issue filed as another edition; 11 second scans filed under another date; 7 issues filed under the wrong date; 5 issues holding pages of another issue or sheet; 2 second scans filed under another title; 1 issue whose RevX transcriptions are filed under the wrong page.
  Two papers, the *Connecticut Courant* of 1773-74 and the *Royal Gazette* of Charleston of 1781-82, head each issue with a
  range of days and are filed under its first day, though each appeared on its last; the collection files other such papers
  under the last day. Data release v0.11.40 corrects 296 of these issues and v0.11.41 corrects the other 23 (`pipeline/errata_1784_1786/`).

## `transcription.csv`: 762 printings whose transcription changes what was printed

Every printing of the reviewed stories of 1770, 1771, 1772, 1773, 1774, 1775, 1776, 1777, 1778, 1779, 1780, 1781, 1782, 1783, 1787, 1788, 1789, 1790, 1791, 1792, 1793, 1794, 1795, 1796, 1797, 1798, 1799, 1800, 1801, 1802, 1803, 1804, 1805, 1806, 1807, 1808, 1809 and 1810 was read against its scan:
6390 printings, of which 760 (12%) carry a misreading
that changes a fact (a number, a date, a name, or a word with another meaning) or leave printed text out. For 1797 the count is the 33 printings of its later reading; its other 108 were checked against their scans before verdicts were recorded in this form. One row per
printing: the newspaper, the date and page, which transcription the passage was taken from (RevX, or CA where RevX is
missing or misfiled), whether printed text is left out, and the reviewers' notes, mostly in the form
`scan '…' / transcription '…'`. A printing's notes may also list smaller errors beside the one that changes a fact.

| Year | Printings read | Changes what was printed |
|---|---|---|
| 1770 | 12 | 1 |
| 1771 | 4 | 1 |
| 1772 | 52 | 2 |
| 1773 | 212 | 16 |
| 1774 | 159 | 21 |
| 1775 | 212 | 24 |
| 1776 | 350 | 50 |
| 1777 | 186 | 35 |
| 1778 | 161 | 22 |
| 1779 | 162 | 14 |
| 1780 | 142 | 21 |
| 1781 | 144 | 7 |
| 1782 | 166 | 17 |
| 1783 | 113 | 16 |
| 1787 | 54 | 8 |
| 1788 | 30 | 1 |
| 1789 | 24 | 2 |
| 1790 | 20 | 0 |
| 1791 | 98 | 6 |
| 1792 | 146 | 15 |
| 1793 | 135 | 9 |
| 1794 | 192 | 12 |
| 1795 | 102 | 14 |
| 1796 | 116 | 31 |
| 1797 | 33 | 3 |
| 1798 | 126 | 8 |
| 1799 | 205 | 28 |
| 1800 | 182 | 25 |
| 1801 | 160 | 25 |
| 1802 | 132 | 23 |
| 1803 | 238 | 30 |
| 1804 | 296 | 49 |
| 1805 | 243 | 26 |
| 1806 | 464 | 51 |
| 1807 | 282 | 36 |
| 1808 | 320 | 27 |
| 1809 | 495 | 60 |
| 1810 | 222 | 24 |

Examples: "ſtaves" read as "slaves" in 8 of the 9 printings of the resolution of
Congress opening the ports (1776); "WAR INEVITABLE!!!" read as "NECESSARY INFORMATION!!" (1807); "Junot" read as "Juan" and
"(MURAT.)" as "(MANUEL.)" (1808). 188 of the 760 leave printed text out, often
behind a bare "...".

No review read 1784, 1785 or 1786 (too few papers survive for any item to reach the bar), so these years were checked on a
sample, for this list only: every printing of the eleven texts the count of 1784 found in two or three papers, and for each
month of 1785 and 1786 the first passage both surviving papers printed, chosen by that rule before any checking
(`pipeline/errata_1784_1786/`). It is a sample of reprinted items, chosen so that each month and both papers are covered, not
every page, so its rate is not the archive's. Its rows in `transcription.csv` have printing ids E84-, E85- and E86-, and
their notes say "Checked for the errata only"; they are not in the counts above.

| Year | Sample | Printings read | Changes what was printed |
|---|---|---|---|
| 1784 | 33 | 33 | 0 |
| 1785 | 20 | 20 | 2 |
| 1786 | 22 | 22 | 0 |

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
- Release v0.11.7 dates the two 1793 issues as printed, files the 1806 pages under the issues they belong to, and leaves the
  second scan out of the analysis (77,747 usable pages rather than 77,749). One reviewed printing stands on a corrected
  page: Captain Fanning's account of 1793, which takes its issue's printed date, 13 July.
- Release v0.11.40 dates 169 issues as printed or issued (162 of them dated by the last day of their ranges),
  files 16 pages with the issues they belong to (12 of them in four issues the collection did not hold), and leaves 347
  pages of second scans and second copies out of the analysis (77,743 usable pages become 77,396). The reviewed printings
  on corrected pages take their issues' dates.
- Release v0.11.41 leaves out 65 more pages of second copies, read on their scans (77,396 usable pages become 77,331), and
  adds the Patowmac Guardian's RevX pages of 12 May 1796 to the RevX page map, read on their scans (`pipeline/corrections_0_11_41/`).
- The reviewed passages keep the transcription as it is, and their notes name each error.

`summary.json` holds the counts and the examples the site's Findings page shows.
