from __future__ import annotations

import logging

import pandas as pd


STATE_REGION = {
    "NY": "Northeast",
    "MA": "Northeast",
    "PA": "Northeast",
    "GA": "South",
    "FL": "South",
    "TX": "South",
    "IL": "Midwest",
    "OH": "Midwest",
    "MN": "Midwest",
    "CO": "West",
    "AZ": "West",
    "CA": "West",
    "WA": "West",
    "INT": "International",
}


def flag_high_value_transactions(transactions: pd.DataFrame, fixed_threshold: float) -> pd.Series:
    return transactions["transaction_amount"] >= fixed_threshold


def flag_spending_deviation(transactions: pd.DataFrame) -> pd.Series:
    customer_stats = transactions.groupby("customer_id")["transaction_amount"].agg(["mean", "std", "median"]).reset_index()
    customer_stats["std"] = customer_stats["std"].fillna(0)
    scored = transactions.merge(customer_stats, on="customer_id", how="left")
    customer_threshold = scored[["mean", "std", "median"]].apply(
        lambda row: max(row["mean"] + 3 * row["std"], row["median"] * 4, 500),
        axis=1,
    )
    return scored["transaction_amount"] > customer_threshold


def flag_rapid_repeated_transactions(transactions: pd.DataFrame, threshold_minutes: int) -> pd.Series:
    sortable = transactions[["transaction_id", "customer_id", "merchant_id", "transaction_amount", "transaction_timestamp"]].copy()
    sortable["transaction_timestamp"] = pd.to_datetime(sortable["transaction_timestamp"], errors="coerce")
    sortable["rounded_amount"] = sortable["transaction_amount"].round(0)
    sortable = sortable.sort_values(["customer_id", "merchant_id", "rounded_amount", "transaction_timestamp"])
    previous_timestamp = sortable.groupby(["customer_id", "merchant_id", "rounded_amount"])["transaction_timestamp"].shift(1)
    minute_difference = (sortable["transaction_timestamp"] - previous_timestamp).dt.total_seconds() / 60
    sortable["rapid_repeat_transaction"] = minute_difference.between(0, threshold_minutes, inclusive="both")
    return transactions["transaction_id"].map(sortable.set_index("transaction_id")["rapid_repeat_transaction"]).fillna(False).astype(bool)


def flag_geographic_inconsistency(transactions: pd.DataFrame) -> pd.Series:
    sortable = transactions[["transaction_id", "customer_id", "transaction_timestamp", "state"]].copy()
    sortable["transaction_timestamp"] = pd.to_datetime(sortable["transaction_timestamp"], errors="coerce")
    sortable["region"] = sortable["state"].map(STATE_REGION).fillna("Unknown")
    sortable = sortable.sort_values(["customer_id", "transaction_timestamp"])
    sortable["previous_region"] = sortable.groupby("customer_id")["region"].shift(1)
    sortable["previous_timestamp"] = sortable.groupby("customer_id")["transaction_timestamp"].shift(1)
    hours_between = (sortable["transaction_timestamp"] - sortable["previous_timestamp"]).dt.total_seconds() / 3600
    sortable["geographic_inconsistency"] = (
        sortable["previous_region"].notna()
        & (sortable["region"] != sortable["previous_region"])
        & (sortable["region"] != "Unknown")
        & (sortable["previous_region"] != "Unknown")
        & (hours_between <= 2)
    )
    return transactions["transaction_id"].map(sortable.set_index("transaction_id")["geographic_inconsistency"]).fillna(False).astype(bool)


def flag_unusual_international_activity(transactions: pd.DataFrame) -> pd.Series:
    sortable = transactions[["transaction_id", "customer_id", "transaction_timestamp", "is_international"]].copy()
    sortable["transaction_timestamp"] = pd.to_datetime(sortable["transaction_timestamp"], errors="coerce")
    sortable = sortable.sort_values(["customer_id", "transaction_timestamp"])
    prior_international_count = sortable.groupby("customer_id")["is_international"].cumsum() - sortable["is_international"].astype(int)
    sortable["unusual_international_activity"] = sortable["is_international"] & (prior_international_count <= 1)
    return transactions["transaction_id"].map(sortable.set_index("transaction_id")["unusual_international_activity"]).fillna(False).astype(bool)


