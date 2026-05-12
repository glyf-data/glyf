# sales_dashboard

Sales dashboard example with monthly revenue, channel mix, and regional sales.

```bash
cd examples/sales_dashboard
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run dbt-ggsql render
uv run dbt-ggsql dashboard
uv run dbt-ggsql export --clean --zip
```

Expected generated output:

```text
target/ggsql/site/index.html
target/ggsql/charts/monthly_revenue.svg
target/ggsql/charts/channel_revenue.svg
target/ggsql/charts/regional_revenue.svg
```
