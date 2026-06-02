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
) -> None:
    _run_step(
        "validate",
        "validated project",
        lambda: run_validate(project, config_path),
        verbose,
    )
    _run_step(
        "render",
        "rendered chart artifacts",
        lambda: run_render(project, config_path),
        verbose,
    )
    _run_step(
        "dashboard",
        "generated dashboard HTML",
        lambda: run_dashboard(project, config_path),
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
    typer.echo(f"✓ {summary}")
