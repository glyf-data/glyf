import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path

from glyf.config import ExecutionConfig, GlyfConfig, RenderConfig
from glyf.downsample import Downsampling, downsample_m4, plan_downsampling
from glyf.execution import QueryResult, SqlExecutionError, execute_sql
from glyf.execution.dialect import sql_dialect
from glyf.execution.limits import wrap_row_limit
from glyf.ggsql.models import GgsqlChart
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql_file
from glyf.ggsql.renderer import (
    ChartRenderError,
    missing_columns,
    prune_to_encoded_columns,
    render_chart,
    strip_svg_row_values,
    table_columns,
)
from glyf.ggsql.kpi import render_kpi
from glyf.ggsql.table import render_table
from glyf.lineage import chart_lineage
from glyf.manifest.loader import DbtManifest, ManifestError, load_manifest
from glyf.manifest.resolver import RefResolution, resolve_refs
from glyf.ordering import is_order_sensitive, order_rows
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
    PiiColumn,
    PiiPolicyError,
    apply_pii_policy,
    classify_pii,
    scan_for_pii,
)
from glyf.project.scanner import ProjectScan, scan_project
from glyf.provenance import (
    BuildRecord,
    ChartRecord,
    build_record,
    sql_digest,
    write_build_record,
)
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
    # What the run did, for the audit record. None only when unset by a
    # caller constructing a result by hand.
    build: BuildRecord | None = None
    # True when the run only checked the queries; no chart artifacts exist.
    validated_only: bool = False
    # Downgrades worth telling the user about, rather than doing silently.
    warnings: tuple[str, ...] = ()


class RenderError(ValueError):
    """Raised when chart artifacts cannot be generated."""


@dataclass
class _Run:
    """What every chart in one render shares, and what the run accumulates."""

    scan: ProjectScan
    manifest: DbtManifest
    config: GlyfConfig
    # The render settings this run draws with; `export.row_data: exclude`
    # narrows them to PNG before any chart is drawn.
    render_config: RenderConfig
    # Downgrades worth telling the user about, rather than doing silently.
    warnings: list[str] = field(default_factory=list)
    records: list[ChartRecord] = field(default_factory=list)
    # The SQL dialect the charts are read in; see `glyf.execution.dialect`.
    dialect: str = "generic"

    @property
    def validate_only(self) -> bool:
        return self.config.execution.mode == "validate"

    @property
    def exclude_row_data(self) -> bool:
        return self.config.export.excludes_row_data

    @property
    def prune_row_data(self) -> bool:
        return self.config.export.prunes_row_data


@dataclass(frozen=True)
class _Compiled:
    """A chart file parsed and resolved, with nothing run yet."""

    chart: GgsqlChart
    sql: str
    resolution: RefResolution
    artifacts: ChartArtifacts
    # The file as the user would type it, for every message about this chart.
    rel_path: str
    # The models and sources behind the chart, for its metadata.
    lineage: dict[str, object]


def render_project(
    project: Path,
    config: GlyfConfig | None = None,
    *,
    select: tuple[str, ...] | None = None,
) -> RenderResult:
    config = config or GlyfConfig()
    started = time.monotonic()
    built_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
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

    run = _Run(
        scan=scan,
        manifest=manifest,
        config=config,
        render_config=(
            replace(config.render, formats=("png",))
            if config.export.excludes_row_data
            else config.render
        ),
        dialect=sql_dialect(scan.root, config.execution),
    )
    rendered = tuple(
        _render_chart_file(path, run) for path in _selected_files(scan, selection)
    )

    if selection is not None and not run.validate_only:
        # The output directory has to describe the build that just ran. A
        # previous, wider build left artifacts here, and export copies the
        # directory rather than a list -- so another audience's chart would
        # ride along into this one's site.
        _prune_unselected_artifacts(scan.root, config, selection.chart_names)

    record = build_record(
        project=scan.root.name,
        built_at=built_at,
        config=config,
        charts=tuple(run.records),
        selectors=None if selection is None else selection.selectors,
        dashboards=None if selection is None else selection.dashboard_names,
        dbt_manifest_generated_at=manifest.generated_at,
        duration_ms=int((time.monotonic() - started) * 1000),
    )
    # An artifact of the render, written where the others are. `glyf export`
    # does not copy the output root, so it stays local unless someone opts in
    # to publishing it through the bundle.
    write_build_record(artifact_paths(scan.root, config).root / "build.json", record)

    return RenderResult(
        scan=scan,
        charts=rendered,
        validated_only=run.validate_only,
        warnings=tuple(run.warnings),
        selection=selection,
        build=record,
    )


