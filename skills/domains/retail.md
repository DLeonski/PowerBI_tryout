---
name: retail-pbix-agent
description: >
  Use this skill whenever the agent is building a Power BI (.pbix) file or dashboard from
  retail, e-commerce, or transactional sales data regardless of the specific schema or
  column names used. Trigger on any dataset that contains transactional records linking
  customers, products, and sales amounts: e.g. POS exports, order history, shop analytics,
  marketplace exports (Shopify, WooCommerce, Amazon, ERP), or any CSV where the data clearly
  represents sales transactions. Also trigger when the user says "retail dashboard", "sales
  performance", "product analytics", "customer revenue", "store report", "order analysis",
  or asks to build a pbix from transactional data. The skill applies regardless of whether
  column names exactly match canonical names — it uses semantic inference to identify the
  equivalent columns in any schema.
---

# Retail PBIX Agent Skill

## Purpose
This skill makes the agent behave like a senior retail analyst when generating Power BI
dashboards from any transactional sales dataset. It is schema-agnostic: column names will
vary across data sources, but the underlying business concepts are universal. The skill
defines how to: infer column semantics from name patterns, apply retail KPI logic, select
mandatory vs. optional visuals, and structure a coherent dashboard.

---

## Step 1 — Column Profiling & Semantic Attribution

**Always run a profiling pass first.** For every column collect: dtype, cardinality
(unique value count), null %, sample values, and min/max for numerics.
Then classify each column into a semantic type using the rules below.

### 1.1 Semantic Type Inference (pattern-matching on column names)

Retail datasets use many naming conventions. Map incoming columns to canonical semantic
types by matching name patterns. First match wins; go in order.

| Semantic type | Name patterns to match (case-insensitive) | Treatment |
|---|---|---|
| **Transaction ID** | `*order*id*`, `*transaction*id*`, `*invoice*`, `*receipt*`, `*sale*id*` | COUNT DISTINCT only. Never SUM. |
| **Line Item ID** | `*row*id*`, `*line*id*`, `*item*id*` | Surrogate — suppress from visuals. |
| **Transaction Date** | `*order*date*`, `*sale*date*`, `*purchase*date*`, `*transaction*date*`, `*date*` | Parse as date. Extract Year/Month/Quarter/Week. |
| **Ship / Fulfillment Date** | `*ship*date*`, `*dispatch*date*`, `*delivery*date*`, `*fulfilled*` | Use for shipping lag calculation. |
| **Customer ID** | `*customer*id*`, `*client*id*`, `*buyer*id*`, `*user*id*`, `*account*id*` | COUNT DISTINCT for unique customers. Never SUM. Top N ranking anchor. |
| **Customer Name** | `*customer*name*`, `*client*name*`, `*buyer*name*` | Top N leaderboard. High cardinality — use only filtered. |
| **Product ID** | `*product*id*`, `*item*id*`, `*sku*`, `*barcode*`, `*upc*` | COUNT DISTINCT. Top N anchor. Never SUM. |
| **Product Name** | `*product*name*`, `*item*name*`, `*product*desc*`, `*description*` | Top N leaderboard. High cardinality — use only filtered (Top 10/20). |
| **Category** | `*category*`, `*department*`, `*type*`, `*product*group*` | Breakdown visual. Check cardinality to determine chart type. |
| **Sub-Category** | `*sub*category*`, `*sub*department*`, `*subcategory*`, `*product*family*`, `*product*line*` | Breakdown visual. Cardinality usually 10–25. |
| **Customer Segment** | `*segment*`, `*customer*type*`, `*tier*`, `*channel*`, `*market*` | Segment comparison visual. |
| **Geography — coarse** | `*region*`, `*zone*`, `*territory*`, `*area*` | Bar chart breakdown. |
| **Geography — medium** | `*state*`, `*province*`, `*county*`, `*prefecture*` | Map or filtered bar. |
| **Geography — fine** | `*city*`, `*town*`, `*store*location*` | Map only if cardinality > 50. |
| **Postal / Zip** | `*postal*`, `*zip*`, `*postcode*` | Map geo-binding only. Never aggregate. |
| **Country** | `*country*` | If cardinality = 1: suppress entirely. If > 1: breakdown bar. |
| **Fulfillment Method** | `*ship*mode*`, `*delivery*method*`, `*fulfillment*`, `*shipping*type*` | Bar breakdown. |
| **Revenue / Sales** | `*sales*`, `*revenue*`, `*amount*`, `*gmv*`, `*net*sales*`, `*gross*sales*`, `*turnover*` | **Primary revenue metric.** SUM. North Star candidate. |
| **Profit / Margin (absolute)** | `*profit*`, `*margin*`, `*net*income*`, `*contribution*`, `*gross*profit*` | **North Star metric.** SUM + compute as % of Revenue. |
| **Cost** | `*cost*`, `*cogs*`, `*cost*of*goods*`, `*unit*cost*` | If Profit absent: derive Profit = Revenue — Cost. |
| **Quantity / Units** | `*quantity*`, `*qty*`, `*units*`, `*items*sold*`, `*pieces*` | SUM. Volume metric. Avg units per order = Qty / Order Count. |
| **Discount** | `*discount*`, `*markdown*`, `*promo*amount*`, `*rebate*` | **Margin risk metric.** Always bucket and analyze impact. |
| **Price** | `*price*`, `*unit*price*`, `*selling*price*`, `*list*price*` | If Revenue absent: derive Revenue = Price × Quantity. |
| **Return / Refund flag** | `*return*`, `*refund*`, `*cancelled*`, `*chargeback*` | Return Rate KPI. Filter from revenue if flagged. |

