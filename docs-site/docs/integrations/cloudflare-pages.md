# Cloudflare Pages

Cloudflare Pages is the planned host for this documentation site.

The first hosted URL should use the default Pages domain:

```text
https://glyf.pages.dev
```

Cloudflare Pages default domains use this shape:

```text
<project-name>.pages.dev
```

That means `docs.glyf.pages.dev` is not the right starting format. Use `glyf` as the Pages project name, then add `docs.glyf.com` later as a custom domain.

If `glyf` is not available in your Cloudflare account, choose the closest available project name and update both `CLOUDFLARE_PROJECT_NAME` and `DOCS_SITE_URL` in the workflow together.

## Deployment model

The repository builds and deploys the Docusaurus site from:

```text
docs-site/
```

The deploy workflow is:

```text
.github/workflows/docs-site.yml
```

It runs on pull requests as a build check. It deploys only when changes land on `main`.

## GitHub secrets

Add these repository secrets before merging a deploy change to `main`:

```text
CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_API_TOKEN
```

Create the API token in Cloudflare with Account, Cloudflare Pages, Edit permission.

## Build settings

The GitHub Action builds with:

```bash
cd docs-site
npm ci
npm run build
```

The deployed output is:

```text
docs-site/build
```

## Dashboard child pages

Docusaurus copies everything under `docs-site/static/` into the build root. Committed dashboard exports under:

```text
docs-site/static/dashboards/
```

are deployed as child pages under:

```text
https://glyf.pages.dev/dashboards/
```

For local development, use root-relative links such as:

```text
/dashboards/simple-dbt/dashboards/executive.html
```

This resolves to localhost when running `npm start` or `npm run serve`, and to `glyf.pages.dev` after deployment.

To refresh the deployed child pages:

```bash
task dashboard-ci EXAMPLE_PROJECT=examples/simple_dbt
task dashboard-ci EXAMPLE_PROJECT=examples/sales_dashboard
task dashboard-ci EXAMPLE_PROJECT=examples/product_analytics
task dashboard-ci EXAMPLE_PROJECT=examples/finance_metrics
```

Then copy each generated `target/glyf/site/` folder into the matching `docs-site/static/dashboards/<example>/` folder, build locally, commit, push, and merge to `main`.

The Docusaurus config defaults to:

```text
DOCS_SITE_URL=https://glyf.pages.dev
DOCS_SITE_BASE_URL=/
```

If a temporary GitHub Pages build is needed later, override those values in the workflow instead of changing the default config.

## Local verification

Run:

```bash
cd docs-site
npm install
npm start
```

Open:

```text
http://localhost:3000/
```

Build before opening a PR:

```bash
npm run build
```

## Future custom domain

Later, add:

```text
docs.glyf.com
```

Keep the Pages project name as `glyf`. The custom domain should be added in Cloudflare Pages after the default `pages.dev` deployment is working and private access has been validated.
