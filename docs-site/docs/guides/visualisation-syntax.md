import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Visualisation Syntax

A `.ggsql` file contains SQL followed by a small chart block.

The format is [ggsql](https://ggsql.org): a SQL query, then a few lines saying
what to draw. glyf reads that format as is, so a ggsql chart is a glyf chart
and `.ggsql` files get the format's editor support. glyf also adds chart
types, `CONFIG` and `INTERACT`, which ggsql does not have; they are marked
below. A file that uses one is a glyf file, and upstream ggsql tools will not
accept it.

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

- `x`: required by every chart type except `table` and `kpi`.
- `y`: required by every chart type except `histogram`, which rejects it,
  `table` and `kpi`.
- `color`: optional, except for `heatmap`, which requires it.
- `value` and `compare`: a `kpi`'s roles, and nobody else's. See [KPI](#kpi).

A `table` takes no roles at all: its `VISUALISE` is a list of columns. See
[Table](#table).

## Chart types

Every type below is drawn from the [product analytics example](/docs/examples/product-analytics).
Switch a card to **Code** to see the `.ggsql` file that drew it, as it is in
the repository.

<div className="chartTypeGrid">

<ChartTypeCard type="line" title="Line" anchor="line" example="examples/product_analytics/visualisations/activation_rate_by_plan.ggsql" summary="A value over an ordered x, one line per colour. Shows trend and turning points.">

```sql
SELECT
  week,
  plan,
  round(sum(activated_users) * 100.0 / nullif(sum(active_users), 0), 1) as activation_rate
FROM {{ ref('fct_product_usage') }}
GROUP BY 1, 2

VISUALISE week AS x, activation_rate AS y, plan AS color
DRAW line
LABEL title => 'Activation Rate by Plan'
LABEL x_title => 'Week'
LABEL y_title => 'Activation Rate (%)'
INTERACT tooltip, legend_filter
```

</ChartTypeCard>

<ChartTypeCard type="bar" title="Bar" anchor="bar" example="examples/product_analytics/visualisations/sessions_per_user.ggsql" summary="One bar per x value, stacked by colour. Compares amounts across categories or periods.">

```sql
SELECT
  week,
  round(sum(sessions) * 1.0 / nullif(sum(active_users), 0), 2) as sessions_per_user
FROM {{ ref('fct_product_usage') }}
GROUP BY 1

VISUALISE week AS x, sessions_per_user AS y
DRAW bar
LABEL title => 'Sessions per Active User'
LABEL x_title => 'Week'
LABEL y_title => 'Sessions per User'
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="area" title="Area" anchor="area" example="examples/product_analytics/visualisations/active_users.ggsql" summary="A line with the space under it filled, stacked by colour. Shows volume and its make-up over time.">

```sql
SELECT week, sum(active_users) as active_users
FROM {{ ref('fct_product_usage') }}
GROUP BY 1

VISUALISE week AS x, active_users AS y
DRAW area
LABEL title => 'Active Users'
LABEL x_title => 'Week'
LABEL y_title => 'Users'
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="scatter" title="Scatter" anchor="scatter" example="examples/product_analytics/visualisations/sessions_scatter.ggsql" summary="One point per row. Shows how two numbers move together, and the rows that do not.">

```sql
SELECT active_users, sessions, plan
FROM {{ ref('fct_product_usage') }}
ORDER BY plan, active_users

VISUALISE active_users AS x, sessions AS y, plan AS color
DRAW scatter
LABEL title => 'Sessions vs Active Users'
LABEL x_title => 'Active Users'
LABEL y_title => 'Sessions'
INTERACT tooltip, zoom
```

</ChartTypeCard>

<ChartTypeCard type="pie" title="Pie" anchor="pie" example="examples/product_analytics/visualisations/sessions_by_plan.ggsql" summary="One slice per x value, sized by y. Shows the share of a whole, for a handful of parts.">

```sql
SELECT
  plan,
  sum(sessions) as sessions
FROM {{ ref('fct_product_usage') }}
GROUP BY 1
ORDER BY sessions DESC

VISUALISE plan AS x, sessions AS y
DRAW pie
LABEL title => 'Sessions by Plan'
LABEL y_title => 'Sessions'
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="histogram" title="Histogram" anchor="histogram" example="examples/product_analytics/visualisations/session_length_distribution.ggsql" summary="Rows counted into bins of x. Shows the shape of a distribution.">

```sql
SELECT
  avg_session_minutes,
  plan
FROM {{ ref('fct_account_sessions') }}
ORDER BY avg_session_minutes, plan

VISUALISE avg_session_minutes AS x, plan AS color
DRAW histogram
LABEL title => 'Session Length by Account'
LABEL subtitle => 'One row per account, binned by average session length'
LABEL x_title => 'Average session (minutes)'
LABEL y_title => 'Accounts'
INTERACT tooltip, legend_filter
```

</ChartTypeCard>

<ChartTypeCard type="boxplot" title="Boxplot" anchor="boxplot" example="examples/product_analytics/visualisations/sessions_per_account.ggsql" summary="Quartiles of y for each x, outliers as points. Compares spreads, not just averages.">

```sql
SELECT
  plan,
  sessions
FROM {{ ref('fct_account_sessions') }}

VISUALISE plan AS x, sessions AS y
DRAW boxplot
LABEL title => 'Sessions per Account'
LABEL subtitle => 'Median, quartiles and outlying accounts for each plan'
LABEL x_title => 'Plan'
LABEL y_title => 'Sessions'
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="heatmap" title="Heatmap" anchor="heatmap" example="examples/product_analytics/visualisations/activity_by_hour.ggsql" summary="One shaded cell per x and y pair. Shows patterns across two categories at once.">

```sql
SELECT
  weekday,
  hour,
  sessions
FROM {{ ref('fct_hourly_activity') }}
ORDER BY weekday_number, hour

VISUALISE hour AS x, weekday AS y, sessions AS color
DRAW heatmap
LABEL title => 'Sessions by Hour'
LABEL subtitle => 'Two working-day peaks; weekends run at a fifth of the volume'
LABEL x_title => 'Hour of day (UTC)'
LABEL y_title => 'Weekday'
CONFIG width => 1100
CONFIG height => 320
INTERACT tooltip
```

</ChartTypeCard>

<ChartTypeCard type="table" title="Table" anchor="table" example="examples/product_analytics/visualisations/top_accounts.ggsql" summary="The rows themselves, one column per listed column. For when the exact values matter.">

```sql
SELECT account_id, plan, sessions, avg_session_minutes
FROM {{ ref('fct_account_sessions') }}
ORDER BY sessions DESC, account_id
LIMIT 10

VISUALISE *
DRAW table
LABEL title => 'Most active accounts'
LABEL account_id => 'Account'
LABEL avg_session_minutes => 'Avg minutes'
CONFIG height => 360
```

</ChartTypeCard>

<ChartTypeCard type="kpi" title="KPI" anchor="kpi" example="examples/product_analytics/visualisations/weekly_activated_users.ggsql" summary="One number as a tile, with its change against a comparison. For a headline.">

```sql
WITH weekly AS (
  SELECT week, sum(activated_users) AS activated_users
  FROM {{ ref('fct_product_usage') }}
  GROUP BY 1
)
SELECT activated_users, lag(activated_users) OVER (ORDER BY week) AS previous
FROM weekly
ORDER BY week DESC
LIMIT 1

VISUALISE activated_users AS value, previous AS compare
DRAW kpi
LABEL title => 'Activated users'
LABEL compare => 'vs last week'
```

</ChartTypeCard>

</div>

| `DRAW` | Draws | Roles | From |
| --- | --- | --- | --- |
| `line` | One line per `color` value. | `x`, `y`, optional `color` | ggsql |
| `bar` | One bar per `x` value, stacked by `color`. | `x`, `y`, optional `color` | ggsql |
| `scatter` | One point per row. `point` is accepted as an alias. | `x`, `y`, optional `color` | ggsql (`point`) |
| `area` | One filled area per `color` value. | `x`, `y`, optional `color` | ggsql |
| `pie` | One slice per `x` value, sized by `y`. | `x`, `y`, optional `color` | glyf |
| `histogram` | The number of rows in each bin of `x`, stacked by `color`. | `x`, optional `color` | glyf |
| `boxplot` | The quartiles of `y` for each `x` value, with outliers as points. | `x`, `y`, optional `color` | glyf |
| `heatmap` | One cell per `x` and `y` pair, shaded by `color`. `tile` is accepted as an alias. | `x`, `y`, `color` | ggsql (`tile`) |
| `table` | The rows themselves, one column per listed column. Not drawn: no PNG or SVG. | a column list, or `*` | glyf |
| `kpi` | One number as a tile, with the change against a comparison value. Not drawn. | `value`, optional `compare` | glyf |

Any other `DRAW` value fails validation with `unsupported chart type`.

### Line

```sql
SELECT week, plan, active_users
FROM {{ ref('fct_product_usage') }}

VISUALISE week AS x, active_users AS y, plan AS color
DRAW line
```

The query returns one row per point: here, one per week and plan. Each `color`
value gets its own line, joined in `x` order, with a dot on every row so a
single week stands out. Without `color` there is one line.

Use a line when `x` is ordered, usually time, and the question is how a value
moves. A text `x` such as `2026-W01` is drawn as evenly spaced categories;
a date or number is drawn to scale.

### Bar

```sql
SELECT week, plan, sessions
FROM {{ ref('fct_product_usage') }}

VISUALISE week AS x, sessions AS y, plan AS color
DRAW bar
```

Each `x` value gets one bar as tall as `y`. With `color`, each bar is split
into one segment per colour value, stacked, so the bar's height is the total
and the segments are its parts. Segments stack in the order the query returns
the rows; see [Row order](#row-order).

Several rows for the same `x` and colour are stacked too, not summed into one
segment, so aggregate in SQL with `GROUP BY` when each bar should be one row.

### Area

```sql
SELECT week, plan, active_users
FROM {{ ref('fct_product_usage') }}

VISUALISE week AS x, active_users AS y, plan AS color
DRAW area
```

A line with the space beneath it filled. With `color`, the areas stack: the
top edge is the total, and each band's thickness is one colour's share of it.
Use an area over a line when the total matters as much as the parts; use a
line when the parts should be compared against each other, since stacked
bands are hard to compare except at the bottom.

### Scatter

```sql
SELECT active_users, sessions, plan
FROM {{ ref('fct_product_usage') }}
ORDER BY plan, active_users

VISUALISE active_users AS x, sessions AS y, plan AS color
DRAW scatter
```

One point per row, placed by two numbers. `point` is accepted as an alias.
Both axes include zero and are padded, so a point on the edge of the data is
drawn whole rather than cut in half by the axis.

Points that land on the same spot are drawn in row order, the later one on
top, so a scatter needs an `ORDER BY` that settles every row; see
[Row order](#row-order). `INTERACT zoom` suits a dense scatter; on a dashboard
the zoom starts locked so scrolling moves the page.

### Pie

```sql
SELECT plan, sum(sessions) AS sessions
FROM {{ ref('fct_product_usage') }}
GROUP BY 1
ORDER BY sessions DESC

VISUALISE plan AS x, sessions AS y
DRAW pie
```

One slice per row: `x` names it and `y` sizes it, as a share of the sum of
`y`. The slices are coloured by `x`, or by `color` when one is mapped. A pie
is a glyf addition, not in ggsql.

A pie reads well with a handful of slices and badly with many or near-equal
ones; a bar shows the same numbers more precisely. Slices go round in the
order the query returns them, so `ORDER BY` the size to read them largest
first.

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

### Table

```sql
SELECT account_id, plan, sessions
FROM {{ ref('fct_account_sessions') }}
ORDER BY sessions DESC
LIMIT 10

VISUALISE account_id, plan, sessions
DRAW table
LABEL title => 'Most active accounts'
LABEL account_id => 'Account'
CONFIG height => 360
```

A table is its rows, so `VISUALISE` lists the columns to show, in order,
without roles. `VISUALISE *` shows every column the query returns, in the
order it returns them. A column the query does not return fails the build with
the column's name; `x AS`, `y AS` and the other roles are rejected for a
table, and a column list is rejected for every other chart type, each error
saying what the chart wanted instead.

`LABEL <column> => '...'` names a column's header; a column without one shows
its name. `CONFIG height` bounds the table's height and the rows scroll inside
it; `CONFIG width` bounds its width. `INTERACT` is rejected: a table's rows are
already readable, and the dashboard lets a reader sort by clicking a header.

A table is not drawn. The build writes `charts/<name>.table.html`, a plain
`<table>` fragment, beside the usual data JSON and metadata, and never a PNG
or an SVG. The dashboard shows the fragment in a card; the bundle records the
table's columns and the fragment's path with `png` and `svg` set to `null`.

Two settings follow from that. [`render.max_rows`](../reference/configuration.md#how-many-rows-a-table-may-list)
(default `1000`) fails a table that would list more rows, naming the chart,
the way `render.max_marks` does for a picture. And
[`export.row_data: exclude`](data-exposure.md) fails a table at validation,
because a picture can be published without its rows and a table cannot.

### KPI

```sql
WITH weekly AS (
  SELECT week, sum(active_users) AS active_users
  FROM {{ ref('fct_product_usage') }}
  GROUP BY 1
)
SELECT active_users, lag(active_users) OVER (ORDER BY week) AS previous
FROM weekly
ORDER BY week DESC
LIMIT 1

VISUALISE active_users AS value, previous AS compare
DRAW kpi
LABEL title => 'Weekly active users'
LABEL compare => 'vs last week'
```

A kpi is one number. The query must return exactly one row; more or fewer
fails the build naming the chart, so aggregate until it does. `value` is the
headline. `compare`, when mapped, is the number to stand it against: the tile
shows the difference with its direction, and the difference as a share of the
comparison when that is not zero. A comparison of `NULL` shows the value
alone. `LABEL compare => '...'` names the comparison; it reads `vs previous`
without one. A number is shown with thousands separators and its precision
untouched; a text value is shown as it is. `INTERACT` is rejected.

Like a table, a kpi is not drawn. The build writes `charts/<name>.kpi.html`
beside the data JSON and metadata; the dashboard shows it as a tile; the
bundle records `fields.value`, `fields.compare` and `artifacts.kpi`, with
`png` and `svg` null. Unlike a table, a kpi is published under
`export.row_data: exclude`: one number is what the tile shows, the way a PNG
shows its values.

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

An `ORDER BY` has to decide every pair of rows to settle the picture. `ORDER BY
department, expenses` leaves two rows with the same department and the same
expenses in either order, and a scatter then draws one point over the other
differently from build to build. Add columns until no two rows tie.
[`glyf diff`](visual-diff.md) names this case when it finds it.

Only the chart types above are reported, because only they show the order.
Every chart is ordered either way, so that a build can be compared against the
last one.

## Labels

- `title`
- `subtitle`
- `x_title`
- `y_title`
- a column name, for a `table`: the text its header shows
- `compare`, for a `kpi`: what the comparison is called

A label value is quoted with single or double quotes: `LABEL title => 'Revenue'`
or `LABEL title => "Revenue"`.

## Config

A glyf addition.

- `width`: positive integer.
- `height`: positive integer.

## Interactions

A glyf addition. Interactions are optional. Static SVG and PNG output remains the default when no `INTERACT` directive is present.

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

A `table` takes no `INTERACT` clause; sorting by column is built into the
dashboard. A `kpi` takes none either.

Interactive charts still write PNG and SVG artifacts. They also write a Vega-Lite JSON artifact, which dashboard pages embed with the Vega runtime scripts. The exported dashboard is still static HTML, but interactive rendering needs a browser with JavaScript enabled and access to those scripts.

Unsupported interaction names fail validation with a parser error.

## Parser scope

glyf validates the chart block itself: the draw type, the roles it takes,
labels, `CONFIG` and `INTERACT`. The SQL is checked for syntax; whether a
column exists is for the warehouse to say, so a query that names a missing
column fails at build, with the chart's name. dbt refs and sources are
resolved before the SQL runs.
