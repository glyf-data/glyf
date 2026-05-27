# CLI-First Tool Design Skill

## Purpose

Design an engineering tool to prove its core workflow through a command-line interface before adding richer interfaces.

## Inputs

- tool goal
- primary user tasks
- core data flow
- output artifacts
- constraints

## Outputs

- CLI-first implementation plan
- initial command surface
- execution boundaries
- staged interface roadmap
- explicit non-goals for v1

## Rules

- Prove the workflow in the CLI before building UI layers.
- Keep commands human-readable and predictable.
- Prefer deterministic output and explicit file locations.
- Avoid async, live, or interactive complexity until the batch workflow works.
- Keep modules small and composable.

## Example Workflow

1. Identify the smallest useful command set.
2. Define the input and output artifacts for each command.
3. Implement the core processing pipeline behind the CLI.
4. Add tests for the command and pipeline behavior.
5. Defer dashboards or interactive surfaces until the CLI is stable.

## Acceptance Criteria

The output is acceptable when it:

- defines a minimal useful CLI
- keeps the execution path understandable
- avoids premature UI or orchestration layers
- supports incremental extension later
