from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from src.clean_data import VALID_ACCOUNT_TYPES, VALID_CATEGORIES, VALID_CHANNELS, VALID_STATUSES, VALID_TRANSACTION_TYPES
from src.utils import save_dataframe


VALID_CATEGORY_NAMES = set(VALID_CATEGORIES.values())
VALID_STATUS_NAMES = set(VALID_STATUSES.values())
VALID_CHANNEL_NAMES = set(VALID_CHANNELS.values())
VALID_ACCOUNT_TYPE_NAMES = set(VALID_ACCOUNT_TYPES.values())
VALID_TRANSACTION_TYPE_NAMES = set(VALID_TRANSACTION_TYPES.values())
VALID_SEGMENTS = {"Students", "Young Professionals", "Families", "Affluent", "Retirees", "Small Business"}
DIGITAL_CHANNELS = {"Mobile", "Online", "Point of Sale"}


def _issue(
    issues: list[dict[str, Any]],
    source_file: str,
    record_identifier: Any,
    column_name: str,
    rule_name: str,
    severity: str,
    description: str,
    original_value: Any,
) -> None:
    issues.append(
        {
            "source_file": source_file,
            "record_identifier": record_identifier,
            "column_name": column_name,
            "rule_name": rule_name,
            "severity": severity,
            "description": description,
            "original_value": "" if pd.isna(original_value) else original_value,
            "detected_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "resolution_status": "Open",
        }
    )


