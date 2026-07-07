INSERT OR REPLACE INTO pipeline_sql_audit (script_name, executed_at, note)
VALUES ('08_validation_queries.sql', CURRENT_TIMESTAMP, 'Validation summary created from data-quality and reconciliation outputs.');

DROP TABLE IF EXISTS validation_summary;

CREATE TABLE validation_summary AS
SELECT
    'data_quality_issues' AS validation_area,
    severity AS validation_status,
    COUNT(*) AS record_count
FROM fact_data_quality_issue
GROUP BY severity
UNION ALL
SELECT
    'reconciliation' AS validation_area,
    status AS validation_status,
    COUNT(*) AS record_count
FROM reconciliation_report
GROUP BY status;
