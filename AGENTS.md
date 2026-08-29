# Agent Instructions

Guidance for AI coding assistants working in this repository. Human
contributors should read [CONTRIBUTING.md](./CONTRIBUTING.md); the design is
described in [ARCHITECTURE.md](./ARCHITECTURE.md).

## Project Shape

`glyf` is a CLI-first Python tool with a Rust core, built with maturin and
PyO3.

- `crates/glyf-core` owns ggsql parsing and validation, manifest extraction
  from `target/manifest.json`, and dbt `ref()` / `source()` resolution. It
  compiles to the extension module `glyf._core`.
- `src/glyf/ggsql/parser.py`, `src/glyf/manifest/loader.py`, and
  `src/glyf/manifest/resolver.py` are thin Python wrappers: they keep the
  Python-facing dataclasses, exceptions, and calling conventions and delegate
  the work to `glyf._core`.
- CLI commands, pipeline orchestration, SQL execution, chart rendering,
  dashboard generation, and file IO are Python.

## Where New Logic Goes

- Parsing, validation, manifest handling, and resolution: change
  `crates/glyf-core` first, expose it through `glyf._core`, then adapt the
  Python wrapper in the same change. Do not duplicate core logic in Python.
- CLI UX, dashboard templating, file generation, orchestration, and
  integration with Python visualisation libraries: Python.
- When a Rust return shape changes, update the Python adapter and tests for
  both layers in the same change.

## Constraints

- Use dbt artifacts, never dbt runtime execution; parse only the manifest
  fields the current feature needs.
- Generated files go under `target/glyf/`.
- Prefer deterministic behaviour and human-readable CLI output.
- Small modules, typed Python, clear error messages, minimal dependencies.
- Use `uv` for every Python command and example; never `pip install`,
  `pipenv`, `poetry`, or `conda`.

## Commands

```bash
uv sync --all-groups            # install
uv run maturin develop          # rebuild the Rust extension
uv run pytest                   # Python tests
cargo test -p glyf-core         # Rust tests
cargo fmt --all
make ci                         # the full local CI flow; `make` lists targets
uv run glyf doctor --project-dir examples/simple_dbt
uv run glyf build  --project-dir examples/simple_dbt
```

## Tests

Add or update tests for anything touching project discovery, manifest
loading, ggsql parsing and validation, `ref()` / `source()` resolution,
dashboard config parsing, or wrapper compatibility. A change that crosses the
Rust/Python boundary needs tests on both sides.

## Commits

Conventional Commits, checked in CI for every commit and the PR title — see
[CONTRIBUTING.md](./CONTRIBUTING.md#commit-messages).
