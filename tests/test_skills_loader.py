from pathlib import Path
import pytest
from skills.loader import load_skills

def test_base_skills_always_loaded():
    text = load_skills()
    assert "general" in text.lower()
    assert "chart type" in text.lower() or "viz-routing" in text.lower() or "line-chart" in text.lower()


def test_design_skill_loaded_when_requested():
    text = load_skills(include_design=True)
    assert "dashboard" in text.lower()
    assert "zone" in text.lower()
    assert "color" in text.lower()

def test_chart_skill_loaded_when_requested():
    text = load_skills(chart_types=["line-chart"])
    assert "line" in text.lower()

def test_multiple_chart_skills_loaded():
    text = load_skills(chart_types=["column-bar-chart", "kpi-card"])
    assert "bar" in text.lower()
    assert "kpi" in text.lower()

def test_unknown_chart_type_ignored_gracefully():
    text = load_skills(chart_types=["nonexistent-chart"])
    assert isinstance(text, str)

def test_domain_skill_loaded_when_requested():
    text = load_skills(domain="retail")
    assert "retail" in text.lower()
    assert "north star" in text.lower()

def test_generic_domain_loads_no_domain_skill():
    text_generic = load_skills(domain="generic")
    text_none = load_skills(domain=None)
    # Both should have same base content; neither loads retail
    assert "north star" not in text_generic.lower()
    assert "north star" not in text_none.lower()

def test_unknown_domain_ignored_gracefully():
    text = load_skills(domain="nonexistent-domain")
    assert isinstance(text, str)
    assert "general" in text.lower()
