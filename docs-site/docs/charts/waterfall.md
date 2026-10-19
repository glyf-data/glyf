import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Waterfall

A running total: one bar per change, rising or falling from where the one
before ended, and a closing bar for the total.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="waterfall" title="Waterfall" example="examples/finance_metrics/visualisations/margin_bridge.ggsql" summary="A running total: a bar per change, rising or falling from where the last ended, then the total. Shows how one number becomes another.">

```sql
SELECT 0 AS step_order, 'Bookings' AS step, sum(bookings) AS amount
FROM {{ ref('fct_finance') }}
UNION ALL
SELECT 1, department || ' expenses', -sum(expenses)
FROM {{ ref('fct_finance') }}
GROUP BY department
ORDER BY step_order, amount

VISUALISE step AS x, amount AS y
DRAW waterfall
LABEL title => 'From Bookings to Gross Margin'
LABEL subtitle => "Twelve months of bookings, less each department's expenses"
LABEL y_title => 'Amount'
LABEL total => 'Gross margin'
CONFIG width => 1100
CONFIG height => 340
INTERACT tooltip
```

</ChartTypeCard>

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `waterfall` | `x` (the step), `y` (the change) | `tooltip` only | glyf |

## How it reads

```sql
SELECT step, change
FROM {{ ref('fct_revenue_bridge') }}
ORDER BY step_number

VISUALISE step AS x, change AS y
DRAW waterfall
LABEL total => 'Closing revenue'
INTERACT tooltip
```

A waterfall shows how one number becomes another: opening revenue, plus new
business, less churn, to closing revenue. Each row is one step: its name
(`x`) and how much it changes the total (`y`), positive or negative.

The first row is where the total starts. It is drawn up from zero, like the
total, so put the opening amount first. Every row after it is a bar from
where the running total stood to where it stands after the change: green when
it rises, red when it falls. glyf adds a closing bar for the final total,
named by `LABEL total` (`Total` when that is not set). A dashed line carries
each bar's end across to the next, and each bar is labelled with its change,
or its amount for the first and the total.

The steps keep the order the query returns them in, so order them with an
`ORDER BY`, by a step number as in the
[finance example](https://github.com/glyf-data/glyf/blob/main/examples/finance_metrics/visualisations/margin_bridge.ggsql).
A row with a missing step or change is skipped. The build fails when a step
has the closing bar's name; set `LABEL total` to another.

`y` must be a number. A waterfall takes no `color`: its colours mean up, down
and total, and its legend names only the kinds it draws. It takes `INTERACT
tooltip`, which shows each bar's change and the running total after it;
`zoom` and `legend_filter` fail validation. Dashboard filters do not apply to
it: the running total runs through every row, so the card says it is not
filtered. The visual diff compares a waterfall pixel by pixel.

## See also

- [Bar](bar.md), for amounts that do not add up to one total.
- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [All chart types](overview.md).
