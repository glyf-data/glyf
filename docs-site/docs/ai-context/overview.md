# AI Context

AI Context gives coding assistants the project-specific information they need to help with glyf safely.

For glyf, that context is simple: where dbt models live, where chart files live, how dashboard YAML is structured, and which commands prove the generated dashboard still works.

Use this section when you want an assistant to draft `.ggsql` visualisations, update dashboard YAML, explain validation failures, or wire a repeatable dashboard workflow into CI.

## How It Works

The practical workflow is:

1. You ask for a dashboard change.
2. The assistant reads `dbt_project.yml`, `glyf.yml`, `models/`, `target/manifest.json`, `visualisations/`, and `dashboards/`.
3. The assistant creates or updates a `.ggsql` file under `visualisations/`.
4. The assistant adds the chart name to the right dashboard YAML file under `dashboards/`.
5. The assistant runs `glyf doctor`, `validate`, `render`, and `dashboard`.
6. The assistant reports the changed files, validation result, and anything that still needs human review.

That loop keeps the assistant close to the same workflow a developer would follow by hand.

## Example Request

```text
Add a monthly revenue chart from the fct_revenue model and include it in the executive dashboard.
Use glyf syntax only and run validation before you finish.
```

Expected assistant output:

```text
Created visualisations/monthly_revenue.ggsql.
Updated dashboards/executive.yml.
Ran glyf validate and render.
The chart appears in target/glyf/dashboards/executive.html.
```

## Files An Assistant Should Inspect

```text
dbt_project.yml
glyf.yml
models/
target/manifest.json
visualisations/
dashboards/
```

The manifest matters because glyf resolves dbt `ref()` and `source()` calls from `target/manifest.json`.

## Validation Commands

```bash
glyf doctor
glyf validate
glyf render
glyf dashboard
```

When running from outside the dbt project, use:

```bash
glyf validate --project-dir path/to/dbt_project
```

## llms.txt

The docs site includes a compact context index at:

```text
/llms.txt
```

Point assistants at this file when they need a short list of the most useful glyf documentation pages.

## Related pages

- [Agents](agents.md) describes which tasks are safe for agents and which need human review.
- [Assistant setup](assistant-setup.md) gives copyable instructions for Codex and Claude-style assistants.
- [Migrating from Looker](../migrations/looker.md) explains how to evaluate existing dashboard ideas before translating them into glyf.
