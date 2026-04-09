# Domain Classifier + Domain Skill System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `classify_domain` LLM sub-call that fires after `profile_data`, identifies the dataset as `retail` or `generic`, and loads the appropriate domain skill so the agent designs domain-aware dashboards.

**Architecture:** A new `agent/classifier.py` module makes a focused Haiku API call with the data profile and returns `{domain, confidence, reasoning, matched_columns}`. The result is passed to `load_skills` via a new `domain` parameter, which appends the matching file from `skills/domains/`. The main agent system prompt is updated to call `classify_domain` as step 2.

**Tech Stack:** Python 3.11, `anthropic` SDK (already installed), `pytest` for tests.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `skills/domains/retail.md` | CREATE | Retail KPI skill document |
| `skills/domains/generic.md` | CREATE | Generic fallback (instructs base-skills-only) |
| `skills/loader.py` | MODIFY | Add `domain` parameter |
| `agent/classifier.py` | CREATE | `classify_domain(profile) -> dict` via Haiku API call |
| `agent/tools.py` | MODIFY | Add `classify_domain` tool definition + dispatch; add `domain` to `load_skills` |
| `agent/main_agent.py` | MODIFY | Update SYSTEM_PROMPT steps 2-3 |
| `tests/test_classifier.py` | CREATE | Unit tests for classifier with mocked API |
| `tests/test_skills_loader.py` | MODIFY | Add test for `domain` parameter |
| `tests/test_tools.py` | MODIFY | Update expected tool names set |

---

## Task 1: Create skill domain files

**Files:**
- Create: `skills/domains/retail.md`
- Create: `skills/domains/generic.md`

- [ ] **Step 1: Create the domains directory and generic fallback**

```bash
mkdir skills/domains
```

Create `skills/domains/generic.md`:

```markdown
# Generic Domain Skill

No specific domain was detected for this dataset.

Apply base skills only: use the general-rules and viz-routing skills already loaded.
Select visuals based on column types from the data profile.
Do not assume any domain-specific KPI hierarchy.
```

- [ ] **Step 2: Create `skills/domains/retail.md`**

Copy the full content of the retail skill document provided during the design session
(`docs/superpowers/specs/2026-04-09-domain-classifier-design.md` references it as
"the skill document already authored"). The file must begin with this frontmatter:

```markdown
---
name: retail-pbix-agent
description: >
  Use this skill whenever the agent is building a Power BI (.pbix) file or dashboard from
  retail, e-commerce, or transactional sales data regardless of the specific schema or
  column names used. Trigger on any dataset that contains transactional records linking
  customers, products, and sales amounts.
---

# Retail PBIX Agent Skill

## Purpose
This skill makes the agent behave like a senior retail analyst when generating Power BI
dashboards from any transactional sales dataset...
```

Paste the complete skill text (all 8 Steps + Universal Principles section) from the
document shared in the brainstorming session.

- [ ] **Step 3: Commit**

```bash
git add skills/domains/
git commit -m "feat: add domain skill files (retail + generic fallback)"
```

---

## Task 2: Update `skills/loader.py` — add domain parameter

**Files:**
- Modify: `skills/loader.py`
- Modify: `tests/test_skills_loader.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_skills_loader.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_skills_loader.py::test_domain_skill_loaded_when_requested -v
```

Expected: `FAILED` — `load_skills() got an unexpected keyword argument 'domain'`

- [ ] **Step 3: Update `skills/loader.py`**

