from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from glyf import __version__
from glyf.config import GlyfConfig
from glyf.dashboard.loader import Dashboard, DashboardFilter, load_dashboard
from glyf.dashboard.renderer import DashboardBuildMeta
from glyf.output.paths import artifact_paths
from glyf.project.scanner import scan_project


BUNDLE_VERSION = "1"


def write_bundle_manifest(
    project: Path,
    *,
    config: GlyfConfig | None = None,
    public: bool = False,
    generated_at: str | None = None,
    dashboards: Sequence[object] | None = None,
    output_path: Path | None = None,
) -> Path:
    config = config or GlyfConfig()
    scan = scan_project(project, config)
    paths = artifact_paths(scan.root, config)
    target_path = output_path or (
        paths.site_bundle_manifest if public else paths.bundle_manifest
    )
    inherited = _read_existing_bundle(paths.bundle_manifest)
    payload = {
        "bundle_version": BUNDLE_VERSION,
        "glyf_version": __version__,
        "project": scan.root.name,
        "mode": "public_site" if public else "local_artifact",
        "generated_at": generated_at
        or inherited.get("generated_at")
        or _infer_generated_at(paths.root),
        "paths": _paths_payload(public),
        "security": _security_payload(public),
        "charts": _charts_payload(scan.root, config, public=public),
        "dashboards": _dashboards_payload(scan.root, config, dashboards),
    }
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target_path


def _read_existing_bundle(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def _infer_generated_at(root: Path) -> str | None:
    """Fall back to the index page's mtime when no caller supplied a timestamp.

    `glyf export` writes the public bundle without a timestamp of its own and
    normally inherits the one `glyf dashboard` recorded in the local bundle.
    When the local bundle is missing, the index page is the youngest artifact
    the build wrote, so its mtime is the closest available build time.
    """
    index_path = root / "index.html"
    if not index_path.exists():
        return None
    mtime = datetime.fromtimestamp(index_path.stat().st_mtime, tz=timezone.utc)
    return DashboardBuildMeta.from_datetime(mtime).generated_at_iso


def _paths_payload(public: bool) -> dict[str, object]:
    if public:
        return {
            "index": "index.html",
            "dashboards": "dashboards/",
            "charts": "charts/",
            "assets": "assets/",
            "compiled": "compiled/",
        }
    return {
        "index": "index.html",
        "dashboards": "dashboards/",
        "charts": "charts/",
        "assets": "assets/",
        "compiled": "compiled/",
        "data": {
            "normalized": "data/normalized/",
            "vega": "data/vega/",
        },
    }


def _security_payload(public: bool) -> dict[str, object]:
    return {
        "public_export": public,
        "browser_visible_data": (
            "Public exports include rendered dashboard HTML and public chart artifacts. "
            "Embedded app packages may intentionally expose Vega specs to the browser."
        ),
        "internal_artifacts_included": not public,
        "internal_artifacts": [] if public else ["data/normalized", "data/vega"],
    }


def _charts_payload(
    project_root: Path,
    config: GlyfConfig,
    *,
    public: bool,
) -> dict[str, object]:
    paths = artifact_paths(project_root, config)
    charts: dict[str, object] = {}
    for metadata_path in sorted(paths.charts_dir.glob("*.json")):
        if metadata_path.name.endswith(".data.json") or metadata_path.name.endswith(
            ".vega.json"
        ):
            continue
        try:
            raw = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict) or not isinstance(raw.get("name"), str):
            continue
        charts[raw["name"]] = _chart_payload(
            project_root,
            config,
            raw,
            public=public,
        )
    return charts


