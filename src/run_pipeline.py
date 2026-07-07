from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.anomaly_rules import run_anomaly_rules
from src.build_database import build_sqlite_database, read_database_table_counts, read_view_sample_counts
from src.clean_data import clean_datasets
from src.export_powerbi_tables import POWERBI_TABLES, POWERBI_VIEWS, export_powerbi_tables
from src.generate_excel_report import generate_excel_report
from src.generate_synthetic_data import generate_synthetic_data
from src.ingest_data import ingest_source_files
from src.reconcile_data import build_reconciliation_report
from src.run_analysis import run_analysis
from src.transform_data import build_model_tables
from src.utils import ensure_directories, load_config, project_path, save_dataframe, setup_logging
from src.validate_data import validate_datasets


def _attach_transaction_keys(anomaly_flags: pd.DataFrame, fact_transaction: pd.DataFrame) -> pd.DataFrame:
    if anomaly_flags.empty:
        output = anomaly_flags.copy()
        output.insert(1, "transaction_key", pd.Series(dtype="int64"))
        return output
    keys = fact_transaction[["transaction_key", "transaction_id"]]
    output = anomaly_flags.merge(keys, on="transaction_id", how="left")
    column_order = ["anomaly_id", "transaction_key", *[column for column in output.columns if column not in {"anomaly_id", "transaction_key"}]]
    return output[column_order]


def _write_pipeline_summary(
    config: dict,
    raw_datasets: dict[str, pd.DataFrame],
    validated: dict[str, pd.DataFrame],
    model_tables: dict[str, pd.DataFrame],
    anomaly_flags: pd.DataFrame,
    exported_files: list[Path],
    excel_path: str,
    database_counts: dict[str, int],
    view_counts: dict[str, int],
) -> pd.DataFrame:
    categories = model_tables["dim_transaction_category"]
    category_count = int(categories[categories["transaction_category"] != "Unknown"]["transaction_category"].nunique())
    summary = pd.DataFrame(
        [
            {"metric": "raw_transaction_rows", "value": len(raw_datasets["transactions"])},
            {"metric": "valid_analyzed_transactions", "value": len(validated["valid_transactions"])},
            {"metric": "rejected_transaction_rows", "value": len(validated["rejected_transactions"])},
            {"metric": "synthetic_customers", "value": raw_datasets["customers"]["customer_id"].nunique()},
            {"metric": "synthetic_accounts", "value": raw_datasets["accounts"]["account_id"].nunique()},
            {"metric": "transaction_categories", "value": category_count},
            {"metric": "potential_anomaly_flags", "value": len(anomaly_flags)},
            {"metric": "data_quality_issues", "value": len(validated["data_quality_issues"])},
            {"metric": "powerbi_export_files", "value": len(exported_files)},
            {"metric": "excel_workbook", "value": excel_path},
            {"metric": "database_path", "value": config["paths"]["database_path"]},
            {"metric": "database_table_count_checks", "value": len(database_counts)},
            {"metric": "database_view_count_checks", "value": len(view_counts)},
        ]
    )
    save_dataframe(summary, f"{config['paths']['output_dir']}/pipeline_execution_summary.csv")
    return summary


def run_pipeline(config_path: str = "config/config.yaml") -> pd.DataFrame:
    config = load_config(config_path)
    ensure_directories(config)
    setup_logging(config)
    logging.info("Pipeline started")

    generate_synthetic_data(config)
    raw_datasets = ingest_source_files(config)
    cleaned = clean_datasets(raw_datasets, config)
    validated = validate_datasets(cleaned, config)
    model_tables = build_model_tables(validated, config)

    anomaly_flags = run_anomaly_rules(validated["valid_transactions"], config)
    anomaly_flags = _attach_transaction_keys(anomaly_flags, model_tables["fact_transaction"])
    model_tables["fact_anomaly_flag"] = anomaly_flags
    save_dataframe(anomaly_flags, f"{config['paths']['processed_data_dir']}/fact_anomaly_flag.csv")

    reconciliation_report = build_reconciliation_report(raw_datasets, validated, model_tables, config)
    kpi_summary = run_analysis(model_tables, anomaly_flags, reconciliation_report, config)
    database_path = build_sqlite_database(config, cleaned, model_tables, anomaly_flags, reconciliation_report)
    exported_files = export_powerbi_tables(config)
    excel_path = generate_excel_report(model_tables, anomaly_flags, reconciliation_report, kpi_summary, config)

    database_counts = read_database_table_counts(database_path, POWERBI_TABLES)
    view_counts = read_view_sample_counts(database_path, POWERBI_VIEWS)
    summary = _write_pipeline_summary(
        config,
        raw_datasets,
        validated,
        model_tables,
        anomaly_flags,
        exported_files,
        excel_path,
        database_counts,
        view_counts,
    )

    logging.info("Pipeline completed successfully")
    print(summary.to_string(index=False))
    return summary


if __name__ == "__main__":
    run_pipeline()
