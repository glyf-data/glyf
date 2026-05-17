# Migrating from Looker

This page is a placeholder for a future migration guide.

The likely workflow will help teams move selected Looker dashboard ideas into dbt-charts when the desired output is a version-controlled static dashboard.

## Future use cases

- Recreate a small Looker dashboard as `.ggsql` visualisations and dashboard YAML.
- Map LookML explores or SQL runner queries to dbt models.
- Identify metrics that should move into dbt models before chart generation.
- Preserve dashboard review workflows in pull requests.

## Migration questions to answer later

- Which Looker objects should be supported first: dashboards, tiles, explores, or Looks?
- Should migration start from exported dashboard metadata, screenshots, SQL, or manual descriptions?
- How should filters and parameters map to static dashboards?
- Which chart types can map cleanly to current dbt-charts syntax?

## Current recommendation

For now, manually recreate a small dashboard:

1. Identify the dbt model or source behind each chart.
2. Write one `.ggsql` file per chart.
3. Create a dashboard YAML file that lists the chart names.
4. Run `dbt-charts validate`, `render`, and `dashboard`.
