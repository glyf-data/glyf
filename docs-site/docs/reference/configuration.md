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

privacy:
  pii_columns: []
  on_pii: deny
  redaction: mask

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
| `export.row_data` | `include` | `minimal` publishes only the columns each chart encodes — see [publishing only what the chart shows](#publishing-only-what-the-chart-shows). `exclude` publishes rendered PNGs only — no chart rows, Vega specs or compiled SQL — see [publishing without the rows](#publishing-without-the-rows). |

## Privacy

| Key | Default | Description |
| --- | --- | --- |
| `privacy.pii_columns` | `[]` | Column names to treat as PII in addition to those the dbt project tags. For aliases and expressions dbt does not model. |
| `privacy.on_pii` | `deny` | What a build does when a chart's query returns a PII column. `deny` fails the build; `redact` rewrites the column's values before anything reads them. See [keeping PII out of a chart](#keeping-pii-out-of-a-chart). |
| `privacy.redaction` | `mask` | How `redact` rewrites a value. `mask` keeps a hint (`j***@acme.com`); `hash` keeps only distinctness, for grouping by a sensitive key. |

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

## Keeping PII out of a chart

A chart's query result is classified once, after it runs and before anything
reads it — the renderer, the local data file, a dashboard filter — so every
backend is covered by the same rule. A column is PII if either of two sources
says so:

1. **The dbt project.** A column tagged in `schema.yml` with `meta: {pii: true}`
   or `tags: [pii]`, on any model or source the chart's SQL reads through
   `ref()` or `source()`. glyf reads this from `target/manifest.json`; there is
   no second registry to maintain.
2. **`glyf.yml`.** The `privacy.pii_columns` list, for columns dbt does not
   model — an alias, a computed expression.

```yaml title="glyf.yml"
privacy:
  pii_columns: [contact, contact_phone]
  on_pii: deny
```

Under `deny`, the default, a build whose chart returns a PII column fails and
names the column and where the classification came from:

```
visualisations/signups.ggsql returns a PII column: 'email' (tagged pii on
model dim_customers). Drop it from the query, or set privacy.on_pii: redact to
publish it masked.
```

This holds in [validate mode](#validate-mode) too: the `limit 0` result still
has its columns, so CI catches a charted email with no rows moved. Redacting an
encoded column would produce a meaningless chart, which is why refusing is the
default.

Under `redact`, the column is rewritten instead:

| | `redaction: mask` | `redaction: hash` |
| --- | --- | --- |
| `jane@acme.com` | `j***@acme.com` | `2c1a…` (16 hex characters) |
| `+1 555 0100` | `+***` | `9f0e…` |
| `NULL` | `NULL` | `NULL` |
| distinct inputs | may collide | stay distinct |

Every value becomes a string, whatever it was. `hash` is for grouping by a
sensitive key without showing it; it is unsalted, so a value someone can guess
is not hidden from them — it keeps the key groupable, not secret.

**What this cannot see.** Classification is by column name. A query that
writes `select email as contact` returns a column called `contact`, which no
manifest tags; that is what `privacy.pii_columns` is for. Matching is
case-insensitive, and a tag on a model the chart does not read does not apply.
Column lineage through arbitrary SQL is out of scope.

This is defense-in-depth. The primary control is the warehouse role the build
runs with: grant it the marts a dashboard needs and not the raw or staging
layers, and there is nothing for glyf to catch.

## Publishing only what the chart shows

By default a chart ships more than it draws. An interactive chart inlines its
whole result set into the dashboard page — every column the query returned,
whether or not a `VISUALISE` role binds it — and a static SVG labels each mark
with the exact values it was drawn from.

```yaml title="glyf.yml"
export:
  row_data: minimal
```

That keeps the interactivity and prunes the rest. The invariant: **a `minimal`
export contains no information beyond what the rendered chart displays.**

| | under `minimal` |
| --- | --- |
| Vega specs | `datasets` carries only the columns the `VISUALISE` clause encodes; tooltips, zoom and legend filtering keep working, because Vega needs nothing else |
| SVG marks | accessibility labels keep the field names and drop the values: `month; revenue` instead of `month: 2026-03; revenue: 79000` |
| values | never rounded or transformed — a chart that disagrees with the warehouse would be worse than the precision it reveals |
| compiled SQL | published, as under `include`; it names the columns, not their values |
| `source(chart, field)` filters | resolved, as under `include`; you asked for that column's values by name |
| `target/glyf/data/*.data.json` | keeps every column locally; it is never published in any mode |

Axis ticks, legend entries and titles keep their labels: they describe text
the page already shows. The published `bundle.json` reports
`security.row_data: "minimal"`.

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

Both modes are about what the artifacts contain, not about who can read them.
Access control is whatever your host provides.
