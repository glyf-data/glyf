# Product Specification

## Goal

Build an Open Source Visualization build tool to data pipeline. The tool discovers ggsql visualisation files, connects them to analytical metadata, executes SQL, renders chart outputs, and creates static dashboards. The first integration supports dbt artifacts and dbt `ref()` / `source()` resolution.

## Non-goals

- Do not replace BI tools.
- Do not build a full drag-and-drop dashboard editor.
- Do not modify normal dbt model materialisation in v1.

## Core workflow

```bash
dbt build
glyf render
glyf dashboard
