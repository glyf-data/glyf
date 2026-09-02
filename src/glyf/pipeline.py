from dataclasses import dataclass, replace
from pathlib import Path

from glyf.config import ExecutionConfig, GlyfConfig
from glyf.execution import QueryResult, SqlExecutionError, execute_sql
from glyf.execution.limits import wrap_row_limit
from glyf.ggsql.models import GgsqlChart
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql_file
from glyf.ggsql.renderer import (
    ChartRenderError,
    missing_columns,
    prune_to_encoded_columns,
    render_chart,
    strip_svg_row_values,
)
from glyf.manifest.loader import ManifestError, load_manifest
from glyf.manifest.resolver import resolve_refs
from glyf.output.paths import artifact_paths
from glyf.output.writer import (
    ChartArtifacts,
    chart_artifact_paths,
    cleanup_legacy_chart_artifacts,
    write_chart_data,
    write_chart_metadata,
    write_compiled_sql,
)
from glyf.privacy import (
    PiiPolicyError,
    apply_pii_policy,
    classify_pii,
    scan_for_pii,
)
from glyf.project.scanner import ProjectScan, scan_project
from glyf.selection import Selection, resolve_selection


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
    # Which dashboards this run was restricted to, if any.
    selection: Selection | None = None
    # True when the run only checked the queries; no chart artifacts exist.
    validated_only: bool = False
    # Downgrades worth telling the user about, rather than doing silently.
    warnings: tuple[str, ...] = ()


class RenderError(ValueError):
    """Raised when chart artifacts cannot be generated."""


def render_project(
    project: Path,
    config: GlyfConfig | None = None,
    *,
    select: tuple[str, ...] | None = None,
) -> RenderResult:
    config = config or GlyfConfig()
    execution = config.execution
    validate_only = execution.mode == "validate"
    exclude_row_data = config.export.excludes_row_data
    prune_row_data = config.export.prunes_row_data
    render_config = (
        replace(config.render, formats=("png",))
        if exclude_row_data
        else config.render
    )
    warnings: list[str] = []
    scan = scan_project(project, config)
    selection = resolve_selection(scan, select)
    if scan.manifest_path is None:
        raise RenderError(
            "Missing target/manifest.json. Run dbt compile or dbt build before render."
        )

    try:
        manifest = load_manifest(scan.manifest_path)
    except ManifestError as exc:
        raise RenderError(str(exc)) from exc

    ggsql_files = scan.ggsql_files
    if selection is not None:
        ggsql_files = tuple(
            path for path in ggsql_files if path.stem in selection.chart_names
        )
        missing = sorted(selection.chart_names - {path.stem for path in ggsql_files})
        if missing:
            joined = ", ".join(f"'{name}'" for name in missing)
            raise RenderError(
                f"selected dashboards reference unknown chart {joined}"
            )

    rendered: list[RenderedChart] = []
    for path in ggsql_files:
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

        # The one place every backend's result passes through before anything
        # reads it. Under validate mode the result has columns and no rows,
        # which is all `deny` needs: CI catches a charted email with no data
        # moved.
        findings = classify_pii(data.columns, resolution, manifest, config.privacy)
        try:
            data = apply_pii_policy(
                data, findings, config.privacy, chart_path=rel_path
            )
        except PiiPolicyError as exc:
            raise RenderError(str(exc)) from exc

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

        if config.privacy.scan:
            # The safety net behind the classification above: it reads
            # values, so it needs rows, which is why validate mode cannot
            # run it. It warns rather than redacts -- a fuzzy match that
            # silently rewrote a column would be a wrong chart nobody knew
            # about.
            classified = tuple(finding.name for finding in findings)
            for suspect in scan_for_pii(data, skip=classified):
                message = (
                    f"{rel_path} {suspect.describe()} but is not classified as "
                    "PII. Tag it in schema.yml or list it in privacy.pii_columns"
                )
                if config.privacy.strict:
                    raise RenderError(f"{message} (privacy.strict).")
                warnings.append(message)

        write_chart_data(scan.root, chart, artifacts, data)

        if exclude_row_data:
            # An SVG carries every row in its per-mark accessibility labels and
            # a Vega spec carries them outright, so neither may exist. Clear
            # anything a previous build left behind, or export would ship it.
            _discard(artifacts.svg, artifacts.vega_json)
            if chart.is_interactive:
                warnings.append(
                    f"{rel_path} renders as a static PNG: its INTERACT clause "
                    "needs a Vega spec, which carries the rows "
                    "(export.row_data: exclude)"
                )

        # `.data.json` above keeps every column for the local build; what the
        # chart is drawn from -- and so what its Vega spec inlines -- may not.
        chart_data = prune_to_encoded_columns(chart, data) if prune_row_data else data
        try:
            render_chart(
                chart,
                chart_data,
                artifacts.png,
                artifacts.svg,
                render_config,
                vega_json_path=None if exclude_row_data else artifacts.vega_json,
            )
        except ChartRenderError as exc:
            raise RenderError(f"{rel_path} chart rendering failed: {exc}") from exc
        if prune_row_data and artifacts.svg.exists():
            strip_svg_row_values(artifacts.svg, chart)

        write_chart_metadata(scan.root, chart, artifacts)
        rendered.append(
            RenderedChart(
                chart=chart,
                compiled_sql=resolution.sql,
                data=data,
                artifacts=artifacts,
            )
        )

    if selection is not None and not validate_only:
        # The output directory has to describe the build that just ran. A
        # previous, wider build left artifacts here, and export copies the
        # directory rather than a list -- so another audience's chart would
        # ride along into this one's site.
        _prune_unselected_artifacts(scan.root, config, selection.chart_names)

    return RenderResult(
        scan=scan,
        charts=tuple(rendered),
        validated_only=validate_only,
        warnings=tuple(warnings),
        selection=selection,
    )


def _prune_unselected_artifacts(
    root: Path, config: GlyfConfig, keep: frozenset[str]
) -> None:
    paths = artifact_paths(root, config)
    directories = (
        paths.charts_dir,
        paths.compiled_dir,
        paths.normalized_data_dir,
        paths.vega_data_dir,
    )
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            # `revenue.data.json` and `revenue.vega.json` carry the chart name
            # before the first dot, not in `Path.stem`.
            if path.is_file() and path.name.split(".")[0] not in keep:
                path.unlink()


def _discard(*paths: Path) -> None:
    for path in paths:
        path.unlink(missing_ok=True)


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
