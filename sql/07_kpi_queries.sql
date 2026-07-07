INSERT OR REPLACE INTO pipeline_sql_audit (script_name, executed_at, note)
VALUES ('07_kpi_queries.sql', CURRENT_TIMESTAMP, 'KPI snapshot created from reporting views.');

DROP TABLE IF EXISTS kpi_snapshot;

CREATE TABLE kpi_snapshot AS
SELECT * FROM vw_executive_kpis;
