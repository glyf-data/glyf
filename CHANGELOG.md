# Changelog

All notable changes to `glyf` will be documented in this file.

## Unreleased

### Table chart

- `DRAW table` is the third glyf-only chart type and the first that is not
  drawn. A table is its rows: `VISUALISE` lists the columns to show, in
  order and without roles (`VISUALISE region, revenue`), or `VISUALISE *`
  for every column the query returns. `LABEL <column> => '...'` names a
  header, `CONFIG height` turns the card into a scroll area, and `INTERACT`
  is rejected; the dashboard sorts a table by clicking a column instead.

  ```sql
  SELECT account_id, plan, sessions
  FROM {{ ref('fct_account_sessions') }}
  ORDER BY sessions DESC
  LIMIT 10

  VISUALISE *
  DRAW table
  LABEL title => 'Most active accounts'
  ```

  The build writes `charts/<name>.table.html`, a plain `<table>` fragment,
  beside the usual data JSON and metadata, and never a PNG or an SVG. The
  bundle records the table's `fields.columns` and `artifacts.table`, with
  `png` and `svg` set to `null`. `glyf diff` judges a table by that fragment,
  which is byte-stable like a PNG, says `the table changed` with the row
  changes, and shows the two tables side by side; `diff.json` marks the
  entry `"table": true`.

  Two bounds come with it. `render.max_rows` (default `1000`) fails a table
  that would list more rows, naming the chart, the way `render.max_marks`
  does for a picture. And `export.row_data: exclude` fails a table at
  validation: a picture can be published without its rows and a table
  cannot. The `product_analytics` example gains a table of its ten most
  active accounts.

- A `VISUALISE` line that lists columns without roles under a chart with
  axes, or maps roles under `DRAW table`, now fails saying what that chart
  wanted instead: `bar maps each column to a role (x, y, color); write
  'region AS x', or DRAW table to list columns`.

### What moved, in the chart's terms

- `glyf diff` now explains a changed bar, line or area chart the way the
  chart draws it. It compares the two builds' rows one mark per x value and
  series and says what it finds, before the row changes: `bars: 12 gone
  (Partners)`, `points: 3 higher, 1 lower`. The report's "What moved" panel
  draws it: this build's marks in colour, the baseline's in grey behind them,
  and a box around every x value where a mark went, appeared or changed. A
  series the new build dropped stays in the legend with nothing under it.

  The pixel-level picture (every differing pixel in magenta) said where the
  picture changed and could not say why: a bar that shrank lit up at its old
  height and its new one. It is still written as `images/<chart>.diff.png`,
  and still shown for the charts the overlay cannot draw: a scatter (a
  number on x, nothing to box), a histogram, a boxplot, a heatmap, a pie, or
  any chart from a build under `export.row_data: exclude`.

  `diff.json` gains a `marks` object per changed chart, and chart metadata
  (`charts/<name>.json`) now records the `color` column and the chart's
  labels and size, which is what the overlay reads.

### Changed

- A chart's SQL is now read with [sqlparser-rs](https://github.com/apache/datafusion-sqlparser-rs),
  in the dialect of the warehouse the project runs on (DuckDB, Snowflake or
  BigQuery from the dbt profile; generic SQL otherwise). Two things follow.
  `glyf validate` and `glyf build` now print a warning, with a line and
  column, for SQL that does not parse: `! visualisations/revenue.ggsql: SQL
  did not parse as duckdb: Expected: end of statement, found: oops at Line:
  1, Column: 30`. It is a warning and never an error, because the warehouse
  is the judge of the SQL and a parser can lag a dialect; the build goes on
  and the warehouse reports the error if it is one. And the rule from 0.8.0,
  that glyf orders a chart's rows only when the query does not, reads the
  query's `ORDER BY` from the parsed statement rather than from a walk of
  ggsql's parse tree. Every chart in the example projects gets the same
  answer as before, and that is now a test.

  The `ggsql` and `tree-sitter` crates are no longer dependencies. GGSQL
  remains the file format.

