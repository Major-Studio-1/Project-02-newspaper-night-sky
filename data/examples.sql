-- Each query can be run independently against research.sqlite.
-- QUERY
SELECT * FROM observed_group_summary ORDER BY group_id;
-- QUERY
SELECT lccn, publication_date, edition, page_number, legacy_id, pinned_scan_url
FROM group_publications WHERE group_id='group:boyd-bantry-coverage' ORDER BY publication_date;
-- QUERY
SELECT COUNT(DISTINCT observation_id) AS distinct_selections,
       COUNT(DISTINCT page_id) AS distinct_pages,
       COUNT(DISTINCT issue_id) AS distinct_issues
FROM group_publications WHERE group_id IN ('group:boyd-bantry-coverage','group:boyd-core-report');
-- QUERY
SELECT * FROM newspaper_date_coverage
WHERE publication_date BETWEEN '1797-01-01' AND '1797-12-31' ORDER BY publication_date,newspaper_id;
-- QUERY
SELECT r.id,r.predicate,r.evidence_level,s.kind AS subject_kind,o.kind AS object_kind,
       a.value_json AS recorded_review
FROM relations r JOIN objects s ON s.id=r.subject_id JOIN objects o ON o.id=r.object_id
JOIN current_annotations a ON a.object_id=r.id AND a.annotation_type='relation_review';
-- QUERY
SELECT n.id,COUNT(DISTINCT i.id) AS observed_issues,COUNT(p.id) AS observed_pages,SUM(a.eligible) AS eligible_pages
FROM newspapers n JOIN issues i ON i.newspaper_id=n.id JOIN pages p ON p.issue_id=i.id
JOIN page_versions v ON v.page_id=p.id JOIN page_assessments a ON a.page_version_id=v.id
WHERE i.publication_date BETWEEN '1797-01-01' AND '1797-12-31' AND a.run_id='run:eligibility-v1'
AND v.dataset_revision=(SELECT json_extract(value_json,'$.revision') FROM metadata WHERE key='release') GROUP BY n.id;
