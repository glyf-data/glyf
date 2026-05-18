# Agents

Agents can help analytics engineers move faster when the workflow is explicit and testable.

## Good agent tasks

- Inspect a dbt model and draft `.ggsql` visualisations.
- Add a chart to an existing dashboard YAML file.
- Run `dbt-charts doctor` and summarize project readiness.
- Convert a dashboard request into dbt model, chart, and dashboard file changes.
- Add a GitHub Actions workflow that exports dashboard artifacts.

## Tasks that need human review

- Choosing business metrics.
- Confirming semantic definitions.
- Validating dashboard layout for executives or customers.
- Approving migration assumptions from existing BI tools.

## Recommended guardrails

Ask agents to:

- Keep chart SQL close to dbt model naming.
- Use only supported chart types and directives.
- Run validation commands after editing.
- Preserve existing dashboard YAML unless the requested change requires it.
- Explain unresolved refs, missing manifest files, and DuckDB execution errors directly.

## Starting command set

```bash
uv run dbt-charts doctor --project-dir examples/simple_dbt
uv run dbt-charts validate --project-dir examples/simple_dbt
uv run dbt-charts render --project-dir examples/simple_dbt
uv run dbt-charts dashboard --project-dir examples/simple_dbt
```
