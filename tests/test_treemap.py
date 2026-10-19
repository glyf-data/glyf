import json
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from glyf.dashboard.artifacts import load_chart_artifact
from glyf.dashboard.filters import _mode
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql
from glyf.ggsql.renderer import ChartRenderError, build_chart, required_columns
from glyf.ggsql.treemap import GROUP_GAP, TreemapError, layout_treemap
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

TREEMAP = "select city, format, revenue from stores\n\nVISUALISE city AS label, revenue AS value{group}\nDRAW treemap\n"
STORES = [
    ("New York", "Flagship", 52),
    ("London", "Flagship", 44),
    ("Chicago", "Outlet", 24),
    ("Berlin", "Outlet", 29),
    ("Sydney", "Outlet", 23),
]


def _area(tile) -> float:
    return tile.width * tile.height


def test_parser_wrapper_accepts_a_treemap_with_or_without_a_group() -> None:
    chart = parse_ggsql(TREEMAP.format(group=", format AS group") + "INTERACT tooltip\n")

    assert chart.is_treemap
    assert required_columns(chart) == ("city", "revenue", "format")
    assert parse_ggsql(TREEMAP.format(group="")).field_for_role("group") is None
    with pytest.raises(GgsqlParseError, match="treemap requires label and value mappings"):
        parse_ggsql("select 1\n\nVISUALISE a AS label\nDRAW treemap\n")


def test_tiles_fill_the_box_with_areas_in_proportion_to_values() -> None:
    tiles = layout_treemap([(city, None, revenue) for city, _, revenue in STORES], 600, 400)

    assert [tile.label for tile in tiles] == ["New York", "London", "Berlin", "Chicago", "Sydney"]
    for tile in tiles:
        assert 0 <= tile.x0 < tile.x1 <= 600 and 0 <= tile.y0 < tile.y1 <= 400
    # The 1px gap between tiles shaves a little off each; the proportions hold.
    by_label = {tile.label: tile for tile in tiles}
    assert _area(by_label["New York"]) / _area(by_label["Sydney"]) == pytest.approx(52 / 23, rel=0.05)
    assert sum(_area(tile) for tile in tiles) == pytest.approx(600 * 400, rel=0.03)


def test_tiles_are_close_to_square() -> None:
    tiles = layout_treemap([(f"t{n}", None, 10 + n) for n in range(12)], 600, 400)

    for tile in tiles:
        assert max(tile.width / tile.height, tile.height / tile.width) < 4


def test_a_group_is_one_block_of_its_own_tiles() -> None:
    tiles = layout_treemap(STORES, 600, 400)

    flagship = [tile for tile in tiles if tile.group == "Flagship"]
    outlet = [tile for tile in tiles if tile.group == "Outlet"]
    left, right = (max(t.x1 for t in flagship), min(t.x0 for t in outlet))
    # Flagship's 96 against Outlet's 76: the larger group comes first, whole.
    assert left < right and right - left >= GROUP_GAP - 1e-9


def test_repeated_tiles_are_summed_and_zeros_and_gaps_skipped() -> None:
    tiles = layout_treemap(
        [("A", None, 2), ("A", None, Decimal("3.5")), ("B", None, 0), (None, None, 9), ("C", None, 1)],
        300,
        200,
    )

    assert {tile.label: tile.value for tile in tiles} == {"A": 5.5, "C": 1.0}


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([("A", None, -1)], "is negative"),
        ([("A", None, "lots")], "needs a numeric value"),
        ([("A", None, 0)], "nothing to draw"),
    ],
)
def test_layout_refuses_rows_it_cannot_draw(rows: list, message: str) -> None:
    with pytest.raises(TreemapError, match=message):
        layout_treemap(rows, 300, 200)


def test_spec_draws_rects_coloured_by_group_with_names_that_fit() -> None:
    chart = parse_ggsql(TREEMAP.format(group=", format AS group") + "INTERACT tooltip\n")
    rows = pd.DataFrame(STORES + [("A very long store name indeed", "Outlet", 1)], columns=["city", "format", "revenue"])

    spec = build_chart(chart, rows).to_dict()

    rects, names, amounts = spec["layer"]
    assert rects["mark"]["type"] == "rect"
    assert rects["encoding"]["color"]["scale"]["domain"] == ["Flagship", "Outlet"]
    assert [item["title"] for item in rects["encoding"]["tooltip"]] == [
        "city",
        "format",
        "revenue",
        "share of the total",
    ]
    tiles = {row["label"]: row for row in next(iter(spec["datasets"].values()))}
    assert tiles["New York"]["named"] and tiles["New York"]["name"] == "New York"
    # A tile too small for its name keeps it in the tooltip only.
    assert not tiles["A very long store name indeed"]["named"]
    assert names["transform"] == [{"filter": "datum.named"}]
    assert spec["config"]["view"]["stroke"] is None


def test_a_text_value_is_a_render_error() -> None:
    chart = parse_ggsql(TREEMAP.format(group=""))

    with pytest.raises(ChartRenderError, match="treemap needs a numeric value column"):
        build_chart(chart, pd.DataFrame({"city": ["a"], "revenue": ["b"]}))


def test_pipeline_builds_a_treemap_that_filters_leave_alone(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "stores.ggsql").write_text(
        "select * from (values ('NY', 'Flagship', 5), ('LA', 'Outlet', 3)) as t(city, format, revenue)\n\n"
        "VISUALISE city AS label, revenue AS value, format AS group\nDRAW treemap\nINTERACT tooltip\n",
        encoding="utf-8",
    )

    render_project(project)

    metadata = json.loads((project / "target/glyf/charts/stores.json").read_text(encoding="utf-8"))
    assert (metadata["x"], metadata["y"]) == ("city", "revenue")
    assert metadata["roles"] == [["label", "city"], ["value", "revenue"], ["group", "format"]]
    assert _mode(load_chart_artifact(project, "stores"), "format") == "none"
