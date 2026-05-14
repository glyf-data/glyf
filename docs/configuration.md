# Configuration

`dbt_charts.yml` is optional. If it is missing, defaults are used.

```yaml
visualisations_path: visualisations
dashboards_path: dashboards
output_path: target/ggsql
compiled_path: target/ggsql/compiled
charts_path: target/ggsql/charts
dashboards_output_path: target/ggsql/dashboards
site_path: target/ggsql/site

render:
  formats:
    - svg
    - png
  default_width: 800
  default_height: 400

dashboard:
  theme: light
  embed_charts: true
  show_compiled_sql: true
```

Paths are resolved relative to the dbt project root.

Use a custom config file:

```bash
uv run dbt-charts render --config dbt_charts.yml
```

Use a config with another project:

```bash
uv run dbt-charts render --project-dir examples/simple_dbt --config examples/simple_dbt/dbt_charts.yml
```