def _chart_payload(
    project_root: Path,
    config: GlyfConfig,
    raw: dict[str, object],
    *,
    public: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": raw.get("title"),
        "chart_type": raw.get("chart_type"),
        "fields": {
            "x": raw.get("x"),
            "y": raw.get("y"),
        },
        "artifacts": {
            "metadata": _artifact_path(
                project_root,
                config,
                raw.get("metadata_path"),
                public,
            ),
            "png": _artifact_path(project_root, config, raw.get("png_path"), public),
            "svg": _artifact_path(project_root, config, raw.get("svg_path"), public),
            "compiled_sql": _artifact_path(
                project_root,
                config,
                raw.get("compiled_sql_path"),
                public,
            ),
        },
    }
    interactions = raw.get("interactions")
    if isinstance(interactions, list):
        payload["interactions"] = interactions
    if not public:
        payload["artifacts"]["data"] = _artifact_path(
            project_root,
            config,
            raw.get("data_json_path"),
            public,
        )
        payload["artifacts"]["vega"] = _artifact_path(
            project_root,
            config,
            raw.get("vega_json_path"),
            public,
        )
    else:
        payload["artifacts"]["data"] = None
        payload["artifacts"]["vega"] = None
    return payload


def _artifact_path(
    project_root: Path,
    config: GlyfConfig,
    value: object,
    public: bool,
) -> str | None:
    if not isinstance(value, str):
        return None
    if not public:
        return _strip_output_prefix(value)

    path = project_root / value
    paths = artifact_paths(project_root, config)
    if path.is_relative_to(paths.charts_dir):
        return f"charts/{path.relative_to(paths.charts_dir).as_posix()}"
    if path.is_relative_to(paths.compiled_dir):
        return f"compiled/{path.relative_to(paths.compiled_dir).as_posix()}"
    if path.is_relative_to(paths.dashboards_dir):
        return f"dashboards/{path.relative_to(paths.dashboards_dir).as_posix()}"
    return None


def _strip_output_prefix(value: str) -> str:
    prefix = "target/glyf/"
    if value.startswith(prefix):
        return value[len(prefix) :]
    return value


def _dashboards_payload(
    project_root: Path,
    config: GlyfConfig,
    generated_dashboards: Sequence[object] | None,
) -> dict[str, object]:
    if generated_dashboards is not None:
        return {
            item.dashboard.name: _dashboard_payload(
                project_root,
                config,
                item.dashboard,
                item.path,
            )
            for item in generated_dashboards
        }

    scan = scan_project(project_root, config)
    dashboards: dict[str, object] = {}
    paths = artifact_paths(scan.root, config)
    for dashboard_path in scan.dashboard_files:
        try:
            dashboard = load_dashboard(dashboard_path)
        except ValueError:
            continue
        output_path = paths.dashboards_dir / f"{dashboard.name}.html"
        dashboards[dashboard.name] = _dashboard_payload(
            scan.root,
            config,
            dashboard,
            output_path,
        )
    return dashboards


def _dashboard_payload(
    project_root: Path,
    config: GlyfConfig,
    dashboard: Dashboard,
    output_path: Path,
) -> dict[str, object]:
    paths = artifact_paths(project_root, config)
    path = (
        f"dashboards/{output_path.relative_to(paths.dashboards_dir).as_posix()}"
        if output_path.is_relative_to(paths.dashboards_dir)
        else output_path.relative_to(paths.root).as_posix()
    )
    return {
        "title": dashboard.title,
        "description": dashboard.description,
        "path": path,
        "theme": dashboard.theme or config.dashboard.theme,
        "chart_theme": dashboard.chart_theme or "auto",
        "tags": list(dashboard.tags),
        "charts": list(dashboard.chart_names),
        "filters": [_filter_payload(item) for item in dashboard.filters],
        "source": dashboard.path.relative_to(project_root).as_posix(),
    }


def _filter_payload(filter_spec: DashboardFilter) -> dict[str, object]:
    payload: dict[str, object] = {
        "field": filter_spec.field,
        "values": list(filter_spec.values),
    }
    if filter_spec.is_sourced:
        payload["source"] = {
            "chart": filter_spec.source_chart,
            "field": filter_spec.source_field,
        }
    return payload
