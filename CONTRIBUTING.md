# Contributing to dbt-charts

Thanks for considering a contribution to `dbt-charts`.

`dbt-charts` is an early-stage project for SQL-first, chart-as-code dashboards
that live beside dbt projects. Contributions are welcome, especially when they
make the CLI more reliable, the documentation clearer, or the example projects
easier to learn from.

This guide explains how to prepare a contribution, set up a local development
environment, and describe your work when opening a pull request.

## Before You Start

Small, focused contributions are easiest to review and merge. Good first
contributions include:

- documentation fixes and examples
- small bug fixes with tests
- improvements to error messages and validation
- focused parser, resolver, renderer, dashboard, or CLI changes

For larger changes, please open an issue before writing code. This is especially
important for new chart syntax, dashboard behavior, dbt integration changes,
public APIs, packaging changes, or licensing and governance topics.

## Governance and Conduct

This project is maintained by a single owner. See [GOVERNANCE.md](./GOVERNANCE.md)
for how decisions are made.

All participation in this project is covered by the
[Code of Conduct](./CODE_OF_CONDUCT.md). Be direct, respectful, and focused on
the work.

## Contributor License Agreement (CLA)

Before substantive contributions are merged, contributors must accept the
[Contributor License Agreement](./CLA.md). This applies to code, tests,
documentation, examples, configuration, and other material intended to become
part of the project.

The CLA is a license grant to the project owner, Kannan Kalidasan. It does not
transfer copyright ownership. Contributors keep copyright and authorship in their
work, while granting the project owner the rights needed to maintain,
distribute, sublicense, relicense, and commercialize the project over time.

You do not need to sign the CLA before opening issues, asking questions,
commenting on discussions, or reporting bugs.

### How to Sign

Until an automated CLA workflow is configured, CLA signing is handled with a
pull request comment.

1. Open your pull request.
2. Read [CLA.md](./CLA.md).
3. Post this statement as a pull request comment from the GitHub account used to
   submit the contribution:

```text
I have read and agree to the dbt-charts Contributor License Agreement in CLA.md.

GitHub username: @your-username
Pull request: #123
Date: YYYY-MM-DD
```

4. The maintainer records the CLA acceptance before merge.

Do not paste private legal names, signatures, addresses, or other personal
details into public GitHub comments. If your employer or another organisation
may own rights in your contribution, confirm that you have permission before
signing.

## Development Setup

You will need:

- Python 3.11 or later
- [`uv`](https://docs.astral.sh/uv/)
- [`go-task`](https://taskfile.dev/) if you want to run the same command groups
  used by CI

Clone the repository, then install the project and development dependencies:

```bash
uv sync --all-groups
```

You can also use the project task:

```bash
task install
```

To install a specific Python version through `uv` and use it for the project:

```bash
task install PYTHON_VERSION=3.12
```

## Useful Commands

Run the test suite:

```bash
task test
```

Build the package:

```bash
task build
```

Run the example dashboard workflow used by GitHub Actions:

```bash
task dashboard-ci
```

Run the full local CI flow:

```bash
task ci
```

Run the CLI directly during development:

```bash
uv run dbt-charts --help
uv run dbt-charts doctor --project-dir examples/simple_dbt
uv run dbt-charts render --project-dir examples/simple_dbt
```

## Testing Expectations

Please add or update tests when a change affects behavior. In particular, add
coverage for changes to:

- `.ggsql` parsing
- dbt manifest resolution
- chart rendering
- dashboard generation
- export behavior
- CLI commands and validation

Documentation-only changes do not need tests. For small changes where tests are
not practical, explain that in the pull request.

Keep generated dbt `target/` outputs and exported dashboard artifacts out of
version control unless a fixture is intentionally part of a test.

## Pull Request Guidelines

Before opening a pull request:

1. Keep the change focused on one problem.
2. Rebase or update your branch from `main`.
3. Run the relevant checks, preferably `task ci` for behavior changes.
4. Update documentation or examples if user-facing behavior changed.
5. Make sure generated files, caches, and local database files are not included.

In the pull request description, include:

- what changed
- why the change is needed
- how you tested it
- any follow-up work or known limitations

The maintainer may ask for changes, decline a PR, or suggest opening a separate
issue for a larger design discussion. That keeps review clear while the project
is still early.

## Reporting Bugs

When opening a bug report, please include:

- the `dbt-charts` version or commit
- your Python version
- the dbt adapter and dbt version, if relevant
- the command you ran
- the error output or unexpected result
- a minimal example project or `.ggsql` file when possible

The best bug reports are reproducible with a small example.

## Proposing Features

Feature requests are welcome, but they should explain the workflow they support.
Please include:

- the problem you are trying to solve
- why existing behavior is not enough
- a small example of the desired user experience
- whether the feature belongs in the CLI, chart syntax, dashboard config, docs,
  or examples

For syntax changes, examples are more useful than abstract descriptions. Show
what the `.ggsql` or YAML should look like and what output you expect.

## Documentation Contributions

Documentation is part of the product. Clear examples, troubleshooting notes, and
small corrections are valuable contributions.

When changing docs, prefer practical examples over broad promises. `dbt-charts`
is still alpha-stage, so documentation should be honest about what works today
and what is still evolving.
