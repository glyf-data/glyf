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

## Before you publish

A static host serves whatever the files contain, to whoever can reach them. By
default a glyf site carries the rows behind its charts — inline in the dashboard
HTML — along with the compiled SQL and its table names. Read [what a published
site exposes](../guides/data-exposure.md) before pointing a public bucket at
`site/`, and build with `export.row_data: exclude` if the site should carry
pictures without the data behind them.
