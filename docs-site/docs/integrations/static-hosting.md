# Static Hosting

The exported dashboard site is static HTML plus chart artifacts. You can publish it anywhere that serves static files.

## Supported hosting style

- GitHub Pages.
- Cloudflare Pages.
- Netlify.
- S3-compatible object storage.
- Azure Static Web Apps.
- Internal static file servers.

## Build

```bash
dbt build
dbt-charts render
dbt-charts dashboard
dbt-charts export --clean --zip
```

## Publish

Upload:

```text
target/ggsql/site/
```

or:

```text
target/ggsql/dbt-charts-site.zip
```

No running Python service is needed after export.
