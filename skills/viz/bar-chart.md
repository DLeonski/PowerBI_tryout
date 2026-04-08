# Bar Chart Design

## When to use
Compare a numeric measure across categories (<=8 unique values).

## Configuration
- Orientation: vertical (column chart) by default.
- X axis: categorical column, sorted descending by value.
- Y axis: numeric, no decimals for large numbers (use K/M suffix).
- Color: single accent color (#0078D4), no gradient.
- Data labels: inside end of bar.

## model_spec fields
```json
{
  "type": "barChart",
  "category": "<categorical_column_name>",
  "value": "<numeric_column_name>"
}
```
