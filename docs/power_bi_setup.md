# Power BI Setup

## Files To Import

Use the CSV files in:

```text
data/output/powerbi/
```

Import the dimension and fact CSVs for the main model. The `vw_*.csv` files are optional convenience exports for quick report pages or validation.

## Recommended Model

Create one-to-many single-direction relationships:

- `dim_customer[customer_key]` to `fact_transaction[customer_key]`
- `dim_account[account_key]` to `fact_transaction[account_key]`
- `dim_merchant[merchant_key]` to `fact_transaction[merchant_key]`
- `dim_transaction_category[transaction_category_key]` to `fact_transaction[transaction_category_key]`
- `dim_date[date_key]` to `fact_transaction[date_key]`
- `dim_channel[channel_key]` to `fact_transaction[channel_key]`
- `dim_location[location_key]` to `fact_transaction[location_key]`
- `dim_device[device_key]` to `fact_transaction[device_key]`
- `dim_branch[branch_key]` to `fact_transaction[branch_key]`
- `dim_transaction_status[transaction_status_key]` to `fact_transaction[transaction_status_key]`
- `fact_transaction[transaction_key]` to `fact_anomaly_flag[transaction_key]`
- `dim_customer[customer_key]` to `fact_customer_monthly_summary[customer_key]`
- `dim_account[account_key]` to `fact_account_daily_balance[account_key]`
- `dim_date[date_key]` to `fact_account_daily_balance[date_key]`
- `dim_date[date_key]` to `fact_customer_monthly_summary[month_date_key]`

Avoid bidirectional relationships unless a specific visual requires it.

## Pages

Build these pages:

1. Executive Overview
2. Spending Analysis
3. Customer Analysis
4. Channel and Merchant Analysis
5. Transaction Status and Operations
6. Potentially Anomalous Activity
7. Data Quality

Use `dim_date` as the main date table.
