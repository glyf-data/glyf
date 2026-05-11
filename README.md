# dbt-ggsql

Chart-as-code dashboards for dbt projects.

dbt-ggsql lets users define visualisations close to their dbt models using ggsql-style SQL files, render them into images/specs, and publish them as static dashboards.

## CLI

This early implementation discovers project files, parses `.ggsql`, resolves basic
`ref()` calls using `target/manifest.json`, and writes placeholder chart artifacts.
It does not execute dbt, run SQL, or render real charts yet.

```bash
uv sync
uv run dbt-ggsql list --project examples/basic
uv run dbt-ggsql validate --project examples/basic
uv run dbt-ggsql render --project examples/basic
```

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
