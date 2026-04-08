# KPI Card Design

## When to use
Single summary statistic — always include at least one.

## Configuration
- Show: measure value (large font, 28px), label below (12px).
- Background: white card with subtle shadow.
- Value format: auto (K/M suffix for large numbers, 2 decimals for small).
- Size: 200x120px.

## model_spec fields
```json
{
  "type": "kpiCard",
  "title": "<human readable label>",
  "measure": "<DAX measure name>"
}
```
