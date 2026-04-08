import pytest
import pandas as pd
from pathlib import Path
from data.processor import profile_data

FIXTURE = str(Path(__file__).parent / "fixtures/sales_q3.csv")

def test_profile_returns_row_count():
    profile = profile_data(FIXTURE)
    assert profile["row_count"] == 10

def test_profile_detects_date_column():
    profile = profile_data(FIXTURE)
    date_col = next(c for c in profile["columns"] if c["name"] == "Date")
    assert date_col["semantic_type"] == "date"

def test_profile_detects_numeric_column():
    profile = profile_data(FIXTURE)
    rev_col = next(c for c in profile["columns"] if c["name"] == "Revenue")
    assert rev_col["semantic_type"] == "numeric_continuous"
    assert rev_col["null_count"] == 1
    assert rev_col["outliers"] == [150000.0]

def test_profile_detects_categorical_column():
    profile = profile_data(FIXTURE)
    reg_col = next(c for c in profile["columns"] if c["name"] == "Region")
    assert reg_col["semantic_type"] == "categorical"
    assert reg_col["unique_count"] == 4

def test_profile_has_summary_flags():
    profile = profile_data(FIXTURE)
    assert profile["has_date_column"] is True
    assert profile["has_numeric_columns"] is True
    assert profile["has_categorical_columns"] is True

def test_profile_numeric_stats_present():
    profile = profile_data(FIXTURE)
    rev_col = next(c for c in profile["columns"] if c["name"] == "Revenue")
    assert "min" in rev_col
    assert "max" in rev_col
    assert "mean" in rev_col
    assert rev_col["min"] == pytest.approx(27000.0)
    assert rev_col["max"] == pytest.approx(150000.0)

def test_profile_boolean_column():
    import tempfile
    import os
    df = pd.DataFrame({"flag": [True, False, True], "value": [1.0, 2.0, 3.0]})
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False, newline="") as f:
        df.to_csv(f, index=False)
        tmp = f.name
    try:
        profile = profile_data(tmp)
        flag_col = next(c for c in profile["columns"] if c["name"] == "flag")
        assert flag_col["semantic_type"] == "boolean"
    finally:
        os.unlink(tmp)

from data.processor import clean_data

def test_clean_removes_outliers():
    df = pd.read_csv(FIXTURE)
    rules = {
        "remove_outliers": {"Revenue": {"method": "iqr", "threshold": 3.0}}
    }
    clean_df, log = clean_data(df, rules)
    assert 150000.0 not in clean_df["Revenue"].values
    assert any("outlier" in entry.lower() for entry in log)

def test_clean_fills_nulls_with_mean():
    df = pd.read_csv(FIXTURE)
    rules = {
        "handle_nulls": {"Revenue": "fill_mean"}
    }
    clean_df, log = clean_data(df, rules)
    assert clean_df["Revenue"].isna().sum() == 0
    assert any("null" in entry.lower() for entry in log)

def test_clean_removes_duplicates():
    df = pd.read_csv(FIXTURE)
    df_with_dupe = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    rules = {"remove_duplicates": True}
    clean_df, log = clean_data(df_with_dupe, rules)
    assert len(clean_df) == len(df)
    assert any("duplicate" in entry.lower() for entry in log)

def test_clean_returns_log_of_decisions():
    df = pd.read_csv(FIXTURE)
    rules = {"remove_duplicates": True}
    _, log = clean_data(df, rules)
    assert isinstance(log, list)
    assert len(log) > 0
