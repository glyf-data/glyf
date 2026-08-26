# Quickstart

*Glyf is pronounced like **"glyph"**. \
In typography, a glyph is the visible form of a symbol; in visualization, Glyf is the visible form of your data pipeline, turning modeled data into charts and dashboards that can be built, reviewed, and published like any other project artifact.*

Use this flow when you already have a dbt project and want to add glyf without hand-creating folders.

## Install

```bash
uv tool install glyf-core
glyf --version
```

The PyPI package is `glyf-core`; the command is `glyf`. See the
[installation guide](installation.md) for pipx/pip, upgrades, Windows, and
offline installs.

## Scaffold your dbt project

Run `init` from the root of your dbt project:

```bash
cd path/to/my_dbt_project
glyf init
```

The command prompts for:

- Starter chart name.
- Starter dashboard name.
- dbt model ref for the starter chart.
- Starter chart title.
- Starter chart type.

It creates the standard glyf files:

```text
my_dbt_project/
  glyf.yml
  visualisations/
    monthly_revenue.ggsql
  dashboards/
    executive.yml
```

If you want to rerun the scaffold and replace the starter chart/dashboard files, use:

```bash
glyf init --clean
```

`--clean` keeps an existing `glyf.yml` and replaces only the starter `.ggsql` and dashboard YAML files selected by the prompts.

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

`glyf` reads dbt artifacts. Run dbt before rendering charts so `target/manifest.json` exists and `ref()` or `source()` calls can be resolved.

```bash
dbt build
```

If you only need to regenerate metadata:

```bash
dbt compile
```

## Check and generate

Use `doctor` before the first build:

```bash
glyf doctor
glyf build
glyf serve
```

Open the generated static site:

```text
target/glyf/site/index.html
```

## Expected output

```text
target/glyf/
  compiled/
  charts/
  dashboards/
  site/
  index.html
```

The publish-ready dashboard site lives in:

```text
target/glyf/site/
```

## Try the included example

If you are working from the glyf repository, you can run the included demo project:

```bash
uv sync --all-groups
cd examples/simple_dbt
uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
uv run dbt run --profiles-dir .
uv run dbt compile --profiles-dir .
uv run glyf doctor
uv run glyf build
uv run glyf serve
```

Open:

```text
examples/simple_dbt/target/glyf/site/index.html
```

## Next steps

- Learn the [project structure](project-structure.md).
- Add glyf to an [existing dbt project](existing-dbt-project.md).
- Explore the [examples gallery](../examples/gallery.md).

For lower-level control during debugging or CI, use `glyf validate`, `glyf render`,
`glyf dashboard`, and `glyf export` separately.
