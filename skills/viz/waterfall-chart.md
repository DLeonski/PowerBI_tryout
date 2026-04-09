# Skill: Waterfall Chart Design

**Load this file when:** `viz-routing.md` selected a Waterfall Chart.

---

## Primary Use Case

A waterfall chart answers: *"Why did this KPI go from A to B?"*

Canonical scenarios: Gross profit → Net profit, Opening headcount → Closing headcount, Budget variance decomposition.

---

## Structural Components

| Element type | Visual appearance | Meaning |
|-------------|------------------|---------|
| **Start pillar** | Full-height bar, anchored at zero | Baseline value |
| **Floating bars** | Bars that float between previous and new total | Individual contributions |
| **End pillar** | Full-height bar, anchored at zero | Final total |

---

## IBCS Color Semantics (Mandatory)

| Element | Color |
|---------|-------|
| Start pillar | **Gray** |
| End pillar | **Gray** |
| Positive contribution | **Green** |
| Negative contribution | **Red** |
| Subtotal pillars | **Gray** or **Blue** |

---

## Sorting

Default order is the **logical business process sequence** — not sorted by magnitude.

---

## Power BI model_spec fields

| Visual field slot | Map to |
|------------------|--------|
| type | `"waterfallChart"` |
| category | Labels for each bridge segment |
| value | Numeric measure (positive = increase, negative = decrease) |
| title | Descriptive chart title |
