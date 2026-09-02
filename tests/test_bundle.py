"""The `bundle.json` contract.

`docs-site/docs/reference/bundle.md` documents this file for third parties, so
the shapes asserted here are the published contract, not incidental output. A
field added, removed or renamed fails these tests until the reference page is
updated to match.
"""

import json
import os
import time
from pathlib import Path

from glyf.bundle import BUNDLE_VERSION, write_bundle_manifest
from glyf.dashboard.generator import generate_dashboards
from glyf.exporter import export_site
from glyf.output.paths import artifact_paths
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

TOP_LEVEL_KEYS = {
    "bundle_version",
    "charts",
    "dashboards",
    "generated_at",
    "glyf_version",
    "mode",
    "paths",
    "project",
    "security",
}

# `build` is the provenance record: present in a local manifest, and in a
# public one only under `export.provenance: public`. Covered by
# tests/test_provenance.py.
OPTIONAL_TOP_LEVEL_KEYS = {"build"}

PATH_KEYS = {"assets", "charts", "compiled", "dashboards", "index"}
INTERNAL_PATH_KEYS = PATH_KEYS | {"data"}
DATA_PATH_KEYS = {"normalized", "vega"}

SECURITY_KEYS = {
    "browser_visible_data",
    "internal_artifacts",
    "internal_artifacts_included",
    "public_export",
}

CHART_KEYS = {"artifacts", "chart_type", "fields", "title"}
CHART_ARTIFACT_KEYS = {"compiled_sql", "data", "metadata", "png", "svg", "vega"}
CHART_FIELD_KEYS = {"x", "y"}

DASHBOARD_KEYS = {
    "chart_theme",
    "charts",
    "description",
    "filters",
    "path",
    "source",
    "tags",
    "theme",
    "title",
}

FILTER_KEYS = {"field", "values"}
FILTER_SOURCE_KEYS = {"chart", "field"}


def test_local_bundle_matches_documented_shape(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)

    bundle = _read(project / "target" / "glyf" / "bundle.json")

    _assert_common_shape(bundle)
    assert bundle["mode"] == "local_artifact"
    assert set(bundle["paths"]) == INTERNAL_PATH_KEYS
    assert set(bundle["paths"]["data"]) == DATA_PATH_KEYS
    assert bundle["security"]["public_export"] is False
    assert bundle["security"]["internal_artifacts_included"] is True
    assert bundle["security"]["internal_artifacts"] == [
        "data/normalized",
        "data/vega",
    ]


def test_public_bundle_matches_documented_shape(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)
    export_site(project)

    bundle = _read(project / "target" / "glyf" / "site" / "bundle.json")

    _assert_common_shape(bundle)
    assert bundle["mode"] == "public_site"
    assert set(bundle["paths"]) == PATH_KEYS
    assert bundle["security"]["public_export"] is True
    assert bundle["security"]["internal_artifacts_included"] is False
    assert bundle["security"]["internal_artifacts"] == []


def test_public_bundle_nulls_rather_than_drops_internal_artifacts(
    tmp_path: Path,
) -> None:
    """The keys stay; only their values go. Documented, because a consumer
    checking `"data" in artifacts` would otherwise read it wrong."""
    project = _rendered_project(tmp_path)
    export_site(project)

    local = _read(project / "target" / "glyf" / "bundle.json")
    public = _read(project / "target" / "glyf" / "site" / "bundle.json")

    assert local["charts"]["revenue"]["artifacts"]["data"] == (
        "data/normalized/revenue.data.json"
    )
    assert local["charts"]["revenue"]["artifacts"]["vega"] == (
        "data/vega/revenue.vega.json"
    )
    public_artifacts = public["charts"]["revenue"]["artifacts"]
    assert set(public_artifacts) == CHART_ARTIFACT_KEYS
    assert public_artifacts["data"] is None
    assert public_artifacts["vega"] is None


def test_optional_chart_and_filter_keys(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)

    bundle = _read(project / "target" / "glyf" / "bundle.json")
    chart = bundle["charts"]["revenue"]
    dashboard = bundle["dashboards"]["executive"]

    assert chart["interactions"] == ["tooltip", "zoom"]
    assert [item["field"] for item in dashboard["filters"]] == ["region", "focus"]
    sourced, listed = dashboard["filters"]
    assert set(sourced) == FILTER_KEYS | {"source"}
    assert set(sourced["source"]) == FILTER_SOURCE_KEYS
    assert sourced["source"] == {"chart": "revenue", "field": "month"}
    assert set(listed) == FILTER_KEYS
    assert listed["values"] == ["revenue", "margin"]


def test_bundle_version_is_the_documented_one() -> None:
    assert BUNDLE_VERSION == "1"


def test_generated_at_falls_back_to_the_index_mtime(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)
    paths = artifact_paths(project)
    paths.bundle_manifest.unlink()
    mtime = time.time() - 3600
    os.utime(paths.root / "index.html", (mtime, mtime))

    write_bundle_manifest(project, output_path=paths.bundle_manifest)

    bundle = _read(paths.bundle_manifest)
    assert bundle["generated_at"] == time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(mtime))
    )


def test_generated_at_is_null_without_an_index(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)
    paths = artifact_paths(project)
    paths.bundle_manifest.unlink()
    (paths.root / "index.html").unlink()

    write_bundle_manifest(project, output_path=paths.bundle_manifest)

    assert _read(paths.bundle_manifest)["generated_at"] is None


def _assert_common_shape(bundle: dict) -> None:
    assert TOP_LEVEL_KEYS <= set(bundle)
    assert set(bundle) <= TOP_LEVEL_KEYS | OPTIONAL_TOP_LEVEL_KEYS
    assert bundle["bundle_version"] == BUNDLE_VERSION
    assert isinstance(bundle["glyf_version"], str)
    assert bundle["project"] == "basic"
    assert set(bundle["security"]) == SECURITY_KEYS

    for chart in bundle["charts"].values():
        assert set(chart) <= CHART_KEYS | {"interactions"}
        assert CHART_KEYS <= set(chart)
        assert set(chart["fields"]) == CHART_FIELD_KEYS
        assert set(chart["artifacts"]) == CHART_ARTIFACT_KEYS

    for dashboard in bundle["dashboards"].values():
        assert set(dashboard) == DASHBOARD_KEYS
        for filter_spec in dashboard["filters"]:
            assert set(filter_spec) <= FILTER_KEYS | {"source"}
            assert FILTER_KEYS <= set(filter_spec)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rendered_project(tmp_path: Path) -> Path:
    """A build exercising the optional parts of the contract: a chart with
    interactions (so a Vega spec exists) and both kinds of dashboard filter."""
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "SELECT month, revenue\n"
        "FROM {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW line\n"
        "LABEL title => 'Monthly Revenue'\n"
        "INTERACT tooltip, zoom\n",
        encoding="utf-8",
    )
    dashboard = project / "dashboards" / "executive.yml"
    dashboard.write_text(
        dashboard.read_text(encoding="utf-8")
        + "\nfilters:\n"
        "  - field: region\n"
        "    values: source(revenue, month)\n"
        "  - field: focus\n"
        "    values: [revenue, margin]\n",
        encoding="utf-8",
    )
    render_project(project)
    generate_dashboards(project)
    return project
