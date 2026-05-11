from pathlib import Path

import typer

from dbt_ggsql.dashboard.generator import DashboardGenerationError, generate_dashboards


def run_dashboard(project: Path) -> None:
    try:
        generate_dashboards(project)
    except DashboardGenerationError as exc:
        typer.echo("Dashboard generation failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    typer.echo("✓ discovered dashboard configs")
    typer.echo("✓ loaded chart artifacts")
    typer.echo("✓ generated dashboard HTML")
    typer.echo("✓ generated index page")
