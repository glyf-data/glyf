from pathlib import Path

import pytest

from dbt_charts.dashboard.artifacts import load_chart_artifact
from dbt_charts.dashboard.generator import DashboardGenerationError, generate_dashboards
from dbt_charts.dashboard.loader import load_dashboard
from dbt_charts.pipeline import render_project
from tests.helpers import copy_basic_project


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


def test_dashboard_yaml_parses_sections_and_layout_items(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "layout:\n"
        "  columns: 3\n"
        "sections:\n"
        "  - title: Revenue\n"
        "    description: Key revenue signals.\n"
        "    columns: 2\n"
        "    items:\n"
        "      - metric:\n"
        "          label: Total revenue\n"
        "          value: $7.6k\n"
        "          note: Current sample period\n"
        "      - markdown:\n"
        "          title: Notes\n"
        "          text: Revenue is generated from the fct_orders model.\n"
        "      - chart: revenue\n"
        "        title: Monthly revenue\n"
        "        width: 2\n",
        encoding="utf-8",
    )

    dashboard = load_dashboard(dashboard_path)

    assert dashboard.layout == "grid"
    assert dashboard.layout_config.columns == 3
    assert dashboard.chart_names == ("revenue",)
    assert len(dashboard.sections) == 1
    section = dashboard.sections[0]
    assert section.title == "Revenue"
    assert section.columns == 2
    assert [item.kind for item in section.items] == ["metric", "markdown", "chart"]
    assert section.items[0].label == "Total revenue"
    assert section.items[1].text == "Revenue is generated from the fct_orders model."
    assert section.items[2].chart == "revenue"
    assert section.items[2].width == 2


def test_dashboard_yaml_parses_custom_column_widths(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "layout:\n"
        "  columns: \"30% 70%\"\n"
        "sections:\n"
        "  - title: Revenue\n"
        "    columns: [25%, 75%]\n"
        "    charts:\n"
        "      - revenue\n",
        encoding="utf-8",
    )

    dashboard = load_dashboard(dashboard_path)

    assert dashboard.layout_config.columns == 2
    assert dashboard.layout_config.column_widths == ("30fr", "70fr")
    assert dashboard.layout_config.column_template == (
        "minmax(0, 30fr) minmax(0, 70fr)"
    )
    assert dashboard.sections[0].columns == 2
    assert dashboard.sections[0].column_widths == ("25fr", "75fr")


def test_dashboard_yaml_rejects_boolean_columns(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "layout:\n"
        "  columns: true\n"
        "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="layout.columns"):
        load_dashboard(dashboard_path)


def test_chart_metadata_loading(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)

    artifact = load_chart_artifact(project, "revenue")

    assert artifact.metadata.name == "revenue"
    assert artifact.metadata.title == "Monthly Revenue"
    assert artifact.metadata.chart_type == "line"
    assert artifact.svg is not None
    assert artifact.compiled_sql == "SELECT month, revenue\nFROM main.fct_orders\n"


def test_dashboard_generation_writes_dashboard_and_index(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
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
    assert "vegaEmbed" not in dashboard_html.read_text(encoding="utf-8")
    assert "dashboards/executive.html" in index_html.read_text(encoding="utf-8")


def test_dashboard_generation_embeds_interactive_vega_spec(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select month, revenue from {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW line\n"
        "LABEL title => 'Monthly Revenue'\n"
        "INTERACT tooltip, zoom\n",
        encoding="utf-8",
    )
    render_project(project)

    generate_dashboards(project)

    dashboard_html = (
        project / "target" / "ggsql" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "https://cdn.jsdelivr.net/npm/vega" in dashboard_html
    assert "vegaEmbed" in dashboard_html
    assert 'data-vega-chart="chart-revenue-spec"' in dashboard_html
    assert '"tooltip"' in dashboard_html
    assert (project / "target" / "ggsql" / "charts" / "revenue.vega.json").exists()


def test_dashboard_generation_renders_sections_and_layout_items(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "description: Key business metrics.\n"
        "layout:\n"
        "  columns: 3\n"
        "sections:\n"
        "  - title: Revenue Overview\n"
        "    columns: 2\n"
        "    items:\n"
        "      - metric:\n"
        "          label: Total revenue\n"
        "          value: $7.6k\n"
        "          note: Current sample period\n"
        "      - markdown:\n"
        "          title: Analyst note\n"
        "          text: Revenue is generated from the fct_orders model.\n"
        "      - chart: revenue\n"
        "        title: Monthly revenue\n"
        "        width: 2\n",
        encoding="utf-8",
    )

    generate_dashboards(project)

    html = (
        project / "target" / "ggsql" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "Revenue Overview" in html
    assert "Total revenue" in html
    assert "$7.6k" in html
    assert "Analyst note" in html
    assert "Revenue is generated from the fct_orders model." in html
    assert "Monthly revenue" in html
    assert "--dashboard-columns: 2" in html
    assert "--item-width: 2" in html
    assert all(line == line.rstrip() for line in html.splitlines())


def test_dashboard_generation_renders_custom_column_widths(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "sections:\n"
        "  - title: Revenue Overview\n"
        "    columns: \"30% 70%\"\n"
        "    charts:\n"
        "      - revenue\n",
        encoding="utf-8",
    )

    generate_dashboards(project)

    html = (
        project / "target" / "ggsql" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "--dashboard-columns: 2" in html
    assert "--dashboard-column-template: minmax(0, 30fr) minmax(0, 70fr)" in html
    assert "@media (max-width: 760px)" in html


def test_dashboard_generation_respects_equal_section_columns(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "layout:\n"
        "  columns: \"30% 70%\"\n"
        "sections:\n"
        "  - title: Inherited layout\n"
        "    charts:\n"
        "      - revenue\n"
        "  - title: Equal layout\n"
        "    columns: 2\n"
        "    charts:\n"
        "      - revenue\n",
        encoding="utf-8",
    )

    generate_dashboards(project)

    html = (
        project / "target" / "ggsql" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "--dashboard-column-template: minmax(0, 30fr) minmax(0, 70fr)" in html
    assert 'style="--dashboard-columns: 2; --section-columns: 2">' in html


def test_dashboard_generation_reports_missing_chart(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
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
