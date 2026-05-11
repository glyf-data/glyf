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
    chart_label = "chart" if chart_count == 1 else "charts"
    typer.echo(f"✓ discovered {chart_count} {chart_label}")
    typer.echo("✓ parsed ggsql")
    typer.echo("✓ resolved refs")
    typer.echo("✓ generated compiled SQL")
    typer.echo("✓ wrote artifacts")
