# Pipeline

This folder holds the code that turns the archive into the data release and the website, in the order it runs. It uses Python 3.12, with the packages in [`requirements.txt`](requirements.txt).

> **These are the project's working scripts, copied as they are.** They keep the working folder layout: scripts and the raw dataset in `work/`, results in `outputs/`.
>
> They are here so you can read how each step was done. To run the whole chain again you need the dataset: six Parquet files, about 1.8 GB, downloaded from Hugging Face at the pinned revision. You also need that layout: put this folder's contents in `work/` and run each script from the folder above it.

## 1 · Audit and topics

| Script | What it does |
|---|---|
| `audit_dataset.py` | Checks the six dataset files against their published checksums. Applies the usability rule (at least 200 words in one transcription) and flags duplicate pages. Counts coverage by year and newspaper. |
| `discover_topics.py` | Samples 4,100 pages, at most 100 per year and spread across the papers, and cuts them into 220-word passages. Fits the 24-topic model (TF-IDF and NMF), then fits it a second time from another random start to check stability. |
| `recheck_full_corpus.py` | Applies the frozen model to all 77,749 usable pages without refitting, for trend checks, and runs the phrase-led evidence search. |

## 2 · Reviewed stories (1797)

| Script | What it does |
|---|---|
| `search_chains.py` | The first pilot, which searches both transcriptions for three message families in fixed date windows. |
| `search_pilot_1797.py` | Search for the two 1797 message dossiers, repeated with a recorded version. |
| `reuse_1797.py` | Text reuse in 1797. It compares five-word fingerprints, then aligns the texts word by word: at least 80 words, at least 70% similar, at most 120 days apart. |
| `reuse_families_1797.py` | Groups the 1797 matches into candidate story families, which were then read. |
| `story_phrase_search_1797.py` | Phrase searches over all 1797 pages, to find printings the matcher missed. |
| `scan_ledger.py` | Downloads the pinned scan of every passage in a ledger and crops the passage for checking. |
| `archive_data/ledgers/` | The review decisions. Each candidate is recorded as admitted, excluded or kept as a lead, with a reason and the scan findings. |

## 3 · Matched stories, all years

| Script | What it does |
|---|---|
| `reuse_all.py` | The same text-reuse method over all 41 years (`tokens`, then `match`). Takes hours. |
| `reuse_families_all.py` | Joins overlapping matches into 48,127 matched stories, and flags the long-running ones. |
| `reuse_titles_all.py` | Gives each story a title from the text printed just before its shared wording, so the title starts where the item starts. |
| `story_topics_all.py` | Applies the frozen topic model to every printing. A story takes its strongest topic. |
| `check_cycles_topics.py` | The seasons check behind the telescope's Orbit view ([results](../docs/seasons-check.md)). |
| `transcription_check.py` | Checks every printing against the page's other machine transcription: is the passage in both? |
| `audit_matched.py` | The audit of 200 random matched stories: draws the sample, cuts the scan crops, prepares the reviewers' batches and sums up their verdicts. |

## 4 · Data releases (`archive_data/`)

| Script | What it does |
|---|---|
| `build.py` | Builds the first release (v0.1.0) from the pinned project inputs. |
| `migrate_v0_2_0.py`, `apply_ledger.py` | Apply a reviewed ledger to the previous release to make the next one. |
| `apply_corrections.py` | Makes a correction release. It adds notes that supersede the old ones and never edits them; a few plain text fields can change, with the old value kept (v0.6.1, the English notes). |
| `add_reuse_layer.py`, `add_reuse_titles.py`, `add_story_topics.py` | Add the matched-story layers: v0.5.0, v0.5.1 and v0.5.2. |
| `add_checks_layer.py`, `merge_printings.py` | v0.6.0: count each printing once per page, and add the transcription checks and the audit. |
| `validate.py` | Integrity and count checks. Every release must pass them; v0.6.1 passes 190. |
| `consumer.py`, `check_consumers.py` | Read a release without the website, and check that the site agrees with the release. |

Releases are never edited. New evidence always makes a new version; see [`archive_data/README.md`](archive_data/README.md) for the commands.

## 5 · The website

| File | What it does |
|---|---|
| `build_pulse_explorer.py` | Builds the whole site from the current release: the pages, their data files, and the shared header and footer. |
| `home.html`, `telescope.html`, `pulse_explorer.html`, `method.html`, `notes.html` | The page templates. |
| `site_parts.py`, `site.css` | The header and footer that every page shares. |
| `export_public_repo.py` | Makes this repository from the working project. |
