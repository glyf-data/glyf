import Link from '@docusaurus/Link';

# Product Analytics

`examples/product_analytics` shows product usage and activation metrics by plan.

## Rendered output

Rendered dashboard: <Link to="pathname:///dashboards/product-analytics/dashboards/product.html">Open the full product analytics dashboard</Link>

<iframe
  src="/dashboards/product-analytics/dashboards/product.html"
  title="Product analytics dashboard preview"
  style={{
    width: '100%',
    height: '940px',
    border: '1px solid var(--ifm-color-emphasis-300)',
    borderRadius: '12px',
    background: '#ffffff'
  }}
/>

## What it demonstrates

- Sections with asymmetric `30% 70%` and `65% 35%` column tracks, metric tiles, and titled charts.
- Dashboard filters whose values come from a rendered chart artifact (`source(activation_by_plan, plan)`).
- Built-in macros in `summary` and a project-local macro, `activation_health`, that reads the latest activation rate through `MacroContext`.
- A histogram and a boxplot over `fct_account_sessions`, which has one row per account, and a weekday-by-hour heatmap over `fct_hourly_activity` ordered by `weekday_number, hour` so the week starts on Monday.
- A table of the ten most active accounts (`top_accounts.ggsql`): `VISUALISE *` over the same model with `LIMIT 10`, column labels, and a `CONFIG height` that turns the card into a scroll area.
- Interactive ggsql charts with `tooltip`, `legend_filter`, and `zoom`.

## Run it

```bash
cd examples/product_analytics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf build --zip
uv run glyf serve
```

## Dashboard YAML

This is `dashboards/product.yml` as shipped in the example. `product_owner()` and `activation_health()` are defined in `dashboards/macros.py` beside it.

```yaml
name: product
title: Product Analytics
description: Product usage and activation metrics by plan.
tags:
  - product
  - activation
  - usage

filters:
  - field: plan
    values: source(activation_by_plan, plan)
  - field: team
    values: [product, lifecycle]

toolbar:
  visibility: private

summary:
  - "{{ product_owner() }}"
  - "{{ ui.label_value('Generated', time.now('%Y-%m-%d %H:%M')) }}"
  - "{{ ui.badge('Demo macros', tone='info') }}"

layout:
  columns: "30% 70%"

sections:
  - title: Usage Overview
    description: Active user growth and engagement across twelve weeks.
    columns: "30% 70%"
    items:
      - metric:
          label: Weekly active users
          value: "2.3k"
          note: Week 12, up from 1.5k in week 1
      - chart: active_users
        title: Active Users Trend
      - metric:
          label: Sessions
          value: "86.7k"
          note: Total product sessions across all plans
      - chart: sessions_scatter
        title: Sessions vs Active Users

  - title: Activation
    description: Compare activated users and activation rates by plan.
    columns: 2
    items:
      - component: "{{ activation_health(chart='activation_rate_by_plan', field='activation_rate', threshold=80) }}"
      - component: "{{ ui.list(source('activation_by_plan', 'plan'), title='Tracked plans') }}"
      - chart: activation_by_plan
      - chart: activation_rate_by_plan

  - title: Engagement Mix
    description: Sessions per active user and total session share by plan.
    columns: "65% 35%"
    charts:
      - sessions_per_user
      - sessions_by_plan

  - title: Accounts
    description: The ten most active accounts, as rows rather than a picture.
    columns: "60% 40%"
    items:
      - chart: top_accounts
      - chart: sessions_per_account

  - title: Distribution
    description: What the weekly totals average away, one row per account.
    columns: 2
    items:
      - chart: session_length_distribution
      - chart: sessions_per_account
      - markdown:
          title: Reading these two
          text: |
            Both charts query `fct_account_sessions`, which has one row per
            account. The histogram bins and counts those rows, and the boxplot
            takes their quartiles, so neither query aggregates anything itself.
      - metric:
          label: Median sessions per account
          value: "9 / 24 / 59"
          note: Free, Pro and Team

  - title: Rhythm
    description: When the product is in use, by weekday and hour.
    columns: "75% 25%"
    items:
      - chart: activity_by_hour
      - metric:
          label: Busiest hour
          value: "Tue 11:00"
          note: 694 sessions, about five times a weekend peak
```

## Example chart

```sql
SELECT week, sum(active_users) as active_users
FROM {{ ref('fct_product_usage') }}
GROUP BY 1

VISUALISE week AS x, active_users AS y
DRAW area
LABEL title => 'Active Users'
LABEL x_title => 'Week'
LABEL y_title => 'Users'
INTERACT tooltip
```
