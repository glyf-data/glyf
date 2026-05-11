from pathlib import Path

import typer

from dbt_ggsql.pipeline import RenderError, render_project


def run_render(project: Path) -> None:
    try:
        result = render_project(project)
    except RenderError as exc:
        typer.echo("Render failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    chart_count = len(result.charts)
    typer.echo(f"✓ discovered charts ({chart_count})")
    typer.echo("✓ compiled SQL")
    typer.echo("✓ executed SQL")
    typer.echo("✓ rendered PNG/SVG")
    typer.echo("✓ wrote metadata")
