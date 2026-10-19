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

- `x`: required by every chart type except `table`, `kpi`, `map`, `sankey`
  and `treemap`.
- `y`: required by every chart type except `histogram`, which rejects it,
  `table`, `kpi`, `map`, `sankey` and `treemap`.
- `color`: optional, except for `heatmap`, which requires it.
- `facet`: optional for `line`, `bar`, `area`, `scatter` and `histogram`.
  Draws the chart once per value of the column. See
  [Small multiples](#small-multiples).
- `y2`: a `combo`'s line, drawn on the right axis; required there and taken
  nowhere else. See [Combo](../charts/combo.md).
- `value` and `compare`: a `kpi`'s roles, and nobody else's. See [KPI](../charts/kpi.md).
- `region`, or `latitude` and `longitude`, with an optional `size` and
  `label`: a `map`'s roles. See [Map](../charts/map.md).
- `source`, `target` and `value`: a `sankey`'s roles, all three required. See
  [Sankey](../charts/sankey.md).
- `label` and `value`, with an optional `group`: a `treemap`'s roles. See
  [Treemap](../charts/treemap.md).

A `table` takes no roles at all: its `VISUALISE` is a list of columns. See
[Table](../charts/table.md).

## Chart types

Sixteen chart types, each with its own page under [Charts](../charts/overview.md):

| `DRAW` | Roles | Page |
| --- | --- | --- |
| `line` | `x`, `y`, optional `color` | [Line](../charts/line.md) |
| `bar` | `x`, `y`, optional `color` | [Bar](../charts/bar.md) |
| `area` | `x`, `y`, optional `color` | [Area](../charts/area.md) |
| `combo` | `x`, `y` (bars), `y2` (line) | [Combo](../charts/combo.md) |
| `funnel` | `x` (the step), `y` | [Funnel](../charts/funnel.md) |
| `waterfall` | `x` (the step), `y` (the change) | [Waterfall](../charts/waterfall.md) |
| `scatter` | `x`, `y`, optional `color` | [Scatter](../charts/scatter.md) |
| `pie` | `x`, `y`, optional `color` | [Pie](../charts/pie.md) |
| `histogram` | `x`, optional `color` | [Histogram](../charts/histogram.md) |
| `boxplot` | `x`, `y`, optional `color` | [Boxplot](../charts/boxplot.md) |
| `heatmap` | `x`, `y`, `color` | [Heatmap](../charts/heatmap.md) |
| `table` | a column list, or `*` | [Table](../charts/table.md) |
| `kpi` | `value`, optional `compare` | [KPI](../charts/kpi.md) |
| `map` | `region` or `latitude` and `longitude`, optional `size`, `color` and `label` | [Map](../charts/map.md) |
| `sankey` | `source`, `target`, `value` | [Sankey](../charts/sankey.md) |
| `treemap` | `label`, `value`, optional `group` | [Treemap](../charts/treemap.md) |

Any other `DRAW` value fails validation with `unsupported chart type`.

### Numeric columns

A histogram's `x`, a boxplot's `y`, a heatmap's `color`, a combo's `y` and
`y2`, a funnel's and a waterfall's `y` and a treemap's `value` must be
integer or floating-point columns. So must a map's `latitude`, `longitude` and `size`. A text column fails the render:

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

Add an `ORDER BY` and glyf keeps that order. An `ORDER BY` inside a CTE, a
subquery or a window function orders that, not the rows the chart draws, so
it does not count.

#### Ties

An `ORDER BY` can leave ties. `ORDER BY department` says nothing about two
rows in the same department, so the warehouse may return them either way
round: a scatter then draws one point over the other differently from build
to build, and a table swaps two rows. Under a `LIMIT` it is worse, because
the tie decides which rows come back at all. `ORDER BY sessions DESC LIMIT 10`
with three accounts tied for tenth place keeps whichever one the warehouse
reaches first.

So glyf settles ties. Before the query runs, it adds the query's other
columns to the end of its outermost `ORDER BY`:

```sql
SELECT account_id, plan, sessions
FROM {{ ref('fct_account_sessions') }}
ORDER BY sessions DESC   -- as written
LIMIT 10
```

runs as

```sql
ORDER BY sessions DESC, account_id, plan
LIMIT 10
```

Your keys come first and are untouched, so the order you asked for holds.
The added columns only decide between rows your keys call equal, and because
they are in the SQL, the same ten rows make the cut every build. A column you
already order by, by name, alias or position, is not added again, and a query
whose `ORDER BY` names every column runs exactly as written.

The compiled SQL in `target/glyf/compiled/` and the dashboard's source view
show the query as it ran, tiebreak included. The build record hashes the
query as you wrote it, so a glyf upgrade that adds a tiebreak does not read as
a query change in [`glyf diff`](visual-diff.md). When the rows did tie, the
build says so:

```text
! visualisations/top_accounts.ggsql: rows tie on its ORDER BY sessions, so glyf
  added account_id, plan to settle them the same way every build. Add them to
  the ORDER BY to choose the tiebreak yourself.
```

Rows equal in every column are not a tie: they draw the same mark, so their
order cannot show.

Three cases are handled differently:

- `SELECT *`: glyf cannot name the columns before the query runs, so it
  settles the ties after the rows come back instead, by the other columns.
  That keeps the order still but cannot choose which rows a `LIMIT` keeps,
  and the build says so. Name the columns to get the tiebreak in the SQL.
- A `UNION` or other set operation is left as written.
- A column the warehouse cannot order by, such as a `STRUCT` in BigQuery,
  makes the rewritten query fail. glyf then runs the query as written and
  warns that its ties may change order between builds.

Only the chart types above are reported, because only they show the order.
Every chart is ordered either way, so that a build can be compared against the
last one.

## Small multiples

A `line`, `bar`, `area`, `scatter` or `histogram` takes a `facet` role: the
chart is drawn once per value of that column, as a grid of panels.

```sql
SELECT week, plan, sum(sessions) AS sessions
FROM {{ ref('fct_product_usage') }}
GROUP BY 1, 2
ORDER BY 1, 2

VISUALISE week AS x, sessions AS y, plan AS facet
DRAW bar
CONFIG columns => 3
INTERACT tooltip
```

Every panel shares the same axes and colours, so the panels compare at a
glance: the tallest bar in any panel is the tallest in all of them. Each
panel is named by its value, in ascending order.

`CONFIG width` and `CONFIG height` are the whole grid's. The panels share the
width, in rows of `CONFIG columns`; without it, a row holds up to three
panels, fewer when there are fewer values. Without `CONFIG height`, each panel
is three fifths as tall as it is wide. Where a panel is too narrow for every x
label, every other label is left out.

A faceted chart takes the same `color` and `INTERACT` its chart type does;
`zoom` zooms all the panels together. Dashboard filters redraw the grid, so
filtering the facet's column leaves only the matching panels. The visual diff
compares a faceted chart pixel by pixel rather than draw it over its old self.

## Labels

- `title`
- `subtitle`
- `x_title`
- `y_title`
- `y2_title`, for a `combo`: the right axis, which the line is drawn against
- `total`, for a `waterfall`: the closing bar's name, `Total` by default
- a column name, for a `table`: the text its header shows
- `compare`, for a `kpi`: what the comparison is called

A label value is quoted with single or double quotes: `LABEL title => 'Revenue'`
or `LABEL title => "Revenue"`.

## Config

A glyf addition.

- `width`: positive integer.
- `height`: positive integer.
- `columns`: positive integer, a chart with a `facet` only. How many panels
  to a row. See [Small multiples](#small-multiples).
- `shapes`: a map only. A TopoJSON file in the project to draw instead of the
  world's countries. See [Map](../charts/map.md).
- `projection`: a map only. How the globe is flattened; `equalEarth` by
  default. See [Map](../charts/map.md).

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
dashboard. A `kpi` takes none either. A `map` takes
`tooltip` and `zoom`. A `sankey`, a `combo`, a `funnel`, a `treemap` and a
`waterfall` take `tooltip` only.

Interactive charts still write PNG and SVG artifacts. They also write a Vega-Lite JSON artifact, which dashboard pages embed with the Vega runtime scripts. The exported dashboard is still static HTML, but interactive rendering needs a browser with JavaScript enabled and access to those scripts.

Unsupported interaction names fail validation with a parser error.

## Parser scope

glyf validates the chart block itself: the draw type, the roles it takes,
labels, `CONFIG` and `INTERACT`. The SQL is checked for syntax; whether a
column exists is for the warehouse to say, so a query that names a missing
column fails at build, with the chart's name. dbt refs and sources are
resolved before the SQL runs.
