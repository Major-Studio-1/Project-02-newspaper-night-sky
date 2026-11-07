PRAGMA foreign_keys = ON;
PRAGMA user_version = 1;

CREATE TABLE metadata (key TEXT PRIMARY KEY, value_json TEXT NOT NULL CHECK(json_valid(value_json)));
CREATE TABLE sources (
 id TEXT PRIMARY KEY, path TEXT NOT NULL, sha256 TEXT NOT NULL CHECK(length(sha256)=64),
 bytes INTEGER NOT NULL, kind TEXT NOT NULL, url TEXT, verification TEXT NOT NULL
);
CREATE TABLE runs (
 id TEXT PRIMARY KEY, method TEXT NOT NULL, parameters_json TEXT NOT NULL CHECK(json_valid(parameters_json)),
 source_id TEXT NOT NULL REFERENCES sources(id), recorded_date TEXT NOT NULL,
 reviewer_kind TEXT NOT NULL, independent_review INTEGER NOT NULL CHECK(independent_review IN (0,1))
);
CREATE TABLE objects (id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL);
CREATE TABLE newspapers (
 id TEXT PRIMARY KEY, lccn TEXT NOT NULL UNIQUE,
 titles_json TEXT NOT NULL CHECK(json_valid(titles_json)), places_json TEXT NOT NULL CHECK(json_valid(places_json))
);
CREATE TABLE issues (
 id TEXT PRIMARY KEY, newspaper_id TEXT NOT NULL REFERENCES newspapers(id),
 publication_date TEXT NOT NULL CHECK(length(publication_date)=10), edition INTEGER NOT NULL,
 UNIQUE(newspaper_id, publication_date, edition)
);
CREATE TABLE pages (
 id TEXT PRIMARY KEY, issue_id TEXT NOT NULL REFERENCES issues(id), page_number INTEGER NOT NULL,
 legacy_page_key TEXT NOT NULL UNIQUE, issue_url TEXT, pinned_scan_url TEXT NOT NULL, original_scan_url TEXT,
 UNIQUE(issue_id,page_number)
);
CREATE TABLE page_versions (
 id TEXT PRIMARY KEY, page_id TEXT NOT NULL REFERENCES pages(id), dataset_revision TEXT NOT NULL,
 shard_source_id TEXT NOT NULL REFERENCES sources(id), shard_row INTEGER NOT NULL CHECK(shard_row>=0),
 UNIQUE(page_id,dataset_revision), UNIQUE(shard_source_id,shard_row)
);
CREATE TABLE page_assessments (
 page_version_id TEXT NOT NULL REFERENCES page_versions(id), run_id TEXT NOT NULL REFERENCES runs(id),
 eligible INTEGER NOT NULL CHECK(eligible IN (0,1)), selected_text_field TEXT,
 selected_words INTEGER NOT NULL, revx_words INTEGER NOT NULL, ca_words INTEGER NOT NULL,
 duplicate_key INTEGER NOT NULL, duplicate_scan INTEGER NOT NULL, selected_normalized_text_sha256 TEXT,
 PRIMARY KEY(page_version_id,run_id)
);
CREATE TABLE observations (
 id TEXT PRIMARY KEY REFERENCES objects(id), legacy_namespace TEXT NOT NULL, legacy_id TEXT NOT NULL,
 page_version_id TEXT NOT NULL REFERENCES page_versions(id), transcription_field TEXT NOT NULL,
 excerpts_json TEXT NOT NULL CHECK(json_valid(excerpts_json)), excerpt_sha256 TEXT NOT NULL,
 normalization TEXT NOT NULL, locator_json TEXT NOT NULL CHECK(json_valid(locator_json)),
 scan_review_status TEXT NOT NULL, scan_review_run_id TEXT NOT NULL REFERENCES runs(id),
 source_id TEXT NOT NULL REFERENCES sources(id), source_pointer TEXT NOT NULL,
 UNIQUE(legacy_namespace,legacy_id)
);
CREATE TABLE groups (
 id TEXT PRIMARY KEY REFERENCES objects(id), kind TEXT NOT NULL CHECK(kind IN ('message_group','document_group','context_group','event')),
 label TEXT NOT NULL, definition TEXT NOT NULL, admission_rule TEXT NOT NULL, run_id TEXT NOT NULL REFERENCES runs(id)
);
CREATE TABLE annotations (
 id TEXT PRIMARY KEY, object_id TEXT NOT NULL REFERENCES objects(id), annotation_type TEXT NOT NULL,
 value_json TEXT NOT NULL CHECK(json_valid(value_json)), run_id TEXT NOT NULL REFERENCES runs(id),
 source_id TEXT NOT NULL REFERENCES sources(id), source_pointer TEXT NOT NULL,
 supersedes_id TEXT UNIQUE REFERENCES annotations(id), recorded_date TEXT NOT NULL
);
CREATE TRIGGER annotations_no_update BEFORE UPDATE ON annotations BEGIN SELECT RAISE(ABORT,'Append a superseding annotation instead of overwriting history'); END;
CREATE TRIGGER annotations_no_delete BEFORE DELETE ON annotations BEGIN SELECT RAISE(ABORT,'Annotation history is append-only'); END;
CREATE TRIGGER annotations_same_target BEFORE INSERT ON annotations WHEN NEW.supersedes_id IS NOT NULL BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM annotations WHERE id=NEW.supersedes_id AND object_id=NEW.object_id AND annotation_type=NEW.annotation_type)
 THEN RAISE(ABORT,'Supersession must refer to the same object and annotation type') END;
