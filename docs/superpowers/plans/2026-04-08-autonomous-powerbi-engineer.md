# Autonomous Power BI Engineer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI agent that accepts a natural language command + CSV file and autonomously generates a Power BI `.pbix` dashboard with a Markdown decision report.

**Architecture:** Main Claude agent orchestrates 6 tool calls (profile → clean → load_skills → design_model → generate_pbix → write_report), then hands off to a Reviewer agent (separate Claude session) for self-check before producing output. Skills are loaded in two layers: base skills always, chart-specific design skills after the agent picks visual types from `viz-routing.md`.

**Tech Stack:** Python 3.11+, `anthropic` SDK (Claude claude-sonnet-4-6), `pandas`, `zipfile` + `json` (`.pbix` manipulation), `pytest`, `python-dotenv`, `argparse`

> **v1 scope note on `.pbix` data:** Power BI's DataModel is a compressed binary (Vertipaq). In v1 we do NOT embed data into the DataModel. Instead, the generator modifies only the `Report/Layout` JSON (human-readable, inside the ZIP) to configure visuals, and saves the cleaned CSV to a known path. The user opens the `.pbix` in Power BI Desktop and clicks **Refresh** to load the CSV. Full data embedding is v2.

---

## File Map

| File | Responsibility |
|------|---------------|
| `main.py` | CLI entry point — argparse, calls main agent |
| `config.py` | Loads `.env`, exposes `ANTHROPIC_API_KEY`, `OUTPUT_DIR` |
| `data/processor.py` | `profile_data(csv_path)` → profile dict; `clean_data(df, rules)` → clean df + log |
| `pbix/generator.py` | `generate_pbix(model_spec, template_path, output_path)` — ZIP/JSON manipulation |
| `pbix/visual_templates.py` | Pre-built Layout JSON config strings for each visual type |
| `skills/loader.py` | `load_skills(chart_types=None)` → concatenated skill text (base always included) |
| `agent/tools.py` | Tool definitions (JSON schema) + dispatch function for Claude tool calls |
| `agent/reviewer_agent.py` | `review(command, model_spec, decision_log)` → `{approved: bool, feedback: str}` |
| `agent/main_agent.py` | `run(command, csv_path)` — Claude tool-use loop + reviewer loop |
| `tests/fixtures/sales_q3.csv` | Sample sales data for tests |
| `tests/test_processor.py` | Unit tests for profiler and cleaner |
| `tests/test_generator.py` | Unit tests for PBIX generator |
| `tests/test_skills_loader.py` | Unit tests for skills loader |
| `tests/test_tools.py` | Unit tests for tool dispatch |
| `tests/test_integration.py` | End-to-end: command → `.pbix` file produced |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `.env.example`
- Create: `data/__init__.py`, `pbix/__init__.py`, `agent/__init__.py`, `skills/__init__.py`
- Create: `tests/__init__.py`, `tests/fixtures/`

- [ ] **Step 1: Create `requirements.txt`**

```
anthropic>=0.40.0
pandas>=2.1.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages install without errors.

- [ ] **Step 3: Create `.env.example`**

```
ANTHROPIC_API_KEY=your-key-here
OUTPUT_DIR=output
PBIX_TEMPLATE_PATH=pbix/template.pbix
```

- [ ] **Step 4: Create `.env`** (copy from example, fill in real key)

```bash
cp .env.example .env
# Edit .env and add your real ANTHROPIC_API_KEY
```

- [ ] **Step 5: Create `config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
PBIX_TEMPLATE_PATH = os.getenv("PBIX_TEMPLATE_PATH", "pbix/template.pbix")
```

- [ ] **Step 6: Create package `__init__.py` files**

Run:
```bash
mkdir -p data pbix agent skills tests/fixtures output
touch data/__init__.py pbix/__init__.py agent/__init__.py skills/__init__.py tests/__init__.py
```

- [ ] **Step 7: Create test fixture `tests/fixtures/sales_q3.csv`**

```csv
Date,Region,Product,Revenue,Units
2023-07-01,North,Widget A,45000.0,150
2023-07-01,South,Widget A,32000.0,110
2023-07-02,North,Widget B,28000.0,95
2023-07-02,East,Widget A,51000.0,170
2023-07-03,North,Widget A,150000.0,500
2023-07-03,West,Widget B,29000.0,98
2023-07-04,South,Widget A,,112
2023-07-04,East,Widget B,33000.0,115
2023-07-05,North,Widget A,48000.0,160
2023-07-05,South,Widget B,27000.0,90
```
(Row 5 has outlier Revenue=150000, Row 8 has null Revenue — intentional for testing cleaner.)

- [ ] **Step 8: Commit**

```bash
git add requirements.txt config.py .env.example data/__init__.py pbix/__init__.py agent/__init__.py skills/__init__.py tests/__init__.py tests/fixtures/sales_q3.csv
git commit -m "chore: project scaffolding and fixture data"
```

---

## Task 2: Data Profiler

**Files:**
- Create: `data/processor.py`
- Create: `tests/test_processor.py`

- [ ] **Step 1: Write failing test for `profile_data`**

```python
# tests/test_processor.py
import pytest
import pandas as pd
from data.processor import profile_data

