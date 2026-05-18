# AI Context

This section is a placeholder for making dbt-charts easier to use with coding agents and AI assistants.

The goal is to give agents enough context to help users:

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

## Suggested agent prompt

```text
You are helping me use dbt-charts in a dbt project.
Read the dbt models, target/manifest.json, existing .ggsql files, and dashboards/*.yml.
Suggest chart definitions that use supported dbt-charts syntax.
Run dbt-charts doctor and validate before changing dashboard YAML.
```

## Future work

- Add a dedicated AI context bundle.
- Add a Codex skill placeholder.
- Add a Claude project instruction placeholder.
- Add migration prompts for Looker and other BI tools.
