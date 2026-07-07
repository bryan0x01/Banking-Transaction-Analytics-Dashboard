from __future__ import annotations

import logging

import pandas as pd

from src.anomaly_rules import STATE_REGION
from src.utils import save_dataframe


UNKNOWN_RECORD = "Unknown"


def _add_surrogate_key(dataframe: pd.DataFrame, key_name: str, start: int = 1) -> pd.DataFrame:
    output = dataframe.reset_index(drop=True).copy()
    output.insert(0, key_name, range(start, start + len(output)))
    return output


def _unknown_row(columns: list[str], key_name: str) -> dict:
    row = {column: UNKNOWN_RECORD for column in columns}
    row[key_name] = 0
    return row


def _lookup(series: pd.Series, mapping: dict, default: int = 0) -> pd.Series:
    return series.map(mapping).fillna(default).astype(int)


def build_dim_date(start_date: str, end_date: str) -> pd.DataFrame:
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    dim_date = pd.DataFrame({"date": dates.date})
    dim_date["date_key"] = dates.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dates.year
    dim_date["quarter"] = "Q" + dates.quarter.astype(str)
    dim_date["month_number"] = dates.month
    dim_date["month_name"] = dates.strftime("%B")
    dim_date["month_start_date"] = dates.to_period("M").to_timestamp().date
    dim_date["week_number"] = dates.isocalendar().week.astype(int)
    dim_date["day_of_week"] = dates.strftime("%A")
    dim_date["is_weekend"] = dates.weekday >= 5
    return dim_date[["date_key", "date", "year", "quarter", "month_number", "month_name", "month_start_date", "week_number", "day_of_week", "is_weekend"]]


def build_dimensions(datasets: dict[str, pd.DataFrame], config: dict) -> dict[str, pd.DataFrame]:
    customers = datasets["customers"].drop_duplicates("customer_id").copy()
    accounts = datasets["accounts"].drop_duplicates("account_id").copy()
    merchants = datasets["merchants"].drop_duplicates("merchant_id").copy()
    categories = datasets["transaction_categories"].drop_duplicates("transaction_category").copy()
    branches = datasets["branches"].drop_duplicates("branch_id").copy()
    devices = datasets["devices"].drop_duplicates("device_id").copy()
    transactions = datasets["valid_transactions"].copy()

    dim_customer = _add_surrogate_key(
        customers[
            [
                "customer_id",
                "customer_display_name",
                "age_group",
                "city",
                "state",
                "customer_segment",
                "account_tenure_months",
                "join_date",
                "preferred_channel",
                "risk_tier",
                "income_band",
            ]
        ],
        "customer_key",
    )
    dim_customer = pd.concat([pd.DataFrame([_unknown_row(dim_customer.columns.tolist(), "customer_key")]), dim_customer], ignore_index=True)

    dim_account = _add_surrogate_key(
        accounts[
            [
                "account_id",
                "customer_id",
                "account_type",
                "open_date",
                "account_status",
                "close_date",
                "current_balance",
                "credit_limit",
                "branch_id",
                "currency",
                "product_tier",
            ]
        ],
        "account_key",
    )
    dim_account = pd.concat([pd.DataFrame([_unknown_row(dim_account.columns.tolist(), "account_key")]), dim_account], ignore_index=True)

    dim_merchant = _add_surrogate_key(
        merchants[["merchant_id", "merchant_name", "merchant_category", "city", "state", "region", "is_online_only"]],
        "merchant_key",
    )
    dim_merchant = pd.concat([pd.DataFrame([_unknown_row(dim_merchant.columns.tolist(), "merchant_key")]), dim_merchant], ignore_index=True)

    dim_transaction_category = _add_surrogate_key(categories[["category_id", "transaction_category", "category_group"]], "transaction_category_key")
    dim_transaction_category = pd.concat(
        [pd.DataFrame([_unknown_row(dim_transaction_category.columns.tolist(), "transaction_category_key")]), dim_transaction_category],
        ignore_index=True,
    )

    dim_date = build_dim_date(config["date_range"]["start_date"], config["date_range"]["end_date"])

    dim_channel = _add_surrogate_key(pd.DataFrame({"transaction_channel": sorted(transactions["transaction_channel"].dropna().unique())}), "channel_key")
    dim_channel = pd.concat([pd.DataFrame([_unknown_row(dim_channel.columns.tolist(), "channel_key")]), dim_channel], ignore_index=True)

    location_source = pd.concat(
        [
            transactions[["city", "state"]],
            customers[["city", "state"]],
            merchants[["city", "state"]],
            branches[["city", "state"]],
        ],
        ignore_index=True,
    ).drop_duplicates()
    location_source["region"] = location_source["state"].map(STATE_REGION).fillna("Unknown")
    dim_location = _add_surrogate_key(location_source[["city", "state", "region"]], "location_key")
    dim_location["location_business_key"] = dim_location["city"].astype(str) + "|" + dim_location["state"].astype(str)
    dim_location = pd.concat([pd.DataFrame([_unknown_row(dim_location.columns.tolist(), "location_key")]), dim_location], ignore_index=True)

    dim_device = _add_surrogate_key(devices[["device_id", "customer_id", "device_type", "operating_system", "trusted_device"]], "device_key")
    dim_device = pd.concat([pd.DataFrame([_unknown_row(dim_device.columns.tolist(), "device_key")]), dim_device], ignore_index=True)

    dim_branch = _add_surrogate_key(branches[["branch_id", "branch_name", "city", "state", "region", "branch_type"]], "branch_key")
    dim_branch = pd.concat([pd.DataFrame([_unknown_row(dim_branch.columns.tolist(), "branch_key")]), dim_branch], ignore_index=True)

    dim_status = _add_surrogate_key(pd.DataFrame({"transaction_status": sorted(transactions["transaction_status"].dropna().unique())}), "transaction_status_key")
    dim_status = pd.concat([pd.DataFrame([_unknown_row(dim_status.columns.tolist(), "transaction_status_key")]), dim_status], ignore_index=True)

    return {
        "dim_customer": dim_customer,
        "dim_account": dim_account,
        "dim_merchant": dim_merchant,
        "dim_transaction_category": dim_transaction_category,
        "dim_date": dim_date,
        "dim_channel": dim_channel,
        "dim_location": dim_location,
        "dim_device": dim_device,
        "dim_branch": dim_branch,
        "dim_transaction_status": dim_status,
    }


