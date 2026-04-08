# General Data Rules

## Anomaly Handling
- Remove outliers defined as values beyond 3x IQR from Q1/Q3.
- Fill numeric nulls with column mean unless the column is an ID or date.
- Drop rows where date column is null.
- Log every cleaning decision with count and reason.

## Naming
- Column names in DAX measures must match the cleaned CSV column names exactly.
- Use snake_case for measure names in the model spec.

## DAX Measures to always include
- For any numeric column: SUM, AVERAGE
- If date column present: add a "by month" aggregation
