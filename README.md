# dbt-charts

[![Tests](https://github.com/kannandreams/dbt-charts/actions/workflows/test.yml/badge.svg)](https://github.com/kannandreams/dbt-charts/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/kannandreams/dbt-charts/branch/main/graph/badge.svg)](https://codecov.io/gh/kannandreams/dbt-charts)
[![PyPI version](https://img.shields.io/pypi/v/dbt-charts.svg)](https://pypi.org/project/dbt-charts/)
[![Python versions](https://img.shields.io/pypi/pyversions/dbt-charts.svg)](https://pypi.org/project/dbt-charts/)
[![License](https://img.shields.io/pypi/l/dbt-charts.svg)](LICENSE)

Chart-as-code dashboards for dbt projects.

`dbt-charts` discovers `.ggsql` visualisation files in a dbt project, resolves dbt
`ref()` and `source()` calls from `target/manifest.json`, executes chart SQL with
DuckDB, renders PNG/SVG charts with Altair, and exports static dashboards.

## Status

Alpha-stage Python CLI. Useful for local analytics, static dashboard prototypes,
and repeatable reporting artifacts that live beside dbt projects. It is not a
dbt adapter, BI server, or hosted dashboard service.

## Installation

Install the CLI:

```bash
pip install dbt-charts
```

Or keep it isolated with `uv`:

```bash
uv tool install dbt-charts
```

When developing from this repository, install dependencies with `uv`:

```bash
uv sync
```

For the included dbt examples, dev dependencies include `dbt-core` and
`dbt-duckdb`.

## CI Run

This project uses Taskfile to run the same checks locally and in GitHub Actions.
Install Task before running these commands:

```bash
brew install go-task
task --version
```

Run the full CI pipeline:

```bash
task ci
```

Run CI with a specific Python version:

```bash
task ci PYTHON_VERSION=3.12
```

Run individual CI steps:

```bash
task install
task test
task build
task dashboard-ci
```

## Copy-Paste Quickstart

In a dbt project:

```bash
dbt-charts init
dbt build
dbt-charts doctor
dbt-charts validate
dbt-charts render
dbt-charts dashboard
dbt-charts export --clean
```

For the included example project:

```bash
uv sync
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run dbt-charts validate
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean
```

Open:

```text
examples/simple_dbt/target/ggsql/site/index.html
```

## CLI

```bash
uv run dbt-charts init
uv run dbt-charts doctor
uv run dbt-charts list
uv run dbt-charts validate
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean --zip
uv run dbt-charts serve
```

Point at another project:

```bash
uv run dbt-charts render --project-dir examples/sales_dashboard
```

Preview a generated dashboard locally:

```bash
uv run dbt-charts serve --project-dir examples/simple_dbt
uv run dbt-charts serve --project-dir examples/simple_dbt --host 127.0.0.1 --port 8080
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

The Docusaurus docs site source lives in [docs-site](docs-site/). It is intended
to be the primary documentation experience with a landing page, quickstart,
examples gallery, command reference, integrations, AI context, and community
resources.

Run it locally after installing Node.js:

```bash
cd docs-site
npm install
npm start
```

Existing Markdown docs are still available while the site is being introduced:

- [Getting started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Visualisation syntax](docs/visualisation-syntax.md)
- [Dashboard YAML](docs/dashboard-yaml.md)
- [dbt integration](docs/dbt-integration.md)
- [CI/CD](docs/ci-cd.md)
- [Release process](docs/release.mdxplain)
- [Troubleshooting](docs/troubleshooting.md)

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the detailed future roadmap.

Near-term themes:

- richer chart syntax while keeping the parser small
- more dashboard layouts
- better error messages for dbt adapter-specific execution failures
- snapshot tests for generated HTML
- optional publish helpers for common static hosts
- local `serve` and `watch` workflows after the release baseline is stable

## License

`dbt-charts` is released under the
[Apache License 2.0](LICENSE).

## Common Issues

- Missing `target/manifest.json`: run `dbt compile` or `dbt build`.
- Unresolved `ref()` or `source()`: check the dbt model/source names in the
  generated manifest.
- No charts found: check `visualisations_path` in `dbt_charts.yml`.
- DuckDB execution error: run `dbt seed` and `dbt run` before `dbt-charts render`.
- Rendering dependency error: run `uv sync` to install Altair and
  `vl-convert-python`.
