from pathlib import Path
from typing import Annotated

import typer

from glyf.commands.build_cmd import run_build
from glyf.commands.dashboard_cmd import run_dashboard
from glyf.commands.doctor_cmd import run_doctor
from glyf.commands.export_cmd import run_export
from glyf.commands.init_cmd import run_init
from glyf.commands.list_cmd import run_list
from glyf.commands.render_cmd import run_render
from glyf.commands.serve_cmd import run_serve
from glyf.commands.validate_cmd import run_validate

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
        help="Path to glyf.yml. Defaults to PROJECT/glyf.yml if present.",
    ),
]


@app.command("init")
def init_command(
    project: ProjectOption = Path("."),
    config: ConfigOption = None,
    clean: Annotated[
        bool,
        typer.Option(
            "--clean",
            help="Replace starter chart/dashboard files created by init.",
        ),
    ] = False,
    chart_name: Annotated[
        str,
        typer.Option(
            "--chart-name",
            prompt="Starter chart name",
            help="Filename stem for the starter .ggsql file.",
        ),
    ] = "monthly_revenue",
    dashboard_name: Annotated[
        str,
        typer.Option(
            "--dashboard-name",
            prompt="Starter dashboard name",
            help="Filename stem for the starter dashboard YAML file.",
        ),
    ] = "executive",
    model_name: Annotated[
        str,
        typer.Option(
            "--model-name",
            prompt="dbt model ref for the starter chart",
            help="dbt model name used in the starter ref().",
        ),
    ] = "fct_revenue",
    chart_title: Annotated[
        str,
        typer.Option(
            "--chart-title",
            prompt="Starter chart title",
            help="Title label for the starter chart.",
        ),
    ] = "Monthly Revenue",
    chart_type: Annotated[
        str,
        typer.Option(
            "--chart-type",
            prompt="Starter chart type",
            help="Starter chart type: line, bar, scatter, area, or pie.",
        ),
    ] = "line",
) -> None:
    """Scaffold glyf files inside a dbt project."""
    run_init(
        project,
        config_path=config,
        clean=clean,
        chart_name=chart_name,
        dashboard_name=dashboard_name,
        model_name=model_name,
        chart_title=chart_title,
        chart_type=chart_type,
    )


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


@app.command("build")
def build_command(
    project: ProjectOption = Path("."),
    config: ConfigOption = None,
    clean: Annotated[
        bool,
        typer.Option(
            "--clean/--no-clean",
            help="Clean the previous site export before copying. Enabled by default.",
        ),
    ] = True,
    zip_site: Annotated[
        bool,
        typer.Option("--zip", help="Create target/glyf/glyf-site.zip."),
    ] = False,
) -> None:
    """Run the full glyf artifact pipeline and export a static site."""
    run_build(project, clean=clean, zip_site=zip_site, config_path=config)


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
        typer.Option("--zip", help="Create target/glyf/glyf-site.zip."),
    ] = False,
) -> None:
    """Copy generated outputs into a publish-ready static site folder."""
    run_export(project, clean=clean, zip_site=zip_site, config_path=config)


@app.command("serve")
def serve_command(
    project: ProjectOption = Path("."),
    config: ConfigOption = None,
    host: Annotated[
        str,
        typer.Option("--host", help="Host interface to bind. Defaults to 127.0.0.1."),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            min=0,
            max=65535,
            help="Port to bind. Defaults to 8000. Use 0 to choose an available port.",
        ),
    ] = 8000,
) -> None:
    """Serve the generated static dashboard site locally."""
    run_serve(project, host=host, port=port, config_path=config)


@app.command("doctor")
def doctor_command(project: ProjectOption = Path("."), config: ConfigOption = None) -> None:
    """Check whether a project is ready for glyf workflows."""
    run_doctor(project, config)
