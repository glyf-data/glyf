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
uv run glyf doctor
uv run glyf build
uv run glyf serve
```

This creates the example DuckDB database at `target/simple_dbt.duckdb`.

Open:

```text
target/glyf/site/index.html
```

## Use an existing dbt project

From your dbt project root:

```bash
dbt build
glyf doctor
glyf build
glyf serve
```

`glyf` is artifact-driven, not dbt-runtime-driven. It does not run dbt for you.
It uses dbt artifacts, especially
`target/manifest.json`.
