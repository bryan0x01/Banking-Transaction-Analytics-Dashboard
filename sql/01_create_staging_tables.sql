CREATE TABLE IF NOT EXISTS pipeline_sql_audit (
    script_name TEXT PRIMARY KEY,
    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    note TEXT
);

INSERT OR REPLACE INTO pipeline_sql_audit (script_name, executed_at, note)
VALUES ('01_create_staging_tables.sql', CURRENT_TIMESTAMP, 'Staging tables are loaded from cleaned CSV data by Python.');