def build_fact_transaction(valid_transactions: pd.DataFrame, dimensions: dict[str, pd.DataFrame]) -> pd.DataFrame:
    transactions = valid_transactions.copy()
    transactions["transaction_date"] = pd.to_datetime(transactions["transaction_date"], errors="coerce").dt.date
    transactions["date_key"] = pd.to_datetime(transactions["transaction_date"]).dt.strftime("%Y%m%d").astype(int)
    transactions["location_business_key"] = transactions["city"].astype(str) + "|" + transactions["state"].astype(str)

    customer_map = dimensions["dim_customer"].set_index("customer_id")["customer_key"].to_dict()
    account_map = dimensions["dim_account"].set_index("account_id")["account_key"].to_dict()
    merchant_map = dimensions["dim_merchant"].set_index("merchant_id")["merchant_key"].to_dict()
    category_map = dimensions["dim_transaction_category"].set_index("transaction_category")["transaction_category_key"].to_dict()
    channel_map = dimensions["dim_channel"].set_index("transaction_channel")["channel_key"].to_dict()
    location_map = dimensions["dim_location"].set_index("location_business_key")["location_key"].to_dict()
    device_map = dimensions["dim_device"].set_index("device_id")["device_key"].to_dict()
    branch_map = dimensions["dim_branch"].set_index("branch_id")["branch_key"].to_dict()
    status_map = dimensions["dim_transaction_status"].set_index("transaction_status")["transaction_status_key"].to_dict()

    fact = pd.DataFrame()
    fact["transaction_id"] = transactions["transaction_id"]
    fact["date_key"] = transactions["date_key"]
    fact["customer_key"] = _lookup(transactions["customer_id"], customer_map)
    fact["account_key"] = _lookup(transactions["account_id"], account_map)
    fact["merchant_key"] = _lookup(transactions["merchant_id"], merchant_map)
    fact["transaction_category_key"] = _lookup(transactions["transaction_category"], category_map)
    fact["channel_key"] = _lookup(transactions["transaction_channel"], channel_map)
    fact["location_key"] = _lookup(transactions["location_business_key"], location_map)
    fact["device_key"] = _lookup(transactions["device_id"], device_map)
    fact["branch_key"] = _lookup(transactions["branch_id"], branch_map)
    fact["transaction_status_key"] = _lookup(transactions["transaction_status"], status_map)
    fact["source_row_number"] = transactions["source_row_number"]
    fact["account_id"] = transactions["account_id"]
    fact["customer_id"] = transactions["customer_id"]
    fact["merchant_id"] = transactions["merchant_id"]
    fact["transaction_timestamp"] = transactions["transaction_timestamp"]
    fact["transaction_amount"] = transactions["transaction_amount"].astype(float)
    fact["signed_transaction_amount"] = fact["transaction_amount"].where(transactions["debit_credit_indicator"] == "Credit", -fact["transaction_amount"])
    fact["debit_amount"] = fact["transaction_amount"].where(transactions["debit_credit_indicator"] == "Debit", 0.0)
    fact["credit_amount"] = fact["transaction_amount"].where(transactions["debit_credit_indicator"] == "Credit", 0.0)
    fact["approved_amount"] = fact["transaction_amount"].where(transactions["transaction_status"] == "Approved", 0.0)
    fact["transaction_count"] = 1
    fact["is_approved"] = transactions["transaction_status"] == "Approved"
    fact["is_declined"] = transactions["transaction_status"] == "Declined"
    fact["is_pending"] = transactions["transaction_status"] == "Pending"
    fact["is_reversed"] = transactions["transaction_status"] == "Reversed"
    fact["is_international"] = transactions["is_international"]
    fact["is_recurring"] = transactions["is_recurring"]
    fact["debit_credit_indicator"] = transactions["debit_credit_indicator"]
    fact["balance_after_transaction"] = transactions["balance_after_transaction"].astype(float)
    fact.insert(0, "transaction_key", range(1, len(fact) + 1))
    return fact


