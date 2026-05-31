import Link from '@docusaurus/Link';

# Simple dbt

`examples/simple_dbt` is the smallest useful project. It is best for learning the core workflow and checking that local dependencies are installed correctly.

## Rendered output

Rendered dashboard: <Link to="pathname:///dashboards/simple-dbt/dashboards/executive.html">Open the full simple dbt dashboard</Link>

Deployed docs path: `https://glyf.pages.dev/dashboards/simple-dbt/dashboards/executive.html`

<iframe
  src="/dashboards/simple-dbt/dashboards/executive.html"
  title="Simple dbt dashboard preview"
  style={{
    width: '100%',
    height: '820px',
    border: '1px solid var(--ifm-color-emphasis-300)',
    borderRadius: '12px',
    background: '#ffffff'
  }}
/>

## What it demonstrates

- A compact dbt project with seeds and models.
- Multiple chart types against one fact model.
- A simple dashboard generated from chart names.

## Run it

```bash
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf doctor
uv run glyf build
uv run glyf serve
```

## Example chart

```sql
SELECT month, revenue
FROM {{ ref('fct_orders') }}

VISUALISE month AS x, revenue AS y
DRAW line
LABEL title => 'Revenue'
```

## Expected output

```text
target/ggsql/site/index.html
target/ggsql/charts/revenue.svg
target/ggsql/charts/revenue.png
```
