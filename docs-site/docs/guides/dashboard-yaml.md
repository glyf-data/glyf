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

Existing dashboards that only use `charts` render as a responsive chart grid.

## Rich layout

Use `layout.columns` plus `sections` when a dashboard needs grouped content, metric tiles, markdown notes, or chart sizing hints.

```yaml
name: executive
title: Executive Dashboard
description: Key business metrics generated from dbt models.

layout:
  columns: 3

sections:
  - title: Revenue overview
    description: Revenue signals for the current sample period.
    columns: 3
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
        width: 2
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

## Fields

| Field | Description |
| --- | --- |
| `name` | Output filename stem. |
| `title` | Dashboard page title. |
| `description` | Optional intro text. |
| `charts` | List of `.ggsql` chart names without the extension. |
| `layout` | Optional layout string or mapping. |
| `layout.columns` | Optional default number of grid columns for rich sections. |
| `sections` | Optional grouped dashboard content. |
| `groups` | Optional alias for `sections`. |
| `sections[].title` | Optional section heading. |
| `sections[].description` | Optional section intro text. |
| `sections[].columns` | Optional section-level grid column count. |
| `sections[].charts` | Shorthand list of chart names for a section. |
| `sections[].items` | Ordered list of chart, markdown, and metric items. |
| `items[].chart` | Chart name, with optional `title` and `width`. |
| `items[].markdown` | Markdown-style text block, either a string or a mapping with `title` and `text`. |
| `items[].metric` | Metric tile with `label`, `value`, optional `note`, and optional `width`. |

Generated HTML is written to:

```text
target/ggsql/dashboards/<name>.html
```

The dashboard index is written to:

```text
target/ggsql/index.html
```
