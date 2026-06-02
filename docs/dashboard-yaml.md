# Dashboard YAML

Dashboard configs live in `dashboards/`.

```yaml
name: executive
title: Executive Dashboard
description: Key business metrics generated from dbt models.
tags:
  - finance
  - monthly

charts:
  - revenue
  - revenue_by_region_bar
  - revenue_share_pie
```

Existing dashboards that only use `charts` continue to render as a simple
responsive chart grid.

## Toolbar and AI Summary

Generated dashboards include a BI-style toolbar by default. Configure it with
`toolbar` when the page should show public/private state or a subset of actions:

```yaml
toolbar:
  visibility: private
  actions: [share, visibility]
```

Generated dashboards also render static controls for star, lookback, feedback,
and AI Summary. Those controls are part of the generated dashboard shell today;
they do not require YAML fields yet.

The dashboard header metadata shows the actual UTC build timestamp, so
`Refreshed` reflects when the HTML artifact was generated.

Use `summary` for macro-backed AI Summary content. Summary entries are Jinja
expressions that return typed dashboard components:

```yaml
summary:
  - "{{ ai.summary('Revenue moved up this month.') }}"
  - "{{ ai.insight('Starter churn needs review.', tone='warning') }}"
  - "{{ ui.label_value('Owner', 'Analytics Engineering') }}"
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
- `ai.summary(value, title='Overview')`: text block for the AI Summary panel.
- `ai.insight(value, title=None, tone='info')`: signal-style item for the AI
  Summary panel.
- `ai.signal(value, title=None, tone='info')`: alias for `ai.insight`.
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

## Fields

- `name`: output filename stem.
- `title`: dashboard page title.
- `description`: optional intro text.
- `tags`: optional list of short labels shown in the dashboard header.
- `toolbar`: optional dashboard action bar configuration. Use `false` to hide it.
- `toolbar.visibility`: `public` or `private`.
- `toolbar.actions`: list of YAML-configured toolbar actions. Currently
  supports `share` and `visibility`.
- `summary`: optional list of macro expressions rendered in the AI Summary panel.
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
target/glyf/dashboards/<name>.html
```

The dashboard index is written to:

```text
target/glyf/index.html
```

## Tags

Use `tags` to control the badges shown under the dashboard description:

```yaml
tags:
  - finance
  - monthly
  - board
```

Tags must be a list of non-empty strings. Glyf preserves their order and
removes duplicates.
