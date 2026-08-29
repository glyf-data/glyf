# Integrations

`glyf` produces files, so integrations should stay simple: run the CLI, collect the generated site, and publish the static output.

## Current integration paths

- GitHub Actions for repeatable dashboard builds.
- S3-compatible object storage for static dashboard publishing.
- GitHub Pages or any static host for published output.
- CI artifact uploads for review before publishing.
- Internal documentation portals or static servers for private team sharing.

Planned integrations are listed on the [roadmap](../resources/roadmap.md).

## Output contract

Treat this directory as the deployable artifact:

```text
target/glyf/site/
```

Use this archive, produced by `glyf build --zip` or `glyf export --zip`, when a platform expects a single file:

```text
target/glyf/glyf-site.zip
```
