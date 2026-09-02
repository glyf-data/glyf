import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import typer

from glyf.config import ConfigError, apply_run_overrides, load_config
from glyf.pipeline import RenderError, render_project
from glyf.provenance import append_build_event, failure_record
from glyf.selection import SelectionError


def run_render(
    project: Path,
    config_path: Path | None = None,
    *,
    validate: bool = False,
    target: str | None = None,
    select: tuple[str, ...] | None = None,
    output_dir: Path | None = None,
    log_json: Path | None = None,
) -> None:
    config = None
    started = time.monotonic()
    try:
        config = apply_run_overrides(
            load_config(project, config_path),
            target=target,
            output_dir=output_dir,
        )
        if validate:
            config = replace(config, execution=replace(config.execution, mode="validate"))
        result = render_project(project, config, select=select)
    except RenderError as exc:
        # An audit log that records only successful builds is a weak one.
        _log_failure(config, project, select, log_json, started, str(exc))
        typer.echo("Render failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except SelectionError as exc:
        typer.echo("Selection failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    if result.build is not None and log_json is not None:
        append_build_event(log_json, result.build)

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


def _log_failure(
    config: object,
    project: Path,
    select: tuple[str, ...] | None,
    log_json: Path | None,
    started: float,
    error: str,
) -> None:
    if log_json is None or config is None:
        return
    built_at = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    append_build_event(
        log_json,
        failure_record(
            project=project.name,
            built_at=built_at,
            config=config,
            error=error,
            selectors=select,
            duration_ms=int((time.monotonic() - started) * 1000),
        ),
    )
