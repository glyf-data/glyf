# Test Strategy Skill

## Purpose

Define a practical testing approach for a codebase, feature, or change set.

Use this skill when a team needs to decide what to test, at what level, and with what priority.

## Inputs

- feature or system scope
- risk profile
- change size
- critical user flows
- existing test coverage
- operational constraints

## Outputs

- testing goals
- test layers to use
- high-priority scenarios
- coverage gaps
- validation order
- remaining risk notes

## Rules

- Focus testing effort where the risk is highest.
- Prefer a small number of meaningful checks over broad but shallow coverage.
- Separate unit, integration, and end-to-end concerns.
- Call out what is intentionally not being tested.
- Keep the plan executable by a human or an automated agent.

## Example Workflow

1. Identify the highest-risk behavior in scope.
2. Map the behavior to the appropriate test layers.
3. Define the minimum set of checks required for confidence.
4. Note existing coverage and gaps.
5. Produce a sequence for running or adding tests.

## Acceptance Criteria

The output is acceptable when it:

- names the primary testing goal
- identifies the important test layers
- prioritizes critical paths
- documents gaps and residual risk
- is specific enough to drive implementation or review
