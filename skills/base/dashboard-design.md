# Skill: Power BI Dashboard Color & Layout Placement

**Load this file when:** designing a new Power BI dashboard — before positioning any visual or picking any color. This skill defines the structural conventions and color logic observed across high-quality analytical dashboards.

---

## Part 1 — Layout Placement

### The canonical dashboard grid

Every dashboard analyzed uses a consistent 3-zone vertical layout:

```
┌──────────────────────────────────────────────────────┐
│  ZONE 1 — KPI Bar (full width, ~80–100px tall)        │
│  4 headline metrics, equal-width cards                │
├──────────────────────────────────────────────────────┤
│  ZONE 2 — Primary Analysis (60–65% of remaining h)   │
│  Left: compact charts (part-to-whole, breakdown)      │
│  Right: main trend chart (60–70% of row width)        │
├──────────────────────────────────────────────────────┤
│  ZONE 3 — Detail / Supporting (35–40% of remaining h)│
│  Left: secondary chart (wider)                        │
│  Right: data table / leaderboard (narrower)           │
└──────────────────────────────────────────────────────┘
```

### Zone 1 — KPI headline bar

- **Always full-width, always at the top.** The reader's eye enters top-left; put the answer to "how are we doing?" there immediately.
- Use exactly **4 KPI cards** of equal width. More than 4 fragments attention; fewer feels sparse.
- Each card contains: metric name (small, muted), large bold value, and a **bullet/progress bar** showing position vs. target or vs. previous period.
- No chart types in Zone 1 — numbers and comparison bars only.
- Background: **white or very light gray** to contrast with the colored visuals below.

### Zone 2 — Primary analysis row

- Split into **left column (30–35% width)** and **right column (65–70% width)**.
- **Left column:** 1–2 compact visuals that answer structural questions — donut charts (part-to-whole), small bar charts, or ranked lists. These visuals are compact; their primary job is supporting the main chart on the right.
- **Right column:** The single most important chart on the dashboard. Usually a **time-series trend** (column chart with toggle between metrics, or a line chart). This chart should be visually dominant — tall, wide, given the most breathing room.
- If the left column holds 2 visuals, stack them vertically with equal height and add a visible card border/shadow between them.

### Zone 3 — Detail and supporting row

- Split into **left section (~55–60% width)** and **right section (~40–45% width)**.
- **Left:** a richer secondary chart (multi-series column, scatter, grouped bar). This is where you answer the "drill-down" question the main chart raised.
- **Right:** a **data table or ranked list**. Tables belong here — not in Zone 1 or Zone 2. They anchor the bottom-right and give power users a way to read exact values.
- Row height is shorter than Zone 2 — these are supporting, not primary.

### Left navigation sidebar (optional, consistent width ~200px)

- If a sidebar is used, it holds only: logo/branding at top, page navigation links (icon + label), and user profile at bottom.
- Keep it **dark (near-black background)** contrasting against the white dashboard canvas — this creates a clear visual separation and a professional frame.
- Navigation items: active state uses a filled highlight rectangle behind the item; inactive items are muted white text.

### Filters / global controls

- Position filter dropdowns in the **top-right corner of the canvas header** — never inside the chart zones.
- Use a consistent horizontal row: `Select A ▾  Select B ▾  Select C ▾` with a Reset button to the left of them.
- Labels above each dropdown ("Select Nationality", "Select Gender") are small and muted — they are not headings.

### Chart card containers

- Every visual lives inside a **white card with a subtle border or soft drop shadow**.
- Consistent internal padding: ~16px on all sides.
- Chart title at **top-left of the card**, bold, sentence case. Subtitle (italics or muted gray) directly below it if needed.
- Never use colored backgrounds on chart cards — white/near-white only. Color belongs inside the chart, not in the container.

### Spacing rules

| Element | Value |
|---------|-------|
| Gap between KPI cards | 8–12px |
| Gap between chart cards | 12–16px |
| Canvas edge padding (left/right) | 16–20px |
| Canvas edge padding (top/bottom) | 12–16px |
| Internal card padding | 14–18px |
| Chart title margin-bottom | 6–8px |

---

## Part 2 — Color System

### The dominant color principle

All three reference dashboards share one structural rule: **one primary brand color carries 70–80% of the colored ink**. Secondary colors appear only to encode a distinct second dimension of meaning.

Never use 6+ colors on a single dashboard. More colors = more cognitive load. Precision in meaning requires restraint in palette.

### Primary palette structure

```
Primary color (dominant)   → All main data series, key bars, active states
Accent color (highlight)   → The "current" or "selected" period / top-ranked item
Muted gray (background)    → Non-selected, secondary, comparison bars
Alert colors (semantic)    → Positive delta: green. Negative delta: red/orange.
Text hierarchy             → Title: #1a1a1a. Subtitle: #555. Label: #888.
```

### Color assignments by visual type

