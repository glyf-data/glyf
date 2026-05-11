from pathlib import Path
from typing import Annotated

import typer

from dbt_ggsql.commands.dashboard_cmd import run_dashboard
from dbt_ggsql.commands.export_cmd import run_export
from dbt_ggsql.commands.list_cmd import run_list
from dbt_ggsql.commands.render_cmd import run_render
from dbt_ggsql.commands.validate_cmd import run_validate

app = typer.Typer(
    help="Discover, validate, render, and publish ggsql assets in a dbt project."
)

ProjectOption = Annotated[
    Path,
    typer.Option(
        "--project-dir",
        "--project",
        "-p",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Path to a dbt project. Defaults to the current directory.",
    ),
]

ConfigOption = Annotated[
    Path | None,
    typer.Option(
        "--config",
        file_okay=True,
        dir_okay=False,
        help="Path to dbt_ggsql.yml. Defaults to PROJECT/dbt_ggsql.yml if present.",
    ),
]


@app.command("list")
def list_command(project: ProjectOption = Path("."), config: ConfigOption = None) -> None:
    """List discovered ggsql project files."""
    run_list(project, config)


@app.command("validate")
def validate_command(project: ProjectOption = Path("."), config: ConfigOption = None) -> None:
    """Validate discovered files and manifest refs."""
    run_validate(project, config)


@app.command("render")
def render_command(project: ProjectOption = Path("."), config: ConfigOption = None) -> None:
    """Generate compiled SQL and chart artifacts."""
    run_render(project, config)


@app.command("dashboard")
def dashboard_command(project: ProjectOption = Path("."), config: ConfigOption = None) -> None:
    """Generate static dashboard HTML from rendered chart artifacts."""
    run_dashboard(project, config)


@app.command("export")
def export_command(
    project: ProjectOption = Path("."),
    config: ConfigOption = None,
    clean: Annotated[
        bool,
        typer.Option("--clean", help="Delete the previous site export before copying."),
    ] = False,
    zip_site: Annotated[
        bool,
        typer.Option("--zip", help="Create target/ggsql/dbt-ggsql-site.zip."),
    ] = False,
) -> None:
    """Copy generated outputs into a publish-ready static site folder."""
    run_export(project, clean=clean, zip_site=zip_site, config_path=config)
