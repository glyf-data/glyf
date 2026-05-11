from pathlib import Path

import typer

from dbt_ggsql.config import ConfigError, load_config
from dbt_ggsql.dashboard.loader import load_dashboard
from dbt_ggsql.ggsql.parser import GgsqlParseError, parse_ggsql_file
from dbt_ggsql.manifest.loader import ManifestError, load_manifest
from dbt_ggsql.manifest.resolver import resolve_refs
from dbt_ggsql.project.scanner import scan_project


def _rel(path: Path, project: Path) -> str:
    return path.relative_to(project).as_posix()


def run_validate(project: Path, config_path: Path | None = None) -> None:
    try:
        config = load_config(project, config_path)
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    scan = scan_project(project, config)
    errors: list[str] = []

    if scan.dbt_project_path is None:
        errors.append(
            "Missing dbt_project.yml. Run from a dbt project root or pass --project-dir."
        )
    if scan.visualisations_dir is None:
        errors.append(
            "Missing visualisations directory. Check visualisations_path in dbt_ggsql.yml."
        )
    if scan.dashboards_dir is None:
        errors.append(
            "Missing dashboards directory. Check dashboards_path in dbt_ggsql.yml."
        )
    if scan.manifest_path is None:
        errors.append(
            "Missing target/manifest.json. Run dbt compile or dbt build before dbt-ggsql."
        )
        manifest = None
    else:
        try:
            manifest = load_manifest(scan.manifest_path)
        except ManifestError as exc:
            errors.append(str(exc))
            manifest = None

    ggsql_names = {path.stem for path in scan.ggsql_files}

    for path in scan.ggsql_files:
        try:
            parsed = parse_ggsql_file(path)
        except GgsqlParseError as exc:
            errors.append(f"{_rel(path, scan.root)}: {exc}")
            continue

        if manifest is None:
            continue
        result = resolve_refs(parsed.sql, manifest)
        for ref in result.missing_refs:
            errors.append(f"{_rel(path, scan.root)} references unknown model '{ref}'")
        for source_name, table_name in result.missing_sources:
            errors.append(
                f"{_rel(path, scan.root)} references unknown source "
                f"'{source_name}.{table_name}'"
            )

    for path in scan.dashboard_files:
        try:
            dashboard = load_dashboard(path)
        except ValueError as exc:
            errors.append(f"{_rel(path, scan.root)}: {exc}")
            continue

        for chart in dashboard.charts:
            if chart not in ggsql_names:
                errors.append(
                    f"{_rel(path, scan.root)} references unknown chart '{chart}'"
                )

    if errors:
        typer.echo("Validation failed")
        for error in errors:
            typer.echo(f"  - {error}")
        raise typer.Exit(1)

    typer.echo("Validation passed")
    typer.echo(f"  GGSQL files: {len(scan.ggsql_files)}")
    typer.echo(f"  Dashboard YAML files: {len(scan.dashboard_files)}")
    typer.echo(f"  Manifest: {'present' if scan.manifest_path else 'missing'}")
