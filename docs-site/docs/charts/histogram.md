import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Histogram

The number of rows in each bin of `x`, stacked by `color`.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="histogram" title="Histogram" example="examples/product_analytics/visualisations/session_length_distribution.ggsql" summary="Rows counted into bins of x. Shows the shape of a distribution.">

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

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `histogram` | `x`, optional `color` | `tooltip`, `zoom` and `legend_filter` (with a `color` mapping) | glyf |

## How it reads

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

To draw one histogram chart per value of a column, add a `facet` role: see
[Small multiples](../guides/visualisation-syntax.md#small-multiples).

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
