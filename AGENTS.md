# Agent Instructions

  ## Shared Capability Library

  Use the shared capability library mounted in this repository at `capabilities/agent-forge/`.

  Primary reference:
  - `capabilities/agent-forge/docs/capabilities_index.md`

  Use these topic files for this project:
  - `capabilities/agent-forge/skills/python/uv_project_setup.md`
  - `capabilities/agent-forge/skills/python/packaging_standards.md`
  - `capabilities/agent-forge/skills/architecture/cli_first_tool_design.md`
  - `capabilities/agent-forge/skills/architecture/artifact_driven_integration.md`
  - `capabilities/agent-forge/skills/testing/test_strategy.md`

  Apply the shared guidance from those files unless a project-specific rule below overrides it.

  ## Project Scope

  This project is a CLI-first Python tool that reads dbt-generated artifacts and produces ggsql outputs.

  Initial implementation priority:
  - project discovery
  - manifest loading
  - ggsql parsing
  - `ref()` resolution
  - artifact generation

  Do not initially implement:
  - frontend UI
  - live dashboard server
  - realtime rendering
  - async orchestration
  - browser-based editing

  ## Project Constraints

  - Keep v1 simple.
  - Keep implementation incremental.
  - Keep architecture modular.
  - Prioritize correctness over features.
  - Avoid premature abstractions.
  - Prefer deterministic behavior.
  - Keep CLI outputs human-readable.
  - Do not couple tightly to dbt internals.
  - Use dbt-generated artifacts instead of dbt runtime execution.
  - Primary artifact: `target/manifest.json`
  - Generate files into `target/ggsql/`
  - Support `ref()` first.
  - Defer `source()` support until later.
  - Parse only the artifact fields needed for the current feature set.
  - Use `uv` commands in all examples.
  - Do not use `pip install`.

  ## Python Environment

  Use `uv` for:
  - virtual environments
  - dependency installation
  - command execution
  - dependency locking

  Avoid:
  - `pipenv`
  - `poetry`
  - `conda`

  Preferred commands:
  - `uv venv`
  - `uv sync`
  - `uv add typer rich pyyaml pydantic`
  - `uv add --dev pytest ruff`
  - `uv run pytest`
  - `uv run dbt-charts list`

  ## Packaging Baseline

  Project should use:
  - `pyproject.toml`
  - `uv.lock`
  - `.python-version`
  - `src/` layout

  Target structure:

  ```text
  dbt-charts/
  ├── pyproject.toml
  ├── uv.lock
  ├── .python-version
  ├── README.md
  ├── SPEC.md
  ├── ARCHITECTURE.md
  ├── TASKS.md
  ├── DECISIONS.md
  ├── src/
  │   └── dbt_charts/
  │       ├── __init__.py
  │       ├── cli.py
  │       ├── config.py
  │       ├── constants.py
  │       ├── commands/
  │       │   ├── __init__.py
  │       │   ├── list_cmd.py
  │       │   ├── render_cmd.py
  │       │   └── dashboard_cmd.py
  │       ├── manifest/
  │       │   ├── __init__.py
  │       │   ├── loader.py
  │       │   ├── parser.py
  │       │   └── resolver.py
  │       ├── ggsql/
  │       │   ├── __init__.py
  │       │   ├── models.py
  │       │   ├── renderer.py
  │       │   └── serializer.py
  │       ├── output/
  │       │   ├── __init__.py
  │       │   ├── writer.py
  │       │   └── paths.py
  │       ├── dashboard/
  │       │   ├── __init__.py
  │       │   ├── generator.py
  │       │   └── templates/
  │       │       └── dashboard.html.j2
  │       └── utils/
  │           ├── __init__.py
  │           ├── logging.py
  │           ├── files.py
  │           └── errors.py
  ├── tests/
  │   ├── __init__.py
  │   ├── test_cli.py
  │   ├── test_manifest_loader.py
  │   ├── test_renderer.py
  │   ├── fixtures/
  │   │   ├── manifest.json
  │   │   └── sample_project/
  │   └── snapshots/
  ├── examples/
  │   ├── minimal_dbt_project/
  │   │   ├── dbt_project.yml
  │   │   ├── models/
  │   │   │   └── example.sql
  │   │   └── target/
  │   │       └── manifest.json
  │   ├── sample_outputs/
  │   │   ├── rendered.sql
  │   │   └── dashboard.html
  │   └── cli_examples.md
  ├── scripts/
  │   ├── dev.sh
  │   └── release.sh
  ├── .gitignore
  ├── LICENSE
  └── AGENTS.md

  ## Coding Rules

  - Small modules.
  - Typed Python.
  - Clear error messages.
  - Prefer standard library where possible.
  - Keep dependencies minimal.
  - Keep functions composable and testable.
  - Prefer explicit naming over clever abstractions.

  ## First Milestone

  Implement:

  - dbt-charts list
  - dbt-charts validate
  - dbt-charts render
  - dbt-charts dashboard

  Initial implementation may use placeholder artifacts instead of real rendered charts.

  ## Testing Expectations

  Add tests for:

  - project discovery
  - manifest loading
  - ggsql parsing
  - ref() resolution
  - dashboard config parsing

  Use:

  - uv run pytest