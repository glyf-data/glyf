"""Ties a query's ORDER BY leaves are settled, and its order is not touched.

`ORDER BY half` says nothing about two rows in the same half, so the
warehouse may return them either way round, and under a LIMIT it may keep a
different row. glyf appends the query's other columns to its ORDER BY; these
tests pin that the author's order holds, the ties settle, and the build says
so only when there were ties to settle.
"""

from pathlib import Path

import pyarrow as pa
import pytest

import glyf.pipeline as pipeline
from glyf.execution.result import QueryResult
from glyf.ggsql.models import OrderTiebreak
from glyf.ggsql.parser import order_tiebreak
from glyf.ordering import settle_ties
from glyf.pipeline import render_project
from glyf.provenance import sql_digest
from tests.helpers import copy_basic_project

HALVES = (
    "SELECT CASE WHEN month < '2026-03' THEN 'early' ELSE 'late' END AS half,\n"
    "  month, revenue\n"
    "FROM {{ ref('fct_orders') }}\n"
    "ORDER BY half DESC\n"
    "LIMIT 3"
)


def _table_chart(project: Path, sql: str) -> Path:
    path = project / "visualisations" / "halves.ggsql"
    path.write_text(f"{sql}\n\nVISUALISE *\nDRAW table\n", encoding="utf-8")
    return path


def test_the_core_answers_through_the_wrapper() -> None:
    tiebreak = order_tiebreak(
        "SELECT plan, sessions FROM t ORDER BY sessions DESC LIMIT 10", dialect="duckdb"
    )

    assert tiebreak.sql == "SELECT plan, sessions FROM t ORDER BY sessions DESC, plan LIMIT 10"
    assert (tiebreak.added, tiebreak.keys, tiebreak.limited) == (("plan",), ("sessions",), True)
    assert order_tiebreak("SELECT a FROM t", dialect="duckdb") == OrderTiebreak()


def test_settling_sorts_inside_a_tie_and_never_across_one() -> None:
    # Descending on plan, as the warehouse returned it; Team's rows tie.
    rows = pa.table(
        {"plan": ["Team", "Team", "Pro", "Free", "Free"], "n": [9, 3, 5, 2, 1]}
    )
    tiebreak = OrderTiebreak(keys=("plan",), added=("n",))

    settled, settlement = settle_ties(QueryResult.from_arrow(rows), tiebreak, applied=False)

    table = settled.to_arrow()
    assert table.column("plan").to_pylist() == ["Team", "Team", "Pro", "Free", "Free"]
    assert table.column("n").to_pylist() == [3, 9, 5, 1, 2]
    assert settlement.tied and settlement.by == "rows"


def test_identical_rows_are_not_a_tie() -> None:
    """Two rows equal in every column draw one mark twice; order cannot show."""
    rows = pa.table({"minutes": [4.0, 4.0, 7.5], "plan": ["Pro", "Pro", "Team"]})
    tiebreak = OrderTiebreak(keys=("minutes", "plan"))

    _, settlement = settle_ties(QueryResult.from_arrow(rows), tiebreak, applied=False)

    assert not settlement.tied


def test_no_ties_means_nothing_to_say() -> None:
    rows = pa.table({"plan": ["Team", "Pro"], "n": [1, 2]})
    tiebreak = OrderTiebreak(keys=("PLAN",), added=("n",))

    settled, settlement = settle_ties(QueryResult.from_arrow(rows), tiebreak, applied=True)

    assert not settlement.tied
    assert settled.to_arrow() == rows


def test_a_limit_keeps_the_same_rows_and_the_build_says_why(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    _table_chart(project, HALVES)

    result = render_project(project)

    (chart,) = [c for c in result.charts if c.chart.name == "halves"]
    rows = chart.data.to_arrow().to_pylist()
    # The author's order holds: late before early. Inside 'late' the tie is
    # settled by month, so the LIMIT keeps the same two rows every build.
    assert [row["half"] for row in rows] == ["late", "late", "early"]
    assert [row["month"] for row in rows] == ["2026-03", "2026-04", "2026-01"]

    compiled = (project / "target" / "glyf" / "compiled" / "halves.sql").read_text(encoding="utf-8")
    assert "ORDER BY half DESC, month, revenue\nLIMIT 3" in compiled
    assert chart.compiled_sql.strip() == compiled.strip(), "the source view shows what ran"

    warning = [w for w in result.warnings if "halves.ggsql" in w and "tie" in w]
    assert warning and "glyf added month, revenue" in warning[0], result.warnings


def test_the_record_hashes_the_query_as_written(tmp_path: Path) -> None:
    """Upgrading glyf must not read as every partially ordered query changing."""
    project = copy_basic_project(tmp_path)
    _table_chart(project, HALVES)

    result = render_project(project)

    (record,) = [c for c in result.build.charts if c.name == "halves"]
    (chart,) = [c for c in result.charts if c.chart.name == "halves"]
    assert "ORDER BY half DESC, month" in chart.compiled_sql
    assert record.compiled_sql_sha256 != sql_digest(chart.compiled_sql)
    assert record.compiled_sql_sha256 == sql_digest(
        chart.compiled_sql.replace("ORDER BY half DESC, month, revenue", "ORDER BY half DESC")
    )


def test_a_fully_ordered_query_runs_as_written(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    _table_chart(project, "SELECT month, revenue FROM {{ ref('fct_orders') }} ORDER BY month, revenue")

    result = render_project(project)

    (chart,) = [c for c in result.charts if c.chart.name == "halves"]
    assert chart.compiled_sql.rstrip().endswith("ORDER BY month, revenue")
    assert not [w for w in result.warnings if "halves.ggsql" in w], result.warnings


def test_a_refused_tiebreak_falls_back_to_the_query_as_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = copy_basic_project(tmp_path)
    _table_chart(project, HALVES)
    real = pipeline.execute_sql

    def refuse_tiebreaks(root, sql, **kwargs):
        if "ORDER BY half DESC, month" in sql:
            raise pipeline.SqlExecutionError("cannot order by that type")
        return real(root, sql, **kwargs)

    monkeypatch.setattr(pipeline, "execute_sql", refuse_tiebreaks)

    result = render_project(project)

    (chart,) = [c for c in result.charts if c.chart.name == "halves"]
    assert "ORDER BY half DESC\nLIMIT 3" in chart.compiled_sql
    compiled = (project / "target" / "glyf" / "compiled" / "halves.sql").read_text(encoding="utf-8")
    assert "ORDER BY half DESC\nLIMIT 3" in compiled
    assert [w for w in result.warnings if "could not order by the tiebreak" in w], result.warnings


def test_select_star_settles_after_the_rows_come_back_and_names_the_limit(
    tmp_path: Path,
) -> None:
    project = copy_basic_project(tmp_path)
    _table_chart(
        project,
        "SELECT * FROM (\n  SELECT CASE WHEN month < '2026-03' THEN 'early' ELSE 'late' END AS half,\n"
        "    month, revenue FROM {{ ref('fct_orders') }}\n) AS t\nORDER BY half\nLIMIT 3",
    )

    result = render_project(project)

    (chart,) = [c for c in result.charts if c.chart.name == "halves"]
    rows = chart.data.to_arrow().to_pylist()
    assert [row["month"] for row in rows[:2]] == ["2026-01", "2026-02"]
    warning = [w for w in result.warnings if "halves.ggsql" in w and "tie" in w]
    assert warning and "cannot choose which rows the LIMIT keeps" in warning[0], result.warnings
