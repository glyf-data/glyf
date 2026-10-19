import Link from '@docusaurus/Link';

# Sales Dashboard

`examples/sales_dashboard` shows a sales performance dashboard with monthly revenue, channel mix, and regional sales.

## Rendered output

Rendered dashboard: <Link to="pathname:///dashboards/sales-dashboard/dashboards/sales.html">Open the full sales dashboard</Link>

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

- Three charts (monthly revenue, channel mix, regional sales) all querying one `fct_sales` model.
- Two maps: revenue by country, shaded on the world's countries, and stores as points sized by revenue. See [Map](../charts/map.md).
- A treemap of the same stores, each sized by its revenue and grouped by format. See [Treemap](../charts/treemap.md).
- A simple dashboard shape: two groups of charts, with no sections or macros.

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
target/glyf/charts/revenue_by_country.svg
target/glyf/charts/store_locations.svg
target/glyf/charts/store_revenue.svg
```
