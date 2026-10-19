import json
from pathlib import Path

import pandas as pd
import pytest

from glyf.dashboard.artifacts import load_chart_artifact
from glyf.dashboard.filters import _mode
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql
from glyf.ggsql.renderer import ChartRenderError, build_chart
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

FUNNEL = "select step, users from fct_signup{order}\n\nVISUALISE step AS x, users AS y\nDRAW funnel\n"
ROWS = pd.DataFrame({"step": ["Visited", "Paid", "Signed up"], "users": [1000, 50, 400]})


def _steps(spec: dict) -> list[dict]:
    return next(iter(spec["datasets"].values()))


def test_parser_wrapper_accepts_a_funnel() -> None:
    chart = parse_ggsql(FUNNEL.format(order="") + "INTERACT tooltip\n")

    assert chart.is_funnel
    with pytest.raises(GgsqlParseError, match="funnel does not take a 'color' mapping"):
        parse_ggsql("select 1\n\nVISUALISE a AS x, b AS y, c AS color\nDRAW funnel\n")


def test_without_an_order_by_the_largest_step_comes_first() -> None:
    spec = build_chart(parse_ggsql(FUNNEL.format(order="")), ROWS).to_dict()

    assert [step["step"] for step in _steps(spec)] == ["Visited", "Signed up", "Paid"]


def test_an_order_by_keeps_the_query_order() -> None:
    spec = build_chart(parse_ggsql(FUNNEL.format(order=" order by 1")), ROWS).to_dict()

    assert [step["step"] for step in _steps(spec)] == ["Visited", "Paid", "Signed up"]


def test_bars_are_centred_and_labelled_with_their_share_of_the_first() -> None:
    chart = parse_ggsql(FUNNEL.format(order="") + "INTERACT tooltip\n")

    spec = build_chart(chart, ROWS).to_dict()

    visited, signed_up, paid = _steps(spec)
    assert (signed_up["start"], signed_up["end"]) == (300, 700)
    assert signed_up["share"] == pytest.approx(0.4)
    assert paid["from_previous"] == pytest.approx(50 / 400)
    assert visited["label"] == "1,000 · 100%"
    # A narrow bar's label goes beside it rather than spilling over its edges.
    assert visited["inside"] and not paid["inside"]
    bars = spec["layer"][0]
    assert bars["encoding"]["y"]["sort"] is None
    assert [item["title"] for item in bars["encoding"]["tooltip"]] == [
        "step",
        "users",
        "of the first step",
        "of the step before",
    ]


def test_a_negative_or_missing_value_is_handled() -> None:
    chart = parse_ggsql(FUNNEL.format(order=""))

    with pytest.raises(ChartRenderError, match="funnel needs values of zero or more"):
        build_chart(chart, ROWS.assign(users=[10, -1, 5]))
    with pytest.raises(ChartRenderError, match="funnel has no steps to draw"):
        build_chart(chart, pd.DataFrame({"step": ["a"], "users": pd.Series([None], dtype="float")}))
    spec = build_chart(chart, pd.DataFrame({"step": ["a", "b"], "users": [0, 0]})).to_dict()
    assert {step["share"] for step in _steps(spec)} == {0.0}


def test_pipeline_builds_a_funnel_that_filters_leave_alone(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "signup.ggsql").write_text(
        "select * from (values ('Visited', 10), ('Paid', 2)) as t(step, users)\n\n"
        "VISUALISE step AS x, users AS y\nDRAW funnel\nINTERACT tooltip\n",
        encoding="utf-8",
    )

    render_project(project)

    metadata = json.loads((project / "target/glyf/charts/signup.json").read_text(encoding="utf-8"))
    assert (metadata["chart_type"], metadata["x"], metadata["y"]) == ("funnel", "step", "users")
    assert _mode(load_chart_artifact(project, "signup"), "step") == "none"
