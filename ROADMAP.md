# Roadmap

This roadmap captures optional future directions after the core `dbt-charts`
workflow is usable:

```bash
dbt build
dbt-charts render
dbt-charts dashboard
dbt-charts export
```

The current priority is to keep the core CLI deterministic and static-first.
Milestone 12 is therefore not a single required delivery milestone. It is a set
of advanced feature candidates that can be picked up independently once the
release baseline is stable.

## Milestone 12: Advanced Features

### 12A: Serve Mode

Add a local preview server so users can inspect generated dashboards without
manually opening files from `target/ggsql/site`.

Proposed command:

```bash
uv run dbt-charts serve
```

Expected behavior:

- serve the generated static site from `target/ggsql/site`
- print the local URL in the terminal
- validate that the site exists before starting
- keep the server lightweight and local-only by default
- avoid introducing a full hosted dashboard service

Why this matters:

Local preview is the most useful next advanced feature because it improves the
developer loop without changing the chart compiler, dashboard generator, or
static export model.

Suggested first scope:

- add a `serve` CLI command
- use Python standard-library HTTP serving if sufficient
- support `--project-dir`, `--host`, and `--port`
- fail clearly when dashboard output has not been generated

Acceptance criteria:

- `uv run dbt-charts serve` serves an existing generated site
- the command prints a clickable local URL
- missing output produces a clear instruction to run `dbt-charts dashboard`
- tests cover default path resolution and missing-site behavior

### 12B: Watch Mode

Add a local development loop that regenerates chart and dashboard artifacts when
source files change.

Proposed command:

```bash
uv run dbt-charts watch
```

Expected behavior:

- watch `.ggsql` files, dashboard YAML files, and `dbt_charts.yml`
- rerun the smallest useful generation step when files change
- report failures without stopping the watch process
- keep the implementation simple enough for local development use

Why this matters:

Watch mode makes authoring visualisations faster, especially when paired with
serve mode. It should come after serve mode because a live preview target makes
file watching more valuable.

Suggested first scope:

- watch project visualisation and dashboard directories
- rerun `render` and `dashboard` on change
- debounce rapid file updates
- leave dbt model execution outside the watch loop unless explicitly requested

Acceptance criteria:

- editing a `.ggsql` file regenerates chart artifacts
- editing a dashboard YAML regenerates the dashboard site
- syntax or execution errors are shown in the terminal
- the process continues watching after a failed regeneration

### 12C: Richer Dashboard Layout

Expand dashboard layout options while preserving the current YAML-driven static
dashboard model.

Possible capabilities:

- sections and groups
- configurable grid columns
- chart sizing hints
- dashboard-level filters as static metadata
- markdown text blocks
- summary metric tiles

Why this matters:

The current static dashboard output is useful for simple demos. Richer layout
support would make the generated dashboards more practical for repeated internal
reporting and stakeholder review.

Suggested first scope:

- extend dashboard YAML with optional layout metadata
- keep defaults backward compatible
- avoid a drag-and-drop editor
- keep generated HTML static and inspectable

Acceptance criteria:

- existing dashboard YAML files continue to render unchanged
- new layout fields are documented
- examples demonstrate at least two dashboard layout patterns
- tests cover layout parsing and generated HTML structure

### 12D: Cloud Publish Adapters

Add optional helpers that publish generated static dashboard artifacts to common
static hosting targets.

Possible targets:

- GitHub Pages
- Netlify
- Vercel
- S3-compatible storage
- internal static hosting directories

Why this matters:

`dbt-charts` already produces static artifacts. Publish adapters would make it
easier to move those artifacts from local development into team-accessible
locations without turning the project into a hosted service.

Suggested first scope:

- document a generic publish contract
- add a local filesystem publish adapter first
- add GitHub Pages guidance before deeper cloud integrations
- keep provider-specific dependencies optional

Acceptance criteria:

