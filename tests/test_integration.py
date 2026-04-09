# tests/test_integration.py
# NOTE: This test makes real API calls to Anthropic. Set ANTHROPIC_API_KEY in .env before running.
import os
import zipfile
import pytest

FIXTURE_CSV = "tests/fixtures/sales_q3.csv"
COMMAND = "Analyze Q3 sales data, clean anomalies, and build a revenue dashboard."

@pytest.mark.integration
def test_end_to_end_produces_pbix(tmp_path):
    from agent.main_agent import run
    result = run(COMMAND, FIXTURE_CSV, output_dir=str(tmp_path))
    assert result["pbix_path"] is not None
    assert os.path.exists(result["pbix_path"])
    assert zipfile.is_zipfile(result["pbix_path"])

@pytest.mark.integration
def test_end_to_end_produces_report(tmp_path):
    from agent.main_agent import run
    result = run(COMMAND, FIXTURE_CSV, output_dir=str(tmp_path))
    assert result["report_path"] is not None
    assert os.path.exists(result["report_path"])
    content = open(result["report_path"], encoding="utf-8").read()
    assert "## Data Cleaning Log" in content
    assert "## Model Spec" in content


@pytest.mark.integration
def test_classify_domain_on_superstore():
    """classify_domain should return retail for the Superstore dataset (live API call)."""
    from data.processor import profile_data
    from agent.classifier import classify_domain

    csv_path = r"C:\Users\leonc\Desktop\archive\Sample - Superstore.csv"
    profile = profile_data(csv_path)
    result = classify_domain(profile)

    assert result["domain"] == "retail", (
        f"Expected retail, got {result['domain']}. Reasoning: {result['reasoning']}"
    )
    assert result["confidence"] in ("high", "medium")
    assert "revenue" in result["matched_columns"] or "profit" in result["matched_columns"]


@pytest.mark.integration
def test_classify_domain_on_generic_csv(tmp_path):
    """classify_domain should return generic for a non-retail dataset."""
    import pandas as pd
    from data.processor import profile_data
    from agent.classifier import classify_domain

    df = pd.DataFrame({
        "employee_id": range(20),
        "department": ["Engineering"] * 10 + ["Marketing"] * 10,
        "salary": [75000.0 + i * 1000 for i in range(20)],
        "tenure_years": [float(i % 10) for i in range(20)],
        "performance_score": [3.5 + (i % 5) * 0.1 for i in range(20)],
    })
    csv_path = str(tmp_path / "employees.csv")
    df.to_csv(csv_path, index=False)

    profile = profile_data(csv_path)
    result = classify_domain(profile)

    assert result["domain"] == "generic", (
        f"Expected generic, got {result['domain']}. Reasoning: {result['reasoning']}"
    )
