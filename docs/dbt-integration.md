# dbt Integration

`glyf` integrates with dbt through artifacts rather than dbt internals.

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

The current execution backend is DuckDB. For the examples, `profiles.yml` points
dbt at a project-local `.duckdb` database under `target/`. If that database
exists, `glyf` executes compiled SQL against it.

If no local DuckDB file exists, examples can still use seed CSV fallback for simple
demo execution.

`glyf render` does not run `dbt seed`, `dbt run`, `dbt build`, or `dbt compile`
for you. Run dbt first so both `target/manifest.json` and the DuckDB relations
exist before rendering.
