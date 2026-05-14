from dataclasses import dataclass
from pathlib import Path

from dbt_charts.config import DbtChartsConfig, resolve_project_path


@dataclass(frozen=True)
class ArtifactPaths:
    root: Path
    compiled_dir: Path
    charts_dir: Path
    dashboards_dir: Path
    site_dir: Path
    site_zip: Path


def artifact_paths(project_root: Path, config: DbtChartsConfig | None = None) -> ArtifactPaths:
    config = config or DbtChartsConfig()
    root = resolve_project_path(project_root, config.output_path)
    return ArtifactPaths(
        root=root,
        compiled_dir=resolve_project_path(project_root, config.compiled_path),
        charts_dir=resolve_project_path(project_root, config.charts_path),
        dashboards_dir=resolve_project_path(project_root, config.dashboards_output_path),
        site_dir=resolve_project_path(project_root, config.site_path),
        site_zip=root / "dbt-charts-site.zip",
    )
