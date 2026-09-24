# Examples

Each example is a small dbt project with seeds, models, ggsql visualisations, and
dashboard YAML.

## Gallery

- `simple_dbt`: minimal revenue dashboard and chart syntax sampler.
- `sales_dashboard`: sales performance by month, channel, and region.
- `product_analytics`: product usage and activation by plan, with a histogram and
  a boxplot over per-account rows and a weekday-by-hour heatmap.
- `finance_metrics`: bookings, expenses, margin and collections over twelve
  months. Uses all eight chart types.
- `clanker_insights`: what one customer's AI agents did on Clanker, a made-up
  agent platform: runs, success, spend by model, run time, failures. Built with
  `export.embed` for the glyf-js customer-facing demo app.

## Run an example

From an example directory:

```bash
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean --zip
```

Each example keeps its local DuckDB file under that example's `target/`
directory.

Open `target/glyf/site/index.html`.

## Seed data

The seeds of `finance_metrics`, `product_analytics` and `clanker_insights` are synthetic and are
written by `seed_data.py`. The generator is seeded, so it rewrites the same
files byte for byte:

```bash
uv run python examples/seed_data.py
```

Change the shapes at the top of that file, run it, and commit the CSVs to
change what the examples show. The metric tiles in the dashboards quote figures
from the data, so check them after regenerating.
