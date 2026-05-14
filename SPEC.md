# Product Specification

## Goal

Build a dbt-compatible tool/package that discovers ggsql visualisation files, resolves dbt refs, executes the SQL, renders chart outputs, and creates static dashboards.

## Non-goals

- Do not replace BI tools.
- Do not build a full drag-and-drop dashboard editor.
- Do not modify normal dbt model materialisation in v1.

## Core workflow

```bash
dbt build
dbt-charts render
dbt-charts dashboard