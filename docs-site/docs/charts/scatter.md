import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Scatter

One point per row. `point` is accepted as an alias.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="scatter" title="Scatter" example="examples/product_analytics/visualisations/sessions_scatter.ggsql" summary="One point per row. Shows how two numbers move together, and the rows that do not.">

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

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `scatter` | `x`, `y`, optional `color` | `tooltip`, `zoom` and `legend_filter` (with a `color` mapping) | ggsql (`point`) |

## How it reads

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
[Row order](../guides/visualisation-syntax.md#row-order). `INTERACT zoom` suits a dense scatter; on a dashboard
the zoom starts locked so scrolling moves the page.

To draw one scatter chart per value of a column, add a `facet` role: see
[Small multiples](../guides/visualisation-syntax.md#small-multiples).

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
