# Architecture

`glyf` is an artifact-driven CLI. dbt remains responsible for model execution and
manifest production. `glyf` consumes those artifacts, resolves chart SQL, renders
chart assets, and generates static dashboard output.

## System Flow

```text
dbt project
   ↓
dbt manifest.json + built relations
   ↓
ggsql parser
   ↓
ref()/source() resolver
   ↓
SQL executor
   ↓
chart renderer
   ↓
artifact store
   ↓
dashboard generator
   ↓
static site export
```

## Current Responsibilities

- Rust-first core engine:
  - ggsql parsing
  - manifest extraction
  - dbt ref/source resolution
- Python wrapper and orchestration:
  - CLI commands
  - SQL execution (DuckDB today; see Design Decisions)
  - chart rendering
  - dashboard YAML loading
  - dashboard macro loading and evaluation
  - static HTML generation and export

This split is intentional. Stable parsing and resolution logic fits the Rust core.
Project-local extensibility and output orchestration still fit Python better.

## Dashboard Rendering

Dashboards are generated server-side in Python; there is no client-side
framework and no build step for the user.

- `loader.py` parses dashboard YAML into a typed spec.
- Chart artifacts rendered earlier are read from `target/glyf/charts/`.
- Macros (`ui.*`, `alert.*`, `ai.*`, `time.*`, plus project-local custom macros)
  resolve into typed components in `components.py`; the registry lives in
  `macros/`.
- `DashboardRenderer` renders the componentised Jinja templates.
- `AssetManager` copies `dashboard.css` and bundled fonts next to the output.
- `Theme` names the dashboard theme (`light` or `dark`, chosen in YAML);
  `chart_theme.py` re-tints chart SVG and Vega output to match.
- `glyf export` copies dashboards, charts, compiled SQL, and assets into
  `target/glyf/site/`.

```text
src/glyf/dashboard/
  loader.py          dashboard YAML → spec
  components.py      typed components (text, label/value, list, badge, link, alert)
  macros/            built-in macro namespaces and the registry
  renderer.py        DashboardRenderer, RenderedDashboard
  assets.py          AssetManager
  theme.py           Theme
  chart_theme.py     chart re-tinting for dark dashboards
  generator.py       orchestration: generate_dashboards()
  templates/
    dashboard.html.j2
    index.html.j2
    components/      chart_card, component_card, toolbar, source_drawer, ai_panel, icons
  assets/
    dashboard.css    one stylesheet: semantic `.glyf-*` classes over CSS custom properties
```

## Styling Rules

- Styling lives in `dashboard.css`, never in large inline blocks in templates.
- Templates use stable semantic classes (`.glyf-card`, `.glyf-toolbar`, …) and
  CSS custom properties as the token layer, so themes override variables
  rather than components.
- Generated output stays static and inspectable: HTML, one CSS file, chart
  artifacts. Users never need Node, and no browser-side framework is part of
  the renderer contract. Tooling such as Tailwind may be used at development
  time to produce `dashboard.css`, but only the compiled CSS ships.

## Design Decisions

- **Visualisations live in separate `.ggsql` files**, not inside dbt model SQL.
  Models stay focused on transformation; charts are a presentation layer.
- **dbt integration reads `target/manifest.json`** rather than reimplementing
  dbt compilation. `glyf` never runs dbt; it consumes the artifacts dbt
  already produced.
- **glyf is a compile-time renderer, not a data engine.** A chart is a picture
  of an aggregate, and the `SELECT` is where aggregation belongs. The ceiling is
  real and measurable: one chart at 1k rows is a 0.26 MB SVG, at 10k 2.55 MB, at
  100k 25.7 MB — SVG spends a DOM node per mark, and `embed_charts` inlines that
  markup into the dashboard page, so the page *is* that size. The same chart as
  PNG at 100k rows is 644 KB, because raster does not care how many marks it
  drew. A line chart is around 2,000 pixels wide, so a million points is 500
  marks per pixel column: nothing a reader can see, at a cost everyone pays.

  Altair carries a 5,000-row cap, but `altair/utils/save.py` disables it while
  saving because vl-convert needs the data inlined — which is exactly the path
  glyf renders through, so nothing bounded the input at all. `execution.max_rows`
  is that bound, and it fails rather than truncating: a chart drawn from part of
  a result is indistinguishable from a correct one. Rendering large results
  faster is a separate question from rendering them at all, and is being handled
  as its own investigation.

