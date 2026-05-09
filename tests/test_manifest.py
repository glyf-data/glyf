from pathlib import Path

from dbt_ggsql.manifest.loader import load_manifest
from dbt_ggsql.manifest.resolver import resolve_refs


def test_manifest_loads_models() -> None:
    manifest = load_manifest(Path("examples/basic/target/manifest.json"))

    assert len(manifest.models) == 1
    assert manifest.models[0].name == "fct_orders"
    assert manifest.models[0].relation_name == "main.fct_orders"


def test_resolve_refs_uses_manifest_relation_name() -> None:
    manifest = load_manifest(Path("examples/basic/target/manifest.json"))

    result = resolve_refs("select * from {{ ref('fct_orders') }}", manifest)

    assert result.sql == "select * from main.fct_orders"
    assert result.refs == ("fct_orders",)
    assert result.missing_refs == ()


def test_resolve_refs_reports_missing_refs() -> None:
    manifest = load_manifest(Path("examples/basic/target/manifest.json"))

    result = resolve_refs("select * from {{ ref('missing_model') }}", manifest)

    assert result.sql == "select * from {{ ref('missing_model') }}"
    assert result.missing_refs == ("missing_model",)
