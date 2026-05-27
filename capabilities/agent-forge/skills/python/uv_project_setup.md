# uv Project Setup Skill

## Purpose

Set up a Python project with `uv` in a consistent, modern, and reproducible way.

## Inputs

- project name
- Python version
- package layout preference
- dependency requirements
- testing needs

## Outputs

- project initialization steps
- dependency management approach
- basic project layout
- recommended developer commands
- notes for future automation

## Rules

- Prefer reproducible dependency management.
- Keep setup minimal and explicit.
- Align the structure with the project's actual needs.
- Avoid adding tools that do not solve a current problem.

## Recommended Standards

- Use `pyproject.toml` as the package configuration entry point.
- Commit `uv.lock` for deterministic environments when the project is application-oriented.
- Use a `src/` layout for import isolation in packaged Python projects.
- Keep runtime and development dependencies explicit.
- Run commands through `uv run`.

## Preferred Commands

- `uv venv`
- `uv sync`
- `uv add <package>`
- `uv add --dev <package>`
- `uv run pytest`

## Acceptance Criteria

The setup is acceptable when it:

- uses `uv` for environment and dependency management
- has a clear package layout
- documents the main developer commands
- avoids unnecessary tooling complexity
