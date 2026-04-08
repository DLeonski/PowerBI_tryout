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
