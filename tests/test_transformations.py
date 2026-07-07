import pandas as pd

from src.transform_data import build_dim_date, calculate_customer_monthly_summary


def test_date_dimension_contains_expected_fields():
    dim_date = build_dim_date("2024-01-01", "2024-01-03")
    assert dim_date["date_key"].tolist() == [20240101, 20240102, 20240103]
    assert dim_date.loc[0, "month_name"] == "January"


def test_customer_monthly_summary_calculation():
    fact = pd.DataFrame(
        [
            {"transaction_id": "T1", "customer_key": 1, "date_key": 20240101, "is_approved": True, "is_declined": False, "debit_amount": 100.0, "credit_amount": 0.0, "signed_transaction_amount": -100.0, "transaction_amount": 100.0, "is_recurring": False, "is_international": False},
            {"transaction_id": "T2", "customer_key": 1, "date_key": 20240115, "is_approved": True, "is_declined": False, "debit_amount": 0.0, "credit_amount": 500.0, "signed_transaction_amount": 500.0, "transaction_amount": 500.0, "is_recurring": True, "is_international": False},
        ]
    )
    dim_date = build_dim_date("2024-01-01", "2024-01-31")
    summary = calculate_customer_monthly_summary(fact, dim_date)
    assert summary.loc[0, "transaction_count"] == 2
    assert summary.loc[0, "debit_transaction_value"] == 100.0
    assert summary.loc[0, "net_transaction_flow"] == 400.0