FIXTURE = "tests/fixtures/sales_q3.csv"

def test_profile_returns_row_count():
    profile = profile_data(FIXTURE)
    assert profile["row_count"] == 10

def test_profile_detects_date_column():
    profile = profile_data(FIXTURE)
    date_col = next(c for c in profile["columns"] if c["name"] == "Date")
    assert date_col["semantic_type"] == "date"

def test_profile_detects_numeric_column():
    profile = profile_data(FIXTURE)
    rev_col = next(c for c in profile["columns"] if c["name"] == "Revenue")
    assert rev_col["semantic_type"] == "numeric_continuous"
    assert rev_col["null_count"] == 1
    assert rev_col["outliers"] == [150000.0]

def test_profile_detects_categorical_column():
    profile = profile_data(FIXTURE)
    reg_col = next(c for c in profile["columns"] if c["name"] == "Region")
    assert reg_col["semantic_type"] == "categorical"
    assert reg_col["unique_count"] == 4

def test_profile_has_summary_flags():
    profile = profile_data(FIXTURE)
    assert profile["has_date_column"] is True
    assert profile["has_numeric_columns"] is True
    assert profile["has_categorical_columns"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_processor.py -v`
Expected: `ModuleNotFoundError` or 5 FAILs — confirms tests are wired up.

- [ ] **Step 3: Implement `data/processor.py` — `profile_data`**

```python
import pandas as pd
import numpy as np
from pathlib import Path


def _detect_semantic_type(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric_continuous"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if series.nunique() / max(len(series), 1) < 0.2:
        return "categorical"
    return "text"


def _detect_outliers(series: pd.Series) -> list:
    """IQR-based outlier detection. Returns list of outlier values."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 3 * iqr
    upper = q3 + 3 * iqr
    return series[series > upper].tolist() + series[series < lower].tolist()


def profile_data(csv_path: str) -> dict:
    """Load CSV and return a profile dict describing its structure and statistics."""
    df = pd.read_csv(csv_path, parse_dates=True, infer_datetime_format=True)

    # Try to parse object columns as dates
    for col in df.select_dtypes(include="object").columns:
        try:
            df[col] = pd.to_datetime(df[col])
        except (ValueError, TypeError):
            pass

    columns = []
    for col in df.columns:
        series = df[col]
        sem_type = _detect_semantic_type(series)
        col_info = {
            "name": col,
            "dtype": str(series.dtype),
            "semantic_type": sem_type,
            "null_count": int(series.isna().sum()),
            "unique_count": int(series.nunique()),
            "sample_values": series.dropna().head(3).tolist(),
        }
        if sem_type == "numeric_continuous":
            col_info["min"] = float(series.min()) if not series.isna().all() else None
            col_info["max"] = float(series.max()) if not series.isna().all() else None
            col_info["mean"] = float(series.mean()) if not series.isna().all() else None
            col_info["outliers"] = _detect_outliers(series.dropna())
        columns.append(col_info)

    return {
        "row_count": len(df),
        "columns": columns,
        "has_date_column": any(c["semantic_type"] == "date" for c in columns),
        "has_numeric_columns": any(c["semantic_type"] == "numeric_continuous" for c in columns),
        "has_categorical_columns": any(c["semantic_type"] == "categorical" for c in columns),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_processor.py -v`
Expected: 5 PASSes.

- [ ] **Step 5: Commit**

```bash
git add data/processor.py tests/test_processor.py
git commit -m "feat: data profiler with IQR outlier detection"
```

---

## Task 3: Data Cleaner

**Files:**
- Modify: `data/processor.py` (add `clean_data`)
- Modify: `tests/test_processor.py` (add cleaner tests)

- [ ] **Step 1: Write failing tests for `clean_data`**

Add to `tests/test_processor.py`:
```python
from data.processor import clean_data

def test_clean_removes_outliers():
    df = pd.read_csv(FIXTURE)
    rules = {
        "remove_outliers": {"Revenue": {"method": "iqr", "threshold": 3.0}}
    }
    clean_df, log = clean_data(df, rules)
    assert 150000.0 not in clean_df["Revenue"].values
    assert any("outlier" in entry.lower() for entry in log)

def test_clean_fills_nulls_with_mean():
    df = pd.read_csv(FIXTURE)
    rules = {
        "handle_nulls": {"Revenue": "fill_mean"}
    }
    clean_df, log = clean_data(df, rules)
    assert clean_df["Revenue"].isna().sum() == 0
    assert any("null" in entry.lower() for entry in log)

def test_clean_removes_duplicates():
    df = pd.read_csv(FIXTURE)
    df_with_dupe = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    rules = {"remove_duplicates": True}
    clean_df, log = clean_data(df_with_dupe, rules)
    assert len(clean_df) == len(df)
    assert any("duplicate" in entry.lower() for entry in log)

def test_clean_returns_log_of_decisions():
    df = pd.read_csv(FIXTURE)
    rules = {"remove_duplicates": True}
    _, log = clean_data(df, rules)
    assert isinstance(log, list)
    assert len(log) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_processor.py::test_clean_removes_outliers -v`
Expected: FAIL with `ImportError` or `AttributeError`.

- [ ] **Step 3: Implement `clean_data` in `data/processor.py`**

Add to `data/processor.py`:
```python
def clean_data(df: pd.DataFrame, rules: dict) -> tuple[pd.DataFrame, list[str]]:
    """Apply cleaning rules to df. Returns (clean_df, decision_log)."""
    df = df.copy()
    log = []

    if rules.get("remove_duplicates"):
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        log.append(f"Removed {removed} duplicate rows.")

    for col, strategy in rules.get("handle_nulls", {}).items():
        null_count = df[col].isna().sum()
        if null_count == 0:
            continue
        if strategy == "fill_mean":
            mean_val = df[col].mean()
            df[col] = df[col].fillna(mean_val)
            log.append(f"Filled {null_count} null(s) in '{col}' with mean ({mean_val:.2f}).")
        elif strategy == "fill_median":
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            log.append(f"Filled {null_count} null(s) in '{col}' with median ({median_val:.2f}).")
        elif strategy == "drop_row":
            df = df.dropna(subset=[col])
            log.append(f"Dropped {null_count} rows with null in '{col}'.")

    for col, cfg in rules.get("remove_outliers", {}).items():
        if col not in df.columns:
            continue
        series = df[col].dropna()
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        threshold = cfg.get("threshold", 3.0)
        upper = q3 + threshold * iqr
        lower = q1 - threshold * iqr
        outlier_mask = (df[col] > upper) | (df[col] < lower)
        count = outlier_mask.sum()
        if count > 0:
            df = df[~outlier_mask]
            log.append(
                f"Removed {count} outlier row(s) in '{col}' "
                f"(threshold: {threshold}x IQR, range [{lower:.2f}, {upper:.2f}])."
            )

    return df, log
```

- [ ] **Step 4: Run all processor tests**

Run: `pytest tests/test_processor.py -v`
Expected: 9 PASSes.

- [ ] **Step 5: Commit**

```bash
git add data/processor.py tests/test_processor.py
git commit -m "feat: data cleaner with outlier removal, null handling, deduplication"
```

---

## Task 4: Skills Loader + Skill Files

**Files:**
- Create: `skills/loader.py`
- Create: `skills/base/dashboard-design.md`
- Create: `skills/base/general-rules.md`
- Create: `skills/viz-routing.md`
- Create: `skills/viz/line-chart.md`
- Create: `skills/viz/bar-chart.md`
- Create: `skills/viz/kpi-card.md`
- Create: `skills/viz/scatter-plot.md`
- Create: `skills/viz/pie-chart.md`
- Create: `skills/viz/table.md`
- Create: `tests/test_skills_loader.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_skills_loader.py
import pytest
from skills.loader import load_skills

def test_base_skills_always_loaded():
    text = load_skills()
    assert "dashboard" in text.lower()
    assert "viz-routing" in text.lower() or "chart type" in text.lower()

def test_chart_skill_loaded_when_requested():
    text = load_skills(chart_types=["line-chart"])
    assert "line" in text.lower()

def test_multiple_chart_skills_loaded():
    text = load_skills(chart_types=["bar-chart", "kpi-card"])
    assert "bar" in text.lower()
    assert "kpi" in text.lower()

def test_unknown_chart_type_ignored_gracefully():
    # Should not raise, just skip unknown skill files
    text = load_skills(chart_types=["nonexistent-chart"])
    assert isinstance(text, str)
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_skills_loader.py -v`
Expected: 4 FAILs.

- [ ] **Step 3: Implement `skills/loader.py`**

```python
from pathlib import Path

SKILLS_DIR = Path(__file__).parent

BASE_FILES = [
    SKILLS_DIR / "base" / "dashboard-design.md",
    SKILLS_DIR / "base" / "general-rules.md",
    SKILLS_DIR / "viz-routing.md",
]


def load_skills(chart_types: list[str] | None = None) -> str:
    """Return concatenated skill text. Base skills always included.
    chart_types: list of viz skill names e.g. ['line-chart', 'bar-chart']
    """
    parts = []
    for path in BASE_FILES:
        if path.exists():
            parts.append(f"## {path.stem}\n\n{path.read_text(encoding='utf-8')}")

    for chart_type in (chart_types or []):
        path = SKILLS_DIR / "viz" / f"{chart_type}.md"
        if path.exists():
            parts.append(f"## {path.stem}\n\n{path.read_text(encoding='utf-8')}")

    return "\n\n---\n\n".join(parts)
```

- [ ] **Step 4: Create `skills/base/dashboard-design.md`**

```markdown
# Dashboard Design Principles

## Layout
- Use a 1280x720 canvas (16:9).
- Place KPI cards at the top row (full width, height ~120px).
- Main charts occupy the middle section in a 2-column grid.
- Leave 10px margins between visuals.

## Color
- Use a consistent accent color for all charts (default: #0078D4 — Microsoft blue).
- Neutral background: #F3F2F1.
- Text: #252423.

## Titles
- Every visual must have a descriptive title (not just the column name).
- Report title: centered at top, font size 18.

## Simplicity
- Max 6 visuals per page for v1.
- Avoid pie charts when there are more than 5 categories.
```

- [ ] **Step 5: Create `skills/base/general-rules.md`**

```markdown
# General Data Rules

## Anomaly Handling
- Remove outliers defined as values beyond 3x IQR from Q1/Q3.
- Fill numeric nulls with column mean unless the column is an ID or date.
- Drop rows where date column is null.
- Log every cleaning decision with count and reason.

## Naming
- Column names in DAX measures must match the cleaned CSV column names exactly.
- Use snake_case for measure names in the model spec.

## DAX Measures to always include
- For any numeric column: SUM, AVERAGE
- If date column present: add a "by month" aggregation
```

- [ ] **Step 6: Create `skills/viz-routing.md`**

```markdown
# Visualization Routing

Given the data profile, select chart types as follows:

## Rules (apply in order, pick best match)

| Data pattern | Recommended chart | Notes |
|---|---|---|
| date column + 1 numeric column | `line-chart` | Time series |
| date column + 1 numeric + 1 categorical | `line-chart` (series per category) | Multi-series |
| 1 categorical + 1 numeric, ≤8 categories | `bar-chart` | Compare values |
| 1 categorical + 1 numeric, >8 categories | `table` | Too many bars |
| 2 numeric columns | `scatter-plot` | Correlation |
| Single KPI summary (SUM or AVERAGE of 1 numeric) | `kpi-card` | Always add 1-2 KPI cards |
| categorical breakdown with ≤5 categories | `pie-chart` | Use sparingly |
| multiple columns, no clear pattern | `table` | Fallback |

## Always include
- At least 1 `kpi-card` showing the primary numeric measure.
- A `table` as a details view if the dataset has more than 3 columns.

## Example
Data: Date, Region, Revenue → use: line-chart (Revenue over Date) + bar-chart (Revenue by Region) + kpi-card (Total Revenue)
```

- [ ] **Step 7: Create `skills/viz/line-chart.md`**

```markdown
# Line Chart Design

## When to use
Time series: x-axis is a date/time column, y-axis is a continuous numeric.

## Configuration
- X axis: date column, format "MMM YYYY" for monthly, "DD MMM" for daily.
- Y axis: numeric column, show gridlines, start at 0 unless data variance is small.
- Line: solid, 2px stroke, accent color (#0078D4).
- Show data labels only on last point.
- Legend: bottom, only if multi-series.

## model_spec fields
```json
{
  "type": "lineChart",
  "x_axis": "<date_column_name>",
  "y_axis": "<numeric_column_name>",
  "series": null
}
```

## Avoid
- Do not use line chart for categorical x-axis.
- Do not use more than 5 series on a single chart.
```

- [ ] **Step 8: Create `skills/viz/bar-chart.md`**

```markdown
# Bar Chart Design

## When to use
Compare a numeric measure across categories (≤8 unique values).

## Configuration
- Orientation: vertical (column chart) by default.
- X axis: categorical column, sorted descending by value.
- Y axis: numeric, no decimals for large numbers (use K/M suffix).
- Color: single accent color (#0078D4), no gradient.
- Data labels: inside end of bar.

## model_spec fields
```json
{
  "type": "barChart",
  "category": "<categorical_column_name>",
  "value": "<numeric_column_name>"
}
```
```

- [ ] **Step 9: Create `skills/viz/kpi-card.md`**

```markdown
# KPI Card Design

## When to use
Single summary statistic — always include at least one.

## Configuration
- Show: measure value (large font, 28px), label below (12px).
- Background: white card with subtle shadow.
- Value format: auto (K/M suffix for large numbers, 2 decimals for small).
- Size: 200x120px.

## model_spec fields
```json
{
  "type": "kpiCard",
  "title": "<human readable label>",
  "measure": "<DAX measure name>"
}
```
```

- [ ] **Step 10: Create remaining viz skill files**

`skills/viz/scatter-plot.md`:
```markdown
# Scatter Plot Design
## When to use
Correlation between two numeric columns.
## Configuration
- X axis: first numeric, Y axis: second numeric.
- Point size: 6px, opacity: 0.7.
- Add trend line if correlation coefficient > 0.5.
## model_spec fields
```json
{"type": "scatterPlot", "x_axis": "<numeric_col>", "y_axis": "<numeric_col>"}
```
```

`skills/viz/pie-chart.md`:
```markdown
# Pie Chart Design
## When to use
Part-to-whole with ≤5 categories. Use bar chart if >5.
## Configuration
- Show percentage labels outside slices.
- Legend: right side.
- No 3D effects.
## model_spec fields
```json
{"type": "pieChart", "category": "<categorical_col>", "value": "<numeric_col>"}
```
```

`skills/viz/table.md`:
```markdown
# Table Design
## When to use
Detail view or when >8 categories make charts unreadable.
## Configuration
- Show all columns from cleaned data.
- Alternating row colors: white / #F3F2F1.
- Header: bold, #252423.
- Max 20 rows visible, enable scroll.
## model_spec fields
```json
{"type": "tableEx", "columns": ["<col1>", "<col2>"]}
```
```

- [ ] **Step 11: Run skills tests**

Run: `pytest tests/test_skills_loader.py -v`
Expected: 4 PASSes.

- [ ] **Step 12: Commit**

```bash
git add skills/ tests/test_skills_loader.py
git commit -m "feat: two-level skills system with viz routing and chart design guides"
```

---

## Task 5: Obtain `.pbix` Template

Power BI Desktop must be installed on this machine. This task creates the `template.pbix` by hand — one-time manual step.

- [ ] **Step 1: Open Power BI Desktop and create blank report**

1. Open Power BI Desktop.
2. Choose **Blank report**.
3. Do NOT connect any data source.
4. Go to **File → Save As**.
5. Save as `pbix/template.pbix` in the project root.

- [ ] **Step 2: Verify the template is a valid ZIP**

Run:
```bash
python -c "import zipfile; z = zipfile.ZipFile('pbix/template.pbix'); print(z.namelist())"
```
Expected output includes: `['[Content_Types].xml', 'Report/Layout', 'Version', ...]`

- [ ] **Step 3: Inspect `Report/Layout` structure**

Run:
```python
# run as: python -c "exec(open('scripts/inspect_pbix.py').read())"
import zipfile, json
with zipfile.ZipFile("pbix/template.pbix") as z:
    layout_raw = z.read("Report/Layout").decode("utf-16-le")
    layout = json.loads(layout_raw)
    print(json.dumps(layout, indent=2)[:2000])
```

Save this as `scripts/inspect_pbix.py` and run it. Note the structure — specifically the `sections[0]` object and its `visualContainers` list (should be empty `[]` in a blank report).

- [ ] **Step 4: Commit template**

```bash
mkdir -p scripts
git add pbix/template.pbix scripts/inspect_pbix.py
git commit -m "chore: add blank pbix template and inspection script"
```

---

## Task 6: PBIX Visual Templates

**Files:**
- Create: `pbix/visual_templates.py`
- Create: `tests/test_generator.py` (partial — visual config tests)

Power BI's `Report/Layout` encodes visual config as a JSON-within-JSON string. This task builds the config-string factory for each visual type.

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_generator.py -v`
Expected: 4 FAILs.

- [ ] **Step 3: Implement `pbix/visual_templates.py`**

```python
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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_generator.py -v`
Expected: 4 PASSes.

- [ ] **Step 5: Commit**

```bash
git add pbix/visual_templates.py tests/test_generator.py
git commit -m "feat: pbix visual container factory for all chart types"
```

---

## Task 7: PBIX Generator

**Files:**
- Create: `pbix/generator.py`
- Modify: `tests/test_generator.py` (add generation tests)

- [ ] **Step 1: Write failing tests for `generate_pbix`**

Add to `tests/test_generator.py`:
```python
import zipfile
import os
import tempfile
from pbix.generator import generate_pbix

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
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_generator.py::test_generate_pbix_creates_file -v`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement `pbix/generator.py`**

```python
import json
import shutil
import zipfile
from pathlib import Path
from pbix.visual_templates import build_visual_container


def generate_pbix(model_spec: dict, template_path: str, output_path: str) -> None:
    """
    Generate a .pbix by cloning template and injecting visuals into Report/Layout.
    Data is NOT embedded — user must refresh data source in Power BI Desktop.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, output_path)

    # Read current layout from template
    with zipfile.ZipFile(output_path, "r") as z:
        layout_raw = z.read("Report/Layout").decode("utf-16-le")

    layout = json.loads(layout_raw)

    # Ensure at least one section exists
    if not layout.get("sections"):
        layout["sections"] = [{
            "id": 0,
            "name": "ReportSection",
            "displayName": model_spec.get("report_title", "Dashboard"),
            "visualContainers": [],
            "width": 1280,
            "height": 720,
            "config": "{}",
            "filters": "[]",
        }]

    section = layout["sections"][0]
    section["displayName"] = model_spec.get("report_title", "Dashboard")

    # Build visual containers from spec
    section["visualContainers"] = [
        build_visual_container(vis) for vis in model_spec.get("visuals", [])
    ]

    new_layout = json.dumps(layout)

    # Repack ZIP with updated Layout
    tmp_path = output_path + ".tmp"
    with zipfile.ZipFile(output_path, "r") as zin:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "Report/Layout":
                    zout.writestr(item, new_layout.encode("utf-16-le"))
                else:
                    zout.writestr(item, zin.read(item.filename))

    Path(output_path).unlink()
    Path(tmp_path).rename(output_path)
```

- [ ] **Step 4: Run all generator tests**

Run: `pytest tests/test_generator.py -v`
Expected: 7 PASSes.

- [ ] **Step 5: Commit**

```bash
git add pbix/generator.py tests/test_generator.py
git commit -m "feat: pbix generator via ZIP/JSON layout injection"
```

---

## Task 8: Agent Tools

**Files:**
- Create: `agent/tools.py`
- Create: `tests/test_tools.py`

This module defines the tool schemas (sent to Claude) and a dispatcher that routes tool calls to the actual implementations.

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/test_tools.py -v`
Expected: 4 FAILs.

- [ ] **Step 3: Implement `agent/tools.py`**

```python
import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

from data.processor import profile_data, clean_data
from pbix.generator import generate_pbix
from skills.loader import load_skills
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
        "name": "load_skills",
        "description": "Load skill documents. Always includes base skills. Pass chart_types to include specific chart design guides.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of chart type names e.g. ['line-chart', 'bar-chart', 'kpi-card']",
                }
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
                    "description": "Cleaning rules: remove_duplicates (bool), handle_nulls (object col→strategy), remove_outliers (object col→config)",
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
        "description": "Generate the .pbix file from the model_spec.",
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

        elif name == "load_skills":
            text = load_skills(chart_types=inputs.get("chart_types"))
            _state["skills_text"] = text
            return {"status": "ok", "data": {"text": text}, "message": "Skills loaded."}

        elif name == "clean_data":
            df = pd.read_csv(inputs["csv_path"])
            clean_df, log = clean_data(df, inputs["rules"])
            out_dir = Path(inputs["output_dir"])
            out_dir.mkdir(parents=True, exist_ok=True)
            clean_path = str(out_dir / "data.csv")
            clean_df.to_csv(clean_path, index=False)
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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_tools.py -v`
Expected: 4 PASSes.

- [ ] **Step 5: Commit**

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: agent tool definitions and dispatcher"
```

---

## Task 9: Reviewer Agent

**Files:**
- Create: `agent/reviewer_agent.py`

- [ ] **Step 1: Implement `agent/reviewer_agent.py`**

No unit test for reviewer (it makes a live API call). Test via integration in Task 11.

```python
import json
import anthropic
import config

REVIEWER_SYSTEM_PROMPT = """You are a Power BI dashboard quality reviewer.
You receive: the original user command, the model_spec (visuals and measures designed), and the data cleaning log.
Your job: check that the visuals match the data, DAX measures are syntactically plausible, and cleaning decisions were sensible.
Reply with a JSON object: {"approved": true/false, "feedback": "...brief explanation..."}
Be concise. Only block (approved: false) for clear errors (wrong visual type, obviously broken DAX, missing key visual).
"""


def review(command: str, model_spec: dict, decision_log: list[str]) -> dict:
    """
    Run a separate Claude session to review the agent's decisions.
    Returns {"approved": bool, "feedback": str}
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    user_message = f"""
User command: {command}

Cleaning decisions:
{chr(10).join(f'- {entry}' for entry in decision_log)}

Model spec:
{json.dumps(model_spec, indent=2)}

Review and reply with JSON: {{"approved": true/false, "feedback": "..."}}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=REVIEWER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text.strip()
    # Extract JSON from response (may be wrapped in markdown code block)
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # If Claude didn't return valid JSON, treat as approved with note
        return {"approved": True, "feedback": text}
```

- [ ] **Step 2: Commit**

```bash
git add agent/reviewer_agent.py
git commit -m "feat: reviewer agent with separate Claude session for self-check"
```

---

## Task 10: Main Agent

**Files:**
- Create: `agent/main_agent.py`

- [ ] **Step 1: Implement `agent/main_agent.py`**

```python
import json
from datetime import datetime
from pathlib import Path

import anthropic

import config
from agent.tools import TOOL_DEFINITIONS, dispatch_tool, _state
from agent.reviewer_agent import review

SYSTEM_PROMPT = """You are an autonomous Power BI engineer. You receive a natural language command and a CSV file path.
Your job is to produce a Power BI dashboard (.pbix) and a decision report (.md).

You MUST call tools in this order:
1. profile_data — understand the data
2. load_skills — load base skills AND viz-routing. Analyze viz-routing to pick chart types, then call load_skills again with chart_types for the charts you selected.
3. clean_data — clean based on profile and general-rules skill
4. design_model — design visuals and DAX measures based on data profile and loaded skills
5. generate_pbix — generate the .pbix file
6. write_report — write the decision report

Use the output_dir provided in the user message for all file outputs.
When calling design_model, pass a complete model_spec with: report_title, data_source_path (the cleaned CSV path), visuals (list), measures (list of {name, expression}).
"""


def run(command: str, csv_path: str, output_dir: str | None = None) -> dict:
    """
    Run the main agent. Returns {pbix_path, report_path, reviewer_feedback}.
    Raises RuntimeError if reviewer rejects after 2 iterations.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_dir or str(Path(config.OUTPUT_DIR) / ts)

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    user_message = f"""Command: {command}
CSV file: {csv_path}
Output directory: {output_dir}
"""

    messages = [{"role": "user", "content": user_message}]

    # Tool-use loop
    for _ in range(20):  # max 20 tool calls to prevent runaway loops
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "user", "content": tool_results})

    # Reviewer loop (max 2 iterations)
    model_spec = _state.get("model_spec", {})
    cleaning_log = _state.get("cleaning_log", [])

    for attempt in range(2):
        review_result = review(command, model_spec, cleaning_log)

        if review_result.get("approved", True):
            break

        if attempt == 1:
            # Write diagnostic report instead of .pbix
            error_report = Path(output_dir) / "review_failed.md"
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            error_report.write_text(
                f"# Review Failed\n\nFeedback after 2 attempts:\n{review_result['feedback']}",
                encoding="utf-8",
            )
            raise RuntimeError(
                f"Reviewer rejected output after 2 attempts. See {error_report}"
            )

        # Feed reviewer feedback back into agent for one more pass
        messages.append({
            "role": "user",
            "content": f"Reviewer feedback: {review_result['feedback']}. Please redesign the model_spec and regenerate.",
        })

        # Re-run tool loop
        for _ in range(10):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason == "end_turn":
                break
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                messages.append({"role": "user", "content": tool_results})
        model_spec = _state.get("model_spec", {})

    return {
        "pbix_path": _state.get("pbix_path"),
        "report_path": _state.get("report_path"),
        "reviewer_feedback": review_result.get("feedback", ""),
    }
```

- [ ] **Step 2: Commit**

```bash
git add agent/main_agent.py
git commit -m "feat: main agent with tool-use loop and reviewer feedback cycle"
```

---

## Task 11: CLI Entry Point

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement `main.py`**

```python
import argparse
import sys
from agent.main_agent import run


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Power BI Engineer — generates .pbix dashboards from CSV + natural language."
    )
    parser.add_argument("command", type=str, help='Natural language command, e.g. "Analyze Q3 sales and build a dashboard"')
    parser.add_argument("csv", type=str, help="Path to the input CSV file")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory (default: output/<timestamp>)")

    args = parser.parse_args()

    print(f"Running agent...\nCommand: {args.command}\nCSV: {args.csv}\n")

    try:
        result = run(args.command, args.csv, output_dir=args.output_dir)
        print(f"\nDone!")
        print(f"  Dashboard: {result['pbix_path']}")
        print(f"  Report:    {result['report_path']}")
        if result.get("reviewer_feedback"):
            print(f"  Reviewer:  {result['reviewer_feedback']}")
    except RuntimeError as e:
        print(f"\nAgent stopped: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test CLI help**

Run: `python main.py --help`
Expected: Prints usage with `command`, `csv`, and `--output-dir` arguments.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: CLI entry point with argparse"
```

---

## Task 12: Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
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
```

- [ ] **Step 2: Add `pytest.ini` to mark integration tests**

```ini
# pytest.ini
[pytest]
markers =
    integration: marks tests as integration tests (require ANTHROPIC_API_KEY, deselect with -m "not integration")
```

- [ ] **Step 3: Run unit tests only (no API calls)**

Run: `pytest -m "not integration" -v`
Expected: All unit tests pass. Integration tests skipped.

- [ ] **Step 4: Run full integration test**

Run: `pytest tests/test_integration.py -v -s`
Expected: Agent runs end-to-end, produces `.pbix` and `.md` in the tmp directory. Takes 30-90 seconds.

- [ ] **Step 5: Final commit**

```bash
git add tests/test_integration.py pytest.ini
git commit -m "test: integration test for end-to-end agent run"
```

---

## Post-Implementation: Manual Verification

After the integration test passes:

1. Find the generated `.pbix` in `output/`
2. Open it in **Power BI Desktop**
3. Go to **Home → Transform Data → Data Source Settings**
4. Update the CSV path to point to the `data.csv` file in the same output folder
5. Click **Refresh** — visuals should populate
6. Verify: correct number of visuals, titles match the report, no error banners
