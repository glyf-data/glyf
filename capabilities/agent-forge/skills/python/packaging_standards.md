# Python Packaging Standards Skill

## Purpose

Define a practical packaging baseline for a Python project so that implementation work starts from a consistent structure.

## Inputs

- project type
- CLI or library expectations
- dependency constraints
- testing needs
- release expectations

## Outputs

- recommended project structure
- required packaging files
- dependency management rules
- testing and linting entry points
- file layout guidance

## Rules

- Prefer `pyproject.toml` as the primary package configuration.
- Use `src/` layout for packaged code unless the project has a strong reason not to.
- Keep dependency management reproducible.
- Avoid tool sprawl in v1.
- Separate runtime and development dependencies clearly.

## Default Baseline

- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `src/`
- `tests/`
- `README.md`

## Acceptance Criteria

The output is acceptable when it:

- defines a small, coherent packaging baseline
- keeps the file layout understandable
- supports testing and command execution cleanly
- avoids premature structure beyond the project need
