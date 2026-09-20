from pathlib import Path

import typer

from glyf.config import ConfigError, load_config, resolve_project_path
from glyf.diff import DiffError, compare_builds, headline, write_report
from glyf.diff.report import describe_data, format_percent


def run_diff(
    project: Path,
    *,
    baseline: Path,
    threshold: float = 0.0,
    tolerance: int = 0,
    fail_on_change: bool = False,
    config_path: Path | None = None,
) -> None:
    try:
        config = load_config(project, config_path)
        current = resolve_project_path(project, config.output_path)
        diff = compare_builds(
            baseline, current, threshold=threshold, tolerance=tolerance
        )
        page = write_report(diff, diff.current / "diff")
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except DiffError as exc:
        typer.echo("Diff failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    for chart in diff.charts:
        if chart.status == "changed":
            typer.echo(
                f"~ {chart.name}: {format_percent(chart.changed_percent)} of the picture moved "
                f"({'; '.join(chart.reasons)})"
            )
            # What moved in the rows, under the chart it moved in: a CI log is
            # read more often than the report is downloaded.
            for line in describe_data(chart.data):
                typer.echo(f"    {line}")
        elif chart.status == "added":
            typer.echo(f"+ {chart.name}: added")
        elif chart.status == "removed":
            typer.echo(f"- {chart.name}: removed")
    typer.echo(f"✓ {headline(diff)}")
    typer.echo(f"✓ wrote {_rel(page, project)}")

    if fail_on_change and diff.has_changes:
        raise typer.Exit(1)


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