def calculate_customer_monthly_summary(fact_transaction: pd.DataFrame, dim_date: pd.DataFrame) -> pd.DataFrame:
    data = fact_transaction.merge(dim_date[["date_key", "month_start_date"]], on="date_key", how="left")
    summary = (
        data.groupby(["customer_key", "month_start_date"], dropna=False)
        .agg(
            transaction_count=("transaction_id", "count"),
            approved_transaction_count=("is_approved", "sum"),
            declined_transaction_count=("is_declined", "sum"),
            debit_transaction_value=("debit_amount", "sum"),
            credit_transaction_value=("credit_amount", "sum"),
            net_transaction_flow=("signed_transaction_amount", "sum"),
            average_transaction_amount=("transaction_amount", "mean"),
            recurring_transaction_count=("is_recurring", "sum"),
            international_transaction_count=("is_international", "sum"),
        )
        .reset_index()
    )
    summary["month_date_key"] = pd.to_datetime(summary["month_start_date"]).dt.strftime("%Y%m%d").astype(int)
    summary.insert(0, "customer_monthly_summary_key", range(1, len(summary) + 1))
    return summary


def build_account_daily_balance(fact_transaction: pd.DataFrame, dim_date: pd.DataFrame) -> pd.DataFrame:
    data = fact_transaction[fact_transaction["is_approved"]].copy()
    data["transaction_timestamp"] = pd.to_datetime(data["transaction_timestamp"], errors="coerce")
    data = data.sort_values(["account_key", "date_key", "transaction_timestamp"])
    daily = data.groupby(["account_key", "date_key"], as_index=False).tail(1)
    daily = daily[["account_key", "date_key", "balance_after_transaction"]].rename(columns={"balance_after_transaction": "ending_balance"})
    daily.insert(0, "account_daily_balance_key", range(1, len(daily) + 1))
    return daily


def build_fact_data_quality_issue(issues: pd.DataFrame) -> pd.DataFrame:
    fact = issues.copy()
    if "data_quality_issue_key" not in fact.columns:
        fact.insert(0, "data_quality_issue_key", range(1, len(fact) + 1))
    return fact


def build_model_tables(validated: dict[str, pd.DataFrame], config: dict) -> dict[str, pd.DataFrame]:
    logging.info("Starting dimensional transformations")
    dimensions = build_dimensions(validated, config)
    fact_transaction = build_fact_transaction(validated["valid_transactions"], dimensions)
    fact_customer_monthly_summary = calculate_customer_monthly_summary(fact_transaction, dimensions["dim_date"])
    fact_account_daily_balance = build_account_daily_balance(fact_transaction, dimensions["dim_date"])
    fact_data_quality_issue = build_fact_data_quality_issue(validated["data_quality_issues"])

    tables = {
        **dimensions,
        "fact_transaction": fact_transaction,
        "fact_account_daily_balance": fact_account_daily_balance,
        "fact_customer_monthly_summary": fact_customer_monthly_summary,
        "fact_data_quality_issue": fact_data_quality_issue,
    }

    processed_dir = config["paths"]["processed_data_dir"]
    for table_name, dataframe in tables.items():
        save_dataframe(dataframe, f"{processed_dir}/{table_name}.csv")
        logging.info("Built %s with %s rows", table_name, len(dataframe))

    return tables
