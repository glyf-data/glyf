# CI/CD for glyf

`glyf` generates a static site from dbt artifacts and rendered chart outputs.
The site in `target/ggsql/site/` can be uploaded by any CI/CD system that can run
Python commands.

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
target/ggsql/site/
```

The optional zip archive is written to:

```text
target/ggsql/glyf-site.zip
```

## GitHub Actions workflow

This repository includes an example workflow:

```text
.github/workflows/glyf-dashboard.yml
```

The workflow:

- checks out the repository
- installs `uv`
- installs dependencies
- changes into the example dbt project directory
- runs `dbt seed` and `dbt build`
- runs `glyf doctor`
- runs `glyf build`
- uploads the static site as a workflow artifact

For your own project, run the dbt commands from the dbt project directory so
profile-relative paths such as DuckDB database files resolve inside that
project. If your dbt profile needs credentials, provide them through GitHub
Actions secrets and environment variables.

## GitHub Pages

The workflow includes a commented `publish-pages` job. To use it:

1. Enable GitHub Pages from GitHub Actions in repository settings.
2. Uncomment the `publish-pages` job.
3. Ensure the site artifact path points at your generated `target/ggsql/site/`.

No external CDN is required. The exported HTML uses relative links, and chart
SVGs/PNGs are copied into the site folder.

## Other static hosts

You can publish `target/ggsql/site/` to any static host, including:

- Cloudflare Pages
- Netlify
- S3 static website hosting
- Azure Static Web Apps
- any internal static file host

Use `glyf build --zip` when the target platform expects a single archive.
