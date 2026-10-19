import json
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from glyf.dashboard.artifacts import load_chart_artifact
from glyf.dashboard.filters import _mode
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql
from glyf.ggsql.renderer import ChartRenderError, build_chart, render_chart
from glyf.ggsql.sankey import NODE_GAP, SankeyError, layout_sankey
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

SANKEY = (
    "select step, next_step, users from fct_funnel\n\n"
    "VISUALISE step AS source, next_step AS target, users AS value\n"
    "DRAW sankey\n"
)
FUNNEL = [
    ("Search", "Trial", 50),
    ("Search", "Bounce", 30),
    ("Ads", "Trial", 20),
    ("Trial", "Pro", 40),
    ("Trial", "Free", 30),
]


def test_parser_wrapper_accepts_a_sankey_and_names_its_roles() -> None:
    chart = parse_ggsql(SANKEY + "INTERACT tooltip\n")

    assert chart.is_sankey
    with pytest.raises(GgsqlParseError, match="sankey requires source, target and value"):
        parse_ggsql("select 1\n\nVISUALISE a AS source, n AS value\nDRAW sankey\n")


def test_columns_follow_the_longest_path_and_ends_go_right() -> None:
    layout = layout_sankey(FUNNEL, 600, 400)

    column = {node.name: node.column for node in layout.nodes}
    assert layout.columns == 3
    assert column == {"Search": 0, "Ads": 0, "Trial": 1, "Bounce": 2, "Pro": 2, "Free": 2}


def test_node_value_is_the_larger_of_what_arrives_and_what_leaves() -> None:
    nodes = {node.name: node for node in layout_sankey(FUNNEL, 600, 400).nodes}

    assert nodes["Trial"].value == 70
    assert nodes["Search"].value == 80
    # Heights are proportional to values, on one scale for every column.
    ratio = (nodes["Trial"].y1 - nodes["Trial"].y0) / (nodes["Search"].y1 - nodes["Search"].y0)
    assert ratio == pytest.approx(70 / 80)


def test_columns_fit_the_height_and_nodes_keep_their_gap() -> None:
    layout = layout_sankey(FUNNEL, 600, 400)

    for column in range(layout.columns):
        stack = sorted((n for n in layout.nodes if n.column == column), key=lambda n: n.y0)
        assert stack[0].y0 >= 0 and stack[-1].y1 <= 400 + 1e-9
        for upper, lower in zip(stack, stack[1:]):
            assert lower.y0 - upper.y1 == pytest.approx(NODE_GAP)


def test_bands_stack_without_overlapping_at_a_node() -> None:
    layout = layout_sankey(FUNNEL, 600, 400)
    trial = next(node for node in layout.nodes if node.name == "Trial")

    leaving = sorted(
        (link for link in layout.links if link.source == "Trial"), key=lambda link: link.y_source
    )
    assert leaving[0].y_source - leaving[0].width / 2 == pytest.approx(trial.y0)
    for upper, lower in zip(leaving, leaving[1:]):
        assert lower.y_source - lower.width / 2 == pytest.approx(upper.y_source + upper.width / 2)
    curve = leaving[0].curve()
    assert curve[0] == (trial.x1, leaving[0].y_source)
    assert curve[-1][1] == pytest.approx(leaving[0].y_target)


def test_repeated_links_are_summed_and_zeros_and_gaps_skipped() -> None:
    layout = layout_sankey(
        [("A", "B", 2), ("A", "B", Decimal("3.5")), ("A", "C", 0), (None, "B", 9), ("A", "C", 1)],
        400,
        200,
    )

    flows = {(link.source, link.target): link.value for link in layout.links}
    assert flows == {("A", "B"): 5.5, ("A", "C"): 1.0}


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([("A", "B", 1), ("B", "A", 1)], "flows loop back through 'A', 'B'"),
        ([("A", "A", 1)], "from 'A' to itself"),
        ([("A", "B", -1)], "is negative"),
        ([("A", "B", "many")], "needs a numeric value"),
        ([("A", "B", 0)], "no flows to draw"),
    ],
)
def test_layout_refuses_rows_it_cannot_draw(
    rows: list[tuple[object, object, object]], message: str
) -> None:
    with pytest.raises(SankeyError, match=message):
        layout_sankey(rows, 400, 200)


def test_too_many_nodes_for_the_height_says_what_to_change() -> None:
    rows = [("Start", f"end {index}", 1) for index in range(40)]

    with pytest.raises(SankeyError, match="set CONFIG height higher"):
        layout_sankey(rows, 400, 200)


def test_spec_draws_bands_nodes_and_labels_on_pixel_scales() -> None:
    chart = parse_ggsql(SANKEY + "INTERACT tooltip\nCONFIG height => 300\n")
    data = pd.DataFrame(FUNNEL, columns=["step", "next_step", "users"])

    spec = build_chart(chart, data).to_dict()

    links, nodes, left, right = spec["layer"]
    assert links["mark"]["type"] == "area"
    assert links["encoding"]["y2"] == {"field": "y2"}
    assert links["encoding"]["y"]["stack"] is None
    assert [item["title"] for item in links["encoding"]["tooltip"]] == ["step", "next_step", "users"]
    assert nodes["mark"]["type"] == "rect"
    assert (left["mark"]["align"], right["mark"]["align"]) == ("left", "right")
    assert links["encoding"]["y"]["scale"]["domain"] == [0, 300]
    assert links["encoding"]["x"]["axis"] is None
    assert spec["config"]["view"]["stroke"] is None


def test_render_reports_a_loop_as_a_chart_error(tmp_path: Path) -> None:
    chart = parse_ggsql(SANKEY)
    data = pd.DataFrame([("A", "B", 1), ("B", "A", 1)], columns=["step", "next_step", "users"])

    with pytest.raises(ChartRenderError, match="loop back"):
        render_chart(chart, data, tmp_path / "s.png", tmp_path / "s.svg")


def test_pipeline_builds_a_sankey_that_filters_leave_alone(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "funnel.ggsql").write_text(
        "select * from (values ('Search', 'Trial', 5), ('Trial', 'Pro', 3)) "
        "as t(step, next_step, users)\n\n"
        "VISUALISE step AS source, next_step AS target, users AS value\nDRAW sankey\n"
        "INTERACT tooltip\n",
        encoding="utf-8",
    )

    render_project(project)

    metadata = json.loads(
        (project / "target/glyf/charts/funnel.json").read_text(encoding="utf-8")
    )
    assert metadata["roles"] == [["source", "step"], ["target", "next_step"], ["value", "users"]]
    assert (metadata["x"], metadata["y"]) == ("step", "next_step")
    artifact = load_chart_artifact(project, "funnel")
    assert artifact.metadata.roles == (("source", "step"), ("target", "next_step"), ("value", "users"))
    assert _mode(artifact, "step") == "none"


def test_dark_theme_keeps_a_frameless_chart_frameless_and_colours_its_labels() -> None:
    from glyf.dashboard.chart_theme import _apply_dark_vega_theme

    frameless = _apply_dark_vega_theme({"config": {"view": {"stroke": None}}})
    framed = _apply_dark_vega_theme({"config": {}})

    assert frameless["config"]["view"]["stroke"] is None
    assert framed["config"]["view"]["stroke"] == "#3f3f46"
    assert frameless["config"]["text"]["color"] == "#f4f4f5"
