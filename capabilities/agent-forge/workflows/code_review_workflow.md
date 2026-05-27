# Code Review Workflow

## Purpose

Review a proposed change using reusable review criteria and a consistent output format.

## Sequence

1. Use the code review skill to assess the change against correctness and risk.
2. Use the test strategy skill if the change alters behavior or carries meaningful risk.
3. Capture findings in severity order.
4. Separate blocking issues from optional improvements.
5. Confirm whether additional verification is needed.

## Rules

- Focus on behavior first.
- Keep review notes actionable.
- Ground feedback in the actual diff.
- Do not bury high-severity issues below minor comments.

## Expected Result

A review should end with:

- a concise summary
- ordered findings
- explicit verification gaps
- clear next actions
