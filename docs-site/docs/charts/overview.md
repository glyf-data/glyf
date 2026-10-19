---
slug: /charts
sidebar_label: All charts
---

import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Charts

Every chart is a `.ggsql` file: a SQL query, then a `VISUALISE` line that maps
its columns to roles and a `DRAW` line that picks the chart type. Each card
below is a chart from the example projects; switch it to **Code** to see the
file that drew it, as it is in the repository, or open the chart's page for
its roles and how it reads.

<div className="chartTypeGrid">

<ChartTypeCard type="line" title="Line" page="/docs/charts/line" example="examples/product_analytics/visualisations/activation_rate_by_plan.ggsql" summary="A value over an ordered x, one line per colour. Shows trend and turning points.">

```sql
SELECT
  week,
  plan,
  round(sum(activated_users) * 100.0 / nullif(sum(active_users), 0), 1) as activation_rate
FROM {{ ref('fct_product_usage') }}
GROUP BY 1, 2

VISUALISE week AS x, activation_rate AS y, plan AS color
DRAW line
LABEL title => 'Activation Rate by Plan'
LABEL x_title => 'Week'
LABEL y_title => 'Activation Rate (%)'
INTERACT tooltip, legend_filter
```

</ChartTypeCard>

<ChartTypeCard type="bar" title="Bar" page="/docs/charts/bar" example="examples/product_analytics/visualisations/sessions_per_user.ggsql" summary="One bar per x value, stacked by colour. Compares amounts across categories or periods.">

```sql
SELECT
  week,
  round(sum(sessions) * 1.0 / nullif(sum(active_users), 0), 2) as sessions_per_user
FROM {{ ref('fct_product_usage') }}
GROUP BY 1

VISUALISE week AS x, sessions_per_user AS y
DRAW bar
LABEL title => 'Sessions per Active User'
LABEL x_title => 'Week'
LABEL y_title => 'Sessions per User'
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="area" title="Area" page="/docs/charts/area" example="examples/product_analytics/visualisations/active_users.ggsql" summary="A line with the space under it filled, stacked by colour. Shows volume and its make-up over time.">

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

</ChartTypeCard>

<ChartTypeCard type="combo" title="Combo" page="/docs/charts/combo" example="examples/finance_metrics/visualisations/bookings_and_margin.ggsql" summary="Bars of one measure and a line of another over the same x, each on its own axis. Shows a total and a rate together.">

```sql
SELECT
  month,
  sum(bookings) as bookings,
  round(sum(gross_margin) * 100.0 / nullif(sum(bookings), 0), 1) as margin_rate
FROM {{ ref('fct_finance') }}
GROUP BY 1
ORDER BY 1

VISUALISE month AS x, bookings AS y, margin_rate AS y2
DRAW combo
LABEL title => 'Bookings and Margin Rate'
LABEL subtitle => 'Bars are bookings; the line is gross margin as a share of them'
LABEL x_title => 'Month'
LABEL y_title => 'Bookings'
LABEL y2_title => 'Margin Rate (%)'
CONFIG width => 1100
CONFIG height => 320
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="scatter" title="Scatter" page="/docs/charts/scatter" example="examples/product_analytics/visualisations/sessions_scatter.ggsql" summary="One point per row. Shows how two numbers move together, and the rows that do not.">

```sql
SELECT active_users, sessions, plan
FROM {{ ref('fct_product_usage') }}
ORDER BY plan, active_users

VISUALISE active_users AS x, sessions AS y, plan AS color
DRAW scatter
LABEL title => 'Sessions vs Active Users'
LABEL x_title => 'Active Users'
LABEL y_title => 'Sessions'
INTERACT tooltip, zoom
```

</ChartTypeCard>

<ChartTypeCard type="pie" title="Pie" page="/docs/charts/pie" example="examples/product_analytics/visualisations/sessions_by_plan.ggsql" summary="One slice per x value, sized by y. Shows the share of a whole, for a handful of parts.">

```sql
SELECT
  plan,
  sum(sessions) as sessions
FROM {{ ref('fct_product_usage') }}
GROUP BY 1
ORDER BY sessions DESC

VISUALISE plan AS x, sessions AS y
DRAW pie
LABEL title => 'Sessions by Plan'
LABEL y_title => 'Sessions'
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="histogram" title="Histogram" page="/docs/charts/histogram" example="examples/product_analytics/visualisations/session_length_distribution.ggsql" summary="Rows counted into bins of x. Shows the shape of a distribution.">

```sql
SELECT
  avg_session_minutes,
  plan
FROM {{ ref('fct_account_sessions') }}
ORDER BY avg_session_minutes, plan

VISUALISE avg_session_minutes AS x, plan AS color
DRAW histogram
LABEL title => 'Session Length by Account'
LABEL subtitle => 'One row per account, binned by average session length'
LABEL x_title => 'Average session (minutes)'
LABEL y_title => 'Accounts'
INTERACT tooltip, legend_filter
```

</ChartTypeCard>

<ChartTypeCard type="boxplot" title="Boxplot" page="/docs/charts/boxplot" example="examples/product_analytics/visualisations/sessions_per_account.ggsql" summary="Quartiles of y for each x, outliers as points. Compares spreads, not just averages.">

```sql
SELECT
  plan,
  sessions
FROM {{ ref('fct_account_sessions') }}

