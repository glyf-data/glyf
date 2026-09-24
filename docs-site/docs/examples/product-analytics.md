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

- Dark by default (`theme: dark`) and an `owner` in the bar under the header.
- A headline row of four: three KPI tiles computed from the data (`weekly_active_users`, `weekly_sessions`, `weekly_activated_users`), each the latest week against the one before with the change in green or red, beside a hand-written metric tile with a `delta` and `trend: down`.
- Dashboard filters whose values come from a rendered chart artifact (`source(activation_by_plan, plan)`).
- Built-in macros in `summary` and two project-local macros: `activation_health` reads the latest activation rates through `MacroContext` and returns a status card led by the number, and `product_notes` returns hand-written release notes, to show that a macro can carry fixed text as well as values from the build.
- A histogram and a boxplot over `fct_account_sessions`, which has one row per account, and a weekday-by-hour heatmap over `fct_hourly_activity` ordered by `weekday_number, hour` so the week starts on Monday.
- A table of the ten most active accounts (`top_accounts.ggsql`): `VISUALISE *` over the same model with `LIMIT 10`, column labels, and a `CONFIG height` that turns the card into a scroll area.
- Interactive ggsql charts with `tooltip`, `legend_filter`, and `zoom`; the zooming scatter starts with its zoom locked, and every chart card has download and full-screen tools.

## Run it

```bash
cd examples/product_analytics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf build --zip
uv run glyf serve
```

## Dashboard YAML

This is `dashboards/product.yml` as shipped in the example. `product_owner()`, `product_notes()` and `activation_health()` are defined in `dashboards/macros.py` beside it.

```yaml
name: product
title: Product Analytics
description: Product usage and activation metrics by plan.
owner: Growth team
theme: dark
tags:
  - product
  - activation
  - usage

filters:
  - field: plan
    values: source(activation_by_plan, plan)
    control: toggle
  - field: week
    values: source(active_users, week)

toolbar:
  visibility: private
  stars: 24

summary:
  - "{{ ui.text('Active users grew every week of the quarter, from 1,480 in week 1 to 2,325 in week 12, and the Team plan accounts for most of the growth in sessions per user. Activation holds near a third of active users; Team converts best, at close to 60%. Hourly activity peaks mid-morning on weekdays.', title='Overview') }}"
  - "{{ alert.info('Written by hand for this demo. An AI-generated summary is on the roadmap.', 'About this summary') }}"
  - "{{ product_owner() }}"
  - "{{ ui.label_value('Generated', time.now('%Y-%m-%d %H:%M')) }}"

layout:
  columns: "30% 70%"

sections:
  - title: Headline
    description: Week 12 against week 11, in four numbers.
    columns: 4
    items:
      - chart: weekly_active_users
      - chart: weekly_sessions
      - chart: weekly_activated_users
      - metric:
          label: Activation rate
          value: "28.5%"
          delta: "-1.7 pts vs last week"
          trend: down
          note: Activated users over active users, week 12

  - title: Usage Overview
    description: Active user growth and engagement across twelve weeks.
    columns: 2
    items:
      - chart: active_users
        title: Active Users Trend
      - chart: sessions_scatter
        title: Sessions vs Active Users

  - title: Activation
    description: Compare activated users and activation rates by plan.
    columns: 2
    items:
      - component: "{{ activation_health(chart='activation_rate_by_plan', field='activation_rate', threshold=40) }}"
      - component: "{{ product_notes() }}"
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