- generated site artifacts can be copied to a configured publish directory
- publish output is deterministic and easy to inspect
- provider-specific failures produce actionable messages
- documentation explains CI usage

### 12E: Interactive Charts

Support interactive chart output for dashboards while retaining static export as
the default behavior.

Possible capabilities:

- tooltips
- zoom and pan
- legend filtering
- selection-driven highlighting
- embedded Vega-Lite JSON

Why this matters:

Interactive charts can make dashboards more useful for local exploration and
review. This should remain optional so the core output stays portable and easy
to publish.

Suggested first scope:

- expose a small set of interaction options in `.ggsql`
- preserve PNG/SVG/static HTML generation where possible
- document which interactions are supported by each export format
- add examples for tooltip and legend interactions

Acceptance criteria:

- users can opt into supported interactions from chart definitions
- unsupported interactions fail with clear validation errors
- static output remains the default
- docs explain output-format tradeoffs

### 12F: dbt Docs Integration

Link generated dashboards back to dbt documentation metadata where available.

Possible capabilities:

- model descriptions
- column descriptions
- source descriptions
- owner or maturity metadata
- links to dbt docs pages

Why this matters:

Dashboards become more trustworthy when users can trace charts back to dbt
models, sources, and documented definitions.

Suggested first scope:

- read descriptions and metadata already present in `target/manifest.json`
- show model and source context in generated dashboard pages
- optionally link to a configured dbt docs base URL
- avoid depending on a running dbt docs server

Acceptance criteria:

- chart pages can show model/source descriptions from the manifest
- missing docs metadata does not break dashboard generation
- configuration supports an optional dbt docs base URL
- tests cover manifest metadata extraction

### 12G: Lineage-Aware Dashboards

Use dbt manifest lineage to show which models and sources feed each dashboard or
chart.

Possible capabilities:

- list upstream models for each chart
- list source dependencies
- flag charts affected by a changed model
- group dashboard content by dbt domain or model family

Why this matters:

Lineage helps users understand dashboard impact and trust. It also creates a
foundation for smarter validation and change review in CI.

Suggested first scope:

- extract direct dependencies for each chart query where possible
- display dependencies in dashboard metadata
- add validation output that summarizes dashboard dependencies
- avoid building a full lineage visualization in the first pass

Acceptance criteria:

- each chart can report known dbt model and source dependencies
- dashboard output includes dependency metadata
- unresolved or unknown dependencies are reported clearly
- tests cover simple `ref()` and `source()` dependency extraction

### 12H: Scheduled Report Generation

Document and support scheduled static report generation for CI and automation
systems.

Possible capabilities:

- GitHub Actions schedules
- cron-compatible command examples
- timestamped exports
- zipped dashboard artifacts
- retention guidance

Why this matters:

Scheduled generation turns `dbt-charts` into a repeatable reporting tool without
requiring a server process.

Suggested first scope:

- provide a GitHub Actions workflow example
- support deterministic export directories
- document how to run dbt build before chart generation
- reuse the existing export command where possible

Acceptance criteria:

- docs include a complete scheduled-report workflow example
- generated artifacts can be archived from CI
- failures are visible in CI logs
- examples avoid provider lock-in where practical

## Recommended Priority

The best next advanced feature after the release baseline is:

```bash
uv run dbt-charts serve
```

Serve mode should be prioritized before watch mode because it improves the
preview experience with minimal architectural risk. Once serve mode is stable,
watch mode can build on it to provide an automatic local feedback loop:

```bash
uv run dbt-charts watch
```

Suggested order:

1. 12A: Serve mode
2. 12B: Watch mode
3. 12C: Richer dashboard layout
4. 12F: dbt docs integration
5. 12G: Lineage-aware dashboards
6. 12H: Scheduled report generation
7. 12D: Cloud publish adapters
8. 12E: Interactive charts

This order favors features that improve the local development workflow and
static dashboard trust before adding provider-specific publishing or richer
runtime behavior.
