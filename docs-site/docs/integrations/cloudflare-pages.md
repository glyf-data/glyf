# Cloudflare Pages

Cloudflare Pages is the planned host for this documentation site.

The first hosted URL should use the default Pages domain:

```text
https://dbtcharts.pages.dev
```

Cloudflare Pages default domains use this shape:

```text
<project-name>.pages.dev
```

That means `docs.dbt-charts.pages.dev` is not the right starting format. Use `dbtcharts` as the Pages project name, then add `docs.dbtcharts.com` later as a custom domain.

If `dbtcharts` is not available in your Cloudflare account, choose the closest available project name and update both `CLOUDFLARE_PROJECT_NAME` and `DOCS_SITE_URL` in the workflow together.

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

The Docusaurus config defaults to:

```text
DOCS_SITE_URL=https://dbtcharts.pages.dev
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
docs.dbtcharts.com
```

Keep the Pages project name as `dbtcharts`. The custom domain should be added in Cloudflare Pages after the default `pages.dev` deployment is working and private access has been validated.
