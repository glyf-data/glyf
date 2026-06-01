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
  - DuckDB execution
  - chart rendering
  - dashboard YAML loading
  - dashboard macro loading and evaluation
  - static HTML generation and export

This split is intentional. Stable parsing and resolution logic fits the Rust core.
Project-local extensibility and output orchestration still fit Python better.

## Dashboard Rendering System

Today the dashboard renderer is server-side HTML generation:

- dashboard YAML is parsed into a typed dashboard spec
- rendered chart artifacts are loaded from `target/glyf/charts/`
- Python macros resolve into typed dashboard components
- `DashboardRenderer` coordinates componentized Jinja templates
- `AssetManager` copies the generated dashboard CSS asset
- export copies dashboards, charts, compiled SQL, and assets into
  `target/glyf/site/`

The renderer now follows a clearer component and asset system. Styling lives in
`dashboard.css` and templates use stable semantic classes instead of embedding a
large inline style block in each dashboard.

### Target Direction

The current direction is:

- keep rendering in Python
- keep output as static HTML
- avoid runtime frontend frameworks
- avoid making end users depend on Node
- move styling out of large inline templates
- use stable semantic classes instead of utility-class-heavy templates

That means a server-rendered component system, not a client-rendered app shell.

### Layout

```text
src/glyf/dashboard/
  renderer.py
  assets.py
  theme.py
  templates/
    dashboard.html.j2
    index.html.j2
    components/
      chart_card.j2
      component_card.j2
      toolbar.j2
      source_drawer.j2
      ai_panel.j2
  assets/
    dashboard.css
    themes/
      light.css
      dark.css
      corporate.css
  tokens/
    theme.json
```

### Renderer Interfaces

```python
class DashboardRenderer:
    def render(self, spec: DashboardSpec) -> RenderedDashboard:
        ...


class AssetManager:
    def prepare(self, output_dir: Path, *, single_file: bool) -> DashboardAssets:
        ...


class Theme:
    name: str
    stylesheet_path: str
    variables_path: str | None = None
```

The main idea is:

- `DashboardRenderer` owns template rendering
- `AssetManager` owns linked vs inlined asset behavior
- `Theme` defines which variable overrides are active

## Styling Strategy

Avoid putting long-lived styling directly into giant HTML templates.

Instead:

- define stable semantic classes such as `.glyf-card`, `.glyf-toolbar`,
  `.glyf-alert`, `.glyf-inspector`
- keep layout and component CSS in `dashboard.css`
- keep theme overrides in separate theme files
- use CSS custom properties as the token layer

Example direction:

```css
:root {
  --glyf-color-bg: #ffffff;
  --glyf-color-bg-muted: #f7f7f7;
  --glyf-color-border: #e5e5e5;
  --glyf-color-text: #111111;
  --glyf-color-text-muted: #666666;

  --glyf-space-2: 8px;
  --glyf-space-3: 12px;
  --glyf-space-4: 16px;

  --glyf-font-size-label: 14px;
  --glyf-font-size-body: 12px;
  --glyf-font-size-title: 16px;
}

.glyf-card {
  padding: var(--glyf-space-4);
  border: 1px solid var(--glyf-color-border);
  background: var(--glyf-color-bg);
}
```

Use semantic tokens first. Theme files should mostly override variables, not
replace whole component styles.

## Single-File vs Default Output

Default output should remain:

- HTML files
- CSS assets
- chart artifacts

That keeps the output inspectable and easy to host.

A future portable mode is still useful:

- `glyf dashboard --single-file`
- or `glyf build --single-file`

In that mode, CSS can be inlined for people who want one portable HTML artifact.

This should apply to dashboard/site generation, not to chart rendering itself.

## Tailwind Position

Tailwind can be used later as an internal authoring tool, but not as a runtime
requirement for end users.

Acceptable:

- use Tailwind during development to generate `dashboard.css`
- ship only compiled static CSS with `glyf`

Not acceptable:

- requiring `npm install` for normal `glyf build`
- generating dashboards through a browser-side framework
- shipping utility-class-heavy templates as the public renderer contract

The external contract should remain semantic classes and static assets.

## Future Theme Support

Theme switching should happen at the dashboard generation layer, for example:

```bash
glyf dashboard --theme corporate
glyf build --theme corporate
```

This belongs to dashboard generation and site export, not to the SQL/chart
rendering step.

The long-term goal is:

- one stable HTML structure
- one stable component CSS layer
- multiple variable-driven themes
- optional single-file export for portability
