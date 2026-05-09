from dataclasses import dataclass
from pathlib import Path

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


def scan_project(project: Path) -> ProjectScan:
    root = project.expanduser().resolve()
    if not root.exists():
        raise ValueError(f"Project path does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Project path is not a directory: {root}")

    files = _iter_project_files(root)
    ggsql_files = tuple(path for path in files if path.suffix == ".ggsql")
    dashboard_files = tuple(
        path
        for path in files
        if path.suffix.lower() in {".yml", ".yaml"}
            and "dashboards" in path.relative_to(root).parts
    )
    manifest_path = root / "target" / "manifest.json"

    return ProjectScan(
        root=root,
        ggsql_files=ggsql_files,
        dashboard_files=dashboard_files,
        manifest_path=manifest_path if manifest_path.exists() else None,
    )
