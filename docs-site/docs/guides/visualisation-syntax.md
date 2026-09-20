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

Roles:

- `x`: required by every chart type.
- `y`: required by every chart type except `histogram`, which rejects it.
- `color`: optional, except for `heatmap`, which requires it.

## Chart types

| `DRAW` | Draws | Roles |
| --- | --- | --- |
| `line` | One line per `color` value. | `x`, `y`, optional `color` |
| `bar` | One bar per `x` value, stacked by `color`. | `x`, `y`, optional `color` |
| `scatter` | One point per row. `point` is accepted as an alias. | `x`, `y`, optional `color` |
| `area` | One filled area per `color` value. | `x`, `y`, optional `color` |
| `pie` | One slice per `x` value, sized by `y`. | `x`, `y`, optional `color` |
| `histogram` | The number of rows in each bin of `x`, stacked by `color`. | `x`, optional `color` |
| `boxplot` | The quartiles of `y` for each `x` value, with outliers as points. | `x`, `y`, optional `color` |
| `heatmap` | One cell per `x` and `y` pair, shaded by `color`. `tile` is accepted as an alias. | `x`, `y`, `color` |

Any other `DRAW` value fails validation with `unsupported chart type`.

### Histogram

```sql
SELECT order_amount, region
FROM {{ ref('fct_orders') }}

VISUALISE order_amount AS x, region AS color
DRAW histogram
LABEL title => 'Order size'
LABEL x_title => 'Order amount'
LABEL y_title => 'Orders'
```

The query returns one row per observation, not one row per bin. glyf divides
`x` into at most 30 bins and counts the rows in each. A `y` mapping fails
validation, because the y axis is the count.

### Boxplot

```sql
SELECT plan, sessions
FROM {{ ref('fct_product_usage') }}

VISUALISE plan AS x, sessions AS y
DRAW boxplot
LABEL title => 'Sessions by plan'
```

The query returns one row per observation. Each `x` value gets a box from the
first to the third quartile of `y` with a line at the median. Whiskers extend
1.5 times the interquartile range, and rows beyond them are drawn as points.
Without a `LABEL y_title`, the y axis is titled with the column name.

### Heatmap

```sql
SELECT weekday, hour, sessions
FROM {{ ref('fct_sessions_by_hour') }}
ORDER BY weekday_number, hour

VISUALISE hour AS x, weekday AS y, sessions AS color
DRAW heatmap
LABEL title => 'Sessions by hour'
```

The query returns one row per cell. Both axes are discrete, so a numeric `x`
such as an hour is drawn as 24 columns rather than a continuous scale.

Cells appear in the order the query returns them. Use `ORDER BY` to put Monday
before Tuesday; without it the order is whatever the warehouse returns.

### Numeric columns

A histogram's `x`, a boxplot's `y` and a heatmap's `color` must be integer or
floating-point columns. A text column fails the render:

```text
histogram needs a numeric x column and 'region' is string
```

### Row order

A chart is drawn from the rows the query returned, in the order it returned
them. For some chart types that order is the picture: it sets a stacked bar's
segment order, a pie's slice order, which points a scatter draws on top, and a
heatmap's axes.

SQL only promises an order when the query asks for one. A query with no
`ORDER BY` can come back in a different order on the next build and draw a
different chart from the same data, so glyf orders the rows itself when the
query does not, and says which columns it used:

```text
! visualisations/margin_share.ggsql: the query has no ORDER BY, so glyf ordered
  the rows by department, gross_margin to keep the chart reproducible. Add an
  ORDER BY to choose the order yourself.
```

Add an `ORDER BY` and glyf keeps that order exactly, untouched. An `ORDER BY`
inside a CTE, a subquery or a window function orders that, not the rows the
chart draws, so it does not count.

Only the chart types above are reported, because only they show the order.
Every chart is ordered either way, so that a build can be compared against the
last one.

## Labels

- `title`
- `subtitle`
- `x_title`
- `y_title`

A label value is quoted with single or double quotes: `LABEL title => 'Revenue'`
or `LABEL title => "Revenue"`.

## Config

- `width`: positive integer.
- `height`: positive integer.

## Interactions

Interactions are optional. Static SVG and PNG output remains the default when no `INTERACT` directive is present.

```sql
INTERACT tooltip, zoom, legend_filter
```

Supported interactions:

- `tooltip`: adds Vega-Lite tooltips for encoded fields. A `histogram` tooltip
  shows the bin and its count. A `boxplot` tooltip shows the quartiles of the box
  under the pointer.
- `zoom`: enables pan and zoom for local interactive dashboard previews.
- `legend_filter`: lets users filter by legend values. This requires a `color`
  mapping. It is not supported for `boxplot` or `heatmap` and fails validation
  there.

Interactive charts still write PNG and SVG artifacts. They also write a Vega-Lite JSON artifact, which dashboard pages embed with the Vega runtime scripts. The exported dashboard is still static HTML, but interactive rendering needs a browser with JavaScript enabled and access to those scripts.

Unsupported interaction names fail validation with a parser error.

## Parser scope

The parser is intentionally small. It does not parse SQL. SQL is passed through after dbt refs and sources are resolved.
