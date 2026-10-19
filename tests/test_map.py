import json
from pathlib import Path

import pandas as pd
import pytest

from glyf.ggsql.geo import MapShapesError, load_shapes, match_regions, resolve_shapes_path
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql
from glyf.ggsql.renderer import ChartRenderError, build_chart, render_chart
from glyf.pipeline import RenderError, render_project
from tests.helpers import copy_basic_project

REGIONS = (
    "select country, revenue from fct_orders\n\n"
    "VISUALISE country AS region, revenue AS color\n"
    "DRAW map\n"
)
POINTS = (
    "select lat, lon, stores, chain from fct_stores\n\n"
    "VISUALISE lat AS latitude, lon AS longitude, stores AS size, chain AS color\n"
    "DRAW map\n"
    "INTERACT tooltip\n"
)
# Two squares, keyed by `code` in their properties and by `id`.
SQUARES = {
    "type": "Topology",
    "objects": {
        "territories": {
            "type": "GeometryCollection",
            "geometries": [
                {"type": "Polygon", "arcs": [[0]], "id": 1, "properties": {"code": "NORTH"}},
                {"type": "Polygon", "arcs": [[1]], "id": 2, "properties": {"code": "SOUTH"}},
            ],
        }
    },
    "arcs": [
        [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
        [[0, -20], [10, -20], [10, -10], [0, -10], [0, -20]],
    ],
}


def test_parser_wrapper_carries_map_options() -> None:
    chart = parse_ggsql(
        REGIONS + "CONFIG shapes => 'geo/states.topojson'\nCONFIG projection => 'MERCATOR'\n"
    )

    assert chart.is_map and not chart.is_point_map
    assert chart.options == {"shapes": "geo/states.topojson", "projection": "mercator"}
    assert parse_ggsql(POINTS).is_point_map
    assert parse_ggsql("select 1\n\nVISUALISE a AS x, b AS y\nDRAW bar\n").options == {}


def test_parser_wrapper_reports_map_role_errors() -> None:
    with pytest.raises(GgsqlParseError, match="map requires a region mapping"):
        parse_ggsql("select 1\n\nVISUALISE revenue AS color\nDRAW map\n")


@pytest.mark.parametrize(
    ("regions", "key"),
    [
        (["USA", "GBR", "IND"], "properties.iso_a3"),
        (["US", "GB", "IN"], "properties.iso_a2"),
        (["United States", "United Kingdom", "India"], "properties.name"),
    ],
)
def test_bundled_world_matches_codes_and_names(regions: list[str], key: str) -> None:
    match = match_regions(load_shapes(None), regions)

    assert match.lookup_key == key
    assert match.unmatched == ()


def test_match_reports_regions_without_a_shape() -> None:
    match = match_regions(load_shapes(None), ["USA", "GBR", "ATLANTIS", None])

    assert match.lookup_key == "properties.iso_a3"
    assert match.unmatched == ("ATLANTIS",)


def test_match_fails_when_nothing_matches() -> None:
    with pytest.raises(MapShapesError, match="ISO 3166 codes such as 'USA'"):
        match_regions(load_shapes(None), ["North", "South"])


def test_choropleth_draws_land_and_looks_regions_up_by_the_matching_key(
    tmp_path: Path,
) -> None:
    chart = parse_ggsql(REGIONS)
    data = pd.DataFrame({"country": ["US", "GB", "IN"], "revenue": [30, 20, 10]})

    spec = build_chart(chart, data).to_dict()

    land, regions = spec["layer"]
    assert land["data"]["format"] == {"type": "topojson", "feature": "countries"}
    assert land["mark"]["fill"] == "#94a3b8"
    lookup = regions["transform"][0]
    assert lookup["lookup"] == "country"
    assert lookup["from"]["key"] == "properties.iso_a2"
    assert regions["encoding"]["color"]["type"] == "quantitative"
    # The rows are the layered chart's own data, so a filter added at the top
    # of the spec narrows them and leaves the land alone.
    assert "data" not in regions and spec["data"]["name"].startswith("data-")
    assert spec["projection"] == {"type": "equalEarth"}

    png, svg = tmp_path / "map.png", tmp_path / "map.svg"
    render_chart(chart, data, png, svg)
    assert png.read_bytes().startswith(b"\x89PNG")
    # Every country of the land layer is a path of its own.
    assert svg.read_text(encoding="utf-8").count("<path") > 150


def test_point_map_draws_circles_at_coordinates_with_tooltips() -> None:
    chart = parse_ggsql(POINTS)
    data = pd.DataFrame(
        {"lat": [51.5, 40.7], "lon": [-0.1, -74.0], "stores": [12, 30], "chain": ["A", "B"]}
    )

    spec = build_chart(chart, data).to_dict()

    points = spec["layer"][1]
    assert points["mark"]["type"] == "circle"
    assert points["encoding"]["latitude"]["field"] == "lat"
    assert points["encoding"]["size"]["field"] == "stores"
    assert points["encoding"]["color"]["type"] == "nominal"
    assert [item["field"] for item in points["encoding"]["tooltip"]] == [
        "lat",
        "lon",
        "stores",
        "chain",
    ]


def test_point_map_needs_numeric_coordinates(tmp_path: Path) -> None:
    chart = parse_ggsql(POINTS)
    data = pd.DataFrame(
        {"lat": ["north"], "lon": [-0.1], "stores": [1], "chain": ["A"]}
    )

    with pytest.raises(ChartRenderError, match="numeric latitude column and 'lat'"):
        render_chart(chart, data, tmp_path / "m.png", tmp_path / "m.svg")


def test_custom_shapes_match_on_their_own_keys(tmp_path: Path) -> None:
    shapes = tmp_path / "territories.topojson"
    shapes.write_text(json.dumps(SQUARES), encoding="utf-8")
    chart = parse_ggsql(
        "select territory, sales from t\n\nVISUALISE territory AS region, sales AS color\n"
        f"DRAW map\nCONFIG shapes => '{shapes}'\nCONFIG projection => 'mercator'\n"
    )
    data = pd.DataFrame({"territory": ["NORTH", "SOUTH"], "sales": [3, 4]})

    spec = build_chart(chart, data).to_dict()

    assert spec["layer"][0]["data"]["format"]["feature"] == "territories"
    assert spec["layer"][1]["transform"][0]["from"]["key"] == "properties.code"
    assert spec["projection"] == {"type": "mercator"}
    by_id = match_regions(load_shapes(str(shapes)), [1, 2])
    assert by_id.lookup_key == "id"


def test_custom_shapes_must_be_topojson(tmp_path: Path) -> None:
    path = tmp_path / "regions.json"
    path.write_text('{"type": "FeatureCollection", "features": []}', encoding="utf-8")

    with pytest.raises(MapShapesError, match="not a TopoJSON topology"):
        load_shapes(str(path))


def test_shapes_path_stays_inside_the_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "geo").mkdir(parents=True)
    (project / "geo" / "x.topojson").write_text("{}", encoding="utf-8")
    (tmp_path / "outside.topojson").write_text("{}", encoding="utf-8")

    assert resolve_shapes_path("geo/x.topojson", project) == (
        project / "geo" / "x.topojson"
    ).resolve()
    with pytest.raises(MapShapesError, match="outside the project"):
        resolve_shapes_path("../outside.topojson", project)
    with pytest.raises(MapShapesError, match="does not exist"):
        resolve_shapes_path("geo/missing.topojson", project)


