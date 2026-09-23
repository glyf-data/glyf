import json
from pathlib import Path

import typer

from glyf.config import ConfigError, load_config
from glyf.impact import ImpactError, compute_impact


def run_impact(
    project: Path,
    target: str,
    *,
    config_path: Path | None = None,
    as_json: bool = False,
) -> None:
    try:
        config = load_config(project, config_path)
        report = compute_impact(project, config, target)
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except ImpactError as exc:
        typer.echo("Impact failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    if as_json:
        typer.echo(json.dumps(report.as_document(), indent=2, sort_keys=True))
        return

    typer.echo(report.headline())
    if not report.charts:
        return
    width = max(len(chart.path) for chart in report.charts)
    detail_width = max(len(_detail(chart)) for chart in report.charts)
    for chart in report.charts:
        boards = ", ".join(chart.dashboards) or "no dashboard"
        typer.echo(
            f"  {chart.path.ljust(width)}  {_detail(chart).ljust(detail_width)}  {boards}"
        )


def _detail(chart) -> str:
    # `may read` is the whole point of the line, so it comes before the why.
    if chart.certainty == "may read":
        return f"{chart.detail}, may read"
    return chart.detail
