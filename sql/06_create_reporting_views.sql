INSERT OR REPLACE INTO pipeline_sql_audit (script_name, executed_at, note)
VALUES ('06_create_reporting_views.sql', CURRENT_TIMESTAMP, 'Business reporting views created for Excel and Power BI.');

DROP VIEW IF EXISTS vw_transaction_overview;
CREATE VIEW vw_transaction_overview AS
SELECT
    ft.transaction_id,
    dd.date AS transaction_date,
    ft.transaction_timestamp,
    dc.customer_id,
    dc.customer_display_name,
    dc.customer_segment,
    dc.age_group,
    da.account_id,
    da.account_type,
    dm.merchant_id,
    dm.merchant_name,
    dtc.transaction_category,
    dts.transaction_status,
    dch.transaction_channel,
    dl.city,
    dl.state,
    dl.region,
    ft.transaction_amount,
    ft.signed_transaction_amount,
    ft.debit_amount,
    ft.credit_amount,
    ft.debit_credit_indicator,
    ft.is_international,
    ft.is_recurring,
    ft.balance_after_transaction
FROM fact_transaction ft
LEFT JOIN dim_date dd ON ft.date_key = dd.date_key
LEFT JOIN dim_customer dc ON ft.customer_key = dc.customer_key
LEFT JOIN dim_account da ON ft.account_key = da.account_key
LEFT JOIN dim_merchant dm ON ft.merchant_key = dm.merchant_key
LEFT JOIN dim_transaction_category dtc ON ft.transaction_category_key = dtc.transaction_category_key
LEFT JOIN dim_transaction_status dts ON ft.transaction_status_key = dts.transaction_status_key
LEFT JOIN dim_channel dch ON ft.channel_key = dch.channel_key
LEFT JOIN dim_location dl ON ft.location_key = dl.location_key;

DROP VIEW IF EXISTS vw_daily_transaction_trends;
CREATE VIEW vw_daily_transaction_trends AS
SELECT
    dd.date AS transaction_date,
    dd.day_of_week,
    dd.is_weekend,
    COUNT(*) AS transaction_count,
    SUM(ft.transaction_amount) AS total_transaction_value,
    SUM(ft.approved_amount) AS approved_transaction_value,
    AVG(ft.transaction_amount) AS average_transaction_amount
FROM fact_transaction ft
JOIN dim_date dd ON ft.date_key = dd.date_key
GROUP BY dd.date, dd.day_of_week, dd.is_weekend;

DROP VIEW IF EXISTS vw_monthly_transaction_trends;
CREATE VIEW vw_monthly_transaction_trends AS
SELECT
    dd.month_start_date,
    dd.year,
    dd.month_number,
    COUNT(*) AS transaction_count,
    SUM(ft.transaction_amount) AS total_transaction_value,
    SUM(ft.approved_amount) AS approved_transaction_value,
    SUM(ft.signed_transaction_amount) AS net_transaction_flow,
    ROUND(AVG(ft.transaction_amount), 2) AS average_transaction_amount
FROM fact_transaction ft
JOIN dim_date dd ON ft.date_key = dd.date_key
GROUP BY dd.month_start_date, dd.year, dd.month_number
ORDER BY dd.month_start_date;

