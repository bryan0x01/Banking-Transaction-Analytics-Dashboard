import pandas as pd

from src.reconcile_data import calculate_reconciliation_totals
from src.run_analysis import calculate_approval_rate, calculate_decline_rate, calculate_net_flow


def _fact_transactions():
    return pd.DataFrame(
        [
            {"transaction_id": "T1", "is_approved": True, "is_declined": False, "signed_transaction_amount": -100.0, "debit_amount": 100.0},
            {"transaction_id": "T2", "is_approved": False, "is_declined": True, "signed_transaction_amount": -50.0, "debit_amount": 50.0},
            {"transaction_id": "T3", "is_approved": True, "is_declined": False, "signed_transaction_amount": 200.0, "debit_amount": 0.0},
        ]
    )


def test_approval_decline_and_net_flow_calculations():
    fact = _fact_transactions()
    assert calculate_approval_rate(fact) == 2 / 3
    assert calculate_decline_rate(fact) == 1 / 3
    assert calculate_net_flow(fact) == 50.0


def test_reconciliation_totals():
    fact = _fact_transactions()
    monthly = pd.DataFrame([{"transaction_count": 3, "debit_transaction_value": 150.0}])
    totals = calculate_reconciliation_totals(fact, monthly)
    assert totals["fact_transaction_count"] == 3
    assert totals["monthly_summary_transaction_count"] == 3
    assert totals["fact_debit_value"] == 150.0
    assert totals["monthly_debit_value"] == 150.0
