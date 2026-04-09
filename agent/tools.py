import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

from data.processor import profile_data, clean_data
from pbix.generator import generate_pbix
from skills.loader import load_skills
from agent.classifier import classify_domain as _classify_domain
import config

TOOL_DEFINITIONS = [
    {
        "name": "profile_data",
        "description": "Load a CSV file and return a profile describing column types, distributions, nulls, and outliers.",
        "input_schema": {
            "type": "object",
            "properties": {"csv_path": {"type": "string", "description": "Absolute or relative path to the CSV file."}},
            "required": ["csv_path"],
        },
    },
    {
        "name": "classify_domain",
        "description": "Classify the dataset domain (retail, generic) via a focused LLM call. Call this once after profile_data and before load_skills. Returns {domain, confidence, reasoning, matched_columns}.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "description": "The full profile dict returned by profile_data.",
                }
            },
            "required": ["profile"],
        },
    },
    {
        "name": "load_skills",
        "description": "Load skill documents. Always includes base skills. Pass chart_types to include specific chart design guides. Pass domain (from classify_domain result) to load domain-specific KPI skill. Set include_design=true to load the dashboard color & layout placement skill — REQUIRED before calling generate_pbix.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of chart type names e.g. ['line-chart', 'bar-chart', 'kpi-card']",
                },
                "include_design": {
                    "type": "boolean",
                    "description": "Set to true to load the dashboard color & layout placement skill (zones, color system, typography, anti-patterns). Must be loaded before generate_pbix.",
                },
                "domain": {
                    "type": "string",
                    "description": "Domain skill to load alongside base skills. Pass the domain returned by classify_domain (e.g. 'retail'). Omit or pass 'generic' to skip domain skill.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "clean_data",
        "description": "Apply cleaning rules to the loaded CSV data. Returns cleaned data path and decision log.",
        "input_schema": {
            "type": "object",
            "properties": {
                "csv_path": {"type": "string"},
                "rules": {
                    "type": "object",
                    "description": "Cleaning rules: remove_duplicates (bool), handle_nulls (object col->strategy), remove_outliers (object col->config)",
                },
                "output_dir": {"type": "string", "description": "Directory to save cleaned CSV."},
            },
            "required": ["csv_path", "rules", "output_dir"],
        },
    },
    {
        "name": "design_model",
        "description": "Given data profile and skills context, design the report model (visuals, measures). Returns model_spec dict.",
        "input_schema": {
            "type": "object",
            "properties": {
                "spec": {
                    "type": "object",
                    "description": "model_spec dict with keys: report_title, data_source_path, visuals (list), measures (list).",
                }
            },
            "required": ["spec"],
        },
    },
    {
        "name": "generate_pbix",
        "description": "Generate the .pbix file from the model_spec. IMPORTANT: Before calling this tool you MUST call load_skills with include_design=true to load dashboard layout, color, and typography rules.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_spec": {"type": "object"},
                "output_dir": {"type": "string"},
            },
            "required": ["model_spec", "output_dir"],
        },
    },
    {
        "name": "write_report",
        "description": "Write the Markdown decision report to the output directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "object",
                    "description": "Dict with keys: command, cleaning_log (list), model_spec, reviewer_notes.",
                },
                "output_dir": {"type": "string"},
            },
            "required": ["summary", "output_dir"],
        },
    },
]

# In-memory state shared across tool calls within one agent run
_state: dict = {}


def dispatch_tool(name: str, inputs: dict) -> dict:
    """Route a tool call to its implementation. Returns {status, data, message}."""
    try:
        if name == "profile_data":
            data = profile_data(inputs["csv_path"])
            _state["profile"] = data
            _state["csv_path"] = inputs["csv_path"]
            return {"status": "ok", "data": data, "message": f"Profiled {data['row_count']} rows."}

        elif name == "classify_domain":
            result = _classify_domain(inputs["profile"])
            _state["domain"] = result.get("domain", "generic")
            return {"status": "ok", "data": result, "message": f"Domain classified as: {result.get('domain')} (confidence: {result.get('confidence')})"}

        elif name == "load_skills":
            text = load_skills(
                chart_types=inputs.get("chart_types"),
                include_design=inputs.get("include_design", False),
                domain=inputs.get("domain"),
            )
            _state["skills_text"] = text
            return {"status": "ok", "data": {"text": text}, "message": "Skills loaded."}

        elif name == "clean_data":
            from data.processor import _read_csv_any_encoding
            df = _read_csv_any_encoding(inputs["csv_path"])
            clean_df, log = clean_data(df, inputs["rules"])
            out_dir = Path(inputs["output_dir"])
            out_dir.mkdir(parents=True, exist_ok=True)
            clean_path = str(out_dir / "data.xlsx")
            clean_df.to_excel(clean_path, index=False, sheet_name="data")
            _state.setdefault("cleaning_log", []).extend(log)
            _state["clean_csv_path"] = clean_path
            return {"status": "ok", "data": {"clean_csv_path": clean_path, "log": log}, "message": f"Cleaned data saved to {clean_path}."}

        elif name == "design_model":
            _state["model_spec"] = inputs["spec"]
            return {"status": "ok", "data": inputs["spec"], "message": "Model spec saved."}

        elif name == "generate_pbix":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_dir = Path(inputs["output_dir"])
            out_dir.mkdir(parents=True, exist_ok=True)
            pbix_path = str(out_dir / f"dashboard_{ts}.pbix")
            generate_pbix(inputs["model_spec"], config.PBIX_TEMPLATE_PATH, pbix_path)
            _state["pbix_path"] = pbix_path
            return {"status": "ok", "data": {"pbix_path": pbix_path}, "message": f"PBIX generated: {pbix_path}"}

        elif name == "write_report":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_dir = Path(inputs["output_dir"])
            out_dir.mkdir(parents=True, exist_ok=True)
            report_path = str(out_dir / f"report_{ts}.md")
            s = inputs["summary"]
            lines = [
                f"# Report: {s.get('command', '')}",
                f"\n**Generated:** {datetime.now().isoformat()}",
                "\n## Data Cleaning Log",
                *[f"- {entry}" for entry in s.get("cleaning_log", [])],
                "\n## Model Spec",
                f"```json\n{json.dumps(s.get('model_spec', {}), indent=2)}\n```",
                "\n## Reviewer Notes",
                s.get("reviewer_notes", "Approved."),
            ]
            Path(report_path).write_text("\n".join(lines), encoding="utf-8")
            _state["report_path"] = report_path
            return {"status": "ok", "data": {"report_path": report_path}, "message": f"Report written: {report_path}"}

        else:
            return {"status": "error", "data": None, "message": f"Unknown tool: {name}"}

    except Exception as e:
        return {"status": "error", "data": None, "message": str(e)}