### 1.2 Fallback — dtype + cardinality inference

If no name pattern matches, apply these rules:

| Condition | Inferred semantic type |
|---|---|
| dtype = date/datetime | Temporal dimension |
| dtype = float/int, no ID/Code suffix, cardinality > 20 | Likely metric — candidate for SUM |
| dtype = int, cardinality < 20 | Likely categorical code — treat as dimension |
| dtype = string, cardinality ≤ 10 | Low-cardinality dimension — breakdown visual |
| dtype = string, cardinality 11–50 | Medium-cardinality dimension — bar chart with care |
| dtype = string, cardinality > 50 | High-cardinality dimension — Top N only |
| dtype = string, cardinality = total rows | Surrogate / free text — suppress from visuals |

### 1.3 Derive missing metrics if possible

| If column is absent | Derivation rule |
|---|---|
| Profit | If Cost present: `Profit = Revenue — Cost` |
| Revenue | If Price + Quantity present: `Revenue = Price × Quantity` |
| Profit Margin % | Always derive: `Margin % = Profit / Revenue` |
| AOV | Always derive: `AOV = Revenue / COUNT DISTINCT(Transaction ID)` |
| Shipping Lag (days) | If Order Date + Ship Date both present: `Lag = Ship Date — Order Date` |

---

## Step 2 — North Star Selection

Before building any visual, identify the **North Star metric** — the single KPI the
dashboard centers around. Apply this decision logic in order:

1. **Profit or Margin column exists** — North Star = `Profit Margin %` (Profit / Revenue).
   Profit is more actionable than Revenue alone in retail.
2. **Only Revenue/Sales exists (no Profit/Cost)** — North Star = `Total Revenue`,
   secondary focus on `Revenue Growth %` if time dimension is present.
3. **Returns/refund-focused dataset** — North Star = `Return Rate %`
4. **Traffic/conversion dataset** (sessions, views, conversion rate present) —
   North Star = `Conversion Rate` or `Revenue per Session`

Once selected, all other metrics are explanatory layers beneath the North Star.
State the chosen North Star in the Rejection Log (Step 8).

---

## Step 3 — KPI Hierarchy

Structure the dashboard in this priority order. Each level is conditional on relevant
columns being present.

```
LEVEL 1 — Headline KPIs  [always include if data supports]
  ├── Total Revenue           (SUM of revenue metric)
  ├── Total Profit            (SUM of profit metric, or Revenue — Cost)
  ├── Profit Margin %         ← NORTH STAR if profit present
  ├── Transaction Count       (COUNT DISTINCT of transaction ID)
  └── AOV                     (Revenue / Transaction Count)

LEVEL 2 — Product & Category Profitability  [if product/category + margin present]
  ├── Margin % by Category    (sort ascending — loss-makers surface at top)
  ├── Margin % by Sub-Category
  └── Top N / Bottom N products by Profit  (not Revenue — they often diverge)

LEVEL 3 — Discount & Pricing Impact  [if discount/markdown column present]
  ├── Margin % by Discount Tier  (bucketed: 0% / 1–20% / 21–40% / 40%+)
  └── % Transactions at Negative Margin  → alert KPI, always surface

LEVEL 4 — Customer Analysis  [if customer ID/name present]
  ├── Top N Customers by Revenue
  ├── Unique Customer Count
  └── Revenue per Customer (avg)

LEVEL 5 — Segment Comparison  [if segment/channel/tier column present]
  ├── Revenue by Segment
  ├── Margin % by Segment
  └── AOV by Segment

LEVEL 6 — Time Trend  [if date column with ≥ 7 distinct periods]
  ├── Revenue over time (line chart, monthly default)
  └── Margin % over time (secondary axis or separate)

LEVEL 7 — Geography  [if region/state/city present]
  ├── Revenue by Region (bar — always)
  └── Revenue by State/City (map — only if geocoding confirmed)
```

