# Dashboard YAML

Dashboard configs live in `dashboards/`.

This guide is the dashboard specification for glyf today: what fields exist,
which values are currently supported, how layout works, and where macros are
allowed to run.

## Minimal dashboard

The smallest dashboard only needs a name, title, and a list of chart names:

```yaml
name: executive
title: Executive Dashboard
description: Key business metrics generated from dbt models.
theme: dark
chart_theme: auto
tags:
  - finance
  - monthly

charts:
  - revenue
  - revenue_by_region_bar
  - revenue_share_pie
```

The filename stem of each `.ggsql` file becomes the chart name used here.
Dashboards that only use `charts` render as a responsive chart grid.

## Dashboard specification

### Toolbar

The toolbar is predefined. It is not a free-form plugin surface today.

Current YAML-supported values:

| Field | Supported values | Default |
| --- | --- | --- |
| `toolbar` | `false` or a mapping | enabled |
| `toolbar.enabled` | `true`, `false` | `true` |
| `toolbar.visibility` | `public`, `private` | `private` |
| `toolbar.actions` | `share`, `visibility` | both |

Default behavior:

```yaml
toolbar:
  visibility: private
  actions: [share, visibility]
```

Hide the toolbar completely:

```yaml
toolbar: false
```

Or keep it enabled but show only one action:

```yaml
toolbar:
  visibility: public
  actions:
    - share
```

Generated dashboards also render static controls for star, lookback, feedback,
and AI Summary. Those controls are part of the generated dashboard shell today;
they do not require YAML fields yet.

The dashboard header metadata shows the actual UTC build timestamp. `Refreshed`
is no longer a generic label; it reflects when `glyf dashboard` or `glyf build`
generated that HTML artifact.

### Summary

`summary` is an optional list of macro expressions rendered in the dashboard AI
Summary panel.

```yaml
summary:
  - "{{ ai.summary('Revenue moved up this month.') }}"
  - "{{ ai.insight('Starter churn needs review.', tone='warning') }}"
  - "{{ ui.label_value('Owner', 'Analytics Engineering') }}"

filters:
  - field: plan
    values: source(revenue_by_region_bar, region)
  - field: focus
    values: [revenue, margin, bookings]
```

Important boundary:

- `summary` entries must be full Jinja expressions
- they do not inject HTML directly
- they resolve to typed dashboard components before rendering

### Layout with example

Use `layout.columns` and `sections` when the dashboard needs grouped content,
mixed text/chart layouts, metric tiles, or custom column tracks.

```yaml
name: executive
title: Executive Dashboard
description: Key business metrics generated from dbt models.

toolbar:
  visibility: private
  actions: [share, visibility]

summary:
  - "{{ ui.label_value('Owner', 'Analytics Engineering') }}"
  - "{{ ui.badge('Updated', tone='info') }}"

layout:
  columns: 3

sections:
  - title: Revenue overview
    description: Revenue signals for the current sample period.
    columns: "30% 70%"
    items:
      - metric:
          label: Total revenue
          value: $7.6k
          note: Generated from fct_orders
      - markdown:
          title: Analyst note
          text: |
            Revenue charts are generated from dbt model outputs.
            Use this section to capture dashboard context.
      - chart: revenue
        title: Monthly revenue

  - title: Status
    columns: 2
    items:
      - component: "{{ echo('Refresh complete', 'Notification') }}"
      - component: "{{ ui.list(['Revenue', 'Margin', 'Bookings'], title='Metrics') }}"
      - chart: revenue_by_region_bar
```

`layout.columns` and `sections[].columns` accept:

- an integer column count like `3`
- a track string like `"30% 70%"`
- a list of track widths like `["1fr", "2fr"]`

`groups` is accepted as an alias for `sections`:

```yaml
groups:
  - title: Regional performance
    columns: 2
    charts:
      - revenue_by_region_bar
      - revenue_share_pie
```

### Item types

Inside each section, glyf currently supports four item kinds:

| Kind | Example | Notes |
| --- | --- | --- |
| `chart` | `- chart: revenue` | Can also be a bare string in `items` or `charts`. |
| `component` | `- component: "{{ ui.badge('Ready') }}"` | Macro expression returning a typed component. |
| `markdown` | `- markdown: "Text"` | Can be a string or mapping with `title` and `text`. |
| `metric` | `- metric: { label: Revenue, value: $7.6k }` | Optional `note` and `width`. |

## Field definitions

### Top-level fields

| Field | Description |
| --- | --- |
| `name` | Output filename stem. |
| `title` | Dashboard page title. |
| `description` | Optional intro text. |
| `theme` | Optional dashboard UI theme. Supported values: `light`, `dark`. |
| `chart_theme` | Optional chart appearance theme. Supported values: `auto`, `light`, `dark`. |
| `tags` | Optional list of short labels shown in the dashboard header. |
| `charts` | List of `.ggsql` chart names without the extension. |
| `filters` | Optional preset filter definitions shown in the dashboard control row. |
| `toolbar` | Optional toolbar configuration, or `false` to hide it. |
| `summary` | Optional list of macro expressions rendered in the AI Summary panel. |
| `layout` | Optional layout string or mapping. |
| `sections` | Optional grouped dashboard content. |
| `groups` | Alias for `sections`. |

