from dataclasses import replace
from pathlib import Path

import typer

from glyf.config import ConfigError, load_config
from glyf.pipeline import RenderError, render_project


def run_render(
    project: Path,
    config_path: Path | None = None,
    *,
    validate: bool = False,
) -> None:
    try:
        config = load_config(project, config_path)
        if validate:
            config = replace(config, execution=replace(config.execution, mode="validate"))
        result = render_project(project, config)
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except RenderError as exc:
        typer.echo("Render failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    chart_count = len(result.charts)
    typer.echo(f"\u2713 discovered charts ({chart_count})")
    typer.echo("\u2713 compiled SQL")
    if result.validated_only:
        # Say what was not done, so a green CI run is not mistaken for a build.
        typer.echo("\u2713 checked SQL and chart columns (no rows fetched)")
        typer.echo("- skipped chart artifacts (validate mode)")
        return
    typer.echo("\u2713 executed SQL")
    typer.echo("\u2713 rendered PNG/SVG")
    typer.echo("\u2713 wrote metadata")
