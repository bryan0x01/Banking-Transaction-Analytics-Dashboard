# Banking Transaction Analytics Dashboard

This is an end-to-end data analytics project built with Python, Pandas, SQL, SQLite, Excel, and Power BI-ready CSV exports. It uses fully synthetic banking data to show how raw transaction files can be cleaned, validated, modeled, analyzed, and prepared for dashboard reporting.

The project does not use real customer data, real account numbers, banking APIs, cloud services, Docker, or paid tools.

## Business Problem

Banking leaders often need clear answers about transaction volume, spending behavior, approval and decline rates, channel usage, merchant concentration, and unusual activity that may require review. This project turns transaction-level source files into reusable analytical tables and business-facing outputs that support those questions.

## What The Pipeline Builds

The current default run generates:

- 75,035 raw synthetic transaction rows
- 74,555 valid analyzed transactions after validation
- 1,500 synthetic customers
- 2,406 synthetic accounts
- 14 transaction categories
- 12,972 rule-based potential anomaly flags
- 12,040 data-quality issues for review
- A SQLite database at `database/banking_analytics.db`
- An Excel workbook at `data/output/banking_transaction_analysis.xlsx`
- 32 Power BI-ready CSV exports in `data/output/powerbi/`

## Technology Stack

- Python and Pandas for generation, cleaning, validation, transformations, and analysis
- SQLite for local dimensional modeling and reporting views
- SQL scripts for indexes, views, KPI snapshots, and validation summaries
- XlsxWriter for Excel workbook generation
- CSV exports for Power BI
- Pytest for unit tests

## Repository Structure

```text
config/       Pipeline settings
data/         Raw, processed, output, and Power BI export files
database/     Local SQLite database
docs/         Architecture, data dictionary, metrics, insights, setup, walkthrough
excel/        Excel report requirements
powerbi/      Dashboard, model, visual, and DAX guidance
sql/          SQLite scripts and reporting views
src/          Python pipeline modules
tests/        Pytest unit tests
```

## Pipeline Steps

1. Generate synthetic source CSVs.
2. Ingest raw files and standardize column names.
3. Clean IDs, text, dates, timestamps, currencies, categories, statuses, channels, and booleans.
4. Validate business rules and preserve issues in `fact_data_quality_issue`.
5. Build dimensions and facts for a Power BI-friendly model.
6. Run reconciliation checks.
7. Calculate KPIs and generate business insights.
8. Build SQLite tables and reporting views.
9. Export Power BI-ready CSV files.
10. Generate the Excel workbook.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run The Project

```bash
python src/run_pipeline.py
```

The script creates missing folders and rebuilds generated outputs from the repository root.

## Run Tests

```bash
pytest
```

The current suite has 14 tests covering cleaning, validation, transformations, KPIs, reconciliation totals, and anomaly rules.

## Data Model Summary

Dimensions:

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

Facts:

- `fact_transaction`
- `fact_account_daily_balance`
- `fact_customer_monthly_summary`
- `fact_anomaly_flag`
- `fact_data_quality_issue`

## Reporting Views

The SQLite database creates business-friendly views including transaction overview, daily and monthly trends, category performance, customer summaries, merchant performance, channel performance, status summaries, account activity, segment analysis, geographic summaries, anomaly review, declined transaction analysis, data-quality summary, and executive KPIs.

## Synthetic Data Notes

The generator creates realistic patterns such as weekend dining activity, seasonal travel and retail activity, payroll deposits, recurring payments, channel preferences, different segment behavior, decline-rate differences by channel, and international activity for a small share of customers.

It also intentionally injects data-quality issues such as duplicate IDs, invalid relationships, missing values, inconsistent text, invalid statuses, zero or negative amounts, invalid devices, invalid branches, and transactions outside expected account windows.

## Anomaly Rules

The project uses rule-based review flags only. It does not determine or claim fraud.

Rules include high-value transactions, customer spending deviation, rapid repeated transactions, geographic inconsistency, unusual international activity, unusual transaction time, repeated declines, and balance-related issues. Scores map to low, medium, and high review priority.

## Excel And Power BI

The Excel workbook includes executive summary, monthly trends, category analysis, customer segments, channel analysis, merchant analysis, transaction status, anomaly review, data quality, and reconciliation sheets.

Power BI deliverables are CSV exports and setup documents rather than a `.pbix` file.

## Limitations

- All data is simulated and should not be interpreted as real banking behavior.
- Rule-based anomaly flags only identify transactions worth reviewing.
- Geographic logic uses simple state and region approximations.
- The pipeline is a local analysis workflow, not production infrastructure.
