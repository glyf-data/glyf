# dbt-charts

`dbt-charts` is an experimental Python CLI for building static dashboards from dbt projects.

It discovers `.ggsql` visualisation files, resolves dbt `ref()` and `source()` calls from `target/manifest.json`, executes chart SQL with DuckDB, renders charts with Altair, and exports a publish-ready static site.

## Who it is for

- Analytics engineers who want dashboards versioned with dbt projects.
- Developers who prefer code review, CI, and static publishing over a running BI service for lightweight reporting.
- Teams that want generated dashboard artifacts they can inspect, archive, and publish anywhere.

## What it is not

`dbt-charts` is not a dbt adapter, hosted BI server, semantic layer, or drag-and-drop dashboard editor. The current goal is a deterministic CLI workflow:

```bash
dbt build
dbt-charts render
dbt-charts dashboard
dbt-charts export
```

## Documentation map

- Start with [Quickstart](get-started/quickstart.md) to generate the sample dashboard.
- Use [Existing dbt project](get-started/existing-dbt-project.md) when adding dbt-charts to your own repo.
- Browse [Examples gallery](examples/gallery.md) for project patterns.
- Keep [CLI reference](reference/cli.md) open when wiring scripts or CI.
- Read [Technical architecture](guides/technical-architecture.md) before contributing.

## Recommended maintenance model

The `docs-site` directory should be the source for the public docs website. The older root `docs/` Markdown files can remain as compatibility references during the transition, then either redirect to this site or be retired once the Docusaurus site is published.

This keeps the website maintainable because navigation, landing pages, examples, and references live in one Docusaurus project while the Python package and examples stay in their existing locations.
