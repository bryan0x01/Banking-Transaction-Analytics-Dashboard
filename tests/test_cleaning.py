import pandas as pd

from src.clean_data import normalize_category, normalize_channel, normalize_status
from src.utils import parse_currency, parse_date_series, standardize_column_names


def test_column_standardization():
    dataframe = pd.DataFrame(columns=[" Transaction ID ", "Customer Name", "Amount ($)"])
    cleaned = standardize_column_names(dataframe)
    assert cleaned.columns.tolist() == ["transaction_id", "customer_name", "amount"]


def test_category_status_and_channel_normalization():
    assert normalize_category(" dinning ") == "Dining"
    assert normalize_category("ATM Withdrawal") == "Cash Withdrawal"
    assert normalize_status(" apprved ") == "Approved"
    assert normalize_channel("POS") == "Point of Sale"
    assert normalize_channel("point-of-sale") == "Point of Sale"


def test_currency_conversion():
    assert parse_currency("$1,234.50") == 1234.50
    assert parse_currency("(25.00)") == -25.00
    assert parse_currency("") is None


def test_date_parsing_mixed_formats():
    parsed = parse_date_series(pd.Series(["2024-01-05", "02/10/2024", "Mar 15, 2024"]))
    assert [value.isoformat() for value in parsed] == ["2024-01-05", "2024-02-10", "2024-03-15"]
