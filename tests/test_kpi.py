"""The kpi tile: one number, and how it compares.

The second draw type glyf does not draw. A kpi is the single row its query
returns, shown as a tile: the `value` column as a headline and, with a
`compare` column, the difference and its direction. It follows the table's
path through the build: an HTML fragment beside the data JSON, a card on the
dashboard, `png` and `svg` null in the bundle, and a diff by its rows.
"""

import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyf.cli import app
from glyf.config import ExportConfig, GlyfConfig
from glyf.dashboard.artifacts import ChartArtifactError, load_chart_artifact
from glyf.dashboard.generator import generate_dashboards
from glyf.diff import compare_builds, write_report
from glyf.exporter import export_site
from glyf.ggsql.kpi import format_number
from glyf.ggsql.kpi import build_tile
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql
from glyf.pipeline import RenderError, render_project
from tests.helpers import copy_basic_project

runner = CliRunner()

KPI = (
    "SELECT sum(revenue) AS revenue, 6000 AS previous\n"
    "FROM {{ ref('fct_orders') }}\n"
    "\n"
    "VISUALISE revenue AS value, previous AS compare\n"
    "DRAW kpi\n"
    "LABEL title => 'Revenue'\n"
    "LABEL compare => 'vs last quarter'\n"
)
VALUE_ONLY = (
    "SELECT count(*) AS months FROM {{ ref('fct_orders') }}\n\nVISUALISE months AS value\nDRAW kpi\n"
)


# --- the chart language -----------------------------------------------------


def test_a_kpi_binds_a_value_and_an_optional_comparison() -> None:
    chart = parse_ggsql(KPI, name="revenue_kpi")

    assert chart.draw_type == "kpi"
    assert chart.is_kpi and not chart.has_picture
    assert chart.field_for_role("value") == "revenue"
    assert chart.field_for_role("compare") == "previous"

    alone = parse_ggsql(VALUE_ONLY, name="months")
    assert alone.field_for_role("compare") is None


@pytest.mark.parametrize(
    ("visual", "message"),
    [
        ("VISUALISE a AS x, b AS y\nDRAW kpi\n", "kpi does not take a 'x' mapping; it takes value, compare"),
        ("VISUALISE a AS compare\nDRAW kpi\n", "kpi requires a value mapping"),
        ("VISUALISE a, b\nDRAW kpi\n", "kpi maps each column to a role \\(value, compare\\); write 'a AS value'"),
        ("VISUALISE a AS value\nDRAW kpi\nINTERACT zoom\n", "kpi takes no INTERACT"),
    ],
)
def test_a_kpi_rejects_what_it_cannot_show(visual: str, message: str) -> None:
    with pytest.raises(GgsqlParseError, match=message):
        parse_ggsql(f"SELECT a, b FROM t\n\n{visual}", name="c")


def test_a_headline_number_reads_with_separators_and_keeps_its_precision() -> None:
    assert format_number(2314900) == "2,314,900"
    assert format_number(1234.5) == "1,234.5"
    assert format_number(-250, signed=True) == "-250"
    assert format_number(250, signed=True) == "+250"
    assert format_number("Pro") == "Pro"
    assert format_number(None) == ""
    assert format_number(True) == "true"


# --- the build --------------------------------------------------------------


def test_a_kpi_is_written_as_a_tile_not_a_picture(tmp_path: Path) -> None:
    project = _project_with(tmp_path, KPI, "revenue_kpi")

    result = render_project(project)

    charts = project / "target" / "glyf" / "charts"
    kpi = next(rendered for rendered in result.charts if rendered.chart.is_kpi)
    assert kpi.artifacts.kpi_html == charts / "revenue_kpi.kpi.html"
    assert not (charts / "revenue_kpi.png").exists()
    assert not (charts / "revenue_kpi.svg").exists()
    assert json.loads((charts / "revenue_kpi.json").read_text(encoding="utf-8")) == {
        "name": "revenue_kpi",
        "title": "Revenue",
        "chart_type": "kpi",
        "value": "revenue",
        "compare": "previous",
        "compiled_sql_path": "target/glyf/compiled/revenue_kpi.sql",
        "data_json_path": "target/glyf/data/normalized/revenue_kpi.data.json",
        "metadata_path": "target/glyf/charts/revenue_kpi.json",
        "kpi_html_path": "target/glyf/charts/revenue_kpi.kpi.html",
        "lineage": {"models": {"fct_orders": {"parents": [], "path": None}}, "sources": []},
    }


