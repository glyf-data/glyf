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
- **Chart SQL reaches the warehouse through the dbt profile, over ADBC.**
  *Decided, not yet built: DuckDB is the only backend that ships today.* SQL
  execution is already pluggable — backends register with `@sql_executor` in
  `glyf.execution.base`, and `execution.backend` selects one — but every
  registered backend is DuckDB and nothing reads `profiles.yml`, so a project
  whose models live in Snowflake or BigQuery cannot render charts. The compiled
  SQL is not the problem: `ref()` resolution already substitutes the manifest's
  `relation_name`, so it is warehouse-qualified before it is executed.

  A `dbt` backend will resolve `profiles.yml` and connect over ADBC, one driver
  per warehouse type behind an optional extra. ADBC because
  `adbc-driver-manager` is already a runtime dependency and returns Arrow, which
  is what `QueryResult` holds — a warehouse executor is then the same shape as
  the DuckDB one. The alternative, driving dbt's own adapters, was rejected:
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
