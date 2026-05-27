# Capabilities Index

`agent-forge` is organized as a reusable capability library. This index groups the shared assets by topic so downstream projects can reference only what they need.

## Planning

- `skills/github/backlog_creation.md`
- `skills/github/project_milestone.md`
- `skills/github/issue_breakdown.md`
- `workflows/backlog_creation_workflow.md`
- `workflows/milestone_execution.md`

## Quality

- `skills/github/code_review.md`
- `skills/testing/test_strategy.md`
- `workflows/code_review_workflow.md`

## Delivery

- `skills/release/release_management.md`
- `workflows/release_workflow.md`

## Operations

- `skills/incident/incident_response.md`
- `workflows/incident_response_workflow.md`

## Architecture

- `skills/architecture/service_design.md`
- `skills/architecture/cli_first_tool_design.md`
- `skills/architecture/artifact_driven_integration.md`
- `templates/architecture_template.md`

## Python

- `skills/python/uv_project_setup.md`
- `skills/python/packaging_standards.md`

## GitHub Tooling

- `tools/github/backlog_to_project.sh`

## How To Use

Downstream repos should reference only the relevant topic entries for the task at hand.

Example:

```md
For lightweight planning, use `skills/github/backlog_creation.md` and `workflows/backlog_creation_workflow.md`.
For release tasks, use `skills/release/release_management.md` and `workflows/release_workflow.md`.
```
