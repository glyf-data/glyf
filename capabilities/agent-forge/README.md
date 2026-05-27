# agent-forge

`agent-forge` is a reusable engineering and AI capability library for multiple projects.

It is not a prompt dump. It is a shared execution system for humans and agents: a place to keep reusable skills, workflows, templates, tools, examples, and documentation in one modular repository.

## Purpose

The goal is to centralize capability instead of repeating it in every project. A project should be able to reference a skill, follow a workflow, or reuse a template without re-implementing the same operating logic in different places.

This repository is designed to:

- scale over time
- stay model and vendor agnostic
- support both AI agents and humans
- reduce duplication across projects
- keep reusable capability discoverable and maintainable

## Philosophy

- Capabilities over prompts
- Workflows over isolated tasks
- Reusable intelligence over one-off instructions
- Composable execution systems over monolithic automation
- Human and AI collaboration over agent-only assumptions

The core idea is simple: skills define what can be done, workflows define how capabilities are composed, templates define the expected structure, and tools carry out the actual action when needed.

## Repository Structure

```text
agent-forge/
├── README.md
├── AGENTS.md
├── docs/
├── skills/
├── workflows/
├── templates/
├── tools/
├── agents/
├── examples/
└── .gitignore
```

- `docs/` contains repository-level guidance and architecture notes.
- `docs/capabilities_index.md` provides a topic-based index of reusable capabilities.
- `docs/consuming_agent_forge.md` explains how downstream repositories should mount and reference the shared library.
- `skills/` contains reusable capability modules, organized by domain.
- `workflows/` contains repeatable multi-step operating patterns that orchestrate skills.
- `templates/` contains Markdown structures that standardize outputs and inputs.
- `tools/` contains future executable integrations and tool-specific guidance.
- `agents/` contains agent-oriented assets and conventions.
- `examples/` contains practical examples of how the system is used in real projects.

## How Projects Use This Repository

Projects should reference this repository as a shared source of truth for reusable capability.

Typical usage patterns:

1. Import or mirror a relevant skill into the project’s working context.
2. Follow a workflow when a task needs multiple steps or coordination.
3. Use a template when you want consistent output formatting or handoff structure.
4. Call out to a tool only when the task requires execution, integration, or side effects.

This keeps projects small and focused while allowing the reusable system to evolve centrally.

## Example Usage

### Use a skill directly

If a project needs to break down a GitHub issue, it can reference:

`skills/github/issue_breakdown.md`

### Use a workflow

If a project needs a milestone delivered end to end, it can follow:

`workflows/milestone_execution.md`

If a project only needs a lightweight backlog from a goal or feature idea, it can follow:

`workflows/backlog_creation_workflow.md`

### Use a template

If a project needs a consistent milestone plan, it can use:

`templates/milestone_template.md`

## Reference Model

Projects should treat this repository as a capability library, not as copy-paste content.

Recommended pattern:

- keep domain knowledge here
- keep project-specific state in the project
- avoid hard-coding vendor or model assumptions into reusable assets
- favor small, composable building blocks over large bespoke procedures

## Future Vision

Over time, `agent-forge` should become a durable library of:

- domain skills
- operational workflows
- execution tools
- reusable templates
- agent coordination patterns
- tested examples and patterns

The long-term objective is a stable capability layer that can be shared across teams and projects without turning into prompt sprawl or duplicated process docs.

## Suggested Next Milestones

1. Add more production-grade skills for common engineering work such as testing, code review, incident handling, and release management.
2. Define a small set of end-to-end workflows that compose multiple skills into repeatable operating patterns.
3. Add executable tools only where there is a real integration point or recurring automation need.
4. Expand the examples with project-shaped walkthroughs that show how teams should apply the library.
5. Introduce versioning and change notes once multiple projects start depending on the same capabilities.