def flag_unusual_transaction_time(transactions: pd.DataFrame, start_hour: int, end_hour: int) -> pd.Series:
    timestamps = pd.to_datetime(transactions["transaction_timestamp"], errors="coerce")
    hours = timestamps.dt.hour
    return hours.between(start_hour, end_hour, inclusive="both")


def flag_repeated_declines(transactions: pd.DataFrame) -> pd.Series:
    declines = transactions[transactions["transaction_status"] == "Declined"].copy()
    if declines.empty:
        return pd.Series(False, index=transactions.index)
    declines["transaction_day"] = pd.to_datetime(declines["transaction_date"], errors="coerce").dt.date
    decline_counts = declines.groupby(["customer_id", "transaction_day"])["transaction_id"].transform("count")
    declines["repeated_declines"] = decline_counts >= 3
    mapped = transactions["transaction_id"].map(declines.set_index("transaction_id")["repeated_declines"])
    return mapped.where(mapped.notna(), False).astype(bool)


def flag_balance_issue(transactions: pd.DataFrame, negative_balance_warning: float) -> pd.Series:
    return (transactions["balance_after_transaction"] <= negative_balance_warning) & (transactions["transaction_amount"] >= 1000)


def calculate_anomaly_score(flagged: pd.DataFrame, weights: dict) -> pd.Series:
    score = pd.Series(0, index=flagged.index)
    for rule_name, weight in weights.items():
        if rule_name in flagged.columns:
            score = score + flagged[rule_name].fillna(False).astype(bool).astype(int) * int(weight)
    return score


def classify_review_priority(score: int) -> str:
    if score >= 6:
        return "High"
    if score >= 3:
        return "Medium"
    if score > 0:
        return "Low"
    return "None"


def run_anomaly_rules(transactions: pd.DataFrame, config: dict) -> pd.DataFrame:
    logging.info("Starting rule-based anomaly analysis")
    output = transactions.copy().reset_index(drop=True)
    thresholds = config["thresholds"]
    weights = config["anomaly_scoring_weights"]

    output["high_value_transaction"] = flag_high_value_transactions(output, thresholds["high_value_transaction"])
    output["spending_deviation"] = flag_spending_deviation(output)
    output["rapid_repeat_transaction"] = flag_rapid_repeated_transactions(output, thresholds["rapid_transaction_minutes"])
    output["geographic_inconsistency"] = flag_geographic_inconsistency(output)
    output["unusual_international_activity"] = flag_unusual_international_activity(output)
    output["unusual_transaction_time"] = flag_unusual_transaction_time(output, thresholds["unusual_hour_start"], thresholds["unusual_hour_end"])
    output["repeated_declines"] = flag_repeated_declines(output)
    output["balance_issue"] = flag_balance_issue(output, thresholds["negative_balance_warning"])
    output["anomaly_score"] = calculate_anomaly_score(output, weights)
    output["review_priority"] = output["anomaly_score"].map(classify_review_priority)

    rule_columns = list(weights.keys())
    output["triggered_rules"] = output[rule_columns].apply(lambda row: ", ".join([column for column, is_flagged in row.items() if is_flagged]), axis=1)
    flagged = output[output["anomaly_score"] > 0].copy()
    flagged.insert(0, "anomaly_id", [f"ANOM{i:07d}" for i in range(1, len(flagged) + 1)])
    logging.info("Flagged %s transactions for potential review", len(flagged))
    return flagged[
        [
            "anomaly_id",
            "transaction_id",
            "customer_id",
            "account_id",
            "transaction_date",
            "transaction_amount",
            "transaction_category",
            "transaction_channel",
            *rule_columns,
            "triggered_rules",
            "anomaly_score",
            "review_priority",
            "synthetic_anomaly_flag",
        ]
    ]
