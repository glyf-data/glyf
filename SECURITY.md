# Security Policy

## Reporting a vulnerability

Please report a security problem privately, not in a public issue, a
discussion or Slack.

**[Report a vulnerability](https://github.com/glyf-data/glyf/security/advisories/new)**
through GitHub's private vulnerability reporting. Only the maintainer sees the
report. Include:

- what the problem is and what it lets someone do
- the `glyf` version (`glyf --version`) and how it was installed
- the smallest project, `.ggsql` file or command that shows it

`glyf` has one maintainer, so a reply can take a little while. Once a fix is
released the advisory is published; say in your report whether you would like
to be credited in it.

## What counts

`glyf` is a build tool: it runs on your machine or in your CI, reads your dbt
project, queries your warehouse and writes files. Reports about any of these
are in scope:

- a published site that contains data it should not, given the project's
  `export.row_data` and `privacy` settings
- a secret from `profiles.yml` or the environment appearing in output, an error
  message, `build.json` or a published file
- a crafted `.ggsql` file, dashboard YAML or `manifest.json` that makes `glyf`
  read or write outside the project, or run code
- a vulnerability in the published packages or the install script

## What does not

**Who can open a published dashboard is not something `glyf` controls.** It
writes static files with no login inside them; access is decided by wherever
you host them. [What a Published Site Exposes](https://glyfdata.com/docs/guides/data-exposure)
explains what a build publishes and how to publish less. A dashboard being
readable by someone who can reach its URL is how static files work, not a
vulnerability in `glyf`.

A viewer who is allowed to open a chart can read the values it displays. That
is also not a vulnerability.

## Supported versions

Fixes are released for the latest version. Please upgrade before reporting.
