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
            "sample_values": [str(v) for v in series.dropna().head(3)],
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


def clean_data(df: pd.DataFrame, rules: dict) -> tuple[pd.DataFrame, list[str]]:
    """Apply cleaning rules to df. Returns (clean_df, decision_log)."""
    df = df.copy()
    log = []

    if rules.get("remove_duplicates"):
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        log.append(f"Removed {removed} duplicate rows.")

    for col, strategy in rules.get("handle_nulls", {}).items():
        null_count = int(df[col].isna().sum())
        if null_count == 0:
            continue
        if strategy == "fill_mean":
            mean_val = df[col].mean()
            df[col] = df[col].fillna(mean_val)
            log.append(f"Filled {null_count} null(s) in '{col}' with mean ({mean_val:.2f}).")
        elif strategy == "fill_median":
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            log.append(f"Filled {null_count} null(s) in '{col}' with median ({median_val:.2f}).")
        elif strategy == "drop_row":
            df = df.dropna(subset=[col])
            log.append(f"Dropped {null_count} rows with null in '{col}'.")

    for col, cfg in rules.get("remove_outliers", {}).items():
        if col not in df.columns:
            continue
        series = df[col].dropna()
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        threshold = cfg.get("threshold", 3.0)
        upper = q3 + threshold * iqr
        lower = q1 - threshold * iqr
        outlier_mask = (df[col] > upper) | (df[col] < lower)
        count = int(outlier_mask.sum())
        if count > 0:
            df = df[~outlier_mask]
            log.append(
                f"Removed {count} outlier row(s) in '{col}' "
                f"(threshold: {threshold}x IQR, range [{lower:.2f}, {upper:.2f}])."
            )

    return df, log
