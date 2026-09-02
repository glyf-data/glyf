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
`profiles.yml` names — a Trino cluster, Snowflake, or BigQuery.

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

`type: duckdb`, `type: trino`, `type: snowflake` and `type: bigquery`
targets execute today. A profile naming another warehouse is reported as
unsupported rather than silently ignored; see `ARCHITECTURE.md` for where
that is going.

`glyf doctor` checks the whole chain before a build does: the resolved
backend, profile and target, whether the driver extra is installed, and a
`select 1` probe against the warehouse.

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

### Snowflake

```bash
pip install 'glyf-core[snowflake]'
```

The executor connects over ADBC and follows dbt-snowflake's field names.
`account`, `user`, `database`, `warehouse`, `schema` and `role` map straight
through. Auth methods honoured: password (the default), key-pair
(`private_key_path`, with an optional `private_key_passphrase`),
`authenticator: externalbrowser`, and `authenticator: oauth` with a `token`.
Anything else — an Okta URL, `username_password_mfa` — is rejected loudly.

<!-- glyf-docs: skip — a dbt-snowflake profiles.yml, dbt's file rather than a glyf spec -->
```yaml title="~/.dbt/profiles.yml"
my_project:
  target: prod
  outputs:
    prod:
      type: snowflake
      account: acme-xy12345
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      private_key_path: ~/.ssh/snowflake_key.p8
      database: analytics
      warehouse: reporting
      schema: marts
      role: reporter
```

### BigQuery

```bash
pip install 'glyf-core[bigquery]'
```

Also over ADBC, following dbt-bigquery's field names — aliases included:
`project` or `database` is the billing project, `dataset` or `schema` the
default dataset, and `location` passes through. Auth methods honoured map
one-to-one onto the driver's: `oauth` (application default credentials — run
`gcloud auth application-default login` first), `service-account` (a
`keyfile` path), `service-account-json` (`keyfile_json` inline), and
`oauth-secrets` (`client_id`, `client_secret`, `refresh_token`).

<!-- glyf-docs: skip — a dbt-bigquery profiles.yml, dbt's file rather than a glyf spec -->
```yaml title="~/.dbt/profiles.yml"
my_project:
  target: prod
  outputs:
    prod:
      type: bigquery
      method: service-account
      project: acme-analytics
      dataset: marts
      keyfile: "{{ env_var('BIGQUERY_KEYFILE') }}"
      location: EU
```

### Cost and CI

Every `glyf build` runs every chart's query against the warehouse. In CI,
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

## Tagging PII in `schema.yml`

glyf reads column classification from the manifest, so tagging a column as PII
where the dbt project already documents it is enough:

<!-- glyf-docs: skip — a dbt schema.yml, dbt's file rather than a glyf spec -->
```yaml title="models/schema.yml"
models:
  - name: dim_customers
    columns:
      - name: email
        meta:
          pii: true
      - name: phone
        tags: [pii]
```

Either spelling counts. A chart that reads `dim_customers` and returns `email`
or `phone` then fails the build, or has those values redacted, depending on
`privacy.on_pii` in `glyf.yml` — see
[keeping PII out of a chart](../reference/configuration.md#keeping-pii-out-of-a-chart).
Run `dbt compile` after editing `schema.yml`; glyf reads the manifest, not the
YAML.
