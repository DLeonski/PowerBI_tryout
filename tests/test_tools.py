# tests/test_tools.py
import pytest
from agent.tools import TOOL_DEFINITIONS, dispatch_tool

def test_tool_definitions_are_valid_schemas():
    required_keys = {"name", "description", "input_schema"}
    for tool in TOOL_DEFINITIONS:
        assert required_keys.issubset(tool.keys()), f"Tool missing keys: {tool}"
        assert tool["input_schema"]["type"] == "object"

def test_tool_names_match_expected():
    names = {t["name"] for t in TOOL_DEFINITIONS}
    assert names == {
        "profile_data", "load_skills", "clean_data",
        "design_model", "generate_pbix", "write_report"
    }

def test_dispatch_profile_data_returns_dict(tmp_path):
    import shutil
    csv_dst = tmp_path / "sales.csv"
    shutil.copy("tests/fixtures/sales_q3.csv", csv_dst)
    result = dispatch_tool("profile_data", {"csv_path": str(csv_dst)})
    assert result["status"] == "ok"
    assert "row_count" in result["data"]

def test_dispatch_unknown_tool_returns_error():
    result = dispatch_tool("nonexistent_tool", {})
    assert result["status"] == "error"
