import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Bar

One bar per `x` value, stacked by `color`.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="bar" title="Bar" example="examples/product_analytics/visualisations/sessions_per_user.ggsql" summary="One bar per x value, stacked by colour. Compares amounts across categories or periods.">

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

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `bar` | `x`, `y`, optional `color` | `tooltip`, `zoom` and `legend_filter` (with a `color` mapping) | ggsql |

## How it reads

```sql
SELECT week, plan, sessions
FROM {{ ref('fct_product_usage') }}

VISUALISE week AS x, sessions AS y, plan AS color
DRAW bar
```

Each `x` value gets one bar as tall as `y`. With `color`, each bar is split
into one segment per colour value, stacked, so the bar's height is the total
and the segments are its parts. Segments stack in the order the query returns
the rows; see [Row order](../guides/visualisation-syntax.md#row-order).

Several rows for the same `x` and colour are stacked too, not summed into one
segment, so aggregate in SQL with `GROUP BY` when each bar should be one row.

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
