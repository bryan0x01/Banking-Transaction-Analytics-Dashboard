from __future__ import annotations

import logging

import pandas as pd

from src.utils import project_path, standardize_column_names


RAW_FILES = {
    "customers": "customers.csv",
    "accounts": "accounts.csv",
    "transactions": "transactions.csv",
    "merchants": "merchants.csv",
    "transaction_categories": "transaction_categories.csv",
    "branches": "branches.csv",
    "devices": "devices.csv",
    "customer_segments": "customer_segments.csv",
}


def ingest_source_files(config: dict) -> dict[str, pd.DataFrame]:
    logging.info("Starting source CSV ingestion")
    raw_dir = project_path(config["paths"]["raw_data_dir"])
    datasets: dict[str, pd.DataFrame] = {}

    for dataset_name, file_name in RAW_FILES.items():
        file_path = raw_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Missing required source file: {file_path}")
        dataframe = pd.read_csv(file_path, dtype=str, keep_default_na=False)
        datasets[dataset_name] = standardize_column_names(dataframe)
        logging.info("Ingested %s rows from %s", len(dataframe), file_path)

    return datasets
