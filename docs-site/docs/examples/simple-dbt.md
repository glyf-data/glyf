import Link from '@docusaurus/Link';

# Simple dbt

`examples/simple_dbt` is the smallest useful project. It is best for learning the core workflow and checking that local dependencies are installed correctly.

## Rendered output

![Simple dbt dashboard screenshot placeholder](/img/examples/simple-dbt-banner.svg)

Rendered dashboard: <Link to="pathname:///dashboards/simple-dbt/dashboards/executive.html">/dashboards/simple-dbt/dashboards/executive.html</Link>

Deployed docs path: `https://dbtcharts.pages.dev/dashboards/simple-dbt/dashboards/executive.html`

## What it demonstrates

- A compact dbt project with seeds and models.
- Multiple chart types against one fact model.
- A simple dashboard generated from chart names.

## Run it

```bash
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run dbt-charts doctor
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean
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
