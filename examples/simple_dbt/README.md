# simple_dbt

A tiny dbt-style project for testing `glyf` against realistic dbt artifact
shapes.

The committed `target/manifest.json` is intentionally minimal but follows the dbt
manifest structure used by models and sources.

Example flow:

```bash
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run glyf render
uv run glyf dashboard
```

This creates the example DuckDB database at `target/simple_dbt.duckdb`.

`--no-partial-parse` is useful if you have previously run this example from a
different working directory and dbt has cached old file paths.

Run the dbt commands from the example directory so the DuckDB file stays inside
that project's `target/` folder.
