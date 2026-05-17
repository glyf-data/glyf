# Quickstart

This flow uses the included `examples/simple_dbt` project and writes a static dashboard site under `target/ggsql/site`.

## Prerequisites

- Python 3.11 or newer.
- [`uv`](https://docs.astral.sh/uv/) for dependency management.
- A shell from the repository root.

Install project dependencies:

```bash
uv sync --all-groups
```

## Run the example

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

Open the generated dashboard:

```text
examples/simple_dbt/target/ggsql/site/index.html
```

## What happened

`dbt-charts doctor` checked that the dbt project has the required artifacts and chart files.

`dbt-charts render` resolved dbt references, compiled chart SQL, executed the queries, and rendered chart files.

`dbt-charts dashboard` generated dashboard HTML from the rendered artifacts.

`dbt-charts export --clean` copied the dashboard output into a static site folder that can be uploaded to a static host.

## Expected output

```text
target/ggsql/
  compiled/
  charts/
  dashboards/
  site/
  index.html
```

The publish-ready site lives in:

```text
target/ggsql/site/
```

## Next steps

- Learn the [project structure](project-structure.md).
- Run another project from the [examples gallery](../examples/gallery.md).
- Add dbt-charts to an [existing dbt project](existing-dbt-project.md).
