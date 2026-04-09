# Skill: Combo Chart Design (Line + Column)

**Load this file when:** `viz-routing.md` selected a Combo Chart.

---

## Primary Purpose

A combo chart is justified **only** when you need to overlay two measures that belong to fundamentally different unit classes or orders of magnitude on the same time axis. The canonical case:

- **Columns (left axis):** Absolute measure — e.g., Revenue, Units Sold
- **Line (right axis):** Relative/ratio measure — e.g., Gross Margin %, YoY Growth %

---

## The One Anti-Pattern That Must Be Blocked

**Do not combine two measures of the same unit class on a combo chart.**

If both measures are absolute currency values, use a **Clustered Column Chart** instead.

---

## Axis Design Rules

| Axis | Content | Scale behavior |
|------|---------|----------------|
| Left Y-axis (primary) | Absolute measure (column series) | Must start at zero |
| Right Y-axis (secondary) | Relative/ratio measure (line series) | May be scaled to range; label with unit (%) |
| X-axis | Time dimension | Chronological, ascending |

---

## Color & Series Identification

- Column series: neutral fill (gray or brand primary).
- Line series: high-contrast accent color so it separates from the columns.
- Include a legend that labels both series with their units.

---

## Power BI model_spec fields

| Visual field slot | Map to |
|------------------|--------|
| type | `"comboChart"` |
| x_axis | Time dimension |
| column_value | Absolute measure |
| line_value | Relative/ratio measure |
| title | Descriptive chart title |
