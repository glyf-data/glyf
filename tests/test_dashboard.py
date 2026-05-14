import shutil
from pathlib import Path

import pytest

from dbt_charts.dashboard.artifacts import load_chart_artifact
from dbt_charts.dashboard.generator import DashboardGenerationError, generate_dashboards
from dbt_charts.dashboard.loader import load_dashboard
from dbt_charts.pipeline import render_project


def test_dashboard_yaml_parses_optional_fields(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "description: Key business metrics.\n"
        "layout: grid\n"
        "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    dashboard = load_dashboard(dashboard_path)

    assert dashboard.name == "executive"
    assert dashboard.title == "Executive Dashboard"
    assert dashboard.description == "Key business metrics."
    assert dashboard.layout == "grid"
    assert dashboard.charts == ("revenue",)


def test_chart_metadata_loading(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    render_project(project)

    artifact = load_chart_artifact(project, "revenue")

    assert artifact.metadata.name == "revenue"
    assert artifact.metadata.title == "Monthly Revenue"
    assert artifact.metadata.chart_type == "line"
    assert artifact.svg is not None
    assert artifact.compiled_sql == "SELECT month, revenue\nFROM main.fct_orders\n"


def test_dashboard_generation_writes_dashboard_and_index(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    render_project(project)

    result = generate_dashboards(project)

    dashboard_html = project / "target" / "ggsql" / "dashboards" / "executive.html"
    index_html = project / "target" / "ggsql" / "index.html"

    assert result.index_path == index_html
    assert len(result.dashboards) == 1
    assert dashboard_html.exists()
    assert index_html.exists()
    assert "Executive Dashboard" in dashboard_html.read_text(encoding="utf-8")
    assert "Monthly Revenue" in dashboard_html.read_text(encoding="utf-8")
    assert "<svg" in dashboard_html.read_text(encoding="utf-8")
    assert "dashboards/executive.html" in index_html.read_text(encoding="utf-8")


def test_dashboard_generation_reports_missing_chart(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "charts:\n"
        "  - missing_chart\n",
        encoding="utf-8",
    )

    with pytest.raises(DashboardGenerationError, match="missing chart metadata"):
        generate_dashboards(project)
