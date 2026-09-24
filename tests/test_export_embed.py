"""Publishing charts for embedding, and the bundle schema that describes them.

`export.embed` publishes each drawn chart's Vega spec in the site so an
application can draw it live with glyf-js. These tests pin what it publishes,
what it refuses to, and that every bundle glyf writes matches the published
JSON Schema, which is the contract glyf-js tests against.
"""

import json
from dataclasses import replace
from pathlib import Path

import jsonschema
import pytest

from glyf.config import ConfigError, ExportConfig, GlyfConfig, load_config
from glyf.dashboard.generator import generate_dashboards
from glyf.exporter import export_site
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

SCHEMA_PATH = Path("schemas/bundle.v1.schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _site(tmp_path: Path, export: ExportConfig) -> tuple[Path, dict]:
    project = copy_basic_project(tmp_path)
    config = replace(GlyfConfig(), export=export)
    render_project(project, config)
    generate_dashboards(project, config)
    export_site(project, config=config)
    site = project / "target" / "glyf" / "site"
    return site, json.loads((site / "bundle.json").read_text(encoding="utf-8"))


def test_embed_publishes_each_drawn_charts_spec(tmp_path: Path) -> None:
    site, bundle = _site(tmp_path, ExportConfig(embed=True))

    artifacts = bundle["charts"]["revenue"]["artifacts"]
    assert artifacts["vega"] == "charts/revenue.vega.json"
    assert artifacts["data"] is None, "the normalised rows stay local"
    spec = json.loads((site / artifacts["vega"]).read_text(encoding="utf-8"))
    assert "$schema" in spec and spec.get("datasets")
    assert bundle["security"]["embedded_specs"] is True
    assert "export.embed" in bundle["security"]["browser_visible_data"]


def test_without_embed_no_spec_is_published_and_a_stale_one_goes(tmp_path: Path) -> None:
    site, _ = _site(tmp_path, ExportConfig(embed=True))
    project = site.parent.parent.parent

    export_site(project, config=GlyfConfig())

    bundle = json.loads((site / "bundle.json").read_text(encoding="utf-8"))
    assert bundle["charts"]["revenue"]["artifacts"]["vega"] is None
    assert "embedded_specs" not in bundle["security"]
    assert not list((site / "charts").glob("*.vega.json"))


def test_embed_under_minimal_publishes_only_the_encoded_columns(tmp_path: Path) -> None:
    site, bundle = _site(tmp_path, ExportConfig(row_data="minimal", embed=True))

    spec = json.loads((site / "charts" / "revenue.vega.json").read_text(encoding="utf-8"))
    rows = next(iter(spec["datasets"].values()))
    chart = bundle["charts"]["revenue"]["fields"]
    assert set(rows[0]) == {chart["x"], chart["y"]}


def test_embed_cannot_be_asked_for_alongside_exclude(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text(
        "export:\n  row_data: exclude\n  embed: true\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="export.embed"):
        load_config(tmp_path)


@pytest.mark.parametrize(
    "export",
    [ExportConfig(), ExportConfig(embed=True), ExportConfig(row_data="minimal"), ExportConfig(row_data="exclude")],
    ids=["include", "embed", "minimal", "exclude"],
)
def test_every_bundle_matches_the_published_schema(tmp_path: Path, export: ExportConfig) -> None:
    site, public = _site(tmp_path, export)
    local = json.loads((site.parent / "bundle.json").read_text(encoding="utf-8"))

    jsonschema.validate(public, SCHEMA)
    jsonschema.validate(local, SCHEMA)


def test_the_docs_site_serves_the_same_schema() -> None:
    served = Path("docs-site/static/schema/bundle.v1.schema.json")
    assert served.read_text(encoding="utf-8") == SCHEMA_PATH.read_text(encoding="utf-8")
