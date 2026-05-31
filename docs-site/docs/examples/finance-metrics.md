import Link from '@docusaurus/Link';

# Finance Metrics

`examples/finance_metrics` shows bookings, expenses, and gross margin reporting.

## Rendered output

Rendered dashboard: <Link to="pathname:///dashboards/finance-metrics/dashboards/finance.html">Open the full finance metrics dashboard</Link>

Deployed docs path: `https://glyf.pages.dev/dashboards/finance-metrics/dashboards/finance.html`

<iframe
  src="/dashboards/finance-metrics/dashboards/finance.html"
  title="Finance metrics dashboard preview"
  style={{
    width: '100%',
    height: '900px',
    border: '1px solid var(--ifm-color-emphasis-300)',
    borderRadius: '12px',
    background: '#ffffff'
  }}
/>

## What it demonstrates

- Finance dashboard structure.
- Multiple KPI views in one static site.
- A clean pattern for adding new metric dashboards.
- Mixed line, bar, area, scatter, and pie ggsql charts.
- Section-level dashboard columns such as `65% 35%` and `35% 65%`.

## Run it

```bash
cd examples/finance_metrics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf build --zip
uv run glyf serve
```

## Dashboard YAML

```yaml
name: finance
title: Finance Metrics
description: Bookings, expenses, and margin by month and department.

layout:
  columns: "65% 35%"

sections:
  - title: Financial Performance
    columns: "65% 35%"
    charts:
      - bookings_trend
      - margin_share

  - title: Expense Control
    columns: 2
    charts:
      - expenses_by_department
      - gross_margin_trend

  - title: Margin Efficiency
    columns: "35% 65%"
    items:
      - metric:
          label: March gross margin
          value: "$37.6k"
      - chart: margin_vs_expenses
```

## Extend it

Add another `.ggsql` file under `visualisations/`, then add the filename stem to `dashboards/finance.yml`.
