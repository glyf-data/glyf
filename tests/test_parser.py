from pathlib import Path

import pytest

from dbt_charts.ggsql.parser import GgsqlParseError, parse_ggsql


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


def test_parse_ggsql_rejects_unsupported_chart_type() -> None:
    with pytest.raises(GgsqlParseError, match="unsupported chart type 'heatmap'"):
        parse_ggsql("select 1\n\nVISUALISE a AS x, b AS y\nDRAW heatmap\n")


def test_parse_ggsql_rejects_invalid_config_value() -> None:
    with pytest.raises(GgsqlParseError, match="invalid CONFIG width"):
        parse_ggsql(
            "select 1\n\nVISUALISE a AS x, b AS y\nDRAW line\nCONFIG width => wide\n"
        )


def test_parse_ggsql_requires_x_and_y_mappings() -> None:
    with pytest.raises(GgsqlParseError, match="requires x and y mappings"):
        parse_ggsql("select 1\n\nVISUALISE region AS color\nDRAW bar\n")
