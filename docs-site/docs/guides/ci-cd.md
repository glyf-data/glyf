# CI/CD

`dbt-charts` generates a static site from dbt artifacts and rendered chart outputs. The site in `target/ggsql/site/` can be uploaded by any CI/CD system that can run Python commands.

## Local workflow

From a dbt project root:

```bash
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt build --profiles-dir .
uv run dbt-charts doctor
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean --zip
```

The publish-ready files are written to:

```text
target/ggsql/site/
```

The optional zip archive is written to:

```text
target/ggsql/dbt-charts-site.zip
```

## GitHub Actions

This repository includes an example dashboard workflow:

```text
.github/workflows/dbt-charts-dashboard.yml
```

The workflow checks out the repository, installs `uv`, installs dependencies, builds a dbt example project, runs `dbt-charts`, and uploads the static site as a workflow artifact.

For your own project, change the `examples/simple_dbt` paths to your dbt project directory. If your dbt profile needs credentials, provide them through GitHub Actions secrets and environment variables.

## GitHub Pages

The workflow includes a commented `publish-pages` job. To use it:

1. Enable GitHub Pages from GitHub Actions in repository settings.
2. Uncomment the `publish-pages` job.
3. Ensure the site artifact path points at your generated `target/ggsql/site/`.

No external CDN is required. The exported HTML uses relative links, and chart SVGs/PNGs are copied into the site folder.