### Layout fields

| Field | Description |
| --- | --- |
| `layout.columns` | Default grid columns for the dashboard body. Accepts an integer, a track string like `"30% 70%"`, or a list like `["1fr", "2fr"]`. |
| `filters[].field` | Label shown for the filter in the dashboard controls row. |
| `filters[].values` | Either a hardcoded list or `source(chart, field)` to read distinct values from rendered chart artifacts. |
| `sections[].title` | Optional section heading. |
| `sections[].description` | Optional section intro text. |
| `sections[].columns` | Optional section-level grid columns, using the same formats as `layout.columns`. |
| `sections[].charts` | Shorthand list of chart names for that section. |
| `sections[].items` | Ordered list of chart, component, markdown, and metric items. |

### Item fields

| Field | Description |
| --- | --- |
| `items[].chart` | Chart name, with optional `title` and `width`. |
| `items[].component` | Macro expression that returns a typed dashboard component. |
| `items[].markdown` | Markdown-style text block, either a string or a mapping with `title` and `text`. |
| `items[].metric.label` | Metric tile label. |
| `items[].metric.value` | Metric tile value. |
| `items[].metric.note` | Optional supporting text. |
| `items[].width` | Optional width hint on `chart`, `component`, or `metric` items. |

## Dashboard macros

Macros are allowed in two places today:

- `summary[]`
- `sections[].items[].component`

They must be full Jinja expressions such as:

```yaml
component: "{{ ui.label_value('Owner', 'Analytics Engineering') }}"
```

They are evaluated into typed component specs before the dashboard template
renders HTML.

For the grouped macro catalog, usage patterns, aliases, and custom macro rules,
see [Dashboard Macros](/docs/guides/dashboard-macros).

## Filters

Dashboard filters are currently static UI controls. They do not execute runtime
cross-filtering in the generated HTML yet, but they let you expose the intended
filter vocabulary directly from the dashboard spec.

Hardcoded values:

```yaml
filters:
  - field: plan
    values: [starter, growth, enterprise]
```

Artifact-backed values:

```yaml
filters:
  - field: plan
    values: source(activation_by_plan, plan)
```

`source(chart, field)` reads the distinct values from the normalized chart data
artifact written by `glyf render`. That keeps the filter list aligned with the
chart output instead of duplicating values in YAML.

## Tags

Use `tags` to control the badges shown under the dashboard description.

```yaml
name: executive
title: Executive Dashboard
tags:
  - finance
  - monthly
  - board
```

Tags must be a list of non-empty strings. Glyf preserves their order and
removes duplicates.

## Theme

Use `theme` to switch the generated dashboard shell between `light` and `dark`.
When omitted, the dashboard falls back to the configured default in `glyf.yml`.

```yaml
name: executive_dark
title: Executive Dashboard Dark
theme: dark
chart_theme: dark
charts:
  - revenue
  - revenue_by_region_bar
```

Current behavior:

- the dashboard shell, controls, source drawer, and AI panel use dark tokens
- `chart_theme: auto` follows the dashboard theme
- `chart_theme: dark` applies a dark chart surface, light labels, and dark-aware interactive Vega config
- `chart_theme: light` keeps charts in the default light style even inside a dark dashboard

Recommended setup:

```yaml
theme: dark
chart_theme: auto
```

Use `chart_theme: dark` when you want the plots themselves to match the dark
dashboard chrome. Use `chart_theme: light` when the shell should be dark but the
charts should stay in the default light rendering.

Implementation note:

- `glyf render` still produces one shared set of base chart artifacts under `target/glyf/charts/`
- `glyf dashboard` applies `chart_theme` when each dashboard HTML page is generated
- this means a light dashboard and a dark dashboard can reuse the same chart names in one project without overwriting each other's chart output
- the theme change is applied per dashboard page, not by rewriting the shared chart files on disk

### Custom macros

Project-specific Python macros can live in `dashboards/macros.py`:

```python
from glyf.dashboard import components as c


def finance_owner():
    return c.label_value("Owner", "Finance Analytics")


def stale_data_warning(hours_old):
    if hours_old > 24:
        return c.alert("Data is stale", title="Freshness", tone="warning")
    return c.badge("Fresh", tone="success")
```

Use them from dashboard YAML:

```yaml
summary:
  - "{{ finance_owner() }}"

sections:
  - title: Status
    items:
      - component: "{{ stale_data_warning(25) }}"
```

Built-in namespaces are reserved. Custom macros cannot replace `ui`, `alert`,
`ai`, or `time`.

## Output paths

Generated dashboard HTML is written to:

```text
target/glyf/dashboards/<name>.html
```

The dashboard index is written to:

```text
target/glyf/index.html
```
