import Link from '@docusaurus/Link';

# Finance Metrics

`examples/finance_metrics` shows bookings, expenses, gross margin and collections reporting over twelve months of synthetic data.

## Rendered output

Rendered dashboard: <Link to="pathname:///dashboards/finance-metrics/dashboards/finance.html">Open the full finance metrics dashboard</Link>

<iframe
  src="/dashboards/finance-metrics/dashboards/finance.html"
  title="Finance metrics dashboard preview"
  style={{
    width: '100%',
    height: '1200px',
    border: '1px solid var(--ifm-color-emphasis-300)',
    borderRadius: '12px',
    background: '#ffffff'
  }}
/>

## What it demonstrates

- All eight chart types from two finance models. `fct_finance` has one row per month and department and feeds the line, bar, area, scatter, pie and heatmap. `fct_invoices` has one row per invoice and feeds the histogram and boxplot.
- A histogram and a boxplot whose queries select rows and aggregate nothing. glyf bins and counts `days_to_pay`, and takes the quartiles of `discount_pct`.
- A heatmap whose axis order comes from the query's `ORDER BY month, department`.
- Section-level dashboard columns such as `65% 35%`, a row of metric tiles, filters resolved from chart artifacts, and built-in macros in `summary`.

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
description: Bookings, expenses, margin and collections for the last twelve months.
tags:
  - finance
  - margin
  - bookings
  - collections

filters:
  - field: department
    values: source(expenses_by_department, department)
  - field: segment
    values: source(days_to_pay, segment)

summary:
  - "{{ ui.label_value('Period', 'Apr 2025 to Mar 2026') }}"
  - "{{ ui.label_value('Generated', time.now('%Y-%m-%d %H:%M')) }}"
  - "{{ ui.badge('Synthetic data', tone='info') }}"

layout:
  columns: "65% 35%"

sections:
  - title: Headline
    description: The twelve months in three numbers.
    columns: 3
    items:
      - metric:
          label: Bookings
          value: "$1.08M"
          note: Four departments, twelve months
      - metric:
          label: Gross margin
          value: "$504k"
          note: 46.7% of bookings
      - metric:
          label: March gross margin
          value: "$62.5k"
          note: On $116k of bookings, the strongest month

  - title: Financial Performance
    description: Bookings and contribution mix.
    columns: "65% 35%"
    charts:
      - bookings_trend
      - margin_share

  - title: Expense Control
    description: Department-level spend and margin trend.
    columns: 2
    charts:
      - expenses_by_department
      - gross_margin_trend

  - title: Margin Efficiency
    description: Where margin comes from, by department and month.
    columns: 1
    items:
      - chart: margin_rate_by_department
      - chart: margin_vs_expenses

  - title: Collections
    description: How long invoices take to pay and what is given away to close them.
    columns: 2
    items:
      - chart: days_to_pay
      - chart: discount_by_segment
      - metric:
          label: Median days to pay
          value: "24"
          note: 17 of 300 invoices took longer than 60 days
      - component: "{{ alert.warning('Enterprise invoices pay at a median of 47 days and carry the deepest discounts.', title='Watch') }}"
```

## Extend it

Add another `.ggsql` file under `visualisations/`, then add the filename stem to `dashboards/finance.yml`.
