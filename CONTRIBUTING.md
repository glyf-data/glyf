# Contributing

Thanks for considering a contribution. `dbt-ggsql` is experimental, so small,
focused changes are easiest to review.

## Development Setup

```bash
uv sync
uv run pytest
```

## Useful Commands

```bash
uv run dbt-ggsql --help
uv run pytest
uv build
```

## Guidelines

- Keep the CLI-first workflow simple.
- Prefer small modules and typed Python.
- Do not add dbt runtime coupling beyond artifacts unless discussed first.
- Add tests for parser, resolver, renderer, dashboard, and CLI behavior changes.
- Keep generated `target/` outputs out of version control.

## Pull Requests

Please include:

- a concise description of the change
- tests or a note explaining why tests were not added
- any documentation updates needed for users