```python
from pathlib import Path

SKILLS_DIR = Path(__file__).parent

BASE_FILES = [
    SKILLS_DIR / "base" / "general-rules.md",
    SKILLS_DIR / "viz-routing.md",
]

DESIGN_SKILL_FILE = SKILLS_DIR / "base" / "dashboard-design.md"


def load_skills(
    chart_types: list[str] | None = None,
    include_design: bool = False,
    domain: str | None = None,
) -> str:
    """Return concatenated skill text. Base skills always included.
    chart_types: list of viz skill names e.g. ['line-chart', 'bar-chart']
    include_design: if True, append the dashboard color & layout placement skill
    domain: domain name e.g. 'retail'. Loads skills/domains/<domain>.md if it exists.
            Pass None or 'generic' to skip domain skill.
    """
    parts = []
    for path in BASE_FILES:
        if path.exists():
            parts.append(f"## {path.stem}\n\n{path.read_text(encoding='utf-8')}")

    if domain and domain != "generic":
        domain_path = SKILLS_DIR / "domains" / f"{domain}.md"
        if domain_path.exists():
            parts.append(f"## domain-{domain}\n\n{domain_path.read_text(encoding='utf-8')}")

    for chart_type in (chart_types or []):
        path = SKILLS_DIR / "viz" / f"{chart_type}.md"
        if path.exists():
            parts.append(f"## {path.stem}\n\n{path.read_text(encoding='utf-8')}")

    if include_design and DESIGN_SKILL_FILE.exists():
        parts.append(f"## {DESIGN_SKILL_FILE.stem}\n\n{DESIGN_SKILL_FILE.read_text(encoding='utf-8')}")

    return "\n\n---\n\n".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_skills_loader.py -v
```

Expected: all 8 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add skills/loader.py tests/test_skills_loader.py
git commit -m "feat: add domain parameter to load_skills"
```

---

## Task 3: Create `agent/classifier.py`

**Files:**
- Create: `agent/classifier.py`
- Create: `tests/test_classifier.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_classifier.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from agent.classifier import classify_domain

RETAIL_PROFILE = {
    "row_count": 20,
    "columns": [
        {"name": "Order ID", "dtype": "object", "semantic_type": "categorical", "unique_count": 20},
        {"name": "Order Date", "dtype": "datetime64[ns]", "semantic_type": "date", "unique_count": 15},
        {"name": "Sales", "dtype": "float64", "semantic_type": "numeric_continuous", "unique_count": 20},
        {"name": "Profit", "dtype": "float64", "semantic_type": "numeric_continuous", "unique_count": 20},
        {"name": "Quantity", "dtype": "int64", "semantic_type": "numeric_continuous", "unique_count": 8},
        {"name": "Discount", "dtype": "float64", "semantic_type": "numeric_continuous", "unique_count": 5},
        {"name": "Category", "dtype": "object", "semantic_type": "categorical", "unique_count": 3},
        {"name": "Sub-Category", "dtype": "object", "semantic_type": "categorical", "unique_count": 17},
        {"name": "Region", "dtype": "object", "semantic_type": "categorical", "unique_count": 4},
        {"name": "Customer Name", "dtype": "object", "semantic_type": "text", "unique_count": 18},
    ],
    "has_date_column": True,
    "has_numeric_columns": True,
    "has_categorical_columns": True,
}

GENERIC_PROFILE = {
    "row_count": 20,
    "columns": [
        {"name": "employee_id", "dtype": "int64", "semantic_type": "numeric_continuous", "unique_count": 20},
        {"name": "department", "dtype": "object", "semantic_type": "categorical", "unique_count": 5},
        {"name": "salary", "dtype": "float64", "semantic_type": "numeric_continuous", "unique_count": 18},
        {"name": "hire_date", "dtype": "datetime64[ns]", "semantic_type": "date", "unique_count": 15},
    ],
    "has_date_column": True,
    "has_numeric_columns": True,
    "has_categorical_columns": True,
}


def _make_mock_response(domain: str, confidence: str, reasoning: str, matched: dict):
    """Build a mock anthropic response with the classifier JSON."""
    import json
    payload = json.dumps({
        "domain": domain,
        "confidence": confidence,
        "reasoning": reasoning,
        "matched_columns": matched,
    })
    mock_content = MagicMock()
    mock_content.text = payload
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


@patch("agent.classifier.anthropic.Anthropic")
def test_retail_profile_returns_retail_domain(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        domain="retail",
        confidence="high",
        reasoning="Sales, Profit, Order Date, Category, Sub-Category detected",
        matched={"revenue": "Sales", "profit": "Profit", "transaction_date": "Order Date"},
    )

    result = classify_domain(RETAIL_PROFILE)

    assert result["domain"] == "retail"
    assert result["confidence"] == "high"
    assert "matched_columns" in result
    assert "reasoning" in result


