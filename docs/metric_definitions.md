# Metric Definitions

| Metric | Business Purpose | Formula | Included Records | Excluded Records | Assumptions |
|---|---|---|---|---|---|
| Total Transaction Count | Measure transaction activity | Count rows in `fact_transaction` | Valid transactions, all statuses | Rejected records | One valid row equals one transaction |
| Total Transaction Value | Measure gross activity | Sum `transaction_amount` | Valid transactions, all statuses | Rejected records | Uses absolute values |
| Approved Transaction Value | Measure completed approved value | Sum `approved_amount` | Approved valid transactions | Declined, pending, reversed, rejected | Uses absolute values |
| Average Transaction Amount | Typical transaction size | Average `transaction_amount` | Valid transactions | Rejected records | Uses absolute values |
| Median Transaction Amount | Middle transaction size | Median `transaction_amount` | Valid transactions | Rejected records | Calculated in Python |
| Active Customers | Customer reach | Distinct `customer_key` in fact | Valid transactions | Customers without valid transactions | Unknown customer key is excluded in analysis views when needed |
| Active Accounts | Account reach | Distinct `account_key` in fact | Valid transactions | Accounts without valid transactions | Based on valid transaction activity |
| Approval Rate | Operational success rate | Approved count / total count | Valid transactions | Rejected records | Denominator includes all valid statuses |
| Decline Rate | Operational issue indicator | Declined count / total count | Valid transactions | Rejected records | Denominator includes all valid statuses |
| Reversal Rate | Reversal activity | Reversed count / total count | Valid transactions | Rejected records | Denominator includes all valid statuses |
| Pending Transaction Rate | Open processing activity | Pending count / total count | Valid transactions | Rejected records | Denominator includes all valid statuses |
| Debit Value | Outflow activity | Sum `debit_amount` | Valid debit transactions | Credits and rejected records | Amounts are absolute |
| Credit Value | Inflow activity | Sum `credit_amount` | Valid credit transactions | Debits and rejected records | Amounts are absolute |
| Net Transaction Flow | Directional flow | Sum `signed_transaction_amount` | Valid transactions | Rejected records | Credits positive, debits negative |
| Mobile Adoption Rate | Digital behavior | Mobile or Online count / total count | Valid transactions | Rejected records | Mobile and Online are treated as digital adoption |
| International Transaction Rate | Cross-border activity | International count / total count | Valid transactions | Rejected records | Based on synthetic flag |
| Potential Anomaly Count | Review workload | Count rows in `fact_anomaly_flag` | Flagged valid transactions | Unflagged and rejected records | Does not confirm fraud |
| High-Priority Review Count | Priority queue size | Count `review_priority = High` | Flagged valid transactions | Lower priority flags | Rule-score based |
| Month-over-Month Growth | Trend direction | Current month value / previous month value - 1 | Monthly customer summaries | Months without valid value | Uses debit transaction value |
| Average Monthly Spend per Customer | Segment spend indicator | Average monthly debit value | Customer monthly summaries | Rejected records | Debit spend only |
