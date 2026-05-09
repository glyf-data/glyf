
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

## Coding rules

- Small modules.
- Typed Python.
- Clear error messages.
- Add tests for parser and manifest resolution.
- Avoid building UI before CLI works.

## First milestone

Implement:

```bash
dbt-ggsql list
dbt-ggsql render
dbt-ggsql dashboard