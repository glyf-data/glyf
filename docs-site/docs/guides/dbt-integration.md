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

## Execution

Chart SQL runs against DuckDB. Which DuckDB depends on the backend.

The default, `backend: duckdb`, looks for a database beside the project —
`target/<project>.duckdb`, then `<project>.duckdb` — and falls back to reading
the seed CSVs, which is what lets the examples render before dbt has run.

`backend: dbt` reads the project's `profiles.yml` instead and connects where the
selected target points, the way dbt does:

```yaml title="glyf.yml"
execution:
  backend: dbt
  target: dev          # optional; defaults to the profile's own target
```

Nothing is guessed: if the target names a database that does not exist, glyf
says so rather than connecting to an empty one. `env_var()` is expanded in the
profile, so credentials stay out of the file. `profiles.yml` is looked for the
way dbt looks for it — `DBT_PROFILES_DIR`, the project directory, then `~/.dbt`
— unless `execution.profiles_dir` says otherwise.

Only `type: duckdb` targets execute today. A profile naming another warehouse
is reported as unsupported rather than silently ignored; see `ARCHITECTURE.md`
for where that is going.

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
