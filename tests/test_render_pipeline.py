import json
import shutil
from pathlib import Path

import pytest

from dbt_ggsql.execution.duckdb import execute_sql
from dbt_ggsql.pipeline import RenderError, render_project


def test_render_project_writes_compiled_sql_and_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)

    result = render_project(project)

    assert len(result.charts) == 1
    assert list(result.charts[0].data.columns) == ["month", "revenue"]

    compiled_sql = project / "target" / "ggsql" / "compiled" / "revenue.sql"
    metadata_json = project / "target" / "ggsql" / "charts" / "revenue.json"
    png = project / "target" / "ggsql" / "charts" / "revenue.png"
    svg = project / "target" / "ggsql" / "charts" / "revenue.svg"

    assert compiled_sql.read_text(encoding="utf-8") == (
        "SELECT month, revenue\nFROM main.fct_orders\n"
    )
    assert json.loads(metadata_json.read_text(encoding="utf-8")) == {
        "name": "revenue",
        "chart_type": "line",
        "compiled_sql_path": "target/ggsql/compiled/revenue.sql",
        "png_path": "target/ggsql/charts/revenue.png",
        "svg_path": "target/ggsql/charts/revenue.svg",
        "title": "Monthly Revenue",
        "x": "month",
        "y": "revenue",
    }
    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert "<svg" in svg.read_text(encoding="utf-8")
    assert "Monthly Revenue" in svg.read_text(encoding="utf-8")


def test_duckdb_execution_loads_seed_tables(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)

    data = execute_sql(
        project,
        "select month, revenue from main.fct_orders order by month",
    )

    assert data.to_dict(orient="records") == [
        {"month": "2026-01", "revenue": 1200},
        {"month": "2026-02", "revenue": 1800},
        {"month": "2026-03", "revenue": 2100},
        {"month": "2026-04", "revenue": 2400},
    ]


def test_render_project_reports_unsupported_chart_type(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select month, revenue from {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW heatmap\n",
        encoding="utf-8",
    )

    with pytest.raises(RenderError, match="unsupported chart type 'heatmap'"):
        render_project(project)
