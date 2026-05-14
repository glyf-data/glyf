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
uv run dbt-charts doctor
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean
```

Open:

```text
target/ggsql/site/index.html
```

## Use an existing dbt project

From your dbt project root:

```bash
dbt build
dbt-charts doctor
dbt-charts render
dbt-charts dashboard
dbt-charts export
```

`dbt-charts` does not run dbt for you. It uses dbt artifacts, especially
`target/manifest.json`.
