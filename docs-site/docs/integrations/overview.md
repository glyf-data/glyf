# Integrations

`glyf` produces files, so integrations should stay simple: run the CLI, collect the generated site, and publish the static output.

## Current integration paths

- GitHub Actions for repeatable dashboard builds.
- S3-compatible object storage for static dashboard publishing.
- GitHub Pages or any static host for published output.
- CI artifact uploads for review before publishing.
- Internal documentation portals or static servers for private team sharing.

## Planned integration areas

- dbt docs metadata links.
- Lineage-aware dashboard summaries from the manifest.
- Optional publish helpers for common static hosting targets.
- SQLMesh and other transformation-tool integrations.
- Alerting and collaboration hooks such as Slack or webhooks.
- Agent workflows that propose charts from dbt model metadata.

## Output contract

Integrations should treat this directory as the deployable artifact:

```text
target/glyf/site/
```

Use this archive when a platform expects a single file:

```text
target/glyf/glyf-site.zip
```
