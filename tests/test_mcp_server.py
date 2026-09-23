"""The MCP server: a glyf project exposed to an agent.

Every tool is built on a function the CLI already uses, so these tests check
the shape an agent receives and the two promises the server makes: it never
runs a build, and validate moves no rows.
"""

import asyncio
import json
from pathlib import Path
import shutil

import pytest

from glyf.mcp_server import build_server
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

pytest.importorskip("mcp")


def _call(server, tool: str, **arguments) -> dict:
    result = asyncio.run(server.call_tool(tool, arguments))
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    return json.loads(result.content[0].text)


def test_the_server_lists_its_tools_with_instructions(tmp_path: Path) -> None:
    server = build_server(copy_basic_project(tmp_path))

    tools = asyncio.run(server.list_tools())

    assert sorted(tool.name for tool in tools) == [
        "diff", "get_chart", "impact", "list_charts", "list_dashboards", "validate"
    ]
    assert "never fetches rows" in server.instructions or "fetches rows" in server.instructions


def test_list_charts_and_dashboards_join_the_two(tmp_path: Path) -> None:
    server = build_server(copy_basic_project(tmp_path))

    charts = _call(server, "list_charts")["charts"]
    dashboards = _call(server, "list_dashboards")["dashboards"]

    assert charts == [
        {
            "name": "revenue",
            "path": "visualisations/revenue.ggsql",
            "type": "line",
            "title": "Monthly Revenue",
            "dashboards": ["executive"],
            "models": ["fct_orders"],
            "sources": [],
        }
    ]
    assert dashboards[0]["name"] == "executive"
    assert dashboards[0]["charts"] == ["revenue"]


def test_get_chart_returns_the_file_and_its_spec(tmp_path: Path) -> None:
    server = build_server(copy_basic_project(tmp_path))

    chart = _call(server, "get_chart", name="revenue")

    assert chart["text"].startswith("SELECT month, revenue")
    assert chart["visualise"] == [
        {"field": "month", "role": "x"},
        {"field": "revenue", "role": "y"},
    ]
    assert chart["models"] == ["fct_orders"]
    assert "main.fct_orders" in chart["compiled_sql"]
    assert chart["sql_columns"] == ["month", "revenue"]

    missing = _call(server, "get_chart", name="nope")
    assert "no chart named 'nope'" in missing["error"]


def test_impact_is_the_command_answer(tmp_path: Path) -> None:
    server = build_server(copy_basic_project(tmp_path))

    report = _call(server, "impact", target="fct_orders.revenue")

    assert report["charts"][0]["certainty"] == "reads"
    assert report["charts"][0]["detail"] == "revenue AS y"
    assert report["dashboards"] == ["executive"]
    assert "error" in _call(server, "impact", target="nothing")


def test_validate_reads_files_and_with_execute_asks_the_warehouse(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select month, revenue as takings from {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\nDRAW line\n",
        encoding="utf-8",
    )
    server = build_server(project)

    passive = _call(server, "validate")
    assert passive["ok"] is True and passive["executed"] is False

    executed = _call(server, "validate", execute=True)
    assert executed["ok"] is False
    assert "missing chart column 'revenue'" in executed["errors"][0]
    assert not list((project / "target" / "glyf" / "charts").glob("*.png")), "no build ran"


def test_diff_compares_two_existing_builds_and_runs_none(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    baseline = tmp_path / "baseline"
    shutil.copytree(project / "target" / "glyf", baseline)
    (project / "seeds" / "fct_orders.csv").write_text(
        "month,revenue\n2026-01,1200\n2026-02,1800\n2026-03,2100\n2026-04,9000\n", encoding="utf-8"
    )
    render_project(project)
    server = build_server(project)

    report = _call(server, "diff", baseline=str(baseline))

    assert report["counts"]["changed"] == 1
    assert report["charts"]["revenue"]["reasons"] == ["the rows changed"]
    assert "error" in _call(server, "diff", baseline=str(tmp_path / "nowhere"))
