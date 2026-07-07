from __future__ import annotations

import logging

import pandas as pd

from src.utils import project_path, safe_divide, save_dataframe


def calculate_approval_rate(fact_transaction: pd.DataFrame) -> float:
    return safe_divide(float(fact_transaction["is_approved"].sum()), float(len(fact_transaction)))


def calculate_decline_rate(fact_transaction: pd.DataFrame) -> float:
    return safe_divide(float(fact_transaction["is_declined"].sum()), float(len(fact_transaction)))


def calculate_net_flow(fact_transaction: pd.DataFrame) -> float:
    return float(fact_transaction["signed_transaction_amount"].sum())


def calculate_kpis(model_tables: dict[str, pd.DataFrame], anomaly_flags: pd.DataFrame) -> pd.DataFrame:
    fact = model_tables["fact_transaction"]
    customer_monthly = model_tables["fact_customer_monthly_summary"]
    dim_channel = model_tables["dim_channel"]

    channel_fact = fact.merge(dim_channel[["channel_key", "transaction_channel"]], on="channel_key", how="left")
    mobile_online_count = channel_fact["transaction_channel"].isin(["Mobile", "Online"]).sum()

    monthly_totals = customer_monthly.groupby("month_start_date")["debit_transaction_value"].sum().sort_index()
    if len(monthly_totals) >= 2 and monthly_totals.iloc[-2] != 0:
        mom_growth = (monthly_totals.iloc[-1] - monthly_totals.iloc[-2]) / monthly_totals.iloc[-2]
    else:
        mom_growth = 0.0

    metrics = {
        "Total Transaction Count": len(fact),
        "Total Transaction Value": fact["transaction_amount"].sum(),
        "Approved Transaction Count": fact["is_approved"].sum(),
        "Approved Transaction Value": fact["approved_amount"].sum(),
        "Average Transaction Amount": fact["transaction_amount"].mean(),
        "Median Transaction Amount": fact["transaction_amount"].median(),
        "Largest Transaction Amount": fact["transaction_amount"].max(),
        "Active Customer Count": fact["customer_key"].nunique(),
        "Active Account Count": fact["account_key"].nunique(),
        "Transactions Per Customer": safe_divide(len(fact), fact["customer_key"].nunique()),
        "Transactions Per Account": safe_divide(len(fact), fact["account_key"].nunique()),
        "Approval Rate": calculate_approval_rate(fact),
        "Decline Rate": calculate_decline_rate(fact),
        "Reversal Rate": safe_divide(float(fact["is_reversed"].sum()), float(len(fact))),
        "Pending Transaction Rate": safe_divide(float(fact["is_pending"].sum()), float(len(fact))),
        "Debit Transaction Value": fact["debit_amount"].sum(),
        "Credit Transaction Value": fact["credit_amount"].sum(),
        "Net Transaction Flow": calculate_net_flow(fact),
        "International Transaction Percentage": safe_divide(float(fact["is_international"].sum()), float(len(fact))),
        "Recurring Transaction Percentage": safe_divide(float(fact["is_recurring"].sum()), float(len(fact))),
        "Mobile and Online Adoption Rate": safe_divide(float(mobile_online_count), float(len(fact))),
        "High-Value Transaction Count": int((fact["transaction_amount"] >= 5000).sum()),
        "Potential Anomaly Count": len(anomaly_flags),
        "Customers With Anomaly Flags": anomaly_flags["customer_id"].nunique() if not anomaly_flags.empty else 0,
        "Average Customer Monthly Spend": customer_monthly["debit_transaction_value"].mean(),
        "Month-over-Month Transaction Growth": mom_growth,
    }
    return pd.DataFrame([{"metric_name": key, "metric_value": value} for key, value in metrics.items()])


def _format_currency(value: float) -> str:
    return f"${value:,.0f}"


def _format_percent(value: float) -> str:
    return f"{value:.1%}"


