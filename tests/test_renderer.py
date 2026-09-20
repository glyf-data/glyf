import json
from pathlib import Path
import re

import pandas as pd
import polars as pl
import pytest

from glyf.config import RenderConfig
from glyf.ggsql.parser import SUPPORTED_CHART_TYPES, GgsqlParseError, parse_ggsql
from glyf.ggsql.renderer import CHART_TYPES, ChartRenderError, render_chart
from glyf.renderers import chart_renderer


def test_render_chart_writes_png_and_svg(tmp_path: Path) -> None:
    chart = parse_ggsql(
        "select month, revenue from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW bar\n"
        "LABEL title => 'Monthly Revenue'\n",
        name="revenue",
    )
    data = pl.DataFrame(
        {
            "month": ["2026-01", "2026-02"],
            "revenue": [1200, 1800],
        }
    )
    png_path = tmp_path / "revenue.png"
    svg_path = tmp_path / "revenue.svg"

    render_chart(chart, data, png_path, svg_path)

    assert png_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    svg = svg_path.read_text(encoding="utf-8")
    assert "<svg" in svg
    width = int(re.search(r'width="(\d+)"', svg).group(1))
    height = int(re.search(r'height="(\d+)"', svg).group(1))
    assert width >= 800
    assert height >= 400


def test_render_chart_rejects_unsupported_chart_type(tmp_path: Path) -> None:
    with pytest.raises(GgsqlParseError, match="unsupported chart type 'violin'"):
        parse_ggsql(
            "select month, revenue from fct_orders\n\n"
            "VISUALISE month AS x, revenue AS y\n"
            "DRAW violin\n",
            name="revenue",
        )


def test_render_chart_supports_area_pie_scatter_and_color(tmp_path: Path) -> None:
    data = pd.DataFrame(
        {
            "month": ["2026-01", "2026-02"],
            "region": ["North", "South"],
            "revenue": [1200, 1800],
        }
    )
    chart_types = ["area", "pie", "scatter"]

    for chart_type in chart_types:
        chart = parse_ggsql(
            "select month, region, revenue from fct_orders\n\n"
            "VISUALISE month AS x, revenue AS y, region AS color\n"
            f"DRAW {chart_type}\n"
            "LABEL title => 'Revenue'\n"
            "LABEL subtitle => 'By region'\n"
            "LABEL x_title => 'Month'\n"
            "LABEL y_title => 'Revenue'\n"
            "CONFIG width => 500\n"
            "CONFIG height => 300\n",
            name=f"revenue_{chart_type}",
        )
        png_path = tmp_path / f"{chart_type}.png"
        svg_path = tmp_path / f"{chart_type}.svg"

        render_chart(chart, data, png_path, svg_path)

        assert png_path.exists()
        assert svg_path.exists()
        assert "Revenue" in svg_path.read_text(encoding="utf-8")


def test_render_chart_reports_missing_color_column(tmp_path: Path) -> None:
    chart = parse_ggsql(
        "select month, revenue from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y, region AS color\n"
        "DRAW bar\n",
        name="revenue",
    )
    data = pd.DataFrame({"month": ["2026-01"], "revenue": [1200]})

    with pytest.raises(ChartRenderError, match="query result missing chart column 'region'"):
        render_chart(chart, data, tmp_path / "revenue.png", tmp_path / "revenue.svg")


def test_render_chart_writes_vega_json_for_interactive_chart(tmp_path: Path) -> None:
    chart = parse_ggsql(
        "select month, revenue, region from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y, region AS color\n"
        "DRAW scatter\n"
        "INTERACT tooltip, zoom, legend_filter\n",
        name="revenue",
    )
    data = pd.DataFrame(
        {
            "month": ["2026-01", "2026-02"],
            "region": ["North", "South"],
            "revenue": [1200, 1800],
        }
    )
    vega_json_path = tmp_path / "revenue.vega.json"

    render_chart(
        chart,
        data,
        tmp_path / "revenue.png",
        tmp_path / "revenue.svg",
        vega_json_path=vega_json_path,
    )

    spec = vega_json_path.read_text(encoding="utf-8")
    assert '"tooltip"' in spec
    assert '"params"' in spec
    assert '"bind": "legend"' in spec


def test_render_chart_reports_legend_filter_without_color_mapping(tmp_path: Path) -> None:
    chart = parse_ggsql(
        "select month, revenue from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW scatter\n"
        "INTERACT legend_filter\n",
        name="revenue",
    )
    data = pd.DataFrame({"month": ["2026-01"], "revenue": [1200]})

    with pytest.raises(ChartRenderError, match="requires a color mapping"):
        render_chart(
            chart,
            data,
            tmp_path / "revenue.png",
            tmp_path / "revenue.svg",
            vega_json_path=tmp_path / "revenue.vega.json",
        )


def test_render_chart_uses_custom_python_renderer(tmp_path: Path) -> None:
    @chart_renderer("test_custom_renderer")
    def custom_renderer(
        chart,
        data,
        png_path,
        svg_path,
        config,
        vega_json_path,
    ) -> None:
        png_path.write_text(chart.name, encoding="utf-8")
        svg_path.write_text(str(len(data)), encoding="utf-8")

    chart = parse_ggsql(
        "select month, revenue from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW line\n",
        name="custom_revenue",
    )
    data = pd.DataFrame({"month": ["2026-01"], "revenue": [1200]})

    render_chart(
        chart,
        data,
        tmp_path / "custom.txt",
        tmp_path / "custom.svg",
        RenderConfig(renderer="test-custom-renderer"),
    )

    assert (tmp_path / "custom.txt").read_text(encoding="utf-8") == "custom_revenue"
    assert (tmp_path / "custom.svg").read_text(encoding="utf-8") == "1"


