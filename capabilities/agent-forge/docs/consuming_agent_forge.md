# Consuming Agent Forge

This document explains how downstream repositories should use `agent-forge` as a shared capability library.

## Consumption Models

There are four practical ways to consume `agent-forge`:

1. sibling repository
2. git submodule
3. git subtree
4. vendored copy

The recommended default is `git submodule` or `git subtree`, because both make the shared files visible inside the consuming repository.

## Recommended Layout

Use an in-repo path such as:

```text
consuming-repo/
  vendor/
    agent-forge/
```

This makes relative references stable for humans, agents, CI, and local tooling.

## Option 1: Sibling Repository

Example layout:

```text
workspace/
  agent-forge/
  consuming-repo/
```

Reference `agent-forge` from the consuming repo with paths like:

```md
- `../agent-forge/docs/capabilities_index.md`
- `../agent-forge/skills/python/uv_project_setup.md`
```

Use this only when your agent runtime can read sibling directories. It is simple, but less reliable than mounting inside the repo.

## Option 2: Git Submodule

This is the cleanest option when you want:

- a stable in-repo path
- independent version pinning
- explicit updates

Add it to the consuming repo:

```bash
git submodule add <agent-forge-repo-url> vendor/agent-forge
git commit -m "Add agent-forge submodule"
```

Clone with submodules:

```bash
git clone --recurse-submodules <consuming-repo-url>
```

Update the mounted version later:

```bash
git submodule update --remote vendor/agent-forge
git add vendor/agent-forge
git commit -m "Update agent-forge"
```

Use this when you want downstream repos to pin a specific `agent-forge` revision and upgrade deliberately.

## Option 3: Git Subtree

This is a good option when you want:

- the files committed directly into the consuming repo
- no submodule workflow
- simpler cloning for other contributors

Initial add:

```bash
git remote add agent-forge <agent-forge-repo-url>
git subtree add --prefix=vendor/agent-forge agent-forge main --squash
```

Pull updates later:

```bash
git subtree pull --prefix=vendor/agent-forge agent-forge main --squash
```

Use this when you want the mounted content to behave like normal repo files.

## Option 4: Vendored Copy

You can copy selected files or directories into the consuming repo manually.

Use this only when:

- the consuming repo needs a frozen local snapshot
- the team does not want git submodule or subtree workflows

This is the least maintainable option because updates are manual.

## Recommended AGENTS.md Pattern

Keep the consuming repo `AGENTS.md` short. Point to `agent-forge`, then list only the relevant topic files.

Example when mounted in `vendor/agent-forge/`:

```md
# Agent Instructions

## Shared Capability Library

Primary reference:
- `vendor/agent-forge/docs/capabilities_index.md`

Use these topic files for this project:
- `vendor/agent-forge/skills/python/uv_project_setup.md`
- `vendor/agent-forge/skills/python/packaging_standards.md`
- `vendor/agent-forge/skills/architecture/cli_first_tool_design.md`
- `vendor/agent-forge/skills/architecture/artifact_driven_integration.md`
- `vendor/agent-forge/skills/testing/test_strategy.md`

## Project Constraints

- keep v1 simple
- use `target/manifest.json`
- generate outputs into `target/ggsql/`
```

## What Stays Local

Keep these in the consuming repo:

- project-specific paths
- domain-specific constraints
- exact command names
- current milestone scope
- local architecture decisions

Keep these in `agent-forge`:

- reusable engineering policy
- packaging standards
- workflow patterns
- shared tooling conventions
- generic capability definitions

## Recommendation

If you want the most predictable setup for Codex, VS Code agents, and CI:

1. mount `agent-forge` inside the consuming repo at `vendor/agent-forge/`
2. reference `vendor/agent-forge/docs/capabilities_index.md`
3. list only the relevant topic files in the consuming repo `AGENTS.md`

That gives you stable paths, explicit version control, and a clean boundary between shared capability and project-specific guidance.
