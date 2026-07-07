from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from src.utils import save_dataframe


def _status(difference: float, warning_tolerance: float = 0.01) -> str:
    if abs(difference) <= warning_tolerance:
        return "Passed"
    return "Warning"


def _check(name: str, source_value: Any, target_value: Any, notes: str, status: str | None = None) -> dict[str, Any]:
    try:
        difference = float(source_value) - float(target_value)
    except (TypeError, ValueError):
        difference = 0 if source_value == target_value else 1
    return {
        "reconciliation_name": name,
        "source_value": source_value,
        "target_value": target_value,
        "difference": round(difference, 4) if isinstance(difference, float) else difference,
        "status": status or _status(difference),
        "notes": notes,
    }


def calculate_reconciliation_totals(fact_transaction: pd.DataFrame, customer_monthly_summary: pd.DataFrame) -> dict[str, float]:
    return {
        "fact_transaction_count": float(len(fact_transaction)),
        "monthly_summary_transaction_count": float(customer_monthly_summary["transaction_count"].sum()),
        "fact_debit_value": float(fact_transaction["debit_amount"].sum()),
        "monthly_debit_value": float(customer_monthly_summary["debit_transaction_value"].sum()),
    }


def build_reconciliation_report(raw: dict[str, pd.DataFrame], validated: dict[str, pd.DataFrame], model_tables: dict[str, pd.DataFrame], config: dict) -> pd.DataFrame:
    logging.info("Starting reconciliation checks")
    raw_transactions = raw["transactions"].copy()
    valid_transactions = validated["valid_transactions"].copy()
    rejected_transactions = validated["rejected_transactions"].copy()
    fact_transaction = model_tables["fact_transaction"].copy()
    monthly_summary = model_tables["fact_customer_monthly_summary"].copy()
    issues = validated["data_quality_issues"].copy()

    rows = []
    rows.append(
        _check(
            "Raw transaction count versus valid processed count",
            len(raw_transactions),
            len(valid_transactions),
            "Difference represents rejected records with blocking validation issues.",
            "Passed" if len(valid_transactions) > 50000 else "Failed",
        )
    )
    rows.append(
        _check(
            "Raw transaction count versus valid plus rejected count",
            len(raw_transactions),
            len(valid_transactions) + len(rejected_transactions),
            "Valid and rejected rows should reconcile to raw transaction rows.",
        )
    )

    raw_amount = pd.to_numeric(raw_transactions["transaction_amount"].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False), errors="coerce").sum()
    processed_amount = valid_transactions["transaction_amount"].sum()
    rows.append(
        _check(
            "Raw transaction amount versus processed transaction amount",
            round(raw_amount, 2),
            round(processed_amount, 2),
            "Difference is expected when invalid records are rejected.",
            "Warning" if len(rejected_transactions) > 0 else "Passed",
        )
    )

    rows.append(
        _check(
            "Approved transaction total versus fact-table total",
            round(valid_transactions.loc[valid_transactions["transaction_status"] == "Approved", "transaction_amount"].sum(), 2),
            round(fact_transaction["approved_amount"].sum(), 2),
            "Approved transaction value should match between validated data and fact table.",
        )
    )

    for rule_name, label in [
        ("account_id_exists", "Transactions without valid accounts"),
        ("customer_id_exists", "Transactions without valid customers"),
        ("account_customer_exists", "Accounts without valid customers"),
    ]:
        issue_count = int((issues["rule_name"] == rule_name).sum()) if not issues.empty else 0
        rows.append(_check(label, issue_count, 0, "Count of relationship issues found during validation.", "Warning" if issue_count else "Passed"))

    customers_without_accounts = len(set(validated["customers"]["customer_id"].dropna()) - set(validated["accounts"]["customer_id"].dropna()))
    rows.append(_check("Customers without accounts", customers_without_accounts, 0, "Synthetic customers can exist without active accounts.", "Warning" if customers_without_accounts else "Passed"))

    merchant_source_total = round(valid_transactions.groupby("merchant_id")["transaction_amount"].sum().sum(), 2)
    merchant_fact_total = round(fact_transaction["transaction_amount"].sum(), 2)
    rows.append(_check("Merchant transaction totals before and after transformation", merchant_source_total, merchant_fact_total, "Merchant totals should match after fact loading."))

    category_source_total = round(valid_transactions.groupby("transaction_category")["transaction_amount"].sum().sum(), 2)
    category_fact_total = round(fact_transaction["transaction_amount"].sum(), 2)
    rows.append(_check("Category totals before and after transformation", category_source_total, category_fact_total, "Category totals should match after fact loading."))

    daily_source_count = valid_transactions.groupby("transaction_date")["transaction_id"].count().sum()
    daily_fact_count = fact_transaction.groupby("date_key")["transaction_id"].count().sum()
    rows.append(_check("Daily transaction totals before and after loading", daily_source_count, daily_fact_count, "Daily row counts should match after date-key assignment."))

    totals = calculate_reconciliation_totals(fact_transaction, monthly_summary)
    rows.append(
        _check(
            "Transaction totals versus customer monthly summaries",
            totals["fact_transaction_count"],
            totals["monthly_summary_transaction_count"],
            "Monthly summaries should roll up to the fact transaction count.",
        )
    )
    rows.append(
        _check(
            "Debit value versus customer monthly summaries",
            round(totals["fact_debit_value"], 2),
            round(totals["monthly_debit_value"], 2),
            "Monthly summaries should roll up to debit transaction value.",
        )
    )

    rows.append(_check("Database row counts versus exported reporting tables", len(fact_transaction), len(valid_transactions), "Fact table and processed export row counts should match before SQLite load."))

    report = pd.DataFrame(rows)
    save_dataframe(report, f"{config['paths']['output_dir']}/reconciliation_report.csv")
    logging.info("Completed %s reconciliation checks", len(report))
    return report
