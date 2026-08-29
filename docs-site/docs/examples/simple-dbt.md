import Link from '@docusaurus/Link';

# Simple dbt

`examples/simple_dbt` is the smallest useful project. It is best for learning the core workflow and checking that local dependencies are installed correctly.

## Rendered output

Rendered dashboards:
- <Link to="pathname:///dashboards/simple-dbt/dashboards/executive.html">Open the full simple dbt dashboard</Link>
- <Link to="pathname:///dashboards/simple-dbt/dashboards/executive_dark.html">Open the dark mode simple dbt dashboard</Link>

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
- A second dashboard that uses `theme: dark` and `chart_theme: dark` in dashboard YAML.

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
target/glyf/site/index.html
target/glyf/charts/revenue.svg
target/glyf/charts/revenue.png
```