@patch("agent.classifier.anthropic.Anthropic")
def test_generic_profile_returns_generic_domain(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_mock_response(
        domain="generic",
        confidence="high",
        reasoning="No retail indicators detected",
        matched={},
    )

    result = classify_domain(GENERIC_PROFILE)

    assert result["domain"] == "generic"


@patch("agent.classifier.anthropic.Anthropic")
def test_api_error_falls_back_to_generic(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.side_effect = Exception("API timeout")

    result = classify_domain(RETAIL_PROFILE)

    assert result["domain"] == "generic"
    assert result["confidence"] == "low"
    assert "error" in result["reasoning"].lower()


@patch("agent.classifier.anthropic.Anthropic")
def test_malformed_json_falls_back_to_generic(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_content = MagicMock()
    mock_content.text = "not valid json at all"
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response

    result = classify_domain(RETAIL_PROFILE)

    assert result["domain"] == "generic"
    assert result["confidence"] == "low"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_classifier.py -v
```

Expected: `ERROR` — `ModuleNotFoundError: No module named 'agent.classifier'`

- [ ] **Step 3: Create `agent/classifier.py`**

```python
import json
import anthropic
import config

_SYSTEM_PROMPT = """You are a data domain classifier. Given a CSV data profile (column names, dtypes, sample values), identify which domain the dataset belongs to.

Known domains:
- retail: Transactional sales data. Indicators: columns for revenue/sales/amount, profit/margin, quantity/units, discount/promo, order date, product category/sub-category, customer name/id, region/geography, order id/transaction id. E-commerce, POS, marketplace exports (Shopify, WooCommerce, ERP), superstore-style CSVs all qualify.
- generic: Everything else — HR, finance, scientific, IoT, logs, etc.

Respond ONLY with a JSON object, no markdown fences, no explanation outside the JSON:
{
  "domain": "<retail|generic>",
  "confidence": "<high|medium|low>",
  "reasoning": "<one sentence>",
  "matched_columns": {
    "<semantic_role>": "<actual_column_name>"
  }
}

matched_columns should map semantic roles (revenue, profit, transaction_date, quantity, discount, category, sub_category, customer_name, region) to the actual column names found. Omit roles not found. Empty object {} if domain is generic."""


def classify_domain(profile: dict) -> dict:
    """Classify the dataset domain via a focused Haiku API call.

    Args:
        profile: The dict returned by profile_data (row_count, columns, ...).

    Returns:
        {domain, confidence, reasoning, matched_columns}
        Falls back to {domain: 'generic', confidence: 'low'} on any error.
    """
    fallback = {
        "domain": "generic",
        "confidence": "low",
        "reasoning": "Classification failed — defaulting to generic.",
        "matched_columns": {},
    }

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        # Slim down the profile to just what the classifier needs
        slim_profile = {
            "row_count": profile.get("row_count"),
            "columns": [
                {
                    "name": col["name"],
                    "dtype": col["dtype"],
                    "semantic_type": col.get("semantic_type"),
                    "unique_count": col.get("unique_count"),
                    "sample_values": col.get("sample_values", [])[:3],
                }
                for col in profile.get("columns", [])
            ],
        }

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Classify this dataset profile:\n\n{json.dumps(slim_profile, indent=2)}",
                }
            ],
        )

        raw = response.content[0].text.strip()
        result = json.loads(raw)

        # Ensure required keys present
        for key in ("domain", "confidence", "reasoning", "matched_columns"):
            if key not in result:
                return fallback

        return result

    except Exception as e:
        fallback["reasoning"] = f"Classification error: {e}"
        return fallback
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_classifier.py -v
```

Expected: all 4 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add agent/classifier.py tests/test_classifier.py
git commit -m "feat: add classify_domain with Haiku LLM sub-call and fallback"
```

---

## Task 4: Update `agent/tools.py` — add classify_domain tool + domain param

**Files:**
- Modify: `agent/tools.py`
- Modify: `tests/test_tools.py`

- [ ] **Step 1: Update the expected tool names test**

In `tests/test_tools.py`, update `test_tool_names_match_expected`:

