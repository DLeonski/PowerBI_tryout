# Skill: Column & Bar Chart Design

**Load this file when:** `viz-routing.md` selected a Column Chart (vertical) or Bar Chart (horizontal).

---

## Orientation Rule

| Axis content | Required orientation |
|-------------|---------------------|
| Time dimension (Year, Quarter, Month, Week) | **Vertical columns** — temporal flow reads left-to-right |
| Categorical attributes (names, products, clients) | **Horizontal bars** — allows full label readability |
| Any label that would require rotation > 0° | **Force horizontal bars** |

---

## Zero-Baseline Rule (Non-Negotiable)

**Always start the value axis at zero.**

Truncating the axis floor visually transforms a 3% difference into an apparent 300% difference — this is a critical perceptual distortion. There are no exceptions for column/bar charts.

---

## Variant Selection: Clustered vs. Stacked vs. 100% Stacked

| User need | Variant |
|-----------|---------|
| Precise comparison of individual components across categories | **Clustered** — positions components side-by-side for direct length comparison |
| Show total aggregate value per category; components are secondary | **Stacked** — components accumulate into a single bar showing the whole |
| Show relative proportion only; absolute volume is irrelevant | **100% Stacked** — normalizes all bars to the same height |

> **Rule:** Never use Stacked when the user needs to compare middle layers across categories — those segments lack a shared baseline, making comparison impossible.

---

## Color & Visual Hierarchy

- Use a single neutral color (e.g., steel blue) for all bars when no semantic distinction is needed.
- Apply a **highlight color only on the selected / most important bar**, keeping all others muted.
- Avoid gradients — solid fills only.
- Grid lines: horizontal only (value axis), light gray, no vertical grid lines.
- Remove all chart borders and background fills.

---

## Labels

- Show data labels **only** on the most significant bars (e.g., top 3, or the period in focus) — not on all bars.
- Place labels inside the bar end (column charts) or outside the bar end (bar charts) for readability.
- Do not show both a data label and a visible axis — choose one source of precision.

---

## Sorting

- **Categorical axis:** Sort bars by value descending (largest → smallest) unless the category has a natural order.
- **Time axis:** Always sort chronologically ascending (oldest → newest).

---

## Power BI model_spec fields

| Visual field slot | Map to |
|------------------|--------|
| type | `"barChart"` (horizontal) or `"columnChart"` (vertical) |
| category | Time dimension or categorical attribute |
| value | Primary numeric measure |
| title | Descriptive chart title |
