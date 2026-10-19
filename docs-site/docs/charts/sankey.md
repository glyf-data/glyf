import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Sankey

Flows between stages, one band per `source` and `target` pair, as wide as its `value`.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="sankey" title="Sankey" example="examples/product_analytics/visualisations/account_flow.ggsql" summary="Flows between stages, each band as wide as its value. Shows where things go.">

```sql
WITH accounts AS (
  SELECT
    plan,
    CASE
      WHEN sessions >= 40 THEN 'Heavy use'
      WHEN sessions >= 15 THEN 'Regular use'
      ELSE 'Light use'
    END AS activity,
    CASE WHEN avg_session_minutes >= 15 THEN 'Long sessions' ELSE 'Short sessions' END AS session_length
  FROM {{ ref('fct_account_sessions') }}
)
SELECT plan AS stage, activity AS next_stage, count(*) AS accounts
FROM accounts
GROUP BY 1, 2
UNION ALL
SELECT activity, session_length, count(*)
FROM accounts
GROUP BY 1, 2
ORDER BY 1, 2

VISUALISE stage AS source, next_stage AS target, accounts AS value
DRAW sankey
LABEL title => 'How Accounts Use the Product'
LABEL subtitle => 'Accounts by plan, then by how often and how long they use it'
CONFIG width => 1100
CONFIG height => 420
INTERACT tooltip
```

</ChartTypeCard>

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `sankey` | `source`, `target`, `value` | `tooltip` only | glyf |

## How it reads

```sql
WITH accounts AS (
  SELECT plan, CASE WHEN sessions >= 15 THEN 'Regular use' ELSE 'Light use' END AS activity
  FROM {{ ref('fct_account_sessions') }}
)
SELECT plan AS stage, activity AS next_stage, count(*) AS accounts
FROM accounts
GROUP BY 1, 2
ORDER BY 1, 2

VISUALISE stage AS source, next_stage AS target, accounts AS value
DRAW sankey
INTERACT tooltip
```

A sankey is one row per flow: where it starts (`source`), where it ends
(`target`) and how much moves along it (`value`). A flow of three stages is
two sets of rows, the first stage to the second and the second to the third,
joined with `UNION ALL`, as in the
[product analytics example](https://github.com/glyf-data/glyf/blob/main/examples/product_analytics/visualisations/account_flow.ggsql).

glyf lays it out itself. A node's column is the longest chain of flows that
leads to it, and a node with nothing flowing out of it goes to the last
column. Each node is as tall as the larger of what arrives and what leaves.
Rows that link the same two nodes are summed. A row with a missing end or
value, or a value of zero, is skipped. Within a column, a node sits near the
nodes that feed it, so fewer bands cross. Each node's colour comes from the
order the query first names it in, so keep the `ORDER BY`.

The build fails, naming the chart, when the flows cannot be drawn:

- a loop, such as `A` to `B` and `B` back to `A`: every flow has to move to a
  later stage;
- a flow from a node to itself, or a negative value;
- more nodes in one column than `CONFIG height` has room for. Raise the
  height, or group the smallest flows in SQL.

A sankey takes `INTERACT tooltip`: a band shows its two ends and its value,
and a node shows its total. It has no legend, because each node is already
labelled. Dashboard filters do not apply to it: its spec carries the laid-out
picture rather than the rows, so the card says it is not filtered. The visual
diff compares a sankey pixel by pixel.

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
