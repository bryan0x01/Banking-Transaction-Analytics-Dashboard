INSERT OR REPLACE INTO pipeline_sql_audit (script_name, executed_at, note)
VALUES ('05_load_facts.sql', CURRENT_TIMESTAMP, 'Fact load verified after Python table writes.');

DROP VIEW IF EXISTS vw_fact_row_counts;

CREATE VIEW vw_fact_row_counts AS
SELECT 'fact_transaction' AS table_name, COUNT(*) AS row_count FROM fact_transaction
UNION ALL SELECT 'fact_account_daily_balance', COUNT(*) FROM fact_account_daily_balance
UNION ALL SELECT 'fact_customer_monthly_summary', COUNT(*) FROM fact_customer_monthly_summary
UNION ALL SELECT 'fact_anomaly_flag', COUNT(*) FROM fact_anomaly_flag
UNION ALL SELECT 'fact_data_quality_issue', COUNT(*) FROM fact_data_quality_issue;
