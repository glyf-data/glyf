# GitHub Actions

This repository includes a dashboard build example at:

```text
.github/workflows/glyf-dashboard.yml
```

## Minimal workflow shape

```yaml
name: glyf dashboard

on:
  workflow_dispatch:
  push:
    branches:
      - main

jobs:
  build-dashboard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install dependencies
        run: uv sync --all-groups

      - name: Build dbt project
        run: |
          cd examples/simple_dbt
          uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
          uv run dbt build --profiles-dir .

      - name: Build glyf site
        run: |
          uv run glyf doctor --project-dir examples/simple_dbt
          uv run glyf build --project-dir examples/simple_dbt --zip

      - name: Upload static site artifact
        uses: actions/upload-artifact@v4
        with:
          name: glyf-site
          path: examples/simple_dbt/target/glyf/site
```

## Credentials

If your dbt profile needs warehouse credentials, configure them with GitHub Actions secrets and environment variables. Keep `glyf.yml` free of secrets.

## Warehouse-backed projects

The workflow above runs a full build on a GitHub-hosted runner, which is fine
for the DuckDB example it builds. For a project whose charts query a
warehouse, a full build pulls every chart's rows onto GitHub's machines. Run
`glyf build --validate` in GitHub Actions instead, and full builds inside your
perimeter — see [where to run builds](../guides/where-to-run-builds.md).
