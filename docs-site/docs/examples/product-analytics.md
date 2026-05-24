import Link from '@docusaurus/Link';

# Product Analytics

`examples/product_analytics` shows product usage and activation metrics by plan.

## Rendered output

![Product analytics screenshot placeholder](/img/examples/product-analytics-banner.svg)

Rendered dashboard: <Link to="pathname:///dashboards/product-analytics/dashboards/product.html">/dashboards/product-analytics/dashboards/product.html</Link>

Deployed docs path: `https://glyf.pages.dev/dashboards/product-analytics/dashboards/product.html`

## What it demonstrates

- Active user trend visualisation.
- Activation by plan.
- Scatter plot patterns for usage analysis.
- Rich dashboard sections with asymmetric `30% 70%` and `65% 35%` columns.
- Dashboard macro components, including built-ins and project-local Python macros.
- Interactive ggsql charts with tooltip, legend filtering, and zoom.

## Run it

```bash
cd examples/product_analytics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean --zip
```

## Dashboard YAML

```yaml
name: product
title: Product Analytics
description: Product usage and activation metrics by plan.

toolbar:
  visibility: private
  actions: [share, visibility]

summary:
  - "{{ product_owner() }}"
  - "{{ ui.label_value('Generated', time.now('%Y-%m-%d %H:%M')) }}"
  - "{{ ui.badge('Demo macros', tone='info') }}"

layout:
  columns: "30% 70%"

sections:
  - title: Usage Overview
    columns: "30% 70%"
    items:
      - metric:
          label: Active users
          value: "4.3k"
      - chart: active_users
      - metric:
          label: Sessions
          value: "14.9k"
      - chart: sessions_scatter

  - title: Activation
    columns: 2
    items:
      - component: "{{ activation_health(0.82) }}"
      - component: "{{ ui.list(['Free', 'Team', 'Enterprise'], title='Tracked plans') }}"
      - chart: activation_by_plan
      - chart: activation_rate_by_plan

  - title: Engagement Mix
    columns: "65% 35%"
    charts:
      - sessions_per_user
      - sessions_by_plan
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
