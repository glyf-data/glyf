from pathlib import Path

import typer

from glyf.doctor import DoctorResult, run_doctor_checks


def run_doctor(project: Path, config_path: Path | None = None) -> None:
    result = run_doctor_checks(project, config_path)
    _print_result(result)
    if result.has_errors:
        raise typer.Exit(1)


def _print_result(result: DoctorResult) -> None:
    typer.echo(f"Project: {result.project_root}")
    for check in result.checks:
        label = check.status.upper()
        typer.echo(f"[{label}] {check.name}: {check.message}")
