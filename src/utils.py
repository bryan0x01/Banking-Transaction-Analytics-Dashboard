from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_config(config_path: str | Path = "config/config.yaml") -> dict[str, Any]:
    with project_path(config_path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def ensure_directories(config: dict[str, Any]) -> None:
    paths = config["paths"]
    for key in ["raw_data_dir", "processed_data_dir", "output_dir", "powerbi_export_dir"]:
        project_path(paths[key]).mkdir(parents=True, exist_ok=True)
    project_path(paths["database_path"]).parent.mkdir(parents=True, exist_ok=True)
    project_path(paths["excel_output_path"]).parent.mkdir(parents=True, exist_ok=True)


def setup_logging(config: dict[str, Any]) -> None:
    log_path = project_path(config["paths"]["log_path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def standardize_column_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    renamed_columns = []
    for column in dataframe.columns:
        cleaned = str(column).strip().lower()
        cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        renamed_columns.append(cleaned)
    output = dataframe.copy()
    output.columns = renamed_columns
    return output


def clean_text(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text if text else None


def title_clean(value: Any) -> str | None:
    text = clean_text(value)
    return text.title() if text is not None else None


def parse_currency(value: Any) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("$", "").replace(",", "").replace("USD", "").strip()
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    try:
        return float(text)
    except ValueError:
        return None


def parse_date_series(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", format="mixed")
    return parsed.dt.date


def parse_timestamp_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", format="mixed")


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "t", "yes", "y", "1"}


def save_dataframe(dataframe: pd.DataFrame, path: str | Path) -> None:
    full_path = project_path(path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(full_path, index=False)


def read_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(project_path(path), dtype=str, keep_default_na=False)


def month_start(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.to_period("M").dt.to_timestamp().dt.date


def safe_divide(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator
