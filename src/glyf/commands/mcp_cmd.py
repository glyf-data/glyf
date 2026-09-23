from pathlib import Path

import typer

from glyf.config import ConfigError
from glyf.mcp_server import McpUnavailable, build_server


def run_mcp(project: Path, config_path: Path | None = None) -> None:
    """Serve the project to an agent over stdio until the client hangs up."""
    try:
        server = build_server(project, config_path)
    except McpUnavailable as exc:
        typer.echo("MCP server unavailable", err=True)
        typer.echo(f"  - {exc}", err=True)
        raise typer.Exit(1) from exc
    except ConfigError as exc:
        typer.echo("Config error", err=True)
        typer.echo(f"  - {exc}", err=True)
        raise typer.Exit(1) from exc
    server.run(transport="stdio")
