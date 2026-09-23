"""Lineage: the sources, models and charts behind a dashboard.

Recorded per chart at build time from the manifest's parent records, so a
dashboard draws the whole graph from artifacts alone. Shown as a Lineage
view beside Source, and withheld the way the compiled SQL is under
`export.row_data: exclude`, because it names warehouse tables.
"""

import json
from dataclasses import replace
from pathlib import Path

from glyf.config import ExportConfig, GlyfConfig, load_config
from glyf.dashboard.artifacts import load_chart_artifact
from glyf.dashboard.generator import generate_dashboards
from glyf.dashboard.lineage import build_lineage
from glyf.exporter import export_site
from glyf.manifest.loader import load_manifest
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project, copy_simple_dbt_project, _write_manifest


def _project(tmp_path: Path) -> Path:
    """A project whose manifest records parents: fct_orders <- stg_orders <- raw.orders."""
    project = copy_simple_dbt_project(tmp_path)
    _write_manifest(
        project,
        {
            "nodes": {
                "model.simple_dbt.fct_orders": {
                    "resource_type": "model", "package_name": "simple_dbt", "name": "fct_orders",
                    "relation_name": "main.fct_orders", "original_file_path": "models/fct_orders.sql",
                    "depends_on": {"macros": [], "nodes": ["model.simple_dbt.stg_orders"]},
                },
                "model.simple_dbt.stg_orders": {
                    "resource_type": "model", "package_name": "simple_dbt", "name": "stg_orders",
                    "relation_name": "main.stg_orders", "original_file_path": "models/stg_orders.sql",
                    "depends_on": {"macros": [], "nodes": ["source.simple_dbt.raw.orders"]},
                },
            },
            "sources": {
                "source.simple_dbt.raw.orders": {
                    "resource_type": "source", "package_name": "simple_dbt", "source_name": "raw",
                    "name": "orders", "relation_name": "main.raw_orders",
                }
            },
        },
    )
    return project


def test_the_manifest_loader_reads_parents_and_files(tmp_path: Path) -> None:
    project = _project(tmp_path)

    manifest = load_manifest(project / "target" / "manifest.json")

    fct = manifest.node_for_ref("fct_orders")
    assert fct is not None
    assert fct.parents == ("model.simple_dbt.stg_orders",)
    assert fct.path == "models/fct_orders.sql"
    assert manifest.node_by_id("source.simple_dbt.raw.orders").name == "orders"


def test_a_chart_records_its_lineage_back_to_the_raw_tables(tmp_path: Path) -> None:
    project = _project(tmp_path)

    render_project(project)

    charts = project / "target" / "glyf" / "charts"
    for path in sorted(charts.glob("*.json")):
        metadata = json.loads(path.read_text(encoding="utf-8"))
        assert "lineage" in metadata, path.name
    revenue = json.loads((charts / "revenue.json").read_text(encoding="utf-8"))
    assert revenue["lineage"] == {
        "models": {
            "fct_orders": {"parents": ["stg_orders"], "path": "models/fct_orders.sql"},
            "stg_orders": {"parents": ["source:raw.orders"], "path": "models/stg_orders.sql"},
        },
        "sources": ["raw.orders"],
    }


def test_the_graph_joins_every_chart_on_the_dashboard(tmp_path: Path) -> None:
    project = _project(tmp_path)
    render_project(project)
    names = sorted(p.stem for p in (project / "target" / "glyf" / "charts").glob("*.json"))
    charts = tuple(load_chart_artifact(project, name) for name in names)

    graph = build_lineage(charts)

    kinds = {node.id: node for node in graph.nodes}
    assert graph.source_count == 1 and graph.model_count == 2 and graph.chart_count == len(charts)
    assert "source:raw.orders" in kinds and "model:stg_orders" in kinds and "model:fct_orders" in kinds
    assert kinds["chart:revenue"].subtitle == "line"
    assert kinds["chart:revenue"].tip == "binds month AS x, revenue AS y"
    assert kinds["model:fct_orders"].tip == "models/fct_orders.sql"
    pairs = {(edge.source, edge.target) for edge in graph.edges}
    assert ("source:raw.orders", "model:stg_orders") in pairs
    assert ("model:stg_orders", "model:fct_orders") in pairs
    assert ("model:fct_orders", "chart:revenue") in pairs
    # A chart reads its direct refs only; stg_orders is reached through fct_orders.
    assert ("model:stg_orders", "chart:revenue") not in pairs
    # Columns sit left to right, rows never overlap.
    xs = {node.kind: node.x for node in graph.nodes}
    assert xs["source"] < xs["model"] < xs["chart"]


def test_the_dashboard_gets_a_lineage_button_and_view(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)

    generate_dashboards(project)

    html = (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(encoding="utf-8")
    assert 'data-glyf-lineage-button' in html
    assert 'id="glyf-lineage-view"' in html and "hidden" in html
    assert 'data-node="chart:revenue"' in html
    assert 'data-node="model:fct_orders"' in html
    assert 'data-glyf-zoom="in"' in html
    assert "getPointerCapture" not in html and "setPointerCapture" in html


def test_the_view_can_be_turned_off_in_config(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "glyf.yml").write_text("dashboard:\n  show_lineage: false\n", encoding="utf-8")
    config = load_config(project)
    assert config.dashboard.show_lineage is False
    render_project(project, config)

    generate_dashboards(project, config)

    html = (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(encoding="utf-8")
    assert "data-glyf-lineage-button" not in html
    assert "glyf-lineage-view" not in html


def test_exclude_withholds_lineage_like_the_compiled_sql(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    config = replace(GlyfConfig(), export=ExportConfig(row_data="exclude"))
    render_project(project, config)
    generate_dashboards(project, config)
    export_site(project, config=config)

    site = project / "target" / "glyf" / "site"
    html = (site / "dashboards" / "executive.html").read_text(encoding="utf-8")
    assert "data-glyf-lineage-button" not in html
    metadata = json.loads((site / "charts" / "revenue.json").read_text(encoding="utf-8"))
    assert "lineage" not in metadata
    # ...while the default export keeps it.
    render_project(project)
    generate_dashboards(project)
    export_site(project)
    metadata = json.loads((site / "charts" / "revenue.json").read_text(encoding="utf-8"))
    assert metadata["lineage"]["models"] == {"fct_orders": {"parents": [], "path": None}}
