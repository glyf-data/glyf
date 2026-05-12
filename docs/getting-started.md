# Getting Started

## Install dependencies

```bash
uv sync
```

## Run the simplest example

```bash
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run dbt-ggsql doctor
uv run dbt-ggsql render
uv run dbt-ggsql dashboard
uv run dbt-ggsql export --clean
```

Open:

```text
target/ggsql/site/index.html
```

## Use an existing dbt project

From your dbt project root:

```bash
dbt build
dbt-ggsql doctor
dbt-ggsql render
dbt-ggsql dashboard
dbt-ggsql export
```

`dbt-ggsql` does not run dbt for you. It uses dbt artifacts, especially
`target/manifest.json`.
