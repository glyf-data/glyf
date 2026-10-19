import json
from pathlib import Path

import pandas as pd
import pytest

from glyf.dashboard.artifacts import load_chart_artifact
from glyf.dashboard.filters import _mode
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql
from glyf.ggsql.renderer import ChartRenderError, build_chart
from glyf.ordering import is_order_sensitive
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

WATERFALL = "select step, change from bridge order by 1\n\nVISUALISE step AS x, change AS y\nDRAW waterfall\n"
ROWS = pd.DataFrame({"step": ["Opening", "Price", "Churn"], "change": [100, 20, -15]})


def _bars(spec: dict) -> list[dict]:
    return next(iter(spec["datasets"].values()))


def test_parser_wrapper_accepts_a_waterfall() -> None:
    chart = parse_ggsql(WATERFALL + "INTERACT tooltip\n")

    assert chart.is_waterfall
    assert is_order_sensitive(chart)
    with pytest.raises(GgsqlParseError, match="waterfall does not take a 'color' mapping"):
        parse_ggsql("select 1\n\nVISUALISE a AS x, b AS y, c AS color\nDRAW waterfall\n")


def test_bars_run_from_where_the_last_ended_and_a_total_closes_them() -> None:
    spec = build_chart(parse_ggsql(WATERFALL), ROWS).to_dict()

    bars = [(bar["step"], bar["kind"], bar["start"], bar["end"], bar["label"]) for bar in _bars(spec)]
    assert bars == [
        ("Opening", "Total", 0, 100, "100"),
        ("Price", "Increase", 100, 120, "+20"),
        ("Churn", "Decrease", 120, 105, "−15"),
        ("Total", "Total", 0, 105, "105"),
    ]
    # Each bar's end is carried across to the next.
    assert [bar["next"] for bar in _bars(spec)] == ["Price", "Churn", "Total", None]


def test_label_total_names_the_closing_bar_and_cannot_repeat_a_step() -> None:
    chart = parse_ggsql(WATERFALL + "LABEL total => 'Closing'\n")

    assert _bars(build_chart(chart, ROWS).to_dict())[-1]["step"] == "Closing"
    with pytest.raises(ChartRenderError, match="a step already has that name"):
        build_chart(parse_ggsql(WATERFALL), ROWS.assign(step=["Opening", "Total", "Churn"]))


def test_spec_keeps_the_query_order_and_names_only_the_kinds_it_draws() -> None:
    chart = parse_ggsql(WATERFALL + "INTERACT tooltip\n")

    spec = build_chart(chart, ROWS.assign(change=[100, -20, -15])).to_dict()

    connectors, columns, labels = spec["layer"]
    assert connectors["mark"]["type"] == "rule"
    assert columns["encoding"]["x"]["sort"] is None
    assert columns["encoding"]["color"]["scale"]["domain"] == ["Decrease", "Total"]
    assert [item["title"] for item in columns["encoding"]["tooltip"]] == ["step", "change", "running total"]
    assert labels["mark"]["type"] == "text"


def test_a_text_change_or_no_rows_is_a_render_error() -> None:
    chart = parse_ggsql(WATERFALL)

    with pytest.raises(ChartRenderError, match="waterfall needs a numeric y column"):
        build_chart(chart, ROWS.assign(change=["a", "b", "c"]))
    with pytest.raises(ChartRenderError, match="waterfall has no steps to draw"):
        build_chart(chart, pd.DataFrame({"step": ["a"], "change": pd.Series([None], dtype="float")}))


def test_pipeline_builds_a_waterfall_that_filters_leave_alone(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "bridge.ggsql").write_text(
        "select * from (values (1, 'Opening', 10), (2, 'Churn', -2)) as t(n, step, change) order by n\n\n"
        "VISUALISE step AS x, change AS y\nDRAW waterfall\nINTERACT tooltip\n",
        encoding="utf-8",
    )

    render_project(project)

    metadata = json.loads((project / "target/glyf/charts/bridge.json").read_text(encoding="utf-8"))
    assert (metadata["chart_type"], metadata["x"], metadata["y"]) == ("waterfall", "step", "change")
    assert _mode(load_chart_artifact(project, "bridge"), "step") == "none"
