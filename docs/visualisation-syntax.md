# Visualisation Syntax

A `.ggsql` file contains SQL followed by a small chart block.

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

- `VISUALISE`: maps query columns to chart roles.
- `DRAW`: chooses a chart type.

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

- `width`: positive integer
- `height`: positive integer

## Interactions

Interactions are optional. Static SVG and PNG output remains the default when no
`INTERACT` directive is present.

```sql
INTERACT tooltip, zoom, legend_filter
```

Supported interactions:

- `tooltip`: adds Vega-Lite tooltips for encoded fields.
- `zoom`: enables pan and zoom for local interactive dashboard previews.
- `legend_filter`: lets users filter by legend values. This requires a
  `color` mapping.

Interactive charts still write PNG and SVG artifacts. They also write an
additional Vega-Lite JSON artifact and dashboard pages embed that JSON with
Vega/Vega-Lite runtime scripts. The exported dashboard remains static HTML, but
interactive rendering requires a browser with JavaScript enabled and access to
the Vega runtime scripts referenced by the page.

Unsupported interaction names fail validation with a clear parser error.

The parser is intentionally small. It does not parse SQL; SQL is passed through
after dbt refs and sources are resolved.
