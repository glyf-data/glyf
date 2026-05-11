from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactPaths:
    root: Path
    compiled_dir: Path
    charts_dir: Path
    dashboards_dir: Path


def artifact_paths(project_root: Path) -> ArtifactPaths:
    root = project_root / "target" / "ggsql"
    return ArtifactPaths(
        root=root,
        compiled_dir=root / "compiled",
        charts_dir=root / "charts",
        dashboards_dir=root / "dashboards",
    )
