from dataclasses import replace
from pathlib import Path

import typer

from glyf.config import ConfigError, apply_run_overrides, load_config
from glyf.dashboard.loader import load_dashboard
from glyf.dashboard.macros import (
    DashboardMacroError,
    MacroContext,
    DashboardMacroRegistry,
    resolve_dashboard_components,
)
from glyf.execution.dialect import sql_dialect
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql_file
from glyf.manifest.loader import ManifestError, load_manifest
from glyf.manifest.resolver import resolve_refs
from glyf.pipeline import RenderError, render_project
from glyf.project.scanner import scan_project


def _rel(path: Path, project: Path) -> str:
    return path.relative_to(project).as_posix()


def run_validate(
    project: Path,
    config_path: Path | None = None,
    *,
    execute: bool = False,
    target: str | None = None,
) -> None:
    """Check the project's files, and with `execute`, each chart's SQL.

    The structural checks read files and the manifest and touch no
    warehouse. `execute` then runs every chart's query with `LIMIT 0` on the
    configured backend and checks the columns it returns against the chart's
    bindings: the check `glyf build --validate` makes, without the rest of the
    build. It moves no rows, so it is safe on a runner outside the warehouse's
    boundary, and it is the only way to know before a build that a renamed
    column or a broken query is there.
    """
    try:
        config = load_config(project, config_path)
        if execute:
            config = apply_run_overrides(config, target=target, output_dir=None)
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    scan = scan_project(project, config)
    errors: list[str] = []
    warnings: list[str] = []
    dialect = sql_dialect(scan.root, config.execution)
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
            parsed = parse_ggsql_file(path, dialect=dialect)
        except GgsqlParseError as exc:
            errors.append(f"{_rel(path, scan.root)}: {exc}")
            continue
        if parsed.sql_warning:
            warnings.append(f"{_rel(path, scan.root)}: {parsed.sql_warning}")

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

    if execute:
        # The files are sound; now the warehouse is asked. Its errors carry
        # the chart's file name, and a warning it prints is one the parser
        # already gave above, so only errors are reported here.
        dry_run = replace(config, execution=replace(config.execution, mode="validate"))
        try:
            render_project(scan.root, dry_run)
        except RenderError as exc:
            typer.echo("Validation failed")
            typer.echo(f"  - {exc}")
            raise typer.Exit(1) from exc

    for warning in warnings:
        typer.echo(f"! {warning}")
    typer.echo("Validation passed")
    typer.echo("✓ validated project structure")
    typer.echo("✓ loaded manifest")
    typer.echo(f"✓ validated GGSQL files ({len(scan.ggsql_files)})")
    typer.echo(f"✓ validated dashboard specs ({len(scan.dashboard_files)})")
    typer.echo("✓ validated dashboard chart refs")
    if execute:
        typer.echo(
            f"✓ ran each chart's SQL against {config.execution.backend} "
            f"and checked its columns ({len(scan.ggsql_files)} charts, no rows fetched)"
        )