END;
CREATE TABLE memberships (
 annotation_id TEXT PRIMARY KEY REFERENCES annotations(id), observation_id TEXT NOT NULL REFERENCES observations(id),
 group_id TEXT NOT NULL REFERENCES groups(id), decision TEXT NOT NULL CHECK(decision IN ('admitted','candidate','excluded','withdrawn')),
 roles_json TEXT NOT NULL CHECK(json_valid(roles_json))
);
CREATE TRIGGER membership_consistency BEFORE INSERT ON memberships BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM annotations a WHERE a.id=NEW.annotation_id
 AND a.object_id=NEW.observation_id AND a.annotation_type='membership:'||NEW.group_id
 AND json_extract(a.value_json,'$.decision')=NEW.decision)
 THEN RAISE(ABORT,'Membership must agree with its evidence annotation') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM memberships m JOIN annotations a ON a.id=m.annotation_id
 WHERE m.observation_id=NEW.observation_id AND m.group_id=NEW.group_id
 AND NOT EXISTS(SELECT 1 FROM annotations newer WHERE newer.supersedes_id=a.id))
 THEN RAISE(ABORT,'Supersede the existing membership decision first') END;
END;
CREATE TRIGGER memberships_no_update BEFORE UPDATE ON memberships BEGIN SELECT RAISE(ABORT,'Append a superseding membership decision'); END;
CREATE TRIGGER memberships_no_delete BEFORE DELETE ON memberships BEGIN SELECT RAISE(ABORT,'Membership history is append-only'); END;
CREATE TABLE group_hierarchy (
 annotation_id TEXT PRIMARY KEY REFERENCES annotations(id), parent_id TEXT NOT NULL REFERENCES groups(id),
 child_id TEXT NOT NULL REFERENCES groups(id), CHECK(parent_id<>child_id), UNIQUE(parent_id,child_id)
);
CREATE TRIGGER hierarchy_no_cycle BEFORE INSERT ON group_hierarchy BEGIN
 SELECT CASE WHEN EXISTS(WITH RECURSIVE descendants(id) AS (
 SELECT child_id FROM group_hierarchy WHERE parent_id=NEW.child_id
 UNION SELECT h.child_id FROM group_hierarchy h JOIN descendants d ON h.parent_id=d.id
 ) SELECT 1 FROM descendants WHERE id=NEW.parent_id)
 THEN RAISE(ABORT,'Group hierarchy cannot contain a cycle') END;
