# glyf

`glyf` is an open-source visualisation build tool for data pipelines.

It lets analytics engineers define chart queries in `.ggsql`, connect them to analytical metadata, render the results into static chart artifacts, and publish dashboards without running a BI server. The first integration reads dbt artifacts and resolves dbt `ref()` and `source()` calls from `target/manifest.json`.

The chart syntax builds on the SQL-first visualisation model from [ggsql](https://ggsql.org), which brings Grammar of Graphics-style clauses such as `VISUALISE`, `DRAW`, `SCALE`, and `LABEL` into SQL workflows.

Use it when you want visualizations to live beside analytical code, move through code review, and produce static output for internal reporting, client delivery, or lightweight documentation.

## Who it is for

- Analytics engineers who want dashboards versioned with analytical projects.
- Developers who prefer code review, CI, and static publishing over a running BI service for lightweight reporting.
- Teams that want generated dashboard artifacts they can inspect, archive, and publish anywhere.

## What it is not

`glyf` is not a dbt adapter, hosted BI server, metrics store, or drag-and-drop dashboard editor. `glyf` is artifact-driven, not dbt-runtime-driven. The goal is a deterministic CLI workflow:

```bash
dbt build
glyf build
glyf serve
```

## Documentation map

- Start with [Quickstart](get-started/quickstart.md) to install the CLI, scaffold starter files, and generate your first dashboard.
- Browse [Examples gallery](examples/gallery.md) for project patterns.
- Keep [CLI reference](reference/cli.md) open when wiring scripts or CI.
