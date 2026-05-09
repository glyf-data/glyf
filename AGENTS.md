
### `AGENTS.md`

This guides coding agents.

```md
# Agent Instructions

## Principles

- Keep v1 simple.
- Prefer CLI-first implementation.
- Do not couple tightly to dbt internals.
- Use dbt artifacts such as `target/manifest.json`.
- Generate files into `target/ggsql/`.

## Python Environment

Package Manager

This project uses uv as the Python package manager and environment manager.

Use uv for:
- virtual environments
- dependency installation
- command execution
- dependency locking

Avoid:
- pipenv
- poetry
- conda

Preferred commands:

```bash
uv venv
uv sync
uv add typer rich pyyaml pydantic
uv add --dev pytest ruff
uv run pytest
uv run dbt-ggsql list
```

## Packaging Standards

Project should use:
- pyproject.toml
- uv.lock
- .python-version
- src/ layout

Expected structure:

```bash
    dbt-ggsql/
    ├── pyproject.toml
    ├── uv.lock
    ├── .python-version
    ├── README.md
    ├── SPEC.md
    ├── ARCHITECTURE.md
    ├── TASKS.md
    ├── DECISIONS.md
    │
    ├── src/
    │   └── dbt_ggsql/
    │       ├── __init__.py
    │       ├── cli.py
    │       ├── config.py
    │       ├── constants.py
    │       │
    │       ├── commands/
    │       │   ├── __init__.py
    │       │   ├── list_cmd.py
    │       │   ├── render_cmd.py
    │       │   └── dashboard_cmd.py
    │       │
    │       ├── manifest/
    │       │   ├── __init__.py
    │       │   ├── loader.py
    │       │   ├── parser.py
    │       │   └── resolver.py
    │       │
    │       ├── ggsql/
    │       │   ├── __init__.py
    │       │   ├── models.py
    │       │   ├── renderer.py
    │       │   └── serializer.py
    │       │
    │       ├── output/
    │       │   ├── __init__.py
    │       │   ├── writer.py
    │       │   └── paths.py
    │       │
    │       ├── dashboard/
    │       │   ├── __init__.py
    │       │   ├── generator.py
    │       │   └── templates/
    │       │       └── dashboard.html.j2
    │       │
    │       └── utils/
    │           ├── __init__.py
    │           ├── logging.py
    │           ├── files.py
    │           └── errors.py
    │
    ├── tests/
    │   ├── __init__.py
    │   ├── test_cli.py
    │   ├── test_manifest_loader.py
    │   ├── test_renderer.py
    │   ├── fixtures/
    │   │   ├── manifest.json
    │   │   └── sample_project/
    │   └── snapshots/
    │
    ├── examples/
    │   ├── minimal_dbt_project/
    │   │   ├── dbt_project.yml
    │   │   ├── models/
    │   │   │   └── example.sql
    │   │   └── target/
    │   │       └── manifest.json
    │   │
    │   ├── sample_outputs/
    │   │   ├── rendered.sql
    │   │   └── dashboard.html
    │   │
    │   └── cli_examples.md
    │
    ├── scripts/
    │   ├── dev.sh
    │   └── release.sh
    │
    ├── .gitignore
    ├── LICENSE
    └── AGENTS.md

```


## Coding rules

- Small modules.
- Typed Python.
- Clear error messages.
- Prefer standard library where possible.
- Keep dependencies minimal.
- Add tests for parser and manifest resolution.
- Avoid premature abstractions.
- Avoid building UI before CLI works.
- Keep functions composable and testable.
- Prefer explicit naming over clever abstractions.


## Architecture Guidelines
Initial Focus

Build the following pipeline first:

filesystem
- project discovery
- manifest loading
- ggsql parsing
- ref resolution
- artifact generation

Do NOT initially implement:

- frontend UI
- live dashboard server
- realtime rendering
- async orchestration
- browser-based editing

## First milestone

Implement:

```bash
dbt-ggsql list
dbt-ggsql validate
dbt-ggsql render
dbt-ggsql dashboard
```
Initial implementation may use placeholder artifacts instead of real rendered charts.

## dbt Integration

Use dbt-generated artifacts instead of reimplementing dbt internals.

Primary artifact:

- target/manifest.json

Support:
- ref()
- source() later
- basic node discovery

Do not depend on dbt runtime execution in v1.

## Testing Expectations

Add tests for:
- project discovery
- manifest loading
- ggsql parsing
- ref resolution
- dashboard config parsing

Use:
- uv run pytest

## Notes for AI Coding Agents

- Use uv commands in all examples.
- Do not use pip install.
- Keep architecture modular.
- Keep CLI outputs human-readable.
- Prefer deterministic behaviour.
- Keep implementation incremental.
- Prioritize correctness over features.