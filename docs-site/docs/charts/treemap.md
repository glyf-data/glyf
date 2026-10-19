import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Treemap

A rectangle per row, its area its `value`, clustered and coloured by an
optional `group`.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="treemap" title="Treemap" example="examples/sales_dashboard/visualisations/store_revenue.ggsql" summary="A rectangle per row, its area its value, clustered by group. Shows the parts of a whole when there are too many for a pie.">

```sql
SELECT city, format, revenue
FROM {{ source('raw', 'stores') }}
ORDER BY revenue DESC

VISUALISE city AS label, revenue AS value, format AS group
DRAW treemap
LABEL title => 'Revenue by Store'
LABEL subtitle => 'Each store sized by its revenue, grouped by format'
INTERACT tooltip
```

</ChartTypeCard>

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `treemap` | `label`, `value`, optional `group` | `tooltip` only | glyf |

## How it reads

```sql
SELECT product, category, sum(revenue) AS revenue
FROM {{ ref('fct_orders') }}
GROUP BY 1, 2

VISUALISE product AS label, revenue AS value, category AS group
DRAW treemap
INTERACT tooltip
```

A treemap shows the parts of a whole when there are too many for a
[pie](pie.md): one tile per row, named by `label` and as big as its `value`.
Rows with the same `label`, in the same group, are one tile, their values
summed. A row with a missing label or value, or a value of zero, is skipped.

glyf lays the tiles out itself, largest first, each row of tiles chosen to
keep them as close to square as it can, so a tile is easy to compare with its
neighbours. With a `group`, each group is laid out as one block, the largest
group first, and its tiles inside it; the groups are coloured and a legend
names them. Without one, every tile is one colour. Ties in value keep the
order the query first names them in.

A tile shows its name, and its value under it, when it has room; a name too
long for its tile is cut short with an ellipsis. With `INTERACT tooltip`,
every tile shows its label, group, value and share of the total, however
small it is.

`value` must be a number of zero or more; a negative value fails the build.
A treemap takes no `x`, `y` or `color`, and `zoom` and `legend_filter` fail
validation. Dashboard filters do not apply to it: its spec carries the
laid-out tiles rather than the rows, so the card says it is not filtered.
The visual diff compares a treemap pixel by pixel.

## See also

- [Pie](pie.md), for a whole of a few parts.
- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [All chart types](overview.md).
