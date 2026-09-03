# Changelog

All notable changes to `glyf` will be documented in this file.

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
