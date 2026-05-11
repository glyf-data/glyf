from dataclasses import dataclass
from pathlib import Path

from dbt_ggsql.config import DbtGgsqlConfig, resolve_project_path

IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}


@dataclass(frozen=True)
class ProjectScan:
    root: Path
    ggsql_files: tuple[Path, ...]
    dashboard_files: tuple[Path, ...]
    manifest_path: Path | None
    dbt_project_path: Path | None
    visualisations_dir: Path | None
    dashboards_dir: Path | None


def _iter_project_files(root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for child in sorted(root.iterdir()):
        if child.is_dir():
            if child.name in IGNORED_DIRS:
                continue
            files.extend(_iter_project_files(child))
        elif child.is_file():
            files.append(child)
    return tuple(files)


def scan_project(project: Path, config: DbtGgsqlConfig | None = None) -> ProjectScan:
    config = config or DbtGgsqlConfig()
    root = project.expanduser().resolve()
    if not root.exists():
        raise ValueError(f"Project path does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Project path is not a directory: {root}")

    files = _iter_project_files(root)
    visualisations_dir = resolve_project_path(root, config.visualisations_path)
    dashboards_dir = resolve_project_path(root, config.dashboards_path)
    ggsql_files = tuple(
        path
        for path in files
        if path.suffix == ".ggsql"
        and visualisations_dir in (path.parent, *path.parents)
    )
    dashboard_files = tuple(
        path
        for path in files
        if path.suffix.lower() in {".yml", ".yaml"}
        and dashboards_dir in (path.parent, *path.parents)
    )
    manifest_path = root / "target" / "manifest.json"
    dbt_project_path = root / "dbt_project.yml"

    return ProjectScan(
        root=root,
        ggsql_files=ggsql_files,
        dashboard_files=dashboard_files,
        manifest_path=manifest_path if manifest_path.exists() else None,
        dbt_project_path=dbt_project_path if dbt_project_path.exists() else None,
        visualisations_dir=visualisations_dir if visualisations_dir.is_dir() else None,
        dashboards_dir=dashboards_dir if dashboards_dir.is_dir() else None,
    )
