import pandas as pd

from src.anomaly_rules import calculate_anomaly_score, flag_high_value_transactions, flag_rapid_repeated_transactions


def test_high_value_transaction_rule():
    transactions = pd.DataFrame({"transaction_amount": [100.0, 6000.0, 5000.0]})
    assert flag_high_value_transactions(transactions, 5000).tolist() == [False, True, True]


def test_rapid_transaction_rule():
    transactions = pd.DataFrame(
        [
            {"transaction_id": "T1", "customer_id": "C1", "merchant_id": "M1", "transaction_amount": 25.0, "transaction_timestamp": "2024-01-01 10:00:00"},
            {"transaction_id": "T2", "customer_id": "C1", "merchant_id": "M1", "transaction_amount": 25.4, "transaction_timestamp": "2024-01-01 10:05:00"},
            {"transaction_id": "T3", "customer_id": "C1", "merchant_id": "M1", "transaction_amount": 25.0, "transaction_timestamp": "2024-01-01 11:00:00"},
        ]
    )
    assert flag_rapid_repeated_transactions(transactions, 10).tolist() == [False, True, False]


def test_anomaly_score_calculation():
    flags = pd.DataFrame(
        {
            "high_value_transaction": [True, False],
            "rapid_repeat_transaction": [True, True],
            "balance_issue": [False, True],
        }
    )
    weights = {"high_value_transaction": 2, "rapid_repeat_transaction": 2, "balance_issue": 2}
    assert calculate_anomaly_score(flags, weights).tolist() == [4, 4]
