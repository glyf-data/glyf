# Migrating from Looker

Use this page to decide which Looker dashboard ideas are good candidates for glyf.

`glyf` is not a Looker replacement. It is a static dashboard workflow for teams that want selected dashboard outputs to live closer to dbt models, code review, and CI.

## Good candidates

- Dashboards with stable metrics and predictable filters.
- Client-ready KPI pages that can be regenerated from dbt outputs.
- Internal reporting views that do not need live drill-down behavior.
- Charts where the business logic already belongs in dbt models.

## Migration workflow

1. Pick one Looker dashboard with a small number of stable charts.
2. Identify the dbt model, source, or SQL behind each chart.
3. Move metric definitions into dbt models when they are not already modeled.
4. Write one `.ggsql` file per chart.
5. Create a dashboard YAML file that lists the chart names.
6. Run `glyf validate`, `render`, and `dashboard`.
7. Compare the generated dashboard with the original Looker dashboard before expanding the migration.

## Questions to resolve before scaling

- Which source should drive the migration: dashboard screenshots, SQL, LookML metadata, or manual chart descriptions?
- Which filters should become static dashboard variants?
- Which chart types map cleanly to current glyf syntax?
- Which interactive Looker behaviors should stay in Looker instead of moving to static output?
