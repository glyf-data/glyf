from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from dbt_charts.config import DbtChartsConfig
from dbt_charts.dashboard.artifacts import (
    ChartArtifact,
    ChartArtifactError,
    load_chart_artifact,
)
from dbt_charts.dashboard.loader import Dashboard, load_dashboard
from dbt_charts.output.paths import artifact_paths
from dbt_charts.project.scanner import ProjectScan, scan_project


class DashboardGenerationError(ValueError):
    """Raised when static dashboard HTML cannot be generated."""


@dataclass(frozen=True)
class GeneratedDashboard:
    dashboard: Dashboard
    path: Path
    charts: tuple[ChartArtifact, ...]


@dataclass(frozen=True)
class DashboardGenerationResult:
    scan: ProjectScan
    dashboards: tuple[GeneratedDashboard, ...]
    index_path: Path


def generate_dashboards(
    project: Path,
    config: DbtChartsConfig | None = None,
) -> DashboardGenerationResult:
    config = config or DbtChartsConfig()
    scan = scan_project(project, config)
    paths = artifact_paths(scan.root, config)
    paths.dashboards_dir.mkdir(parents=True, exist_ok=True)

    dashboards: list[GeneratedDashboard] = []
    for dashboard_path in scan.dashboard_files:
        try:
            dashboard = load_dashboard(dashboard_path)
        except ValueError as exc:
            rel_path = dashboard_path.relative_to(scan.root).as_posix()
            raise DashboardGenerationError(f"{rel_path}: {exc}") from exc

        chart_artifacts = []
        for chart_name in dashboard.charts:
            try:
                chart_artifacts.append(load_chart_artifact(scan.root, chart_name, config))
            except ChartArtifactError as exc:
                rel_path = dashboard_path.relative_to(scan.root).as_posix()
                raise DashboardGenerationError(f"{rel_path}: {exc}") from exc

        output_path = paths.dashboards_dir / f"{dashboard.name}.html"
        output_path.write_text(
            _render_dashboard(dashboard, tuple(chart_artifacts), config),
            encoding="utf-8",
        )
        dashboards.append(
            GeneratedDashboard(
                dashboard=dashboard,
                path=output_path,
                charts=tuple(chart_artifacts),
            )
        )

    index_path = paths.root / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(_render_index(tuple(dashboards)), encoding="utf-8")

    return DashboardGenerationResult(
        scan=scan,
        dashboards=tuple(dashboards),
        index_path=index_path,
    )


def _environment() -> Environment:
    templates_dir = Path(__file__).parent / "templates"
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(("html", "xml")),
    )


def _render_dashboard(
    dashboard: Dashboard,
    charts: tuple[ChartArtifact, ...],
    config: DbtChartsConfig,
) -> str:
    template = _environment().get_template("dashboard.html.j2")
    return template.render(
        dashboard=dashboard,
        charts=charts,
        dashboard_config=config.dashboard,
    )


def _render_index(dashboards: tuple[GeneratedDashboard, ...]) -> str:
    template = _environment().get_template("index.html.j2")
    return template.render(dashboards=dashboards)
