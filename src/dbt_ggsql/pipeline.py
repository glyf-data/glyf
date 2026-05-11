from dataclasses import dataclass
from pathlib import Path

from dbt_ggsql.ggsql.models import GgsqlChart
from dbt_ggsql.ggsql.parser import GgsqlParseError, parse_ggsql_file
from dbt_ggsql.manifest.loader import ManifestError, load_manifest
from dbt_ggsql.manifest.resolver import resolve_refs
from dbt_ggsql.output.writer import ChartArtifacts, write_chart_artifacts
from dbt_ggsql.project.scanner import ProjectScan, scan_project


@dataclass(frozen=True)
class RenderedChart:
    chart: GgsqlChart
    compiled_sql: str
    artifacts: ChartArtifacts


@dataclass(frozen=True)
class RenderResult:
    scan: ProjectScan
    charts: tuple[RenderedChart, ...]


class RenderError(ValueError):
    """Raised when chart artifacts cannot be generated."""


def render_project(project: Path) -> RenderResult:
    scan = scan_project(project)
    if scan.manifest_path is None:
        raise RenderError("Missing target/manifest.json")

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
        if resolution.missing_refs:
            missing = ", ".join(f"'{ref}'" for ref in resolution.missing_refs)
            rel_path = path.relative_to(scan.root).as_posix()
            raise RenderError(f"{rel_path} references unknown model {missing}")

        artifacts = write_chart_artifacts(scan.root, chart, resolution.sql)
        rendered.append(
            RenderedChart(
                chart=chart,
                compiled_sql=resolution.sql,
                artifacts=artifacts,
            )
        )

    return RenderResult(scan=scan, charts=tuple(rendered))
