from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from dbt_ggsql.config import DbtGgsqlConfig
from dbt_ggsql.execution.duckdb import SqlExecutionError, execute_sql
from dbt_ggsql.ggsql.models import GgsqlChart
from dbt_ggsql.ggsql.parser import GgsqlParseError, parse_ggsql_file
from dbt_ggsql.ggsql.renderer import ChartRenderError, render_chart
from dbt_ggsql.manifest.loader import ManifestError, load_manifest
from dbt_ggsql.manifest.resolver import resolve_refs
from dbt_ggsql.output.writer import (
    ChartArtifacts,
    chart_artifact_paths,
    write_chart_metadata,
    write_compiled_sql,
)
from dbt_ggsql.project.scanner import ProjectScan, scan_project


@dataclass(frozen=True)
class RenderedChart:
    chart: GgsqlChart
    compiled_sql: str
    data: pd.DataFrame
    artifacts: ChartArtifacts


@dataclass(frozen=True)
class RenderResult:
    scan: ProjectScan
    charts: tuple[RenderedChart, ...]


class RenderError(ValueError):
    """Raised when chart artifacts cannot be generated."""


def render_project(
    project: Path,
    config: DbtGgsqlConfig | None = None,
) -> RenderResult:
    config = config or DbtGgsqlConfig()
    scan = scan_project(project, config)
    if scan.manifest_path is None:
        raise RenderError(
            "Missing target/manifest.json. Run dbt compile or dbt build before render."
        )

    try:
        manifest = load_manifest(scan.manifest_path)
    except ManifestError as exc:
        raise RenderError(str(exc)) from exc

    rendered: list[RenderedChart] = []
    for path in scan.ggsql_files:
        try:
            chart = parse_ggsql_file(path)
        except GgsqlParseError as exc:
            rel_path = path.relative_to(scan.root).as_posix()
            raise RenderError(f"{rel_path}: {exc}") from exc

        resolution = resolve_refs(chart.sql, manifest)
        missing_refs = [f"ref('{ref}')" for ref in resolution.missing_refs]
        missing_sources = [
            f"source('{source_name}', '{table_name}')"
            for source_name, table_name in resolution.missing_sources
        ]
        if missing_refs or missing_sources:
            missing = ", ".join(missing_refs + missing_sources)
            rel_path = path.relative_to(scan.root).as_posix()
            raise RenderError(f"{rel_path} has unresolved dbt references: {missing}")

        artifacts = chart_artifact_paths(scan.root, chart, config)
        write_compiled_sql(artifacts.compiled_sql, resolution.sql)

        try:
            data = execute_sql(scan.root, resolution.sql)
        except SqlExecutionError as exc:
            rel_path = path.relative_to(scan.root).as_posix()
            raise RenderError(f"{rel_path} SQL execution failed: {exc}") from exc

        try:
            render_chart(chart, data, artifacts.png, artifacts.svg, config.render)
        except ChartRenderError as exc:
            rel_path = path.relative_to(scan.root).as_posix()
            raise RenderError(f"{rel_path} chart rendering failed: {exc}") from exc

        write_chart_metadata(scan.root, chart, artifacts)
        rendered.append(
            RenderedChart(
                chart=chart,
                compiled_sql=resolution.sql,
                data=data,
                artifacts=artifacts,
            )
        )

    return RenderResult(scan=scan, charts=tuple(rendered))