DROP VIEW IF EXISTS vw_category_performance;
CREATE VIEW vw_category_performance AS
SELECT
    dtc.transaction_category,
    COUNT(*) AS transaction_count,
    SUM(ft.transaction_amount) AS total_transaction_value,
    SUM(ft.approved_amount) AS approved_transaction_value,
    ROUND(AVG(ft.transaction_amount), 2) AS average_transaction_amount,
    ROUND(SUM(CASE WHEN ft.is_declined = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS decline_rate
FROM fact_transaction ft
JOIN dim_transaction_category dtc ON ft.transaction_category_key = dtc.transaction_category_key
GROUP BY dtc.transaction_category;

DROP VIEW IF EXISTS vw_customer_spending_summary;
CREATE VIEW vw_customer_spending_summary AS
SELECT
    dc.customer_id,
    dc.customer_display_name,
    dc.customer_segment,
    dc.age_group,
    COUNT(ft.transaction_id) AS transaction_count,
    SUM(ft.debit_amount) AS debit_transaction_value,
    SUM(ft.credit_amount) AS credit_transaction_value,
    SUM(ft.signed_transaction_amount) AS net_transaction_flow,
    ROUND(AVG(ft.transaction_amount), 2) AS average_transaction_amount
FROM fact_transaction ft
JOIN dim_customer dc ON ft.customer_key = dc.customer_key
GROUP BY dc.customer_id, dc.customer_display_name, dc.customer_segment, dc.age_group;

DROP VIEW IF EXISTS vw_merchant_performance;
CREATE VIEW vw_merchant_performance AS
SELECT
    dm.merchant_id,
    dm.merchant_name,
    dm.merchant_category,
    COUNT(*) AS transaction_count,
    SUM(ft.transaction_amount) AS total_transaction_value,
    ROUND(AVG(ft.transaction_amount), 2) AS average_transaction_amount
FROM fact_transaction ft
JOIN dim_merchant dm ON ft.merchant_key = dm.merchant_key
GROUP BY dm.merchant_id, dm.merchant_name, dm.merchant_category;

DROP VIEW IF EXISTS vw_channel_performance;
CREATE VIEW vw_channel_performance AS
SELECT
    dch.transaction_channel,
    COUNT(*) AS transaction_count,
    SUM(ft.transaction_amount) AS total_transaction_value,
    ROUND(SUM(CASE WHEN ft.is_approved = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS approval_rate,
    ROUND(SUM(CASE WHEN ft.is_declined = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS decline_rate
FROM fact_transaction ft
JOIN dim_channel dch ON ft.channel_key = dch.channel_key
GROUP BY dch.transaction_channel;

DROP VIEW IF EXISTS vw_transaction_status_summary;
CREATE VIEW vw_transaction_status_summary AS
SELECT
    dts.transaction_status,
    COUNT(*) AS transaction_count,
    SUM(ft.transaction_amount) AS total_transaction_value,
    ROUND(COUNT(*) * 1.0 / (SELECT COUNT(*) FROM fact_transaction), 4) AS transaction_share
FROM fact_transaction ft
JOIN dim_transaction_status dts ON ft.transaction_status_key = dts.transaction_status_key
GROUP BY dts.transaction_status;

DROP VIEW IF EXISTS vw_account_activity;
CREATE VIEW vw_account_activity AS
SELECT
    da.account_id,
    da.account_type,
    da.account_status,
    COUNT(ft.transaction_id) AS transaction_count,
    SUM(ft.transaction_amount) AS total_transaction_value,
    SUM(ft.signed_transaction_amount) AS net_transaction_flow,
    MIN(dd.date) AS first_transaction_date,
    MAX(dd.date) AS last_transaction_date
FROM fact_transaction ft
JOIN dim_account da ON ft.account_key = da.account_key
JOIN dim_date dd ON ft.date_key = dd.date_key
GROUP BY da.account_id, da.account_type, da.account_status;

DROP VIEW IF EXISTS vw_customer_segment_analysis;
CREATE VIEW vw_customer_segment_analysis AS
SELECT
    dc.customer_segment,
    COUNT(DISTINCT dc.customer_id) AS active_customer_count,
    COUNT(ft.transaction_id) AS transaction_count,
    SUM(ft.debit_amount) AS debit_transaction_value,
    ROUND(AVG(ft.transaction_amount), 2) AS average_transaction_amount,
    ROUND(COUNT(ft.transaction_id) * 1.0 / COUNT(DISTINCT dc.customer_id), 2) AS transactions_per_customer
FROM fact_transaction ft
JOIN dim_customer dc ON ft.customer_key = dc.customer_key
GROUP BY dc.customer_segment;

DROP VIEW IF EXISTS vw_geographic_transaction_summary;
CREATE VIEW vw_geographic_transaction_summary AS
SELECT
    dl.region,
    dl.state,
    dl.city,
    COUNT(*) AS transaction_count,
    SUM(ft.transaction_amount) AS total_transaction_value,
    SUM(CASE WHEN ft.is_international = 1 THEN 1 ELSE 0 END) AS international_transaction_count
FROM fact_transaction ft
JOIN dim_location dl ON ft.location_key = dl.location_key
GROUP BY dl.region, dl.state, dl.city;

DROP VIEW IF EXISTS vw_anomaly_review;
CREATE VIEW vw_anomaly_review AS
SELECT
    af.anomaly_id,
    af.transaction_id,
    dd.date AS transaction_date,
    dc.customer_id,
    dc.customer_display_name,
    dtc.transaction_category,
    dch.transaction_channel,
    ft.transaction_amount,
    af.triggered_rules,
    af.anomaly_score,
    af.review_priority
FROM fact_anomaly_flag af
JOIN fact_transaction ft ON af.transaction_key = ft.transaction_key
LEFT JOIN dim_date dd ON ft.date_key = dd.date_key
LEFT JOIN dim_customer dc ON ft.customer_key = dc.customer_key
LEFT JOIN dim_transaction_category dtc ON ft.transaction_category_key = dtc.transaction_category_key
LEFT JOIN dim_channel dch ON ft.channel_key = dch.channel_key;

DROP VIEW IF EXISTS vw_declined_transaction_analysis;
CREATE VIEW vw_declined_transaction_analysis AS
SELECT
    dd.month_start_date,
    dtc.transaction_category,
    dch.transaction_channel,
    COUNT(*) AS transaction_count,
    SUM(CASE WHEN ft.is_declined = 1 THEN 1 ELSE 0 END) AS declined_transaction_count,
    ROUND(SUM(CASE WHEN ft.is_declined = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS decline_rate
FROM fact_transaction ft
JOIN dim_date dd ON ft.date_key = dd.date_key
JOIN dim_transaction_category dtc ON ft.transaction_category_key = dtc.transaction_category_key
JOIN dim_channel dch ON ft.channel_key = dch.channel_key
GROUP BY dd.month_start_date, dtc.transaction_category, dch.transaction_channel;

DROP VIEW IF EXISTS vw_data_quality_summary;
CREATE VIEW vw_data_quality_summary AS
SELECT
    source_file,
    rule_name,
    severity,
    resolution_status,
    COUNT(*) AS issue_count
FROM fact_data_quality_issue
GROUP BY source_file, rule_name, severity, resolution_status;

DROP VIEW IF EXISTS vw_executive_kpis;
CREATE VIEW vw_executive_kpis AS
SELECT
    COUNT(*) AS total_transaction_count,
    SUM(transaction_amount) AS total_transaction_value,
    SUM(approved_amount) AS approved_transaction_value,
    ROUND(AVG(transaction_amount), 2) AS average_transaction_amount,
    MAX(transaction_amount) AS largest_transaction_amount,
    COUNT(DISTINCT customer_key) AS active_customer_count,
    COUNT(DISTINCT account_key) AS active_account_count,
    ROUND(SUM(CASE WHEN is_approved = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS approval_rate,
    ROUND(SUM(CASE WHEN is_declined = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS decline_rate,
    ROUND(SUM(CASE WHEN is_reversed = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS reversal_rate,
    ROUND(SUM(CASE WHEN is_pending = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS pending_transaction_rate,
    SUM(debit_amount) AS debit_transaction_value,
    SUM(credit_amount) AS credit_transaction_value,
    SUM(signed_transaction_amount) AS net_transaction_flow,
    ROUND(SUM(CASE WHEN is_international = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS international_transaction_percentage,
    ROUND(SUM(CASE WHEN is_recurring = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS recurring_transaction_percentage,
    (SELECT COUNT(*) FROM fact_anomaly_flag) AS potential_anomaly_count
FROM fact_transaction;
