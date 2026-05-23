# Dashboard YAML

Dashboard configs live in `dashboards/`.

```yaml
name: executive
title: Executive Dashboard
description: Key business metrics generated from dbt models.

charts:
  - revenue
  - revenue_by_region_bar
  - revenue_share_pie
```

Existing dashboards that only use `charts` continue to render as a simple
responsive chart grid.

## Toolbar and Summary Components

Generated dashboards include a BI-style toolbar by default. Configure it with
`toolbar` when the page should show public/private state or a subset of actions:

```yaml
toolbar:
  visibility: private
  actions: [share, visibility]
```

Use `summary` for macro-backed dashboard metadata or quick context. Summary
entries are Jinja expressions that return typed dashboard components:

```yaml
summary:
  - "{{ ui.label_value('Owner', 'Analytics Engineering') }}"
  - "{{ ui.label_value('Generated', time.now('%Y-%m-%d %H:%M')) }}"
```

## Rich Layout

Use `layout.columns` plus `sections` when a dashboard needs grouped content,
metric tiles, markdown notes, or chart sizing hints.

```yaml
name: executive
title: Executive Dashboard
description: Key business metrics generated from dbt models.

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
```

Macro-backed components can also be used inside section items:

```yaml
sections:
  - title: Status
    items:
      - component: "{{ echo('Refresh complete', 'Notification') }}"
      - component: "{{ ui.list(['Revenue', 'Margin', 'Bookings'], title='Metrics') }}"
      - chart: revenue
```

`groups` is accepted as an alias for `sections`:

```yaml
groups:
  - title: Regional performance
    columns: 2
    charts:
      - revenue_by_region_bar
      - revenue_share_pie
```

`layout.columns` and `sections[].columns` can be an integer column count, a
space-separated string, or a list of track widths. Percentage tracks are treated
as proportional grid weights, so `columns: "30% 70%"` renders as a two-column
grid without overflowing around the dashboard gap.

## Dashboard Macros

Dashboard macros follow a dbt-inspired authoring model: write a Jinja expression
in YAML, call a macro, and let the macro return a typed component spec. The
renderer owns the HTML, so macros cannot directly inject arbitrary dashboard
markup.

Built-in namespaces:

- `ui.label_value(label, value, note=None)`: compact label/value component.
- `ui.text(value, title=None)`: text component.
- `ui.list(values, title=None)`: list component.
- `ui.badge(label, tone='neutral')`: badge component.
- `ui.link(label, href, title=None)`: link component.
- `alert.info(value, title=None)`: informational alert.
- `alert.success(value, title=None)`: success alert.
- `alert.warning(value, title=None)`: warning alert.
- `alert.error(value, title=None)`: error alert.
- `time.now(format='%Y-%m-%d %H:%M', timezone=None)`: formatted timestamp.

Convenience aliases are available for common calls:

```yaml
sections:
  - title: Status
    items:
      - component: "{{ echo('Welcome', 'Notification') }}"
      - component: "{{ listofvalues(['a', 'b', 'c'], title='Values') }}"
```

Project-specific Python macros can live in `dashboards/macros.py`:

```python
from dbt_charts.dashboard import components as c


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

## Fields

- `name`: output filename stem.
- `title`: dashboard page title.
- `description`: optional intro text.
- `toolbar`: optional dashboard action bar configuration. Use `false` to hide it.
- `toolbar.visibility`: `public` or `private`.
- `toolbar.actions`: list of toolbar actions. Currently supports `share` and
  `visibility`.
- `summary`: optional list of macro expressions rendered as summary components.
- `charts`: list of `.ggsql` chart names without the extension.
- `layout`: optional layout string or mapping.
- `layout.columns`: optional default grid columns for rich sections. Use an
  integer, a string like `"30% 70%"`, or a list like `[1fr, 2fr]`.
- `sections`: optional grouped dashboard content.
- `groups`: optional alias for `sections`.
- `sections[].title`: optional section heading.
- `sections[].description`: optional section intro text.
- `sections[].columns`: optional section-level grid columns, using the same
  formats as `layout.columns`.
- `sections[].charts`: shorthand list of chart names for a section.
- `sections[].items`: ordered list of chart, markdown, and metric items.
- `items[].chart`: chart name, with optional `title` and `width`.
- `items[].component`: macro expression that returns a typed dashboard component.
- `items[].markdown`: markdown-style text block, either a string or a mapping with
  `title` and `text`.
- `items[].metric`: metric tile with `label`, `value`, optional `note`, and
  optional `width`.

Generated HTML is written to:

```text
target/ggsql/dashboards/<name>.html
```

The dashboard index is written to:

```text
target/ggsql/index.html
```
