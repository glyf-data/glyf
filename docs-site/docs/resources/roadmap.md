# Roadmap

The current priority is to keep the core CLI deterministic and static-first.

## Current baseline

```bash
dbt build
dbt-charts render
dbt-charts dashboard
dbt-charts export
```

## Future themes

- Serve and watch workflows for local development.
- Richer dashboard layouts.
- Cloud publish helpers.
- Interactive chart support.
- dbt docs integration.
- Lineage-aware dashboards.
- Agent-assisted chart authoring.
- Migration guides for existing BI dashboards.

## Product direction

`dbt-charts` should stay useful as an open source package before becoming anything larger. The near-term documentation should therefore focus on install, first success, examples, command reference, and practical integration patterns.
