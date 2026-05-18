# dbt-charts Docs Site

This is the Docusaurus website for dbt-charts documentation.

## Local development

Install Node.js, then run:

```bash
npm install
npm start
```

Open:

```text
http://localhost:3000/dbt-charts/
```

If port `3000` is busy, choose another port:

```bash
npm start -- --port 3001
```

Open:

```text
http://localhost:3001/dbt-charts/
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
