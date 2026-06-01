import Link from '@docusaurus/Link';

# Sales Dashboard

`examples/sales_dashboard` shows a sales performance dashboard with monthly revenue, channel mix, and regional sales.

## Rendered output

Rendered dashboard: <Link to="pathname:///dashboards/sales-dashboard/dashboards/sales.html">Open the full sales dashboard</Link>

Deployed docs path: `https://glyf.pages.dev/dashboards/sales-dashboard/dashboards/sales.html`

<iframe
  src="/dashboards/sales-dashboard/dashboards/sales.html"
  title="Sales dashboard preview"
  style={{
    width: '100%',
    height: '860px',
    border: '1px solid var(--ifm-color-emphasis-300)',
    borderRadius: '12px',
    background: '#ffffff'
  }}
/>

## What it demonstrates

- Multiple visualisations in one dashboard.
- Chart SQL grouped around a sales fact model.
- Output suitable for static publishing or CI artifacts.

## Run it

```bash
cd examples/sales_dashboard
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf build --zip
uv run glyf serve
```

## Example chart

```sql
SELECT month, sum(revenue) as revenue
FROM {{ ref('fct_sales') }}
GROUP BY 1

VISUALISE month AS x, revenue AS y
DRAW line
LABEL title => 'Monthly Revenue'
LABEL subtitle => 'Revenue across all channels'
LABEL x_title => 'Month'
LABEL y_title => 'Revenue'
```

## Generated artifacts

```text
target/glyf/site/index.html
target/glyf/charts/monthly_revenue.svg
target/glyf/charts/channel_revenue.svg
target/glyf/charts/regional_revenue.svg
```
