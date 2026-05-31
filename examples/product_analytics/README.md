# product_analytics

Product analytics example with active users, activation, engagement mix,
dashboard macro components, and asymmetric dashboard sections.

```bash
cd examples/product_analytics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean --zip
```

This creates the example DuckDB database at `target/product_analytics.duckdb`.
