# Troubleshooting

## Missing manifest.json

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

Check that the model/source name exists in dbt:

```bash
dbt ls
```

Then regenerate the manifest:

```bash
dbt compile
```

## No charts found

Check:

- `.ggsql` files exist
- files are under `visualisations/`
- `visualisations_path` in `dbt_ggsql.yml` is correct

Run:

```bash
dbt-ggsql doctor
```

## DuckDB execution error

Usually this means the relation exists in the manifest but not in DuckDB yet.

Run:

```bash
dbt seed
dbt run
```

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

## DuckDB lock error

DuckDB allows a limited writer concurrency pattern. Run dbt commands sequentially:

```bash
dbt seed
dbt run
dbt compile
dbt-ggsql render
```
