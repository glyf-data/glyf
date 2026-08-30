import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from glyf.bundle import write_bundle_manifest
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
    exclude_row_data = config.export.excludes_row_data
    _copy_chart_artifacts(
        paths.charts_dir,
        paths.site_dir / "charts",
        exclude_row_data=exclude_row_data,
    )
    if not exclude_row_data:
        # Compiled SQL names the warehouse tables the dashboard was built from.
        _copy_tree(paths.compiled_dir, paths.site_dir / "compiled")
    copy_dashboard_assets(paths.root, paths.site_dir)
    write_bundle_manifest(
        scan.root,
        config=config,
        public=True,
        output_path=paths.site_bundle_manifest,
    )

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


# What may be published from the charts directory. An allowlist, so an artifact
# type added later is withheld until someone decides it is publishable --
# the previous denylist named `*.data.json` and `*.vega.json` and copied
# everything else, and those files no longer live here anyway.
PUBLISHABLE_CHART_SUFFIXES = frozenset({".png", ".svg", ".json"})

# Suffixes that carry the rows themselves rather than a picture of them.
ROW_DATA_SUFFIXES = (".data.json", ".vega.json")


def _copy_chart_artifacts(
    source: Path,
    destination: Path,
    *,
    exclude_row_data: bool = False,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if any(path.name.endswith(suffix) for suffix in ROW_DATA_SUFFIXES):
            continue
        if path.suffix not in PUBLISHABLE_CHART_SUFFIXES:
            continue
        if exclude_row_data and path.suffix == ".svg":
            # Every mark in an SVG carries its row in an accessibility label.
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            _copy_public_chart_metadata(
                path,
                target,
                exclude_row_data=exclude_row_data,
            )
        else:
            shutil.copy2(path, target)

    for suffix in ROW_DATA_SUFFIXES:
        for stale in destination.rglob(f"*{suffix}"):
            stale.unlink()
    if exclude_row_data:
        for stale in destination.rglob("*.svg"):
            stale.unlink()


def _copy_public_chart_metadata(
    source: Path,
    destination: Path,
    *,
    exclude_row_data: bool = False,
) -> None:
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        shutil.copy2(source, destination)
        return
    if not isinstance(payload, dict):
        shutil.copy2(source, destination)
        return

    payload.pop("data_json_path", None)
    payload.pop("vega_json_path", None)
    if exclude_row_data:
        # Neither is published, so the manifest must not point at them.
        payload.pop("svg_path", None)
        payload.pop("compiled_sql_path", None)
        payload.pop("interactions", None)
    _rewrite_public_chart_path(payload, "metadata_path", "charts")
    _rewrite_public_chart_path(payload, "png_path", "charts")
    _rewrite_public_chart_path(payload, "svg_path", "charts")
    _rewrite_public_chart_path(payload, "compiled_sql_path", "compiled")
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _rewrite_public_chart_path(
    payload: dict[str, object],
    key: str,
    public_dir: str,
) -> None:
    value = payload.get(key)
    if isinstance(value, str):
        payload[key] = f"{public_dir}/{Path(value).name}"


def _write_zip(site_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(site_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(site_dir).as_posix())
