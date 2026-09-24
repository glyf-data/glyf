# Dashboard YAML

Dashboard configs live in `dashboards/`.

This guide is the dashboard specification: what fields exist, which values
they accept, how layout works, and where macros run.

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

The toolbar holds star, share, visibility, lookback, feedback, and AI Summary
controls. YAML decides whether it appears, what the visibility badge says, and
which of the share and visibility buttons render.

| Field | Supported values | Default |
| --- | --- | --- |
| `toolbar` | `false` or a mapping | enabled |
| `toolbar.enabled` | `true`, `false` | `true` |
| `toolbar.visibility` | `public`, `private` | `private` |
| `toolbar.actions` | list drawn from `share`, `visibility` | both |

:::warning `visibility` is a label, not a control

`toolbar.visibility` sets the badge and padlock the page displays. It does not
restrict anything: a dashboard marked `private` is exported byte-for-byte
identically to one marked `public`, rows and all. Access control comes from
wherever you host the site. See [what a published site
exposes](./data-exposure.md).

:::

```yaml
toolbar:
  visibility: public
```

Show only the share button:

```yaml
toolbar:
  actions: [share]
```

An empty `actions: []` removes both. Star, lookback, feedback, and AI Summary
are always present while the toolbar is enabled.

Hide the toolbar completely:

```yaml
toolbar: false
```

The header's `Refreshed` value is the UTC time at which `glyf dashboard` or
`glyf build` generated the page.

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

Percentage tracks are treated as proportional weights, so `"30% 70%"` renders
as a two-column grid without overflowing around the grid gap.

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

Each section item is one of four kinds:

| Kind | Example | Notes |
| --- | --- | --- |
| `chart` | `- chart: revenue` | Can also be a bare string in `items` or `charts`. |
| `component` | `- component: "{{ ui.badge('Ready') }}"` | Macro expression returning a typed component. |
| `markdown` | `- markdown: "Text"` | Can be a string or mapping with `title` and `text`. |
| `metric` | `- metric: { label: Revenue, value: $7.6k }` | Optional `delta`, `trend`, `note` and `width`. |

## Field definitions

### Top-level fields

| Field | Description |
| --- | --- |
| `name` | Output filename stem. |
| `title` | Dashboard page title. |
| `description` | Optional intro text. |
| `owner` | Optional team or person shown as the dashboard's owner in the bar under the header. Defaults to `data team`. |
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
| `items[].metric.delta` | Optional change, written as it should read: `"-1.7 pts vs last week"`. |
| `items[].metric.trend` | Optional direction of the delta, `up`, `down` or `flat`: green, red or grey, with an arrow. Needs a `delta`. |
| `items[].width` | Optional width hint on `chart`, `component`, or `metric` items. |

### Chart tools

Every chart card carries a small row of tools beside its type badge:

- **Download** saves the chart as a PNG, as it looks on the page: in the current theme and with any filter applied, at twice its size.
- **Full screen** opens the chart over the whole window; Escape or the same button closes it.
- **Zoom lock** and **reset** appear on charts with `INTERACT zoom`. Such a chart starts locked, so scrolling the page never zooms it by accident; unlock it to zoom with the wheel and pan by dragging, and reset to go back to the chart as built.

## Dashboard macros

`summary[]` entries and `sections[].items[].component` values are Jinja
expressions that call macros, such as
`"{{ ui.label_value('Owner', 'Analytics Engineering') }}"`. The built-in
catalog, the artifact helpers, and project-local custom macros are documented
in [Dashboard Macros](/docs/guides/dashboard-macros).

## Filters

A filter names a column. On the page it is a select with `All` and the
filter's values, and choosing a value redraws every chart on the dashboard
whose rows carry that column, in the browser, from the rows the page already
holds. Nothing is fetched and no server is involved.

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

What a filter does to each kind of card:

- A drawn chart is redrawn from its Vega specification with the filter applied,
  and a chip on the card names the value, `plan = Pro`.
- A table hides the rows that do not match and says `4 of 25 rows`.
- A kpi is one aggregated number and cannot be recomputed, so it is dimmed.
- A chart whose rows do not carry the column is dimmed, with a note saying
  which filter does not apply to it. A chart that looked filtered and was not
  would be worse than one that says so.

By default a filter applies to every chart that carries its column. `charts`
narrows it to a list:

```yaml
filters:
  - field: plan
    values: source(activation_by_plan, plan)
    charts: [activation_by_plan, sessions_by_plan]
```

Filtering works on the rows the page publishes, so it follows
[`export.row_data`](./data-exposure.md). Under `include`, any column of a
chart's result can be filtered. Under `minimal`, only the columns a chart
encodes are published, so a filter on any other column does not apply to it.
Under `exclude`, no rows are published and the filters are shown as labels
only. Filter selections are not written to the URL, so a link never carries a
value.

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

Use `theme` to choose the dashboard shell's default, `light` or `dark`. When
omitted, the dashboard falls back to the configured default in `glyf.yml`.
Every page also has a sun-and-moon button in its top-right actions that lets
the reader switch, and the choice is remembered in that reader's browser. When
`chart_theme` is `auto` the charts follow the switch; a `chart_theme` set to
`light` or `dark` keeps the charts as built.

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

## Output paths

Generated dashboard HTML is written to:

```text
target/glyf/dashboards/<name>.html
```

The dashboard index is written to:

```text
target/glyf/index.html
```
