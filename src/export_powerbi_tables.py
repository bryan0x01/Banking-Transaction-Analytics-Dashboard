from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from src.utils import project_path


POWERBI_TABLES = [
    "dim_customer",
    "dim_account",
    "dim_merchant",
    "dim_transaction_category",
    "dim_date",
    "dim_channel",
    "dim_location",
    "dim_device",
    "dim_branch",
    "dim_transaction_status",
    "fact_transaction",
    "fact_account_daily_balance",
    "fact_customer_monthly_summary",
    "fact_anomaly_flag",
    "fact_data_quality_issue",
    "reconciliation_report",
    "kpi_snapshot",
]

POWERBI_VIEWS = [
    "vw_transaction_overview",
    "vw_daily_transaction_trends",
    "vw_monthly_transaction_trends",
    "vw_category_performance",
    "vw_customer_spending_summary",
    "vw_merchant_performance",
    "vw_channel_performance",
    "vw_transaction_status_summary",
    "vw_account_activity",
    "vw_customer_segment_analysis",
    "vw_geographic_transaction_summary",
    "vw_anomaly_review",
    "vw_declined_transaction_analysis",
    "vw_data_quality_summary",
    "vw_executive_kpis",
]


def export_powerbi_tables(config: dict) -> list[Path]:
    logging.info("Starting Power BI CSV exports")
    database_path = project_path(config["paths"]["database_path"])
    export_dir = project_path(config["paths"]["powerbi_export_dir"])
    export_dir.mkdir(parents=True, exist_ok=True)
    exported_files: list[Path] = []

    with sqlite3.connect(database_path) as connection:
        for object_name in [*POWERBI_TABLES, *POWERBI_VIEWS]:
            dataframe = pd.read_sql_query(f"SELECT * FROM {object_name}", connection)
            output_path = export_dir / f"{object_name}.csv"
            dataframe.to_csv(output_path, index=False)
            exported_files.append(output_path)
            logging.info("Exported %s rows to %s", len(dataframe), output_path)

    return exported_files