def test_the_tile_shows_the_value_the_delta_and_its_direction(tmp_path: Path) -> None:
    """The fixture's revenue sums to 7,500 against a comparison of 6,000."""
    project = _project_with(tmp_path, KPI, "revenue_kpi")

    render_project(project)

    html = _fragment(project, "revenue_kpi")
    assert html.startswith('<figure class="glyf-kpi" data-glyf-kpi="revenue_kpi">')
    assert '<div class="glyf-kpi-value">7,500</div>' in html
    assert 'class="glyf-kpi-compare glyf-kpi-compare--up"' in html
    assert "&#9650; +1,500 (+25.0%)" in html
    assert "vs last quarter 6,000" in html
    assert "<script" not in html


def test_a_fall_a_tie_and_a_missing_comparison_each_read_as_such(tmp_path: Path) -> None:
    down = KPI.replace("6000 AS previous", "9000 AS previous")
    project = _project_with(tmp_path, down, "down")
    render_project(project)
    html = _fragment(project, "down")
    assert "glyf-kpi-compare--down" in html and "&#9660; -1,500 (-16.7%)" in html

    flat = KPI.replace("6000 AS previous", "7500 AS previous")
    (project / "visualisations" / "down.ggsql").write_text(flat, encoding="utf-8")
    render_project(project)
    html = _fragment(project, "down")
    assert "glyf-kpi-compare--flat" in html and "&#8212; +0 (+0.0%)" in html

    nothing = KPI.replace("6000 AS previous", "NULL AS previous")
    (project / "visualisations" / "down.ggsql").write_text(nothing, encoding="utf-8")
    render_project(project)
    html = _fragment(project, "down")
    assert "glyf-kpi-compare" not in html, "no comparison to show"

    zero = KPI.replace("6000 AS previous", "0 AS previous")
    (project / "visualisations" / "down.ggsql").write_text(zero, encoding="utf-8")
    render_project(project)
    html = _fragment(project, "down")
    assert "+7,500</span>" in html and "%" not in html, "a share of nothing is not a number"


def test_a_value_alone_is_just_the_number(tmp_path: Path) -> None:
    project = _project_with(tmp_path, VALUE_ONLY, "months")

    render_project(project)

    html = _fragment(project, "months")
    assert '<div class="glyf-kpi-value">4</div>' in html
    assert "glyf-kpi-compare" not in html
    metadata = json.loads(
        (project / "target" / "glyf" / "charts" / "months.json").read_text(encoding="utf-8")
    )
    assert metadata["compare"] is None


def test_more_than_one_row_fails_the_build_naming_the_chart(tmp_path: Path) -> None:
    text = "SELECT revenue, 1 AS previous FROM {{ ref('fct_orders') }}\n\nVISUALISE revenue AS value\nDRAW kpi\n"
    project = _project_with(tmp_path, text, "each")

    with pytest.raises(RenderError, match="each.ggsql kpi rendering failed: the query returned 4 rows and a kpi shows one"):
        render_project(project)
    assert not (project / "target" / "glyf" / "charts" / "each.kpi.html").exists()


def test_validate_mode_checks_the_columns_without_a_row(tmp_path: Path) -> None:
    text = KPI.replace("revenue AS value", "margin AS value")
    project = _project_with(tmp_path, text, "bad")
    config = replace(GlyfConfig(), execution=replace(GlyfConfig().execution, mode="validate"))

    with pytest.raises(RenderError, match="missing chart column 'margin'"):
        render_project(project, config)

    (project / "visualisations" / "bad.ggsql").write_text(KPI, encoding="utf-8")
    assert render_project(project, config).validated_only


def test_a_kpi_survives_row_data_exclude(tmp_path: Path) -> None:
    """One number is what the tile shows, the way a PNG shows its values."""
    project = _project_with(tmp_path, KPI, "revenue_kpi")
    config = replace(GlyfConfig(), export=ExportConfig(row_data="exclude"))

    render_project(project, config)
    _dashboard_with(project, "revenue", "revenue_kpi")
    generate_dashboards(project, config)
    export_site(project, config=config)

    site = project / "target" / "glyf" / "site"
    assert (site / "charts" / "revenue_kpi.kpi.html").exists()
    assert "7,500" in (site / "dashboards" / "executive.html").read_text(encoding="utf-8")


# --- the dashboard, the bundle, the site, the diff --------------------------