```python
def test_tool_names_match_expected():
    names = {t["name"] for t in TOOL_DEFINITIONS}
    assert names == {
        "profile_data", "load_skills", "clean_data",
        "design_model", "generate_pbix", "write_report",
        "classify_domain",
    }
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python -m pytest tests/test_tools.py::test_tool_names_match_expected -v
```

Expected: `FAILED` — set doesn't contain `classify_domain`

- [ ] **Step 3: Add `classify_domain` to TOOL_DEFINITIONS in `agent/tools.py`**

In the `TOOL_DEFINITIONS` list (after the `profile_data` entry), add:

```python
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
```

- [ ] **Step 4: Add `domain` to the `load_skills` tool definition**

Find the `load_skills` entry in `TOOL_DEFINITIONS` and add the `domain` property:

```python
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
```

- [ ] **Step 5: Add dispatch for `classify_domain` in `dispatch_tool`**

At the top of `agent/tools.py`, add the import:

```python
from agent.classifier import classify_domain as _classify_domain
```

In `dispatch_tool`, add the handler after the `profile_data` block:

```python
        elif name == "classify_domain":
            result = _classify_domain(inputs["profile"])
            _state["domain"] = result.get("domain", "generic")
            return {"status": "ok", "data": result, "message": f"Domain classified as: {result.get('domain')} (confidence: {result.get('confidence')})"}
```

- [ ] **Step 6: Pass `domain` through in the `load_skills` dispatch**

Find the `load_skills` dispatch block and update it:

```python
        elif name == "load_skills":
            text = load_skills(
                chart_types=inputs.get("chart_types"),
                include_design=inputs.get("include_design", False),
                domain=inputs.get("domain"),
            )
            _state["skills_text"] = text
            return {"status": "ok", "data": {"text": text}, "message": "Skills loaded."}
```

- [ ] **Step 7: Run all tool tests**

```bash
python -m pytest tests/test_tools.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 8: Commit**

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: add classify_domain tool and domain param to load_skills tool"
```

---

## Task 5: Update `agent/main_agent.py` — system prompt

**Files:**
- Modify: `agent/main_agent.py`

- [ ] **Step 1: Replace the ordered steps in SYSTEM_PROMPT**

Find the `You MUST call tools in this order:` block and replace it:

```python
SYSTEM_PROMPT = """You are an autonomous Power BI engineer. You receive a natural language command and a CSV file path.
Your job is to produce a Power BI dashboard (.pbix) and a decision report (.md).

You MUST call tools in this order:
1. profile_data — understand the data structure and column types
2. classify_domain — pass the full profile dict returned by profile_data; note the returned domain and matched_columns
3. load_skills — pass domain from classify_domain result AND viz-routing chart types you plan to use. Analyze viz-routing to pick chart types.
   If the domain skill was loaded (e.g. retail), follow its KPI hierarchy (Steps 2-4) to select which visuals to build.
   If domain is generic, use base skills only.
4. clean_data — clean based on profile and general-rules skill. Do NOT remove outliers — they may represent legitimate high-value events.
5. design_model — design visuals and DAX measures based on data profile and loaded skills.
   If retail domain: follow the retail skill's mandatory visuals (timeline, leaderboard, breakdown, profitability matrix, discount impact chart).
   Column names in visuals must exactly match the cleaned data columns.
6. load_skills with include_design=true — load the dashboard color & layout placement skill (zones, color system, typography). Apply these rules to finalize visual positions, colors, and sizes in your model_spec before generating.
7. generate_pbix — generate the .pbix file
8. write_report — write the decision report

Use the output_dir provided in the user message for all file outputs.
When calling design_model, pass a complete model_spec with: report_title, data_source_path (the cleaned data path), visuals (list of dicts), measures (list of {name, expression}).

Each visual dict MUST be a structured object (not a string) with these keys:
- type: one of lineChart, barChart, kpiCard, pieChart, tableEx, scatterPlot
- title: display title
- position: {x, y} in pixels
- width, height: in pixels
- For lineChart/scatterPlot: x_column (date/text column name), y_column (numeric column name)
- For barChart: category_column (text column name), value_column (numeric column name)
- For pieChart: category_column (text column name), value_column (numeric column name)
- For kpiCard: value_column (numeric column name)
- For tableEx: columns (list of column names to show)

Column names must exactly match column names in the data profile.
After loading the design skill in step 6, update visual positions and color assignments in the model_spec to comply with the 3-zone layout and color system before calling generate_pbix.
"""
```

