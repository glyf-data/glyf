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

Current supported values:

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

### Summary

`summary` is an optional list of macro expressions rendered as typed summary
components above the dashboard body.

```yaml
summary:
  - "{{ ui.label_value('Owner', 'Analytics Engineering') }}"
  - "{{ ui.label_value('Generated', time.now('%Y-%m-%d %H:%M')) }}"
  - "{{ ui.badge('Reviewed', tone='success') }}"
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
| `charts` | List of `.ggsql` chart names without the extension. |
| `toolbar` | Optional toolbar configuration, or `false` to hide it. |
| `summary` | Optional list of macro expressions rendered as summary components. |
| `layout` | Optional layout string or mapping. |
| `sections` | Optional grouped dashboard content. |
| `groups` | Alias for `sections`. |

### Layout fields

| Field | Description |
| --- | --- |
| `layout.columns` | Default grid columns for the dashboard body. Accepts an integer, a track string like `"30% 70%"`, or a list like `["1fr", "2fr"]`. |
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

### Built-in macros

Built-in namespaces:

| Macro | Description |
| --- | --- |
| `ui.label_value(label, value, note=None, width=None)` | Compact label/value component. |
| `ui.text(value, title=None, width=None)` | Text component. |
| `ui.list(values, title=None, width=None)` | List component. |
| `ui.listofvalues(values, title=None, width=None)` | Alias-style list component. |
| `ui.badge(label, tone='neutral', width=None)` | Badge component. |
| `ui.link(label, href, title=None, width=None)` | Link component. |
| `alert.message(value, title=None, tone='info', width=None)` | Generic alert component. |
| `alert.info(value, title=None, width=None)` | Informational alert. |
| `alert.success(value, title=None, width=None)` | Success alert. |
| `alert.warning(value, title=None, width=None)` | Warning alert. |
| `alert.error(value, title=None, width=None)` | Error alert. |
| `time.now(format='%Y-%m-%d %H:%M', timezone=None)` | Formatted timestamp string. |

Convenience aliases:

- `label_value(...)`
- `text(...)`
- `listofvalues(...)`
- `link(...)`
- `badge(...)`
- `now(...)`
- `echo(...)` which maps to `alert.info(...)`

Example:

```yaml
summary:
  - "{{ label_value('Generated', now('%Y-%m-%d %H:%M')) }}"

sections:
  - title: Status
    items:
      - component: "{{ echo('Welcome', 'Notification') }}"
      - component: "{{ listofvalues(['a', 'b', 'c'], title='Values') }}"
      - component: "{{ alert.warning('Threshold exceeded', 'Freshness') }}"
```

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
or `time`.

## Output paths

Generated dashboard HTML is written to:

```text
target/ggsql/dashboards/<name>.html
```

The dashboard index is written to:

```text
target/ggsql/index.html
```
