# MCP Server

`glyf mcp` serves a project to an AI agent over the
[Model Context Protocol](https://modelcontextprotocol.io). An agent that can
already read dbt models and write SQL gets what it lacks: which charts exist,
what each one draws, which charts a model or column change reaches, and
whether a chart it edited still validates. The tools are the CLI's own
functions, so the agent sees what a person sees.

## Install and run

The server needs the `mcp` extra:

```bash
uv tool install "glyf-core[mcp]"
```

It speaks stdio, the transport every local agent host uses. The host starts
it; you do not run it yourself:

```json title="Claude Code, Claude Desktop, Cursor, and others: the MCP servers config"
{
  "mcpServers": {
    "glyf": {
      "command": "glyf",
      "args": ["mcp", "--project-dir", "/path/to/your/dbt/project"]
    }
  }
}
```

With Claude Code from inside the project:

```bash
claude mcp add glyf -- glyf mcp --project-dir .
```

## Tools

| Tool | Returns |
| --- | --- |
| `list_charts` | Every chart: name, file, type, title, the models and sources it reads, the dashboards it is on. |
| `list_dashboards` | Every dashboard: name, title, description, tags, its charts in order. |
| `get_chart(name)` | One chart's file text and parsed spec: SQL, `VISUALISE` mappings, type, labels, config, interactions, the columns its SQL mentions, compiled SQL. |
| `impact(target)` | The charts and dashboards downstream of a model, a source or a column, as [`glyf impact`](../reference/cli.md#impact) reports it. |
| `validate(execute=false)` | The project's validation verdict. With `execute`, each chart's SQL runs with `LIMIT 0` and its columns are checked, as [`glyf validate --execute`](../reference/cli.md#validate) does. |
| `diff(baseline)` | What changed between the current build and an earlier one, the same document [`glyf diff`](../guides/visual-diff.md) writes to `diff.json`. |

The server's instructions tell the agent the order that works: list, then
`impact` before proposing a model change, then `validate` with `execute` after
editing a chart. A pull request an agent opens this way can name every
downstream chart and show that each still validates.

## What it does not do

It never runs a build and never fetches rows. `validate` with `execute` moves
zero rows, the same `LIMIT 0` dry run CI uses. Building, publishing and
anything that pulls data out of the warehouse stay with the person and the
pipeline. That is deliberate: a tool that let an agent query the warehouse
would be the exposure [data protection](../guides/data-exposure.md) is there to
prevent.

`diff` compares two builds that already exist; it is for a workflow where
the pipeline built both and the agent is asked to explain the result.

## For an assistant without MCP

The [AI assistants](../ai-context/overview.md) page has a brief to paste into
a tool that can only read files and run shell commands. The CLI commands it
names are the same functions the tools above call.
