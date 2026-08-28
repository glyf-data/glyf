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

The docs site is hosted on Cloudflare Pages:

```text
https://glyf.pages.dev
```

The Pages project name is `glyf`. During the beta the site sits behind
Cloudflare Access, so it is reachable only by signed-in maintainers.

Deploys are manual. `.github/workflows/docs-site.yml` only builds the site and
uploads the result as a workflow artifact, so a broken page fails CI without
needing any Cloudflare credentials in the repository.

To publish, build locally and deploy with your own wrangler login:

```bash
cd docs-site
npm run build
npx wrangler@4 pages deploy build --project-name=glyf --branch=main
```

`wrangler login` handles authentication once per machine; no
`CLOUDFLARE_API_TOKEN` secret is stored in the repository.

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