- glyf now validates a chart's `VISUALISE`, `DRAW`, `INTERACT` and `CONFIG`
  lines itself, for every chart type. ggsql is the file format and still
  parses the SQL, but it no longer judges the chart block through a stand-in
  type (`pie` used to be shown to it as `bar`), so an error names the chart
  you wrote: `pie does not take a 'banana' mapping; it takes x, y, color`
  rather than `Layer 'bar' does not support the banana mapping`.

  One consequence: a mapping the renderer never drew, such as `AS size` on a
  scatter, used to pass validation and be silently ignored. It is now rejected
  with that message. `unsupported chart type` and `unsupported CONFIG key`
  errors list what is supported.

## 0.9.0 - 2026-09-22

### Visual diff

- `glyf diff --baseline <build>` compares this build's charts with an earlier
  build and reports what changed. A chart whose PNG has the same bytes is
  unchanged. Otherwise the two images are compared pixel by pixel, in the Rust
  core, and the chart is reported with the share of the picture that moved.

  Each changed chart says why, as far as the two builds record it: the query
  changed, the rows changed, the glyf version changed, or, when none of those
  did, the chart definition changed. Row changes are spelled out: `rows 48 →
  36`, `gone from department: Partners`, `sum of expenses 576,000 → 527,500
  (-8.4%)`.

  The report goes to `target/glyf/diff/`: `index.html` with each changed chart
  before, after and marked up, `summary.md` for a pull request comment, and
  `diff.json` for a script. `--fail-on-change` exits 1 when anything moved.
  The command prints each changed chart followed by what moved in its rows, so
  a CI log reads without downloading the report.
  `--threshold` and `--tolerance` loosen the comparison for builds rendered on
  different machines; both default to zero because glyf's renders are
  byte-stable since 0.8.0.

- `.github/workflows/visual-diff.yml` runs it on glyf's own example projects:
  the base branch and the pull request are built in one job, compared, and the
  summary is posted on the pull request.

### Fixed

- `QueryResult.from_arrow` accepted a pyarrow `RecordBatchReader` and then
  failed on the first `len()` or, when the result had a decimal column, inside
  decimal normalisation with `'RecordBatchReader' object has no attribute
  'column'`. A reader is now read in full, a `RecordBatch` becomes a one-batch
  table, and anything that is not Arrow-exportable is rejected with a
  `TypeError` at construction rather than a stray `AttributeError` later.

## 0.8.0 - 2026-09-20

A chart drew a different picture on every build when its query left the row
order undefined. It no longer does.


### Fixed

- A chart whose query has no `ORDER BY` could draw a different picture on every
  build from the same data. SQL returns rows in an undefined order unless the
  query asks for one, and for a stacked bar, a pie, a coloured scatter and a
  heatmap that order is part of the picture: the segment order, the slice
  order, which points are drawn on top, and the axes. Four of the seventeen
  charts in the example projects rendered a different image on each of four
  runs.

  glyf now orders the rows itself when the query does not, by the columns the
  chart encodes and then by the rest to break ties, and the build says which
  chart and which columns. A query that orders itself is never reordered, so a
  heatmap whose `ORDER BY weekday_number` puts Monday first still does. An
  `ORDER BY` inside a CTE, a subquery or a window function orders that rather
  than the chart's rows, and does not count.

  Chart artifacts are now byte-identical between independent builds of
  unchanged data, which is what lets a build be compared against the last one.

  The example projects now order the charts whose picture depends on it, so
  they show the practice and build without the warning.

## 0.7.0 - 2026-09-20

Three more chart types, two example projects rebuilt around them, and two
fixes: one to what `export.row_data: minimal` leaves in an SVG, and one to the
first chart a new project validates.


### Three more chart types

