# glyf

[![Tests](https://github.com/kannandreams/glyf/actions/workflows/test.yml/badge.svg)](https://github.com/kannandreams/glyf/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/kannandreams/glyf/branch/main/graph/badge.svg)](https://codecov.io/gh/kannandreams/glyf)
[![PyPI version](https://img.shields.io/pypi/v/glyf.svg)](https://pypi.org/project/glyf/)
[![Python versions](https://img.shields.io/pypi/pyversions/glyf.svg)](https://pypi.org/project/glyf/)
[![License](https://img.shields.io/pypi/l/glyf.svg)](LICENSE)

A semantic visualization layer for analytical systems.

`glyf` turns analytical metadata and SQL-first visualisation files into
versioned chart artifacts and static dashboards. Its first integration reads dbt
project artifacts, resolves dbt `ref()` and `source()` calls from
`target/manifest.json`, executes chart SQL with DuckDB, renders PNG/SVG charts
with Altair, and exports publishable dashboard sites.

## Status

Alpha-stage Python CLI. Useful for local analytics, static dashboard prototypes,
and repeatable reporting artifacts that live beside analytical systems. It is
not a dbt adapter, BI server, or hosted dashboard service.

## Installation

Install from a GitHub Release wheel:

```bash
uv tool install \
  https://github.com/kannandreams/glyf/releases/download/v0.1.0/glyf-0.1.0-<platform>.whl
```

Replace `<platform>` with the wheel asset that matches your OS and architecture.

PyPI publishing is intentionally deferred for now.

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
task coverage
task build
task dashboard-ci
```

`task test` runs pytest with coverage and writes `coverage.xml`; CI uploads that
report to Codecov for the README coverage badge.

## Copy-Paste Quickstart

In a dbt project:

```bash
glyf init
dbt build
glyf doctor
glyf validate
glyf render
glyf dashboard
glyf export --clean
```

For the included example project:

```bash
uv sync
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run glyf validate
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean
```

This creates the example DuckDB database at
`examples/simple_dbt/target/simple_dbt.duckdb`.

Open:

```text
examples/simple_dbt/target/ggsql/site/index.html
```

## CLI

```bash
uv run glyf init
uv run glyf doctor
uv run glyf list
uv run glyf validate
uv run glyf render
uv run glyf dashboard
uv run glyf export --clean --zip
uv run glyf serve
```

Point at another project:

```bash
uv run glyf render --project-dir examples/sales_dashboard
```

Preview a generated dashboard locally:

```bash
uv run glyf serve --project-dir examples/simple_dbt
uv run glyf serve --project-dir examples/simple_dbt --host 127.0.0.1 --port 8080
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

`glyf` is released under the
[Apache License 2.0](LICENSE).

## Common Issues

- Missing `target/manifest.json`: run `dbt compile` or `dbt build`.
- Unresolved `ref()` or `source()`: check the dbt model/source names in the
  generated manifest.
- No charts found: check `visualisations_path` in `glyf.yml`.
- DuckDB execution error: run `dbt build` before `glyf render`.
- Rendering dependency error: run `uv sync` to install Altair and
  `vl-convert-python`.
