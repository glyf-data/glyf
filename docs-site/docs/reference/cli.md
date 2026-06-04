# CLI Reference

The CLI entry point is:

```bash
glyf
```

When working from this repository, use:

```bash
uv run glyf
```

## High-level commands

| Command | Purpose |
| --- | --- |
| `glyf init` | Scaffold glyf config, starter chart, and dashboard files. |
| `glyf doctor` | Check whether a project is ready for glyf workflows. |
| `glyf build` | Run the full glyf artifact pipeline and export a static site. |
| `glyf serve` | Serve the exported static dashboard site locally. |

## Low-level commands

| Command | Purpose |
| --- | --- |
| `glyf list` | List discovered ggsql project files. |
| `glyf validate` | Validate discovered files and manifest refs. |
| `glyf render` | Generate compiled SQL and chart artifacts. |
| `glyf dashboard` | Generate static dashboard HTML from rendered chart artifacts. |
| `glyf export` | Copy generated outputs into a publish-ready static site folder. |

## Shared options

Most commands support:

| Option | Description |
| --- | --- |
| `--project-dir`, `--project`, `-p` | Path to a dbt project. Defaults to the current directory. |
| `--config` | Path to `glyf.yml`. Defaults to `PROJECT/glyf.yml` if present. |

## Recommended workflow

For a new dbt project, scaffold starter files first:

```bash
glyf init --project-dir path/to/dbt_project
```

Then run dbt and build the exported site:

```bash
uv run glyf doctor --project-dir examples/simple_dbt
uv run glyf build --project-dir examples/simple_dbt --zip
uv run glyf serve --project-dir examples/simple_dbt
```

`glyf` is artifact-driven, not dbt-runtime-driven. Run dbt first so the
manifest and relations exist before you call `glyf`.

## Low-level control

Use the lower-level commands when you want to debug or script specific pipeline
steps:

```bash
uv run glyf validate --project-dir examples/simple_dbt
uv run glyf render --project-dir examples/simple_dbt
uv run glyf dashboard --project-dir examples/simple_dbt
uv run glyf export --project-dir examples/simple_dbt --clean --zip
```

## Example Output

<div className="cliReferenceExamples">

Run dbt first so `target/manifest.json` and project relations exist:

```bash title="Prepare dbt artifacts"
uv run dbt build --project-dir examples/simple_dbt --profiles-dir examples/simple_dbt
```

### `init`

Use `init` inside a dbt project to create the standard glyf config, starter `.ggsql` file, and dashboard YAML.

```bash title="Command"
glyf init
```

Example prompts:

```text title="Prompts"
Starter chart name [monthly_revenue]:
Starter dashboard name [executive]:
dbt model ref for the starter chart [fct_revenue]:
Starter chart title [Monthly Revenue]:
Starter chart type [line]:
```

Example output:

```text title="Output"
Initialized glyf in .
✓ wrote glyf.yml
✓ ensured visualisations/
✓ wrote visualisations/monthly_revenue.ggsql
✓ ensured dashboards/
✓ wrote dashboards/executive.yml

Next steps:
  dbt build
  glyf doctor
  glyf build
  glyf serve
```

### `doctor`

Use `doctor` to check whether the dbt project has the required config, manifest, chart files, dashboard files, and output directories.

```bash title="Command"
uv run glyf doctor --project-dir examples/simple_dbt
```

Example output:

```text title="Output"
Project: examples/simple_dbt
[OK] uv: uv executable found
[OK] config: loaded glyf.yml
[OK] dbt_project.yml: found dbt_project.yml
[OK] manifest.json: found target/manifest.json
[OK] visualisations: found 5 .ggsql file(s)
[OK] dashboards: found 1 dashboard YAML file(s)
[OK] visualisation files: 5 .ggsql file(s) discovered
[OK] dashboard files: 1 dashboard YAML file(s) discovered
[OK] output directory: found target/glyf
[OK] compiled directory: found target/glyf/compiled
[OK] charts directory: found target/glyf/charts
[OK] dashboards output directory: found target/glyf/dashboards
[OK] site directory: found target/glyf/site
```

### `list`

Use `list` to see the `.ggsql` files, dashboard YAML files, and dbt models discovered from the manifest.

```bash title="Command"
uv run glyf list --project-dir examples/simple_dbt
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
uv run glyf validate --project-dir examples/simple_dbt
```

Example output:

```text title="Output"
Validation passed
✓ validated project structure
✓ loaded manifest
✓ validated GGSQL files (5)
✓ validated dashboard specs (1)
✓ validated dashboard chart refs
```

