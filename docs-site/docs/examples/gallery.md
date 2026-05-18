# Examples Gallery

Each example is a small dbt project with seeds, models, ggsql visualisations, and dashboard YAML.

## Gallery

| Example | Best for | Includes |
| --- | --- | --- |
| [Simple dbt](simple-dbt.md) | Learning the shortest path from dbt project to dashboard. | Revenue charts, dashboard YAML, local DuckDB profile. |
| [Sales dashboard](sales-dashboard.md) | Reporting patterns for revenue by time, channel, and region. | Line, bar, and regional charts. |
| [Product analytics](product-analytics.md) | Product usage and activation metrics. | Area, bar, and scatter examples. |
| [Finance metrics](finance-metrics.md) | Finance KPI dashboard patterns. | Bookings, expense, and margin charts. |
| [Screenshots](screenshots.md) | Planning the future visual gallery. | Capture backlog and screenshot guidelines. |

## Run an example

From an example directory:

```bash
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean --zip
```

Open:

```text
target/ggsql/site/index.html
```

## Use examples as templates

Copy the shape, not necessarily the data:

- Keep dbt models under `models/`.
- Keep chart SQL under `visualisations/`.
- Keep dashboard definitions under `dashboards/`.
- Keep `dbt_charts.yml` at the project root for repeatable local and CI commands.
