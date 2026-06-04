import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from glyf.config import GlyfConfig
from glyf.dashboard.assets import copy_dashboard_assets
from glyf.output.paths import artifact_paths
from glyf.project.scanner import ProjectScan, scan_project


class ExportError(ValueError):
    """Raised when the static site cannot be exported."""


@dataclass(frozen=True)
class ExportResult:
    scan: ProjectScan
    site_dir: Path
    zip_path: Path | None


def export_site(
    project: Path,
    *,
    clean: bool = False,
    zip_site: bool = False,
    config: GlyfConfig | None = None,
) -> ExportResult:
    config = config or GlyfConfig()
    scan = scan_project(project, config)
    paths = artifact_paths(scan.root, config)

    if clean and paths.site_dir.exists():
        shutil.rmtree(paths.site_dir)

    _ensure_generated_outputs(paths.root)
    paths.site_dir.mkdir(parents=True, exist_ok=True)

    _copy_file(paths.root / "index.html", paths.site_dir / "index.html")
    _copy_tree(paths.dashboards_dir, paths.site_dir / "dashboards")
    _copy_chart_artifacts(paths.charts_dir, paths.site_dir / "charts")
    _copy_tree(paths.compiled_dir, paths.site_dir / "compiled")
    copy_dashboard_assets(paths.root, paths.site_dir)

    zip_path = None
    if zip_site:
        zip_path = paths.site_zip
        _write_zip(paths.site_dir, zip_path)

    return ExportResult(scan=scan, site_dir=paths.site_dir, zip_path=zip_path)


def _ensure_generated_outputs(root: Path) -> None:
    required = [
        root / "index.html",
        root / "dashboards",
        root / "charts",
        root / "compiled",
        root / "assets",
    ]
    missing = [path.relative_to(root).as_posix() for path in required if not path.exists()]
    if missing:
        joined = ", ".join(missing)
        raise ExportError(
            f"Missing generated outputs: {joined}. Run glyf render and "
            "glyf dashboard before export."
        )


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, dirs_exist_ok=True)


def _copy_chart_artifacts(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if (
            path.suffixes[-2:] == [".data", ".json"]
            or path.name.endswith(".data.json")
            or path.name.endswith(".vega.json")
        ):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

    for stale in destination.rglob("*.data.json"):
        stale.unlink()
    for stale in destination.rglob("*.vega.json"):
        stale.unlink()


def _write_zip(site_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(site_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(site_dir).as_posix())
