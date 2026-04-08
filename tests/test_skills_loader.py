from pathlib import Path
import pytest
from skills.loader import load_skills

def test_base_skills_always_loaded():
    text = load_skills()
    assert "dashboard" in text.lower()
    assert "chart type" in text.lower() or "viz-routing" in text.lower() or "line-chart" in text.lower()

def test_chart_skill_loaded_when_requested():
    text = load_skills(chart_types=["line-chart"])
    assert "line" in text.lower()

def test_multiple_chart_skills_loaded():
    text = load_skills(chart_types=["bar-chart", "kpi-card"])
    assert "bar" in text.lower()
    assert "kpi" in text.lower()

def test_unknown_chart_type_ignored_gracefully():
    text = load_skills(chart_types=["nonexistent-chart"])
    assert isinstance(text, str)
