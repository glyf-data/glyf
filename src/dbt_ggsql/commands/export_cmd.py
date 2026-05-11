from pathlib import Path

import typer

from dbt_ggsql.config import ConfigError, load_config
from dbt_ggsql.exporter import ExportError, export_site


def run_export(
    project: Path,
    *,
    clean: bool = False,
    zip_site: bool = False,
    config_path: Path | None = None,
) -> None:
    try:
        config = load_config(project, config_path)
        result = export_site(project, clean=clean, zip_site=zip_site, config=config)
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except ExportError as exc:
        typer.echo("Export failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    typer.echo("✓ copied dashboard HTML")
    typer.echo("✓ copied chart artifacts")
    typer.echo("✓ copied compiled SQL")
    typer.echo("✓ wrote site assets")
    typer.echo(f"✓ exported site to {result.site_dir.relative_to(result.scan.root)}")
    if result.zip_path is not None:
        typer.echo(f"✓ wrote zip archive {result.zip_path.relative_to(result.scan.root)}")