| Visual | Color rule |
|--------|------------|
| Column chart (main trend) | Primary color for all bars; **single accent color** on the current/highlighted bar only; gray for all others |
| Bar chart (breakdown) | Primary color fill, sorted top-to-bottom — no additional colors unless a second dimension is encoded |
| Donut / Pie chart | 2–4 categorical colors drawn from the palette; the dominant segment gets the primary color |
| KPI bullet bar | Primary fill for actual; gray for target/background bar |
| Positive delta (MoM, YoY) | Always **green** — do not use your primary brand color for positive deltas |
| Negative delta | Always **red or orange-red** — never green |
| Table rows | Alternating white / very light gray (#f7f7f7) — no color in cells |
| Reference line (average, target) | Dashed gray line, no fill |
| Selected / active filter chip | Primary color background with white text |

### Color palettes by dashboard archetype

**Corporate / Financial (Education example)**
- Primary: `#2C3E6B` (dark navy blue)
- Accent: `#4CAF50` (green, for the current/best period)
- Neutral bars: `#B0BEC5` (blue-gray)
- Delta positive: `#43A047`
- Delta negative: `#E53935`
- Background: `#FFFFFF` canvas, `#F5F6FA` zone fill

**Marketing / Consumer (Marketing Campaign example)**
- Primary: `#1E3A5F` (deep navy)
- Accent: `#00BCD4` (teal/cyan for CTR line, secondary series)
- Categorical: 3 values use `[#1E3A5F, #E87040, #E74C8B]` (navy, orange, pink)
- Background: `#FFFFFF`
- Delta: green (#4CAF50) for positive, muted red for negative

**Health / Wellness / B2C (Gym example)**
- Primary: `#3B4F9E` (medium blue-purple)
- Accent shades: `#6B7FCC`, `#9BA8DC`, `#C3CAF0` (same hue, lighter stops for sub-categories)
- Neutral gray: `#A8A8B0`
- Background: `#FFFFFF` canvas, `#F0F1F8` soft lavender-gray for zone fills
- Delta: green, red

### Same-hue depth for multi-series charts

When showing **multiple series of the same measure** (e.g., 4 membership tiers), use **one hue at different lightness stops** rather than 4 distinct colors:

```
Tier 1 (largest): darkest stop   e.g. #1E3A5F
Tier 2:           medium stop    e.g. #3B6EA6
Tier 3:           light stop     e.g. #6B9FCC
Tier 4 (smallest): lightest stop e.g. #A8C8E8
```

This keeps the chart cohesive and reduces the need for a legend — readers understand it as a depth/scale encoding.

### Dark sidebar contrast rule

If a dark left sidebar is used, its background must be at minimum 3 stops darker than the dashboard canvas on the same hue ramp. The contrast boundary must be sharp (no fade, no gradient). This creates the "frame" effect that anchors the layout.

### Semantic alert colors (never repurpose these)

| Semantic role | Color | Hex (reference) |
|--------------|-------|-----------------|
| Positive / good / above target | Green | `#43A047` or `#4CAF50` |
| Negative / bad / below target | Red | `#E53935` or `#D32F2F` |
| Warning / approaching threshold | Amber/Orange | `#FF8F00` or `#FB8C00` |
| Neutral comparison baseline | Gray | `#90A4AE` or `#B0BEC5` |

These colors have universal meaning to business readers. Reassigning them (e.g., using green as a category color) breaks the dashboard's semantic language.

---

## Part 3 — Typography Hierarchy

| Level | Usage | Style |
|-------|-------|-------|
| Dashboard title | Page/report name at top | 20–22px, bold, dark |
| Section subtitle | Supporting description under title | 11–13px, italic or regular, muted gray |
| Chart title | Inside each card, top-left | 13–14px, semi-bold, dark |
| Chart subtitle | Under chart title, describing scope | 10–12px, regular, muted |
| Axis labels | Category and value axis | 10–11px, regular, #666 |
| Data labels | On bars/lines, key points only | 10–11px, regular or semi-bold |
| KPI value | Large number in Zone 1 cards | 26–32px, bold |
| KPI label | Metric name above the large number | 11–12px, regular, muted |
| Table header | Column titles in Zone 3 table | 11–12px, semi-bold, slightly muted |
| Table values | Cell data | 11–12px, regular |

**Rule:** Never use more than 3 distinct font sizes in a single chart card.

---

## Part 4 — Anti-Patterns (Block These)

| Anti-pattern | What to do instead |
|-------------|-------------------|
| Colored card backgrounds | White/near-white only; color lives inside the chart |
| More than 4 colors in one chart | Reduce to primary + accent + gray + one semantic color |
| Charts with no breathing room (zero padding) | Always 14–18px internal card padding |
| KPI card without a comparison bar | Add a bullet/progress bar showing vs. target or prior period |
| Large table in Zone 2 (primary analysis) | Tables belong in Zone 3 only |
| Using red/green as category colors | Reserve red/green exclusively for semantic delta encoding |
| Charts at different vertical alignments | All cards in a row must share the same top and bottom edge |
| Titles in ALL CAPS | Sentence case always |