def _selected_files(scan: ProjectScan, selection: Selection | None) -> tuple[Path, ...]:
    """The chart files this run builds: all of them, or a selection's."""
    if selection is None:
        return scan.ggsql_files
    files = tuple(
        path for path in scan.ggsql_files if path.stem in selection.chart_names
    )
    missing = sorted(selection.chart_names - {path.stem for path in files})
    if missing:
        joined = ", ".join(f"'{name}'" for name in missing)
        raise RenderError(f"selected dashboards reference unknown chart {joined}")
    return files


def _render_chart_file(path: Path, run: _Run) -> RenderedChart:
    """One chart, from its file to its artifacts.

    The order of these steps is the design. Everything between the query
    returning and the chart being drawn sits in one place, so that a rule about
    rows -- a PII policy, a cap, an order -- holds for every backend and cannot
    be skipped by choosing a different one.
    """
    compiled = _compile(path, run)
    data = _fetch_rows(compiled, run)
    data, findings = _apply_pii_policy(compiled, data, run)
    redacted = (
        tuple(finding.name for finding in findings)
        if run.config.privacy.on_pii == "redact"
        else ()
    )

    if run.validate_only:
        _check_columns(compiled.chart, data, compiled.rel_path)
        run.records.append(
            ChartRecord(
                name=compiled.chart.name,
                compiled_sql_sha256=sql_digest(compiled.sql),
                # A validate run fetches no rows; that is not zero rows.
                row_count=None,
                redacted_columns=redacted,
            )
        )
        return _rendered(compiled, data)

    _enforce_row_cap(compiled, data, run)
    data = _order(compiled, data, run)
    if not compiled.chart.has_picture:
        # A table lists its rows as they are and a kpi is one of them:
        # nothing to downsample, and a table's bound is on rows, not marks.
        if compiled.chart.is_table:
            _enforce_table_budget(compiled, data, run)
        render_data, plan = data, Downsampling(
            applied=False, reason="", rows=len(data), marks=len(data)
        )
    else:
        # Downsampling comes before the budget: the budget bounds what is
        # drawn, and what is drawn is what survives this.
        render_data, plan = _downsample(compiled, data, run)
        _enforce_mark_budget(compiled, render_data, run)
    scan_warnings = _scan_values(compiled, data, findings, run)

    run.records.append(
        ChartRecord(
            name=compiled.chart.name,
            compiled_sql_sha256=sql_digest(compiled.sql),
            row_count=len(data),
            redacted_columns=redacted,
            scan_warnings=scan_warnings,
            downsampled_to=plan.marks if plan.applied else None,
        )
    )
    _write_artifacts(compiled, data, render_data, run)
    return _rendered(compiled, data)


def _rendered(compiled: _Compiled, data: QueryResult) -> RenderedChart:
    return RenderedChart(
        chart=compiled.chart,
        compiled_sql=compiled.sql,
        data=data,
        artifacts=compiled.artifacts,
    )


def _compile(path: Path, run: _Run) -> _Compiled:
    """Parse the file, resolve its dbt references, and write the compiled SQL."""
    root = run.scan.root
    rel_path = path.relative_to(root).as_posix()
    try:
        chart = parse_ggsql_file(path, dialect=run.dialect)
    except GgsqlParseError as exc:
        raise RenderError(f"{rel_path}: {exc}") from exc
    if chart.sql_warning:
        run.warnings.append(f"{rel_path}: {chart.sql_warning}")
    if chart.is_table and run.exclude_row_data:
        # A picture can be published without its rows; a table is its rows.
        # Say so here, where validate mode also passes, rather than after the
        # query has run.
        raise RenderError(
            f"{rel_path} is a table, and export.row_data: exclude publishes no "
            "rows. Set export.row_data to include or minimal, or leave the "
            "table out of this build with --select."
        )

    resolution = resolve_refs(chart.sql, run.manifest)
    missing_refs = [f"ref('{ref}')" for ref in resolution.missing_refs]
    missing_sources = [
        f"source('{source_name}', '{table_name}')"
        for source_name, table_name in resolution.missing_sources
    ]
    if missing_refs or missing_sources:
        missing = ", ".join(missing_refs + missing_sources)
        raise RenderError(f"{rel_path} has unresolved dbt references: {missing}")

    artifacts = chart_artifact_paths(root, chart, run.config)
    cleanup_legacy_chart_artifacts(root, chart, run.config)
    # The compiled SQL on disk is always the query as written; the bounds
    # `_fetch_rows` adds exist for this run, not for the artifact someone reads
    # later.
    write_compiled_sql(artifacts.compiled_sql, resolution.sql)
    return _Compiled(
        chart=chart,
        sql=resolution.sql,
        resolution=resolution,
        artifacts=artifacts,
        rel_path=rel_path,
        lineage=chart_lineage(resolution, run.manifest),
    )


