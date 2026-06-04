from dataclasses import dataclass
from pathlib import Path

from glyf.config import GlyfConfig, resolve_project_path


@dataclass(frozen=True)
class ArtifactPaths:
    root: Path
    bundle_manifest: Path
    compiled_dir: Path
    charts_dir: Path
    data_dir: Path
    normalized_data_dir: Path
    vega_data_dir: Path
    dashboards_dir: Path
    site_dir: Path
    site_bundle_manifest: Path
    site_zip: Path


def artifact_paths(project_root: Path, config: GlyfConfig | None = None) -> ArtifactPaths:
    config = config or GlyfConfig()
    root = resolve_project_path(project_root, config.output_path)
    return ArtifactPaths(
        root=root,
        bundle_manifest=root / "bundle.json",
        compiled_dir=resolve_project_path(project_root, config.compiled_path),
        charts_dir=resolve_project_path(project_root, config.charts_path),
        data_dir=root / "data",
        normalized_data_dir=root / "data" / "normalized",
        vega_data_dir=root / "data" / "vega",
        dashboards_dir=resolve_project_path(project_root, config.dashboards_output_path),
        site_dir=resolve_project_path(project_root, config.site_path),
        site_bundle_manifest=resolve_project_path(project_root, config.site_path)
        / "bundle.json",
        site_zip=root / "glyf-site.zip",
    )
