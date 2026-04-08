import pytest
import pandas as pd
from data.processor import profile_data

FIXTURE = "tests/fixtures/sales_q3.csv"

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
