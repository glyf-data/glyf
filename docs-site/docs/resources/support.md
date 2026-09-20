# Support

Where to take a question, and what to check before you ask it.

## Where to ask what

| You want to | Go to |
| --- | --- |
| Get unstuck, or talk through how to do something | [Slack](pathname:///slack), in the help channel. The quickest answer. |
| Ask something others will search for later | [GitHub Discussions](https://github.com/glyf-data/glyf/discussions) |
| Report a bug | [Open an issue](https://github.com/glyf-data/glyf/issues/new/choose) |
| Propose a feature | [Open a feature request](https://github.com/glyf-data/glyf/issues/new/choose), or Discussions while it is still an idea |
| Report a security problem | **Privately**, through [GitHub's vulnerability reporting](https://github.com/glyf-data/glyf/security/advisories/new). Never in a public issue or in Slack. See the [security policy](https://github.com/glyf-data/glyf/blob/main/SECURITY.md). |

Already in the Slack? The help channel is
[here](https://glyfdata.slack.com/archives/C0C30CX7ZDZ).

Slack is quick, and its history is neither public nor permanent. When a
conversation there finds a bug or settles a decision, it still goes into an
issue or a discussion afterwards.

## Before you ask

Run this in your project and include its output:

```bash
glyf doctor
```

It checks that dbt's `manifest.json` exists, which execution backend and dbt
target the project would use, whether that warehouse's driver is installed, and
whether a `select 1` reaches the warehouse. It separates "glyf cannot connect"
from "my chart is wrong", which is most of the way to an answer.

Then check [Troubleshooting](troubleshooting.md), which covers the common
failures.

## A good question

Whether it goes to Slack, a discussion or an issue, include:

- the `glyf` version, from `glyf --version`
- the command you ran
- what happened: the error text, or what you expected and what you got
- the output of `glyf doctor`
- the smallest `.ggsql` file or project that shows it, when you can

## A bug, or a question?

If you are not sure, ask in Slack or Discussions first. It is a bug when `glyf`
does something other than what the documentation says, fails without telling
you what to change, or publishes something your settings said it would not.
