# tests/test_generator.py
import json
import pytest
import zipfile
import os
import tempfile
from pbix.visual_templates import build_visual_container
from pbix.generator import generate_pbix

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

TEMPLATE = "pbix/template.pbix"

SAMPLE_MODEL_SPEC = {
    "report_title": "Q3 Sales",
    "data_source_path": "output/test/data.csv",
    "visuals": [
        {
            "type": "lineChart",
            "title": "Revenue Over Time",
            "x_axis": "Date",
            "y_axis": "Revenue",
            "width": 600,
            "height": 350,
            "position": {"x": 0, "y": 0},
        },
        {
            "type": "kpiCard",
            "title": "Total Revenue",
            "measure": "Total Revenue",
            "width": 200,
            "height": 120,
            "position": {"x": 620, "y": 0},
        },
    ],
}

def test_generate_pbix_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "out.pbix")
        generate_pbix(SAMPLE_MODEL_SPEC, TEMPLATE, out)
        assert os.path.exists(out)

def test_generated_pbix_is_valid_zip():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "out.pbix")
        generate_pbix(SAMPLE_MODEL_SPEC, TEMPLATE, out)
        assert zipfile.is_zipfile(out)

def test_generated_pbix_has_visuals_in_layout():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "out.pbix")
        generate_pbix(SAMPLE_MODEL_SPEC, TEMPLATE, out)
        with zipfile.ZipFile(out) as z:
            layout_raw = z.read("Report/Layout").decode("utf-16-le")
            layout = json.loads(layout_raw)
        containers = layout["sections"][0]["visualContainers"]
        assert len(containers) == 2
