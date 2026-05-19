# Quickstart

Use this flow when you already have a dbt project and want to add dbt-charts without hand-creating folders.

## Install

Install the CLI with your Python package manager:

```bash
pip install dbt-charts
```

Or install it as an isolated `uv` tool:

```bash
uv tool install dbt-charts
```

## Scaffold your dbt project

Run `init` from the root of your dbt project:

```bash
cd path/to/my_dbt_project
dbt-charts init
```

The command prompts for:

- Starter chart name.
- Starter dashboard name.
- dbt model ref for the starter chart.
- Starter chart title.
- Starter chart type.

It creates the standard dbt-charts files:

```text
my_dbt_project/
  dbt_charts.yml
  visualisations/
    monthly_revenue.ggsql
  dashboards/
    executive.yml
```

If you want to rerun the scaffold and replace the starter chart/dashboard files, use:

```bash
dbt-charts init --clean
```

`--clean` keeps an existing `dbt_charts.yml` and replaces only the starter `.ggsql` and dashboard YAML files selected by the prompts.

## Edit the starter chart

Open the generated `.ggsql` file and point it at real columns from your dbt model:

```sql title="visualisations/monthly_revenue.ggsql"
SELECT
  date_day,
  metric_value
FROM {{ ref('fct_revenue') }}

VISUALISE date_day AS x, metric_value AS y
DRAW line
LABEL title => "Monthly Revenue"
LABEL x_title => "Date"
LABEL y_title => "Revenue"
CONFIG width => 900
CONFIG height => 500
```

The filename stem becomes the chart name used by dashboard YAML. For example, `visualisations/monthly_revenue.ggsql` is referenced as `monthly_revenue`.

## Build dbt first

`dbt-charts` reads dbt artifacts. Run dbt before rendering charts so `target/manifest.json` exists and `ref()` or `source()` calls can be resolved.

```bash
dbt build
```

If you only need to regenerate metadata:

```bash
dbt compile
```

## Check and generate

Use `doctor` and `validate` before rendering:

```bash
dbt-charts doctor
dbt-charts validate
dbt-charts render
dbt-charts dashboard
dbt-charts export --clean
```

Open the generated static site:

```text
target/ggsql/site/index.html
```

## Expected output

```text
target/ggsql/
  compiled/
  charts/
  dashboards/
  site/
  index.html
```

The publish-ready dashboard site lives in:

```text
target/ggsql/site/
```

## Try the included example

If you are working from the dbt-charts repository, you can run the included demo project:

```bash
uv sync --all-groups
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run dbt-charts doctor
uv run dbt-charts validate
uv run dbt-charts render
uv run dbt-charts dashboard
uv run dbt-charts export --clean
```

Open:

```text
examples/simple_dbt/target/ggsql/site/index.html
```

## Next steps

- Learn the [project structure](project-structure.md).
- Add dbt-charts to an [existing dbt project](existing-dbt-project.md).
- Explore the [examples gallery](../examples/gallery.md).
