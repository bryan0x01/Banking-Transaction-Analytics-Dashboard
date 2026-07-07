from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils import project_path, save_dataframe


TRANSACTION_CATEGORIES = [
    ("CAT01", "Groceries"),
    ("CAT02", "Dining"),
    ("CAT03", "Transportation"),
    ("CAT04", "Travel"),
    ("CAT05", "Entertainment"),
    ("CAT06", "Utilities"),
    ("CAT07", "Housing"),
    ("CAT08", "Healthcare"),
    ("CAT09", "Retail"),
    ("CAT10", "Education"),
    ("CAT11", "Cash Withdrawal"),
    ("CAT12", "Transfers"),
    ("CAT13", "Subscription Services"),
    ("CAT14", "Fees and Charges"),
]

TRANSACTION_TYPES = [
    "Card Purchase",
    "ACH Payment",
    "Bank Transfer",
    "ATM Withdrawal",
    "Direct Deposit",
    "Bill Payment",
    "Refund",
    "Bank Fee",
    "Cash Deposit",
]

CHANNELS = ["Mobile", "Online", "ATM", "Branch", "Point of Sale", "Automatic Payment"]
STATUSES = ["Approved", "Declined", "Pending", "Reversed"]
ACCOUNT_TYPES = ["Checking", "Savings", "Credit Card", "Money Market"]
PRODUCT_TIERS = ["Basic", "Standard", "Premium"]
RISK_TIERS = ["Low", "Medium", "High"]
INCOME_BANDS = ["Under $40k", "$40k-$75k", "$75k-$125k", "$125k+"]
AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]

SEGMENTS = [
    {"segment_id": "SEG01", "segment_name": "Students", "spend_multiplier": 0.75, "digital_preference": 0.85},
    {"segment_id": "SEG02", "segment_name": "Young Professionals", "spend_multiplier": 1.10, "digital_preference": 0.82},
    {"segment_id": "SEG03", "segment_name": "Families", "spend_multiplier": 1.25, "digital_preference": 0.68},
    {"segment_id": "SEG04", "segment_name": "Affluent", "spend_multiplier": 1.70, "digital_preference": 0.72},
    {"segment_id": "SEG05", "segment_name": "Retirees", "spend_multiplier": 0.90, "digital_preference": 0.40},
    {"segment_id": "SEG06", "segment_name": "Small Business", "spend_multiplier": 1.45, "digital_preference": 0.62},
]

LOCATIONS = [
    ("New York", "NY", "Northeast"),
    ("Boston", "MA", "Northeast"),
    ("Philadelphia", "PA", "Northeast"),
    ("Atlanta", "GA", "South"),
    ("Miami", "FL", "South"),
    ("Dallas", "TX", "South"),
    ("Chicago", "IL", "Midwest"),
    ("Columbus", "OH", "Midwest"),
    ("Minneapolis", "MN", "Midwest"),
    ("Denver", "CO", "West"),
    ("Phoenix", "AZ", "West"),
    ("Los Angeles", "CA", "West"),
    ("Seattle", "WA", "West"),
]

CATEGORY_AMOUNT_RANGES = {
    "Groceries": (20, 220),
    "Dining": (12, 180),
    "Transportation": (5, 160),
    "Travel": (150, 2500),
    "Entertainment": (15, 300),
    "Utilities": (45, 420),
    "Housing": (650, 3200),
    "Healthcare": (35, 1200),
    "Retail": (15, 700),
    "Education": (50, 1600),
    "Cash Withdrawal": (20, 500),
    "Transfers": (50, 4000),
    "Subscription Services": (5, 90),
    "Fees and Charges": (3, 75),
}


def _random_date(start_date: date, end_date: date) -> date:
    days = (end_date - start_date).days
    return start_date + timedelta(days=random.randint(0, days))


def _weighted_choice(options: list[str], weights: list[float]) -> str:
    return random.choices(options, weights=weights, k=1)[0]


def _amount_for_category(category: str, segment_multiplier: float) -> float:
    low, high = CATEGORY_AMOUNT_RANGES[category]
    amount = random.triangular(low, high, low + (high - low) * 0.35)
    return round(amount * segment_multiplier, 2)


