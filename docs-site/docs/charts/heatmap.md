import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Heatmap

One cell per `x` and `y` pair, shaded by `color`. `tile` is accepted as an alias.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="heatmap" title="Heatmap" example="examples/product_analytics/visualisations/activity_by_hour.ggsql" summary="One shaded cell per x and y pair. Shows patterns across two categories at once.">

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

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `heatmap` | `x`, `y`, `color` | `tooltip` and `zoom`; `legend_filter` fails validation | ggsql (`tile`) |

## How it reads

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

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
