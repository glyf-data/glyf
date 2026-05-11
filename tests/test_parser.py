from pathlib import Path

import pytest

from dbt_ggsql.ggsql.parser import GgsqlParseError, parse_ggsql


def test_parse_ggsql_extracts_structured_chart() -> None:
    chart = parse_ggsql(
        """SELECT month, revenue
FROM {{ ref('fct_orders') }}

VISUALISE month AS x, revenue AS y
DRAW line
LABEL title => 'Monthly Revenue'
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
    assert chart.labels == {"title": "Monthly Revenue"}


def test_parse_ggsql_requires_visualise_section() -> None:
    with pytest.raises(GgsqlParseError, match="missing VISUALISE"):
        parse_ggsql("select 1", name="broken")


def test_parse_ggsql_requires_draw_directive() -> None:
    with pytest.raises(GgsqlParseError, match="missing DRAW"):
        parse_ggsql("select 1\n\nVISUALISE one AS x", name="broken")
