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
  target: dev
  profiles_dir: ~/.dbt
  mode: full
  max_rows: 50000

render:
  renderer: altair
  formats:
    - svg
    - png
  default_width: 800
  default_height: 400

export:
  row_data: include

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
| `execution.backend` | `duckdb` | Where chart SQL runs. `duckdb` finds a database beside the project; `dbt` uses the project's `profiles.yml` and reaches its `duckdb`, `trino`, `snowflake` and `bigquery` targets (each warehouse needs its extra: `glyf-core[trino]`, `glyf-core[snowflake]`, `glyf-core[bigquery]`). |
| `execution.target` | profile's own | `dbt` backend only. Render against a target other than the profile's default. Overrides `DBT_TARGET`. |
| `execution.profiles_dir` | dbt's search order | `dbt` backend only. Where to find `profiles.yml`, instead of `DBT_PROFILES_DIR`, the project directory, then `~/.dbt`. |
| `execution.mode` | `full` | `full` runs the queries and draws the charts. `validate` runs each with `limit 0` and draws nothing — see [validate mode](#validate-mode). |
| `execution.max_rows` | unset | Fail the build if a chart's query returns more than this many rows. Unset means no limit. |
| `export.row_data` | `include` | `exclude` publishes rendered PNGs only — no chart rows, Vega specs or compiled SQL. See [publishing without the rows](#publishing-without-the-rows). |

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

## Validate mode

A normal `glyf build` executes every chart's query in full, because pulling the
data is what produces the charts. In CI that is usually waste: the question a
pull request asks is whether the SQL still runs and still binds the columns the
chart draws, not what the numbers are this morning.

```bash
glyf build --validate
```

Each query runs wrapped in `limit 0`, which returns the result's columns and no
rows. glyf checks that every column bound by `VISUALISE` is present, writes the
compiled SQL, and stops — no images, no data files, no dashboards, no export.
A renamed column fails the build; a slow or expensive query costs almost
nothing. `execution.mode: validate` does the same thing from `glyf.yml`.

Nothing is drawn, deliberately: a chart rendered from a sample looks exactly
like a real one and would be reviewed, or published, as if it were.

## Bounding a query with `max_rows`

`execution.max_rows` fails a build when a chart's query returns more rows than
the cap:

```text
visualisations/events.ggsql returned more than 50000 rows. Aggregate the query
or raise execution.max_rows; glyf will not draw a chart from part of a result.
```

It is a guardrail against an unbounded chart query, not a data policy, so it
errors rather than truncating — a chart drawn from an arbitrary slice of a
result looks completely plausible and is wrong.

Both bounds are applied in SQL, so the warehouse sends less over the wire. They
bound transfer and render time, **not** what the warehouse scans: an aggregate
is computed in full whatever limit follows it.

## Publishing without the rows

A normal export publishes the data along with the pictures, and not obviously:
an interactive chart inlines its whole Vega specification — rows included — into
the dashboard page, a static SVG carries each row in a per-mark accessibility
label, and `site/compiled/*.sql` names the warehouse tables the charts were
built from.

```yaml title="glyf.yml"
export:
  row_data: exclude
```

That publishes rendered PNG images and nothing else:

| | under `exclude` |
| --- | --- |
| chart artifacts | PNG only; no SVG is produced or published |
| interactive charts | rendered as a static PNG, with a build warning naming the chart |
| dashboard HTML | references the PNG; no inline SVG, no Vega spec, no SQL drawer |
| compiled SQL | kept in `target/glyf/compiled/` for you, not copied into the site |
| `source(chart, field)` filters | left empty — a resolved list is a `SELECT DISTINCT` of a column |
| hand-written `values:` lists | published, being configuration you wrote rather than data |

The published `bundle.json` reports `security.row_data: "excluded"` and leaves
`artifacts.svg` and `artifacts.compiled_sql` null, so a consumer is not sent to
a file that was deliberately withheld.

This is about what the artifacts contain, not about who can read them. Access
control is whatever your host provides.
