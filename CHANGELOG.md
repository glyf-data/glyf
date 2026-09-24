# Changelog

All notable changes to `glyf` will be documented in this file.

## 0.18.0 - 2026-09-25

### Added

- `export.embed: true` publishes each drawn chart's Vega spec in the
  exported site, at `charts/<name>.vega.json`, and points `bundle.json` at
  it, so an application can draw the charts live with glyf-js: tooltips,
  its own theme, filters. `security.embedded_specs` says so. A spec carries
  the rows the chart was drawn from, only the encoded columns under
  `row_data: minimal`; `embed` with `row_data: exclude` is refused.
- A JSON Schema for `bundle.json`, version 1, at
  `schemas/bundle.v1.schema.json` and
  `glyfdata.com/schema/bundle.v1.schema.json`. Every bundle glyf writes is
  tested against it.
- Dashboard filters in `bundle.json` carry their `control`: `select`,
  `radio` or `toggle`.
- `examples/clanker_insights`: the customer-facing insights of a made-up AI
  agent platform, built with `export.embed` for the glyf-js demo at
  clanker.glyfdata.com.

### Fixed

- A KPI tile's change is rounded to the precision of the two numbers it
  compares: `89.9` against `92.3` reads `-2.4`, not `-2.3999999999999915`.
- The exported `bundle.json` lists the values of a `source(chart, field)`
  filter. They were empty, although the bundle reference promises them;
  under `row_data: exclude` they stay out, as they are rows.

## 0.17.0 - 2026-09-24

### Added

- `glyf diff` says when a chart's axes moved, before the marks that moved:
  `y axis 0–30.4k → 0–154k` when either end of the y range shifts by a
  tenth or more, and `x axis: 2026-04 added, 2025-04 dropped`. A rescaled
  axis moves every mark on the page; this says which part of a change is
  scale. The JSON report carries the ranges and the sentence.

### Changed

- glyf settles the ties a query's `ORDER BY` leaves. The query's other
  output columns are appended to its outermost `ORDER BY`, after the
  author's keys, so the order asked for holds and a `LIMIT` keeps the same
  rows every build. The compiled SQL shows the query as it ran; the build
  record hashes it as written, so upgrading is not a query change.
  `SELECT *` is settled after the rows come back instead, and a warehouse
  that refuses the tiebreak runs the query as written, with a warning.
  A chart whose rows tied may draw its tied rows in a new, now fixed,
  order the first time it is built with this version.

## 0.16.0 - 2026-09-24

### Added

- A dashboard filter takes `control`: `select` (the default dropdown),
  `radio` (a row of buttons, one value or All) or `toggle` (buttons that
  keep any number of values on; a chart keeps the rows matching any of
  them, and its chip reads `plan = Pro or Team`).
- Alerts take `trigger=`, the rule that raised them at build time. The
  card shows an "Auto-triggered" pill whose tooltip names the rule;
  `alert.threshold` sets it.

### Changed

- Status cards are a solid tint of their tone instead of a gradient.

### Fixed

- Dashboard and index pages escape text. The templates were never
  autoescaped, so a title, card text, a filter value or compiled SQL
  reached the page as markup; a `<script>` in any of them would run.

## 0.15.0 - 2026-09-24

### Added

- Every dashboard chart card has download (a PNG of the chart as shown,
  theme and filters included) and full-screen tools beside its type badge.
- A chart with `INTERACT zoom` gets a zoom lock and a reset. It starts
  locked, so scrolling the page no longer zooms the chart by accident.
- `metric` items take `delta` and `trend` (`up`, `down` or `flat`), shown
  in green, red or grey with an arrow, like a kpi tile.
- An alert macro given `metric=` renders as a status card led by the
  number; alerts, text and lists take a `note` footnote.
- `owner` in dashboard YAML names the owner shown under the header.

### Changed

- Headline numbers on kpi, metric and status cards are larger (40px).
- A dashboard filter reads as a label then a value: the field name is a
  muted segment and the selection is bold, with more room between filters.

### Fixed

- Points on the edge of a scatter chart are no longer cut in half when the
  chart zooms: its scales are padded.

## 0.14.0 - 2026-09-24

### Added

- A card a dashboard filter cannot touch is stamped "Not filtered" across
  its face, and a card the filter empties is stamped "No data", instead of
  only dimming.
- `toolbar.stars` in dashboard YAML sets the count the star button shows.

### Fixed

- A class that sets `display` no longer beats the `hidden` attribute,
  which had left an empty chip beside every chart-type badge.

- A dashboard's stylesheet link carries a hash of its contents, so a
  browser that cached an earlier stylesheet fetches the new one. Without it
  a rebuilt page could render with the old stylesheet: the lineage graph as
  black boxes, oversized filter icons, untinted tags.
- The filter select's icon is sized like every other control icon.

### Changed

- Lineage colours every column: sources grey, models blue, charts green.
- Lineage opens as a full-screen view with a "Back to dashboard" bar,
  rather than a window over the dashboard, so the graph has the page's
  width. Escape still closes it.

## 0.13.0 - 2026-09-23

### Dashboard