def _render_spec(tmp_path: Path, text: str, data: pd.DataFrame) -> dict[str, object]:
    chart = parse_ggsql(text, name="chart")
    vega_json_path = tmp_path / "chart.vega.json"
    render_chart(
        chart,
        data,
        tmp_path / "chart.png",
        tmp_path / "chart.svg",
        vega_json_path=vega_json_path,
    )
    assert (tmp_path / "chart.png").read_bytes().startswith(b"\x89PNG")
    assert "<svg" in (tmp_path / "chart.svg").read_text(encoding="utf-8")
    return json.loads(vega_json_path.read_text(encoding="utf-8"))


def test_render_chart_bins_and_counts_a_histogram(tmp_path: Path) -> None:
    spec = _render_spec(
        tmp_path,
        "select amount, region from fct_orders\n\n"
        "VISUALISE amount AS x, region AS color\n"
        "DRAW histogram\n"
        "INTERACT tooltip, legend_filter\n",
        pd.DataFrame(
            {
                "amount": [12.0, 14.5, 18.0, 40.0, 41.5, 90.0],
                "region": ["North", "North", "South", "South", "North", "South"],
            }
        ),
    )

    encoding = spec["encoding"]
    assert spec["mark"]["type"] == "bar"
    assert encoding["x"]["field"] == "amount"
    assert encoding["x"]["bin"] == {"maxbins": 30}
    assert encoding["y"]["aggregate"] == "count"
    assert "field" not in encoding["y"]
    assert encoding["color"]["field"] == "region"
    # The tooltip describes the bar -- a bin and its count -- not a row.
    assert [item.get("aggregate", item.get("field")) for item in encoding["tooltip"]] == [
        "amount",
        "count",
        "region",
    ]


def test_render_chart_draws_a_boxplot_with_its_own_tooltip(tmp_path: Path) -> None:
    spec = _render_spec(
        tmp_path,
        "select region, amount from fct_orders\n\n"
        "VISUALISE region AS x, amount AS y\n"
        "DRAW boxplot\n"
        "INTERACT tooltip\n",
        pd.DataFrame(
            {
                "region": ["North"] * 5 + ["South"] * 5,
                "amount": [10, 12, 13, 15, 60, 20, 22, 23, 25, 27],
            }
        ),
    )

    assert spec["mark"]["type"] == "boxplot"
    # Two categories across the default 800 pixels, capped.
    assert spec["mark"]["size"] == 80
    assert spec["encoding"]["x"]["field"] == "region"
    assert spec["encoding"]["y"]["field"] == "amount"
    # The tooltip reads "Median of <y title>", so the title is never null.
    assert spec["encoding"]["y"]["title"] == "amount"
    # A row-field tooltip would replace the quartile summary the mark provides.
    assert "tooltip" not in spec["encoding"]


def test_render_chart_draws_a_heatmap_in_query_order(tmp_path: Path) -> None:
    spec = _render_spec(
        tmp_path,
        "select hour, weekday, orders from fct_orders\n\n"
        "VISUALISE hour AS x, weekday AS y, orders AS color\n"
        "DRAW heatmap\n"
        "INTERACT tooltip\n",
        pd.DataFrame(
            {
                "hour": [9, 10, 9, 10],
                "weekday": ["Mon", "Mon", "Tue", "Tue"],
                "orders": [4, 9, 2, 7],
            }
        ),
    )

    encoding = spec["encoding"]
    assert spec["mark"]["type"] == "rect"
    assert encoding["x"]["type"] == "ordinal"
    assert encoding["y"]["type"] == "ordinal"
    # Alphabetical order would put Friday first; the query's order stands.
    assert encoding["x"]["sort"] is None
    assert encoding["y"]["sort"] is None
    assert encoding["color"] == {"field": "orders", "type": "quantitative"}
    assert [item["field"] for item in encoding["tooltip"]] == ["hour", "weekday", "orders"]


@pytest.mark.parametrize(
    ("draw", "mapping", "message"),
    [
        ("histogram", "region AS x", "histogram needs a numeric x column and 'region' is"),
        ("boxplot", "month AS x, region AS y", "boxplot needs a numeric y column and 'region' is"),
        (
            "heatmap",
            "month AS x, revenue AS y, region AS color",
            "heatmap needs a numeric color column and 'region' is",
        ),
    ],
)
def test_render_chart_reports_a_text_column_where_a_number_is_computed(
    tmp_path: Path, draw: str, mapping: str, message: str
) -> None:
    chart = parse_ggsql(f"select 1\n\nVISUALISE {mapping}\nDRAW {draw}\n", name="chart")
    data = pd.DataFrame(
        {"month": ["2026-01", "2026-02"], "region": ["North", "South"], "revenue": [1, 2]}
    )

    with pytest.raises(ChartRenderError, match=message):
        render_chart(chart, data, tmp_path / "chart.png", tmp_path / "chart.svg")


def test_every_chart_type_the_parser_accepts_can_be_drawn() -> None:
    """The parser's list and the renderer's table are two statements of one fact.

    A type added to one and not the other parses and then fails to render, or
    is drawable and never reachable.
    """
    assert set(CHART_TYPES) == SUPPORTED_CHART_TYPES
