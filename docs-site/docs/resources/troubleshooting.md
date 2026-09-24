# Troubleshooting

## Missing `manifest.json`

Error:

```text
Missing target/manifest.json
```

Fix:

```bash
dbt compile
```

or:

```bash
dbt build
```

## Unresolved ref or source

Check that the model or source name exists in dbt:

```bash
dbt ls
```

Then regenerate the manifest:

```bash
dbt compile
```

## No charts found

Check:

- `.ggsql` files exist.
- Files are under `visualisations/`.
- `visualisations_path` in `glyf.yml` is correct.

Run:

```bash
glyf doctor
```

## DuckDB execution error

Usually this means the relation exists in the manifest but not in DuckDB yet.

```bash
dbt build
```

For the bundled examples, run dbt from inside the example directory so the
database file is created under that example's `target/` folder.

For changed seed schemas, use:

```bash
dbt seed --full-refresh
```

## Rendering dependency error

Install dependencies:

```bash
uv sync
```

Rendering needs Altair and `vl-convert-python`.

## A chart changes between builds when the data did not

The rows came back in a different order. For several chart types the order is
part of the picture: which scatter point is drawn on top, the segment order in
a stacked bar, a pie's slices, a table's rows. `glyf diff` reports this as
`the same rows came back in a different order`.

glyf keeps the order still on its own: it orders the rows of a query without
an `ORDER BY`, and adds a tiebreak to an `ORDER BY` that leaves ties. When it
still moves, the build output says why, in a line naming the chart:

- `the query selects *`: glyf settled the ties after the rows came back, but a
  `LIMIT` can still keep different rows. List the columns instead of `*`.
- `the warehouse could not order by the tiebreak`: one of the query's columns
  cannot be sorted. Add an `ORDER BY` that decides every row yourself, from
  columns that can be.

See [Row order](../guides/visualisation-syntax.md#row-order) for the rules.

## DuckDB lock error

DuckDB allows a limited writer concurrency pattern. Run dbt commands sequentially:

```bash
dbt seed
dbt run
dbt compile
glyf render
```
