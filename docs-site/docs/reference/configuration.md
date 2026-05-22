# Configuration Reference

`dbt_charts.yml` controls paths, rendering, and dashboard output.

## Paths

| Key | Default | Description |
| --- | --- | --- |
| `visualisations_path` | `visualisations` | Directory containing `.ggsql` files. |
| `dashboards_path` | `dashboards` | Directory containing dashboard YAML files. |
| `output_path` | `target/ggsql` | Root output directory. |
| `compiled_path` | `target/ggsql/compiled` | Compiled SQL output directory. |
| `charts_path` | `target/ggsql/charts` | Rendered chart artifact directory. |
| `dashboards_output_path` | `target/ggsql/dashboards` | Generated dashboard HTML directory. |
| `site_path` | `target/ggsql/site` | Exported static site directory. |

## Render

| Key | Default | Description |
| --- | --- | --- |
| `render.formats` | `[svg, png]` | Chart artifact formats. |
| `render.default_width` | `800` | Default chart width. |
| `render.renderer` | `altair` | Python renderer hook used for chart artifact generation. |
| `render.default_height` | `400` | Default chart height. |

## Dashboard

| Key | Default | Description |
| --- | --- | --- |
| `dashboard.theme` | `light` | Dashboard visual theme. |
| `dashboard.embed_charts` | `true` | Embed chart artifacts into dashboard HTML. |
| `dashboard.show_compiled_sql` | `true` | Show compiled SQL in generated dashboard pages. |
