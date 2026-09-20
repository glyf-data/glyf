"""A chart draws the same picture every build.

Without an ORDER BY the warehouse may return the rows in any order, and for a
stacked bar, a pie, a coloured scatter or a heatmap that order is the picture.
These tests pin both halves of the rule: glyf orders the rows when the query
did not, and never when it did.
"""

from pathlib import Path

import pyarrow as pa
import pytest

from glyf.execution.result import QueryResult
from glyf.ggsql.parser import parse_ggsql
from glyf.ordering import is_order_sensitive, order_rows
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

SHUFFLED = pa.table(
    {
        "month": ["2026-03", "2026-01", "2026-02", "2026-01"],
        "revenue": [300, 100, 200, 150],
        "region": ["South", "South", "North", "North"],
    }
)


def _chart(sql: str, draw: str = "bar", mapping: str = "month AS x, revenue AS y, region AS color"):
    return parse_ggsql(f"{sql}\n\nVISUALISE {mapping}\nDRAW {draw}\n", name="chart")


def test_rows_are_ordered_when_the_query_does_not_order_them() -> None:
    chart = _chart("SELECT month, revenue, region FROM fct_orders")
    data = QueryResult.from_arrow(SHUFFLED)

    ordered, plan = order_rows(chart, data)

    assert plan.applied
    # Encoded columns first, in the order the chart binds them.
    assert plan.columns == ("month", "revenue", "region")
    rows = ordered.to_arrow().to_pylist()
    assert [row["month"] for row in rows] == ["2026-01", "2026-01", "2026-02", "2026-03"]
    # The tie on month is broken by revenue, so it cannot fall either way.
    assert [row["revenue"] for row in rows[:2]] == [100, 150]


def test_rows_are_left_alone_when_the_query_orders_them() -> None:
    chart = _chart("SELECT month, revenue, region FROM fct_orders ORDER BY month DESC")
    data = QueryResult.from_arrow(SHUFFLED)

    ordered, plan = order_rows(chart, data)

    assert not plan.applied
    assert plan.describe("chart.ggsql") == "chart.ggsql: "
    assert ordered.to_arrow() == SHUFFLED


def test_ordering_is_reported_against_the_file() -> None:
    chart = _chart("SELECT month, revenue, region FROM fct_orders")

    _, plan = order_rows(chart, QueryResult.from_arrow(SHUFFLED))

    message = plan.describe("visualisations/revenue.ggsql")
    assert message.startswith("visualisations/revenue.ggsql: the query has no ORDER BY")
    assert "ordered the rows by month, revenue, region" in message
    assert "Add an ORDER BY to choose the order yourself." in message


@pytest.mark.parametrize(
    ("draw", "mapping", "sensitive"),
    [
        # The row order is the stack order, the slice order, or the axes.
        ("bar", "month AS x, revenue AS y, region AS color", True),
        ("area", "month AS x, revenue AS y, region AS color", True),
        ("histogram", "revenue AS x, region AS color", True),
        ("scatter", "month AS x, revenue AS y, region AS color", True),
        ("pie", "region AS x, revenue AS y", True),
        ("heatmap", "month AS x, region AS y, revenue AS color", True),
        # Drawn along the x axis, or from every row at once, whatever the order.
        ("line", "month AS x, revenue AS y, region AS color", False),
        ("line", "month AS x, revenue AS y", False),
        ("bar", "month AS x, revenue AS y", False),
        ("boxplot", "region AS x, revenue AS y", False),
    ],
)
def test_only_charts_whose_picture_shows_the_order_are_reported(
    draw: str, mapping: str, sensitive: bool
) -> None:
    chart = _chart("SELECT month, revenue, region FROM fct_orders", draw, mapping)

    assert is_order_sensitive(chart) is sensitive


def test_unsortable_columns_are_reported_rather_than_ordered() -> None:
    chart = _chart(
        "SELECT month, revenue FROM fct_orders",
        "line",
        "month AS x, revenue AS y",
    )
    nested = pa.table({"month": [[1], [2]], "revenue": [[3], [4]]})

    ordered, plan = order_rows(chart, QueryResult.from_arrow(nested))

    assert not plan.applied
    assert "none of its columns can be ordered" in plan.describe("chart.ggsql")
    assert ordered.to_arrow() == nested


def test_a_build_renders_the_same_bytes_twice(tmp_path: Path) -> None:
    """The point of all of the above, end to end."""
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "SELECT month, revenue\nFROM {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\nDRAW bar\nLABEL title => 'Revenue'\n",
        encoding="utf-8",
    )

    render_project(project)
    first = (project / "target" / "glyf" / "charts" / "revenue.svg").read_bytes()
    render_project(project)
    second = (project / "target" / "glyf" / "charts" / "revenue.svg").read_bytes()

    assert first == second


def test_a_build_reports_the_order_it_chose(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "SELECT month, revenue\nFROM {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y, month AS color\n"
        "DRAW bar\nLABEL title => 'Revenue'\n",
        encoding="utf-8",
    )

    result = render_project(project)

    assert [w for w in result.warnings if "no ORDER BY" in w], result.warnings


def test_a_build_says_nothing_when_the_query_orders_itself(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "SELECT month, revenue\nFROM {{ ref('fct_orders') }}\nORDER BY month\n\n"
        "VISUALISE month AS x, revenue AS y, month AS color\n"
        "DRAW bar\nLABEL title => 'Revenue'\n",
        encoding="utf-8",
    )

    result = render_project(project)

    assert not [w for w in result.warnings if "ORDER BY" in w], result.warnings
