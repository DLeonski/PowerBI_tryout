import json

# Maps our spec type names to Power BI visualType strings
VISUAL_TYPE_MAP = {
    "lineChart": "lineChart",
    "barChart": "clusteredBarChart",
    "kpiCard": "card",
    "scatterPlot": "scatterChart",
    "pieChart": "donutChart",
    "tableEx": "tableEx",
}


def _base_config(visual_type: str, title: str) -> dict:
    return {
        "name": f"visual_{title.replace(' ', '_')}",
        "layouts": [{"id": 0, "position": {"x": 0, "y": 0, "z": 0, "tabOrder": 0, "height": 100, "width": 100}}],
        "singleVisual": {
            "visualType": visual_type,
            "drillFilterOtherVisuals": True,
            "objects": {
                "title": [{"properties": {"text": {"expr": {"Literal": {"Value": f"'{title}'"}}}, "show": {"expr": {"Literal": {"Value": "true"}}}}}]
            },
            "vcObjects": {},
            "projections": {},
            "prototypeQuery": {
                "Version": 2,
                "From": [],
                "Select": [],
            },
        },
    }


def build_visual_container(spec: dict) -> dict:
    """Build a Power BI Layout visualContainer dict from a model_spec visual entry."""
    pbi_type = VISUAL_TYPE_MAP.get(spec["type"], "tableEx")
    config = _base_config(pbi_type, spec.get("title", "Visual"))

    # Position/size
    pos = spec.get("position", {"x": 0, "y": 0})
    width = spec.get("width", 400)
    height = spec.get("height", 300)

    return {
        "x": pos["x"],
        "y": pos["y"],
        "z": 0,
        "width": width,
        "height": height,
        "config": json.dumps(config),
        "filters": "[]",
        "query": json.dumps({"Version": 2, "From": [], "Select": []}),
        "dataTransforms": json.dumps({"projectionOrdering": {}, "roles": {}}),
    }
