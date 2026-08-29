# Visualisation Syntax

A `.ggsql` file contains SQL followed by a small chart block.

`glyf` uses a focused subset of [ggsql](https://ggsql.org)-style directives so chart definitions stay readable in dbt projects and easy to validate in CI.

```sql
SELECT month, revenue, region
FROM {{ ref('fct_sales') }}

VISUALISE month AS x, revenue AS y, region AS color
DRAW bar
LABEL title => 'Revenue by Region'
LABEL subtitle => 'Grouped monthly revenue'
LABEL x_title => 'Month'
LABEL y_title => 'Revenue'
CONFIG width => 900
CONFIG height => 500
INTERACT tooltip, zoom
```

## Required directives

`VISUALISE` maps query columns to chart roles.

`DRAW` chooses a chart type.

Required roles:

- `x`
- `y`

Optional role:

- `color`

## Chart types

- `line`
- `bar`
- `scatter`
- `area`
- `pie`

## Labels

- `title`
- `subtitle`
- `x_title`
- `y_title`

## Config

- `width`: positive integer.
- `height`: positive integer.

## Interactions

Interactions are optional. Static SVG and PNG output remains the default when no `INTERACT` directive is present.

```sql
INTERACT tooltip, zoom, legend_filter
```

Supported interactions:

- `tooltip`: adds Vega-Lite tooltips for encoded fields.
- `zoom`: enables pan and zoom for local interactive dashboard previews.
- `legend_filter`: lets users filter by legend values. This requires a `color` mapping.

Interactive charts still write PNG and SVG artifacts. They also write a Vega-Lite JSON artifact, which dashboard pages embed with the Vega runtime scripts. The exported dashboard is still static HTML, but interactive rendering needs a browser with JavaScript enabled and access to those scripts.

Unsupported interaction names fail validation with a parser error.

## Parser scope

The parser is intentionally small. It does not parse SQL. SQL is passed through after dbt refs and sources are resolved.
