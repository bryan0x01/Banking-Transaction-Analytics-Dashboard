INSERT OR REPLACE INTO pipeline_sql_audit (script_name, executed_at, note)
VALUES ('04_load_dimensions.sql', CURRENT_TIMESTAMP, 'Dimension load verified after Python table writes.');

DROP VIEW IF EXISTS vw_dimension_row_counts;

CREATE VIEW vw_dimension_row_counts AS
SELECT 'dim_customer' AS table_name, COUNT(*) AS row_count FROM dim_customer
UNION ALL SELECT 'dim_account', COUNT(*) FROM dim_account
UNION ALL SELECT 'dim_merchant', COUNT(*) FROM dim_merchant
UNION ALL SELECT 'dim_transaction_category', COUNT(*) FROM dim_transaction_category
UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL SELECT 'dim_channel', COUNT(*) FROM dim_channel
UNION ALL SELECT 'dim_location', COUNT(*) FROM dim_location
UNION ALL SELECT 'dim_device', COUNT(*) FROM dim_device
UNION ALL SELECT 'dim_branch', COUNT(*) FROM dim_branch
UNION ALL SELECT 'dim_transaction_status', COUNT(*) FROM dim_transaction_status;
