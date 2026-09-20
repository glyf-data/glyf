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
  provenance: local

privacy:
  pii_columns: []
  on_pii: deny
  redaction: mask
  scan: true
  strict: false

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
| `execution.target` | profile's own | `dbt` backend only. Render against a target other than the profile's default. Overrides `DBT_TARGET`; `--target` overrides both. The target names the warehouse identity the queries run as. See [building one artifact per audience](../guides/where-to-run-builds.md#building-one-artifact-per-audience). |
| `execution.profiles_dir` | dbt's search order | `dbt` backend only. Where to find `profiles.yml`, instead of `DBT_PROFILES_DIR`, the project directory, then `~/.dbt`. |
| `execution.mode` | `full` | `full` runs the queries and draws the charts. `validate` runs each with `limit 0` and draws nothing. See [validate mode](#validate-mode). |
| `execution.max_rows` | unset | Fail the build if a chart's query returns more than this many rows. Unset means no limit. |
| `export.provenance` | `local` | Where the build provenance record goes. `local` keeps it in `build.json` and the local `bundle.json`; `public` also publishes it, which publishes the warehouse identity and the selectors. See [what a build records about itself](#what-a-build-records-about-itself). |
| `export.row_data` | `include` | `minimal` publishes only the columns each chart encodes. See [publishing only what the chart shows](#publishing-only-what-the-chart-shows). `exclude` publishes rendered PNGs only, with no chart rows, Vega specs or compiled SQL. See [publishing without the rows](#publishing-without-the-rows). |

## Privacy

| Key | Default | Description |
| --- | --- | --- |
| `privacy.pii_columns` | `[]` | Column names to treat as PII in addition to those the dbt project tags. For aliases and expressions dbt does not model. |
| `privacy.on_pii` | `deny` | What a build does when a chart's query returns a PII column. `deny` fails the build; `redact` rewrites the column's values before anything reads them. See [keeping PII out of a chart](#keeping-pii-out-of-a-chart). |
| `privacy.redaction` | `mask` | How `redact` rewrites a value. `mask` keeps a hint (`j***@acme.com`); `hash` keeps only distinctness, for grouping by a sensitive key. |
| `privacy.scan` | `true` | Read the values of unclassified string columns and warn when they look like email addresses, phone numbers, card numbers or social security numbers. Warns only and never redacts. See [the value scan](#the-value-scan). |
| `privacy.strict` | `false` | Fail the build on a scan warning instead of printing it. |

## Render

| Key | Default | Description |
| --- | --- | --- |
| `render.renderer` | `altair` | Python renderer used for chart artifacts. |
| `render.formats` | `[svg, png]` | Chart artifact formats. Only `svg` and `png` are accepted; anything else fails config loading. |
| `render.default_width` | `800` | Chart width in pixels when a `.ggsql` file sets none. |
| `render.default_height` | `400` | Chart height in pixels when a `.ggsql` file sets none. |
| `render.max_marks` | `500000` | The most marks a chart may draw. See [how many marks a chart may draw](#how-many-marks-a-chart-may-draw). `null` removes the bound. |
| `render.downsample` | `false` | Reduce a large line or area chart to the marks its pixels can show. See [downsampling a large chart](#downsampling-a-large-chart). |
| `render.downsample_over` | `25000` | Rows a chart may return before downsampling applies to it. |

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
compiled SQL, and stops. No images, data files, dashboards or export are
written. A renamed column fails the build; a slow or expensive query costs
almost nothing. `execution.mode: validate` does the same thing from `glyf.yml`.

Because no rows leave the warehouse, validate mode is also the right thing to
run on infrastructure outside it. See
[where to run builds](../guides/where-to-run-builds.md).

## Bounding a query with `max_rows`

`execution.max_rows` fails a build when a chart's query returns more rows than
the cap:

```text
visualisations/events.ggsql returned more than 50000 rows. Aggregate the query
or raise execution.max_rows; glyf will not draw a chart from part of a result.
```

It errors rather than truncating. A chart drawn from an arbitrary slice of a
result looks completely plausible and is wrong.

Both bounds are applied in SQL, so the warehouse sends less over the wire. They
bound transfer and render time, **not** what the warehouse scans: an aggregate
is computed in full whatever limit follows it.

## Row order

A chart whose query has no `ORDER BY` is drawn from whatever order the
warehouse returned, which is not the same order next build. glyf orders those
rows itself, by the columns the chart encodes and then by the rest to break
ties, so a rebuild of unchanged data produces the same artifact.

There is no setting. A query that orders itself is never reordered, and a query
that does not expresses no order to override. See
[Row order](../guides/visualisation-syntax.md#row-order) for which chart types
report it.

## How many marks a chart may draw

`render.max_marks` fails a chart that would draw more marks than the renderer
can survive:

```text
visualisations/events.ggsql would draw 612000 marks, more than the 500000 glyf
will render. The renderer holds every mark in memory at once and the whole
build dies when it runs out, so glyf stops first. Aggregate the query, or raise
render.max_marks if this machine can take it.
```

`render.max_marks` has a default, so the bound applies to a project that has
configured nothing. glyf draws a chart by handing every mark to a renderer that
holds them all in memory at once, and when that memory runs out the process is
killed rather than returning an error. What reaches you then is an out-of-memory
abort and a stack trace from inside the renderer, with no chart named, no build
output, and in a multi-chart build no way to tell which query was responsible.
The budget turns that into a normal build failure that names the chart.

The count is the number of rows the query returns. For a `histogram` or a
`boxplot` that is more than the marks on the picture, and it is still the number
that matters: the renderer receives every row to bin or summarise.

`500000` is the largest single-series chart observed to render, on one machine.
The real limit belongs to the renderer's memory rather than to glyf, so it
moves with the platform and the chart. Raise it if your builds are fine above
it; lower it if a build has ever died without an error. Setting it to `null`
removes the bound:

```yaml
render:
  max_marks: 750000
```

## Downsampling a large chart

An 800-pixel-wide chart cannot show more than 800 distinguishable positions
across its x axis, but glyf draws a mark per row regardless. `render.downsample`
reduces a line or area chart to the marks its pixels can actually show:

```yaml
render:
  downsample: true
  downsample_over: 25000
```

A chart returning more than `downsample_over` rows keeps four rows per pixel
column: the leftmost, the rightmost, the highest and the lowest. Those are
exactly the rows a line renderer's output depends on in that column. Everything
dropped would have been painted over by something else. Measured on a 120,000
row chart, that is 1,675 marks instead of 120,000, and a 0.5 MB SVG instead of
35 MB.

The bin count comes from the chart's own width and is not configurable: one bin
per horizontal pixel is what makes the reduction invisible, and fewer bins is
where it starts to move the line.

### Why it is opt-in

A downsampled chart's artifacts carry fewer rows than the query returned. That
is a decision about what gets published, in the same territory as
[`export.row_data`](#publishing-only-what-the-chart-shows), so glyf does not
make it on a project's behalf.

### What downsampling keeps

The rows kept are rows the warehouse returned, never values computed from them.
Averaging each column would redraw the series: a noisy one loses its envelope,
and an outlier narrower than one column disappears into the mean of its
neighbours. Keeping the highest and lowest row of each column preserves the
vertical extent of every column exactly.

### What it applies to

| | downsampled |
| --- | --- |
| `line`, `area` over `downsample_over` rows | yes |
| `scatter` | no; binning snaps its marks to a lattice and drops the density it exists to show |
| `bar`, `pie` | no; one mark per category rather than one per pixel column |
| `histogram`, `boxplot`, `heatmap` | no; a histogram and a boxplot are computed from every row, and a heatmap has one mark per cell |
| a non-numeric x axis | no; bins over a string axis would be bins over the warehouse's row order |

A build says which charts it downsampled, and says when it could not:

```text
! visualisations/events.ggsql: 120000 rows downsampled to 1675 marks (M4, 800 bins)
! visualisations/scatter.ggsql: 60000 rows, downsampling applies to line and area
  charts only; rendering all 60000 marks
```

The second warning means downsampling was asked for, could not be given, and
the build is about to draw every mark. A chart with a string x axis reports the
column and its type, so the fix, casting the axis in the chart's SQL, is visible
from the message.

Downsampling is recorded in [`build.json`](#what-a-build-records-about-itself)
as `downsampled_to` beside the chart's `row_count`, because the published
artifacts carry the former rather than the latter.

### Which bound to reach for

| | `execution.max_rows` | `render.downsample` | `render.max_marks` |
| --- | --- | --- | --- |
| does what | fails the build | reduces the marks | fails the chart |
| bounds | what the query returns | what the chart draws | what the renderer is asked to draw |
| default | unset | off | `500000` |
| applied | in SQL, before the rows travel | after execution | after downsampling, before rendering |
| exists to | keep an unbounded query from running away | keep a large chart small without changing it | keep an oversized chart from killing the build |

They compose in that order. A project that sets `max_rows` below `max_marks`
will never see the mark budget, which is a reasonable way to run: the query
fails earlier and more cheaply. With downsampling on, the budget applies to
what is left after it, so a chart that downsampling brings under the budget
builds normally.

## Keeping PII out of a chart

A chart's query result is classified once, after it runs and before anything
reads it: the renderer, the local data file, a dashboard filter. Every backend
is covered by the same rule. A column is PII if either of two sources
says so:

1. **The dbt project.** A column tagged in `schema.yml` with `meta: {pii: true}`
   or `tags: [pii]`, on any model or source the chart's SQL reads through
   `ref()` or `source()`. glyf reads this from `target/manifest.json`; there is
   no second registry to maintain.
2. **`glyf.yml`.** The `privacy.pii_columns` list, for columns dbt does not
   model, such as an alias or a computed expression.

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
has its columns, so CI catches a charted email with no rows moved.

Under `redact`, the column is rewritten instead:

| | `redaction: mask` | `redaction: hash` |
| --- | --- | --- |
| `jane@acme.com` | `j***@acme.com` | `2c1a…` (16 hex characters) |
| `+1 555 0100` | `+***` | `9f0e…` |
| `NULL` | `NULL` | `NULL` |
| distinct inputs | may collide | stay distinct |

Every value becomes a string, whatever it was. `hash` is for grouping by a
sensitive key without showing it; it is unsalted, so a value someone can guess
is not hidden from them. It keeps the key groupable rather than secret.

**What this cannot see.** Classification is by column name. A query that
writes `select email as contact` returns a column called `contact`, which no
manifest tags; that is what `privacy.pii_columns` is for. Matching is
case-insensitive, and a tag on a model the chart does not read does not apply.
Column lineage through arbitrary SQL is out of scope.

### The value scan

Behind the classification sits a safety net for the alias nobody listed and
the column nobody tagged. With `privacy.scan: true`, the default, a full build
samples up to 200 values of every string column the classification did not
cover, spread across the result, and warns when they read like:

| | matches | does not match |
| --- | --- | --- |
| email addresses | `jane@acme.example` | `j***@acme.example`, `x@y` |
| phone numbers | `+1-555-010-0123`, `(415) 555-0100`, `+14155550100` | `4155550100` (a bare run of digits is an ID until proven otherwise), dates |
| card numbers | 13-19 digits passing the Luhn check, and only when most of the column does, since one random digit string in ten passes Luhn | an order-id column with a few accidental hits |
| social security numbers | `123-45-6789` | area `000`, `666` or `9xx`, group `00`, serial `0000`, ranges never issued |

A whole value has to match; an address inside a sentence does not count. One
match in twenty sampled values is enough to warn, except for card numbers,
which need a majority.

```text
! signups.ggsql column 'contact' looks like email addresses (200 of 200
sampled values) but is not classified as PII. Tag it in schema.yml or list it
in privacy.pii_columns
```

**The scan warns and never redacts.** A fuzzy match is a guess, and a guess that
silently rewrote a column would produce a wrong chart. Classify the column
instead: the deterministic policy above then takes over, and the scan skips it.
`privacy.strict: true` fails the build on a warning instead, for teams that
would rather classify than be surprised.

The scan reads rows, so it runs in full builds only; [validate mode](#validate-mode)
moves no rows and runs the classification alone. `glyf build` prints scan
warnings even without `--verbose`. Numeric columns are not scanned: a phone
number stored as an integer has already lost the shape the detectors look for.

The primary control is the warehouse role the build runs with: grant it the
marts a dashboard needs and not the raw or staging layers, and there is nothing
for glyf to catch.

## What a build records about itself

Every render writes `target/glyf/build.json`: what went into the artifacts and
how they were made. Which queries ran is in the warehouse's own logs, and who
opened a dashboard is in the edge's.

The record carries the identity the queries ran as, the dbt run the artifacts
were built from, the selection, the privacy policy and what it did, and per
chart a row count and a digest of the SQL. The
[bundle reference](./bundle.md#build) lists every field.

It is **not published by default**. `export.provenance: public` embeds it in
the published `bundle.json` as well, and should be set only for an internal
site: the record names the warehouse identity and the selectors.

```bash
glyf build --log-json /var/log/glyf/builds.jsonl
```

`--log-json` appends the same record to a file as
[JSON Lines](https://jsonlines.org), one object per build, for a log collector
to ship. Failed builds are appended too, with `outcome: "failed"` and the
error. `build.json` describes the
artifact currently in the output directory; the log file is the history.

Nothing verifies the record, so it is not evidence. Retention and tamper
resistance belong to whoever runs the pipeline;
see [where to run builds](../guides/where-to-run-builds.md).

## Publishing only what the chart shows

By default a chart ships more than it draws. An interactive chart inlines its
whole result set into the dashboard page, every column the query returned,
whether or not a `VISUALISE` role binds it. A static SVG labels each mark with
the exact values it was drawn from.

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
| values | never rounded or transformed |
| compiled SQL | published, as under `include`; it names the columns, not their values |
| `source(chart, field)` filters | resolved, as under `include`; you asked for that column's values by name |
| `target/glyf/data/*.data.json` | keeps every column locally; it is never published in any mode |

Axis ticks, legend entries and titles keep their labels: they describe text
the page already shows. The published `bundle.json` reports
`security.row_data: "minimal"`.

## Publishing without the rows

A normal export publishes the data along with the pictures, and not obviously:
an interactive chart inlines its whole Vega specification, rows included, into
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
| `source(chart, field)` filters | left empty, since a resolved list is a `SELECT DISTINCT` of a column |
| hand-written `values:` lists | published, being configuration you wrote rather than data |

The published `bundle.json` reports `security.row_data: "excluded"` and leaves
`artifacts.svg` and `artifacts.compiled_sql` null, so a consumer is not sent to
a file that was deliberately withheld.

Both modes bound what the artifacts contain. Access control is whatever your
host provides.
