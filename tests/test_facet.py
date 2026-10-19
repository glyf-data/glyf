import json
from pathlib import Path

import pandas as pd
import pytest

from glyf.dashboard.chart_theme import _apply_dark_vega_theme
from glyf.diff.overlay import build_overlay
from glyf.downsample import downsample_m4
from glyf.execution.result import QueryResult
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql
from glyf.ggsql.renderer import build_chart, required_columns
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

ROWS = pd.DataFrame(
    {
        "month": ["Jan", "Feb", "Jan", "Feb", "Jan", "Feb", "Jan", "Feb"],
        "revenue": [10, 12, 8, 9, 5, 7, 3, 4],
        "region": ["North", "North", "South", "South", "East", "East", "West", "West"],
    }
)


def _chart(extra: str = "", draw: str = "line", mapping: str = "month AS x, revenue AS y") -> object:
    return parse_ggsql(
        f"select month, revenue, region from fct_sales\n\nVISUALISE {mapping}, region AS facet\n"
        f"DRAW {draw}\n{extra}"
    )


def test_parser_wrapper_reads_the_facet_and_its_columns() -> None:
    chart = _chart("CONFIG columns => 2\n")

    assert chart.facet == "region"
    assert chart.columns == 2
    assert required_columns(chart) == ("month", "revenue", "region")
    with pytest.raises(GgsqlParseError, match="CONFIG columns lays out a faceted chart's panels"):
        parse_ggsql("select 1\n\nVISUALISE a AS x, b AS y\nDRAW bar\nCONFIG columns => 2\n")


def test_panels_share_the_width_in_rows_of_at_most_three() -> None:
    spec = build_chart(_chart("CONFIG width => 960\n"), ROWS).to_dict()

    assert spec["facet"]["field"] == "region"
    assert spec["columns"] == 3
    # Three panels and two gaps across the width; a panel 0.6 of its width tall.
    assert spec["spec"]["width"] == (960 - 2 * 16) // 3
    assert spec["spec"]["height"] == int(spec["spec"]["width"] * 0.6)
    assert spec["spec"]["encoding"]["x"]["axis"]["labelOverlap"] == "parity"


def test_config_columns_and_height_set_the_grid() -> None:
    spec = build_chart(_chart("CONFIG columns => 2\nCONFIG height => 416\nLABEL title => 'By region'\n"), ROWS).to_dict()

    assert spec["columns"] == 2
    # Two rows of panels and one gap in the height.
    assert spec["spec"]["height"] == (416 - 16) // 2
    assert spec["title"] == {"text": "By region", "anchor": "middle"}


def test_fewer_panels_than_columns_take_the_room_between_them() -> None:
    spec = build_chart(_chart("CONFIG columns => 6\n"), ROWS.head(4)).to_dict()

    assert spec["columns"] == 2


@pytest.mark.parametrize(
    ("draw", "mapping"),
    [("bar", "month AS x, revenue AS y"), ("scatter", "month AS x, revenue AS y"), ("histogram", "revenue AS x")],
)
def test_every_chart_with_axes_can_be_faceted_with_its_interactions(draw: str, mapping: str) -> None:
    chart = _chart("INTERACT tooltip, zoom\n", draw=draw, mapping=mapping)

    spec = build_chart(chart, ROWS).to_dict()

    assert spec["facet"]["field"] == "region"
    assert "tooltip" in spec["spec"]["encoding"]
    assert spec["params"], "zoom binds the panels' scales"


def test_downsampling_bins_each_panel_on_its_own() -> None:
    rows = pd.DataFrame(
        {
            "x": list(range(100)) * 2,
            "y": [n % 7 for n in range(200)],
            "region": ["North"] * 100 + ["South"] * 100,
        }
    )
    chart = parse_ggsql("select 1\n\nVISUALISE x AS x, y AS y, region AS facet\nDRAW line\n")

    reduced, _ = downsample_m4(chart, QueryResult.from_dataframe(rows), bins=2)

    regions = reduced.to_arrow().column("region").to_pylist()
    assert {"North", "South"} <= set(regions)


def test_dark_theme_colours_the_panel_names() -> None:
    themed = _apply_dark_vega_theme({"config": {}})

    assert themed["config"]["header"]["labelColor"] == "#f4f4f5"


def test_visual_diff_masks_a_faceted_chart_rather_than_merge_its_panels() -> None:
    metadata = {"chart_type": "line", "x": "month", "y": "revenue", "facet": "region"}
    rows = [{"month": "Jan", "revenue": 1, "region": "North"}]

    assert build_overlay(metadata, rows, rows, config=None) is None


def test_pipeline_records_the_facet(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "by_region.ggsql").write_text(
        "select * from (values ('Jan', 1, 'N'), ('Jan', 2, 'S')) as t(month, revenue, region)\n\n"
        "VISUALISE month AS x, revenue AS y, region AS facet\nDRAW bar\nCONFIG columns => 2\n",
        encoding="utf-8",
    )

    render_project(project)

    metadata = json.loads((project / "target/glyf/charts/by_region.json").read_text(encoding="utf-8"))
    assert (metadata["facet"], metadata["columns"]) == ("region", 2)