---

## Step 4 — Mandatory Baseline Visuals

These are **non-negotiable** when triggered. Apply to whichever columns map to each semantic type.

### 4.1 The Timeline
- **Trigger**: Any temporal dimension with ≥ 7 distinct periods AND any revenue/profit metric
- **Visual**: Line chart — Revenue trend with Margin % as secondary axis
- **Granularity**: ≥ 24 months → monthly. 7–23 months → weekly. < 7 months → daily
- **Principle**: Revenue alone misleads. Pair with Margin % to show whether growth is profitable.

### 4.2 The Leaderboard (always two — Revenue AND Profit)
- **Trigger**: Any high-cardinality entity (product, customer, SKU) + any metric
- **Visual**: Two horizontal bar charts — Top 10 by Revenue AND Top 10 by Profit/Margin
- **Principle**: These two lists almost always disagree in retail. Show both — never just one.
- **Gate**: Only build if entity has > 10 unique values (otherwise use a simple breakdown bar)

### 4.3 The Breakdown
- **Trigger**: Any low-cardinality categorical (≤ 15 unique values) + metric
- **Visual**: Horizontal bar chart. Donut only if ≤ 5 values and user requests it.
- **Principle**: Show Revenue AND Margin % for each category. Revenue-only breakdowns hide loss-makers.
- **Variance gate**: Only build if the metric varies meaningfully across categories.
  Skip if all values are within 5% of each other — that visual adds no information.

### 4.4 The Profitability Matrix
- **Trigger**: Two categorical dimensions present (e.g. Category + Sub-Category, Department + Product Line)
- **Visual**: Matrix table with conditional formatting — green = positive margin, red = negative
- **Principle**: Surfaces the exact dimension intersection where value is being destroyed.
  Often the most operationally useful visual in the entire dashboard.

### 4.5 The Discount Impact Chart
- **Trigger**: Any discount/markdown/promo column with variance > 0
- **Visual**: Clustered bar — Margin % by discount bucket (0% / 1–20% / 21–40% / 40%+)
- **Principle**: Heavy discounting is the most common hidden margin killer in retail.
  This chart is almost always the most surprising visual. Never skip it.

---

## Step 5 — Cardinality Guardrails

Apply universally, regardless of column name:

| Unique value count | Allowed chart types | Blocked |
|---|---|---|
| 1 | Suppress entirely — zero variance, zero insight | All |
| 2–5 | Bar, donut, pie, 100% stacked | None |
| 6–15 | Bar chart, matrix | Pie, donut |
| 16–50 | Horizontal bar (Top N, max 20), matrix | Pie, donut, full vertical bar |
| 51–200 | Top N table (max 20 rows), map if geographic | All charts showing all values |
| > 200 | Map (if geographic), Top N table only | All charts showing all values |
| = row count | Surrogate/free text — suppress entirely | All |

**Hard rules:**
- Never pie/donut for > 5 unique values
- Never bar chart showing all values if cardinality > 50
- Never SUM or AVG any column classified as ID/key type
- Never show a geographic column as a bar chart if cardinality > 30 (use map)
- Suppress any single-value column entirely

---

## Step 6 — Calculated Measures (DAX templates)

Substitute actual column names discovered in Step 1 for the placeholders below.

