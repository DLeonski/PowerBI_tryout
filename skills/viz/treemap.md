# Skill: Treemap Design

**Load this file when:** `viz-routing.md` selected a Treemap.

---

## Primary Use Case

Treemaps answer: *"Which entities dominate this structure, and how do the sub-categories nest within them?"*

Use when there are many hierarchical categories too numerous for a readable bar chart, and the goal is to identify dominant segments at a glance.

---

## Hierarchy Design

- Use **one level of hierarchy** for straightforward analysis.
- Use **two levels** when both parent and child segments matter simultaneously.
- Avoid three or more levels — they become unreadable.

---

## Color Semantics

| Color approach | When to use |
|---------------|------------|
| **Single-hue saturation scale** | Color encodes magnitude (darker = higher value) |
| **Categorical color per parent group** | Color identifies top-level group |
| **Diverging scale (red → green)** | Color encodes deviation from target |

> **Rule:** Never use random or decorative colors. Every color must carry a defined meaning.

---

## Power BI model_spec fields

| Visual field slot | Map to |
|------------------|--------|
| type | `"treemap"` |
| category | Primary dimension (parent level) |
| value | Numeric measure determining tile size |
| title | Descriptive chart title |
