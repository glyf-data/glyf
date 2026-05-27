# GitHub Tools

This folder is reserved for future GitHub-focused tooling.

Expected future content may include:

- repository automation
- issue and pull request helpers
- milestone and release support
- API-backed operational scripts

The repository starts with documentation-first placeholders so the tool layer can be added without forcing a framework too early.

## Current Tool

- `backlog_to_project.sh` - create GitHub Project draft items from a markdown backlog file

## Usage

```bash
./tools/github/backlog_to_project.sh \
  --owner my-org \
  --project 1 \
  --input examples/backlog_input.md
```

The script uses `gh project item-create`, so GitHub CLI authentication must include the `project` scope.
