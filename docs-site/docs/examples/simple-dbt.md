# Simple dbt

`examples/simple_dbt` is the smallest useful project. It is best for learning the core workflow and checking that local dependencies are installed correctly.

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
