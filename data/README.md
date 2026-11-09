# Data release v0.7.1

This is the data behind the site. It holds:

- every page, issue and newspaper in the archive;
- the reviewed stories of 1776 and 1797;
- the automatic matched stories for all 41 years.

A release is never edited. New evidence makes a new version with its own checks: this one passes all 449. The code is in [`../pipeline/archive_data/`](../pipeline/archive_data).

## Two tiers

| Tier | Where | Checked against the scans? |
|---|---|---|
| **Reviewed stories:** 127 passages in 34 groups, with roles, notes and relations | `tables/` | Yes |
| **Matched stories:** 48,127 stories found by shared wording, with 163,926 printings (one per page) | `derived/reuse_*.parquet` | Not one by one. Every printing has a machine check against the page's other transcription, and a random 200 stories were audited against the scans. |

**What the audit found:** 86% of matched stories are one item in every printing, and every located passage is on its page. But about 1 passage in 5, up to 1 in 3, has a misread word that changes a fact, so check the scan before quoting a matched transcription.

## Files

| Path | Contents |
|---|---|
| `tables/newspapers.jsonl`, `issues.jsonl` | 110 newspaper series (by LCCN) and 19,445 issues |
| `tables/pages.jsonl.gz`, `page_versions.jsonl.gz`, `page_assessments.jsonl.gz` | All 77,793 pages, with their Library of Congress links, the exact dataset row each comes from, and whether the page is usable (77,749 are). These are compressed; `gunzip -k data/tables/*.gz` restores them. |
| `tables/observations.jsonl` | Reviewed passages: where each was printed, with its excerpt |
| `tables/groups.jsonl`, `memberships.jsonl`, `group_hierarchy.jsonl` | Stories and their parts, and which passage belongs to which, with the reason |
| `tables/annotations.jsonl` | The review history: roles, scan findings, corrections. Nothing is overwritten; a new note supersedes the old one. |
| `tables/relations.jsonl`, `relation_evidence.jsonl`, `claims.jsonl`, `claim_evidence.jsonl`, `date_assertions.jsonl`, `objects.jsonl` | Connections that the papers state themselves, claims, and dates mentioned in the texts |
| `tables/topics.jsonl` | The 24 topics of the frozen model |
| `tables/sources.jsonl`, `runs.jsonl`, `metadata.jsonl`, `assets.jsonl` | Provenance: input files and their hashes, the runs that made each layer, scan crops |
| `derived/reuse_matches.parquet` | 376,036 automatic matches between passages in different newspapers. The 310,155 marked `main` make up the stories. |
| `derived/reuse_families.parquet` | The matched stories: first and last date, newspapers, pages, and the `long_running` flag |
| `derived/reuse_family_appearances.parquet` | Every printing of a matched story, one per page: page, date, newspaper, the matched blocks on the page, and an excerpt |
| `derived/transcription_checks.parquet` | For every printing, whether its passage also appears in the page's other machine transcription (`confirmed`, `partly`, `missing_in_other`, `other_unreadable`, `no_second_transcription`) |
| `derived/matched_audit.parquet` | The audit of 200 random matched stories against the scans: the reviewers' verdicts, the harmonised verdicts, notes, and a blind second reading of 30 |
| `derived/reuse_family_titles.parquet` | A title for each matched story |
| `derived/story_topics.parquet` | The topic of each story, with the share and how far its printings agree |
| `derived/page_topic_census.parquet` | Topic scores for all 77,749 usable pages |
| `schemas/schema.sql`, `examples.sql` | The table definitions and example queries |
| `manifest.json` | Every file of the release with its SHA-256 hash, the counts, and the dataset revision |
| `validation.json` | The 190 checks and their results |
| `release-notes.md` | The release's own notes: changes in each version, the data model, counting rules, and how to extend it |

## Left out of this copy

These files are listed in `manifest.json` with their hashes:

- `research.sqlite` (107 MB): the same tables as one SQLite database;
- `assets/`: scan crops of the reviewed passages, which the site also serves from `site/assets/`;
- `sources/`: snapshots of the input files and code each release was built from, including the audit's verdicts and protocol.

The raw dataset is not here either. It is six Parquet files, about 1.8 GB, on Hugging Face (`RevolutionCrossroads/loc_chronicling_america_1770-1810`, revision `0b97906ad32e269376872934820357fc333151d8`).

## Read it

```python
import pyarrow.parquet as pq
stories = pq.read_table('data/derived/reuse_families.parquet').to_pylist()
widest = max(stories, key=lambda s: s['newspapers'])
```

**Counting:** a passage can belong to several groups, so count distinct `observation_id` values for a union. A missing page means the archive has no page for that date, not that nothing was printed.

**Language:** 16 `date_assertions` and 6 relation-review notes, imported from the first relation pilot, keep their original Chinese wording. A release never rewrites evidence.
