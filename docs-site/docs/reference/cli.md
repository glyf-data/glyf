# CLI Reference

The CLI entry point is:

```bash
dbt-charts
```

When working from this repository, use:

```bash
uv run dbt-charts
```

## Commands

| Command | Purpose |
| --- | --- |
| `dbt-charts doctor` | Check whether a project is ready for dbt-charts workflows. |
| `dbt-charts list` | List discovered ggsql project files. |
| `dbt-charts validate` | Validate discovered files and manifest refs. |
| `dbt-charts render` | Generate compiled SQL and chart artifacts. |
| `dbt-charts dashboard` | Generate static dashboard HTML from rendered chart artifacts. |
| `dbt-charts export` | Copy generated outputs into a publish-ready static site folder. |
| `dbt-charts serve` | Serve the generated static dashboard site locally. |

## Shared options

Most commands support:

| Option | Description |
| --- | --- |
| `--project-dir`, `--project`, `-p` | Path to a dbt project. Defaults to the current directory. |
| `--config` | Path to `dbt_charts.yml`. Defaults to `PROJECT/dbt_charts.yml` if present. |

## Common workflow

```bash
uv run dbt-charts doctor --project-dir examples/simple_dbt
uv run dbt-charts list --project-dir examples/simple_dbt
uv run dbt-charts validate --project-dir examples/simple_dbt
uv run dbt-charts render --project-dir examples/simple_dbt
uv run dbt-charts dashboard --project-dir examples/simple_dbt
uv run dbt-charts export --project-dir examples/simple_dbt --clean --zip
```

## Example Output

<div className="cliReferenceExamples">

Run dbt first so `target/manifest.json` and project relations exist:

```bash title="Prepare dbt artifacts"
uv run dbt build --project-dir examples/simple_dbt --profiles-dir examples/simple_dbt
```

### `doctor`

Use `doctor` to check whether the dbt project has the required config, manifest, chart files, dashboard files, and output directories.

```bash title="Command"
uv run dbt-charts doctor --project-dir examples/simple_dbt
```

Example output:

```text title="Output"
Project: examples/simple_dbt
[OK] uv: uv executable found
[OK] config: loaded dbt_charts.yml
[OK] dbt_project.yml: found dbt_project.yml
[OK] manifest.json: found target/manifest.json
[OK] visualisations: found 5 .ggsql file(s)
[OK] dashboards: found 1 dashboard YAML file(s)
[OK] visualisation files: 5 .ggsql file(s) discovered
[OK] dashboard files: 1 dashboard YAML file(s) discovered
[OK] output directory: found target/ggsql
[OK] compiled directory: found target/ggsql/compiled
[OK] charts directory: found target/ggsql/charts
[OK] dashboards output directory: found target/ggsql/dashboards
[OK] site directory: found target/ggsql/site
```

### `list`

Use `list` to see the `.ggsql` files, dashboard YAML files, and dbt models discovered from the manifest.

```bash title="Command"
uv run dbt-charts list --project-dir examples/simple_dbt
```

Example output:

```text title="Output"
Project: examples/simple_dbt

GGSQL files (5)
  - visualisations/revenue.ggsql
  - visualisations/revenue_area.ggsql
  - visualisations/revenue_by_region_bar.ggsql
  - visualisations/revenue_scatter.ggsql
  - visualisations/revenue_share_pie.ggsql

Dashboard YAML files (1)
  - dashboards/executive.yml

Manifest: target/manifest.json
Models (1)
  - fct_orders -> "simple_dbt"."main"."fct_orders"
```

### `validate`

Use `validate` before rendering to catch parser errors, unresolved dbt refs or sources, and dashboard references to missing chart names.

```bash title="Command"
uv run dbt-charts validate --project-dir examples/simple_dbt
```

Example output:

```text title="Output"
Validation passed
  GGSQL files: 5
  Dashboard YAML files: 1
  Manifest: present
```

### `render`

Use `render` to compile chart SQL, execute queries, and write chart artifacts.

```bash title="Command"
uv run dbt-charts render --project-dir examples/simple_dbt
```

Example output:

```text title="Output"
✓ discovered charts (5)
✓ compiled SQL
✓ executed SQL
✓ rendered PNG/SVG
✓ wrote metadata
```

### `dashboard`

Use `dashboard` after `render` to generate dashboard HTML pages from the rendered artifacts and dashboard YAML.

```bash title="Command"
uv run dbt-charts dashboard --project-dir examples/simple_dbt
```

Example output:

```text title="Output"
✓ discovered dashboard configs
✓ loaded chart artifacts
✓ generated dashboard HTML
✓ generated index page
```

### `export`

Use `export` to copy the generated dashboard, chart artifacts, compiled SQL, and static assets into the publish-ready site directory.

```bash title="Command"
uv run dbt-charts export --project-dir examples/simple_dbt --clean --zip
```

Example output:

```text title="Output"
✓ copied dashboard HTML
✓ copied chart artifacts
✓ copied compiled SQL
✓ wrote site assets
✓ exported site to target/ggsql/site
✓ wrote zip archive target/ggsql/dbt-charts-site.zip
```

</div>

## `export` options

| Option | Description |
| --- | --- |
| `--clean` | Delete the previous site export before copying. |
| `--zip` | Create `target/ggsql/dbt-charts-site.zip`. |

## `serve` options

| Option | Description |
| --- | --- |
| `--host` | Host interface to bind. Defaults to `127.0.0.1`. |
| `--port` | Port to bind. Defaults to `8000`. Use `0` to choose an available port. |

Preview a generated dashboard:

```bash
uv run dbt-charts serve --project-dir examples/simple_dbt
uv run dbt-charts serve --project-dir examples/simple_dbt --host 127.0.0.1 --port 8080
```
