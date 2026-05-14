# Examples

Each example is a small dbt project with seeds, models, ggsql visualisations, and
dashboard YAML.

## Gallery

- `simple_dbt`: minimal revenue dashboard and chart syntax sampler.
- `sales_dashboard`: sales performance by month, channel, and region.
- `product_analytics`: product usage and conversion metrics.
- `finance_metrics`: finance KPIs for bookings, expenses, and margin.

## Run an example

From an example directory:

```bash
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean --zip
```

Open `target/ggsql/site/index.html`.
