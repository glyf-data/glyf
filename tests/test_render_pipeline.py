import json
import shutil
from pathlib import Path

from dbt_ggsql.pipeline import render_project


def test_render_project_writes_compiled_sql_and_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)

    result = render_project(project)

    assert len(result.charts) == 1

    compiled_sql = project / "target" / "ggsql" / "compiled" / "revenue.sql"
    metadata_json = project / "target" / "ggsql" / "charts" / "revenue.json"
    png = project / "target" / "ggsql" / "charts" / "revenue.png"
    svg = project / "target" / "ggsql" / "charts" / "revenue.svg"

    assert compiled_sql.read_text(encoding="utf-8") == (
        "SELECT month, revenue\nFROM main.fct_orders\n"
    )
    assert json.loads(metadata_json.read_text(encoding="utf-8")) == {
        "chart": "revenue",
        "compiled_sql": "target/ggsql/compiled/revenue.sql",
        "title": "Monthly Revenue",
        "type": "line",
    }
    assert "Placeholder PNG for revenue" in png.read_text(encoding="utf-8")
    assert "Placeholder chart: revenue" in svg.read_text(encoding="utf-8")
