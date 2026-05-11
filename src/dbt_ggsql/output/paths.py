from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactPaths:
    root: Path
    compiled_dir: Path
    charts_dir: Path
    dashboards_dir: Path
    site_dir: Path
    site_zip: Path


def artifact_paths(project_root: Path) -> ArtifactPaths:
    root = project_root / "target" / "ggsql"
    return ArtifactPaths(
        root=root,
        compiled_dir=root / "compiled",
        charts_dir=root / "charts",
        dashboards_dir=root / "dashboards",
        site_dir=root / "site",
        site_zip=root / "dbt-ggsql-site.zip",
    )