def _write_map(project: Path, body: str) -> None:
    (project / "visualisations" / "sales_map.ggsql").write_text(body, encoding="utf-8")


def test_pipeline_builds_a_map_and_warns_about_regions_it_cannot_place(
    tmp_path: Path,
) -> None:
    project = copy_basic_project(tmp_path)
    _write_map(
        project,
        "select * from (values ('USA', 10), ('GBR', 7), ('Atlantis', 1)) "
        "as t(country, revenue)\n\n"
        "VISUALISE country AS region, revenue AS color\nDRAW map\n",
    )

    result = render_project(project)

    metadata = json.loads(
        (project / "target/glyf/charts/sales_map.json").read_text(encoding="utf-8")
    )
    assert metadata["chart_type"] == "map"
    assert metadata["roles"] == [["region", "country"], ["color", "revenue"]]
    assert (metadata["x"], metadata["y"]) == ("country", "revenue")
    assert (project / "target/glyf/charts/sales_map.png").exists()
    assert any(
        "1 region(s) have no shape and are left off the map: Atlantis" in warning
        for warning in result.warnings
    )


def test_pipeline_reads_shapes_relative_to_the_project(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "geo").mkdir()
    (project / "geo" / "territories.topojson").write_text(
        json.dumps(SQUARES), encoding="utf-8"
    )
    _write_map(
        project,
        "select * from (values ('NORTH', 3), ('SOUTH', 4)) as t(territory, sales)\n\n"
        "VISUALISE territory AS region, sales AS color\nDRAW map\n"
        "CONFIG shapes => 'geo/territories.topojson'\n",
    )

    render_project(project)

    assert (project / "target/glyf/charts/sales_map.svg").exists()


