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
target/glyf/site/index.html
target/glyf/charts/monthly_revenue.svg
target/glyf/charts/channel_revenue.svg
target/glyf/charts/regional_revenue.svg
```
