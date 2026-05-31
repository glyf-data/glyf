# sales_dashboard

Sales dashboard example with monthly revenue, channel mix, and regional sales.

```bash
cd examples/sales_dashboard
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean --zip
```

This creates the example DuckDB database at `target/sales_dashboard.duckdb`.

Expected generated output:

```text
target/ggsql/site/index.html
target/ggsql/charts/monthly_revenue.svg
target/ggsql/charts/channel_revenue.svg
target/ggsql/charts/regional_revenue.svg
```
