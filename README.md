# dbt-ggsql

Chart-as-code dashboards for dbt projects.

dbt-ggsql lets users define visualisations close to their dbt models using ggsql-style SQL files, render them into images/specs, and publish them as static dashboards.

## CLI

This implementation discovers project files, parses `.ggsql`, resolves basic
`ref()` calls using `target/manifest.json`, executes the compiled SQL locally with
DuckDB, and renders PNG/SVG chart artifacts with Altair.

It does not execute dbt itself or provide a dashboard server yet.

```bash
uv sync
uv run dbt-ggsql list --project examples/basic
uv run dbt-ggsql validate --project examples/basic
uv run dbt-ggsql render --project examples/basic
uv run dbt-ggsql dashboard --project examples/basic
uv run dbt-ggsql export --project examples/basic
```

For real dbt projects, run dbt first so `target/manifest.json` exists:

```bash
dbt build
dbt-ggsql render
dbt-ggsql dashboard
```

You can point at another dbt project root with `--project-dir`:

```bash
uv run dbt-ggsql validate --project-dir examples/simple_dbt
uv run dbt-ggsql render --project-dir examples/simple_dbt
uv run dbt-ggsql dashboard --project-dir examples/simple_dbt
uv run dbt-ggsql export --project-dir examples/simple_dbt
```

`dbt-ggsql` depends on dbt artifacts rather than invoking dbt itself. The key
artifact is:

```text
target/manifest.json
```

`ref()` and `source()` calls in `.ggsql` files are resolved from that manifest.

The scanner currently discovers:

- `.ggsql` files
- dashboard YAML files under `dashboards/`
- `target/manifest.json`

## Configuration

`dbt-ggsql` uses sensible defaults, so a config file is optional. If present,
`dbt_ggsql.yml` is loaded from the dbt project root. You can also pass a config
explicitly:

```bash
uv run dbt-ggsql render --config dbt_ggsql.yml
uv run dbt-ggsql dashboard --config dbt_ggsql.yml
uv run dbt-ggsql export --config dbt_ggsql.yml
```

Default conventions:

```yaml
visualisations_path: visualisations
dashboards_path: dashboards
output_path: target/ggsql
compiled_path: target/ggsql/compiled
charts_path: target/ggsql/charts
dashboards_output_path: target/ggsql/dashboards
site_path: target/ggsql/site

render:
  formats:
    - svg
    - png
  default_width: 800
  default_height: 400

dashboard:
  theme: light
  embed_charts: true
  show_compiled_sql: true
```

Paths are resolved relative to the dbt project root. Use path settings to keep
visualisations, dashboard YAML, or generated artifacts in custom folders.

`validate` checks malformed `.ggsql`, unresolved refs, missing manifests, and
dashboard chart names that do not match discovered `.ggsql` file names.

`render` writes generated files under `target/ggsql/`:

- `compiled/<chart>.sql`
- `charts/<chart>.json`
- `charts/<chart>.png`
- `charts/<chart>.svg`
- `dashboards/<dashboard>.html`
- `index.html`

Supported chart syntax stays intentionally small:

```sql
SELECT month, revenue, region
FROM {{ ref('fct_orders') }}

VISUALISE month AS x, revenue AS y, region AS color
DRAW bar
LABEL title => 'Revenue by Region'
LABEL subtitle => 'Revenue trend from dbt model'
LABEL x_title => 'Month'
LABEL y_title => 'Revenue'
CONFIG width => 900
CONFIG height => 500
```

Supported chart types are `line`, `bar`, `scatter`, `area`, and `pie`.
`x` and `y` mappings are required. `color`, labels, and width/height config are
optional.

For local examples, CSV files in `seeds/` are loaded into DuckDB using the CSV
filename as the table name.

`dashboard` reads YAML files in `dashboards/` and generates static HTML pages from
the rendered chart artifacts. SVG is embedded directly when available, with PNG as
a fallback.

`export` creates a publish-ready static site:

```bash
uv run dbt-ggsql render
uv run dbt-ggsql dashboard
uv run dbt-ggsql export
```

The exported site is written to:

```text
target/ggsql/site/
```

That folder can be hosted as a static website on GitHub Pages, Cloudflare Pages,
Netlify, S3 static hosting, or opened locally. Use `--clean` to rebuild the site
folder from scratch, and `--zip` to create `target/ggsql/dbt-ggsql-site.zip`.