def _category_for_date(transaction_date: date) -> str:
    categories = [category for _, category in TRANSACTION_CATEGORIES]
    weights = [18, 12, 9, 4, 7, 8, 5, 5, 12, 3, 5, 5, 5, 2]
    if transaction_date.weekday() >= 5:
        weights[categories.index("Dining")] += 8
        weights[categories.index("Entertainment")] += 5
    if transaction_date.month in {6, 7, 8, 11, 12}:
        weights[categories.index("Travel")] += 5
        weights[categories.index("Retail")] += 6
    if transaction_date.day in {1, 2, 3, 28, 29, 30, 31}:
        weights[categories.index("Housing")] += 8
        weights[categories.index("Utilities")] += 5
    return _weighted_choice(categories, weights)


def _type_for_category(category: str) -> str:
    mapping = {
        "Cash Withdrawal": ["ATM Withdrawal"],
        "Transfers": ["Bank Transfer", "ACH Payment"],
        "Utilities": ["Bill Payment", "ACH Payment", "Automatic Payment"],
        "Housing": ["ACH Payment", "Bill Payment"],
        "Fees and Charges": ["Bank Fee"],
        "Subscription Services": ["Card Purchase", "ACH Payment"],
    }
    if category in mapping:
        return random.choice(mapping[category])
    return random.choice(["Card Purchase", "ACH Payment", "Bill Payment"])


def _channel_for_type(transaction_type: str, preferred_channel: str) -> str:
    if transaction_type == "ATM Withdrawal":
        return "ATM"
    if transaction_type == "Cash Deposit":
        return random.choice(["Branch", "ATM"])
    if transaction_type in {"Direct Deposit", "Bank Fee"}:
        return "Automatic Payment"
    if random.random() < 0.45:
        return preferred_channel
    return _weighted_choice(CHANNELS, [28, 22, 10, 8, 22, 10])


def _status_for_channel(channel: str, transaction_type: str) -> str:
    decline_boost = {"Mobile": 1.0, "Online": 1.2, "ATM": 1.4, "Branch": 0.7, "Point of Sale": 1.1, "Automatic Payment": 0.9}
    decline_weight = 5.5 * decline_boost.get(channel, 1.0)
    if transaction_type == "Bank Fee":
        decline_weight = 0.5
    return _weighted_choice(STATUSES, [88, decline_weight, 3.5, 2.5])


def _debit_credit_for_type(transaction_type: str, category: str) -> str:
    if transaction_type in {"Direct Deposit", "Refund", "Cash Deposit"}:
        return "Credit"
    if category == "Transfers" and random.random() < 0.28:
        return "Credit"
    return "Debit"


def _format_date_with_noise(value: date) -> str:
    if random.random() < 0.035:
        return value.strftime("%m/%d/%Y")
    if random.random() < 0.025:
        return value.strftime("%b %d, %Y")
    return value.isoformat()


def _build_segments() -> pd.DataFrame:
    return pd.DataFrame(SEGMENTS)


def _build_branches(count: int = 40) -> pd.DataFrame:
    rows = []
    for branch_number in range(1, count + 1):
        city, state, region = random.choice(LOCATIONS)
        rows.append(
            {
                "branch_id": f"BR{branch_number:03d}",
                "branch_name": f"{city} Branch {branch_number:02d}",
                "city": city,
                "state": state,
                "region": region,
                "branch_type": random.choice(["Retail", "Regional", "Campus", "Business"]),
            }
        )
    return pd.DataFrame(rows)


