# Skill: Scatter & Bubble Chart Design

**Load this file when:** `viz-routing.md` selected a Scatter Chart or Bubble Chart.

---

## Primary Use Case

Scatter and bubble charts reveal **statistical relationships between two (or three) numeric measures** at the individual record level.

---

## Scatter vs. Bubble

| Chart | Data mapped | Third dimension |
|-------|------------|----------------|
| **Scatter** | X measure + Y measure + category label | None |
| **Bubble** | X measure + Y measure + category label | **Size** = third numeric measure |

Add a Bubble only when the third measure meaningfully changes interpretation.

---

## Minimum Data Density Rule

**Do not deploy on fewer than ~1,000 distinct data points.** With sparse data, a table or bar chart is more useful.

---

## Axis Design

- Both axes must have **descriptive labels** including measure name and unit.
- Add **reference lines** (average lines, quadrant dividers) to frame interpretation.

---

## Labels & Annotations

- Do **not** label every data point on 1,000+ points.
- Label only **outliers** and **named key entities**.

---

## Power BI model_spec fields

| Visual field slot | Map to |
|------------------|--------|
| type | `"scatterChart"` |
| x_axis | First numeric measure |
| y_axis | Second numeric measure |
| category | Entity dimension |
| title | Descriptive chart title |
