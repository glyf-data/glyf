# Agents

Agents can help analytics engineers move faster when the task is narrow, the project context is available, and every change is validated.

In glyf, an agent should behave like a careful contributor: inspect files first, make small chart or dashboard changes, run the CLI checks, and explain what still needs human judgment.

## Good Tasks For Agents

- Inspect a dbt model and draft `.ggsql` visualisations.
- Add a chart to an existing dashboard YAML file.
- Run `glyf doctor` and summarize project readiness.
- Convert a dashboard request into chart and dashboard file changes.
- Add a GitHub Actions workflow that exports dashboard artifacts.
- Explain unresolved refs, missing manifest files, or DuckDB execution errors.

## Tasks That Need Human Review

- Choosing business metrics.
- Confirming semantic definitions.
- Validating dashboard layout for executives or customers.
- Approving migration assumptions from existing BI tools.
- Deciding whether dbt models should change.
- Publishing dashboards that contain customer or private business data.

## Guardrails To Give An Agent

Ask agents to:

- Read `glyf.yml` before assuming directory names.
- Keep chart SQL close to dbt model naming.
- Use only supported chart types and directives.
- Run validation commands after editing.
- Preserve existing dashboard YAML unless the requested change requires it.
- Report unresolved refs, missing manifest files, and DuckDB execution errors directly.
- Summarize every file changed.

## Good Prompt Shape

```text
Add a chart for <metric> from <dbt model>.
Read glyf.yml and target/manifest.json first.
Create or update only the required .ggsql and dashboard YAML files.
Run glyf doctor and validate.
Tell me what changed and what still needs review.
```

## Starting Command Set

```bash
uv run glyf doctor --project-dir examples/simple_dbt
uv run glyf validate --project-dir examples/simple_dbt
uv run glyf render --project-dir examples/simple_dbt
uv run glyf dashboard --project-dir examples/simple_dbt
```

For a real project, replace `examples/simple_dbt` with the path to the dbt project.
