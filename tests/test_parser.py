from pathlib import Path

import pytest

from glyf.ggsql.parser import GgsqlParseError, parse_ggsql


def test_parse_ggsql_extracts_structured_chart() -> None:
    chart = parse_ggsql(
        """SELECT month, revenue
FROM {{ ref('fct_orders') }}

VISUALISE month AS x, revenue AS y
DRAW line
LABEL title => 'Monthly Revenue'
LABEL subtitle => 'Revenue trend from dbt model'
LABEL x_title => 'Month'
LABEL y_title => 'Revenue'
CONFIG width => 900
CONFIG height => 500
""",
        path=Path("revenue.ggsql"),
        name="revenue",
    )

    assert chart.name == "revenue"
    assert chart.sql == "SELECT month, revenue\nFROM {{ ref('fct_orders') }}"
    assert [(item.field, item.role) for item in chart.visualise] == [
        ("month", "x"),
        ("revenue", "y"),
    ]
    assert chart.draw_type == "line"
    assert chart.labels == {
        "title": "Monthly Revenue",
        "subtitle": "Revenue trend from dbt model",
        "x_title": "Month",
        "y_title": "Revenue",
    }
    assert chart.config == {"width": 900, "height": 500}
    assert chart.interactions == ()


def test_parse_ggsql_requires_visualise_section() -> None:
    with pytest.raises(GgsqlParseError, match="missing VISUALISE"):
        parse_ggsql("select 1", name="broken")


def test_parse_ggsql_requires_draw_directive() -> None:
    with pytest.raises(GgsqlParseError, match="missing DRAW"):
        parse_ggsql("select 1\n\nVISUALISE one AS x, two AS y", name="broken")


def test_parse_ggsql_supports_color_mapping() -> None:
    chart = parse_ggsql(
        "select month, revenue, region from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y, region AS color\n"
        "DRAW bar\n",
        name="revenue",
    )

    assert chart.field_for_role("color") == "region"


def test_parse_ggsql_supports_interactions() -> None:
    chart = parse_ggsql(
        "select month, revenue, region from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y, region AS color\n"
        "DRAW scatter\n"
        "INTERACT tooltip, zoom, legend-filter, tooltip\n",
        name="revenue",
    )

    assert chart.interactions == ("tooltip", "zoom", "legend_filter")


def test_parse_ggsql_rejects_unsupported_interaction() -> None:
    with pytest.raises(GgsqlParseError, match="unsupported interaction 'brush'"):
        parse_ggsql(
            "select month, revenue from fct_orders\n\n"
            "VISUALISE month AS x, revenue AS y\n"
            "DRAW scatter\n"
            "INTERACT brush\n",
            name="revenue",
        )


def test_parse_ggsql_rejects_unsupported_chart_type() -> None:
    with pytest.raises(GgsqlParseError, match="unsupported chart type 'violin'"):
        parse_ggsql("select 1\n\nVISUALISE a AS x, b AS y\nDRAW violin\n")


def test_parse_ggsql_rejects_invalid_config_value() -> None:
    with pytest.raises(GgsqlParseError, match="invalid CONFIG width"):
        parse_ggsql(
            "select 1\n\nVISUALISE a AS x, b AS y\nDRAW line\nCONFIG width => wide\n"
        )


def test_parse_ggsql_requires_x_and_y_mappings() -> None:
    with pytest.raises(GgsqlParseError, match="requires x and y mappings"):
        parse_ggsql("select 1\n\nVISUALISE region AS color\nDRAW bar\n")


def test_parse_ggsql_accepts_double_quoted_labels() -> None:
    chart = parse_ggsql(
        "select 1\n\nVISUALISE a AS x, b AS y\nDRAW line\n"
        "LABEL title => \"This month's revenue\"\n"
        "LABEL x_title => 'Month'\n"
    )

    assert chart.title == "This month's revenue"
    assert chart.x_title == "Month"


def test_parse_ggsql_supports_histogram_with_x_alone() -> None:
    chart = parse_ggsql(
        "select amount, region from fct_orders\n\n"
        "VISUALISE amount AS x, region AS color\n"
        "DRAW histogram\n"
    )

    assert chart.draw_type == "histogram"
    assert chart.field_for_role("x") == "amount"
    assert chart.field_for_role("y") is None


def test_parse_ggsql_rejects_histogram_with_y_mapping() -> None:
    with pytest.raises(GgsqlParseError, match="takes no y mapping"):
        parse_ggsql("select 1\n\nVISUALISE a AS x, b AS y\nDRAW histogram\n")


def test_parse_ggsql_supports_boxplot() -> None:
    chart = parse_ggsql("select 1\n\nVISUALISE region AS x, amount AS y\nDRAW boxplot\n")

    assert chart.draw_type == "boxplot"


@pytest.mark.parametrize("draw", ["heatmap", "tile"])
def test_parse_ggsql_supports_heatmap_and_tile_alias(draw: str) -> None:
    chart = parse_ggsql(
        f"select 1\n\nVISUALISE hour AS x, weekday AS y, orders AS color\nDRAW {draw}\n"
    )

    assert chart.draw_type == "heatmap"


def test_parse_ggsql_requires_color_mapping_for_heatmap() -> None:
    with pytest.raises(GgsqlParseError, match="heatmap requires x, y and color"):
        parse_ggsql("select 1\n\nVISUALISE hour AS x, weekday AS y\nDRAW heatmap\n")


@pytest.mark.parametrize(
    ("draw", "mapping"),
    [
        ("boxplot", "region AS x, amount AS y, region AS color"),
        ("heatmap", "hour AS x, weekday AS y, orders AS color"),
    ],
)
def test_parse_ggsql_rejects_legend_filter_where_it_cannot_bind(
    draw: str, mapping: str
) -> None:
    with pytest.raises(
        GgsqlParseError,
        match=f"legend_filter interaction is not supported for {draw} charts",
    ):
        parse_ggsql(
            f"select 1\n\nVISUALISE {mapping}\nDRAW {draw}\nINTERACT legend_filter\n"
        )


def test_parse_ggsql_names_the_chart_the_user_wrote_on_an_unknown_role() -> None:
    # glyf validates the chart block itself (DEC-008). Before, ggsql judged a
    # stand-in and the error read "Layer 'bar' does not support the `banana`
    # mapping" for a pie the user never called a bar.
    with pytest.raises(
        GgsqlParseError, match="^pie does not take a 'banana' mapping; it takes x, y, color$"
    ):
        parse_ggsql(
            "SELECT region, revenue FROM t\n\nVISUALISE region AS x, revenue AS banana\nDRAW pie\n"
        )


def test_parse_ggsql_rejects_a_role_the_renderer_never_drew() -> None:
    with pytest.raises(GgsqlParseError, match="scatter does not take a 'size' mapping"):
        parse_ggsql("SELECT a, b, c FROM t\n\nVISUALISE a AS x, b AS y, c AS size\nDRAW scatter\n")


def test_parse_ggsql_lists_the_supported_chart_types() -> None:
    with pytest.raises(GgsqlParseError, match="supported chart types: area, bar, boxplot"):
        parse_ggsql("SELECT a, b FROM t\n\nVISUALISE a AS x, b AS y\nDRAW donut\n")
