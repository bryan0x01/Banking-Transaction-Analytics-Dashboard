import pandas as pd

from src.validate_data import detect_duplicate_transactions, validate_customer_account_relationship, validate_datasets


def _minimal_cleaned_datasets(transaction_amount=100.0):
    customers = pd.DataFrame(
        [
            {
                "customer_id": "CUST000001",
                "customer_display_name": "Synthetic Customer",
                "age_group": "25-34",
                "city": "Dallas",
                "state": "TX",
                "customer_segment": "Students",
                "account_tenure_months": 12,
                "join_date": pd.to_datetime("2023-01-01").date(),
                "preferred_channel": "Mobile",
                "risk_tier": "Low",
                "income_band": "$40k-$75k",
            }
        ]
    )
    accounts = pd.DataFrame(
        [
            {
                "account_id": "ACC000001",
                "customer_id": "CUST000001",
                "account_type": "Checking",
                "open_date": pd.to_datetime("2024-01-01").date(),
                "account_status": "Active",
                "close_date": pd.NaT,
                "current_balance": 500.0,
                "credit_limit": None,
                "branch_id": "BR001",
                "currency": "USD",
                "product_tier": "Standard",
            }
        ]
    )
    transactions = pd.DataFrame(
        [
            {
                "source_row_number": 1,
                "transaction_id": "TXN00000001",
                "account_id": "ACC000001",
                "customer_id": "CUST000001",
                "merchant_id": "MER0001",
                "transaction_date": pd.to_datetime("2024-02-01").date(),
                "transaction_timestamp": pd.to_datetime("2024-02-01 10:00:00"),
                "transaction_amount": transaction_amount,
                "transaction_category": "Groceries",
                "transaction_type": "Card Purchase",
                "transaction_status": "Approved",
                "transaction_channel": "Mobile",
                "device_id": "DEV00001",
                "branch_id": None,
                "city": "Dallas",
                "state": "TX",
                "currency": "USD",
                "debit_credit_indicator": "Debit",
                "description": "Card Purchase - Groceries",
                "is_international": False,
                "is_recurring": False,
                "balance_after_transaction": 400.0,
                "synthetic_anomaly_flag": False,
            }
        ]
    )
    return {
        "customers": customers,
        "accounts": accounts,
        "transactions": transactions,
        "merchants": pd.DataFrame([{"merchant_id": "MER0001", "merchant_name": "Merchant", "merchant_category": "Groceries", "city": "Dallas", "state": "TX", "region": "South", "is_online_only": False}]),
        "transaction_categories": pd.DataFrame([{"category_id": "CAT01", "transaction_category": "Groceries", "category_group": "Spending"}]),
        "branches": pd.DataFrame([{"branch_id": "BR001", "branch_name": "Dallas Branch", "city": "Dallas", "state": "TX", "region": "South", "branch_type": "Retail"}]),
        "devices": pd.DataFrame([{"device_id": "DEV00001", "customer_id": "CUST000001", "device_type": "Mobile App", "operating_system": "iOS", "trusted_device": True}]),
        "customer_segments": pd.DataFrame([{"segment_id": "SEG01", "segment_name": "Students", "spend_multiplier": 1.0, "digital_preference": 0.8}]),
    }


def test_duplicate_transaction_detection():
    transactions = pd.DataFrame({"transaction_id": ["TXN1", "TXN1", "TXN2"]})
    assert detect_duplicate_transactions(transactions).tolist() == [True, True, False]


def test_invalid_customer_account_relationship_detection():
    transaction = pd.Series({"account_id": "ACC1", "customer_id": "CUST2"})
    lookup = {"ACC1": {"customer_id": "CUST1"}}
    assert validate_customer_account_relationship(transaction, lookup) is False


def test_transaction_amount_validation_creates_issue(tmp_path):
    config = {
        "paths": {"processed_data_dir": str(tmp_path)},
        "supported_currency": ["USD"],
        "date_range": {"start_date": "2024-01-01", "end_date": "2024-12-31"},
    }
    validated = validate_datasets(_minimal_cleaned_datasets(transaction_amount=0.0), config)
    assert "transaction_amount_not_zero" in set(validated["data_quality_issues"]["rule_name"])
    assert len(validated["valid_transactions"]) == 0
