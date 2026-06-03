from pathlib import Path

import typer

from glyf.config import ConfigError, load_config
from glyf.dashboard.loader import load_dashboard
from glyf.dashboard.macros import (
    DashboardMacroError,
    MacroContext,
    DashboardMacroRegistry,
    resolve_dashboard_components,
)
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql_file
from glyf.manifest.loader import ManifestError, load_manifest
from glyf.manifest.resolver import resolve_refs
from glyf.project.scanner import scan_project


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
    macro_context = MacroContext(scan.root, config, strict=False)
    try:
        macro_registry = DashboardMacroRegistry.from_project(
            scan.dashboards_dir,
            macro_context,
        )
    except DashboardMacroError as exc:
        errors.append(str(exc))
        macro_registry = None

    if scan.dbt_project_path is None:
        errors.append(
            "Missing dbt_project.yml. Run from a dbt project root or pass --project-dir."
        )
    if scan.visualisations_dir is None:
        errors.append(
            "Missing visualisations directory. Check visualisations_path in glyf.yml."
        )
    if scan.dashboards_dir is None:
        errors.append(
            "Missing dashboards directory. Check dashboards_path in glyf.yml."
        )
    if scan.manifest_path is None:
        errors.append(
            "Missing target/manifest.json. Run dbt compile or dbt build before glyf."
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
        if macro_registry is not None:
            try:
                dashboard = resolve_dashboard_components(dashboard, macro_registry)
            except DashboardMacroError as exc:
                errors.append(f"{_rel(path, scan.root)}: {exc}")

        for chart in dashboard.artifact_chart_names:
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
    typer.echo("✓ validated project structure")
    typer.echo("✓ loaded manifest")
    typer.echo(f"✓ validated GGSQL files ({len(scan.ggsql_files)})")
    typer.echo(f"✓ validated dashboard specs ({len(scan.dashboard_files)})")
    typer.echo("✓ validated dashboard chart refs")
