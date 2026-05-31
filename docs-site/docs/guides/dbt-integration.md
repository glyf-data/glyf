# dbt Integration

`glyf` integrates with dbt through artifacts rather than dbt internals.
It is artifact-driven, not dbt-runtime-driven.

Primary artifact:

```text
target/manifest.json
```

Generate it with:

```bash
dbt compile
```

For executable chart SQL, build the data first:

```bash
dbt seed
dbt run
```

or:

```bash
dbt build
```

## Supported dbt references

```sql
{{ ref('model_name') }}
{{ source('source_name', 'table_name') }}
```

Manifest node types used for `ref()`:

- model
- seed
- snapshot

Sources are resolved from the manifest `sources` section.

## DuckDB execution

The current execution backend is DuckDB. For the examples, `profiles.yml` points dbt at a local `.duckdb` database. If that database exists, `glyf` executes compiled SQL against it.

If no local DuckDB file exists, examples can still use seed CSV fallback for simple demo execution.

`glyf build`, `glyf render`, and the other CLI commands do not run `dbt seed`,
`dbt run`, `dbt build`, or `dbt compile` for you. Run dbt first so both
`target/manifest.json` and the DuckDB relations exist before rendering.

## Practical workflow

Run dbt first, then run glyf:

```bash
dbt build
glyf doctor
glyf build
glyf serve
```

Use the low-level commands only when you need more control:

```bash
glyf validate
glyf render
glyf dashboard
glyf export --clean
```

This keeps dbt model execution and dashboard rendering separate, which makes CI easier to debug.
