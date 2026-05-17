# Integrations

`dbt-charts` produces files, so integrations should stay simple: run the CLI, collect the generated site, and publish the static output.

## Current integration paths

- GitHub Actions for repeatable dashboard builds.
- GitHub Pages or any static host for published output.
- CI artifact uploads for internal review.

## Future integration ideas

- dbt docs metadata links.
- Lineage-aware dashboard summaries from the manifest.
- Optional publish helpers for common static hosting targets.
- Agent workflows that propose charts from dbt model metadata.

## Output contract

Integrations should treat this directory as the deployable artifact:

```text
target/ggsql/site/
```

Use this archive when a platform expects a single file:

```text
target/ggsql/dbt-charts-site.zip
```
