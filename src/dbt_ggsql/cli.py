from pathlib import Path
from typing import Annotated

import typer

from dbt_ggsql.commands.dashboard_cmd import run_dashboard
from dbt_ggsql.commands.list_cmd import run_list
from dbt_ggsql.commands.render_cmd import run_render
from dbt_ggsql.commands.validate_cmd import run_validate

app = typer.Typer(
    help="Discover, validate, render, and publish ggsql assets in a dbt project."
)

ProjectOption = Annotated[
    Path,
    typer.Option(
        "--project",
        "-p",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Path to a dbt project.",
    ),
]


@app.command("list")
def list_command(project: ProjectOption = Path(".")) -> None:
    """List discovered ggsql project files."""
    run_list(project)


@app.command("validate")
def validate_command(project: ProjectOption = Path(".")) -> None:
    """Validate discovered files and manifest refs."""
    run_validate(project)


@app.command("render")
def render_command(project: ProjectOption = Path(".")) -> None:
    """Generate compiled SQL and chart artifacts."""
    run_render(project)


@app.command("dashboard")
def dashboard_command(project: ProjectOption = Path(".")) -> None:
    """Generate static dashboard HTML from rendered chart artifacts."""
    run_dashboard(project)
