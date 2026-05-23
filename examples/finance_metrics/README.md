# finance_metrics

Finance metrics example with bookings, spend, gross margin, and mixed ggsql
chart types.

```bash
cd examples/finance_metrics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean --zip
```