```
-- Always generate:
[Total Revenue]            = SUM(Table[<revenue_col>])
[Total Profit]             = SUM(Table[<profit_col>])        -- or Revenue — Cost
[Profit Margin %]          = DIVIDE([Total Profit], [Total Revenue], 0)
[Transaction Count]        = DISTINCTCOUNT(Table[<txn_id_col>])
[AOV]                      = DIVIDE([Total Revenue], [Transaction Count], 0)

-- Generate if present:
[Unique Customers]         = DISTINCTCOUNT(Table[<customer_id_col>])
[Units Sold]               = SUM(Table[<quantity_col>])
[Avg Discount]             = AVERAGE(Table[<discount_col>])
[Loss-Making Transactions] = COUNTROWS(FILTER(Table, Table[<profit_col>] < 0))
[% Loss Transactions]      = DIVIDE([Loss-Making Transactions], [Transaction Count], 0)

-- Generate if date table established:
[Revenue MoM Δ]            = [Total Revenue] - CALCULATE([Total Revenue], DATEADD(Dates[Date], -1, MONTH))
[Revenue YoY %]            = DIVIDE(
                               [Total Revenue] - CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(Dates[Date])),
                               CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(Dates[Date])), 0)

-- Generate if Cost present but no Profit column:
[Derived Profit]           = [Total Revenue] - SUM(Table[<cost_col>])
[Derived Margin %]         = DIVIDE([Derived Profit], [Total Revenue], 0)
```

---

## Step 7 — Dashboard Layout Template

Slots marked `[conditional]` appear only if the relevant columns were found in Step 1.

```
┌──────────────────────────────────────────────────────────────────┐
│  KPI CARDS: Revenue ▪ Profit ▪ Margin % ▪ AOV ▪ Transaction Count │
├────────────────────────────────┬─────────────────────────────────┤
│  Revenue + Margin % Trend      │  [conditional] Discount Impact   │
│  (line chart)                  │  Margin % by Discount Tier (bar) │
├────────────────────────────────┼─────────────────────────────────┤
│  [conditional] Profitability   │  Top 10 by Profit (horiz. bar)   │
│  Matrix (Cat × Sub-Cat)        │  Bottom 5 by Margin % (alert)    │
├────────────────────────────────┼─────────────────────────────────┤
│  [conditional] Segment         │  [conditional] Top 10 Customers  │
│  Revenue + Margin + AOV        │  by Revenue (horiz. bar)         │
├────────────────────────────────┴─────────────────────────────────┤
│  [conditional] Revenue by Region (bar) + Map (if geo available)  │
└──────────────────────────────────────────────────────────────────┘
Minimum viable dashboard (thin data): KPI cards + one breakdown + one trend.
Never return an empty dashboard — fall back to summary table + KPI cards.
```

---

## Step 8 — Rejection Log (always generate)

After finalizing visuals, output a structured log of every angle considered and the decision made.
This is mandatory — it makes the agent's reasoning transparent and debuggable.

```
NORTH STAR: Profit Margin % — reason: [profit_col] detected
INCLUDED:   Revenue Trend — [date_col] with N distinct months
INCLUDED:   Discount Impact — [discount_col] present, variance confirmed across tiers
INCLUDED:   Category Profitability Matrix — category + sub-category both present
REJECTED:   [country_col] breakdown — cardinality = 1 (single value, zero variance)
REJECTED:   [city_col] bar chart — cardinality 412, exceeds bar limit; map used instead
REJECTED:   Donut for [subcategory_col] — 17 unique values exceeds 5-value donut limit
SKIPPED:    Customer segment analysis — no segment/channel/tier column detected
```

---

## Universal Retail Analytical Principles

These apply to every retail dataset regardless of schema:

⚠️ **Revenue ≠ health** — A category or customer can top the revenue list while actively
losing money. Always pair every revenue visual with Margin %. Never show revenue alone
in a leaderboard context.

⚠️ **Discount = margin risk by default** — Any dataset with a discount/promo/markdown
column is a potential profit erosion problem until the data proves otherwise. The discount
impact chart is mandatory whenever that column is present.

⚠️ **Top revenue ≠ top profit product** — The top-10-by-revenue and top-10-by-profit
product lists almost always differ. Show both. The divergence is typically the most
actionable insight for a category manager or buyer.

⚠️ **Segment volume ≠ segment value** — The largest segment by order count often has the
lowest AOV and weakest margin. Always show Margin % and AOV alongside order volume.

⚠️ **Variance gate before building** — Before committing to any breakdown visual, verify
the metric actually varies across the dimension's values. A region breakdown where all
four regions show 24–26% margin adds no information and wastes space.

---

## Reference Files

- `references/retail-kpi-definitions.md` — KPI definitions, formulas, retail benchmark ranges
- `references/dax-measures-retail.md` — Full DAX library for standard retail measures
- `references/column-semantic-map.md` — Extended pattern-matching table for non-standard schemas

*Load reference files only when generating actual DAX/pbix code, or when the user requests
benchmark context or formula details. Do not load them during profiling/planning.*
