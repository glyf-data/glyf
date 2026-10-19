import json
from pathlib import Path

import pandas as pd
import pytest

from glyf.dashboard.artifacts import load_chart_artifact
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql
from glyf.ggsql.renderer import ChartRenderError, build_chart, required_columns
from glyf.ordering import is_order_sensitive
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

COMBO = (
    "select month, revenue, margin from fct_orders\n\n"
    "VISUALISE month AS x, revenue AS y, margin AS y2\n"
    "DRAW combo\n"
)
ROWS = pd.DataFrame(
    {"month": ["2026-01", "2026-02", "2026-03"], "revenue": [120, 140, 135], "margin": [22.5, 24.0, 21.0]}
)


def test_parser_wrapper_accepts_a_combo_and_its_right_axis_title() -> None:
    chart = parse_ggsql(COMBO + "LABEL y2_title => 'Margin (%)'\nINTERACT tooltip\n")

    assert chart.is_combo
    assert chart.y2_title == "Margin (%)"
    assert required_columns(chart) == ("month", "revenue", "margin")
    with pytest.raises(GgsqlParseError, match="combo requires x, y and y2 mappings"):
        parse_ggsql("select 1\n\nVISUALISE a AS x, b AS y\nDRAW combo\n")


def test_spec_draws_bars_and_a_line_on_independent_axes() -> None:
    chart = parse_ggsql(
        COMBO + "LABEL y_title => 'Revenue'\nLABEL y2_title => 'Margin (%)'\nINTERACT tooltip\n"
    )

    spec = build_chart(chart, ROWS).to_dict()

    bars, line = spec["layer"]
    assert bars["mark"]["type"] == "bar"
    assert line["mark"]["type"] == "line"
    assert spec["resolve"] == {"scale": {"y": "independent"}}
    assert bars["encoding"]["y"]["axis"]["titleColor"] != line["encoding"]["y"]["axis"]["titleColor"]
    assert line["encoding"]["y"]["axis"]["orient"] == "right"
    # One legend names both marks, in the axis titles' words.
    assert bars["encoding"]["color"]["scale"]["domain"] == ["Revenue", "Margin (%)"]
    assert [item["field"] for item in bars["encoding"]["tooltip"]] == ["month", "revenue", "margin"]
    # A text x keeps the query's order, as bands.
    assert bars["encoding"]["x"]["type"] == "ordinal"
    assert bars["encoding"]["x"]["sort"] is None


def test_a_monthly_date_axis_is_a_band_per_month() -> None:
    chart = parse_ggsql(COMBO)
    rows = ROWS.assign(month=pd.date_range("2026-01-01", periods=3, freq="MS"))

    x = build_chart(chart, rows).to_dict()["layer"][0]["encoding"]["x"]

    assert (x["type"], x["timeUnit"]) == ("ordinal", "yearmonth")
    daily = ROWS.assign(month=pd.date_range("2026-01-01", periods=3, freq="D"))
    assert build_chart(chart, daily).to_dict()["layer"][0]["encoding"]["x"]["timeUnit"] == "yearmonthdate"


def test_both_measures_must_be_numbers() -> None:
    chart = parse_ggsql(COMBO)

    with pytest.raises(ChartRenderError, match="combo needs a numeric y2 column and 'margin'"):
        build_chart(chart, ROWS.assign(margin=["a", "b", "c"]))


def test_pipeline_records_the_line_as_a_role_and_reports_row_order(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "combo.ggsql").write_text(
        "select * from (values ('Jan', 10, 1.5), ('Feb', 12, 2.0)) as t(month, revenue, margin)\n\n"
        "VISUALISE month AS x, revenue AS y, margin AS y2\nDRAW combo\nINTERACT tooltip\n",
        encoding="utf-8",
    )

    render_project(project)

    metadata = json.loads((project / "target/glyf/charts/combo.json").read_text(encoding="utf-8"))
    assert (metadata["x"], metadata["y"]) == ("month", "revenue")
    assert metadata["roles"] == [["x", "month"], ["y", "revenue"], ["y2", "margin"]]
    assert load_chart_artifact(project, "combo").metadata.roles[2] == ("y2", "margin")
    assert is_order_sensitive(parse_ggsql(COMBO))
