import ChartTypeCard from '@site/src/components/ChartTypeCard';

# Table

The rows themselves, one column per listed column. Not drawn: no PNG or SVG.

<div className="chartTypeGrid chartTypeGrid--single">

<ChartTypeCard type="table" title="Table" example="examples/product_analytics/visualisations/top_accounts.ggsql" summary="The rows themselves, one column per listed column. For when the exact values matter.">

```sql
SELECT account_id, plan, sessions, avg_session_minutes
FROM {{ ref('fct_account_sessions') }}
ORDER BY sessions DESC, account_id
LIMIT 10

VISUALISE *
DRAW table
LABEL title => 'Most active accounts'
LABEL account_id => 'Account'
LABEL avg_session_minutes => 'Avg minutes'
CONFIG height => 360
```

</ChartTypeCard>

</div>

| `DRAW` | Roles | Interactions | From |
| --- | --- | --- | --- |
| `table` | a column list, or `*` | none: a table takes no `INTERACT` clause, and sorting by column is built into the dashboard | glyf |

## How it reads

```sql
SELECT account_id, plan, sessions
FROM {{ ref('fct_account_sessions') }}
ORDER BY sessions DESC
LIMIT 10

VISUALISE account_id, plan, sessions
DRAW table
LABEL title => 'Most active accounts'
LABEL account_id => 'Account'
CONFIG height => 360
```

A table is its rows, so `VISUALISE` lists the columns to show, in order,
without roles. `VISUALISE *` shows every column the query returns, in the
order it returns them. A column the query does not return fails the build with
the column's name; `x AS`, `y AS` and the other roles are rejected for a
table, and a column list is rejected for every other chart type, each error
saying what the chart wanted instead.

`LABEL <column> => '...'` names a column's header; a column without one shows
its name. `CONFIG height` bounds the table's height and the rows scroll inside
it; `CONFIG width` bounds its width. `INTERACT` is rejected: a table's rows are
already readable, and the dashboard lets a reader sort by clicking a header.

A table is not drawn. The build writes `charts/<name>.table.html`, a plain
`<table>` fragment, beside the usual data JSON and metadata, and never a PNG
or an SVG. The dashboard shows the fragment in a card; the bundle records the
table's columns and the fragment's path with `png` and `svg` set to `null`.

Two settings follow from that. [`render.max_rows`](../reference/configuration.md#how-many-rows-a-table-may-list)
(default `1000`) fails a table that would list more rows, naming the chart,
the way `render.max_marks` does for a picture. And
[`export.row_data: exclude`](../guides/data-exposure.md) fails a table at validation,
because a picture can be published without its rows and a table cannot.

## See also

- [Visualisation syntax](../guides/visualisation-syntax.md): the directives every chart shares, `LABEL`, `CONFIG` and `INTERACT`.
- [Row order](../guides/visualisation-syntax.md#row-order): when the order of the query's rows is part of the picture.
- [All chart types](overview.md).