def _build_customers(count: int, start_date: date, end_date: date) -> pd.DataFrame:
    rows = []
    segment_names = [segment["segment_name"] for segment in SEGMENTS]
    for customer_number in range(1, count + 1):
        city, state, _ = random.choice(LOCATIONS)
        segment_name = _weighted_choice(segment_names, [12, 24, 26, 10, 18, 10])
        join_date = _random_date(start_date - timedelta(days=1800), end_date - timedelta(days=180))
        preferred_channel = _weighted_choice(CHANNELS, [34, 25, 9, 7, 18, 7])
        rows.append(
            {
                "customer_id": f"CUST{customer_number:06d}",
                "customer_display_name": f"Synthetic Customer {customer_number:06d}",
                "age_group": _weighted_choice(AGE_GROUPS, [10, 24, 22, 18, 15, 11]),
                "city": city,
                "state": state,
                "customer_segment": segment_name,
                "account_tenure_months": max(1, (end_date.year - join_date.year) * 12 + end_date.month - join_date.month),
                "join_date": join_date.isoformat(),
                "preferred_channel": preferred_channel,
                "risk_tier": _weighted_choice(RISK_TIERS, [66, 27, 7]),
                "income_band": _weighted_choice(INCOME_BANDS, [24, 38, 27, 11]),
            }
        )
    customers = pd.DataFrame(rows)
    duplicate_sample = customers.sample(n=max(3, count // 250), random_state=11).copy()
    duplicate_sample["customer_display_name"] = duplicate_sample["customer_display_name"].str.lower()
    return pd.concat([customers, duplicate_sample], ignore_index=True)


def _build_accounts(count: int, customers: pd.DataFrame, branches: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    unique_customers = customers.drop_duplicates("customer_id")
    rows = []
    for account_number in range(1, count + 1):
        customer = unique_customers.sample(n=1).iloc[0]
        branch = branches.sample(n=1).iloc[0]
        account_type = _weighted_choice(ACCOUNT_TYPES, [42, 30, 20, 8])
        customer_join = datetime.strptime(customer["join_date"], "%Y-%m-%d").date()
        open_date = _random_date(customer_join, min(end_date, customer_join + timedelta(days=1600)))
        status = _weighted_choice(["Active", "Closed", "Dormant"], [88, 8, 4])
        close_date = ""
        if status == "Closed":
            if open_date + timedelta(days=30) <= end_date:
                close_date = _random_date(open_date + timedelta(days=30), end_date).isoformat()
            else:
                status = "Active"
        credit_limit = round(random.choice([1000, 2500, 5000, 7500, 10000, 15000]) * random.uniform(0.9, 1.25), 2) if account_type == "Credit Card" else ""
        balance_low = -800 if account_type == "Credit Card" else 50
        balance_high = 20000 if account_type != "Credit Card" else 6500
        rows.append(
            {
                "account_id": f"ACC{account_number:06d}",
                "customer_id": customer["customer_id"],
                "account_type": account_type,
                "open_date": open_date.isoformat(),
                "account_status": status,
                "close_date": close_date,
                "current_balance": round(random.uniform(balance_low, balance_high), 2),
                "credit_limit": credit_limit,
                "branch_id": branch["branch_id"],
                "currency": "USD",
                "product_tier": _weighted_choice(PRODUCT_TIERS, [45, 38, 17]),
            }
        )
    accounts = pd.DataFrame(rows)
    issue_rows = accounts.sample(n=max(3, count // 350), random_state=12).copy()
    issue_rows["account_id"] = [f"BADACC{i:04d}" for i in range(len(issue_rows))]
    issue_rows["customer_id"] = "CUST999999"
    return pd.concat([accounts, issue_rows], ignore_index=True)


def _build_merchants(count: int) -> pd.DataFrame:
    rows = []
    merchant_categories = [category for _, category in TRANSACTION_CATEGORIES if category not in {"Cash Withdrawal", "Transfers", "Fees and Charges"}]
    for merchant_number in range(1, count + 1):
        category = random.choice(merchant_categories)
        city, state, region = random.choice(LOCATIONS)
        rows.append(
            {
                "merchant_id": f"MER{merchant_number:04d}",
                "merchant_name": f"Synthetic {category} Merchant {merchant_number:03d}",
                "merchant_category": category,
                "city": city,
                "state": state,
                "region": region,
                "is_online_only": random.random() < 0.18,
            }
        )
    rows.append(
        {
            "merchant_id": "MERBANK",
            "merchant_name": "Synthetic Bank Internal",
            "merchant_category": "Banking",
            "city": "New York",
            "state": "NY",
            "region": "Northeast",
            "is_online_only": False,
        }
    )
    return pd.DataFrame(rows)


def _build_devices(customers: pd.DataFrame, count: int = 2100) -> pd.DataFrame:
    unique_customers = customers.drop_duplicates("customer_id")
    rows = []
    for device_number in range(1, count + 1):
        customer = unique_customers.sample(n=1).iloc[0]
        rows.append(
            {
                "device_id": f"DEV{device_number:05d}",
                "customer_id": customer["customer_id"],
                "device_type": _weighted_choice(["Mobile App", "Web Browser", "ATM Terminal", "Branch Terminal"], [50, 28, 12, 10]),
                "operating_system": random.choice(["iOS", "Android", "Windows", "macOS", "ATM OS", "Branch System"]),
                "trusted_device": random.random() < 0.86,
            }
        )
    return pd.DataFrame(rows)


def _merchant_for_category(category: str, merchants: pd.DataFrame) -> pd.Series:
    if category in {"Cash Withdrawal", "Transfers", "Fees and Charges"}:
        return merchants[merchants["merchant_id"] == "MERBANK"].iloc[0]
    matching = merchants[merchants["merchant_category"] == category]
    if matching.empty:
        return merchants.sample(n=1).iloc[0]
    return matching.sample(n=1).iloc[0]


def _device_for_customer(customer_id: str, devices: pd.DataFrame, channel: str) -> str:
    if channel in {"Branch", "Automatic Payment"}:
        return ""
    customer_devices = devices[devices["customer_id"] == customer_id]
    if customer_devices.empty:
        return ""
    return customer_devices.sample(n=1).iloc[0]["device_id"]


def _build_transactions(
    count: int,
    customers: pd.DataFrame,
    accounts: pd.DataFrame,
    merchants: pd.DataFrame,
    branches: pd.DataFrame,
    devices: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    unique_customers = customers.drop_duplicates("customer_id")
    valid_accounts = accounts[accounts["account_id"].str.startswith("ACC")].copy()
    valid_accounts["open_date_parsed"] = pd.to_datetime(valid_accounts["open_date"]).dt.date
    valid_accounts["close_date_parsed"] = pd.to_datetime(valid_accounts["close_date"], errors="coerce").dt.date
    valid_accounts = valid_accounts[
        (valid_accounts["open_date_parsed"] <= end_date)
        & (valid_accounts["close_date_parsed"].isna() | (valid_accounts["close_date_parsed"] >= start_date))
    ].copy()
    customer_segments = {segment["segment_name"]: segment for segment in SEGMENTS}
    accounts_by_customer = {customer_id: frame for customer_id, frame in valid_accounts.groupby("customer_id")}
    customer_lookup = unique_customers.set_index("customer_id").to_dict("index")
    balances = {row["account_id"]: float(row["current_balance"]) for _, row in valid_accounts.iterrows()}
    rows = []

    customer_ids = list(accounts_by_customer.keys())
    for transaction_number in range(1, count + 1):
        customer_id = random.choice(customer_ids)
        customer = customer_lookup[customer_id]
        customer_accounts = accounts_by_customer[customer_id]
        account = customer_accounts.sample(n=1).iloc[0]
        account_start_date = max(start_date, account["open_date_parsed"])
        account_end_date = end_date
        if pd.notna(account["close_date_parsed"]):
            account_end_date = min(end_date, account["close_date_parsed"])
        transaction_date = _random_date(account_start_date, account_end_date)

        if random.random() < 0.08:
            transaction_date = transaction_date.replace(day=random.choice([1, 3, 15, 28 if transaction_date.month != 2 else 26]))
            if transaction_date < account_start_date or transaction_date > account_end_date:
                transaction_date = _random_date(account_start_date, account_end_date)

        category = _category_for_date(transaction_date)
        transaction_type = _type_for_category(category)
        if random.random() < 0.035 and transaction_date.day in {1, 15}:
            transaction_type = "Direct Deposit"
            category = "Transfers"

        channel = _channel_for_type(transaction_type, customer["preferred_channel"])
        status = _status_for_channel(channel, transaction_type)
        debit_credit = _debit_credit_for_type(transaction_type, category)
        segment_multiplier = customer_segments[customer["customer_segment"]]["spend_multiplier"]

        if transaction_type == "Direct Deposit":
            amount = round(random.uniform(900, 5200) * segment_multiplier, 2)
        elif transaction_type == "Cash Deposit":
            amount = round(random.uniform(40, 1600), 2)
        else:
            amount = _amount_for_category(category, segment_multiplier)

        if random.random() < 0.006:
            amount = round(amount * random.uniform(5, 12), 2)

        hour = random.choices(range(24), weights=[1, 1, 1, 1, 1, 2, 5, 7, 8, 8, 7, 8, 9, 8, 7, 8, 9, 10, 11, 9, 7, 5, 3, 2], k=1)[0]
        minute = random.randint(0, 59)
        timestamp = datetime.combine(transaction_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute, seconds=random.randint(0, 59))

        merchant = _merchant_for_category(category, merchants)
        is_international = random.random() < (0.028 if customer["risk_tier"] != "High" else 0.045)
        if is_international:
            merchant_city, merchant_state = "International", "INT"
        elif channel in {"Branch", "ATM"} and random.random() < 0.75:
            branch = branches[branches["branch_id"] == account["branch_id"]].iloc[0]
            merchant_city, merchant_state = branch["city"], branch["state"]
        else:
            merchant_city, merchant_state = merchant["city"], merchant["state"]

        is_recurring = category in {"Utilities", "Housing", "Subscription Services"} and random.random() < 0.52
        signed_amount = amount if debit_credit == "Credit" else -amount
        if status == "Approved":
            balances[account["account_id"]] = round(balances.get(account["account_id"], 0) + signed_amount, 2)
        balance_after = balances.get(account["account_id"], 0)

        rows.append(
            {
                "transaction_id": f"TXN{transaction_number:08d}",
                "account_id": account["account_id"],
                "customer_id": customer_id,
                "merchant_id": merchant["merchant_id"],
                "transaction_date": _format_date_with_noise(transaction_date),
                "transaction_timestamp": timestamp.isoformat(sep=" "),
                "transaction_amount": amount,
                "transaction_category": category,
                "transaction_type": transaction_type,
                "transaction_status": status,
                "transaction_channel": channel,
                "device_id": _device_for_customer(customer_id, devices, channel),
                "branch_id": account["branch_id"] if channel in {"Branch", "ATM"} else "",
                "city": merchant_city,
                "state": merchant_state,
                "currency": "USD",
                "debit_credit_indicator": debit_credit,
                "description": f"{transaction_type} - {category}",
                "is_international": is_international,
                "is_recurring": is_recurring,
                "balance_after_transaction": balance_after,
                "synthetic_anomaly_flag": amount >= 5000 or is_international and amount > 1500 or balance_after < -500,
            }
        )

    transactions = pd.DataFrame(rows)
    return _inject_transaction_quality_issues(transactions, accounts, start_date)


def _inject_transaction_quality_issues(transactions: pd.DataFrame, accounts: pd.DataFrame, start_date: date) -> pd.DataFrame:
    dirty = transactions.copy()
    dirty["transaction_amount"] = dirty["transaction_amount"].astype(object)
    random_state = 22

    duplicate_indexes = dirty.sample(n=90, random_state=random_state).index
    dirty.loc[duplicate_indexes, "transaction_id"] = dirty.loc[duplicate_indexes[0], "transaction_id"]

    dirty.loc[dirty.sample(n=70, random_state=23).index, "customer_id"] = ""
    dirty.loc[dirty.sample(n=60, random_state=24).index, "account_id"] = "ACC999999"
    dirty.loc[dirty.sample(n=55, random_state=25).index, "merchant_id"] = "MER9999"
    dirty.loc[dirty.sample(n=45, random_state=26).index, "transaction_amount"] = -dirty["transaction_amount"].astype(float).abs()
    dirty.loc[dirty.sample(n=30, random_state=27).index, "transaction_amount"] = 0
    dirty.loc[dirty.sample(n=50, random_state=28).index, "transaction_category"] = " dinning "
    dirty.loc[dirty.sample(n=35, random_state=29).index, "transaction_status"] = " apprved "
    dirty.loc[dirty.sample(n=35, random_state=30).index, "transaction_channel"] = "POS"
    dirty.loc[dirty.sample(n=25, random_state=31).index, "transaction_channel"] = ""

    old_date_indexes = dirty.sample(n=40, random_state=32).index
    dirty.loc[old_date_indexes, "transaction_date"] = (start_date - timedelta(days=365)).isoformat()

    currency_indexes = dirty.sample(n=120, random_state=33).index
    dirty.loc[currency_indexes, "transaction_amount"] = dirty.loc[currency_indexes, "transaction_amount"].map(lambda value: f"${float(value):,.2f}")

    dirty.loc[dirty.sample(n=30, random_state=34).index, "currency"] = "usd"
    dirty.loc[dirty.sample(n=20, random_state=35).index, "transaction_status"] = "Unknown"
    dirty.loc[dirty.sample(n=22, random_state=36).index, "branch_id"] = "BR999"
    dirty.loc[dirty.sample(n=22, random_state=37).index, "device_id"] = "DEV99999"

    high_value_indexes = dirty.sample(n=70, random_state=38).index
    dirty.loc[high_value_indexes, "transaction_amount"] = dirty.loc[high_value_indexes, "transaction_amount"].map(
        lambda value: round(abs(float(str(value).replace("$", "").replace(",", ""))) + random.uniform(8000, 25000), 2)
    )

    repeated = dirty.sample(n=35, random_state=39).copy()
    repeated["transaction_id"] = [f"TXNREPEAT{i:05d}" for i in range(len(repeated))]
    repeated["transaction_timestamp"] = pd.to_datetime(repeated["transaction_timestamp"], errors="coerce") + pd.to_timedelta(3, unit="minutes")
    repeated["transaction_timestamp"] = repeated["transaction_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    closed_accounts = accounts[accounts["account_status"] == "Closed"]
    if not closed_accounts.empty:
        closed_sample = closed_accounts.sample(n=min(25, len(closed_accounts)), random_state=40)
        target_indexes = dirty.sample(n=len(closed_sample), random_state=41).index
        for index, (_, account) in zip(target_indexes, closed_sample.iterrows()):
            close_date = datetime.strptime(account["close_date"], "%Y-%m-%d").date()
            dirty.loc[index, "account_id"] = account["account_id"]
            dirty.loc[index, "customer_id"] = account["customer_id"]
            dirty.loc[index, "transaction_date"] = min(close_date + timedelta(days=20), close_date + timedelta(days=60)).isoformat()

    return pd.concat([dirty, repeated], ignore_index=True)


def generate_synthetic_data(config: dict) -> dict[str, Path]:
    logging.info("Starting synthetic data generation")
    random.seed(config["random_seed"])
    np.random.seed(config["random_seed"])
    raw_dir = project_path(config["paths"]["raw_data_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    start_date = datetime.strptime(config["date_range"]["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(config["date_range"]["end_date"], "%Y-%m-%d").date()
    counts = config["record_counts"]

    customer_segments = _build_segments()
    branches = _build_branches()
    customers = _build_customers(counts["customers"], start_date, end_date)
    accounts = _build_accounts(counts["accounts"], customers, branches, start_date, end_date)
    merchants = _build_merchants(counts["merchants"])
    devices = _build_devices(customers)
    categories = pd.DataFrame(
        [
            {"category_id": category_id, "transaction_category": category, "category_group": "Banking" if category in {"Transfers", "Fees and Charges"} else "Spending"}
            for category_id, category in TRANSACTION_CATEGORIES
        ]
    )
    transactions = _build_transactions(counts["transactions"], customers, accounts, merchants, branches, devices, start_date, end_date)

    outputs = {
        "customers": raw_dir / "customers.csv",
        "accounts": raw_dir / "accounts.csv",
        "transactions": raw_dir / "transactions.csv",
        "merchants": raw_dir / "merchants.csv",
        "transaction_categories": raw_dir / "transaction_categories.csv",
        "branches": raw_dir / "branches.csv",
        "devices": raw_dir / "devices.csv",
        "customer_segments": raw_dir / "customer_segments.csv",
    }

    save_dataframe(customers, outputs["customers"])
    save_dataframe(accounts, outputs["accounts"])
    save_dataframe(transactions, outputs["transactions"])
    save_dataframe(merchants, outputs["merchants"])
    save_dataframe(categories, outputs["transaction_categories"])
    save_dataframe(branches, outputs["branches"])
    save_dataframe(devices, outputs["devices"])
    save_dataframe(customer_segments, outputs["customer_segments"])

    logging.info("Generated %s raw transaction rows", len(transactions))
    return outputs


if __name__ == "__main__":
    from src.utils import ensure_directories, load_config, setup_logging

    pipeline_config = load_config()
    ensure_directories(pipeline_config)
    setup_logging(pipeline_config)
    generate_synthetic_data(pipeline_config)
