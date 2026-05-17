# Technical Architecture

`dbt-charts` keeps the core workflow small and artifact-driven.

```text
dbt project
  -> dbt manifest.json
  -> ggsql file parser
  -> ref/source resolver
  -> query executor
  -> chart renderer
  -> artifact store
  -> dashboard generator
  -> static export
```

## Components

| Component | Responsibility |
| --- | --- |
| Project scanner | Finds `.ggsql`, dashboard YAML, config, and dbt artifacts. |
| Manifest resolver | Resolves supported `ref()` and `source()` calls from `target/manifest.json`. |
| ggsql parser | Splits SQL from visualisation directives and validates chart metadata. |
| Query executor | Executes compiled SQL against DuckDB for the current project. |
| Renderer | Converts query results into Altair chart specs and chart artifacts. |
| Dashboard generator | Builds static dashboard HTML from chart artifacts and dashboard YAML. |
| Exporter | Copies generated output into a publish-ready static site folder. |

## Design principles

- Keep dbt execution separate from dashboard rendering.
- Use dbt artifacts instead of importing dbt internals.
- Generate inspectable files under `target/ggsql`.
- Prefer deterministic static output over a long-running service.
- Keep the chart syntax small enough to review in code.

## Extension points

Future work can add richer layouts, dbt docs metadata, lineage-aware dashboards, cloud publish helpers, and agent-assisted chart creation without changing the basic artifact pipeline.
