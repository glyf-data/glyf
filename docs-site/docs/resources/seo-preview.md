# SEO And Preview Assets

This page tracks launch-readiness assets for the docs site.

The hosted docs are private for now, so the immediate goal is not search indexing. The near-term goal is to keep metadata and preview assets ready for the moment the site becomes public.

## Current stance

- Keep the docs private behind Cloudflare Access.
- Keep `llms.txt` available inside the private site for agent workflows.
- Avoid public SEO work until the project is ready to be discoverable.
- Use Cloudflare preview deployment `noindex` behavior for any future preview URLs.

## Public launch checklist

Before making the docs public:

- Confirm the production URL.
- Confirm whether `docs.glyf.com` is live.
- Replace planning screenshots with real dashboard captures.
- Add a social preview image under `docs-site/static/img/`.
- Update Docusaurus `themeConfig.image` to use the social preview image.
- Review page titles and descriptions.
- Confirm sitemap output from the Docusaurus production build.
- Decide whether `llms.txt` should point to `pages.dev` or the custom domain.

## Social preview direction

The preview image should show:

- `glyf` name.
- The tagline: `Open Source Visualization build tool to data pipeline`.
- A compact generated dashboard screenshot.
- A clean light background that matches the docs theme.

## Release checklist

Keep these items in the release checklist:

- announcement bar updates
- screenshot refreshes
- social preview refreshes
- `llms.txt` URL changes
- public SEO validation