- `DRAW histogram` counts the rows in each bin of `x`. It takes no `y`
  mapping; `color` stacks the bars.
- `DRAW boxplot` draws the quartiles of `y` for each `x` value, with outliers
  as points.
- `DRAW heatmap` draws one cell per `x` and `y` pair, shaded by a numeric
  `color`. `tile`, ggsql's name for it, is accepted as an alias. Cells keep the
  order the query returns them in, so an `ORDER BY` decides the axis order.

  All three are part of ggsql's grammar and are validated by it like the
  existing types. A text column where one of them needs numbers fails the
  render with an error naming the column. `legend_filter` is rejected at
  validation for `boxplot` and `heatmap`, where a legend selection has nothing
  to bind to.

- `bundle.json` and a chart's metadata record `y` as `null` for a histogram.
  `bundle_version` stays `"1"`: no existing chart's entry changes.
- `glyf init --chart-type` still offers `line`, `bar`, `scatter`, `area` and
  `pie`. The starter query maps a date to a value, which is not the shape the
  new types draw.

### Examples

- `finance_metrics` and `product_analytics` run on twelve periods of synthetic
  data in place of six seed rows, and each adds a histogram, a boxplot and a
  heatmap. `finance_metrics` now uses all eight chart types. The seeds are
  written by `examples/seed_data.py`, which is seeded and reproducible, and a
  test fails if the committed CSVs drift from it.

### Fixed

- `export.row_data: minimal` left row values in a chart's SVG when the chart
  set `LABEL x_title` or `LABEL y_title`. Vega leads a mark's accessibility
  label with the axis title (`Month: 2026-03; Revenue: 1200; ...`), and glyf
  recognised a mark's label by the column name it expected it to start with,
  so a titled chart's labels were passed over and its values stayed in the
  SVG and in the dashboard page that inlines it. A mark is now told from an
  axis, legend or title by the role Vega gives the element, and a labelled
  element with no role is treated as a mark.

  A chart without axis titles was not affected. `export.row_data: exclude`
  was not affected: it publishes no SVG.

- A `LABEL` value in double quotes failed validation with `Parse tree contains
  errors` or `VISUALISE clause was not recognized`. ggsql reads single-quoted
  strings only, and glyf passed the line to it unchanged. Both quote styles
  now validate.

  This is the form `glyf init` writes and the quickstart shows, so the starter
  chart of a new project failed `glyf validate` until its quotes were changed
  by hand. The documentation tests now parse every chart the docs show.

## 0.6.0 - 2026-09-03

A chart too large to draw now fails with an error instead of killing the
build, and a large line or area chart can be reduced to the marks its pixels
can actually show.

### A chart that cannot be drawn fails like anything else

- `render.max_marks`, default `500000`, bounds what a chart may draw. Above it
  the build stops with an error naming the chart and what to change.

  Before this, it did not stop -- it died. glyf hands every mark to a renderer
  that holds them all in memory at once, and when that memory ran out the
  process was killed rather than returning an error: no build output, a stack
  trace from inside the renderer where a traceback should be, and in a
  multi-chart build no way to tell which query was responsible. A one-series
  line chart rendered at 500,000 rows and died above it.

  Unlike `execution.max_rows`, this applies to a project that has configured
  nothing, because the projects that hit it are the ones that never set a
  bound. The default is the largest chart observed to render on one machine;
  the real limit belongs to the renderer's memory, so raise it if your builds
  are fine above it, and `null` removes it.

### Downsampling a large line or area chart

