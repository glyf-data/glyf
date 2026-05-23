# product_analytics

Product analytics example with active users, activation, engagement mix, and
asymmetric dashboard sections.

```bash
cd examples/product_analytics
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean --zip
```
