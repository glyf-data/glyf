<div align="center">

<img src="https://raw.githubusercontent.com/glyf-data/glyf/main/docs-site/static/img/glyf-logo-v4.svg" alt="" width="84" />

# glyf

**Open source visualization build tool for your data pipeline.**

Ship charts from the same pipeline as your data.<br />
Define charts in SQL, compose dashboards in YAML, publish anywhere.

[![PyPI](https://img.shields.io/pypi/v/glyf-core?style=flat-square&label=pypi&color=008f5f&labelColor=0f172a)](https://pypi.org/project/glyf-core/)
[![Tests](https://img.shields.io/github/actions/workflow/status/glyf-data/glyf/test.yml?branch=main&style=flat-square&label=tests&color=008f5f&labelColor=0f172a)](https://github.com/glyf-data/glyf/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-0047FF?style=flat-square&labelColor=0f172a)](https://github.com/glyf-data/glyf/blob/main/pyproject.toml)
[![Rust](https://img.shields.io/badge/rust-1.83%2B-0047FF?style=flat-square&labelColor=0f172a)](https://github.com/glyf-data/glyf/blob/main/crates/glyf-core/Cargo.toml)
[![License](https://img.shields.io/badge/license-Apache%202.0-475569?style=flat-square&labelColor=0f172a)](https://github.com/glyf-data/glyf/blob/main/LICENSE)

[Install](#install) · [Quickstart](#quickstart) · [How it works](#how-it-works) · [CLI](#cli) · [Examples](#examples) · [Docs](#documentation)

</div>

```text
  ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
  │     dbt project      │   │     glyf sources     │   │      glyf build      │
  ├──────────────────────┤   ├──────────────────────┤   ├──────────────────────┤
  │ models/*.sql         │   │ charts     *.ggsql   │   │ resolve  ref()       │
  │ target/manifest.json │──▶│ dashboards *.yml     │──▶│ execute  DuckDB      │
  │ warehouse relations  │   │ macros     *.py      │   │ render   Altair      │
  └──────────────────────┘   └──────────────────────┘   └───────────┬──────────┘
                                                                    │
      ┌─────────────────────────┬───────────────────────┬───────────┘
      ▼                         ▼                       ▼
      site/index.html           charts/*.png *.svg      export --zip
      static dashboard          chart artifacts         zip for CI
```

---

## The last mile

Every stage of the modern data stack has declarative, version-controlled,
testable artifacts. Every stage except visualization.

> Your models are versioned. Your jobs are automated. Your data quality is
> tested. **Visualization is still the last artifact outside the pipeline.**

- **Dashboards live outside the workflow.** Your dbt models are in Git. Your
  charts are usually configured in a browser, stored elsewhere, and maintained
  by whoever last touched the UI.
- **Columns rename, charts break silently.** When dbt models change, dashboard
  failures show up late. glyf moves chart definitions into a build step that
  validates earlier.
- **Publishing should not require a vendor.** For internal portals and product
  dashboards, rendered HTML and chart assets are usually enough.

glyf is artifact-driven, not dbt-runtime-driven: run dbt first, then run glyf
against the resulting artifacts and relations.

## Install

glyf is published on PyPI as **`glyf-core`**. The package installs the `glyf`
command and the `glyf` Python module; only the distribution name differs.

```bash
uv tool install glyf-core
glyf --version
```

<details>
<summary><b>Other ways to install</b> — one-line script, Homebrew, pipx, pip, offline</summary>

<br />

**One-line script** (macOS and Linux). Installs `uv` first if it is missing,
never uses `sudo`, and accepts `--update`, `--version X`, and `--help`:

```bash
curl -fsSL https://raw.githubusercontent.com/glyf-data/glyf/main/install.sh | sh
```

**Homebrew.** `brew trust` is required, not optional — Homebrew 6.0 refuses to
load formulae from untrusted third-party taps:

```bash
brew tap glyf-data/glyf
brew trust --tap glyf-data/glyf
brew install glyf
```

**pipx or pip.** Prefer `uv` or `pipx` for a CLI tool; use `pip` when you want
`glyf` inside an existing project virtualenv, next to `dbt-core`:

```bash
pipx install glyf-core
python -m pip install glyf-core
```

**Offline or air-gapped.** Every [release](https://github.com/glyf-data/glyf/releases)
ships platform wheels, an sdist, and a `checksums.txt`:

```bash
sha256sum --check --ignore-missing checksums.txt
uv tool install ./glyf_core-<version>-cp311-abi3-<platform>.whl
```

</details>

Prebuilt wheels cover Linux (x86_64, aarch64), macOS (Intel, Apple Silicon),
and Windows (x86_64). They target Python 3.11+ through the stable ABI, so one
wheel per platform covers every supported Python version and no Rust toolchain
is needed. Upgrade with `uv tool upgrade glyf-core`.

## Quickstart

In an existing dbt project:

```bash
glyf init      # scaffold glyf.yml, visualisations/, dashboards/
dbt build      # produce the dbt artifacts glyf reads
glyf doctor    # check artifacts, charts, and DuckDB execution
glyf build     # compile, render, and export the site
glyf serve     # preview it locally
```

`doctor` reports whether the dbt artifacts, chart files, and DuckDB execution
are ready before your first build, so the first failure is a readable message
rather than a stack trace.

## How it works

### 01 — Write charts in GGSQL

SQL you already know, extended with a visualization grammar. Use `ref()` to
reference dbt models directly, exactly as a dbt model would:

```sql
SELECT month, revenue
FROM {{ ref('fct_orders') }}

VISUALISE month AS x, revenue AS y
DRAW line
LABEL title => 'Monthly Revenue'
LABEL subtitle => 'Revenue trend from dbt model'
CONFIG width => 900
```

glyf resolves each reference to its schema path from `target/manifest.json` and
validates the query before it renders anything.

### 02 — Compose dashboards in YAML

Lay charts out into sections. Use Python macros for labels, thresholds, and
reusable components, so a dashboard change is a one-line diff in review:

```yaml
name: executive
title: Executive Dashboard

summary:
  - "{{ ui.label_value('Owner', 'Analytics Engineering') }}"
  - "{{ ui.label_value('Generated', time.now('%Y-%m-%d %H:%M')) }}"

layout:
  columns: 3

sections:
  - title: Revenue overview
    columns: 3
    items:
      - metric:
          label: Sample revenue
          value: "$7.6k"
      - chart: revenue
        title: Monthly revenue
        width: 2
```

### 03 — Build once, publish anywhere

One command resolves dbt artifacts, validates chart specs, executes chart SQL
with DuckDB, renders charts with Altair, and emits files you can publish:

```text
target/glyf/
├── compiled/     resolved SQL
├── charts/       rendered PNG / SVG
├── dashboards/   dashboard specs
└── site/         self-contained static site  ← publish this
```

No BI server to maintain. Drop `site/` into S3, GitHub Pages, a docs site, or a
CI artifact.

## CLI

| Command | What it does |
| --- | --- |
| `glyf init` | Scaffold glyf config, chart, and dashboard directories |
| `glyf doctor` | Check dbt artifacts, chart files, and DuckDB execution |
| `glyf build` | Full pipeline: compile, render, and export |
| `glyf serve` | Serve the generated site locally |
| `glyf list` | List discovered charts and dashboards |
| `glyf validate` | Validate chart and dashboard specs without rendering |
| `glyf render` | Render charts only |
| `glyf dashboard` | Build dashboards only |
| `glyf export` | Export the publishable site (`--clean`, `--zip`) |

Point any command at another project with `--project-dir`:

```bash
glyf build --project-dir examples/sales_dashboard
```

## Examples

Four runnable projects live in [`examples/`](https://github.com/glyf-data/glyf/blob/main/examples/README.md):
`simple_dbt`, `sales_dashboard`, `product_analytics`, and `finance_metrics`.

```bash
uv sync
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run glyf build
uv run glyf serve
```

Then open `examples/simple_dbt/target/glyf/site/index.html`.

## Who it's for

| | |
| --- | --- |
| **Analytics Engineer** | You work in dbt and version-control everything. You should not need LookML or a BI platform UI to publish a declared dashboard artifact. |
| **Data Scientist** | Write SQL-style chart definitions that run in the pipeline and stay current, instead of one-off notebooks that drift. |
| **Data Leader** | Open source, runs locally, and produces outputs your team already knows how to deploy and review. |
| **Application Engineer** | The data team owns the spec; you consume rendered output without negotiating with an embedded analytics vendor. |

## Status

| Capability | |
| --- | --- |
| dbt `ref()` and `source()` resolution from `manifest.json` | shipped |
| GGSQL chart definitions, DuckDB execution, Altair rendering | shipped |
| Dashboard YAML, Python macros, self-contained static site | shipped |
| PNG / SVG chart artifacts and `--zip` export | shipped |
| Generated typed React components | planned |
| MCP server so agents can reason about the chart graph | planned |
| Visual diff between builds as a CI artifact | planned |

See [ROADMAP.md](https://github.com/glyf-data/glyf/blob/main/ROADMAP.md) for the
longer view.

## Documentation

The full docs site is built from [`docs-site/`](https://github.com/glyf-data/glyf/blob/main/docs-site)
and published at [glyf.pages.dev](https://glyf.pages.dev). These guides are also
readable directly in the repository:

| | |
| --- | --- |
| [Quickstart](https://github.com/glyf-data/glyf/blob/main/docs-site/docs/get-started/quickstart.md) | First build, end to end |
| [Configuration](https://github.com/glyf-data/glyf/blob/main/docs-site/docs/reference/configuration.md) | `glyf.yml` reference |
| [Visualisation syntax](https://github.com/glyf-data/glyf/blob/main/docs-site/docs/guides/visualisation-syntax.md) | The GGSQL grammar |
| [Dashboard YAML](https://github.com/glyf-data/glyf/blob/main/docs-site/docs/guides/dashboard-yaml.md) | Layout, sections, macros |
| [dbt integration](https://github.com/glyf-data/glyf/blob/main/docs-site/docs/guides/dbt-integration.md) | Artifacts, `ref()`, adapters |
| [CI/CD](https://github.com/glyf-data/glyf/blob/main/docs-site/docs/guides/ci-cd.md) | Building glyf in a pipeline |
| [Troubleshooting](https://github.com/glyf-data/glyf/blob/main/docs-site/docs/resources/troubleshooting.md) | Common failures |

## Contributing

<details>
<summary><b>Developing from this repository</b></summary>

<br />

```bash
uv sync
```

Dev dependencies include `dbt-core` and `dbt-duckdb` for the bundled examples.

This project uses [Task](https://taskfile.dev) to run the same checks locally
and in GitHub Actions:

```bash
brew install go-task
task ci                      # the full pipeline
task ci PYTHON_VERSION=3.12  # against a specific Python
```

Individual steps: `task install`, `task test`, `task coverage`, `task build`,
`task dashboard-ci`. `task test` runs pytest with coverage and writes
`coverage.xml`, which CI uploads to Codecov.

Run the docs site locally with Node.js installed:

```bash
cd docs-site
npm install
npm start
```

</details>

Issues and pull requests are welcome. Paths in `glyf.yml` and dashboard YAML use
forward slashes on every platform.

## License

[Apache 2.0](https://github.com/glyf-data/glyf/blob/main/LICENSE)