def test_the_dashboard_shows_the_tile_with_its_title(tmp_path: Path) -> None:
    project = _project_with(tmp_path, KPI, "revenue_kpi")
    render_project(project)
    _dashboard_with(project, "revenue", "revenue_kpi")

    generate_dashboards(project)

    html = (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(
        encoding="utf-8"
    )
    assert 'class="glyf-card glyf-kpi-card"' in html
    assert '<div class="glyf-kpi-label">Revenue</div>' in html
    assert 'data-glyf-kpi="revenue_kpi"' in html
    assert "[data-glyf-table]" not in html

    artifact = load_chart_artifact(project, "revenue_kpi")
    assert artifact.metadata.is_kpi and artifact.metadata.value == "revenue"
    assert artifact.kpi_html is not None and artifact.svg is None
    (project / "target" / "glyf" / "charts" / "revenue_kpi.kpi.html").unlink()
    with pytest.raises(ChartArtifactError, match="missing kpi artifact"):
        load_chart_artifact(project, "revenue_kpi")


def test_the_bundle_and_the_site_carry_the_tile(tmp_path: Path) -> None:
    project = _project_with(tmp_path, KPI, "revenue_kpi")
    render_project(project)
    _dashboard_with(project, "revenue", "revenue_kpi")
    generate_dashboards(project)
    export_site(project)

    bundle = json.loads((project / "target" / "glyf" / "bundle.json").read_text(encoding="utf-8"))
    kpi = bundle["charts"]["revenue_kpi"]
    assert kpi["chart_type"] == "kpi"
    assert kpi["fields"] == {"value": "revenue", "compare": "previous"}
    assert kpi["artifacts"]["png"] is None and kpi["artifacts"]["svg"] is None
    assert kpi["artifacts"]["kpi"] == "charts/revenue_kpi.kpi.html"
    assert "kpi" not in bundle["charts"]["revenue"]["artifacts"]

    site = project / "target" / "glyf" / "site"
    assert (site / "charts" / "revenue_kpi.kpi.html").exists()
    metadata = json.loads((site / "charts" / "revenue_kpi.json").read_text(encoding="utf-8"))
    assert metadata["kpi_html_path"] == "charts/revenue_kpi.kpi.html"


def test_diff_judges_a_kpi_by_its_tile_and_says_the_value_changed(tmp_path: Path) -> None:
    project = _project_with(tmp_path, KPI, "revenue_kpi")
    render_project(project)
    baseline = tmp_path / "baseline"
    shutil.copytree(project / "target" / "glyf", baseline)
    (project / "seeds" / "fct_orders.csv").write_text(
        "month,revenue\n2026-01,1200\n2026-02,1800\n2026-03,2100\n2026-04,3000\n", encoding="utf-8"
    )
    render_project(project)

    diff = compare_builds(baseline, project / "target" / "glyf")
    page = write_report(diff, tmp_path / "report")

    kpi = next(chart for chart in diff.with_status("changed") if chart.name == "revenue_kpi")
    assert kpi.kpi and not kpi.table and kpi.is_fragment
    assert kpi.reasons == ("the rows changed",)
    document = json.loads((page.parent / "diff.json").read_text(encoding="utf-8"))
    assert document["charts"]["revenue_kpi"]["kpi"] is True
    assert document["charts"]["revenue_kpi"]["fragments"]["after"] == "fragments/revenue_kpi.after.html"
    assert "| kpi value |" in (page.parent / "summary.md").read_text(encoding="utf-8")
    assert "the value changed</span>" in page.read_text(encoding="utf-8")

    result = runner.invoke(app, ["diff", "--project-dir", str(project), "--baseline", str(baseline)])
    assert "~ revenue_kpi: the value changed (the rows changed)" in result.output


def test_render_says_it_wrote_a_kpi(tmp_path: Path) -> None:
    project = _project_with(tmp_path, KPI, "revenue_kpi")

    result = runner.invoke(app, ["render", "--project", str(project)])

    assert result.exit_code == 0, result.output
    assert "✓ wrote KPI HTML (1)" in result.output


# --- helpers ----------------------------------------------------------------


def _project_with(tmp_path: Path, text: str, name: str) -> Path:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / f"{name}.ggsql").write_text(text, encoding="utf-8")
    return project


def _dashboard_with(project: Path, *charts: str) -> None:
    listed = "\n".join(f"  - {chart}" for chart in charts)
    (project / "dashboards" / "executive.yml").write_text(
        f"name: executive\ntitle: Executive\ncharts:\n{listed}\n", encoding="utf-8"
    )


def _fragment(project: Path, name: str) -> str:
    return (project / "target" / "glyf" / "charts" / f"{name}.kpi.html").read_text(encoding="utf-8")


def test_a_delta_is_as_precise_as_the_numbers_it_compares() -> None:
    """89.9 - 92.3 is -2.3999999999999915 in floating point; the tile says -2.4."""
    chart = parse_ggsql(
        "SELECT 1\n\nVISUALISE rate AS value, previous AS compare\nDRAW kpi\n", name="k"
    )

    tile = build_tile(chart, {"rate": 89.9, "previous": 92.3})
    spend = build_tile(chart, {"rate": 263.85, "previous": 215.62})
    whole = build_tile(chart, {"rate": 21.8, "previous": 20})

    assert tile.comparison is not None and tile.comparison.delta_text == "-2.4"
    assert spend.comparison is not None and spend.comparison.delta_text == "+48.23"
    assert whole.comparison is not None and whole.comparison.delta_text == "+1.8"
