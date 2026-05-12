# Visualisation Syntax

A `.ggsql` file contains SQL followed by a small chart block.

```sql
SELECT month, revenue, region
FROM {{ ref('fct_sales') }}

VISUALISE month AS x, revenue AS y, region AS color
DRAW bar
LABEL title => 'Revenue by Region'
LABEL subtitle => 'Grouped monthly revenue'
LABEL x_title => 'Month'
LABEL y_title => 'Revenue'
CONFIG width => 900
CONFIG height => 500
```

## Required directives

- `VISUALISE`: maps query columns to chart roles.
- `DRAW`: chooses a chart type.

Required roles:

- `x`
- `y`

Optional role:

- `color`

## Chart types

- `line`
- `bar`
- `scatter`
- `area`
- `pie`

## Labels

- `title`
- `subtitle`
- `x_title`
- `y_title`

## Config

- `width`: positive integer
- `height`: positive integer

The parser is intentionally small. It does not parse SQL; SQL is passed through
after dbt refs and sources are resolved.
