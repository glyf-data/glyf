# Configuration

`glyf.yml` is optional. If it is missing, defaults are used.

```yaml
visualisations_path: visualisations
dashboards_path: dashboards
output_path: target/glyf
compiled_path: target/glyf/compiled
charts_path: target/glyf/charts
dashboards_output_path: target/glyf/dashboards
site_path: target/glyf/site

render:
  renderer: altair
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

`dashboard.show_compiled_sql` controls whether the dashboard renders a `Source`
drawer for compiled SQL. SQL is no longer shown inline below each chart.

Paths are resolved relative to the dbt project root.

Use a custom config file:

```bash
uv run glyf render --config glyf.yml
```

Use a config with another project:

```bash
uv run glyf render --project-dir examples/simple_dbt --config examples/simple_dbt/glyf.yml
```
