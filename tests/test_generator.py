# tests/test_generator.py
import json
import pytest
from pbix.visual_templates import build_visual_container

def test_line_chart_container_has_correct_type():
    spec = {
        "type": "lineChart",
        "title": "Revenue Over Time",
        "x_axis": "Date",
        "y_axis": "Revenue",
        "width": 600,
        "height": 350,
        "position": {"x": 0, "y": 0},
    }
    container = build_visual_container(spec)
    config = json.loads(container["config"])
    assert config["singleVisual"]["visualType"] == "lineChart"

def test_bar_chart_container_has_correct_type():
    spec = {
        "type": "barChart",
        "title": "Revenue by Region",
        "category": "Region",
        "value": "Revenue",
        "width": 600,
        "height": 350,
        "position": {"x": 620, "y": 0},
    }
    container = build_visual_container(spec)
    config = json.loads(container["config"])
    assert config["singleVisual"]["visualType"] == "clusteredBarChart"

def test_kpi_card_container():
    spec = {
        "type": "kpiCard",
        "title": "Total Revenue",
        "measure": "Total Revenue",
        "width": 200,
        "height": 120,
        "position": {"x": 0, "y": 370},
    }
    container = build_visual_container(spec)
    config = json.loads(container["config"])
    assert config["singleVisual"]["visualType"] == "card"

def test_container_has_required_keys():
    spec = {
        "type": "lineChart", "title": "T", "x_axis": "A", "y_axis": "B",
        "width": 100, "height": 100, "position": {"x": 0, "y": 0},
    }
    container = build_visual_container(spec)
    assert all(k in container for k in ["x", "y", "z", "width", "height", "config", "filters", "query", "dataTransforms"])
