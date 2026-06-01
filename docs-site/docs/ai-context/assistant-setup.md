# Assistant Setup

Use this page to give coding assistants a clear, bounded brief before they edit a glyf project.

The goal is not to let an assistant invent a dashboard in isolation. The goal is to make it inspect dbt models, respect supported chart syntax, update dashboard YAML carefully, and run validation commands before handing changes back for review.

## Copy This Brief

```text
You are helping me add glyf dashboards to this dbt project.

Inspect dbt_project.yml, glyf.yml, models/, visualisations/, dashboards/, and target/manifest.json.
Use existing model names and dbt refs where possible.
Create or update .ggsql files only with supported glyf syntax.
Update dashboard YAML only when a chart should appear on a dashboard.
Run glyf doctor, validate, render, and dashboard after editing.
Summarize changed files, commands run, and anything that still needs human review.
```

## Project Instructions

```text
This project uses glyf to generate static dashboards from dbt models.

Chart files live in visualisations/.
Dashboard YAML lives in dashboards/.
The dbt manifest is target/manifest.json.
Use glyf doctor, validate, render, and dashboard to verify changes.
Do not change dbt models unless the user asks for model changes.
Prefer small, reviewable chart additions over broad dashboard rewrites.
```

Use the same text for Codex custom instructions, Claude project instructions, or any assistant that can read files and run shell commands.

## Task Template

```text
Task:
Add <chart description> to <dashboard name>.

Inputs:
- dbt model or source:
- metric definition:
- chart type:
- dashboard YAML:

Rules:
- Read glyf.yml and target/manifest.json first.
- Use supported .ggsql syntax only.
- Run glyf doctor and validate before finishing.
- Do not change dbt models unless required and explicitly requested.
```

## Validation commands

```bash
glyf doctor
glyf validate
glyf render
glyf dashboard
```

When running from outside the dbt project, include `--project-dir`:

```bash
glyf validate --project-dir path/to/dbt_project
```

## Review checklist

- The assistant used model names that exist in the dbt manifest.
- `.ggsql` directives match the supported syntax.
- Dashboard YAML references existing chart names.
- Generated artifacts are under `target/glyf/`.
- The assistant reported any unresolved refs, missing artifacts, or DuckDB execution errors.
