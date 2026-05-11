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

`validate` checks malformed `.ggsql`, unresolved refs, missing manifests, and
dashboard chart names that do not match discovered `.ggsql` file names.

`render` writes generated files under `target/ggsql/`:

- `compiled/<chart>.sql`
- `charts/<chart>.json`
- `charts/<chart>.png`
- `charts/<chart>.svg`
- `dashboards/<dashboard>.html`
- `index.html`

For local examples, CSV files in `seeds/` are loaded into DuckDB using the CSV
filename as the table name.

`dashboard` reads YAML files in `dashboards/` and generates static HTML pages from
the rendered chart artifacts. SVG is embedded directly when available, with PNG as
a fallback.
