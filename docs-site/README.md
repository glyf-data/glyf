# glyf Docs Site

This is the Docusaurus website for glyf documentation.

## Local development

Install Node.js, then run:

```bash
npm install
npm start
```

From the repository root the same steps are `make docs-install` and
`make docs-dev`; `make docs-build` builds the static site.

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

## Refreshing the demo dashboards

The four dashboards linked from the examples gallery are real `glyf build`
output, committed so the gallery has something to link to. To regenerate one,
build the example and copy the result, mapping the underscore in the example
name to a hyphen:

```bash
uv run glyf build --project-dir examples/simple_dbt
rsync -a --delete \
  --exclude 'site/' --exclude 'glyf-site.zip' --exclude 'data/' \
  examples/simple_dbt/target/glyf/ \
  docs-site/static/dashboards/simple-dbt/
```

**Do not copy `target/glyf/` wholesale.** It contains three things the docs
site must not carry, each of which is a copy of content already committed:

| Excluded | Why |
| --- | --- |
| `site/` | A self-contained export of the *same* charts and dashboards. Copying it duplicates every file. |
| `glyf-site.zip` | The `--zip` archive of that same export, ~224 KB per demo. |
| `data/` | Chart data, unused here: dashboards are built with `embed_charts: true`, so the HTML already inlines it. |

Copying the whole directory is exactly how this went wrong before: 106
byte-identical files, 2.58 MB, about half the repository's checkout, removed in
[glyf#102](https://github.com/glyf-data/glyf/pull/102).

Keep the flat half — `assets/`, `charts/`, `compiled/`, `dashboards/`,
`index.html`. The gallery links to
`/dashboards/<name>/dashboards/<file>.html`, so nothing needs `site/`.

A current build also emits `bundle.json` (~8 KB), which the demos predate. It
is kept: no page loads it, but it is the artifact Glyf Studio and the
JavaScript packages consume, so a published one is useful to point at.

After copying, check the links still resolve:

```bash
npm run build
```

## Publishing

The published site is:

```text
https://glyf.pages.dev
```

`.github/workflows/docs-site.yml` builds the site on every pull request and
push to `main` and uploads the result as a workflow artifact, so a broken page
fails CI. Publishing the built site is handled by the maintainers with
`make docs-deploy`, which needs a logged-in `wrangler`.

The planned custom domain is:

```text
docs.glyfdata.com
```

If another host is needed later, override the build URL and base path:

```bash
DOCS_SITE_URL=https://example.com DOCS_SITE_BASE_URL=/ npm run build
```

## Examples are tested

`tests/test_docs.py` runs the documented examples, so a page cannot drift away
from the code it describes. Four checks, all from the repository root as part
of `make ci`:

| Check | What fails it |
| --- | --- |
| Dashboard YAML blocks load | A block using a field the loader does not accept. |
| Macro expressions resolve | A macro called with arguments its signature rejects. |
| Example pages match their file | `examples/product-analytics.md` or `examples/finance-metrics.md` drifting from the `dashboards/*.yml` it presents as shipped. |
| Every block is accounted for | A block that is none of the above and is not marked to skip — usually a misspelled top-level key. |

Blocks are routed by shape, so nothing needs annotating. A YAML block whose
top-level keys are dashboard keys is checked whole or partial — a bare
`toolbar:` is spliced into a minimal spec first — and one shaped like a section
item, such as a lone `component:`, is spliced in as an item so its macro really
is evaluated. A block whose keys are neither, on a page not listed in
`NON_DASHBOARD_PAGES`, fails the last check rather than quietly going
unchecked, which is the point: the drift most worth catching is a block that
stops looking like a dashboard.

Macros resolve against the real thing: a page presenting a shipped example file
is checked against that example project's `dashboards/macros.py`, and any other
page against the `macros.py` it documents itself. They are never pooled, since
the same macro name is deliberately simpler in a guide than in an example.

A block that is *meant* to be invalid — showing a mistake, say — opts out with
an HTML comment on the line above its fence:

````markdown
<!-- glyf-docs: skip -->
```yaml
this: block
is: not checked
```
````

Nothing in the docs uses it today. Prefer fixing the block over marking it.

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
