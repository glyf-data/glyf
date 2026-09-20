# finance_metrics

Finance metrics example with twelve months of bookings, spend, gross margin
and invoice collections. It uses all eight ggsql chart types glyf draws.

```bash
cd examples/finance_metrics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean --zip
```

This creates the example DuckDB database at `target/finance_metrics.duckdb`.
