# dbt-charts Docs Site

This is the Docusaurus website for dbt-charts documentation.

## Local development

Install Node.js, then run:

```bash
npm install
npm start
```

Build the static site:

```bash
npm run build
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
