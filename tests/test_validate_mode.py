"""Bounding what a chart query returns.

Two bounds, one mechanism (`glyf.execution.limits.wrap_row_limit`):

* validate mode runs every query with `limit 0` and draws nothing, so CI can
  prove the SQL still runs and binds its columns without paying for the data;
* `execution.max_rows` fails a normal build that exceeds it, rather than
  drawing a chart from part of a result.

Nothing in the render path bounded anything before this. Altair carries a
5,000-row cap, but `altair/utils/save.py` explicitly disables it while saving
(vl-convert needs the data inlined), which is the path glyf renders through --
so the cap never applied here.
"""

from dataclasses import replace
from pathlib import Path

import pytest

from typer.testing import CliRunner

from glyf.cli import app
from glyf.config import ExecutionConfig, GlyfConfig
from glyf.execution.limits import wrap_row_limit
from glyf.pipeline import RenderError, render_project
from tests.helpers import copy_basic_project

CHART_SQL = "select month, revenue from {{ ref('fct_orders') }}"

runner = CliRunner()


def test_wrap_row_limit_bounds_a_query() -> None:
    wrapped = wrap_row_limit("select 1", 0)

    assert wrapped.endswith("limit 0")
    assert "select 1" in wrapped


def test_wrap_row_limit_survives_a_trailing_clause() -> None:
    """A bare appended `limit` would attach to the inner order by."""
    wrapped = wrap_row_limit("select month from t order by month;", 5)

    assert wrapped.endswith("limit 5")
    assert "order by month" in wrapped
    assert ";" not in wrapped


def test_wrap_row_limit_rejects_a_negative_bound() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        wrap_row_limit("select 1", -1)


def test_validate_mode_writes_no_chart_artifacts(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = render_project(project, _config(mode="validate"))

    assert result.validated_only is True
    assert len(result.charts) == 1
    charts_dir = project / "target" / "glyf" / "charts"
    assert not list(charts_dir.glob("*.png"))
    assert not list(charts_dir.glob("*.svg"))
    assert not list((project / "target" / "glyf" / "data" / "normalized").glob("*.json"))


def test_validate_mode_still_writes_the_compiled_sql(tmp_path: Path) -> None:
    """The artifact on disk is the query as written, never the bounded form."""
    project = copy_basic_project(tmp_path)

    render_project(project, _config(mode="validate"))

    compiled = (project / "target" / "glyf" / "compiled" / "revenue.sql").read_text()
    assert "limit 0" not in compiled.lower()
    assert "fct_orders" in compiled


def test_validate_mode_fetches_no_rows(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = render_project(project, _config(mode="validate"))

    data = result.charts[0].data
    assert len(data) == 0
    assert data.columns == ("month", "revenue"), "columns come back without rows"


def test_validate_mode_catches_a_column_the_chart_binds_but_sql_lacks(
    tmp_path: Path,
) -> None:
    """The point of validate mode: a rename in the model breaks CI here."""
    project = copy_basic_project(tmp_path)
    _write_chart(project, "select month, revenue as takings from {{ ref('fct_orders') }}")

    with pytest.raises(RenderError, match="missing chart column 'revenue'"):
        render_project(project, _config(mode="validate"))


def test_validate_mode_reports_sql_that_does_not_run(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    _write_chart(project, "select month, no_such_column from {{ ref('fct_orders') }}")

    with pytest.raises(RenderError, match="SQL execution failed"):
        render_project(project, _config(mode="validate"))


def test_max_rows_fails_a_build_that_exceeds_it(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    with pytest.raises(RenderError, match="returned more than 2 rows"):
        render_project(project, _config(max_rows=2))


def test_max_rows_error_says_what_to_do(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    with pytest.raises(RenderError) as error:
        render_project(project, _config(max_rows=1))

    message = str(error.value)
    assert "Aggregate the query or raise execution.max_rows" in message
    assert "will not" in message, "the build must not silently draw partial data"


def test_max_rows_allows_a_result_that_exactly_fills_it(tmp_path: Path) -> None:
    """The fixture has four rows; a cap of four is not an overflow."""
    project = copy_basic_project(tmp_path)

    result = render_project(project, _config(max_rows=4))

    assert len(result.charts[0].data) == 4
    assert (project / "target" / "glyf" / "charts" / "revenue.png").exists()


def test_max_rows_is_unset_by_default(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = render_project(project, GlyfConfig())

    assert result.validated_only is False
    assert len(result.charts[0].data) == 4
    assert (project / "target" / "glyf" / "charts" / "revenue.svg").exists()


def test_render_validate_flag_says_what_it_skipped(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = runner.invoke(app, ["render", "--project-dir", str(project), "--validate"])

    assert result.exit_code == 0, result.output
    assert "checked SQL and chart columns (no rows fetched)" in result.output
    assert "skipped chart artifacts" in result.output
    assert "rendered PNG/SVG" not in result.output


def test_build_validate_flag_stops_before_dashboards(tmp_path: Path) -> None:
    """Nothing was drawn, so there is nothing to assemble or publish."""
    project = copy_basic_project(tmp_path)

    result = runner.invoke(app, ["build", "--project-dir", str(project), "--validate"])

    assert result.exit_code == 0, result.output
    assert "skipped dashboard and export (validate mode)" in result.output
    assert not (project / "target" / "glyf" / "site").exists()
    assert not (project / "target" / "glyf" / "dashboards").exists()


def test_build_validate_flag_fails_on_a_broken_chart(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    _write_chart(project, "select month, revenue as takings from {{ ref('fct_orders') }}")

    result = runner.invoke(app, ["build", "--project-dir", str(project), "--validate"])

    assert result.exit_code == 1
    assert "missing chart column 'revenue'" in result.output


def _config(*, mode: str = "full", max_rows: int | None = None) -> GlyfConfig:
    return replace(
        GlyfConfig(),
        execution=ExecutionConfig(mode=mode, max_rows=max_rows),
    )


def _write_chart(project: Path, sql: str) -> None:
    (project / "visualisations" / "revenue.ggsql").write_text(
        f"{sql}\n\nVISUALISE month AS x, revenue AS y\nDRAW line\n"
        "LABEL title => 'Monthly Revenue'\n",
        encoding="utf-8",
    )
