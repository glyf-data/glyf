from pathlib import Path

import typer

from glyf.config import ConfigError, load_config
from glyf.dashboard.generator import DashboardGenerationError, generate_dashboards


def run_dashboard(project: Path, config_path: Path | None = None) -> None:
    try:
        config = load_config(project, config_path)
        generate_dashboards(project, config)
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except DashboardGenerationError as exc:
        typer.echo("Dashboard generation failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    typer.echo("✓ discovered dashboard configs")
    typer.echo("✓ loaded chart artifacts")
    typer.echo("✓ generated dashboard HTML")
    typer.echo("✓ generated index page")
    typer.echo("✓ wrote bundle manifest")
