import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Funnel

One centred bar per step, as wide as its value: how many reach each step of a
process, and how many drop out on the way.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="funnel" title="Funnel" example="examples/product_analytics/visualisations/account_funnel.ggsql" summary="One centred bar per step, narrowing as the value falls. Shows how many get from each step to the next.">

```sql
SELECT 1 AS step_order, 'All accounts' AS step, count(*) AS accounts
FROM {{ ref('fct_account_sessions') }}
UNION ALL
SELECT 2, 'Regular use', count(*)
FROM {{ ref('fct_account_sessions') }}
WHERE sessions >= 15
UNION ALL
SELECT 3, 'Heavy use', count(*)
FROM {{ ref('fct_account_sessions') }}
WHERE sessions >= 40
UNION ALL
SELECT 4, 'Heavy use, long sessions', count(*)
FROM {{ ref('fct_account_sessions') }}
WHERE sessions >= 40 AND avg_session_minutes >= 15
ORDER BY step_order

VISUALISE step AS x, accounts AS y
DRAW funnel
LABEL title => 'From Sign-up to Power Use'
LABEL subtitle => 'Accounts at each level of use, and their share of all accounts'
CONFIG width => 1100
CONFIG height => 280
INTERACT tooltip
```

</ChartTypeCard>

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `funnel` | `x` (the step), `y` (how many reach it) | `tooltip` only | glyf |

## How it reads

```sql
SELECT step, users
FROM {{ ref('fct_signup_steps') }}
ORDER BY step_number

VISUALISE step AS x, users AS y
DRAW funnel
INTERACT tooltip
```

A funnel is one row per step: its name (`x`) and how many reach it (`y`). The
steps run top to bottom in the order the query returns them, so order them
with an `ORDER BY`, by a step number as in the
[product analytics example](https://github.com/glyf-data/glyf/blob/main/examples/product_analytics/visualisations/account_funnel.ggsql).
A query without an `ORDER BY` gets its steps largest first, which is a
funnel's usual shape.

Each bar is centred and as wide as its value against the widest step. Its
label is the value and its share of the first step, `2,600 · 22%`; the label
sits inside the bar when it fits and beside it when it does not. With
`INTERACT tooltip`, a bar also shows its share of the step before it: the
conversion from one step to the next.

`y` must be a number of zero or more; a negative value fails the build. A row
with a missing step or value is skipped. A funnel takes no `color`, and
`zoom` and `legend_filter` fail validation. Dashboard filters do not apply to
it: the shares are of the first step, worked out from every row, so the card
says it is not filtered. The visual diff compares a funnel pixel by pixel.

## See also

- [Bar](bar.md), for amounts that are not steps of one process.
- [Sankey](sankey.md), for where the ones who drop out go instead.
- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [All chart types](overview.md).
