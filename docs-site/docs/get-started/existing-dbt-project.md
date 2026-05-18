# Existing dbt Project

Use this path when you already have a dbt project with models and a working profile.

## Add chart files

Create a `visualisations/` directory in your dbt project and add `.ggsql` files:

```text
my_dbt_project/
  dbt_project.yml
  models/
  visualisations/
    monthly_revenue.ggsql
  dashboards/
    executive.yml
```

## Build dbt artifacts

`dbt-charts` does not run dbt for you. Build or compile first so `target/manifest.json` exists.

```bash
dbt build
```

If you only need to regenerate the manifest:

```bash
dbt compile
```

## Check project health

```bash
dbt-charts doctor
```

Use `--project-dir` when running from outside the dbt project:

```bash
dbt-charts doctor --project-dir path/to/my_dbt_project
```

## Generate dashboards

```bash
dbt-charts render
dbt-charts dashboard
dbt-charts export --clean
```

Preview locally:

```bash
dbt-charts serve
```

## Minimum chart

```sql
SELECT month, revenue
FROM {{ ref('fct_revenue') }}

VISUALISE month AS x, revenue AS y
DRAW line
LABEL title => 'Monthly Revenue'
```

## Minimum dashboard

```yaml
name: executive
title: Executive Dashboard
description: Core metrics generated from dbt models.

charts:
  - monthly_revenue
```