def _fetch_rows(compiled: _Compiled, run: _Run) -> QueryResult:
    execution = run.config.execution
    try:
        return execute_sql(
            run.scan.root,
            _bounded_sql(compiled.sql, execution),
            executor=execution.backend,
            config=execution,
        )
    except SqlExecutionError as exc:
        raise RenderError(f"{compiled.rel_path} SQL execution failed: {exc}") from exc


def _apply_pii_policy(
    compiled: _Compiled, data: QueryResult, run: _Run
) -> tuple[QueryResult, tuple[PiiColumn, ...]]:
    """Fail or redact, before anything else reads the rows.

    The one place every backend's result passes through. Under validate mode
    the result has columns and no rows, which is all `deny` needs: CI catches a
    charted email with no data moved.
    """
    privacy = run.config.privacy
    findings = classify_pii(data.columns, compiled.resolution, run.manifest, privacy)
    try:
        data = apply_pii_policy(data, findings, privacy, chart_path=compiled.rel_path)
    except PiiPolicyError as exc:
        raise RenderError(str(exc)) from exc
    return data, tuple(findings)


def _enforce_row_cap(compiled: _Compiled, data: QueryResult, run: _Run) -> None:
    max_rows = run.config.execution.max_rows
    if max_rows is not None and len(data) > max_rows:
        raise RenderError(
            f"{compiled.rel_path} returned more than {max_rows} rows. "
            "Aggregate the query or raise execution.max_rows; glyf will not "
            "draw a chart from part of a result."
        )


def _order(compiled: _Compiled, data: QueryResult, run: _Run) -> QueryResult:
    """Order the rows if the query did not, and say so where it shows.

    Before anything that draws or publishes these rows: a chart whose query
    chose no order is rendered from whatever order the warehouse happened to
    return, which is not the same order next build.
    """
    data, row_order = order_rows(compiled.chart, data)
    if row_order.applied:
        if is_order_sensitive(compiled.chart):
            run.warnings.append(row_order.describe(compiled.rel_path))
    elif row_order.reason:
        run.warnings.append(row_order.describe(compiled.rel_path))
    return data


def _downsample(
    compiled: _Compiled, data: QueryResult, run: _Run
) -> tuple[QueryResult, Downsampling]:
    """The rows to draw, and what downsampling did or could not do."""
    chart, render_config = compiled.chart, run.render_config
    plan = plan_downsampling(
        chart,
        data,
        enabled=render_config.downsample,
        over_rows=render_config.downsample_over,
        width=chart.width or render_config.default_width,
    )
    if not plan.applied:
        if plan.reason:
            # Downsampling was asked for and could not be given. Saying so
            # matters more than the successful case: the build is about to draw
            # every mark, which is what the user turned this on to avoid.
            run.warnings.append(plan.describe(compiled.rel_path))
        return data, plan

    render_data, marks = downsample_m4(chart, data, plan.bins)
    if marks >= len(data):
        # Every row was already the extreme of its own bin, so this kept all
        # of them. Reporting a downsample that removed nothing would be noise,
        # and the record would claim a reduction that did not happen.
        return data, replace(plan, applied=False, marks=len(data))

    plan = replace(plan, marks=marks)
    run.warnings.append(plan.describe(compiled.rel_path))
    return render_data, plan


def _enforce_mark_budget(compiled: _Compiled, render_data: QueryResult, run: _Run) -> None:
    """Stop before the renderer would crash rather than fail.

    Not a preference: past this the renderer stops failing and starts aborting.
    vl-convert inlines every mark into a V8 heap, and when that heap runs out it
    kills the process -- exit 133 and a C stack trace, no traceback, and in a
    multi-chart build no clue which chart did it. glyf has to stop while it can
    still say.
    """
    max_marks = run.render_config.max_marks
    if max_marks is not None and len(render_data) > max_marks:
        raise RenderError(
            f"{compiled.rel_path} would draw {len(render_data)} marks, more than the "
            f"{max_marks} glyf will render. The renderer holds "
            "every mark in memory at once and the whole build dies when it "
            "runs out, so glyf stops first. Aggregate the query, or raise "
            "render.max_marks if this machine can take it."
        )