def validate_required_columns(dataset_name: str, dataframe: pd.DataFrame, required_columns: list[str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for column in required_columns:
        if column not in dataframe.columns:
            _issue(issues, f"{dataset_name}.csv", "DATASET", column, "required_source_column", "Critical", f"Missing required column {column}", "")
    return issues


def detect_duplicate_transactions(transactions: pd.DataFrame) -> pd.Series:
    transaction_ids = transactions["transaction_id"]
    return transaction_ids.notna() & transaction_ids.duplicated(keep=False)


def validate_customer_account_relationship(transaction: pd.Series, account_lookup: dict[str, dict[str, Any]]) -> bool:
    account_id = transaction.get("account_id")
    if account_id not in account_lookup:
        return False
    return account_lookup[account_id]["customer_id"] == transaction.get("customer_id")


def _validate_customer_records(customers: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    duplicate_mask = customers["customer_id"].notna() & customers["customer_id"].duplicated(keep=False)
    for _, row in customers[duplicate_mask].iterrows():
        _issue(issues, "customers.csv", row["customer_id"], "customer_id", "duplicate_customer_id", "Warning", "Duplicate customer record found", row["customer_id"])

    invalid_segment_mask = ~customers["customer_segment"].isin(VALID_SEGMENTS)
    for _, row in customers[invalid_segment_mask].iterrows():
        _issue(issues, "customers.csv", row["customer_id"], "customer_segment", "valid_customer_segment", "Error", "Customer segment is not in the configured segment list", row["customer_segment"])


def _validate_account_records(accounts: pd.DataFrame, customers: pd.DataFrame, branches: pd.DataFrame, issues: list[dict[str, Any]]) -> None:
    valid_customers = set(customers["customer_id"].dropna())
    valid_branches = set(branches["branch_id"].dropna())
    for _, row in accounts.iterrows():
        record_id = row.get("account_id")
        if row.get("customer_id") not in valid_customers:
            _issue(issues, "accounts.csv", record_id, "customer_id", "account_customer_exists", "Error", "Account references a customer that does not exist", row.get("customer_id"))
        if row.get("account_type") not in VALID_ACCOUNT_TYPE_NAMES:
            _issue(issues, "accounts.csv", record_id, "account_type", "valid_account_type", "Error", "Account type is not valid", row.get("account_type"))
        if row.get("branch_id") not in valid_branches:
            _issue(issues, "accounts.csv", record_id, "branch_id", "account_branch_exists", "Error", "Account references a branch that does not exist", row.get("branch_id"))


def _transaction_has_blocking_issue(transaction_id: str, row_number: int, blocking_keys: set[tuple[str, Any]]) -> bool:
    return ("transaction_id", transaction_id) in blocking_keys or ("source_row_number", row_number) in blocking_keys


def validate_datasets(cleaned: dict[str, pd.DataFrame], config: dict) -> dict[str, pd.DataFrame]:
    logging.info("Starting validation checks")
    issues: list[dict[str, Any]] = []
    transactions = cleaned["transactions"].copy()
    customers = cleaned["customers"].copy()
    accounts = cleaned["accounts"].copy()
    merchants = cleaned["merchants"].copy()
    branches = cleaned["branches"].copy()
    devices = cleaned["devices"].copy()
    categories = cleaned["transaction_categories"].copy()

    required = {
        "transactions": [
            "transaction_id",
            "account_id",
            "customer_id",
            "merchant_id",
            "transaction_date",
            "transaction_timestamp",
            "transaction_amount",
            "transaction_category",
            "transaction_type",
            "transaction_status",
            "transaction_channel",
            "currency",
            "debit_credit_indicator",
            "balance_after_transaction",
        ],
        "customers": ["customer_id", "customer_segment", "join_date"],
        "accounts": ["account_id", "customer_id", "account_type", "open_date", "account_status", "branch_id"],
    }
    for dataset_name, required_columns in required.items():
        issues.extend(validate_required_columns(dataset_name, cleaned[dataset_name], required_columns))

    _validate_customer_records(customers, issues)
    _validate_account_records(accounts, customers, branches, issues)

    valid_customers = set(customers.drop_duplicates("customer_id")["customer_id"].dropna())
    account_lookup = accounts.drop_duplicates("account_id").set_index("account_id").to_dict("index")
    merchant_ids = set(merchants["merchant_id"].dropna())
    branch_ids = set(branches["branch_id"].dropna())
    device_ids = set(devices["device_id"].dropna())
    category_names = set(categories["transaction_category"].dropna())
    supported_currencies = set(config["supported_currency"])
    configured_start_date = pd.to_datetime(config["date_range"]["start_date"])
    configured_end_date = pd.to_datetime(config["date_range"]["end_date"])
    duplicate_mask = detect_duplicate_transactions(transactions)
    blocking_keys: set[tuple[str, Any]] = set()

    for _, row in transactions.iterrows():
        transaction_id = row.get("transaction_id")
        row_number = row.get("source_row_number")
        row_key = ("source_row_number", row_number)
        record_id = transaction_id or f"row_{row_number}"

        def add_transaction_issue(column: str, rule: str, severity: str, description: str, original_value: Any, blocking: bool = False) -> None:
            _issue(issues, "transactions.csv", record_id, column, rule, severity, description, original_value)
            if blocking:
                blocking_keys.add(row_key)
                if transaction_id:
                    blocking_keys.add(("transaction_id", transaction_id))

        if not transaction_id:
            add_transaction_issue("transaction_id", "transaction_id_present", "Critical", "Transaction ID is missing", transaction_id, True)
        elif bool(duplicate_mask.loc[row.name]):
            add_transaction_issue("transaction_id", "transaction_id_unique", "Error", "Transaction ID is duplicated", transaction_id, True)

        if row.get("customer_id") not in valid_customers:
            add_transaction_issue("customer_id", "customer_id_exists", "Error", "Customer ID does not exist", row.get("customer_id"), True)

        account_id = row.get("account_id")
        if account_id not in account_lookup:
            add_transaction_issue("account_id", "account_id_exists", "Error", "Account ID does not exist", account_id, True)
        elif not validate_customer_account_relationship(row, account_lookup):
            add_transaction_issue("account_id", "account_belongs_to_customer", "Error", "Account does not belong to the listed customer", account_id, True)
        else:
            account = account_lookup[account_id]
            transaction_date = pd.to_datetime(row.get("transaction_date"), errors="coerce")
            open_date = pd.to_datetime(account.get("open_date"), errors="coerce")
            close_date = pd.to_datetime(account.get("close_date"), errors="coerce")
            if pd.notna(transaction_date) and pd.notna(open_date) and transaction_date < open_date:
                add_transaction_issue("transaction_date", "transaction_after_account_open", "Error", "Transaction date is before account open date", row.get("transaction_date"), True)
            if account.get("account_status") == "Closed" and pd.notna(close_date) and pd.notna(transaction_date) and transaction_date > close_date:
                add_transaction_issue("transaction_date", "transaction_before_account_close", "Error", "Transaction occurs after the account close date", row.get("transaction_date"), True)

        if row.get("merchant_id") not in merchant_ids:
            add_transaction_issue("merchant_id", "merchant_id_exists", "Error", "Merchant ID does not exist", row.get("merchant_id"), True)

        amount = row.get("transaction_amount")
        if pd.isna(amount):
            add_transaction_issue("transaction_amount", "transaction_amount_numeric", "Error", "Transaction amount is not numeric", amount, True)
        elif amount == 0:
            add_transaction_issue("transaction_amount", "transaction_amount_not_zero", "Error", "Transaction amount is zero", amount, True)
        elif amount < 0:
            add_transaction_issue("transaction_amount", "purchase_amount_positive", "Error", "Transaction amount should be positive with debit or credit direction stored separately", amount, True)

        parsed_transaction_date = pd.to_datetime(row.get("transaction_date"), errors="coerce")
        if pd.isna(parsed_transaction_date):
            add_transaction_issue("transaction_date", "transaction_date_valid", "Error", "Transaction date is not valid", row.get("transaction_date"), True)
        elif parsed_transaction_date < configured_start_date or parsed_transaction_date > configured_end_date:
            add_transaction_issue("transaction_date", "transaction_date_in_reporting_range", "Error", "Transaction date is outside the configured reporting range", row.get("transaction_date"), True)
        if pd.isna(pd.to_datetime(row.get("transaction_timestamp"), errors="coerce")):
            add_transaction_issue("transaction_timestamp", "transaction_timestamp_valid", "Error", "Transaction timestamp is not valid", row.get("transaction_timestamp"), True)
        if row.get("transaction_category") not in category_names or row.get("transaction_category") not in VALID_CATEGORY_NAMES:
            add_transaction_issue("transaction_category", "transaction_category_valid", "Error", "Transaction category is not valid", row.get("transaction_category"), True)
        if row.get("transaction_type") not in VALID_TRANSACTION_TYPE_NAMES:
            add_transaction_issue("transaction_type", "transaction_type_valid", "Error", "Transaction type is not valid", row.get("transaction_type"), True)
        if row.get("transaction_status") not in VALID_STATUS_NAMES:
            add_transaction_issue("transaction_status", "transaction_status_valid", "Error", "Transaction status is not valid", row.get("transaction_status"), True)
        if row.get("transaction_channel") not in VALID_CHANNEL_NAMES:
            add_transaction_issue("transaction_channel", "transaction_channel_valid", "Error", "Transaction channel is not valid", row.get("transaction_channel"), True)
        if row.get("currency") not in supported_currencies:
            add_transaction_issue("currency", "currency_supported", "Error", "Currency is not supported", row.get("currency"), True)
        if row.get("branch_id") and row.get("branch_id") not in branch_ids:
            add_transaction_issue("branch_id", "branch_id_exists", "Error", "Branch ID does not exist", row.get("branch_id"), True)
        if row.get("transaction_channel") in {"Branch", "ATM"} and not row.get("branch_id"):
            add_transaction_issue("branch_id", "branch_required_for_channel", "Warning", "Branch or ATM transactions should include a branch ID", row.get("branch_id"))
        if row.get("device_id") and row.get("device_id") not in device_ids:
            add_transaction_issue("device_id", "device_id_exists", "Warning", "Device ID does not exist", row.get("device_id"))
        if row.get("transaction_channel") in DIGITAL_CHANNELS and not row.get("device_id"):
            add_transaction_issue("device_id", "device_expected_for_digital_transaction", "Warning", "Digital transactions usually include a device ID", row.get("device_id"))
        if pd.isna(row.get("balance_after_transaction")):
            add_transaction_issue("balance_after_transaction", "balance_numeric", "Error", "Balance after transaction is not numeric", row.get("balance_after_transaction"), True)

    transactions["has_blocking_quality_issue"] = transactions.apply(
        lambda row: _transaction_has_blocking_issue(row.get("transaction_id"), row.get("source_row_number"), blocking_keys),
        axis=1,
    )
    valid_transactions = transactions[~transactions["has_blocking_quality_issue"]].copy()
    rejected_transactions = transactions[transactions["has_blocking_quality_issue"]].copy()

    issue_frame = pd.DataFrame(issues)
    if issue_frame.empty:
        issue_frame = pd.DataFrame(
            columns=[
                "source_file",
                "record_identifier",
                "column_name",
                "rule_name",
                "severity",
                "description",
                "original_value",
                "detected_timestamp",
                "resolution_status",
            ]
        )
    issue_frame.insert(0, "issue_id", [f"DQI{i:07d}" for i in range(1, len(issue_frame) + 1)])

    processed_dir = config["paths"]["processed_data_dir"]
    save_dataframe(valid_transactions, f"{processed_dir}/valid_transactions.csv")
    save_dataframe(rejected_transactions, f"{processed_dir}/rejected_transactions.csv")
    save_dataframe(issue_frame, f"{processed_dir}/data_quality_issues.csv")

    logging.info("Validation found %s issues and %s rejected transaction rows", len(issue_frame), len(rejected_transactions))
    return {
        **cleaned,
        "valid_transactions": valid_transactions,
        "rejected_transactions": rejected_transactions,
        "data_quality_issues": issue_frame,
    }
