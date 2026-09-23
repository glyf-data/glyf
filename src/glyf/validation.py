"""What `glyf validate` checks, as a result rather than printed lines.

The CLI prints it; the MCP server returns it. One implementation, so an agent
and a person see the same verdict for the same project.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from glyf.config import GlyfConfig
from glyf.dashboard.loader import load_dashboard
from glyf.dashboard.macros import (
    DashboardMacroError,
    DashboardMacroRegistry,
    MacroContext,
    resolve_dashboard_components,
)
from glyf.execution.dialect import sql_dialect
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql_file
from glyf.manifest.loader import ManifestError, load_manifest
from glyf.manifest.resolver import resolve_refs
from glyf.pipeline import RenderError, render_project
from glyf.project.scanner import scan_project


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    chart_count: int
    dashboard_count: int
    # Whether each chart's SQL was run against the warehouse with LIMIT 0.
    executed: bool
    backend: str
    # Structural checks that ran, in order, for the CLI's tick list.
    checks: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_project(
    project: Path, config: GlyfConfig, *, execute: bool = False
) -> ValidationResult:
    """Check the project's files and manifest refs; with `execute`, its SQL.

    The structural checks read files and the manifest and touch no warehouse.
    `execute` then runs every chart's query with `LIMIT 0` on the configured
    backend and checks the columns it returns against the chart's bindings:
    the check `glyf build --validate` makes, without the rest of the build.
    It moves no rows.
    """
    scan = scan_project(project, config)
    errors: list[str] = []
    warnings: list[str] = []
    dialect = sql_dialect(scan.root, config.execution)
    macro_context = MacroContext(scan.root, config, strict=False)
    try:
        macro_registry = DashboardMacroRegistry.from_project(
            scan.dashboards_dir, macro_context
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
        errors.append("Missing dashboards directory. Check dashboards_path in glyf.yml.")
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
        rel = path.relative_to(scan.root).as_posix()
        try:
            parsed = parse_ggsql_file(path, dialect=dialect)
        except GgsqlParseError as exc:
            errors.append(f"{rel}: {exc}")
            continue
        if parsed.sql_warning:
            warnings.append(f"{rel}: {parsed.sql_warning}")
        if manifest is None:
            continue
        result = resolve_refs(parsed.sql, manifest)
        for ref in result.missing_refs:
            errors.append(f"{rel} references unknown model '{ref}'")
        for source_name, table_name in result.missing_sources:
            errors.append(
                f"{rel} references unknown source '{source_name}.{table_name}'"
            )

    for path in scan.dashboard_files:
        rel = path.relative_to(scan.root).as_posix()
        try:
            dashboard = load_dashboard(path)
        except ValueError as exc:
            errors.append(f"{rel}: {exc}")
            continue
        if macro_registry is not None:
            try:
                dashboard = resolve_dashboard_components(dashboard, macro_registry)
            except DashboardMacroError as exc:
                errors.append(f"{rel}: {exc}")
        for chart in dashboard.artifact_chart_names:
            if chart not in ggsql_names:
                errors.append(f"{rel} references unknown chart '{chart}'")

    checks = [
        "validated project structure",
        "loaded manifest",
        f"validated GGSQL files ({len(scan.ggsql_files)})",
        f"validated dashboard specs ({len(scan.dashboard_files)})",
        "validated dashboard chart refs",
    ]
    if execute and not errors:
        # The files are sound; now the warehouse is asked. Its errors carry
        # the chart's file name, and a warning it prints is one the parser
        # already gave above, so only errors are kept here.
        dry_run = replace(config, execution=replace(config.execution, mode="validate"))
        try:
            render_project(scan.root, dry_run)
        except RenderError as exc:
            errors.append(str(exc))
        else:
            checks.append(
                f"ran each chart's SQL against {config.execution.backend} and checked "
                f"its columns ({len(scan.ggsql_files)} charts, no rows fetched)"
            )
    return ValidationResult(
        errors=tuple(errors),
        warnings=tuple(warnings),
        chart_count=len(scan.ggsql_files),
        dashboard_count=len(scan.dashboard_files),
        executed=execute and not errors,
        backend=config.execution.backend,
        checks=tuple(checks),
    )
