import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Area

One filled area per `color` value.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="area" title="Area" example="examples/product_analytics/visualisations/active_users.ggsql" summary="A line with the space under it filled, stacked by colour. Shows volume and its make-up over time.">

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

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `area` | `x`, `y`, optional `color` | `tooltip`, `zoom` and `legend_filter` (with a `color` mapping) | ggsql |

## How it reads

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

To draw one area chart per value of a column, add a `facet` role: see
[Small multiples](../guides/visualisation-syntax.md#small-multiples).

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
