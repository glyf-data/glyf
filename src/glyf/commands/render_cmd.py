from dataclasses import replace
from pathlib import Path

import typer

from glyf.config import ConfigError, apply_run_overrides, load_config
from glyf.pipeline import RenderError, render_project
from glyf.selection import SelectionError


def run_render(
    project: Path,
    config_path: Path | None = None,
    *,
    validate: bool = False,
    target: str | None = None,
    select: tuple[str, ...] | None = None,
    output_dir: Path | None = None,
) -> None:
    try:
        config = apply_run_overrides(
            load_config(project, config_path),
            target=target,
            output_dir=output_dir,
        )
        if validate:
            config = replace(config, execution=replace(config.execution, mode="validate"))
        result = render_project(project, config, select=select)
    except SelectionError as exc:
        typer.echo("Selection failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except RenderError as exc:
        typer.echo("Render failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    for warning in result.warnings:
        typer.echo(f"! {warning}")

    if result.selection is not None:
        # Say what was left out, so a short build is never a surprise.
        typer.echo(f"\u2713 selected dashboards ({result.selection.describe()})")
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
