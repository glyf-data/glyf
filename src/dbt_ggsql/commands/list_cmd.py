from pathlib import Path

import typer

from dbt_ggsql.config import ConfigError, load_config
from dbt_ggsql.manifest.loader import load_manifest
from dbt_ggsql.project.scanner import scan_project


def _rel(path: Path, project: Path) -> str:
    return path.relative_to(project).as_posix()


def run_list(project: Path, config_path: Path | None = None) -> None:
    try:
        config = load_config(project, config_path)
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    scan = scan_project(project, config)

    typer.echo(f"Project: {scan.root}")
    typer.echo("")

    typer.echo(f"GGSQL files ({len(scan.ggsql_files)})")
    for path in scan.ggsql_files:
        typer.echo(f"  - {_rel(path, scan.root)}")

    typer.echo("")
    typer.echo(f"Dashboard YAML files ({len(scan.dashboard_files)})")
    for path in scan.dashboard_files:
        typer.echo(f"  - {_rel(path, scan.root)}")

    typer.echo("")
    if scan.manifest_path is None:
        typer.echo("Manifest: missing target/manifest.json")
        return

    typer.echo(f"Manifest: {_rel(scan.manifest_path, scan.root)}")
    manifest = load_manifest(scan.manifest_path)
    typer.echo(f"Models ({len(manifest.models)})")
    for model in manifest.models:
        typer.echo(f"  - {model.name} -> {model.relation_name}")