- [ ] **Step 2: Verify the agent module imports cleanly**

```bash
python -c "from agent.main_agent import SYSTEM_PROMPT; print('OK', len(SYSTEM_PROMPT), 'chars')"
```

Expected: `OK <N> chars` with no errors.

- [ ] **Step 3: Commit**

```bash
git add agent/main_agent.py
git commit -m "feat: update agent system prompt to include classify_domain step"
```

---

## Task 6: Integration test — Superstore CSV

**Files:**
- Modify: `tests/test_integration.py`

- [ ] **Step 1: Read the existing integration test to understand its structure**

```bash
python -m pytest tests/test_integration.py -v --collect-only
```

Note the test names shown so you can add alongside them.

- [ ] **Step 2: Add a classifier integration test**

Add to `tests/test_integration.py`:

```python
def test_classify_domain_on_superstore(superstore_csv):
    """classify_domain should return retail for the Superstore dataset (live API call)."""
    from data.processor import profile_data
    from agent.classifier import classify_domain

    profile = profile_data(superstore_csv)
    result = classify_domain(profile)

    assert result["domain"] == "retail", (
        f"Expected retail, got {result['domain']}. Reasoning: {result['reasoning']}"
    )
    assert result["confidence"] in ("high", "medium")
    assert "revenue" in result["matched_columns"] or "profit" in result["matched_columns"]


def test_classify_domain_on_generic_csv(tmp_path):
    """classify_domain should return generic for a non-retail dataset."""
    import pandas as pd
    from data.processor import profile_data
    from agent.classifier import classify_domain

    # Create a clearly non-retail CSV
    df = pd.DataFrame({
        "employee_id": range(20),
        "department": ["Engineering"] * 10 + ["Marketing"] * 10,
        "salary": [75000.0 + i * 1000 for i in range(20)],
        "tenure_years": [float(i % 10) for i in range(20)],
        "performance_score": [3.5 + (i % 5) * 0.1 for i in range(20)],
    })
    csv_path = str(tmp_path / "employees.csv")
    df.to_csv(csv_path, index=False)

    profile = profile_data(csv_path)
    result = classify_domain(profile)

    assert result["domain"] == "generic", (
        f"Expected generic, got {result['domain']}. Reasoning: {result['reasoning']}"
    )
```

- [ ] **Step 3: Run the new integration tests (requires live API key)**

```bash
python -m pytest tests/test_integration.py::test_classify_domain_on_superstore tests/test_integration.py::test_classify_domain_on_generic_csv -v -s
```

Expected:
- `test_classify_domain_on_superstore` → `PASSED`, domain=retail
- `test_classify_domain_on_generic_csv` → `PASSED`, domain=generic

If `test_classify_domain_on_superstore` fails, check:
1. `ANTHROPIC_API_KEY` is set in `.env`
2. The Superstore CSV path in the `superstore_csv` fixture matches the actual file location

- [ ] **Step 4: Run full test suite**

```bash
python -m pytest tests/ -v --ignore=tests/test_integration.py
python -m pytest tests/test_integration.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: integration tests for classify_domain on retail and generic datasets"
```

---

## Task 7: End-to-end smoke test

No new files — manual verification step.

- [ ] **Step 1: Run the agent against the Superstore CSV**

```bash
python main.py "Build dashboard" "C:\Users\leonc\Desktop\archive\Sample - Superstore.csv"
```

- [ ] **Step 2: Verify domain classification fired**

The console output should show the agent calling `classify_domain`. Check that the
reviewer feedback mentions subcategory, discount, or customer visuals — signals that
the retail skill influenced the design.

- [ ] **Step 3: Open the generated `.pbix` in Power BI Desktop**

Verify:
- Dashboard has more analytical depth than before (subcategory breakdown, profitability visuals, customer leaderboard, YoY trend)
- No outlier rows were dropped (reviewer notes should not mention dropped rows)
- All visuals load without `Missing_References` errors

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat: domain classifier + retail skill system complete"
```