def test_pipeline_refuses_shapes_outside_the_project(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (tmp_path / "secret.topojson").write_text(json.dumps(SQUARES), encoding="utf-8")
    _write_map(
        project,
        "select 'NORTH' as territory\n\nVISUALISE territory AS region\nDRAW map\n"
        "CONFIG shapes => '../secret.topojson'\n",
    )

    with pytest.raises(RenderError, match="sales_map.ggsql: CONFIG shapes '../secret.topojson' is outside the project"):
        render_project(project)


def test_a_label_heads_the_tooltip_and_zoom_marks_the_spec() -> None:
    chart = parse_ggsql(
        "select city, lat, lon from fct_stores\n\n"
        "VISUALISE city AS label, lat AS latitude, lon AS longitude\nDRAW map\n"
        "INTERACT tooltip, zoom\n"
    )
    data = pd.DataFrame({"city": ["Paris"], "lat": [48.86], "lon": [2.35]})

    spec = build_chart(chart, data).to_dict()

    points = spec["layer"][1]
    assert [item["field"] for item in points["encoding"]["tooltip"]] == ["city", "lat", "lon"]
    assert spec["usermeta"] == {"glyf": {"zoom": "map"}}
    assert "usermeta" not in build_chart(parse_ggsql(REGIONS), pd.DataFrame({"country": ["FRA"], "revenue": [1]})).to_dict()


def test_the_shapes_are_one_named_dataset_the_land_and_lookup_share() -> None:
    spec = build_chart(parse_ggsql(REGIONS), pd.DataFrame({"country": ["FRA"], "revenue": [1]})).to_dict()

    shapes = [name for name in spec["datasets"] if name.startswith("glyf-shapes-")]
    assert len(shapes) == 1
    land, regions = spec["layer"]
    assert land["data"]["name"] == shapes[0]
    assert regions["transform"][0]["from"]["data"]["name"] == shapes[0]
    assert len(json.dumps(spec)) < 1.5 * len(json.dumps(load_shapes(None).topology))


def test_a_dashboard_carries_the_shapes_once_for_every_map() -> None:
    from glyf.dashboard.artifacts import ChartArtifact, ChartDataArtifact, ChartMetadata
    from glyf.dashboard.renderer import share_datasets

    def artifact(name: str, spec: dict) -> ChartArtifact:
        metadata = ChartMetadata(
            name=name, title=None, chart_type="map", x="country", y="revenue",
            compiled_sql_path=Path("c.sql"), data_json_path=Path("d.json"),
            png_path=Path("p.png"), svg_path=Path("s.svg"),
        )
        return ChartArtifact(metadata, None, None, ChartDataArtifact((), ()), vega_spec=spec)

    rows = pd.DataFrame({"country": ["FRA"], "revenue": [1]})
    spec = build_chart(parse_ggsql(REGIONS), rows).to_dict()
    charts = {"a": artifact("a", spec), "b": artifact("b", spec)}

    trimmed, shared = share_datasets(charts)

    assert list(shared) == [name for name in spec["datasets"] if name.startswith("glyf-shapes-")]
    for chart in trimmed.values():
        assert not any(name.startswith("glyf-shapes-") for name in chart.vega_spec["datasets"])
        assert chart.vega_spec["usermeta"]["glyf"]["shared"] == list(shared)
    # The artifact read from disk keeps its shapes.
    assert any(name.startswith("glyf-shapes-") for name in charts["a"].vega_spec["datasets"])
