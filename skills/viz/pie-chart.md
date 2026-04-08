# Pie Chart Design

## When to use
Part-to-whole with <=5 categories. Use bar chart if >5.

## Configuration
- Show percentage labels outside slices.
- Legend: right side.
- No 3D effects.

## model_spec fields
```json
{"type": "pieChart", "category": "<categorical_col>", "value": "<numeric_col>"}
```
