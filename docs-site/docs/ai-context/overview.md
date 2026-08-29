# AI Assistants

Coding assistants do well at drafting `.ggsql` charts and dashboard YAML for a
glyf project, because everything they need is in files — the dbt manifest,
`glyf.yml`, the chart and dashboard directories — and the CLI validates the
result.

## Brief

Paste this into the assistant's project instructions (Claude project
instructions, Codex custom instructions, or any tool that can read files and
run shell commands):

```text
This project uses glyf to generate static dashboards from dbt models.

Chart files live in visualisations/ (.ggsql: SQL followed by VISUALISE, DRAW,
LABEL, CONFIG, and INTERACT directives). Dashboard YAML lives in dashboards/.
The dbt manifest is target/manifest.json; glyf resolves ref() and source()
from it.

Before editing, read dbt_project.yml, glyf.yml, models/, visualisations/,
dashboards/, and target/manifest.json. Use existing model names and refs.
Create or update .ggsql files only with supported glyf syntax. Update
dashboard YAML only when a chart should appear on a dashboard. Do not change
dbt models unless asked.

After editing, run `glyf doctor` and `glyf build` (add --project-dir when
outside the dbt project). Report the files changed, the commands run, and
anything that still needs human review.
```

## Task template

```text
Add <chart description> to <dashboard name>.

- dbt model or source:
- metric definition:
- chart type:
- dashboard YAML:
```

## Good tasks for an assistant

- Draft a `.ggsql` file from a dbt model and add it to a dashboard.
- Run `glyf doctor` and explain unresolved refs, a missing manifest, or a
  DuckDB execution error.
- Add a GitHub Actions job that builds and uploads the dashboard site.

## Tasks that need a human

- Choosing which business metrics to show, and their definitions.
- Approving a dashboard layout for executives or customers.
- Deciding whether a dbt model should change.
- Publishing dashboards that contain customer or private business data.

## Review checklist

- Model names exist in the dbt manifest.
- `.ggsql` directives are in the [supported syntax](../guides/visualisation-syntax.md).
- Dashboard YAML references chart names that exist.
- Output landed under `target/glyf/`.
- `glyf doctor` and `glyf build` ran clean, and the assistant reported anything
  it could not resolve.

## llms.txt

The docs site publishes a compact index at `/llms.txt`. Point an assistant at
it when it needs the shortest list of the pages that matter.
