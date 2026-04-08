# Scatter Plot Design

## When to use
Correlation between two numeric columns.

## Configuration
- X axis: first numeric, Y axis: second numeric.
- Point size: 6px, opacity: 0.7.
- Add trend line if correlation coefficient > 0.5.

## model_spec fields
```json
{"type": "scatterPlot", "x_axis": "<numeric_col>", "y_axis": "<numeric_col>"}
```
