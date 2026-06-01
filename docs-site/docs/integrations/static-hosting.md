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
glyf render
glyf dashboard
glyf export --clean --zip
```

## Publish

Upload:

```text
target/glyf/site/
```

or:

```text
target/glyf/glyf-site.zip
```

No running Python service is needed after export.
