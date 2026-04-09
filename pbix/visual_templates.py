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

# Aggregation function codes
AGG_SUM = 0
AGG_AVG = 2
AGG_COUNT = 4


def _source_ref(alias: str) -> dict:
    return {"SourceRef": {"Source": alias}}


def _col_select(alias: str, col: str, name: str) -> dict:
    return {
        "Column": {
            "Expression": _source_ref(alias),
            "Property": col,
        },
        "Name": name,
    }


def _agg_select(alias: str, col: str, name: str, func: int = AGG_SUM) -> dict:
    return {
        "Aggregation": {
            "Expression": {
                "Column": {
                    "Expression": _source_ref(alias),
                    "Property": col,
                }
            },
            "Function": func,
        },
        "Name": name,
    }


def _from_clause(table: str) -> list:
    return [{"Name": "t", "Entity": table, "Type": 0}]


def _build_card(spec: dict, table: str) -> dict:
    col = spec.get("value_column", "")
    query_name = f"Sum(t.{col})" if col else "count"
    selects = [_agg_select("t", col, query_name)] if col else []
    return {
        "prototypeQuery": {"Version": 2, "From": _from_clause(table), "Select": selects},
        "projections": {"Values": [{"queryRef": query_name, "active": False}]} if col else {},
    }


def _build_line_chart(spec: dict, table: str) -> dict:
    x_col = spec.get("x_column", "")
    y_col = spec.get("y_column", "")
    selects = []
    projections = {}
    if x_col:
        x_name = f"t.{x_col}"
        selects.append(_col_select("t", x_col, x_name))
        projections["Category"] = [{"queryRef": x_name, "active": False}]
    if y_col:
        y_name = f"Sum(t.{y_col})"
        selects.append(_agg_select("t", y_col, y_name))
        projections["Y"] = [{"queryRef": y_name, "active": False}]
    return {
        "prototypeQuery": {"Version": 2, "From": _from_clause(table), "Select": selects},
        "projections": projections,
    }


def _build_bar_chart(spec: dict, table: str) -> dict:
    cat_col = spec.get("category_column", spec.get("x_column", ""))
    val_col = spec.get("value_column", spec.get("y_column", ""))
    selects = []
    projections = {}
    if cat_col:
        cat_name = f"t.{cat_col}"
        selects.append(_col_select("t", cat_col, cat_name))
        projections["Category"] = [{"queryRef": cat_name, "active": False}]
    if val_col:
        val_name = f"Sum(t.{val_col})"
        selects.append(_agg_select("t", val_col, val_name))
        projections["Y"] = [{"queryRef": val_name, "active": False}]
    return {
        "prototypeQuery": {"Version": 2, "From": _from_clause(table), "Select": selects},
        "projections": projections,
    }


def _build_donut(spec: dict, table: str) -> dict:
    cat_col = spec.get("category_column", "")
    val_col = spec.get("value_column", spec.get("y_column", ""))
    selects = []
    projections = {}
    if cat_col:
        cat_name = f"t.{cat_col}"
        selects.append(_col_select("t", cat_col, cat_name))
        projections["Category"] = [{"queryRef": cat_name, "active": False}]
    if val_col:
        val_name = f"Sum(t.{val_col})"
        selects.append(_agg_select("t", val_col, val_name))
        projections["Y"] = [{"queryRef": val_name, "active": False}]
    return {
        "prototypeQuery": {"Version": 2, "From": _from_clause(table), "Select": selects},
        "projections": projections,
    }


def _build_table(spec: dict, table: str) -> dict:
    columns = spec.get("columns", [])
    selects = [_col_select("t", col, f"t.{col}") for col in columns]
    projections_list = [{"queryRef": f"t.{col}", "active": False} for col in columns]
    return {
        "prototypeQuery": {"Version": 2, "From": _from_clause(table), "Select": selects},
        "projections": {"Values": projections_list} if columns else {},
    }


_VISUAL_BUILDERS = {
    "kpiCard": _build_card,
    "lineChart": _build_line_chart,
    "barChart": _build_bar_chart,
    "pieChart": _build_donut,
    "tableEx": _build_table,
    "scatterPlot": _build_line_chart,  # reuse x/y structure
}


def build_visual_container(spec: dict, table: str = "data") -> dict:
    """Build a Power BI Layout visualContainer dict from a model_spec visual entry."""
    vis_type = spec.get("type", "tableEx")
    pbi_type = VISUAL_TYPE_MAP.get(vis_type, "tableEx")
    title = spec.get("title", "Visual")

    pos = spec.get("position", {"x": 0, "y": 0})
    width = spec.get("width", 400)
    height = spec.get("height", 300)

    # Build field bindings for this visual type
    builder = _VISUAL_BUILDERS.get(vis_type, _build_table)
    bindings = builder(spec, table)

    config = {
        "name": f"visual_{title.replace(' ', '_')}",
        "layouts": [{"id": 0, "position": {"x": pos.get("x", 0), "y": pos.get("y", 0), "z": 0, "tabOrder": 0, "height": height, "width": width}}],
        "singleVisual": {
            "visualType": pbi_type,
            "drillFilterOtherVisuals": True,
            "objects": {},
            "vcObjects": {
                "title": [{"properties": {
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                }}]
            },
            "prototypeQuery": bindings["prototypeQuery"],
            "projections": bindings["projections"],
        },
    }

    # Outer query mirrors prototypeQuery
    outer_query = bindings["prototypeQuery"]

    # Build dataTransforms selects from projections
    selects = []
    proj = bindings["projections"]
    for role, refs in proj.items():
        for ref in refs:
            col_name = ref["queryRef"].split(".")[-1].split("(")[-1].rstrip(")")
            selects.append({
                "displayName": col_name,
                "queryName": ref["queryRef"],
                "roles": {role: True},
            })

    proj_ordering = {role: list(range(len(refs))) for role, refs in proj.items()}

    return {
        "x": pos.get("x", 0),
        "y": pos.get("y", 0),
        "z": 0,
        "width": width,
        "height": height,
        "config": json.dumps(config),
        "filters": "[]",
        "query": json.dumps(outer_query),
        "dataTransforms": json.dumps({"selects": selects, "projectionOrdering": proj_ordering}),
    }
