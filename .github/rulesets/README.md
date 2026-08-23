# Repository rulesets

This directory is the versioned source of truth for reusable GitHub repository
rulesets. Committing a ruleset here does not automatically apply it on GitHub.

## Protect main

[`protect-main.json`](protect-main.json) applies an active ruleset to `main`
that:

- blocks branch deletion and non-fast-forward pushes
- requires changes to arrive through a pull request
- requires all review threads to be resolved
- requires extra approval for unattributed changes
- allows merge commits, squash merges, and rebases

The template intentionally excludes repository-specific and server-generated
fields such as the ruleset ID, source repository, timestamps, node ID, and API
links.

## Apply the template

Before creating a ruleset, list the repository's existing rulesets to avoid
creating a duplicate:

```bash
gh api repos/OWNER/REPO/rulesets \
  --jq '.[] | [.id, .name, .enforcement] | @tsv'
```

Create the ruleset only when the target repository does not already have it:

```bash
gh api --method POST repos/OWNER/REPO/rulesets \
  --input .github/rulesets/protect-main.json
```

To synchronize an existing ruleset, use its ID from the listing command:

```bash
gh api --method PUT repos/OWNER/REPO/rulesets/RULESET_ID \
  --input .github/rulesets/protect-main.json
```

The file can also be imported from the repository's **Settings** > **Rules** >
**Rulesets** page using **New ruleset** > **Import a ruleset**. Review the
imported configuration before creating it. Importing creates a new ruleset, so
update an existing ruleset instead when one already exists.