- `render.downsample` reduces a line or area chart returning more than
  `render.downsample_over` rows (default `25000`) to four rows per pixel
  column: the leftmost, the rightmost, the highest and the lowest. Those are
  the rows a line renderer's output depends on in that column, so the picture
  does not change -- the vertical extent of every column is preserved exactly.
  On a 120,000 row chart that is 1,675 marks and a 0.5 MB SVG, against
  120,000 marks and 35 MB.

  The rows kept are rows the warehouse returned, never values computed from
  them. Averaging each column instead would redraw the series: a noisy one
  loses its envelope, and an outlier narrower than one column disappears into
  the mean of its neighbours.

  It is opt-in because a downsampled chart's artifacts carry fewer rows than
  the query returned, which is a decision about what gets published rather
  than one a build should make on a project's behalf.

- Scatter, bar and pie charts are not downsampled, and neither is a chart
  whose x axis is not numeric or temporal. Each says so rather than passing
  silently: downsampling asked for and not given matters more than the
  successful case, because the build is about to draw every mark.

- `build.json` records `downsampled_to` beside a chart's `row_count`, since
  the published artifacts carry the former.

### Also

- `bench/` holds the measurements behind both features -- render cost against
  mark count, where rendering stops working, and whether a downsampling
  strategy still draws the same chart. `make bench` runs the sweep; none of it
  runs in CI.
- A config error for a `privacy.*` or `render.*` boolean now names that
  section instead of reporting it as `dashboard.`.

## 0.5.0 - 2026-09-03

Charts now execute against a real warehouse, and a build can be told how much
of the data it is allowed to publish.

### Warehouse execution

- Chart SQL runs through the dbt profile the project already has, on DuckDB,
  Trino, Snowflake and BigQuery. Set `execution.backend: dbt` in `glyf.yml`
  and glyf resolves `profiles.yml` the way dbt does, honouring `env_var()`
  and `--target`. A profile naming an unsupported warehouse is reported as
  such rather than silently ignored.
- Trino, Snowflake and BigQuery drivers ship as extras: `glyf-core[trino]`,
  `glyf-core[snowflake]`, `glyf-core[bigquery]`.
- `glyf doctor` now checks the execution chain before a build does — the
  resolved backend, profile and target, whether the driver extra is
  installed, and a `select 1` against the warehouse itself.
- Added validate mode and a row guardrail: `--validate` binds columns without
  fetching rows, and `execution.max_rows` fails a build that would pull more
  than expected.

Trino runs against a service container in CI; Snowflake and BigQuery are
tested against fakes, which covers the SQL and the result mapping but not a
live account's auth flow. `glyf doctor` is the check to run against your own
warehouse first.

### Controlling what a build publishes

- `export.row_data: minimal` publishes only the columns a chart actually
  encodes, pruning both the inlined dataset and the row values SVG marks
  carry. `exclude` ships no row data at all.
- Columns can be classified as PII from dbt `meta: {pii: true}` or
  `tags: [pii]` in the manifest, and from `privacy.pii_columns` in
  `glyf.yml`. `privacy.on_pii: deny` fails the build; `redact` masks or
  hashes the values instead.
- A value scan samples unclassified string columns for email addresses,
  card numbers, phone numbers and social security numbers, and warns.
  `privacy.strict: true` turns those warnings into a failed build.
- `glyf build` accepts `--target`, `--select` and `--output-dir`, so one
  project can produce a different artifact per audience — a narrower
  warehouse role, a subset of dashboards, and its own output directory.
  `--select` takes `tag:NAME`, `name:NAME` or a bare dashboard name.
- Fixed three cases where a rebuild left stale artifacts behind: export
  merged into the destination instead of mirroring it, the bundle manifest
  listed dashboards that were never built, and `glyf dashboard` never pruned
  removed dashboards' HTML.

### Build records

- Every build writes `build.json` next to its artifacts: what ran, which
  charts, their row counts, a digest of each compiled statement, and any
  redactions or scan warnings. `--log-json` appends the same record to a
  JSON Lines log. The record stays local unless `export.provenance: public`
  puts it in the published bundle.

### Documentation

- New guides on what publishing exposes and where to run a build, including
  the threat model glyf does and does not address.
