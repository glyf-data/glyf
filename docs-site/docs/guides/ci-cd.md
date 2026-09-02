# CI/CD

`glyf` generates a static site from dbt artifacts and rendered chart outputs. The site in `target/glyf/site/` can be uploaded by any CI/CD system that can run Python commands.

## Local workflow

From a dbt project root:

```bash
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run glyf doctor
uv run glyf build --zip
```

The publish-ready files are written to:

```text
target/glyf/site/
```

The optional zip archive is written to:

```text
target/glyf/glyf-site.zip
```

## Where each step runs

`dbt build` executes inside the warehouse. `glyf build` pulls each chart's
result rows to the machine running it, so on a GitHub-hosted runner the data
leaves your warehouse's boundary. The recommended split is `glyf build
--validate` in CI — zero rows moved — and full builds inside the perimeter,
published from the pipeline under a service role. See
[where to run builds](./where-to-run-builds.md).

## GitHub Actions

This repository includes an example dashboard workflow:

```text
.github/workflows/glyf-dashboard.yml
```

The workflow checks out the repository, installs `uv`, installs dependencies, builds a dbt example project, runs `glyf`, and uploads the static site as a workflow artifact.

For your own project, change the `examples/simple_dbt` paths to your dbt project directory. If your dbt profile needs credentials, provide them through GitHub Actions secrets and environment variables.

Run the dbt commands from the dbt project directory, or pass `--project-dir` to both dbt and glyf, so profile-relative paths such as a DuckDB database file resolve inside that project.

## GitHub Pages

The workflow includes a commented `publish-pages` job. To use it:

1. Enable GitHub Pages from GitHub Actions in repository settings.
2. Uncomment the `publish-pages` job.
3. Ensure the site artifact path points at your generated `target/glyf/site/`.

No external CDN is required. The exported HTML uses relative links, and chart SVGs/PNGs are copied into the site folder.
