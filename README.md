# dbt-ggsql

Chart-as-code dashboards for dbt projects.

dbt-ggsql lets users define visualisations close to their dbt models using ggsql-style SQL files, render them into images/specs, and publish them as static dashboards.

## Milestone 1 CLI

This early implementation discovers project files and validates basic references using
`target/manifest.json`. It does not execute dbt, run SQL, or render charts yet.

```bash
uv sync
uv run dbt-ggsql list --project examples/basic
uv run dbt-ggsql validate --project examples/basic
```

The scanner currently discovers:

- `.ggsql` files
- dashboard YAML files under `dashboards/`
- `target/manifest.json`

`validate` resolves simple `{{ ref('model_name') }}` expressions against model
`relation_name` values in the manifest and checks that dashboard chart names match
discovered `.ggsql` file names.
