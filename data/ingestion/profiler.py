"""Tabular profiling for CSV, TSV, and JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from data.privacy.identifiers import scan_table


SUPPORTED = {".csv", ".tsv", ".json", ".txt"}


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED and suffix != ".xlsx":
        raise ValueError(f"Unsupported table type: {suffix}")
    if suffix == ".csv" or suffix == ".txt":
        return pd.read_csv(path)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t")
    if suffix == ".json":
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            payload = [payload]
        return pd.DataFrame(payload)
    if suffix == ".xlsx":
        return pd.read_excel(path)
    raise ValueError(f"Unsupported table type: {suffix}")


def profile_frame(frame: pd.DataFrame) -> dict:
    rows = int(len(frame))
    columns = [str(c) for c in frame.columns]
    numerical, categorical, datetime_cols = [], [], []
    missing = {}
    for column in frame.columns:
        series = frame[column]
        missing[str(column)] = float(series.isna().mean()) if rows else 0.0
        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(str(column))
        elif pd.api.types.is_numeric_dtype(series):
            numerical.append(str(column))
        else:
            converted = pd.to_datetime(series, errors="coerce")
            if series.notna().sum() and converted.notna().mean() > 0.8 and not pd.api.types.is_numeric_dtype(series):
                datetime_cols.append(str(column))
            else:
                categorical.append(str(column))
    duplicate_rows = int(frame.duplicated().sum()) if rows else 0
    missing_fraction = float(frame.isna().to_numpy().mean()) if frame.size else 0.0
    sample = frame.head(20).where(pd.notna(frame.head(20)), None)
    records = json.loads(sample.to_json(orient="records", date_format="iso"))
    sensitive = scan_table(columns, records)
    stats = {}
    for column in numerical:
        series = pd.to_numeric(frame[column], errors="coerce")
        stats[column] = {
            "mean": _finite(series.mean()),
            "std": _finite(series.std(ddof=1)) if series.count() > 1 else 0.0,
            "min": _finite(series.min()),
            "max": _finite(series.max()),
            "median": _finite(series.median()),
        }
    return {
        "rows": rows,
        "columns": len(columns),
        "column_names": columns,
        "numerical": numerical,
        "categorical": categorical,
        "datetime": datetime_cols,
        "missing_fraction": missing_fraction,
        "missing_by_column": missing,
        "duplicate_rows": duplicate_rows,
        "statistics": stats,
        "preview": records,
        "sensitive": sensitive,
    }


def _finite(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number
