# Philosophy

`agent-forge` is organized around reusable capabilities rather than isolated prompts.

## Core Ideas

### Capabilities Over Prompts

Prompts are transient. Capabilities can be versioned, reused, and improved over time.

### Workflows Over Isolated Tasks

A single task can be useful, but durable value comes from repeatable workflows that combine multiple skills into a reliable operating pattern.

### Reusable Intelligence

Domain knowledge should live in shared assets that can be applied across projects without rewriting the same instructions in different places.

### Composable Execution Systems

The repository should be made of small pieces that work together:

- skills define capability
- workflows define orchestration
- templates define structure
- tools define execution

### Human + AI Collaboration

The system should work for both humans and agents. Humans need clarity and maintainability; agents need explicit structure and predictable boundaries.

## What This Means In Practice

- keep reusable knowledge centralized
- keep project state local to the project
- design for reuse instead of one-off completion
- prefer explicit structure over hidden assumptions
- avoid coupling shared assets to a specific model or vendor
