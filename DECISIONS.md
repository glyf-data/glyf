# Architecture Decisions

## ADR 001: Use separate visualisation files

Decision: Keep `.ggsql` files separate from dbt model SQL.

Reason: dbt models should remain focused on transformations. Visualisations are a presentation layer.

## ADR 002: Use dbt manifest.json

Decision: Resolve refs using dbt-generated artifacts.

Reason: Avoid reimplementing dbt compilation logic.