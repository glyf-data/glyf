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

Chart SQL runs where the backend points. The default is a DuckDB database
beside the project; the `dbt` backend reaches whatever the project's
`profiles.yml` names, including a Trino cluster.

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

`type: duckdb` and `type: trino` targets execute today. A profile naming
another warehouse is reported as unsupported rather than silently ignored; see
`ARCHITECTURE.md` for where that is going.

### Trino

Install the driver extra, then point `backend: dbt` at a dbt-trino target:

```bash
pip install 'glyf-core[trino]'
```

<!-- glyf-docs: skip — a dbt-trino profiles.yml, dbt's file rather than a glyf spec -->
```yaml title="~/.dbt/profiles.yml"
my_project:
  target: prod
  outputs:
    prod:
      type: trino
      host: trino.example.com
      port: 443
      user: "{{ env_var('TRINO_USER') }}"
      password: "{{ env_var('TRINO_PASSWORD') }}"
      method: ldap
      http_scheme: https
      database: analytics   # the catalog; dbt-trino calls it database
      schema: marts
```

The auth methods glyf honours are `none`, `ldap` (user and password), and
`jwt` (`jwt_token`); a profile using another method is rejected loudly rather
than connected unauthenticated. `database` and `schema` become the session
catalog and schema, so unqualified table names in hand-written SQL resolve —
`ref()`-resolved SQL is already fully qualified and does not need them.

`glyf doctor` checks the whole chain before a build does: the resolved
backend, profile and target, whether the driver extra is installed, and a
`select 1` probe against the warehouse.

Every `glyf build` runs every chart's query against the cluster. In CI,
`execution.mode: validate` proves each query still runs and binds its columns
without fetching data, and `execution.max_rows` bounds what a full build will
pull; see the [configuration reference](../reference/configuration.md).

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
