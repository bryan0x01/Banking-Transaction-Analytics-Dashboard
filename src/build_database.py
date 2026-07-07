from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.utils import project_path


SQL_SCRIPT_ORDER = [
    "01_create_staging_tables.sql",
    "02_create_dimensions.sql",
    "03_create_fact_tables.sql",
    "04_load_dimensions.sql",
    "05_load_facts.sql",
    "06_create_reporting_views.sql",
    "07_kpi_queries.sql",
    "08_validation_queries.sql",
]


def _prepare_for_sqlite(dataframe: pd.DataFrame) -> pd.DataFrame:
    output = dataframe.copy()
    for column in output.columns:
        if pd.api.types.is_datetime64_any_dtype(output[column]):
            output[column] = output[column].astype(str)
        elif output[column].dtype == "bool":
            output[column] = output[column].astype(int)
        elif output[column].dtype == "object":
            output[column] = output[column].map(lambda value: value.isoformat() if hasattr(value, "isoformat") else value)
    return output


def _write_table(connection: sqlite3.Connection, table_name: str, dataframe: pd.DataFrame) -> None:
    _prepare_for_sqlite(dataframe).to_sql(table_name, connection, if_exists="replace", index=False)
    logging.info("Loaded %s rows into %s", len(dataframe), table_name)


def _execute_sql_script(connection: sqlite3.Connection, script_path: Path) -> None:
    sql = script_path.read_text(encoding="utf-8")
    connection.executescript(sql)
    logging.info("Executed SQL script %s", script_path.name)


def build_sqlite_database(
    config: dict,
    cleaned: dict[str, pd.DataFrame],
    model_tables: dict[str, pd.DataFrame],
    anomaly_flags: pd.DataFrame,
    reconciliation_report: pd.DataFrame,
) -> Path:
    logging.info("Starting SQLite database build")
    database_path = project_path(config["paths"]["database_path"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF;")

        staging_tables = {
            "stg_customers": cleaned["customers"],
            "stg_accounts": cleaned["accounts"],
            "stg_transactions": cleaned["transactions"],
            "stg_merchants": cleaned["merchants"],
            "stg_transaction_categories": cleaned["transaction_categories"],
            "stg_branches": cleaned["branches"],
            "stg_devices": cleaned["devices"],
            "stg_customer_segments": cleaned["customer_segments"],
        }
        for table_name, dataframe in staging_tables.items():
            _write_table(connection, table_name, dataframe)

        for table_name, dataframe in model_tables.items():
            if table_name == "fact_anomaly_flag":
                continue
            _write_table(connection, table_name, dataframe)

        _write_table(connection, "fact_anomaly_flag", anomaly_flags)
        _write_table(connection, "reconciliation_report", reconciliation_report)

        for script_name in SQL_SCRIPT_ORDER:
            _execute_sql_script(connection, project_path("sql") / script_name)

        connection.commit()

    logging.info("SQLite database created at %s", database_path)
    return database_path


def read_database_table_counts(database_path: str | Path, table_names: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    with sqlite3.connect(project_path(database_path)) as connection:
        for table_name in table_names:
            counts[table_name] = int(connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
    return counts


def read_view_sample_counts(database_path: str | Path, view_names: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    with sqlite3.connect(project_path(database_path)) as connection:
        for view_name in view_names:
            counts[view_name] = int(connection.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0])
    return counts
