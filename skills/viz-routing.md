# Visualization Routing

Given the data profile, select chart types as follows:

## Rules (apply in order, pick best match)

| Data pattern | Recommended chart | Notes |
|---|---|---|
| date column + 1 numeric column | `line-chart` | Time series |
| date column + 1 numeric + 1 categorical | `line-chart` (series per category) | Multi-series |
| 1 categorical + 1 numeric, <=8 categories | `bar-chart` | Compare values |
| 1 categorical + 1 numeric, >8 categories | `table` | Too many bars |
| 2 numeric columns | `scatter-plot` | Correlation |
| Single KPI summary (SUM or AVERAGE of 1 numeric) | `kpi-card` | Always add 1-2 KPI cards |
| categorical breakdown with <=5 categories | `pie-chart` | Use sparingly |
| multiple columns, no clear pattern | `table` | Fallback |

## Always include
- At least 1 `kpi-card` showing the primary numeric measure.
- A `table` as a details view if the dataset has more than 3 columns.

## Example
Data: Date, Region, Revenue -> use: line-chart (Revenue over Date) + bar-chart (Revenue by Region) + kpi-card (Total Revenue)
