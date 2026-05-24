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
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean
```

Open:

```text
target/ggsql/site/index.html
```

## Use an existing dbt project

From your dbt project root:

```bash
dbt build
glyf doctor
glyf render
glyf dashboard
glyf export
```

`glyf` does not run dbt for you. It uses dbt artifacts, especially
`target/manifest.json`.
