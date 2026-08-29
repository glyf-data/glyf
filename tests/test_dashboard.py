import json
from datetime import datetime
from pathlib import Path
import re

import pytest

from glyf.dashboard.assets import AssetManager
from glyf.dashboard.artifacts import load_chart_artifact
from glyf.dashboard.generator import DashboardGenerationError, generate_dashboards
from glyf.dashboard.loader import load_dashboard
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project


def test_dashboard_yaml_parses_optional_fields(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "description: Key business metrics.\n"
        "theme: dark\n"
        "chart_theme: auto\n"
        "tags:\n"
        "  - finance\n"
        "  - monthly\n"
        "layout: grid\n"
        "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    dashboard = load_dashboard(dashboard_path)

    assert dashboard.name == "executive"
    assert dashboard.title == "Executive Dashboard"
    assert dashboard.description == "Key business metrics."
    assert dashboard.theme == "dark"
    assert dashboard.chart_theme == "auto"
    assert dashboard.tags == ("finance", "monthly")
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


def test_dashboard_yaml_parses_toolbar_summary_and_components(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "toolbar:\n"
        "  visibility: public\n"
        "  actions: [share, visibility]\n"
        "summary:\n"
        "  - \"{{ ui.label_value('Owner', 'Analytics Engineering') }}\"\n"
        "sections:\n"
        "  - title: Status\n"
        "    items:\n"
        "      - component: \"{{ alert.info('Refresh complete', 'Notification') }}\"\n"
        "        width: 2\n",
        encoding="utf-8",
    )

    dashboard = load_dashboard(dashboard_path)

    assert dashboard.toolbar.visibility == "public"
    assert dashboard.toolbar.actions == ("share", "visibility")
    assert dashboard.summary == (
        "{{ ui.label_value('Owner', 'Analytics Engineering') }}",
    )
    assert dashboard.sections[0].items[0].kind == "component"
    assert dashboard.sections[0].items[0].component == (
        "{{ alert.info('Refresh complete', 'Notification') }}"
    )
    assert dashboard.sections[0].items[0].width == 2


def test_dashboard_yaml_parses_filters_with_source_expression(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "filters:\n"
        "  - field: plan\n"
        "    values: source(revenue, month)\n"
        "  - field: region\n"
        "    values: [emea, us]\n"
        "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    dashboard = load_dashboard(dashboard_path)

    assert dashboard.filters[0].field == "plan"
    assert dashboard.filters[0].source_chart == "revenue"
    assert dashboard.filters[0].source_field == "month"
    assert dashboard.filters[0].is_sourced is True
    assert dashboard.filters[1].values == ("emea", "us")
    assert dashboard.artifact_chart_names == ("revenue",)


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


def test_dashboard_yaml_rejects_empty_tags(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "tags:\n"
        "  - finance\n"
        "  - ''\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="tags\\[2\\]"):
        load_dashboard(dashboard_path)


def test_dashboard_yaml_rejects_unknown_theme(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "theme: midnight\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected 'theme' to be one of"):
        load_dashboard(dashboard_path)


def test_dashboard_yaml_rejects_unknown_chart_theme(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "chart_theme: midnight\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected 'chart_theme' to be one of"):
        load_dashboard(dashboard_path)


def test_dashboard_yaml_rejects_invalid_dashboard_name(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: ../executive\n"
        "title: Executive Dashboard\n"
        "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="valid filename stem"):
        load_dashboard(dashboard_path)


def test_dashboard_yaml_rejects_partial_summary_macro_template(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "summary:\n"
        "  - \"Owner: {{ owner() }}\"\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected a Jinja expression"):
        load_dashboard(dashboard_path)


def test_dashboard_yaml_rejects_item_with_multiple_kinds(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "executive.yml"
    dashboard_path.write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "sections:\n"
        "  - title: Mixed\n"
        "    items:\n"
        "      - chart: revenue\n"
        "        markdown: Invalid second kind\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="exactly one"):
        load_dashboard(dashboard_path)


def test_chart_metadata_loading(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)

    artifact = load_chart_artifact(project, "revenue")

    assert artifact.metadata.name == "revenue"
    assert artifact.metadata.title == "Monthly Revenue"
    assert artifact.metadata.chart_type == "line"
    assert artifact.metadata.data_json_path == (
        project / "target" / "glyf" / "data" / "normalized" / "revenue.data.json"
    )
    assert artifact.data.fields == ("month", "revenue")
    assert artifact.data.rows[-1]["revenue"] == 2400
    assert artifact.svg is not None
    assert artifact.compiled_sql == "SELECT month, revenue\nFROM main.fct_orders\n"


def test_dashboard_generation_writes_dashboard_and_index(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)

    result = generate_dashboards(project)

    dashboard_html = project / "target" / "glyf" / "dashboards" / "executive.html"
    index_html = project / "target" / "glyf" / "index.html"

    assert result.index_path == index_html
    assert len(result.dashboards) == 1
    assert dashboard_html.exists()
    assert index_html.exists()
    html = dashboard_html.read_text(encoding="utf-8")
    assert "Executive Dashboard" in html
    assert "Monthly Revenue" in html
    assert "<svg" in html
    assert "vegaEmbed" not in html
    assert "Chart sources" in html
    assert "Source" in html
    assert "Refreshed <strong title=" in html
    assert re.search(r"\d{2} [A-Z][a-z]{2} \d{4}, \d{2}:\d{2} UTC", html)
    assert "on build" not in html
    assert "Compiled SQL" not in html
    assert (project / "target" / "glyf" / "assets" / "dashboard.css").exists()
    assert (
        project
        / "target"
        / "glyf"
        / "assets"
        / "fonts"
        / "HankenGrotesk-Regular.ttf"
    ).exists()
    assert "dashboards/executive.html" in index_html.read_text(encoding="utf-8")
    bundle = json.loads(
        (project / "target" / "glyf" / "bundle.json").read_text(encoding="utf-8")
    )
    assert bundle["bundle_version"] == "1"
    assert bundle["mode"] == "local_artifact"
    assert bundle["charts"]["revenue"]["artifacts"]["data"] == (
        "data/normalized/revenue.data.json"
    )
    assert bundle["dashboards"]["executive"]["path"] == "dashboards/executive.html"


def test_dashboard_single_file_assets_inline_local_fonts(tmp_path: Path) -> None:
    assets = AssetManager().prepare(tmp_path, single_file=True)

    assert assets.inline_css is not None
    assert 'data:font/ttf;base64,' in assets.inline_css
    assert 'fonts/HankenGrotesk-Regular.ttf' not in assets.inline_css


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
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "https://cdn.jsdelivr.net/npm/vega" in dashboard_html
    assert "vegaEmbed" in dashboard_html
    assert 'data-vega-chart="chart-revenue-spec"' in dashboard_html
    assert '"tooltip"' in dashboard_html
    assert (
        project / "target" / "glyf" / "data" / "vega" / "revenue.vega.json"
    ).exists()


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
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "Revenue Overview" in html
    assert "Total revenue" in html
    assert "$7.6k" in html
    assert "Analyst note" in html
    assert "Revenue is generated from the fct_orders model." in html
    assert "Monthly revenue" in html
    assert "--glyf-columns: 2" in html
    assert "--glyf-item-width: 2" in html
    assert all(line == line.rstrip() for line in html.splitlines())


@pytest.mark.parametrize(
    ("toolbar_yaml", "expect_share", "expect_visibility"),
    [
        ("toolbar:\n  visibility: public\n", True, True),
        ("toolbar:\n  visibility: public\n  actions: [share]\n", True, False),
        ("toolbar:\n  actions: [visibility]\n", False, True),
        ("toolbar:\n  actions: []\n", False, False),
    ],
)
def test_dashboard_toolbar_actions_control_rendered_buttons(
    tmp_path: Path, toolbar_yaml: str, expect_share: bool, expect_visibility: bool
) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        + toolbar_yaml
        + "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    generate_dashboards(project)

    html = (
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "Dashboard actions" in html
    assert ('aria-label="Share dashboard"' in html) is expect_share
    assert ('aria-label="Visibility:' in html) is expect_visibility
    # The fixed controls are unaffected by actions.
    assert 'aria-label="Open lookback"' in html
    assert 'aria-label="Send feedback"' in html


def test_dashboard_generation_renders_builtin_macro_components(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    generated_year = datetime.now().astimezone().strftime("%Y")
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "toolbar:\n"
        "  visibility: public\n"
        "summary:\n"
        "  - \"{{ ui.label_value('Owner', 'Analytics Engineering') }}\"\n"
        "  - \"{{ ui.label_value('Generated', time.now('%Y')) }}\"\n"
        "sections:\n"
        "  - title: Status\n"
        "    items:\n"
        "      - component: \"{{ echo('Refresh complete', 'Notification') }}\"\n"
        "      - component: \"{{ ui.list(['Revenue', 'Margin'], title='Metrics') }}\"\n"
        "      - chart: revenue\n",
        encoding="utf-8",
    )

    generate_dashboards(project)

    html = (
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "Dashboard actions" in html
    assert "Analytics Engineering" in html
    assert "Generated" in html
    assert generated_year in html
    assert "Notification" in html
    assert "Refresh complete" in html
    assert "Metrics" in html
    assert "Revenue" in html
    assert "Margin" in html
    assert "glyf-alert" in html
    assert "data-glyf-source-button" in html


def test_dashboard_generation_renders_dashboard_tags(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "tags:\n"
        "  - finance\n"
        "  - executive\n"
        "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    generate_dashboards(project)

    html = (
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "finance" in html
    assert "executive" in html
    assert 'aria-label="Dashboard tags"' in html


def test_dashboard_generation_uses_dashboard_theme_override(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "theme: dark\n"
        "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    html = generate_dashboards(project).dashboards[0].path.read_text(encoding="utf-8")

    assert '<html lang="en" data-theme="dark">' in html


def test_dashboard_generation_applies_dark_chart_theme(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "theme: dark\n"
        "chart_theme: dark\n"
        "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    html = generate_dashboards(project).dashboards[0].path.read_text(encoding="utf-8")

    assert 'data-chart-theme="dark"' in html
    assert 'fill="#09090b"' in html
    assert 'fill="#f4f4f5"' in html


def test_dashboard_generation_renders_ai_macro_summary_panel(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "summary:\n"
        "  - \"{{ ai.summary('Revenue moved up this month.') }}\"\n"
        "  - \"{{ ai.insight('Starter churn needs review.', tone='warning') }}\"\n"
        "charts:\n"
        "  - revenue\n",
        encoding="utf-8",
    )

    generate_dashboards(project)

    html = (
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "AI Summary" in html
    assert "Revenue moved up this month." in html
    assert "Starter churn needs review." in html
    assert "glyf-ai-panel" in html
    assert "glyf-tone-warning" in html


def test_dashboard_generation_loads_project_python_macros(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "macros.py").write_text(
        "from glyf.dashboard import components as c\n\n"
        "def finance_owner():\n"
        "    return c.label_value('Owner', 'Finance Analytics')\n\n"
        "def stale_data_warning(hours_old):\n"
        "    if hours_old > 24:\n"
        "        return c.alert('Data is stale', title='Freshness', tone='warning')\n"
        "    return c.badge('Fresh', tone='success')\n",
        encoding="utf-8",
    )
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "summary:\n"
        "  - \"{{ finance_owner() }}\"\n"
        "sections:\n"
        "  - title: Status\n"
        "    items:\n"
        "      - component: \"{{ stale_data_warning(25) }}\"\n"
        "      - chart: revenue\n",
        encoding="utf-8",
    )

    generate_dashboards(project)

    html = (
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "Finance Analytics" in html
    assert "Freshness" in html
    assert "Data is stale" in html
    assert "tone-warning" in html


def test_dashboard_generation_supports_artifact_aware_macros_and_filters(
    tmp_path: Path,
) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "macros.py").write_text(
        "from glyf.dashboard import components as c\n\n"
        "def latest_revenue_summary(ctx):\n"
        "    latest_revenue = ctx.latest_value('revenue', 'revenue')\n"
        "    return c.label_value('Latest revenue', latest_revenue)\n\n"
        "def health_emoji(ctx):\n"
        "    latest_revenue = float(ctx.latest_value('revenue', 'revenue'))\n"
        "    return '🟢 Healthy' if latest_revenue >= 2000 else '🟠 Watch'\n",
        encoding="utf-8",
    )
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "filters:\n"
        "  - field: month\n"
        "    values: source(revenue, month)\n"
        "summary:\n"
        "  - \"{{ latest_revenue_summary() }}\"\n"
        "sections:\n"
        "  - title: Status\n"
        "    items:\n"
        "      - component: \"{{ alert.threshold('revenue', 'revenue', 2000, op='gte', title='Revenue threshold') }}\"\n"
        "      - component: \"{{ ui.badge(health_emoji(), tone='info') }}\"\n"
        "      - component: \"{{ ui.list(source('revenue', 'month'), title='Months from chart data') }}\"\n"
        "      - chart: revenue\n",
        encoding="utf-8",
    )

    generate_dashboards(project)

    html = (
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "Latest revenue" in html
    assert "2400" in html
    assert "Revenue threshold" in html
    assert "Threshold satisfied" in html
    assert "🟢 Healthy" in html
    assert "Months from chart data" in html
    assert "2026-01, 2026-02, 2026-03, 2026-04" in html
    assert 'title="source(revenue, month)"' in html


def test_dashboard_generation_reports_invalid_macro(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "sections:\n"
        "  - title: Status\n"
        "    items:\n"
        "      - component: \"{{ missing_macro() }}\"\n",
        encoding="utf-8",
    )

    with pytest.raises(DashboardGenerationError, match="missing_macro"):
        generate_dashboards(project)


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
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "--glyf-columns: 2" in html
    assert "--glyf-column-template: minmax(0, 30fr) minmax(0, 70fr)" in html
    css = (project / "target" / "glyf" / "assets" / "dashboard.css").read_text(
        encoding="utf-8"
    )
    assert "@media (max-width: 760px)" in css


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
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert "--glyf-column-template: minmax(0, 30fr) minmax(0, 70fr)" in html
    assert 'style="--glyf-columns: 2' in html


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
