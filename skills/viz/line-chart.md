# Skill: Line Chart & Area Chart Design

**Load this file when:** `viz-routing.md` selected a Line Chart or an Area Chart.

---

## When to Use Line vs. Area

| Intent | Chart type |
|--------|-----------|
| Track the level or rate of a measure over time | **Line Chart** |
| Emphasize cumulative volume or the magnitude of a base growing over time | **Area Chart** |
| Compare two or more time-series trends at the same scale | **Line Chart** (multiple lines) — never multiple overlapping area fills |

> **Rule:** Never use an Area Chart when comparing two or more series — overlapping fills create ambiguity. Use Lines instead.

---

## Zero-Baseline Exception (Authorized)

Unlike column charts, you **may** truncate the Y-axis floor for line charts when the fluctuations are small relative to the absolute value and the purpose is micro-trend detection.

**When truncating:** Add a visible note so the reader knows the axis does not start at zero.

---

## Spaghetti Anti-Pattern (Critical)

**Never place a dimension with > 5 distinct values in the Legend field.**

More than 5 lines on a single chart creates an unreadable tangle. Use **Small Multiples** or reduce to Top N categories.

---

## Markers & Data Labels

- Apply markers **only at key nodes:** series endpoints, minimum, maximum, inflection points.
- Do not place a marker on every data point.
- Data labels: endpoint labels only.

---

## Color

- Use **dashed line style** for forecast, plan, or target series to distinguish from actuals.

---

## Power BI model_spec fields

| Visual field slot | Map to |
|------------------|--------|
| type | `"lineChart"` |
| x_axis | Date/time dimension |
| y_axis | Primary numeric measure |
| title | Descriptive chart title |
