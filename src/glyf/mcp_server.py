"""A glyf project, exposed to an agent over the Model Context Protocol.

Six tools, all built on functions the CLI already uses, so an agent sees
what a person sees: the charts and dashboards, one chart's spec, the charts a
model or column change reaches, the project's validation verdict, and what
moved between two builds.

The server reads files and, on request, dry-runs SQL with `LIMIT 0`. It never
runs a build and never fetches rows: an agent asking a warehouse for data
through a tool is exactly the exposure glyf's data-protection story exists to
prevent, so that stays with the person and the pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from glyf.config import GlyfConfig, load_config, resolve_project_path
from glyf.dashboard.loader import load_dashboard
from glyf.diff import DiffError, compare_builds
from glyf.diff.report import as_document as diff_document
from glyf.execution.dialect import sql_dialect
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql_file
from glyf.impact import ImpactError, compute_impact
from glyf.manifest.loader import ManifestError, load_manifest
from glyf.manifest.resolver import resolve_refs
from glyf.project.scanner import scan_project
from glyf.validation import validate_project

INSTRUCTIONS = """\
This server exposes one glyf project: a dbt project with chart files
(visualisations/*.ggsql: SQL, then VISUALISE, DRAW, LABEL, CONFIG, INTERACT)
and dashboard YAML (dashboards/*.yml). Charts reference dbt models with
{{ ref('model') }} and sources with {{ source('name', 'table') }}.

Start with list_charts or list_dashboards. Before proposing a change to a dbt
model or one of its columns, call impact to see which charts and dashboards it
reaches, and say so in the change. After editing a chart file, call validate
with execute=true to run its SQL with LIMIT 0 and check the columns it binds.
diff compares the current build with an earlier one.

Nothing here runs a build or fetches rows; that is for the person and the
pipeline. Chart file contents come from get_chart.
"""


class McpUnavailable(RuntimeError):
    """Raised when the MCP SDK is not installed."""


def build_server(project: Path, config_path: Path | None = None) -> Any:
    """The MCP server for one project, ready to `run()`.

    Imports the SDK here so that `glyf` without the `mcp` extra still imports
    and runs; only this command needs it.
    """
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as exc:
        raise McpUnavailable(
            "the MCP server needs the mcp package: install glyf-core[mcp]"
        ) from exc

    project = project.resolve()
    server = MCPServer(name="glyf", instructions=INSTRUCTIONS)

    def config() -> GlyfConfig:
        return load_config(project, config_path)

    @server.tool(description="Every chart in the project: name, file, type, title, the dbt models and sources it reads, and the dashboards it is on.")
    def list_charts() -> dict[str, Any]:
        return {"charts": _charts(project, config())}

    @server.tool(description="Every dashboard in the project: name, title, description, tags and the charts it shows, in order.")
    def list_dashboards() -> dict[str, Any]:
        return {"dashboards": _dashboards(project, config())}

    @server.tool(description="One chart's file and its parsed spec: the SQL, the VISUALISE mappings, the DRAW type, labels, config, interactions, and the models and sources it reads.")
    def get_chart(name: str) -> dict[str, Any]:
        return _chart(project, config(), name)

    @server.tool(description="The charts and dashboards downstream of a dbt model (fct_orders), a source (raw.orders) or a column of either (fct_orders.revenue). Model and source answers are exact; a column answer says on each line whether the chart reads it or may read it.")
    def impact(target: str) -> dict[str, Any]:
        try:
            return compute_impact(project, config(), target).as_document()
        except ImpactError as exc:
            return {"error": str(exc)}

    @server.tool(description="Validate the project's files and manifest refs. With execute=true, also run each chart's SQL with LIMIT 0 on the configured backend and check the columns it returns; no rows are fetched.")
    def validate(execute: bool = False) -> dict[str, Any]:
        result = validate_project(project, config(), execute=execute)
        return {
            "ok": result.ok,
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "charts": result.chart_count,
            "dashboards": result.dashboard_count,
            "executed": result.executed,
            "checks": list(result.checks),
        }

    @server.tool(description="Compare the project's current build (target/glyf) with an earlier build directory and report which charts changed, how much, and why. Both builds must exist already; this runs no build.")
    def diff(baseline: str, threshold: float = 0.0) -> dict[str, Any]:
        cfg = config()
        current = resolve_project_path(project, cfg.output_path)
        try:
            report = compare_builds(
                Path(baseline), current, threshold=threshold, render_config=cfg.render
            )
        except DiffError as exc:
            return {"error": str(exc)}
        return diff_document(report)

    return server


def _charts(project: Path, config: GlyfConfig) -> list[dict[str, Any]]:
    scan = scan_project(project, config)
    manifest = _manifest(scan)
    on_dashboards = _dashboards_by_chart(scan)
    dialect = sql_dialect(scan.root, config.execution)
    charts = []
    for path in scan.ggsql_files:
        rel = path.relative_to(scan.root).as_posix()
        try:
            chart = parse_ggsql_file(path, dialect=dialect)
        except GgsqlParseError as exc:
            charts.append({"name": path.stem, "path": rel, "error": str(exc)})
            continue
        entry: dict[str, Any] = {
            "name": chart.name,
            "path": rel,
            "type": chart.draw_type,
            "title": chart.title,
            "dashboards": on_dashboards.get(chart.name, []),
        }
        if manifest is not None:
            resolution = resolve_refs(chart.sql, manifest)
            entry["models"] = list(dict.fromkeys(resolution.refs))
            entry["sources"] = [f"{s}.{t}" for s, t in dict.fromkeys(resolution.sources)]
        charts.append(entry)
    return charts


def _chart(project: Path, config: GlyfConfig, name: str) -> dict[str, Any]:
    scan = scan_project(project, config)
    path = next((p for p in scan.ggsql_files if p.stem == name), None)
    if path is None:
        known = ", ".join(p.stem for p in scan.ggsql_files) or "none"
        return {"error": f"no chart named '{name}'; the project has: {known}"}
    rel = path.relative_to(scan.root).as_posix()
    text = path.read_text(encoding="utf-8")
    try:
        chart = parse_ggsql_file(path, dialect=sql_dialect(scan.root, config.execution))
    except GgsqlParseError as exc:
        return {"name": name, "path": rel, "text": text, "error": str(exc)}
    entry: dict[str, Any] = {
        "name": chart.name,
        "path": rel,
        "text": text,
        "sql": chart.sql,
        "type": chart.draw_type,
        "visualise": [{"field": m.field, "role": m.role} for m in chart.visualise],
        "labels": dict(chart.labels),
        "config": dict(chart.config),
        "interactions": list(chart.interactions),
        "sql_columns": list(chart.sql_columns),
        "sql_selects_star": chart.sql_selects_star,
        "sql_warning": chart.sql_warning,
        "dashboards": _dashboards_by_chart(scan).get(chart.name, []),
    }
    manifest = _manifest(scan)
    if manifest is not None:
        resolution = resolve_refs(chart.sql, manifest)
        entry["models"] = list(dict.fromkeys(resolution.refs))
        entry["sources"] = [f"{s}.{t}" for s, t in dict.fromkeys(resolution.sources)]
        entry["missing_models"] = list(resolution.missing_refs)
        entry["compiled_sql"] = resolution.sql
    return entry


def _dashboards(project: Path, config: GlyfConfig) -> list[dict[str, Any]]:
    scan = scan_project(project, config)
    dashboards = []
    for path in scan.dashboard_files:
        rel = path.relative_to(scan.root).as_posix()
        try:
            dashboard = load_dashboard(path)
        except ValueError as exc:
            dashboards.append({"name": path.stem, "path": rel, "error": str(exc)})
            continue
        dashboards.append(
            {
                "name": dashboard.name,
                "path": rel,
                "title": dashboard.title,
                "description": dashboard.description,
                "tags": list(dashboard.tags),
                "charts": list(dashboard.chart_names),
            }
        )
    return dashboards


def _dashboards_by_chart(scan) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for path in scan.dashboard_files:
        try:
            dashboard = load_dashboard(path)
        except ValueError:
            continue
        for chart in dashboard.chart_names:
            result.setdefault(chart, []).append(dashboard.name)
    return result


def _manifest(scan):
    if scan.manifest_path is None:
        return None
    try:
        return load_manifest(scan.manifest_path)
    except ManifestError:
        return None
