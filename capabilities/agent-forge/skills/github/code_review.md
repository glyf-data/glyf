# Code Review Skill

## Purpose

Review a change for correctness, clarity, maintainability, and risk before merge.

## Inputs

- pull request or change description
- diff or changed files
- expected behavior
- context about the system
- test evidence, if available

## Outputs

- findings ordered by severity
- open questions
- requested fixes or follow-ups
- summary of the change quality

## Rules

- Prioritize bugs, regressions, and missing tests.
- Ground feedback in concrete file and line references when possible.
- Distinguish blockers from suggestions.
- Avoid style commentary unless it affects maintainability or correctness.

## Example Workflow

1. Read the change summary and scope.
2. Inspect the diff for behavioral changes.
3. Check error handling, edge cases, and regressions.
4. Verify test coverage against the risk.
5. Write findings in severity order.

## Acceptance Criteria

The review is complete when it:

- identifies the highest-risk issues first
- explains why each issue matters
- avoids unnecessary noise
- calls out missing verification where relevant
