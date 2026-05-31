# Agent Instructions

## Shared Capability Library

Use the vendored capability library committed directly in this repository at `capabilities/agent-forge/`.

These files are local project files now, not an external submodule or mounted dependency.

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

This project is a CLI-first Python tool with a Rust-first core engine.

Architecture preference:
- Prefer Rust for core engine logic.
- Use Python as the wrapper and orchestration layer.
- Preserve the public Python API even when logic moves into Rust.

Current core boundary:
- `crates/glyf-core` owns ggsql validation.
- `crates/glyf-core` owns manifest extraction from `target/manifest.json`.
- `crates/glyf-core` owns dbt `ref()` and `source()` resolution.
- `crates/glyf-core` compiles into the Python extension module `glyf._core` through PyO3 and maturin.

Current Python wrapper boundary:
- `src/glyf/ggsql/parser.py` keeps Python-facing parsing helpers, dataclasses, and errors, but delegates parsing to `glyf._core`.
- `src/glyf/manifest/loader.py` keeps Python-facing manifest dataclasses and errors, but delegates manifest loading to `glyf._core`.
- `src/glyf/manifest/resolver.py` keeps Python-facing resolution types, but delegates core resolution to `glyf._core`.
- CLI commands, pipeline orchestration, dashboard generation, rendering, and file IO remain in Python unless there is a clear reason to move them.

Implementation priority:
- project discovery
- manifest loading
- ggsql parsing and validation
- `ref()` resolution
- artifact generation

Do not initially implement:
- frontend UI
- live dashboard server features beyond current scope
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
- Generate files into `target/glyf/`
- Support `ref()` first.
- Preserve `source()` support where it already exists.
- Parse only the artifact fields needed for the current feature set.
- Keep Python wrappers thin and stable.
- Move validation and heavy parsing into Rust before adding new Python-only core logic.
- Keep Rust/Python data contracts explicit and tested.
- Use `uv` commands in all Python examples.
- Do not use `pip install`.

## Environment

Use `uv` for:
- virtual environments
- Python dependency installation
- Python command execution
- dependency locking

Use Rust tooling for the core crate:
- `cargo fmt`
- `cargo test`
- `uv run maturin develop`

Avoid:
- `pipenv`
- `poetry`
- `conda`

Preferred commands:
- `uv sync`
- `uv run maturin develop`
- `uv run pytest`
- `cargo test -p glyf-core`
- `cargo fmt --all`
- `uv run glyf validate`
- `uv run glyf render`

## Packaging Baseline

Project packaging should reflect the mixed Rust/Python layout:
- `pyproject.toml` uses `maturin` as the build backend.
- `Cargo.toml` defines the Rust workspace.
- `crates/glyf-core/Cargo.toml` defines the PyO3 extension crate.
- `src/glyf/_core` is produced by the Rust extension build.
- `src/` remains the Python source root.

Representative structure:

```text
glyf/
├── pyproject.toml
├── Cargo.toml
├── Cargo.lock
├── src/
│   └── glyf/
│       ├── cli.py
│       ├── pipeline.py
│       ├── commands/
│       ├── dashboard/
│       ├── execution/
│       ├── ggsql/
│       │   ├── models.py
│       │   └── parser.py
│       ├── manifest/
│       │   ├── loader.py
│       │   └── resolver.py
│       ├── output/
│       └── project/
├── crates/
│   └── glyf-core/
│       ├── Cargo.toml
│       └── src/lib.rs
├── tests/
├── examples/
└── AGENTS.md
```

## Coding Rules

- Small modules.
- Typed Python.
- Clear error messages.
- Prefer standard library where possible.
- Keep dependencies minimal.
- Keep functions composable and testable.
- Prefer explicit naming over clever abstractions.
- In Rust, prefer small pure helpers around parsing and conversion logic.
- In Python, keep wrapper code focused on API compatibility, file IO, and orchestration.
- When changing Rust return shapes, update Python adapters in the same change.
- Do not duplicate core parsing or manifest logic in Python if Rust already owns it.

## First Preference For New Work

When implementing or refactoring core behavior:
- add or change logic in `crates/glyf-core` first
- expose the behavior through `glyf._core`
- adapt Python wrapper modules to preserve existing dataclasses, exceptions, and calling conventions

Use Python-first changes only when the work is clearly outside the core boundary, such as:
- CLI UX
- dashboard templating
- file generation
- process orchestration
- integration with Python visualization libraries

## Testing Expectations

Add or update tests for:
- project discovery
- manifest loading
- ggsql parsing and validation
- `ref()` resolution
- `source()` resolution when touched
- Python wrapper compatibility
- dashboard config parsing

Use:
- `uv run pytest`
- `cargo test -p glyf-core`

If a change crosses the Rust/Python boundary, test both layers.
