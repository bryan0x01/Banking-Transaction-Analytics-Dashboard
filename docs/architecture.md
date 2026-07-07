# Architecture

## Pipeline Flow

```mermaid
flowchart TD
    A["Synthetic Banking Source Files"] --> B["Python and Pandas Ingestion"]
    B --> C["Cleaning and Standardization"]
    C --> D["Validation and Reconciliation"]
    D --> E["SQLite Staging Tables"]
    E --> F["Dimensions and Fact Tables"]
    F --> G["SQL Reporting Views"]
    G --> H["Excel and Power BI Exports"]
    H --> I["Executive Analytics Dashboard"]
```

## Dimensional Model

```mermaid
erDiagram
    dim_customer ||--o{ fact_transaction : customer_key
    dim_account ||--o{ fact_transaction : account_key
    dim_merchant ||--o{ fact_transaction : merchant_key
    dim_transaction_category ||--o{ fact_transaction : transaction_category_key
    dim_date ||--o{ fact_transaction : date_key
    dim_channel ||--o{ fact_transaction : channel_key
    dim_location ||--o{ fact_transaction : location_key
    dim_device ||--o{ fact_transaction : device_key
    dim_branch ||--o{ fact_transaction : branch_key
    dim_transaction_status ||--o{ fact_transaction : transaction_status_key
    fact_transaction ||--o{ fact_anomaly_flag : transaction_key
    dim_customer ||--o{ fact_customer_monthly_summary : customer_key
    dim_account ||--o{ fact_account_daily_balance : account_key
    dim_date ||--o{ fact_customer_monthly_summary : month_date_key
    dim_date ||--o{ fact_account_daily_balance : date_key
```

## Design Choices

- SQLite is used so the project runs locally without external infrastructure.
- Pandas handles practical transformations before loading analytical tables.
- SQL views keep Power BI users away from raw staging tables.
- Unknown dimension rows preserve valid fact rows when optional dimension values are missing.
- Data-quality issues are modeled as an analytical fact table instead of being hidden.
