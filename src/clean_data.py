from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.utils import clean_text, parse_bool, parse_currency, parse_date_series, parse_timestamp_series, save_dataframe, title_clean


VALID_CATEGORIES = {
    "groceries": "Groceries",
    "grocery": "Groceries",
    "dining": "Dining",
    "dinning": "Dining",
    "restaurants": "Dining",
    "transportation": "Transportation",
    "transport": "Transportation",
    "travel": "Travel",
    "entertainment": "Entertainment",
    "utilities": "Utilities",
    "utility": "Utilities",
    "housing": "Housing",
    "rent": "Housing",
    "mortgage": "Housing",
    "healthcare": "Healthcare",
    "health care": "Healthcare",
    "retail": "Retail",
    "shopping": "Retail",
    "education": "Education",
    "cash withdrawal": "Cash Withdrawal",
    "atm withdrawal": "Cash Withdrawal",
    "atm": "Cash Withdrawal",
    "transfers": "Transfers",
    "transfer": "Transfers",
    "subscription services": "Subscription Services",
    "subscriptions": "Subscription Services",
    "fees and charges": "Fees and Charges",
    "fees": "Fees and Charges",
}

VALID_STATUSES = {
    "approved": "Approved",
    "apprved": "Approved",
    "declined": "Declined",
    "pending": "Pending",
    "reversed": "Reversed",
}

VALID_CHANNELS = {
    "mobile": "Mobile",
    "online": "Online",
    "atm": "ATM",
    "branch": "Branch",
    "point of sale": "Point of Sale",
    "point-of-sale": "Point of Sale",
    "pos": "Point of Sale",
    "automatic payment": "Automatic Payment",
    "auto payment": "Automatic Payment",
}

VALID_ACCOUNT_TYPES = {
    "checking": "Checking",
    "savings": "Savings",
    "credit card": "Credit Card",
    "money market": "Money Market",
}

VALID_TRANSACTION_TYPES = {
    "card purchase": "Card Purchase",
    "ach payment": "ACH Payment",
    "bank transfer": "Bank Transfer",
    "atm withdrawal": "ATM Withdrawal",
    "cash withdrawal": "ATM Withdrawal",
    "direct deposit": "Direct Deposit",
    "bill payment": "Bill Payment",
    "automatic payment": "Bill Payment",
    "refund": "Refund",
    "bank fee": "Bank Fee",
    "cash deposit": "Cash Deposit",
}


def _lookup_normalized(value: Any, mapping: dict[str, str]) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    lowered = text.lower().replace("_", " ").replace("-", " ")
    lowered = " ".join(lowered.split())
    return mapping.get(lowered, text.title())


def normalize_category(value: Any) -> str | None:
    return _lookup_normalized(value, VALID_CATEGORIES)


def normalize_status(value: Any) -> str | None:
    return _lookup_normalized(value, VALID_STATUSES)


def normalize_channel(value: Any) -> str | None:
    return _lookup_normalized(value, VALID_CHANNELS)


def normalize_account_type(value: Any) -> str | None:
    return _lookup_normalized(value, VALID_ACCOUNT_TYPES)


def normalize_transaction_type(value: Any) -> str | None:
    return _lookup_normalized(value, VALID_TRANSACTION_TYPES)


def normalize_currency(value: Any) -> str | None:
    text = clean_text(value)
    return text.upper() if text else None


def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    output = customers.copy()
    output["customer_id"] = output["customer_id"].map(lambda value: clean_text(value).upper() if clean_text(value) else None)
    output["customer_display_name"] = output["customer_display_name"].map(title_clean)
    output["age_group"] = output["age_group"].map(clean_text)
    output["city"] = output["city"].map(title_clean)
    output["state"] = output["state"].map(lambda value: clean_text(value).upper() if clean_text(value) else None)
    output["customer_segment"] = output["customer_segment"].map(title_clean)
    output["account_tenure_months"] = pd.to_numeric(output["account_tenure_months"], errors="coerce").astype("Int64")
    output["join_date"] = parse_date_series(output["join_date"])
    output["preferred_channel"] = output["preferred_channel"].map(normalize_channel)
    output["risk_tier"] = output["risk_tier"].map(title_clean)
    output["income_band"] = output["income_band"].map(clean_text)
    return output


