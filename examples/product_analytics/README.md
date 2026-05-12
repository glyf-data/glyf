# product_analytics

Product analytics example with active users, activation, and plan mix.

```bash
cd examples/product_analytics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run dbt-ggsql render
uv run dbt-ggsql dashboard
uv run dbt-ggsql export --clean --zip
```
