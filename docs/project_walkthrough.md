# Project Walkthrough

## Problem Being Solved

This project shows how a banking analytics team could turn transaction-level files into clean reporting tables and business dashboards. The goal is to answer practical questions about spending, approval rates, channels, merchants, customer segments, trends, and transactions that may need review.

## Data Sources

The source files are generated locally and are fully synthetic:

- customers
- accounts
- transactions
- merchants
- transaction categories
- branches
- devices
- customer segments

The data includes realistic patterns such as recurring payments, payroll deposits, weekend spending, seasonal retail and travel activity, customer channel preferences, and different behavior by segment.

## Cleaning Process

The cleaning code standardizes column names, trims text, normalizes categories and channels, parses currency strings, converts dates and timestamps, standardizes booleans, and handles inconsistent capitalization. It corrects values such as `POS` to `Point of Sale` and `dinning` to `Dining`.

## Validation Process

Validation checks required columns, duplicate transaction IDs, customer and account relationships, merchant references, valid amounts, date windows, statuses, categories, channels, branches, devices, currencies, account types, and customer segments. Blocking issues are written to rejected records, and all issues are stored for reporting.

## SQL Model

The model uses dimensions for customers, accounts, merchants, categories, dates, channels, locations, devices, branches, and statuses. Facts cover transactions, account daily balances, customer monthly summaries, anomaly flags, and data-quality issues.

## KPI Design

KPIs separate all-status counts from approved-only values. Debit and credit activity are stored both as absolute values and as signed net flow so calculations are not misleading.

## Anomaly Rules

The anomaly layer is rule-based and review-oriented. It flags high-value transactions, spending deviations, rapid repeats, region inconsistency, unusual international activity, unusual hours, repeated declines, and balance-related issues. The output is labeled as potentially anomalous activity, not fraud.

## Outputs

The pipeline creates:

- SQLite database and SQL reporting views
- Excel workbook with 10 worksheets
- Power BI-ready CSV exports
- KPI summary
- Reconciliation report
- Generated business insights

## Main Technical Decisions

- Use SQLite instead of external database infrastructure.
- Use function-based Python modules instead of classes or orchestration frameworks.
- Preserve data-quality issues instead of silently dropping them.
- Export Power BI CSVs and documentation instead of committing a `.pbix` placeholder.

## Limitations And Next Steps

The project uses synthetic assumptions and simplified geography. Future improvements could add more detailed decline reasons, customer lifecycle analysis, better balance simulation by account type, and optional Power BI screenshots after a manual dashboard build.
