import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Pie

One slice per `x` value, sized by `y`.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="pie" title="Pie" example="examples/product_analytics/visualisations/sessions_by_plan.ggsql" summary="One slice per x value, sized by y. Shows the share of a whole, for a handful of parts.">

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

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `pie` | `x`, `y`, optional `color` | `tooltip`, `zoom` and `legend_filter` (with a `color` mapping) | glyf |

## How it reads

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

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
