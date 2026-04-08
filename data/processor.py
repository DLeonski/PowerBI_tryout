import pandas as pd
import numpy as np
from pathlib import Path


def _detect_semantic_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric_continuous"
    if series.nunique() / max(series.count(), 1) < 0.5:
        return "categorical"
    return "text"


def _detect_outliers(series: pd.Series) -> list:
    """IQR-based outlier detection. Returns list of outlier values."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 3 * iqr
    upper = q3 + 3 * iqr
    return sorted(series[series > upper].tolist() + series[series < lower].tolist())


def profile_data(csv_path: str) -> dict:
    """Load CSV and return a profile dict describing its structure and statistics."""
    df = pd.read_csv(csv_path)

    # Try to parse object columns as dates
    for col in df.select_dtypes(include="object").columns:
        try:
            df[col] = pd.to_datetime(df[col])
        except (ValueError, TypeError):
            pass

    columns = []
    for col in df.columns:
        series = df[col]
        sem_type = _detect_semantic_type(series)
        col_info = {
            "name": col,
            "dtype": str(series.dtype),
            "semantic_type": sem_type,
            "null_count": int(series.isna().sum()),
            "unique_count": int(series.nunique()),
            "sample_values": series.dropna().head(3).tolist(),
        }
        if sem_type == "numeric_continuous":
            col_info["min"] = float(series.min()) if not series.isna().all() else None
            col_info["max"] = float(series.max()) if not series.isna().all() else None
            col_info["mean"] = float(series.mean()) if not series.isna().all() else None
            col_info["outliers"] = _detect_outliers(series.dropna())
        columns.append(col_info)

    return {
        "row_count": len(df),
        "columns": columns,
        "has_date_column": any(c["semantic_type"] == "date" for c in columns),
        "has_numeric_columns": any(c["semantic_type"] == "numeric_continuous" for c in columns),
        "has_categorical_columns": any(c["semantic_type"] == "categorical" for c in columns),
    }
