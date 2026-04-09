# Design: Domain Classifier + Domain Skill System

**Date:** 2026-04-09
**Status:** Approved

---

## Problem

The agent currently produces generic dashboards regardless of the dataset type. It picks
basic metrics (SUM, AVERAGE) and misses domain-specific analytical angles — subcategory
profitability, discount impact, customer leaderboards, YoY trends, etc. A retail dataset
gets the same treatment as any other CSV.

Additionally, the blanket outlier removal rule (3×IQR) was incorrectly dropping legitimate
business events (high-value orders, bulk purchases). This has been fixed separately by
removing the rule from `skills/base/general-rules.md`.

---

## Goal

1. Add a `classify_domain` tool that fires once after `profile_data`, identifies the dataset
   domain (retail, generic), and returns structured output the agent uses to load the right
   domain skill.
2. Add a domain skill system (`skills/domains/`) starting with `retail.md`.
3. Wire the domain skill into `load_skills` so the agent receives domain-specific KPI
   hierarchy, analytical angles, cardinality guardrails, and DAX templates before designing
   the model spec.

---

## Scope

- **In scope:** retail domain + generic fallback, classifier infrastructure, loader update,
  agent prompt update.
- **Out of scope:** CRM, finance, HR domain skills — architecture supports them as future
  additions; stubs are not needed now.

---

## Architecture

### Updated Agent Flow

```
1. profile_data          — unchanged; returns column profile
2. classify_domain       — NEW; LLM sub-call; returns {domain, confidence, reasoning, matched_columns}
3. load_skills           — gains domain parameter; loads base + domain skill + viz-routing
4. clean_data            — unchanged
5. design_model          — unchanged; agent now has domain KPI hierarchy in context
6. load_skills(design)   — unchanged; loads layout/color skill
7. generate_pbix         — unchanged
8. write_report          — unchanged
```

### classify_domain Tool

**Location:** `agent/classifier.py`

**Trigger:** Called by agent after `profile_data` returns, before any `load_skills` call.

**Implementation:**
- Makes a focused Claude API call (claude-haiku-4-5 for cost efficiency).
- System prompt lists known domains with their trigger signatures.
- Input: the full profile dict from `profile_data`.
- Output: structured JSON parsed from the response.

**Output schema:**
```json
{
  "domain": "retail",
  "confidence": "high",
  "reasoning": "Columns Sales, Profit, Quantity, Discount, Order Date, Category, Sub-Category match retail transactional pattern",
  "matched_columns": {
    "revenue": "Sales",
    "profit": "Profit",
    "quantity": "Quantity",
    "discount": "Discount",
    "transaction_date": "Order Date",
    "category": "Category",
    "sub_category": "Sub-Category"
  }
}
```

**Fallback:** If domain is `"generic"` or confidence is `"low"`, no domain skill is loaded.
The agent proceeds with base skills only (existing behavior).

**Known domains the classifier distinguishes:**
- `retail` — transactional sales data: revenue, profit/margin, products, customers, orders, dates
- `generic` — everything else

### Domain Skill Files

```
skills/
  base/
    general-rules.md     — unchanged (outlier rule already removed)
    dashboard-design.md  — unchanged
  viz/                   — unchanged
  domains/               — NEW directory
    retail.md            — the comprehensive retail KPI skill (provided by user)
    generic.md           — minimal: instructs agent to use base skills only
```

`retail.md` is the skill document already authored. It covers:
- Column profiling & semantic attribution (Step 1)
- North Star metric selection (Step 2)
- KPI hierarchy — 7 levels, conditional on columns present (Step 3)
- Mandatory baseline visuals with triggers (Step 4)
- Cardinality guardrails (Step 5)
- DAX measure templates (Step 6)
- Dashboard layout template (Step 7)
- Rejection log (Step 8)

### load_skills Update

`skills/loader.py` gains a `domain` parameter:

```python
def load_skills(chart_types=None, include_design=False, domain=None):
    ...
    if domain and domain != "generic":
        domain_path = BASE / "domains" / f"{domain}.md"
        if domain_path.exists():
            parts.append(domain_path.read_text())
    ...
```

`agent/tools.py` TOOL_DEFINITIONS for `load_skills` gains a `domain` field:
```json
{
  "domain": {
    "type": "string",
    "description": "Domain skill to load alongside base skills. Pass the domain returned by classify_domain (e.g. 'retail'). Omit or pass 'generic' to skip domain skill."
  }
}
```

### Tool Definition for classify_domain

Added to `TOOL_DEFINITIONS` in `agent/tools.py`:
```json
{
  "name": "classify_domain",
  "description": "Classify the dataset domain (retail, generic) using a focused LLM call. Call this once after profile_data, before load_skills. Returns {domain, confidence, reasoning, matched_columns}.",
  "input_schema": {
    "type": "object",
    "properties": {
      "profile": {
        "type": "object",
        "description": "The full profile dict returned by profile_data."
      }
    },
    "required": ["profile"]
  }
}
```

Dispatched via `dispatch_tool` in `agent/tools.py` → calls `classifier.classify_domain(profile)`.

### Agent System Prompt Update

Step 2 in the ordered instructions becomes:

```
2. classify_domain — pass the full profile dict; note the returned domain.
3. load_skills — pass domain from classify_domain result alongside chart_types.
   Always load viz-routing at this step.
```

---

## Files Changed

| File | Change |
|---|---|
| `agent/classifier.py` | NEW — `classify_domain(profile) -> dict` |
| `agent/tools.py` | Add `classify_domain` tool definition + dispatch; add `domain` param to `load_skills` definition |
| `agent/main_agent.py` | Update SYSTEM_PROMPT steps 2-3 |
| `skills/loader.py` | Add `domain` parameter |
| `skills/domains/retail.md` | NEW — retail KPI skill |
| `skills/domains/generic.md` | NEW — generic fallback (minimal) |

---

## What Does NOT Change

- `pbix/` — all generation code untouched
- `data/processor.py` — untouched
- Layout/placement logic — untouched
- Reviewer agent — untouched
- All existing tests pass as-is (classify_domain is additive)

---

## Testing

- Unit test `classifier.classify_domain()` with a Superstore-like profile → expect `domain=retail`
- Unit test with a random non-retail profile → expect `domain=generic`
- Integration: run full agent on Superstore CSV, verify retail skill is loaded, verify
  subcategory/discount/customer visuals appear in model spec