- **Chart SQL reaches the warehouse through the dbt profile.**
  *Shipped for DuckDB, Trino, Snowflake and BigQuery.* SQL execution is
  pluggable — backends register with `@sql_executor`
  in `glyf.execution.base`, and `execution.backend` selects one. The compiled
  SQL is not the problem: `ref()` resolution already substitutes the manifest's
  `relation_name`, so it is warehouse-qualified before it is executed.

  The `dbt` backend resolves `profiles.yml` and connects where the target
  points, one driver per warehouse type behind an optional extra. The wire
  protocol is per warehouse: ADBC where a driver exists (Snowflake and
  BigQuery ship on it; Postgres would too), because
  `adbc-driver-manager` is already a runtime dependency and returns Arrow, which
  is what `QueryResult` holds — a warehouse executor is then the same shape as
  the DuckDB one. Trino has no ADBC driver — it speaks its own HTTP protocol —
  so its executor uses the official `trino` client, the same one dbt-trino
  ships on. The alternative, driving dbt's own adapters, was rejected:
  it would make `dbt-core` a runtime dependency of every install, DuckDB-only
  ones included, and would couple `glyf render` to `dbt.adapters.factory`, which
  is not a public API. `profiles.yml` is. The cost of that choice is auth
  coverage — ADBC handles password and key-pair, but not every SSO or cloud IAM
  flow — and if a real project hits that wall, a dbt-adapter backend is the
  answer, added beside this one rather than instead of it. `glyf` still never
  runs dbt.

- **Parsing and resolution are in Rust, orchestration in Python.** The Rust
  crate owns ggsql validation, manifest extraction, and `ref()`/`source()`
  resolution, exposed through `glyf._core`. Python keeps the CLI, execution,
  rendering, dashboards, and file IO, and preserves its public API when logic
  moves into the crate.

- **PII is classified where dbt already classifies it, and enforced at one
  point.** A column is PII when the dbt project tags it in `schema.yml`
  (`meta: {pii: true}` or a `pii` tag — the Rust manifest extraction reads
  both) on a model or source the chart reads, or when `glyf.yml` lists it. No
  parallel registry. Enforcement happens on the `QueryResult` right after
  execution and before anything reads it, so all backends, validate mode, the
  local data file and dashboard filters see the same outcome. The default is
  to fail the build rather than redact: a redacted encoded column is a
  meaningless chart, so refusing loudly is the honest response, and `redact`
  exists for grouping by a sensitive key. Classification is by column name —
  an alias slips past the manifest and needs listing in `glyf.yml`; column
  lineage through arbitrary SQL is out of scope. Behind the list, a regex
  scan over sampled values of unclassified string columns catches the alias
  nobody listed — and it only ever warns (`privacy.strict` turns that into a
  failure), because a fuzzy match that silently redacted would be a wrong
  chart with a clean conscience. This is defense-in-depth behind the
  warehouse role the build runs with, not a substitute for it.

- **Per-audience restriction is one build per warehouse identity, not a
  filter inside the artifact.** A published dashboard is a static file, so it
  is one materialised view of the data for everyone who opens it; per-viewer
  filtering belongs to a hosted tier, not to a file. `--target` therefore
  selects the dbt profile target, which names the identity the queries run
  as, and the warehouse's own policies decide what comes back — glyf inherits
  that ceiling and never widens it. `--select` decides which dashboards a
  build produces, because a chart whose table the identity cannot read fails
  the build rather than coming back empty, and `--output-dir` keeps the
  results apart. Only the first is a control; the other two are mechanics.
  Consequently a build's output directory is made to describe that build —
  chart artifacts and dashboard HTML from a wider earlier build are pruned,
  the manifest lists only what was generated, and export mirrors rather than
  merges — because export copies a directory, and a stale file there is
  another audience's data published under this audience's URL.

- **A build records itself; only one of the four audit questions is glyf's.**
  Which queries ran belongs to the warehouse's logs, who opened a dashboard to
  the edge's, and who copied the numbers out to nobody. What went into an
  artifact and how it was made is glyf's alone, and was being thrown away.
  `render_project` therefore writes `build.json` beside the other artifacts --
  identity, dbt manifest time, selection, privacy policy and its effect, per
  chart a row count and an SQL digest -- and the local `bundle.json` embeds
  it. Publishing it is opt-in (`export.provenance`), because the record names
  the warehouse identity and the selectors. `--log-json` appends the same
  record, failures included, to a JSON Lines file: the manifest describes the
  artifact that exists now, and only an external append-only log is a history.
  The record is descriptive, exactly like the `security` block -- nothing
  verifies it, and saying so is part of shipping it.
