from dataclasses import dataclass
from pathlib import Path

from glyf.config import GlyfConfig
from glyf.dashboard.artifacts import (
    ChartArtifact,
    ChartArtifactError,
    load_chart_artifact,
)
from glyf.dashboard.loader import Dashboard, load_dashboard
from glyf.dashboard.macros import (
    DashboardMacroError,
    DashboardMacroRegistry,
    resolve_dashboard_components,
)
from glyf.dashboard.renderer import DashboardBuildMeta, DashboardRenderer
from glyf.output.paths import artifact_paths
from glyf.project.scanner import ProjectScan, scan_project


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
    config: GlyfConfig | None = None,
) -> DashboardGenerationResult:
    config = config or GlyfConfig()
    scan = scan_project(project, config)
    paths = artifact_paths(scan.root, config)
    paths.dashboards_dir.mkdir(parents=True, exist_ok=True)
    renderer = DashboardRenderer()
    assets = renderer.prepare_assets(paths.root)
    try:
        macro_registry = DashboardMacroRegistry.from_project(scan.dashboards_dir)
    except DashboardMacroError as exc:
        raise DashboardGenerationError(str(exc)) from exc
    build_meta = DashboardBuildMeta.now()

    dashboards: list[GeneratedDashboard] = []
    for dashboard_path in scan.dashboard_files:
        try:
            dashboard = load_dashboard(dashboard_path)
        except ValueError as exc:
            rel_path = dashboard_path.relative_to(scan.root).as_posix()
            raise DashboardGenerationError(f"{rel_path}: {exc}") from exc
        try:
            dashboard = resolve_dashboard_components(dashboard, macro_registry)
        except DashboardMacroError as exc:
            rel_path = dashboard_path.relative_to(scan.root).as_posix()
            raise DashboardGenerationError(f"{rel_path}: {exc}") from exc

        chart_artifacts = {}
        for chart_name in dashboard.chart_names:
            try:
                chart_artifacts[chart_name] = load_chart_artifact(
                    scan.root,
                    chart_name,
                    config,
                )
            except ChartArtifactError as exc:
                rel_path = dashboard_path.relative_to(scan.root).as_posix()
                raise DashboardGenerationError(f"{rel_path}: {exc}") from exc

        ordered_chart_artifacts = tuple(
            chart_artifacts[chart_name] for chart_name in dashboard.chart_names
        )

        output_path = paths.dashboards_dir / f"{dashboard.name}.html"
        output_path.write_text(
            renderer.render_dashboard(
                dashboard,
                chart_artifacts,
                ordered_chart_artifacts,
                config,
                assets,
                build_meta,
            ).html,
            encoding="utf-8",
        )
        dashboards.append(
            GeneratedDashboard(
                dashboard=dashboard,
                path=output_path,
                charts=ordered_chart_artifacts,
            )
        )

    index_path = paths.root / "index.html"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        renderer.render_index(tuple(dashboards), assets),
        encoding="utf-8",
    )

    return DashboardGenerationResult(
        scan=scan,
        dashboards=tuple(dashboards),
        index_path=index_path,
    )