- Filters filter. A dashboard filter is now a select, and choosing a value
  redraws every chart whose rows carry the column, in the browser, from the
  rows the page already holds: a drawn chart from its Vega specification
  with the filter as a transform, a table by hiding rows, with a chip on
  the card naming the value. A kpi cannot be recomputed and a chart without
  the column cannot be filtered; both dim and say which filter does not
  apply, rather than sitting still and looking filtered. `filters[].charts`
  narrows a filter to named charts. It follows `export.row_data`: any column
  under `include`, encoded columns under `minimal`, labels only under
  `exclude`. Selections are not written to the URL. To make this possible
  every drawn chart now keeps its Vega specification
  (`data/vega/<name>.vega.json`, internal, never exported), not only
  interactive ones; the bundle's `artifacts.vega` reflects that.
- Every page has a light-and-dark switch in its top-right actions. The
  choice is remembered in the reader's browser, the frame follows at once,
  and charts follow too when `chart_theme` is `auto`: static SVGs get the
  same colour swaps the build applies for a dark dashboard, and interactive
  charts re-embed with the dark config.
- Lineage opens as a window over the dashboard rather than in place of the
  chart grid, with a close button and Escape. The Source drawer stays a
  drawer.
- A little colour, in the places that mean something: tags get a soft tint
  that is the same for the same word on every page, the visibility pill is
  green for public and amber for private, and the AI Summary button takes
  the accent.

## 0.12.0 - 2026-09-23

### Added

- Every dashboard has a **Lineage** button beside **Source**. It swaps the
  chart grid for a graph of the raw sources, the dbt models and the
  dashboard's charts, with a line for each read. Click a node to light
  everything upstream and downstream of it; hover for what a chart binds or
  which file a model is; drag to pan and scroll to zoom. The graph is built
  from the chart artifacts: at build time each chart's metadata records the
  models its SQL references and, from the manifest's `depends_on`, every
  model behind them back to the sources, so an exported site carries its
  lineage with no manifest. `dashboard.show_lineage: false` turns the view
  off, and `export.row_data: exclude` withholds it and the `lineage`
  metadata key, the way it withholds the compiled SQL.

## 0.11.0 - 2026-09-23

### Added

- `glyf mcp` serves a project to an AI agent over the Model Context Protocol
  on stdio, with the `mcp` extra (`glyf-core[mcp]`). Six tools, each built on
  a function the CLI already uses: `list_charts`, `list_dashboards`,
  `get_chart`, `impact`, `validate` (with `execute` for the `LIMIT 0` dry
  run) and `diff`. The server never runs a build and never fetches rows;
  its instructions tell the agent to call `impact` before proposing a model
  change and `validate` after editing a chart. `glyf validate`'s checks now
  live in `glyf.validation.validate_project`, which the command prints and
  the server returns.
- `glyf impact` says `listed by *` for a column a `VISUALISE *` table shows,
  instead of `in the SQL`.
- `glyf impact <target>` lists the charts and dashboards downstream of a dbt
  model (`fct_orders`), a source (`raw.orders`) or a column of either
  (`fct_orders.revenue`). A model or source answer is exact, from the
  resolved `ref()` and `source()` calls. A column answer says how sure it
  is on every line: a chart whose SQL names the column `reads` it, shown
  with the role it is drawn as or `in the SQL`; a chart that selects `*`, or
  whose SQL did not parse, `may read` it. `--json` prints the report for a
  script. Next to `glyf diff` it is the review a pull request wants: which
  charts a change reaches, and what moved in them. Underneath, the Rust
  core now records every column name a chart's SQL mentions and whether it
  selects `*`.
- `glyf validate --execute` runs each chart's SQL against the warehouse with
  `LIMIT 0` and checks the columns it returns against the chart's
  `VISUALISE` mappings, fetching no rows. Plain `glyf validate` reads files
  and cannot tell whether a query runs, so a renamed column surfaced only at
  `glyf build`; now it fails validation, naming the chart, with the
  warehouse's own message. `--target` picks the dbt profile target. This is
  the check `glyf build --validate` makes, without the rest of the build.

## 0.10.1 - 2026-09-23

### Fixed

- The macOS wheels are linked with room in the Mach-O header for Homebrew
  to rewrite the extension module's install name. `brew install glyf` at
  0.10.0 failed with `Updated load commands do not fit in the header`;
  0.9.0 had passed the same step by eight bytes. Nothing else changed; a
  PyPI or installer-script install of 0.10.0 was never affected.

## 0.10.0 - 2026-09-23

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

### KPI tile

- `DRAW kpi` shows one number as a tile: `VISUALISE revenue AS value,
  previous AS compare`. The query must return exactly one row. With a
  `compare` column the tile shows the difference, its direction and its
  share of the comparison; `LABEL compare => 'vs last week'` names it. A
  number reads with thousands separators, its precision untouched.

  ```sql
  SELECT active_users, lag(active_users) OVER (ORDER BY week) AS previous
  FROM weekly
  ORDER BY week DESC
  LIMIT 1

  VISUALISE active_users AS value, previous AS compare
  DRAW kpi
  LABEL title => 'Weekly active users'
  ```

  A kpi follows the table's path: `charts/<name>.kpi.html` beside the data
  JSON, a card on the dashboard, `fields.value`, `fields.compare` and
  `artifacts.kpi` in the bundle with `png` and `svg` null, and a diff by
  its rows that says `the value changed`. Unlike a table it is published
  under `export.row_data: exclude`, because one number is what a picture
  of it would show. The `product_analytics` example's hand-written
  "Weekly active users" tile is now a kpi computed from the data.

- In `glyf diff`, a table's or a kpi's before and after are written to
  `fragments/<name>.before.html` and `.after.html`, and `diff.json` points
  at them under `fragments`.

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