VISUALISE plan AS x, sessions AS y
DRAW boxplot
LABEL title => 'Sessions per Account'
LABEL subtitle => 'Median, quartiles and outlying accounts for each plan'
LABEL x_title => 'Plan'
LABEL y_title => 'Sessions'
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="heatmap" title="Heatmap" page="/docs/charts/heatmap" example="examples/product_analytics/visualisations/activity_by_hour.ggsql" summary="One shaded cell per x and y pair. Shows patterns across two categories at once.">

```sql
SELECT
  weekday,
  hour,
  sessions
FROM {{ ref('fct_hourly_activity') }}
ORDER BY weekday_number, hour

VISUALISE hour AS x, weekday AS y, sessions AS color
DRAW heatmap
LABEL title => 'Sessions by Hour'
LABEL subtitle => 'Two working-day peaks; weekends run at a fifth of the volume'
LABEL x_title => 'Hour of day (UTC)'
LABEL y_title => 'Weekday'
CONFIG width => 1100
CONFIG height => 320
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="table" title="Table" page="/docs/charts/table" example="examples/product_analytics/visualisations/top_accounts.ggsql" summary="The rows themselves, one column per listed column. For when the exact values matter.">

```sql
SELECT account_id, plan, sessions, avg_session_minutes
FROM {{ ref('fct_account_sessions') }}
ORDER BY sessions DESC, account_id
LIMIT 10

VISUALISE *
DRAW table
LABEL title => 'Most active accounts'
LABEL account_id => 'Account'
LABEL avg_session_minutes => 'Avg minutes'
CONFIG height => 360
```

</ChartTypeCard>

<ChartTypeCard type="kpi" title="KPI" page="/docs/charts/kpi" example="examples/product_analytics/visualisations/weekly_activated_users.ggsql" summary="One number as a tile, with its change against a comparison. For a headline.">

```sql
WITH weekly AS (
  SELECT week, sum(activated_users) AS activated_users
  FROM {{ ref('fct_product_usage') }}
  GROUP BY 1
)
SELECT activated_users, lag(activated_users) OVER (ORDER BY week) AS previous
FROM weekly
ORDER BY week DESC
LIMIT 1

VISUALISE activated_users AS value, previous AS compare
DRAW kpi
LABEL title => 'Activated users'
LABEL compare => 'vs last week'
```

</ChartTypeCard>

<ChartTypeCard type="map" title="Map" page="/docs/charts/map" example="examples/sales_dashboard/visualisations/revenue_by_country.ggsql" summary="Regions filled by a value, or places as points. Shows where, not just how much.">

```sql
SELECT country, revenue
FROM {{ source('raw', 'country_sales') }}
ORDER BY country

VISUALISE country AS region, revenue AS color
DRAW map
LABEL title => 'Revenue by Country'
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="sankey" title="Sankey" page="/docs/charts/sankey" example="examples/product_analytics/visualisations/account_flow.ggsql" summary="Flows between stages, each band as wide as its value. Shows where things go.">

```sql
WITH accounts AS (
  SELECT
    plan,
    CASE
      WHEN sessions >= 40 THEN 'Heavy use'
      WHEN sessions >= 15 THEN 'Regular use'
      ELSE 'Light use'
    END AS activity,
    CASE WHEN avg_session_minutes >= 15 THEN 'Long sessions' ELSE 'Short sessions' END AS session_length
  FROM {{ ref('fct_account_sessions') }}
)
SELECT plan AS stage, activity AS next_stage, count(*) AS accounts
FROM accounts
GROUP BY 1, 2
UNION ALL
SELECT activity, session_length, count(*)
FROM accounts
GROUP BY 1, 2
ORDER BY 1, 2

VISUALISE stage AS source, next_stage AS target, accounts AS value
DRAW sankey
LABEL title => 'How Accounts Use the Product'
LABEL subtitle => 'Accounts by plan, then by how often and how long they use it'
CONFIG width => 1100
CONFIG height => 420
INTERACT tooltip
```

</ChartTypeCard>

</div>

## At a glance

| `DRAW` | Draws | Roles | From |
| --- | --- | --- | --- |
| `line` | One line per `color` value. | `x`, `y`, optional `color` | ggsql |
| `bar` | One bar per `x` value, stacked by `color`. | `x`, `y`, optional `color` | ggsql |
| `scatter` | One point per row. `point` is accepted as an alias. | `x`, `y`, optional `color` | ggsql (`point`) |
| `area` | One filled area per `color` value. | `x`, `y`, optional `color` | ggsql |
| `pie` | One slice per `x` value, sized by `y`. | `x`, `y`, optional `color` | glyf |
| `histogram` | The number of rows in each bin of `x`, stacked by `color`. | `x`, optional `color` | glyf |
| `boxplot` | The quartiles of `y` for each `x` value, with outliers as points. | `x`, `y`, optional `color` | glyf |
| `heatmap` | One cell per `x` and `y` pair, shaded by `color`. `tile` is accepted as an alias. | `x`, `y`, `color` | ggsql (`tile`) |
| `table` | The rows themselves, one column per listed column. Not drawn: no PNG or SVG. | a column list, or `*` | glyf |
| `kpi` | One number as a tile, with the change against a comparison value. Not drawn. | `value`, optional `compare` | glyf |
| `sankey` | Flows between stages, one band per `source` and `target` pair, as wide as its `value`. | `source`, `target`, `value` | glyf |
| `map` | One filled region per row, or one point per row at a latitude and longitude. | `region` or `latitude` and `longitude`, optional `size` and `color` | glyf |

Any other `DRAW` value fails validation with `unsupported chart type`. The
directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`, are in
[Visualisation syntax](../guides/visualisation-syntax.md).
