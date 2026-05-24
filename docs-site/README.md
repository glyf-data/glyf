# glyf Docs Site

This is the Docusaurus website for glyf documentation.

## Local development

Install Node.js, then run:

```bash
npm install
npm start
```

Open:

```text
http://localhost:3000/
```

If port `3000` is busy, choose another port:

```bash
npm start -- --port 3001
```

Open:

```text
http://localhost:3001/
```

Build the static site:

```bash
npm run build
```

Preview the production build:

```bash
npm run serve
```

Then open the URL printed by Docusaurus.

Static files under `docs-site/static/` are copied to the site root. For example, dashboard exports committed under `docs-site/static/dashboards/simple-dbt/` are served locally as `/dashboards/simple-dbt/` and deployed as `https://glyf.pages.dev/dashboards/simple-dbt/`.

## Cloudflare Pages

The docs site defaults to Cloudflare Pages:

```text
https://glyf.pages.dev
```

Deployments are handled by:

```text
.github/workflows/docs-site.yml
```

Required GitHub secrets:

```text
CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_API_TOKEN
```

The Cloudflare Pages project name is:

```text
glyf
```

If that Pages project name is unavailable, update both `CLOUDFLARE_PROJECT_NAME` and `DOCS_SITE_URL` in the workflow.

The planned custom domain is:

```text
docs.glyf.com
```

If another host is needed later, override the build URL and base path:

```bash
DOCS_SITE_URL=https://example.com DOCS_SITE_BASE_URL=/ npm run build
```

## Maintenance model

Use `docs-site/docs` as the source for public documentation. Keep root-level package docs and examples focused on repository usage, then link readers here for the full developer experience.

## Structure

```text
docs-site/
  docs/
  src/pages/
  src/css/
  static/
  docusaurus.config.js
  sidebars.js
```
