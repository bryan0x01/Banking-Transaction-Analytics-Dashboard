# Power BI Data Model

## Fact Tables

- `fact_transaction`: central transaction fact
- `fact_account_daily_balance`: account balance trend fact
- `fact_customer_monthly_summary`: customer-month aggregation fact
- `fact_anomaly_flag`: rule-based review fact
- `fact_data_quality_issue`: validation issue fact

## Dimension Tables

- `dim_customer`
- `dim_account`
- `dim_merchant`
- `dim_transaction_category`
- `dim_date`
- `dim_channel`
- `dim_location`
- `dim_device`
- `dim_branch`
- `dim_transaction_status`

## Relationship Guidance

Use `fact_transaction` as the central fact table. Connect all dimensions with one-to-many, single-direction relationships from dimension to fact. Connect `fact_anomaly_flag` to `fact_transaction` by `transaction_key`. Connect monthly and daily facts to their relevant dimensions and the date table.

Do not use staging tables in the report model.

## Date Table

Mark `dim_date` as the date table using the `date` column. Use `date_key` for relationships and the date hierarchy fields for visuals.