def _enforce_table_budget(compiled: _Compiled, data: QueryResult, run: _Run) -> None:
    """The most rows a table may list.

    A picture summarises its rows; a table is read a row at a time, and past a
    page or two it stops being a chart on a dashboard and becomes a data export
    that happens to be HTML. The bound is the table's `max_marks`: a normal
    build error naming the chart, not a silent truncation.
    """
    max_rows = run.render_config.max_rows
    if max_rows is not None and len(data) > max_rows:
        raise RenderError(
            f"{compiled.rel_path} would list {len(data)} rows, more than the "
            f"{max_rows} glyf will put in a table. A table is read a row at a "
            "time, and glyf will not show part of a result. Aggregate the query, "
            "add a LIMIT, or raise render.max_rows."
        )


def _scan_values(
    compiled: _Compiled,
    data: QueryResult,
    findings: tuple[PiiColumn, ...],
    run: _Run,
) -> tuple[dict[str, object], ...]:
    """Warn about values that read like PII in columns nobody classified.

    The safety net behind the classification: it reads values, so it needs
    rows, which is why validate mode cannot run it. It warns rather than
    redacts -- a fuzzy match that silently rewrote a column would be a wrong
    chart nobody knew about.
    """
    privacy = run.config.privacy
    if not privacy.scan:
        return ()
    suspects = scan_for_pii(data, skip=tuple(finding.name for finding in findings))
    for suspect in suspects:
        message = (
            f"{compiled.rel_path} {suspect.describe()} but is not classified as "
            "PII. Tag it in schema.yml or list it in privacy.pii_columns"
        )
        if privacy.strict:
            raise RenderError(f"{message} (privacy.strict).")
        run.warnings.append(message)
    return tuple(
        {
            "column": suspect.column,
            "kind": suspect.kind,
            "matched": suspect.matched,
            "sampled": suspect.sampled,
        }
        for suspect in suspects
    )


def _write_artifacts(
    compiled: _Compiled, data: QueryResult, render_data: QueryResult, run: _Run
) -> None:
    """Write the rows, draw the chart, and write its metadata."""
    chart, artifacts, root = compiled.chart, compiled.artifacts, run.scan.root
    write_chart_data(root, chart, artifacts, data)

    if not chart.has_picture:
        # The chart may have been drawn by an earlier build, before its file
        # said `DRAW table`; a stale PNG here would be exported as if current.
        _discard(artifacts.png, artifacts.svg, artifacts.vega_json)
        try:
            if chart.is_table:
                _discard(artifacts.kpi_html)
                render_table(chart, data, artifacts.table_html)
            else:
                _discard(artifacts.table_html)
                render_kpi(chart, data, artifacts.kpi_html)
        except ChartRenderError as exc:
            raise RenderError(
                f"{compiled.rel_path} {chart.draw_type} rendering failed: {exc}"
            ) from exc
        write_chart_metadata(
            root,
            chart,
            artifacts,
            columns=table_columns(chart, data.columns),
            lineage=compiled.lineage,
        )
        return
    _discard(artifacts.table_html, artifacts.kpi_html)

    if run.exclude_row_data:
        # An SVG carries every row in its per-mark accessibility labels and a
        # Vega spec carries them outright, so neither may exist. Clear anything
        # a previous build left behind, or export would ship it.
        _discard(artifacts.svg, artifacts.vega_json)
        if chart.is_interactive:
            run.warnings.append(
                f"{compiled.rel_path} renders as a static PNG: its INTERACT clause "
                "needs a Vega spec, which carries the rows "
                "(export.row_data: exclude)"
            )

    # `.data.json` above keeps every column for the local build; what the chart
    # is drawn from -- and so what its Vega spec inlines -- may not.
    chart_data = (
        prune_to_encoded_columns(chart, render_data)
        if run.prune_row_data
        else render_data
    )
    try:
        render_chart(
            chart,
            chart_data,
            artifacts.png,
            artifacts.svg,
            run.render_config,
            vega_json_path=None if run.exclude_row_data else artifacts.vega_json,
        )
    except ChartRenderError as exc:
        raise RenderError(f"{compiled.rel_path} chart rendering failed: {exc}") from exc
    if run.prune_row_data and artifacts.svg.exists():
        strip_svg_row_values(artifacts.svg, chart)

    write_chart_metadata(root, chart, artifacts, lineage=compiled.lineage)


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