END;
CREATE TABLE claims (
 id TEXT PRIMARY KEY REFERENCES objects(id), statement TEXT NOT NULL, kind TEXT NOT NULL,
 imported_review_annotation_id TEXT NOT NULL REFERENCES annotations(id)
);
CREATE TABLE claim_evidence (
 claim_id TEXT NOT NULL REFERENCES claims(id), observation_id TEXT NOT NULL REFERENCES observations(id),
 PRIMARY KEY(claim_id,observation_id)
);
CREATE TABLE relations (
 id TEXT PRIMARY KEY REFERENCES objects(id), subject_id TEXT NOT NULL REFERENCES objects(id),
 predicate TEXT NOT NULL, object_id TEXT NOT NULL REFERENCES objects(id), directed INTEGER NOT NULL CHECK(directed IN (0,1)),
 evidence_level TEXT NOT NULL CHECK(evidence_level IN ('textual_correspondence','printed_assertion','explicit_citation','context_only')),
 imported_review_annotation_id TEXT NOT NULL REFERENCES annotations(id), CHECK(subject_id<>object_id)
);
CREATE TABLE relation_evidence (
 relation_id TEXT NOT NULL REFERENCES relations(id), evidence_object_id TEXT NOT NULL REFERENCES objects(id),
 locator TEXT NOT NULL, PRIMARY KEY(relation_id,evidence_object_id,locator)
);
CREATE TABLE date_assertions (
 id TEXT PRIMARY KEY, object_id TEXT NOT NULL REFERENCES objects(id), date_role TEXT NOT NULL,
 as_printed TEXT, earliest_date TEXT, latest_date TEXT,
 precision TEXT NOT NULL CHECK(precision IN ('day','range','unresolved','unknown')),
 source_id TEXT NOT NULL REFERENCES sources(id), source_pointer TEXT NOT NULL,
 CHECK(earliest_date IS NULL OR latest_date IS NULL OR earliest_date<=latest_date)
);
CREATE TABLE assets (
 id TEXT PRIMARY KEY, object_id TEXT NOT NULL REFERENCES objects(id), path TEXT NOT NULL,
 sha256 TEXT NOT NULL, kind TEXT NOT NULL, original_source_id TEXT NOT NULL REFERENCES sources(id)
);
CREATE TABLE topics (
 id TEXT PRIMARY KEY REFERENCES objects(id), model_run_id TEXT NOT NULL REFERENCES runs(id), component_id TEXT NOT NULL,
 label TEXT NOT NULL, definition TEXT NOT NULL, terms_json TEXT NOT NULL CHECK(json_valid(terms_json)),
 restart_agreement REAL, review_note TEXT NOT NULL, UNIQUE(model_run_id,component_id)
);
CREATE INDEX observations_page ON observations(page_version_id);
CREATE INDEX issues_date ON issues(publication_date);
CREATE INDEX memberships_group ON memberships(group_id,observation_id);
CREATE INDEX relations_endpoints ON relations(subject_id,object_id);

CREATE VIEW current_annotations AS SELECT a.* FROM annotations a
 WHERE NOT EXISTS(SELECT 1 FROM annotations newer WHERE newer.supersedes_id=a.id);
CREATE VIEW current_memberships AS SELECT m.* FROM memberships m JOIN current_annotations a ON a.id=m.annotation_id;
CREATE VIEW group_publications AS SELECT DISTINCT m.group_id,o.id AS observation_id,o.legacy_id,
 p.id AS page_id,i.id AS issue_id,n.id AS newspaper_id,n.lccn,i.publication_date,i.edition,p.page_number,
 p.pinned_scan_url,o.excerpts_json,m.roles_json
 FROM current_memberships m JOIN observations o ON o.id=m.observation_id
 JOIN page_versions v ON v.id=o.page_version_id JOIN pages p ON p.id=v.page_id
 JOIN issues i ON i.id=p.issue_id JOIN newspapers n ON n.id=i.newspaper_id WHERE m.decision='admitted';
CREATE VIEW newspaper_date_coverage AS SELECT i.newspaper_id,i.publication_date,
 COUNT(DISTINCT i.id) AS observed_issues_editions,COUNT(DISTINCT p.id) AS observed_pages,
 SUM(a.eligible) AS eligible_pages FROM issues i JOIN pages p ON p.issue_id=i.id
 JOIN page_versions v ON v.page_id=p.id JOIN page_assessments a ON a.page_version_id=v.id
 WHERE a.run_id='run:eligibility-v1' AND v.dataset_revision=(SELECT json_extract(value_json,'$.revision') FROM metadata WHERE key='release')
 GROUP BY i.newspaper_id,i.publication_date;
CREATE VIEW observed_group_summary AS SELECT group_id,COUNT(DISTINCT observation_id) AS passage_selections,
 COUNT(DISTINCT page_id) AS pages,COUNT(DISTINCT issue_id) AS issues_editions,
 COUNT(DISTINCT newspaper_id) AS newspapers,MIN(publication_date) AS first_observed_publication,
 MAX(publication_date) AS last_observed_publication FROM group_publications GROUP BY group_id;