def clean_accounts(accounts: pd.DataFrame) -> pd.DataFrame:
    output = accounts.copy()
    output["account_id"] = output["account_id"].map(lambda value: clean_text(value).upper() if clean_text(value) else None)
    output["customer_id"] = output["customer_id"].map(lambda value: clean_text(value).upper() if clean_text(value) else None)
    output["account_type"] = output["account_type"].map(normalize_account_type)
    output["open_date"] = parse_date_series(output["open_date"])
    output["account_status"] = output["account_status"].map(title_clean)
    output["close_date"] = parse_date_series(output["close_date"])
    output["current_balance"] = output["current_balance"].map(parse_currency)
    output["credit_limit"] = output["credit_limit"].map(parse_currency)
    output["branch_id"] = output["branch_id"].map(lambda value: clean_text(value).upper() if clean_text(value) else None)
    output["currency"] = output["currency"].map(normalize_currency)
    output["product_tier"] = output["product_tier"].map(title_clean)
    return output


def clean_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    output = transactions.copy()
    output.insert(0, "source_row_number", range(1, len(output) + 1))
    for column in ["transaction_id", "account_id", "customer_id", "merchant_id", "device_id", "branch_id"]:
        output[column] = output[column].map(lambda value: clean_text(value).upper() if clean_text(value) else None)
    output["transaction_date"] = parse_date_series(output["transaction_date"])
    output["transaction_timestamp"] = parse_timestamp_series(output["transaction_timestamp"])
    output["transaction_amount"] = output["transaction_amount"].map(parse_currency)
    output["transaction_category"] = output["transaction_category"].map(normalize_category)
    output["transaction_type"] = output["transaction_type"].map(normalize_transaction_type)
    output["transaction_status"] = output["transaction_status"].map(normalize_status)
    output["transaction_channel"] = output["transaction_channel"].map(normalize_channel)
    output["city"] = output["city"].map(title_clean)
    output["state"] = output["state"].map(lambda value: clean_text(value).upper() if clean_text(value) else None)
    output["currency"] = output["currency"].map(normalize_currency)
    output["debit_credit_indicator"] = output["debit_credit_indicator"].map(title_clean)
    output["description"] = output["description"].map(clean_text)
    output["is_international"] = output["is_international"].map(parse_bool)
    output["is_recurring"] = output["is_recurring"].map(parse_bool)
    output["balance_after_transaction"] = output["balance_after_transaction"].map(parse_currency)
    output["synthetic_anomaly_flag"] = output["synthetic_anomaly_flag"].map(parse_bool)
    return output


def clean_reference_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    output = dataframe.copy()
    for column in output.columns:
        if column.endswith("_id"):
            output[column] = output[column].map(lambda value: clean_text(value).upper() if clean_text(value) else None)
        elif "date" not in column:
            output[column] = output[column].map(clean_text)
    for column in ["city", "region", "branch_name", "merchant_name", "category_group", "segment_name"]:
        if column in output.columns:
            output[column] = output[column].map(title_clean)
    if "transaction_category" in output.columns:
        output["transaction_category"] = output["transaction_category"].map(normalize_category)
    if "merchant_category" in output.columns:
        output["merchant_category"] = output["merchant_category"].map(normalize_category)
    if "state" in output.columns:
        output["state"] = output["state"].map(lambda value: clean_text(value).upper() if clean_text(value) else None)
    if "is_online_only" in output.columns:
        output["is_online_only"] = output["is_online_only"].map(parse_bool)
    if "trusted_device" in output.columns:
        output["trusted_device"] = output["trusted_device"].map(parse_bool)
    return output


def clean_datasets(datasets: dict[str, pd.DataFrame], config: dict) -> dict[str, pd.DataFrame]:
    logging.info("Starting data cleaning")
    cleaned = {
        "customers": clean_customers(datasets["customers"]),
        "accounts": clean_accounts(datasets["accounts"]),
        "transactions": clean_transactions(datasets["transactions"]),
        "merchants": clean_reference_table(datasets["merchants"]),
        "transaction_categories": clean_reference_table(datasets["transaction_categories"]),
        "branches": clean_reference_table(datasets["branches"]),
        "devices": clean_reference_table(datasets["devices"]),
        "customer_segments": clean_reference_table(datasets["customer_segments"]),
    }

    processed_dir = config["paths"]["processed_data_dir"]
    for name, dataframe in cleaned.items():
        save_dataframe(dataframe, f"{processed_dir}/cleaned_{name}.csv")
        logging.info("Cleaned %s rows for %s", len(dataframe), name)

    return cleaned