def generate_business_insights(model_tables: dict[str, pd.DataFrame], anomaly_flags: pd.DataFrame, reconciliation_report: pd.DataFrame, kpi_summary: pd.DataFrame) -> str:
    fact = model_tables["fact_transaction"]
    dim_category = model_tables["dim_transaction_category"]
    dim_channel = model_tables["dim_channel"]
    dim_customer = model_tables["dim_customer"]
    dim_merchant = model_tables["dim_merchant"]
    dim_date = model_tables["dim_date"]
    issues = model_tables["fact_data_quality_issue"]

    category = fact.merge(dim_category[["transaction_category_key", "transaction_category"]], on="transaction_category_key", how="left")
    category_summary = category.groupby("transaction_category")["transaction_amount"].sum().sort_values(ascending=False)
    top_category = category_summary.index[0]
    top_category_value = category_summary.iloc[0]

    monthly_category = category.merge(dim_date[["date_key", "month_start_date"]], on="date_key", how="left")
    monthly_pivot = monthly_category.groupby(["transaction_category", "month_start_date"])["transaction_amount"].sum().reset_index()
    first_last = monthly_pivot.sort_values("month_start_date").groupby("transaction_category")["transaction_amount"].agg(["first", "last"])
    first_last["growth"] = (first_last["last"] - first_last["first"]) / first_last["first"].replace(0, pd.NA)
    fastest_category = first_last["growth"].dropna().sort_values(ascending=False).index[0]
    fastest_growth = first_last.loc[fastest_category, "growth"]

    channel = fact.merge(dim_channel[["channel_key", "transaction_channel"]], on="channel_key", how="left")
    channel_summary = channel.groupby("transaction_channel").agg(transaction_count=("transaction_id", "count"), decline_count=("is_declined", "sum"))
    channel_summary["decline_rate"] = channel_summary["decline_count"] / channel_summary["transaction_count"]
    top_channel = channel_summary["transaction_count"].sort_values(ascending=False).index[0]
    high_decline_channel = channel_summary["decline_rate"].sort_values(ascending=False).index[0]

    segment = fact.merge(dim_customer[["customer_key", "customer_segment"]], on="customer_key", how="left")
    segment_summary = segment.groupby("customer_segment")["transaction_amount"].mean().sort_values(ascending=False)
    highest_segment = segment_summary.index[0]

    merchant = fact.merge(dim_merchant[["merchant_key", "merchant_name"]], on="merchant_key", how="left")
    merchant_totals = merchant.groupby("merchant_name")["transaction_amount"].sum().sort_values(ascending=False)
    top_10_share = merchant_totals.head(10).sum() / merchant_totals.sum()

    international_rate = fact["is_international"].mean()
    recurring_rate = fact["is_recurring"].mean()
    top_anomaly_rule = "No anomaly flags"
    if not anomaly_flags.empty:
        rule_columns = [
            "high_value_transaction",
            "spending_deviation",
            "rapid_repeat_transaction",
            "geographic_inconsistency",
            "unusual_international_activity",
            "unusual_transaction_time",
            "repeated_declines",
            "balance_issue",
        ]
        top_anomaly_rule = anomaly_flags[rule_columns].sum().sort_values(ascending=False).index[0].replace("_", " ").title()

    top_issue = "No data-quality issues"
    if not issues.empty:
        top_issue = issues["rule_name"].value_counts().index[0].replace("_", " ")

    text = f"""# Business Insights

These findings are based on fully simulated banking data generated by this project. They are useful for dashboard design and analytical review, but they should not be interpreted as real banking conclusions.

## Key Findings

### Highest-spending category
- Observed: `{top_category}` had the highest total transaction value.
- Supporting metric: {_format_currency(float(top_category_value))} in transaction value.
- Possible explanation: The generator assigns realistic larger values to recurring or major spending categories.
- Recommended next step: In Power BI, compare this category by customer segment and month to separate routine spending from spikes.
- Limitation: The result reflects synthetic assumptions, not actual customer behavior.

### Fastest-growing category
- Observed: `{fastest_category}` had the strongest first-to-last-month growth pattern.
- Supporting metric: {_format_percent(float(fastest_growth))} growth from the first available month to the last available month.
- Possible explanation: Seasonal weights and randomized activity can create visible month-to-month changes.
- Recommended next step: Review monthly trends and validate whether seasonality or a few large transactions explain the increase.
- Limitation: Growth is sensitive to the first and last months selected.

### Channel behavior
- Observed: `{top_channel}` was the most-used channel, while `{high_decline_channel}` had the highest decline rate.
- Supporting metric: `{top_channel}` recorded {int(channel_summary.loc[top_channel, "transaction_count"]):,} transactions; `{high_decline_channel}` decline rate was {_format_percent(float(channel_summary.loc[high_decline_channel, "decline_rate"]))}.
- Possible explanation: Digital and point-of-sale channels have higher simulated usage, and decline rates vary by channel.
- Recommended next step: Use the Transaction Status and Operations page to review declines by channel and category.
- Limitation: Decline reasons are simulated and are not tied to real bank processing systems.

### Customer segment behavior
- Observed: `{highest_segment}` had the highest average transaction amount.
- Supporting metric: Average transaction amount was {_format_currency(float(segment_summary.loc[highest_segment]))}.
- Possible explanation: Segment-level spend multipliers create different transaction patterns.
- Recommended next step: Compare segment value with transaction count to identify whether behavior is driven by many small purchases or fewer high-value transactions.
- Limitation: Segments are synthetic and simplified.

### Merchant concentration
- Observed: The top 10 merchants represented {_format_percent(float(top_10_share))} of transaction value.
- Supporting metric: Top 10 merchant value divided by total merchant transaction value.
- Possible explanation: Larger synthetic merchants receive a higher share of common categories.
- Recommended next step: Monitor merchant concentration and drill into unusually large merchants by category.
- Limitation: Merchant names are generated and do not represent real businesses.

### International and recurring activity
- Observed: International transactions represented {_format_percent(float(international_rate))} of activity, and recurring transactions represented {_format_percent(float(recurring_rate))}.
- Supporting metric: Flag counts from the transaction fact table.
- Possible explanation: The generator applies low international activity rates and higher recurring flags for housing, utilities, and subscriptions.
- Recommended next step: Use these flags as slicers in spending and anomaly-review pages.
- Limitation: International behavior uses a simple flag and region approximation.

### Potentially anomalous activity
- Observed: The most common review rule was `{top_anomaly_rule}`.
- Supporting metric: Rule counts from `fact_anomaly_flag`.
- Possible explanation: Rule-based flags are driven by high values, unusual timing, repeated declines, and behavior outside customer norms.
- Recommended next step: Review high-priority records first and compare against normal customer activity.
- Limitation: A flag does not confirm fraud or misconduct; it only identifies transactions worth reviewing.

### Data quality
- Observed: The most common data-quality rule was `{top_issue}`.
- Supporting metric: Issue counts from `fact_data_quality_issue`.
- Possible explanation: The raw generator intentionally introduces realistic issues such as duplicate IDs, invalid relationships, and inconsistent values.
- Recommended next step: Use the Data Quality page to separate blocking errors from warnings before relying on detailed reporting.
- Limitation: The issues are intentionally simulated to demonstrate cleaning and validation workflows.
"""
    return text


def run_analysis(model_tables: dict[str, pd.DataFrame], anomaly_flags: pd.DataFrame, reconciliation_report: pd.DataFrame, config: dict) -> pd.DataFrame:
    logging.info("Starting KPI and insight analysis")
    kpi_summary = calculate_kpis(model_tables, anomaly_flags)
    save_dataframe(kpi_summary, f"{config['paths']['output_dir']}/kpi_summary.csv")

    insight_text = generate_business_insights(model_tables, anomaly_flags, reconciliation_report, kpi_summary)
    insight_path = project_path("docs/business_insights.md")
    insight_path.parent.mkdir(parents=True, exist_ok=True)
    insight_path.write_text(insight_text, encoding="utf-8")
    logging.info("Generated business insights at %s", insight_path)
    return kpi_summary
