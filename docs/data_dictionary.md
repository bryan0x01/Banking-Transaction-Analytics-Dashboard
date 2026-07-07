# Data Dictionary

## Source Tables

| Table | Column | Type | Description | Example | Required | Key | Source |
|---|---|---:|---|---|---|---|---|
| customers | customer_id | text | Synthetic customer business key | CUST000001 | Yes | Yes | Generated |
| customers | customer_segment | text | Behavioral customer segment | Families | Yes | No | Generated |
| customers | preferred_channel | text | Preferred transaction channel | Mobile | Yes | No | Generated |
| accounts | account_id | text | Synthetic account business key | ACC000001 | Yes | Yes | Generated |
| accounts | account_type | text | Checking, Savings, Credit Card, or Money Market | Checking | Yes | No | Generated |
| accounts | account_status | text | Active, Closed, or Dormant | Active | Yes | No | Generated |
| transactions | transaction_id | text | Synthetic transaction business key | TXN00000001 | Yes | Yes | Generated |
| transactions | transaction_amount | decimal | Positive transaction amount before debit/credit sign | 125.44 | Yes | No | Generated |
| transactions | debit_credit_indicator | text | Direction of transaction flow | Debit | Yes | No | Generated |
| transactions | synthetic_anomaly_flag | boolean | Generator-only validation flag | False | No | No | Generated |
| merchants | merchant_id | text | Synthetic merchant key | MER0001 | Yes | Yes | Generated |
| branches | branch_id | text | Synthetic branch key | BR001 | Yes | Yes | Generated |
| devices | device_id | text | Synthetic device key | DEV00001 | No | Yes | Generated |

## Dimension Tables

| Table | Column | Type | Description | Example | Required | Key | Source |
|---|---|---:|---|---|---|---|---|
| dim_customer | customer_key | integer | Surrogate key | 101 | Yes | Primary | Python |
| dim_account | account_key | integer | Surrogate key | 205 | Yes | Primary | Python |
| dim_merchant | merchant_key | integer | Surrogate key | 45 | Yes | Primary | Python |
| dim_transaction_category | transaction_category_key | integer | Category surrogate key | 3 | Yes | Primary | Python |
| dim_date | date_key | integer | Date key in YYYYMMDD format | 20240131 | Yes | Primary | Python |
| dim_channel | channel_key | integer | Channel surrogate key | 2 | Yes | Primary | Python |
| dim_location | location_key | integer | City/state surrogate key | 10 | Yes | Primary | Python |
| dim_device | device_key | integer | Device surrogate key | 500 | No | Primary | Python |
| dim_branch | branch_key | integer | Branch surrogate key | 12 | No | Primary | Python |
| dim_transaction_status | transaction_status_key | integer | Status surrogate key | 1 | Yes | Primary | Python |

## Fact Tables

| Table | Column | Type | Description | Example | Required | Key | Source |
|---|---|---:|---|---|---|---|---|
| fact_transaction | transaction_key | integer | Transaction surrogate key | 1001 | Yes | Primary | Python |
| fact_transaction | transaction_amount | decimal | Absolute transaction value | 84.50 | Yes | No | Cleaned transaction |
| fact_transaction | signed_transaction_amount | decimal | Credit positive, debit negative | -84.50 | Yes | No | Transformation |
| fact_transaction | approved_amount | decimal | Amount only when status is approved | 84.50 | Yes | No | Transformation |
| fact_account_daily_balance | ending_balance | decimal | Last approved balance for account/date | 2450.22 | Yes | No | Transformation |
| fact_customer_monthly_summary | transaction_count | integer | Customer monthly transaction count | 42 | Yes | No | Aggregation |
| fact_anomaly_flag | anomaly_score | integer | Sum of triggered rule weights | 5 | Yes | No | Rule engine |
| fact_anomaly_flag | review_priority | text | Low, Medium, or High | Medium | Yes | No | Rule engine |
| fact_data_quality_issue | rule_name | text | Validation rule that created issue | account_id_exists | Yes | No | Validation |
| fact_data_quality_issue | severity | text | Warning, Error, or Critical | Error | Yes | No | Validation |

## Reporting Views

| View | Purpose |
|---|---|
| vw_transaction_overview | Wide transaction-level reporting view |
| vw_daily_transaction_trends | Daily volume and value trends |
| vw_monthly_transaction_trends | Monthly trend analysis |
| vw_category_performance | Category volume, value, and decline rate |
| vw_customer_spending_summary | Customer-level spend and activity |
| vw_merchant_performance | Merchant value and count summary |
| vw_channel_performance | Channel volume, value, approval, and decline rates |
| vw_anomaly_review | Review-ready anomaly detail |
| vw_data_quality_summary | Data-quality issue counts by rule and source |
| vw_executive_kpis | One-row KPI summary |
