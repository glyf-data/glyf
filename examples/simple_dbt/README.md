# simple_dbt

A tiny dbt-style project for testing `dbt-ggsql` against realistic dbt artifact
shapes.

The committed `target/manifest.json` is intentionally minimal but follows the dbt
manifest structure used by models and sources.

Example flow:

```bash
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run dbt-ggsql render
uv run dbt-ggsql dashboard
```

`--no-partial-parse` is useful if you have previously run this example from a
different working directory and dbt has cached old file paths.

From the repository root, use:

```bash
uv run dbt seed --project-dir examples/simple_dbt --profiles-dir examples/simple_dbt
uv run dbt run --project-dir examples/simple_dbt --profiles-dir examples/simple_dbt
uv run dbt compile --project-dir examples/simple_dbt --profiles-dir examples/simple_dbt
uv run dbt-ggsql render --project-dir examples/simple_dbt
uv run dbt-ggsql dashboard --project-dir examples/simple_dbt
```