- Documented `bundle.json` as a versioned contract, and every `glyf.yml`
  block in the docs is now executed as a test so the documentation cannot
  drift from the config loader.

## 0.4.0 - 2026-08-29

- `toolbar.actions` in dashboard YAML now controls which of the share and
  visibility buttons render. It was validated but ignored before, so every
  dashboard showed both.
- Dropped `polars` and `pandas` as dependencies. Query results are Arrow
  tables end to end and charts are built from them directly, which halves the
  installed size (about 260 MB instead of 530 MB). `build_chart` and
  `QueryResult.from_dataframe` accept any dataframe that implements the Arrow
  PyCapsule interface — polars, pandas 2.2+, pyarrow, or a DuckDB relation —
  so passing your own frame still works; `to_polars()` and `to_pandas()`
  remain and import the library on demand.

## 0.3.0 - 2026-08-26

First release published to PyPI.

- Renamed the PyPI distribution to `glyf-core`; the `glyf` command and
  `import glyf` are unchanged. `pip install glyf-core` / `uv tool install
  glyf-core` are the supported install paths going forward.
- Fixed the release workflow: replaced the retired `macos-13` runner, build
  wheels for x86_64 and aarch64 Linux, Intel and Apple Silicon macOS, and
  x86_64 Windows, and attach a `checksums.txt` to every GitHub Release.
- Trimmed the source distribution to the package, Rust crate, tests, and
  top-level metadata (docs site and examples are no longer bundled).
- Fetch DuckDB results as Arrow via ADBC and split the executors into explicit
  modules; cast Arrow decimal columns to native numbers.
- Added dashboard spec validation to `glyf validate` and a `--verbose` mode for
  `glyf build`.
- Macro system enhancements: custom macros, macro-aware validation, and new
  macro examples; fixed `ui.list` rendering.
- Dashboard UI: dark mode, refresh time and tags from YAML, and assorted
  layout fixes; data and JSON moved out of the exported site.
- Added the `bundle.json` artifact with build metadata and an embedded
  analytics documentation page.
- Moved the repository to the `glyf-data` organisation and enforced
  conventional commit messages in CI.

## 0.2.0 - 2026-06-02

Dashboard rendering system redesign. Tagged as `v0.2.0`; no artifacts were
published because the release workflow failed on the retired `macos-13`
runner.

- Reworked generated dashboard HTML into a product-style static UI shell with a
  header, metadata bar, filter placeholder, toolbar actions, chart content,
  source drawer, AI Summary panel, and lookback modal placeholder.
- Split dashboard rendering into `DashboardRenderer`, `AssetManager`, theme
  metadata, componentized Jinja templates, and a shared `dashboard.css` asset.
- Moved compiled SQL out of individual chart cards and into the dashboard
  `Source` drawer.
- Added linked dashboard CSS assets under `target/glyf/assets` and exported
  static sites under `target/glyf/site/assets`.
- Added built-in AI Summary macros: `ai.summary`, `ai.insight`, and
  `ai.signal`.
- Updated dashboard YAML documentation with toolbar behavior, field
  definitions, built-in macros, custom macro guidance, and source drawer
  behavior.
- Refreshed generated example dashboard previews in the docs site.
- Updated dashboard/export tests to cover linked assets, source drawer output,
  AI Summary macros, and the redesigned dashboard shell.

## 0.1.0 - 2026-05-31

Initial experimental alpha release.

- Typer CLI with `list`, `validate`, `render`, `dashboard`, `export`, and `doctor`.
- Project discovery for `.ggsql`, dashboard YAML, and dbt artifacts.
- dbt `ref()` and `source()` resolution from `target/manifest.json`.
- DuckDB SQL execution.
- Altair chart rendering to SVG and PNG.
- Static dashboard generation and exportable site folder.
- Optional `glyf.yml` project configuration.
- Example dbt projects and documentation.
- GitHub Release workflow for platform wheels and source distribution artifacts.
