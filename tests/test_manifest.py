import json
from pathlib import Path

from glyf.manifest.loader import load_manifest
from glyf.manifest.resolver import resolve_refs
from tests.helpers import write_basic_manifest


def test_manifest_loads_models(tmp_path: Path) -> None:
    manifest = load_manifest(write_basic_manifest(tmp_path / "basic"))

    assert len(manifest.models) == 1
    assert manifest.models[0].name == "fct_orders"
    assert manifest.models[0].relation_name == "main.fct_orders"


def test_resolve_refs_uses_manifest_relation_name(tmp_path: Path) -> None:
    manifest = load_manifest(write_basic_manifest(tmp_path / "basic"))

    result = resolve_refs("select * from {{ ref('fct_orders') }}", manifest)

    assert result.sql == "select * from main.fct_orders"
    assert result.refs == ("fct_orders",)
    assert result.missing_refs == ()


def test_resolve_refs_reports_missing_refs(tmp_path: Path) -> None:
    manifest = load_manifest(write_basic_manifest(tmp_path / "basic"))

    result = resolve_refs("select * from {{ ref('missing_model') }}", manifest)

    assert result.sql == "select * from {{ ref('missing_model') }}"
    assert result.missing_refs == ("missing_model",)


def test_real_style_manifest_loads_refable_nodes_and_sources(tmp_path: Path) -> None:
    manifest = load_manifest(_write_real_style_manifest(tmp_path / "manifest.json"))

    assert {node.resource_type for node in manifest.refable_nodes} == {
        "model",
        "seed",
        "snapshot",
    }
    assert manifest.relation_for_ref("fct_orders") == "main.fct_orders"
    assert manifest.relation_for_ref("raw_orders") == "main.raw_orders"
    assert manifest.relation_for_ref("orders_snapshot") == "main.orders_snapshot"
    assert manifest.relation_for_source("raw", "orders") == "main.raw_orders"


def test_resolve_sources_uses_manifest_source_relation(tmp_path: Path) -> None:
    manifest = load_manifest(_write_real_style_manifest(tmp_path / "manifest.json"))

    result = resolve_refs("select * from {{ source('raw', 'orders') }}", manifest)

    assert result.sql == "select * from main.raw_orders"
    assert result.sources == (("raw", "orders"),)
    assert result.missing_sources == ()


def test_resolve_sources_reports_missing_sources(tmp_path: Path) -> None:
    manifest = load_manifest(_write_real_style_manifest(tmp_path / "manifest.json"))

    result = resolve_refs("select * from {{ source('raw', 'missing') }}", manifest)

    assert result.sql == "select * from {{ source('raw', 'missing') }}"
    assert result.missing_sources == (("raw", "missing"),)


def _write_real_style_manifest(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "nodes": {
                    "model.simple_dbt.fct_orders": {
                        "resource_type": "model",
                        "package_name": "simple_dbt",
                        "name": "fct_orders",
                        "alias": "fct_orders",
                        "database": "main",
                        "schema": "main",
                        "relation_name": "main.fct_orders",
                    },
                    "seed.simple_dbt.raw_orders": {
                        "resource_type": "seed",
                        "package_name": "simple_dbt",
                        "name": "raw_orders",
                        "alias": "raw_orders",
                        "database": "main",
                        "schema": "main",
                        "relation_name": "main.raw_orders",
                    },
                    "snapshot.simple_dbt.orders_snapshot": {
                        "resource_type": "snapshot",
                        "package_name": "simple_dbt",
                        "name": "orders_snapshot",
                        "alias": "orders_snapshot",
                        "database": "main",
                        "schema": "main",
                        "relation_name": "main.orders_snapshot",
                    },
                },
                "sources": {
                    "source.simple_dbt.raw.orders": {
                        "resource_type": "source",
                        "package_name": "simple_dbt",
                        "source_name": "raw",
                        "name": "orders",
                        "identifier": "raw_orders",
                        "database": "main",
                        "schema": "main",
                        "relation_name": "main.raw_orders",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return path
