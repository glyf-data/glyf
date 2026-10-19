import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Combo

Bars of `y` on the left axis and a line of `y2` on the right, over one `x`.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="combo" title="Combo" example="examples/finance_metrics/visualisations/bookings_and_margin.ggsql" summary="Bars of one measure and a line of another over the same x, each on its own axis. Shows a total and a rate together.">

```sql
SELECT
  month,
  sum(bookings) as bookings,
  round(sum(gross_margin) * 100.0 / nullif(sum(bookings), 0), 1) as margin_rate
FROM {{ ref('fct_finance') }}
GROUP BY 1
ORDER BY 1

VISUALISE month AS x, bookings AS y, margin_rate AS y2
DRAW combo
LABEL title => 'Bookings and Margin Rate'
LABEL subtitle => 'Bars are bookings; the line is gross margin as a share of them'
LABEL x_title => 'Month'
LABEL y_title => 'Bookings'
LABEL y2_title => 'Margin Rate (%)'
CONFIG width => 1100
CONFIG height => 320
INTERACT tooltip
```

</ChartTypeCard>

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `combo` | `x`, `y` (bars), `y2` (line) | `tooltip` only | glyf |

## How it reads

```sql
SELECT month, sum(revenue) AS revenue, round(avg(margin_pct), 1) AS margin_pct
FROM {{ ref('fct_orders') }}
GROUP BY 1
ORDER BY 1

VISUALISE month AS x, revenue AS y, margin_pct AS y2
DRAW combo
LABEL y_title => 'Revenue'
LABEL y2_title => 'Margin (%)'
INTERACT tooltip
```

A combo puts two measures that do not share a unit on one chart: a total and
a rate, such as bookings and the margin on them. `y` is drawn as bars against
the left axis and `y2` as a line against the right. The two axes have their
own scales, so neither measure is squashed to fit the other.

To keep the reader from reading the line against the bars' axis, each axis
title takes the colour of its mark, and a legend at the top names both. The
legend's words are the axis titles: `LABEL y_title` and `LABEL y2_title`, or
the column names when those are not set.

`x` is drawn as one band per value, so every bar is a full bar wide. A text
`x` keeps the order the query returned it in, so keep the `ORDER BY`. A date
`x` is ordered by date, one band per month when every date is the first of
one, otherwise one per day.

`y` and `y2` must be numbers. A combo takes no `color`: its two colours are
its two measures. It takes `INTERACT tooltip`, which shows `x`, `y` and `y2`
together on either mark; `zoom` and `legend_filter` fail validation, because
two independent axes have no single zoom and the legend names marks, not
values. Dashboard filters redraw both marks together. The visual diff
compares a combo pixel by pixel.

## See also

- [Bar](bar.md) and [Line](line.md), for one measure.
- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [All chart types](overview.md).
