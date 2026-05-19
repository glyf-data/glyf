# dbt-charts

`dbt-charts` adds a lightweight dashboard layer to dbt projects.

It lets analytics engineers define chart queries in `.ggsql`, resolve dbt `ref()` and `source()` calls from `target/manifest.json`, render the results into static chart artifacts, and publish dashboards without running a BI server.

The chart syntax builds on the SQL-first visualisation model from [ggsql](https://ggsql.org), which brings Grammar of Graphics-style clauses such as `VISUALISE`, `DRAW`, `SCALE`, and `LABEL` into SQL workflows.

Use it when you want dashboards to live beside dbt models, move through code review, and produce static output for internal reporting, client delivery, or lightweight documentation.

## Who it is for

- Analytics engineers who want dashboards versioned with dbt projects.
- Developers who prefer code review, CI, and static publishing over a running BI service for lightweight reporting.
- Teams that want generated dashboard artifacts they can inspect, archive, and publish anywhere.

## What it is not

`dbt-charts` is not a dbt adapter, hosted BI server, semantic layer, or drag-and-drop dashboard editor. The goal is a deterministic CLI workflow:

```bash
dbt build
dbt-charts render
dbt-charts dashboard
dbt-charts export
```

That workflow keeps data transformation in dbt, chart definitions in SQL-first files, and dashboard publishing in static artifacts.

## Documentation map

- Start with [Quickstart](get-started/quickstart.md) to generate the sample dashboard.
- Use [Existing dbt project](get-started/existing-dbt-project.md) when adding dbt-charts to your own repo.
- Browse [Examples gallery](examples/gallery.md) for project patterns.
- Keep [CLI reference](reference/cli.md) open when wiring scripts or CI.
- Read [Technical architecture](guides/technical-architecture.md) before contributing.
