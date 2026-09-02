from pathlib import Path

import typer

from glyf.config import ConfigError, apply_run_overrides, load_config
from glyf.dashboard.generator import DashboardGenerationError, generate_dashboards
from glyf.selection import SelectionError


def run_dashboard(
    project: Path,
    config_path: Path | None = None,
    *,
    select: tuple[str, ...] | None = None,
    output_dir: Path | None = None,
) -> None:
    try:
        config = apply_run_overrides(
            load_config(project, config_path), output_dir=output_dir
        )
        generate_dashboards(project, config, select=select)
    except SelectionError as exc:
        typer.echo("Selection failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except DashboardGenerationError as exc:
        typer.echo("Dashboard generation failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    typer.echo("✓ discovered dashboard configs")
    typer.echo("✓ loaded chart artifacts")
    typer.echo("✓ generated dashboard HTML")
    typer.echo("✓ generated index page")
    typer.echo("✓ wrote bundle manifest")
