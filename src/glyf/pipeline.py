from dataclasses import dataclass
from pathlib import Path

from glyf.config import ExecutionConfig, GlyfConfig
from glyf.execution import QueryResult, SqlExecutionError, execute_sql
from glyf.execution.limits import wrap_row_limit
from glyf.ggsql.models import GgsqlChart
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql_file
from glyf.ggsql.renderer import ChartRenderError, missing_columns, render_chart
from glyf.manifest.loader import ManifestError, load_manifest
from glyf.manifest.resolver import resolve_refs
from glyf.output.writer import (
    ChartArtifacts,
    chart_artifact_paths,
    cleanup_legacy_chart_artifacts,
    write_chart_data,
    write_chart_metadata,
    write_compiled_sql,
)
from glyf.project.scanner import ProjectScan, scan_project


@dataclass(frozen=True)
class RenderedChart:
    chart: GgsqlChart
    compiled_sql: str
    data: QueryResult
    artifacts: ChartArtifacts


@dataclass(frozen=True)
class RenderResult:
    scan: ProjectScan
    charts: tuple[RenderedChart, ...]
    # True when the run only checked the queries; no chart artifacts exist.
    validated_only: bool = False


class RenderError(ValueError):
    """Raised when chart artifacts cannot be generated."""


def render_project(
    project: Path,
    config: GlyfConfig | None = None,
) -> RenderResult:
    config = config or GlyfConfig()
    execution = config.execution
    validate_only = execution.mode == "validate"
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
        cleanup_legacy_chart_artifacts(scan.root, chart, config)
        # The compiled SQL on disk is always the query as written; the bounds
        # below exist for this run, not for the artifact someone reads later.
        write_compiled_sql(artifacts.compiled_sql, resolution.sql)

        rel_path = path.relative_to(scan.root).as_posix()
        try:
            data = execute_sql(
                scan.root,
                _bounded_sql(resolution.sql, execution),
                executor=execution.backend,
                config=execution,
            )
        except SqlExecutionError as exc:
            raise RenderError(f"{rel_path} SQL execution failed: {exc}") from exc

        if validate_only:
            _check_columns(chart, data, rel_path)
            rendered.append(
                RenderedChart(
                    chart=chart,
                    compiled_sql=resolution.sql,
                    data=data,
                    artifacts=artifacts,
                )
            )
            continue

        if execution.max_rows is not None and len(data) > execution.max_rows:
            raise RenderError(
                f"{rel_path} returned more than {execution.max_rows} rows. "
                "Aggregate the query or raise execution.max_rows; glyf will not "
                "draw a chart from part of a result."
            )

        write_chart_data(scan.root, chart, artifacts, data)

        try:
            render_chart(
                chart,
                data,
                artifacts.png,
                artifacts.svg,
                config.render,
                vega_json_path=artifacts.vega_json,
            )
        except ChartRenderError as exc:
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

    return RenderResult(
        scan=scan,
        charts=tuple(rendered),
        validated_only=validate_only,
    )


def _bounded_sql(sql: str, execution: ExecutionConfig) -> str:
    """Apply whichever bound this run asks for, if any."""
    if execution.mode == "validate":
        return wrap_row_limit(sql, 0)
    if execution.max_rows is not None:
        # One more than the cap, so exceeding it is detectable rather than
        # indistinguishable from a result that exactly fills it.
        return wrap_row_limit(sql, execution.max_rows + 1)
    return sql


def _check_columns(chart: GgsqlChart, data: QueryResult, rel_path: str) -> None:
    """Validate the chart's bindings against a result that carries no rows."""
    missing = missing_columns(chart, data.columns)
    if missing:
        joined = ", ".join(f"'{field}'" for field in missing)
        raise RenderError(f"{rel_path} query result missing chart column {joined}")
