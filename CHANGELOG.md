# Changelog

All notable changes to `glyf` will be documented in this file.

## Unreleased

- Dropped `polars` and `pandas` as dependencies. Query results are Arrow
  tables end to end and charts are built from them directly, which halves the
  installed size (about 260 MB instead of 530 MB). `build_chart` and
  `QueryResult.from_dataframe` accept any dataframe that implements the Arrow
  PyCapsule interface — polars, pandas 2.2+, pyarrow, or a DuckDB relation —
  so passing your own frame still works; `to_polars()` and `to_pandas()`
  remain and import the library on demand.

## 0.3.0 - 2026-08-26

First release published to PyPI.

- Renamed the PyPI distribution to `glyf-core`; the `glyf` command and
  `import glyf` are unchanged. `pip install glyf-core` / `uv tool install
  glyf-core` are the supported install paths going forward.
- Fixed the release workflow: replaced the retired `macos-13` runner, build
  wheels for x86_64 and aarch64 Linux, Intel and Apple Silicon macOS, and
  x86_64 Windows, and attach a `checksums.txt` to every GitHub Release.
- Trimmed the source distribution to the package, Rust crate, tests, and
  top-level metadata (docs site and examples are no longer bundled).
- Fetch DuckDB results as Arrow via ADBC and split the executors into explicit
  modules; cast Arrow decimal columns to native numbers.
- Added dashboard spec validation to `glyf validate` and a `--verbose` mode for
  `glyf build`.
- Macro system enhancements: custom macros, macro-aware validation, and new
  macro examples; fixed `ui.list` rendering.
- Dashboard UI: dark mode, refresh time and tags from YAML, and assorted
  layout fixes; data and JSON moved out of the exported site.
- Added the `bundle.json` artifact with build metadata and an embedded
  analytics documentation page.
- Moved the repository to the `glyf-data` organisation and enforced
  conventional commit messages in CI.

## 0.2.0 - 2026-06-02

Dashboard rendering system redesign. Tagged as `v0.2.0`; no artifacts were
published because the release workflow failed on the retired `macos-13`
runner.

- Reworked generated dashboard HTML into a product-style static UI shell with a
  header, metadata bar, filter placeholder, toolbar actions, chart content,
  source drawer, AI Summary panel, and lookback modal placeholder.
- Split dashboard rendering into `DashboardRenderer`, `AssetManager`, theme
  metadata, componentized Jinja templates, and a shared `dashboard.css` asset.
- Moved compiled SQL out of individual chart cards and into the dashboard
  `Source` drawer.
- Added linked dashboard CSS assets under `target/glyf/assets` and exported
  static sites under `target/glyf/site/assets`.
- Added built-in AI Summary macros: `ai.summary`, `ai.insight`, and
  `ai.signal`.
- Updated dashboard YAML documentation with toolbar behavior, field
  definitions, built-in macros, custom macro guidance, and source drawer
  behavior.
- Refreshed generated example dashboard previews in the docs site.
- Updated dashboard/export tests to cover linked assets, source drawer output,
  AI Summary macros, and the redesigned dashboard shell.

## 0.1.0 - 2026-05-31

Initial experimental alpha release.

- Typer CLI with `list`, `validate`, `render`, `dashboard`, `export`, and `doctor`.
- Project discovery for `.ggsql`, dashboard YAML, and dbt artifacts.
- dbt `ref()` and `source()` resolution from `target/manifest.json`.
- DuckDB SQL execution.
- Altair chart rendering to SVG and PNG.
- Static dashboard generation and exportable site folder.
- Optional `glyf.yml` project configuration.
- Example dbt projects and documentation.
- GitHub Release workflow for platform wheels and source distribution artifacts.
