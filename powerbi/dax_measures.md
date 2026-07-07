# DAX Measures

```DAX
Total Transactions = COUNTROWS(fact_transaction)

Total Transaction Value = SUM(fact_transaction[transaction_amount])

Approved Transaction Value = SUM(fact_transaction[approved_amount])

Average Transaction Amount = AVERAGE(fact_transaction[transaction_amount])

Median Transaction Amount = MEDIAN(fact_transaction[transaction_amount])

Active Customers = DISTINCTCOUNT(fact_transaction[customer_key])

Active Accounts = DISTINCTCOUNT(fact_transaction[account_key])

Approval Rate =
DIVIDE(
    CALCULATE(COUNTROWS(fact_transaction), fact_transaction[is_approved] = TRUE()),
    [Total Transactions]
)

Decline Rate =
DIVIDE(
    CALCULATE(COUNTROWS(fact_transaction), fact_transaction[is_declined] = TRUE()),
    [Total Transactions]
)

Reversal Rate =
DIVIDE(
    CALCULATE(COUNTROWS(fact_transaction), fact_transaction[is_reversed] = TRUE()),
    [Total Transactions]
)

Debit Value = SUM(fact_transaction[debit_amount])

Credit Value = SUM(fact_transaction[credit_amount])

Net Transaction Flow = SUM(fact_transaction[signed_transaction_amount])

Mobile Adoption Rate =
DIVIDE(
    CALCULATE(
        COUNTROWS(fact_transaction),
        dim_channel[transaction_channel] IN {"Mobile", "Online"}
    ),
    [Total Transactions]
)

International Transaction Rate =
DIVIDE(
    CALCULATE(COUNTROWS(fact_transaction), fact_transaction[is_international] = TRUE()),
    [Total Transactions]
)

Potential Anomaly Count = COUNTROWS(fact_anomaly_flag)

High-Priority Review Count =
CALCULATE(
    COUNTROWS(fact_anomaly_flag),
    fact_anomaly_flag[review_priority] = "High"
)

Previous Month Transaction Value =
CALCULATE(
    [Total Transaction Value],
    DATEADD(dim_date[date], -1, MONTH)
)

Month-over-Month Transaction Growth =
DIVIDE(
    [Total Transaction Value] - [Previous Month Transaction Value],
    [Previous Month Transaction Value]
)

Average Monthly Spend per Customer =
AVERAGE(fact_customer_monthly_summary[debit_transaction_value])
```

Assumption: rate denominators use valid transactions in `fact_transaction`. Rejected records are analyzed separately on the Data Quality page.
