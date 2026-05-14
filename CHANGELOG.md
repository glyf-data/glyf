# Changelog

All notable changes to `dbt-charts` will be documented in this file.

## 0.1.0 - Unreleased

Initial experimental alpha release.

- Typer CLI with `list`, `validate`, `render`, `dashboard`, `export`, and `doctor`.
- Project discovery for `.ggsql`, dashboard YAML, and dbt artifacts.
- dbt `ref()` and `source()` resolution from `target/manifest.json`.
- DuckDB SQL execution.
- Altair chart rendering to SVG and PNG.
- Static dashboard generation and exportable site folder.
- Optional `dbt_charts.yml` project configuration.
- Example dbt projects and documentation.
