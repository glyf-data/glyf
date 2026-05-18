# Product Analytics

`examples/product_analytics` shows product usage and activation metrics by plan.

## What it demonstrates

- Active user trend visualisation.
- Activation by plan.
- Scatter plot patterns for usage analysis.

## Run it

```bash
cd examples/product_analytics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean --zip
```

## Dashboard YAML

```yaml
name: product
title: Product Analytics
description: Product usage and activation metrics by plan.

charts:
  - active_users
  - activation_by_plan
  - sessions_scatter
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
```
