# AI Context

AI Context gives coding assistants enough project knowledge to make useful, reviewable changes in a dbt-charts project.

Use it when you want an assistant to:

- Add `.ggsql` visualisations from dbt models.
- Create dashboard YAML from existing chart files.
- Explain CLI failures from `dbt-charts doctor`, `validate`, or `render`.
- Propose CI workflows for publishing generated dashboards.

## llms.txt

The docs site includes a starting `llms.txt` file at:

```text
/llms.txt
```

It should list the most useful documentation URLs for language models and coding agents. Keep it short and stable.

## Starter prompt

```text
You are helping me use dbt-charts in a dbt project.
Read the dbt models, target/manifest.json, existing .ggsql files, and dashboards/*.yml.
Suggest chart definitions that use supported dbt-charts syntax.
Run dbt-charts doctor and validate before changing dashboard YAML.
```

## Related pages

- [Agents](agents.md) describes useful tasks and guardrails.
- [Assistant setup](assistant-setup.md) gives copyable instructions for Codex and Claude-style assistants.
- [Migrating from Looker](../migrations/looker.md) describes how to evaluate existing dashboard ideas before translating them into dbt-charts.