### `render`

Use `render` to compile chart SQL, execute queries, and write chart artifacts.

```bash title="Command"
uv run glyf render --project-dir examples/simple_dbt
```

Example output:

```text title="Output"
✓ discovered charts (5)
✓ compiled SQL
✓ executed SQL
✓ rendered PNG/SVG
✓ wrote metadata
```

### `build`

Use `build` for the normal artifact pipeline after dbt has already run.

```bash title="Command"
uv run glyf build --project-dir examples/simple_dbt --zip
```

Example output:

```text title="Output"
✓ validated project
✓ rendered chart artifacts
✓ generated dashboard HTML
✓ exported static site
```

Use `--verbose` to show the detailed low-level output from `validate`,
`render`, `dashboard`, and `export`:

```bash title="Command"
uv run glyf build --project-dir examples/simple_dbt --zip --verbose
```

Verbose output:

```text title="Output"
Running validate
Validation passed
✓ validated project structure
✓ loaded manifest
✓ validated GGSQL files (5)
✓ validated dashboard specs (1)
✓ validated dashboard chart refs
Running render
✓ discovered charts (5)
✓ compiled SQL
✓ executed SQL
✓ rendered PNG/SVG
✓ wrote metadata
Running dashboard
✓ discovered dashboard configs
✓ loaded chart artifacts
✓ generated dashboard HTML
✓ generated index page
✓ wrote bundle manifest
Running export
✓ copied dashboard HTML
✓ copied chart artifacts
✓ copied compiled SQL
✓ wrote site assets
✓ wrote public bundle manifest
✓ exported site to target/glyf/site
✓ wrote zip archive target/glyf/glyf-site.zip
```

### `dashboard`

Use `dashboard` after `render` to generate dashboard HTML pages from the rendered artifacts and dashboard YAML.

```bash title="Command"
uv run glyf dashboard --project-dir examples/simple_dbt
```

Example output:

```text title="Output"
✓ discovered dashboard configs
✓ loaded chart artifacts
✓ generated dashboard HTML
✓ generated index page
✓ wrote bundle manifest
```

`dashboard` also writes `target/glyf/bundle.json`, a local artifact manifest
that describes dashboards, chart metadata, generated paths, and internal
artifact locations for tools such as Glyf Studio, embedded viewers, or cloud
services.

### `export`

Use `export` to copy the generated dashboard, chart artifacts, compiled SQL, and static assets into the publish-ready site directory.

```bash title="Command"
uv run glyf export --project-dir examples/simple_dbt --clean --zip
```

Example output:

```text title="Output"
✓ copied dashboard HTML
✓ copied chart artifacts
✓ copied compiled SQL
✓ wrote site assets
✓ wrote public bundle manifest
✓ exported site to target/glyf/site
✓ wrote zip archive target/glyf/glyf-site.zip
```

`export` writes `target/glyf/site/bundle.json`, a public-safe bundle manifest
for the exported static site. It omits internal normalized data and Vega spec
paths so the exported site does not advertise non-public artifacts.

</div>

## `init` options

| Option | Description |
| --- | --- |
| `--clean` | Replace starter chart/dashboard files selected by the prompts. Keeps existing `glyf.yml`. |
| `--chart-name` | Filename stem for the starter `.ggsql` file. |
| `--dashboard-name` | Filename stem for the starter dashboard YAML file. |
| `--model-name` | dbt model name used in the starter `ref()`. |
| `--chart-title` | Title label for the starter chart. |
| `--chart-type` | Starter chart type: `line`, `bar`, `scatter`, `area`, or `pie`. |

## `export` options

| Option | Description |
| --- | --- |
| `--clean` | Delete the previous site export before copying. |
| `--zip` | Create `target/glyf/glyf-site.zip`. |

## `build` options

| Option | Description |
| --- | --- |
| `--clean`, `--no-clean` | Clean the previous site export before copying. Enabled by default. |
| `--zip` | Create `target/glyf/glyf-site.zip`. |
| `--verbose`, `-v` | Show detailed output from `validate`, `render`, `dashboard`, and `export`. |

## `serve` options

| Option | Description |
| --- | --- |
| `--host` | Host interface to bind. Defaults to `127.0.0.1`. |
| `--port` | Port to bind. Defaults to `8000`. Use `0` to choose an available port. |

Serve the exported site locally:

```bash
uv run glyf build --project-dir examples/simple_dbt
uv run glyf serve --project-dir examples/simple_dbt
uv run glyf serve --project-dir examples/simple_dbt --host 127.0.0.1 --port 8080
```
