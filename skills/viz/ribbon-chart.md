# Skill: Ribbon Chart Design

**Load this file when:** `viz-routing.md` selected a Ribbon Chart.

---

## Primary Use Case

A ribbon chart answers: *"How has the ranking or relative position of each category shifted across periods?"*

---

## Design Rules

### Number of Categories
- Optimal: **5–10 categories**. More than 10 creates visual tangle — filter to Top N.

### Color
- Assign each category a **unique, consistent color** across all time periods.
- Use a colorblind-safe categorical palette.

### Labels
- Label each ribbon at its **rightmost column** (most recent period) with the category name.

---

## Power BI model_spec fields

| Visual field slot | Map to |
|------------------|--------|
| type | `"ribbonChart"` |
| x_axis | Time dimension (period) |
| category | Categorical dimension being ranked |
| value | Numeric measure determining ribbon height |
| title | Descriptive chart title |
