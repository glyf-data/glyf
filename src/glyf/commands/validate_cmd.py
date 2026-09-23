from pathlib import Path

import typer

from glyf.config import ConfigError, apply_run_overrides, load_config
from glyf.validation import validate_project


def run_validate(
    project: Path,
    config_path: Path | None = None,
    *,
    execute: bool = False,
    target: str | None = None,
) -> None:
    """Check the project's files, and with `execute`, each chart's SQL.

    See `glyf.validation.validate_project`; this prints its result.
    """
    try:
        config = load_config(project, config_path)
        if execute:
            config = apply_run_overrides(config, target=target, output_dir=None)
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    result = validate_project(project, config, execute=execute)
    if result.errors:
        typer.echo("Validation failed")
        for error in result.errors:
            typer.echo(f"  - {error}")
        raise typer.Exit(1)

    for warning in result.warnings:
        typer.echo(f"! {warning}")
    typer.echo("Validation passed")
    for check in result.checks:
        typer.echo(f"✓ {check}")
