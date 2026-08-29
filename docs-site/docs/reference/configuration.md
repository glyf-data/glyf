# Configuration

`glyf.yml` is optional. When it is missing every key below takes its default.
Paths are resolved relative to the dbt project root, which is also where
`glyf init` writes the file.

```yaml
visualisations_path: visualisations
dashboards_path: dashboards
output_path: target/glyf
compiled_path: target/glyf/compiled
charts_path: target/glyf/charts
dashboards_output_path: target/glyf/dashboards
site_path: target/glyf/site

execution:
  backend: duckdb

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

## Paths

| Key | Default | Description |
| --- | --- | --- |
| `visualisations_path` | `visualisations` | Directory containing `.ggsql` files. |
| `dashboards_path` | `dashboards` | Directory containing dashboard YAML files. |
| `output_path` | `target/glyf` | Root output directory. |
| `compiled_path` | `target/glyf/compiled` | Compiled SQL output directory. |
| `charts_path` | `target/glyf/charts` | Rendered chart artifact directory. |
| `dashboards_output_path` | `target/glyf/dashboards` | Generated dashboard HTML directory. |
| `site_path` | `target/glyf/site` | Exported static site directory. |

## Execution

| Key | Default | Description |
| --- | --- | --- |
| `execution.backend` | `duckdb` | SQL execution backend. `duckdb` is the only supported value. |

## Render

| Key | Default | Description |
| --- | --- | --- |
| `render.renderer` | `altair` | Python renderer used for chart artifacts. |
| `render.formats` | `[svg, png]` | Chart artifact formats. Only `svg` and `png` are accepted; anything else fails config loading. |
| `render.default_width` | `800` | Chart width in pixels when a `.ggsql` file sets none. |
| `render.default_height` | `400` | Chart height in pixels when a `.ggsql` file sets none. |

## Dashboard

| Key | Default | Description |
| --- | --- | --- |
| `dashboard.theme` | `light` | Default dashboard theme, `light` or `dark`; a dashboard YAML `theme` overrides it. |
| `dashboard.embed_charts` | `true` | Inline chart artifacts into the dashboard HTML instead of linking them. |
| `dashboard.show_compiled_sql` | `true` | Show the `Source` drawer with each chart's compiled SQL. |

## Using another config file

Every command accepts `--config`:

```bash
glyf build --config glyf.yml
glyf build --project-dir examples/simple_dbt --config examples/simple_dbt/glyf.yml
```
