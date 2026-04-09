# Skill: Funnel Chart Design

**Load this file when:** `viz-routing.md` selected a Funnel Chart.

---

## Primary Use Case

A funnel chart visualizes **volume drop-off across sequential, ordered stages** of a linear process. It answers: *"Where are we losing the most volume, and how severe is the drop at each stage?"*

---

## Stage Design Rules

- Stages must be **mutually exclusive and sequentially ordered**.
- Typically 3–8 stages. Below 3 is too simple. Above 8 creates visual compression.

---

## Metrics to Display Per Stage

| Metric | Position |
|--------|---------|
| Stage name | Left label or inside the bar |
| Absolute volume | Inside the segment |
| Conversion rate from previous stage (%) | Right-side annotation or tooltip |

---

## Color

- Use a **single-hue gradient** (darker at top/larger stages, lighter at smaller).
- Optionally apply a **threshold color**: highlight stages where drop-off exceeds a threshold in amber or red.

---

## Sorting

Stages are **always sorted by process order** — never by volume.

---

## Power BI model_spec fields

| Visual field slot | Map to |
|------------------|--------|
| type | `"funnel"` |
| category | Stage name dimension (ordered) |
| value | Volume measure |
| title | Descriptive chart title |
