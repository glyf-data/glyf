import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Boxplot

The quartiles of `y` for each `x` value, with outliers as points.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="boxplot" title="Boxplot" example="examples/product_analytics/visualisations/sessions_per_account.ggsql" summary="Quartiles of y for each x, outliers as points. Compares spreads, not just averages.">

```sql
SELECT
  plan,
  sessions
FROM {{ ref('fct_account_sessions') }}

VISUALISE plan AS x, sessions AS y
DRAW boxplot
LABEL title => 'Sessions per Account'
LABEL subtitle => 'Median, quartiles and outlying accounts for each plan'
LABEL x_title => 'Plan'
LABEL y_title => 'Sessions'
INTERACT tooltip
```

</ChartTypeCard>

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `boxplot` | `x`, `y`, optional `color` | `tooltip` and `zoom`; `legend_filter` fails validation | glyf |

## How it reads

```sql
SELECT plan, sessions
FROM {{ ref('fct_product_usage') }}

VISUALISE plan AS x, sessions AS y
DRAW boxplot
LABEL title => 'Sessions by plan'
```

The query returns one row per observation. Each `x` value gets a box from the
first to the third quartile of `y` with a line at the median. Whiskers extend
1.5 times the interquartile range, and rows beyond them are drawn as points.
Without a `LABEL y_title`, the y axis is titled with the column name.

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
