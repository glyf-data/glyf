# finance_metrics

Finance metrics example with bookings, spend, and gross margin.

```bash
cd examples/finance_metrics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run dbt-ggsql render
uv run dbt-ggsql dashboard
uv run dbt-ggsql export --clean --zip
```
