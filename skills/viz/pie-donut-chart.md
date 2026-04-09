# Skill: Pie & Donut Chart Design

**Load this file when:** `viz-routing.md` selected a Pie or Donut Chart (cardinality ≤ 5 confirmed).

---

## Cardinality Enforcement

| Unique values in dimension | Action |
|---------------------------|--------|
| 1–5 | Proceed with Pie / Donut |
| 6+ | **Block.** Convert to a sorted horizontal Bar Chart. Inform the user. |

---

## Pie vs. Donut Choice

| Variant | When to prefer |
|---------|---------------|
| **Pie** | Simple, single-level part-to-whole |
| **Donut** | You want to place a central KPI figure in the center ring |

---

## Sorting & Labels

- Sort slices from largest to smallest, starting at 12 o'clock, going clockwise.
- Always show percentage labels directly on slices.
- If a slice is < 5% of the total, group it into "Other".
- Do not use exploded slices.

---

## Color

- Use categorically distinct colors (not a sequential scale).
- Maximum of 5 distinct colors — matches the 5-category limit.

---

## Power BI model_spec fields

| Visual field slot | Map to |
|------------------|--------|
| type | `"pieChart"` |
| category | Categorical dimension (≤ 5 values) |
| value | Numeric measure |
| title | Descriptive chart title |
