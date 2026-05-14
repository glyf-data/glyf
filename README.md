# dbt-charts

Chart-as-code dashboards for dbt projects.

`dbt-charts` discovers `.ggsql` visualisation files in a dbt project, resolves dbt
`ref()` and `source()` calls from `target/manifest.json`, executes chart SQL with
DuckDB, renders PNG/SVG charts with Altair, and exports static dashboards.

## Status

Experimental Python CLI. Useful for demos, local analytics, and static dashboard
prototypes. It is not a dbt adapter, BI server, or hosted dashboard service.

## Installation

This project uses `uv`:

```bash
uv sync
```

For the included dbt examples, dev dependencies include `dbt-core` and
`dbt-duckdb`.

## Copy-Paste Quickstart

```bash
uv sync
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export
```

Open:

```text
examples/simple_dbt/target/ggsql/site/index.html
```

## CLI

```bash
uv run dbt-charts doctor
uv run dbt-charts list
uv run dbt-charts validate
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean --zip
```

Point at another project:

```bash
uv run dbt-charts render --project-dir examples/sales_dashboard
```

## Example Output

Generated files are written under `target/ggsql/`:

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

## Examples

See [examples/README.md](examples/README.md).

- `examples/simple_dbt`
- `examples/sales_dashboard`
- `examples/product_analytics`
- `examples/finance_metrics`

## Documentation

- [Getting started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Visualisation syntax](docs/visualisation-syntax.md)
- [Dashboard YAML](docs/dashboard-yaml.md)
- [dbt integration](docs/dbt-integration.md)
- [CI/CD](docs/ci-cd.md)
- [Release process](docs/release.mdxplain)
- [Troubleshooting](docs/troubleshooting.md)

## Roadmap

- richer chart syntax while keeping the parser small
- more dashboard layouts
- better error messages for dbt adapter-specific execution failures
- snapshot tests for generated HTML
- optional publish helpers for common static hosts

## Common Issues

- Missing `target/manifest.json`: run `dbt compile` or `dbt build`.
- Unresolved `ref()` or `source()`: check the dbt model/source names in the
  generated manifest.
- No charts found: check `visualisations_path` in `dbt_charts.yml`.
- DuckDB execution error: run `dbt seed` and `dbt run` before `dbt-charts render`.
- Rendering dependency error: run `uv sync` to install Altair and
  `vl-convert-python`.
