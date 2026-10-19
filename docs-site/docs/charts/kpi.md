import ChartTypeCard from '@site/src/components/ChartTypeCard';

# KPI

One number as a tile, with the change against a comparison value. Not drawn.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="kpi" title="KPI" example="examples/product_analytics/visualisations/weekly_activated_users.ggsql" summary="One number as a tile, with its change against a comparison. For a headline.">

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

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `kpi` | `value`, optional `compare` | none: a kpi takes no `INTERACT` clause | glyf |

## How it reads

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

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
