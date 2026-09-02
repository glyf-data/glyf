from collections.abc import Callable
from contextlib import redirect_stdout
import io
from pathlib import Path

import typer

from glyf.commands.dashboard_cmd import run_dashboard
from glyf.commands.export_cmd import run_export
from glyf.commands.render_cmd import run_render
from glyf.commands.validate_cmd import run_validate


def run_build(
    project: Path,
    *,
    clean: bool = True,
    zip_site: bool = False,
    config_path: Path | None = None,
    verbose: bool = False,
    validate: bool = False,
    target: str | None = None,
    select: tuple[str, ...] | None = None,
    output_dir: Path | None = None,
    log_json: Path | None = None,
) -> None:
    _run_step(
        "validate",
        "validated project",
        lambda: run_validate(project, config_path),
        verbose,
    )
    _run_step(
        "render",
        "checked chart SQL" if validate else "rendered chart artifacts",
        lambda: run_render(
            project,
            config_path,
            validate=validate,
            target=target,
            select=select,
            output_dir=output_dir,
            log_json=log_json,
        ),
        verbose,
    )
    if validate:
        # Nothing was drawn, so there is nothing to assemble or publish.
        typer.echo("- skipped dashboard and export (validate mode)")
        return
    _run_step(
        "dashboard",
        "generated dashboard HTML",
        lambda: run_dashboard(
            project, config_path, select=select, output_dir=output_dir
        ),
        verbose,
    )
    _run_step(
        "export",
        "exported static site",
        lambda: run_export(
            project,
            clean=clean,
            zip_site=zip_site,
            config_path=config_path,
            output_dir=output_dir,
        ),
        verbose,
    )


def _run_step(
    name: str,
    summary: str,
    action: Callable[[], None],
    verbose: bool,
) -> None:
    if verbose:
        typer.echo(f"Running {name}")
        action()
        return

    output = io.StringIO()
    try:
        with redirect_stdout(output):
            action()
    except Exception:
        typer.echo(output.getvalue(), nl=False)
        raise
    # A step's detail is noise on success, except for what it warned about:
    # a warning nobody sees is a silent downgrade.
    for line in output.getvalue().splitlines():
        if line.startswith("! "):
            typer.echo(line)
    typer.echo(f"✓ {summary}")
