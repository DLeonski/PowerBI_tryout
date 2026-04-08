# Line Chart Design

## When to use
Time series: x-axis is a date/time column, y-axis is a continuous numeric.

## Configuration
- X axis: date column, format "MMM YYYY" for monthly, "DD MMM" for daily.
- Y axis: numeric column, show gridlines, start at 0 unless data variance is small.
- Line: solid, 2px stroke, accent color (#0078D4).
- Show data labels only on last point.
- Legend: bottom, only if multi-series.

## model_spec fields
```json
{
  "type": "lineChart",
  "x_axis": "<date_column_name>",
  "y_axis": "<numeric_column_name>",
  "series": null
}
```

## Avoid
- Do not use line chart for categorical x-axis.
- Do not use more than 5 series on a single chart.
