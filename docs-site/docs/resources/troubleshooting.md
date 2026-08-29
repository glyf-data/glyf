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

## DuckDB lock error

DuckDB allows a limited writer concurrency pattern. Run dbt commands sequentially:

```bash
dbt seed
dbt run
dbt compile
glyf render
```
