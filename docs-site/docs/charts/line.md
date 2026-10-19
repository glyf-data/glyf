import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Line

One line per `color` value.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="line" title="Line" example="examples/product_analytics/visualisations/activation_rate_by_plan.ggsql" summary="A value over an ordered x, one line per colour. Shows trend and turning points.">

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

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `line` | `x`, `y`, optional `color` | `tooltip`, `zoom` and `legend_filter` (with a `color` mapping) | ggsql |

## How it reads

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

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
