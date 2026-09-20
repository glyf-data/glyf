# Contributing to glyf

Thanks for considering a contribution. `glyf` is an early-stage, open source
build tool for charts and dashboards that live beside dbt projects, and it gets
better fastest through small, concrete changes: a bug fixed with a test, an
error message that says what to do, an example that teaches something.

This guide takes you from "I found something" to a merged pull request.

## Where to get help

Stuck on setup, not sure whether an idea fits, or want a second opinion before
you write code? Ask. Nobody expects you to work it out alone.

| | |
| --- | --- |
| **[Slack](https://glyfdata.com/slack)** | The quickest answer. Ask in the help channel; say what you ran and what happened. |
| **[Discussions](https://github.com/glyf-data/glyf/discussions)** | Questions and ideas that others will want to find later. |
| **[Issues](https://github.com/glyf-data/glyf/issues)** | Bugs and concrete feature requests. |

## Your first contribution, in five steps

1. **Pick something small.** A docs fix, a clearer error message, a bug with a
   test. For anything larger, [open an issue first](#what-to-work-on) so you do
   not build something that cannot be merged.
2. **Set up**: fork, clone, then `uv sync --all-groups`. You need Python, `uv`
   and a Rust toolchain; [details below](#set-up).
3. **Make the change, with a test.** Run `make ci` before you push.
4. **Open a pull request** with a [Conventional Commits](#commit-messages)
   title. Say what changed, why, and how you tested it.
5. **Sign the CLA with one comment.** A bot asks on your first pull request;
   you reply with one sentence, once, and never again.
   [What it means](#sign-the-cla).

## What to work on

Good first contributions:

- documentation fixes and examples
- small bug fixes with tests
- clearer error messages and validation
- focused changes to the parser, resolver, renderer, dashboards or CLI

Most likely to be merged: small bug fixes, reliability and performance work
with a measurement, documentation with concrete examples, and tightly scoped
maintenance.

**Open an issue before writing code** for new chart syntax, dashboard
behaviour, dbt integration changes, public APIs, packaging, or anything about
licensing and governance. An issue does not guarantee a merge, but it is how
you find out early whether the idea fits.

Least likely to be merged: large pull requests that mix unrelated changes,
features nobody discussed, rewrites of working subsystems, and syntax or API
changes without a workflow that motivates them. These are usually closed and
redirected into an issue, which is no judgement on the work. `glyf` has one
maintainer and its shape is still settling, so it stays coherent by staying
small.

## Set up

You need:

- **Python 3.11** or later
- **[`uv`](https://docs.astral.sh/uv/)**, which manages the environment and
  every Python command here. Do not use `pip`, `poetry` or `conda`.
- **A Rust toolchain, 1.83 or later**, from [rustup](https://rustup.rs). The
  parser and resolver are a Rust crate compiled into the Python package, so
  installing the project compiles it. CI uses 1.98.0.
- `make`, to run the same command groups CI runs. `make` with no arguments
  lists them.

```bash
git clone https://github.com/<you>/glyf.git
cd glyf
uv sync --all-groups      # installs dependencies and compiles the Rust core
uv run glyf --help
```

Check the whole thing works by building an example:

```bash
make example-build        # dbt seed, dbt build, glyf doctor, glyf build
```

### After you change Rust

Python does not see a Rust change until the extension is rebuilt:

```bash
uv sync --all-groups --reinstall-package glyf-core
```

The same applies after switching branches. If a test fails with an error that
belongs to a different branch, the compiled extension is stale; rebuild it.

### Where things live

| Path | What |
| --- | --- |
| `crates/glyf-core/` | Rust: `.ggsql` parsing and validation, dbt manifest loading, `ref()`/`source()` resolution, image comparison. Compiles to `glyf._core`. |
| `src/glyf/` | Python: the CLI, the render pipeline, SQL execution, charts, dashboards, export. |
| `src/glyf/ggsql/`, `src/glyf/manifest/` | Thin Python wrappers over the Rust core. |
| `tests/` | The Python test suite. Rust tests sit beside the code they test. |
| `examples/` | Small dbt projects that double as fixtures and as the demo dashboards. |
| `docs-site/` | The documentation site. |

[ARCHITECTURE.md](./ARCHITECTURE.md) explains the design. The short rule:
parsing, validation and resolution go in Rust first and are exposed through
`glyf._core`; CLI, rendering, dashboards and file IO are Python. Do not
duplicate core logic in Python.

## Make the change

```bash
make test        # the Python suite
make rust        # Rust formatting, clippy and unit tests
make ci          # everything CI runs, in one command
```

Run the CLI against an example while you work:

```bash
uv run glyf doctor --project-dir examples/simple_dbt
uv run glyf build  --project-dir examples/simple_dbt
uv run glyf serve  --project-dir examples/simple_dbt
```

`make bench` measures render cost against mark count. It is slow and never
part of CI.

### Tests

Add or update tests when behaviour changes, in particular for `.ggsql`
parsing, manifest resolution, chart rendering, dashboard generation, export,
and CLI commands. **A change that crosses the Rust/Python boundary needs tests
on both sides.** Documentation-only changes need none. Where a test is not
practical, say why in the pull request.

Keep dbt `target/` output and exported dashboards out of version control unless
a fixture is deliberately part of a test.

### Verifying against a real warehouse

CI runs DuckDB and, in a service container, Trino. Snowflake and BigQuery have
no free container to run against, so their executors are tested against fakes:
that covers the SQL and the result mapping, but not credentials, network routes
or a driver's real auth flow.

`tests/test_warehouse_manual.py` is the by-hand half. Point it at a real dbt
profile and it runs the same execution chain a build uses — a `select 1` and
the `limit 0` probe that validate mode sends:

```bash
export GLYF_WAREHOUSE_PROFILES_DIR=~/.dbt   # directory holding profiles.yml
export GLYF_WAREHOUSE_PROFILE=my_profile    # a profile name inside it
export GLYF_WAREHOUSE_TARGET=prod           # optional; defaults to the profile's target
uv run pytest tests/test_warehouse_manual.py -v
```

Without the first two variables the file skips, so it stays out of the way of a
normal `make test`. It works for any type the dbt backend dispatches, Trino
included. Please say in the pull request which warehouse you ran it against
when a change touches execution.

Users have the same check without the test suite: `glyf doctor` resolves the
profile and target and runs its own `select 1`.

## Commit Messages

Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>)!: <subject>
```

Allowed types are `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`build`, `ci`, `chore`, and `revert`. The scope is optional and lowercase, `!`
before the colon marks a breaking change, and the subject line stays within 72
characters.

```
feat(execution): add an ADBC-backed DuckDB executor
fix: exit non-zero when a model is missing
docs(readme): add quick start
chore!: drop support for schema version 0
```

CI checks every commit in a pull request and the pull request title, because the
title becomes the subject of the squash-merge commit. Install the local hook to
catch problems before you push:

```bash
scripts/install-git-hooks.sh
```

To check a range by hand:

```bash
scripts/check-commit-message.sh --range origin/main..HEAD
```

## Open the pull request

Keep it to one problem. In the description, say:

- what changed
- why it is needed
- how you tested it
- any follow-up or known limitation

If the change is visual, on the docs site or in a rendered chart, include
before and after screenshots. If it depends on motion or interaction, a short
recording.

These checks run on every pull request:

| Check | What it needs |
| --- | --- |
| `test` on Python 3.11, 3.12, 3.13 | `make test` passes |
| `rust core` | `make rust` passes |
| `conventional-commits` | every commit and the title follow the format |
| `visual diff` | nothing; it reports what your change does to the example dashboards, as pictures |
| `cla` | you have signed; see below |

## Sign the CLA

`glyf` asks contributors to accept a
[Contributor License Agreement](./CLA.md) before a contribution is merged. In
plain terms:

- **You keep the copyright** in your work, and your authorship.
- You confirm the work is yours to contribute.
- You grant the project owner the rights needed to keep distributing the
  project, including relicensing it.

It is a licence grant, not a transfer of ownership. [CLA.md](./CLA.md) has a
plain-language summary at the top and the agreement below it.

**Signing takes one comment.** On your first pull request a bot posts a
comment. Reply on the pull request with exactly this sentence:

```text
I have read the CLA Document and I hereby sign the CLA
```

The `cla` check turns green and your GitHub username is recorded. **You sign
once.** Every later pull request from the same account passes without asking.

- You do not need to sign to open issues, comment, ask questions or report
  bugs.
- If the check does not update, comment `recheck`.
- Do not put a legal name, a signature or an address in the comment. The
  sentence and your GitHub account are the whole record.
- If your employer may own rights in what you write, confirm you have
  permission before signing.

## What review looks like

`glyf` has one maintainer, so review takes the time it takes; small and
well-described pull requests go first. You may be asked to narrow the scope, to
split the change, or to move a design question into an issue, and sometimes a
pull request is declined. Opening one does not oblige the maintainer to merge
it or to keep that implementation direction. If yours has gone quiet for a
week, a nudge in Slack is welcome.

## Reporting bugs

A security problem is not a bug report: report it privately, as
[SECURITY.md](./SECURITY.md) describes.


Include:

- the `glyf` version (`glyf --version`) or commit
- your Python version
- the dbt adapter and version, if relevant
- the command you ran
- the error output or the unexpected result
- the output of `glyf doctor`
- a minimal project or `.ggsql` file when you can

The best bug reports reproduce with a small example.

## Proposing features

Explain the workflow the feature supports:

- the problem you are trying to solve
- why existing behaviour is not enough
- a small example of what you would want to type and what you would expect back
- whether it belongs in the CLI, the chart syntax, dashboard config, docs or
  examples

For syntax, an example beats a description: show the `.ggsql` or YAML and the
output you expect. If the idea is still broad, start in Discussions or Slack.

## Documentation

Documentation is part of the product, and small corrections are real
contributions. Prefer a working example to a promise, and describe what works
today. The docs test suite parses every chart and loads every dashboard the
pages show, so an example that does not run fails CI.

## Governance and conduct

[GOVERNANCE.md](./GOVERNANCE.md) explains how decisions are made. All
participation is covered by the [Code of Conduct](./CODE_OF_CONDUCT.md): be
direct, be respectful, and keep it about the work.
