# AGENTS.md

This repository defines reusable engineering capability for humans and AI agents.

## Operating Rules

- Skills are reusable capabilities.
- Avoid model-specific coupling.
- Prefer small, composable workflows.
- Workflows orchestrate skills.
- Tools execute actions.
- Templates provide structure.
- Examples demonstrate usage.
- Keep everything modular.

## Design Principles

### Skills

Skills should describe a repeatable capability in a way that can be reused across projects and execution environments.

### Workflows

Workflows should combine skills into a practical sequence of actions. Keep them small enough to understand and maintain.

### Tools

Tools should be focused on execution. They are not where business logic or reusable process definition belongs.

### Templates

Templates should reduce ambiguity and improve consistency. They should be narrow, readable, and easy to adapt.

### Examples

Examples should show real usage patterns. They are reference material, not the source of truth.

## Maintenance Expectations

- Keep content Markdown-first.
- Prefer clarity over cleverness.
- Keep content vendor-neutral unless a project-specific adapter is required.
- Avoid duplication by linking to shared material instead of rewriting it.
- Update examples when workflows or skills change materially.

## Change Discipline

When adding a new capability:

1. define the skill
2. add or update a workflow if needed
3. provide a template if the output should be standardized
4. include an example if the pattern is likely to be reused

This repository should grow by adding focused building blocks, not by layering large undocumented procedures.
