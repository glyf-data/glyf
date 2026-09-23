"""`glyf impact`: which charts and dashboards a model or column change touches.

The model answer is exact, from the resolved refs. The column answer is
honest rather than exact: a query that names the column reads it, one that
selects `*` may read it, one whose SQL did not parse may read it too, and
every line says which.
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyf.cli import app
from glyf.config import GlyfConfig
from glyf.impact import ImpactError, compute_impact
from tests.helpers import copy_simple_dbt_project

runner = CliRunner()


def _project(tmp_path: Path) -> Path:
    project = copy_simple_dbt_project(tmp_path)
    charts = project / "visualisations"
    for stale in charts.glob("*.ggsql"):
        stale.unlink()
    (charts / "revenue.ggsql").write_text(
        "SELECT month, revenue FROM {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\nDRAW line\n",
        encoding="utf-8",
    )
    (charts / "margin.ggsql").write_text(
        "SELECT o.month, o.revenue - o.cost AS margin FROM {{ ref('fct_orders') }} o\n\n"
        "VISUALISE month AS x, margin AS y\nDRAW bar\n",
        encoding="utf-8",
    )
    (charts / "everything.ggsql").write_text(
        "SELECT * FROM {{ ref('fct_orders') }}\n\nVISUALISE *\nDRAW table\n",
        encoding="utf-8",
    )
    (charts / "raw_orders.ggsql").write_text(
        "SELECT order_id, amount FROM {{ source('raw', 'orders') }}\n\n"
        "VISUALISE order_id AS x, amount AS y\nDRAW bar\n",
        encoding="utf-8",
    )
    (charts / "broken.ggsql").write_text(
        "SELECT month revenue cost FROM {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\nDRAW bar\n",
        encoding="utf-8",
    )
    dashboards = project / "dashboards"
    for stale in dashboards.glob("*.yml"):
        stale.unlink()
    (dashboards / "finance.yml").write_text(
        "name: finance\ntitle: Finance\ncharts:\n  - revenue\n  - margin\n  - everything\n",
        encoding="utf-8",
    )
    (dashboards / "ops.yml").write_text(
        "name: ops\ntitle: Ops\ncharts:\n  - raw_orders\n  - revenue\n", encoding="utf-8"
    )
    return project


def test_a_model_lists_every_chart_that_refs_it_and_their_dashboards(tmp_path: Path) -> None:
    report = compute_impact(_project(tmp_path), GlyfConfig(), "fct_orders")

    assert report.target.kind == "model"
    assert [(c.name, c.certainty, c.detail) for c in report.charts] == [
        ("broken", "reads", "ref('fct_orders')"),
        ("everything", "reads", "ref('fct_orders')"),
        ("margin", "reads", "ref('fct_orders')"),
        ("revenue", "reads", "ref('fct_orders')"),
    ]
    assert next(c for c in report.charts if c.name == "revenue").dashboards == ("finance", "ops")
    assert report.dashboards == ("finance", "ops")
    assert report.headline() == "fct_orders is read by 4 charts on 2 dashboards"


def test_a_source_is_named_the_way_the_chart_names_it(tmp_path: Path) -> None:
    report = compute_impact(_project(tmp_path), GlyfConfig(), "raw.orders")

    assert report.target.kind == "source"
    assert [(c.name, c.detail, c.dashboards) for c in report.charts] == [
        ("raw_orders", "source('raw', 'orders')", ("ops",))
    ]


def test_a_column_says_how_sure_it_is_for_each_chart(tmp_path: Path) -> None:
    report = compute_impact(_project(tmp_path), GlyfConfig(), "fct_orders.revenue")

    assert report.target == report.target.__class__(kind="column", relation="fct_orders", column="revenue")
    assert [(c.name, c.certainty, c.detail) for c in report.charts] == [
        ("broken", "may read", "SQL did not parse"),
        ("everything", "may read", "SELECT *"),
        ("margin", "reads", "in the SQL"),
        ("revenue", "reads", "revenue AS y"),
    ]
    assert report.headline() == "fct_orders.revenue is read by 4 charts on 2 dashboards (2 may read it)"


def test_a_column_a_chart_never_mentions_leaves_it_out(tmp_path: Path) -> None:
    report = compute_impact(_project(tmp_path), GlyfConfig(), "fct_orders.cost")

    assert [(c.name, c.certainty) for c in report.charts] == [
        ("broken", "may read"),
        ("everything", "may read"),
        ("margin", "reads"),
    ]


def test_a_column_of_a_source_works_the_same_way(tmp_path: Path) -> None:
    report = compute_impact(_project(tmp_path), GlyfConfig(), "raw.orders.amount")

    assert report.target.relation == "raw.orders" and report.target.column == "amount"
    assert [(c.name, c.detail) for c in report.charts] == [("raw_orders", "amount AS y")]


def test_a_column_match_ignores_case_and_table_aliases(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "visualisations" / "margin.ggsql").write_text(
        "SELECT o.Month, o.REVENUE - o.cost AS margin FROM {{ ref('fct_orders') }} o\n\n"
        "VISUALISE month AS x, margin AS y\nDRAW bar\n",
        encoding="utf-8",
    )

    report = compute_impact(project, GlyfConfig(), "fct_orders.Revenue")

    assert ("margin", "reads") in [(c.name, c.certainty) for c in report.charts]


def test_an_unknown_target_says_what_it_takes_and_suggests_a_name(tmp_path: Path) -> None:
    project = _project(tmp_path)
    with pytest.raises(ImpactError, match="not a model, a source or a column.*Did you mean fct_orders"):
        compute_impact(project, GlyfConfig(), "fct_order")
    with pytest.raises(ImpactError, match="not a model"):
        compute_impact(project, GlyfConfig(), "nothing_here.column")


def test_no_chart_reads_it_is_a_plain_answer(tmp_path: Path) -> None:
    project = _project(tmp_path)
    for chart in ("revenue", "margin", "everything", "broken"):
        (project / "visualisations" / f"{chart}.ggsql").unlink()

    report = compute_impact(project, GlyfConfig(), "fct_orders")

    assert report.charts == ()
    assert report.headline() == "fct_orders is read by no chart"


def test_the_command_prints_a_table_and_json(tmp_path: Path) -> None:
    project = _project(tmp_path)

    result = runner.invoke(app, ["impact", "fct_orders.revenue", "--project-dir", str(project)])

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == "fct_orders.revenue is read by 4 charts on 2 dashboards (2 may read it)"
    assert any("visualisations/revenue.ggsql" in line and "revenue AS y" in line and "finance, ops" in line for line in lines)
    assert any("visualisations/everything.ggsql" in line and "SELECT *, may read" in line for line in lines)

    as_json = runner.invoke(app, ["impact", "fct_orders", "--project-dir", str(project), "--json"])
    document = json.loads(as_json.output)
    assert document["target"] == {"kind": "model", "relation": "fct_orders", "column": None}
    assert [chart["name"] for chart in document["charts"]] == ["broken", "everything", "margin", "revenue"]
    assert document["dashboards"] == ["finance", "ops"]

    unknown = runner.invoke(app, ["impact", "nope", "--project-dir", str(project)])
    assert unknown.exit_code == 1 and "Impact failed" in unknown.output
