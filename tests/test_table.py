"""The table chart: the one draw type glyf does not draw.

A table is its rows. It has no axes and no picture: `VISUALISE` lists columns
without roles (`VISUALISE region, revenue`, or `VISUALISE *` for every column
the query returns), the artifact is an HTML fragment beside the data JSON, and
the dashboard inlines it where a chart card holds an SVG. Three calls were made
on the way here and these tests pin them: `VISUALISE *` is allowed, a table
over `render.max_rows` fails the build the way `max_marks` does for a picture,
and no PNG exists for a table, ever.
"""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyf.bundle import write_bundle_manifest
from glyf.cli import app
from glyf.config import ConfigError, ExportConfig, GlyfConfig, RenderConfig, load_config
from glyf.dashboard.artifacts import ChartArtifactError, load_chart_artifact
from glyf.dashboard.generator import DashboardGenerationError, generate_dashboards
from glyf.exporter import export_site
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql
from glyf.ggsql.renderer import missing_columns, prune_to_encoded_columns, required_columns
from glyf.execution.result import QueryResult
from glyf.pipeline import RenderError, render_project
from tests.helpers import copy_basic_project

runner = CliRunner()

TABLE = (
    "SELECT month, revenue\n"
    "FROM {{ ref('fct_orders') }}\n"
    "ORDER BY revenue DESC\n"
    "\n"
    "VISUALISE month, revenue\n"
    "DRAW table\n"
    "LABEL title => 'Best months'\n"
    "LABEL revenue => 'Revenue (USD)'\n"
)

EVERY_COLUMN = (
    "SELECT month, revenue, revenue * 2 AS doubled\n"
    "FROM {{ ref('fct_orders') }}\n"
    "ORDER BY month\n"
    "\n"
    "VISUALISE *\n"
    "DRAW table\n"
)


# --- the chart language -----------------------------------------------------


def test_a_table_lists_columns_without_roles() -> None:
    chart = parse_ggsql(TABLE, name="best_months")

    assert chart.draw_type == "table"
    assert chart.is_table
    assert chart.table_columns == ("month", "revenue")
    assert [mapping.role for mapping in chart.visualise] == ["column", "column"]
    assert chart.column_label("revenue") == "Revenue (USD)"
    assert chart.column_label("month") == "month"
    assert chart.has_order_by


def test_visualise_star_lists_every_column_the_query_returns() -> None:
    chart = parse_ggsql(EVERY_COLUMN, name="everything")

    assert chart.lists_every_column
    assert chart.table_columns == ()
    assert required_columns(chart) == ()
    assert missing_columns(chart, ("a", "b")) == ()


@pytest.mark.parametrize(
    ("visual", "message"),
    [
        (
            "VISUALISE month AS x, revenue AS y\nDRAW table\n",
            "table lists its columns without roles",
        ),
        ("VISUALISE *, month\nDRAW table\n", "VISUALISE \\* already lists every column"),
        ("VISUALISE month, month\nDRAW table\n", "lists column 'month' twice"),
        ("VISUALISE month\nDRAW table\nINTERACT tooltip\n", "table takes no INTERACT"),
        (
            "VISUALISE month, revenue\nDRAW bar\n",
            "bar maps each column to a role \\(x, y, color\\); write 'month AS x'",
        ),
    ],
)
def test_the_table_and_the_other_charts_reject_each_others_visualise(
    visual: str, message: str
) -> None:
    with pytest.raises(GgsqlParseError, match=message):
        parse_ggsql(f"SELECT month, revenue FROM t\n\n{visual}", name="c")


def test_the_supported_chart_types_now_name_the_table() -> None:
    with pytest.raises(GgsqlParseError, match="scatter, table"):
        parse_ggsql("SELECT 1\n\nVISUALISE a AS x, b AS y\nDRAW donut\n", name="c")


def test_a_table_is_never_pruned_past_the_columns_it_lists() -> None:
    """`export.row_data: minimal` keeps what the table shows, which is what it lists."""
    data = QueryResult.from_records(
        ("month", "revenue", "secret"), ({"month": "m", "revenue": 1, "secret": "s"},)
    )

    listed = prune_to_encoded_columns(parse_ggsql(TABLE, name="t"), data)
    assert listed.columns == ("month", "revenue")

    everything = prune_to_encoded_columns(parse_ggsql(EVERY_COLUMN, name="t"), data)
    assert everything.columns == ("month", "revenue", "secret")


# --- the build --------------------------------------------------------------


def test_a_table_is_written_as_rows_and_a_fragment_not_a_picture(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path)

    result = render_project(project)

    charts = project / "target" / "glyf" / "charts"
    table = next(rendered for rendered in result.charts if rendered.chart.is_table)
    assert table.artifacts.table_html == charts / "best_months.table.html"
    assert not (charts / "best_months.png").exists()
    assert not (charts / "best_months.svg").exists()

    metadata = json.loads((charts / "best_months.json").read_text(encoding="utf-8"))
    assert metadata == {
        "name": "best_months",
        "title": "Best months",
        "chart_type": "table",
        "columns": ["month", "revenue"],
        "compiled_sql_path": "target/glyf/compiled/best_months.sql",
        "data_json_path": "target/glyf/data/normalized/best_months.data.json",
        "metadata_path": "target/glyf/charts/best_months.json",
        "table_html_path": "target/glyf/charts/best_months.table.html",
        "lineage": {"models": {"fct_orders": {"parents": [], "path": None}}, "sources": []},
    }
    data = json.loads(
        (project / "target" / "glyf" / "data" / "normalized" / "best_months.data.json")
        .read_text(encoding="utf-8")
    )
    assert data["fields"] == ["month", "revenue"]
    assert [row["revenue"] for row in data["rows"]] == [2400, 2100, 1800, 1200]


def test_the_fragment_is_the_rows_in_the_query_order_with_labels_applied(
    tmp_path: Path,
) -> None:
    project = _project_with_table(tmp_path)

    render_project(project)

    html = _table_html(project, "best_months")
    assert html.startswith('<figure class="glyf-table" data-glyf-table="best_months">')
    assert "<script" not in html, "sorting is the dashboard page's, once"
    assert '<th scope="col" data-column="month" data-type="text" aria-sort="none">month</th>' in html
    assert (
        '<th scope="col" data-column="revenue" data-type="number" aria-sort="none" '
        'class="glyf-table-num">Revenue (USD)</th>'
    ) in html
    assert html.index("2400") < html.index("2100") < html.index("1800") < html.index("1200")
    assert '<td class="glyf-table-num">2400</td>' in html
    assert "4 rows</figcaption>" in html


def test_visualise_star_resolves_to_the_columns_the_query_returned(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path, EVERY_COLUMN, name="everything")

    render_project(project)

    metadata = json.loads(
        (project / "target" / "glyf" / "charts" / "everything.json").read_text(encoding="utf-8")
    )
    assert metadata["columns"] == ["month", "revenue", "doubled"]
    html = _table_html(project, "everything")
    assert 'data-column="doubled"' in html
    assert "<td class=\"glyf-table-num\">4800</td>" in html


def test_a_table_only_shows_the_columns_it_lists(tmp_path: Path) -> None:
    """The rows keep every column for the local build; the table shows its list."""
    text = TABLE.replace("SELECT month, revenue", "SELECT month, revenue, 'x' AS extra")
    project = _project_with_table(tmp_path, text)

    render_project(project)

    data = json.loads(
        (project / "target" / "glyf" / "data" / "normalized" / "best_months.data.json")
        .read_text(encoding="utf-8")
    )
    assert data["fields"] == ["month", "revenue", "extra"]
    html = _table_html(project, "best_months")
    assert "extra" not in html


def test_a_listed_column_the_query_does_not_return_fails_the_build(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path, TABLE.replace("VISUALISE month, revenue", "VISUALISE month, margin"))

    with pytest.raises(RenderError, match="missing table column 'margin'"):
        render_project(project)


def test_validate_mode_checks_a_tables_columns_without_writing_it(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path, TABLE.replace("VISUALISE month, revenue", "VISUALISE month, margin"))
    config = replace(GlyfConfig(), execution=replace(GlyfConfig().execution, mode="validate"))

    with pytest.raises(RenderError, match="missing chart column 'margin'"):
        render_project(project, config)

    (project / "visualisations" / "best_months.ggsql").write_text(TABLE, encoding="utf-8")
    result = render_project(project, config)
    assert result.validated_only
    assert not (project / "target" / "glyf" / "charts" / "best_months.table.html").exists()


def test_an_empty_cell_and_a_boolean_read_as_such(tmp_path: Path) -> None:
    text = (
        "SELECT month, CASE WHEN revenue > 2000 THEN revenue END AS big, revenue > 2000 AS is_big\n"
        "FROM {{ ref('fct_orders') }}\nORDER BY month\n\nVISUALISE *\nDRAW table\n"
    )
    project = _project_with_table(tmp_path, text, name="cells")

    render_project(project)

    html = _table_html(project, "cells")
    assert '<td class="glyf-table-num" data-empty="true"></td>' in html
    assert "<td>true</td>" in html and "<td>false</td>" in html


def test_a_table_without_an_order_by_says_so(tmp_path: Path) -> None:
    """A table's picture is its row order, so the order glyf chose is reported."""
    project = _project_with_table(tmp_path, TABLE.replace("ORDER BY revenue DESC\n", ""))

    result = render_project(project)

    assert any(
        "best_months.ggsql: the query has no ORDER BY" in warning for warning in result.warnings
    )


def test_a_stale_picture_goes_when_a_chart_becomes_a_table(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    charts = project / "target" / "glyf" / "charts"
    assert (charts / "revenue.png").exists()

    (project / "visualisations" / "revenue.ggsql").write_text(
        TABLE.replace("VISUALISE month, revenue", "VISUALISE month, revenue"),
        encoding="utf-8",
    )
    render_project(project)

    assert not (charts / "revenue.png").exists()
    assert not (charts / "revenue.svg").exists()
    assert (charts / "revenue.table.html").exists()

    (project / "visualisations" / "revenue.ggsql").write_text(
        (Path("examples/basic/visualisations/revenue.ggsql")).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    render_project(project)

    assert (charts / "revenue.png").exists()
    assert not (charts / "revenue.table.html").exists()


# --- render.max_rows --------------------------------------------------------


def test_a_table_over_max_rows_fails_the_build_naming_the_chart(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path)

    with pytest.raises(RenderError) as error:
        render_project(project, _render(max_rows=3))

    message = str(error.value)
    assert "best_months.ggsql would list 4 rows, more than the 3" in message
    assert "render.max_rows" in message
    assert not (project / "target" / "glyf" / "charts" / "best_months.table.html").exists()


def test_a_table_that_exactly_fills_max_rows_is_written(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path)

    render_project(project, _render(max_rows=4))

    assert (project / "target" / "glyf" / "charts" / "best_months.table.html").exists()


def test_max_rows_bounds_tables_only(tmp_path: Path) -> None:
    """The line chart in the same project draws four marks and is not a table."""
    project = _project_with_table(tmp_path, EVERY_COLUMN.replace("\nVISUALISE *\nDRAW table\n", "\nVISUALISE month AS x, revenue AS y\nDRAW bar\n"), name="bars")

    render_project(project, _render(max_rows=1))

    assert (project / "target" / "glyf" / "charts" / "bars.png").exists()


def test_max_rows_defaults_to_a_thousand_and_can_be_removed(tmp_path: Path) -> None:
    assert RenderConfig().max_rows == 1_000

    (tmp_path / "glyf.yml").write_text("render:\n  max_rows: null\n", encoding="utf-8")
    assert load_config(tmp_path).render.max_rows is None

    (tmp_path / "glyf.yml").write_text("render:\n  max_rows: 25\n", encoding="utf-8")
    assert load_config(tmp_path).render.max_rows == 25

    (tmp_path / "glyf.yml").write_text("render:\n  max_rows: 0\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="max_rows"):
        load_config(tmp_path)


# --- export.row_data: exclude -----------------------------------------------


def test_a_table_and_row_data_exclude_contradict_each_other(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path)
    config = replace(GlyfConfig(), export=ExportConfig(row_data="exclude"))

    with pytest.raises(RenderError, match="best_months.ggsql is a table, and export.row_data: exclude"):
        render_project(project, config)

    # ...and validate mode says so too, so CI catches it before any rows move.
    validate = replace(config, execution=replace(config.execution, mode="validate"))
    with pytest.raises(RenderError, match="is a table"):
        render_project(project, validate)


def test_the_dashboard_refuses_to_publish_a_table_under_exclude(tmp_path: Path) -> None:
    """A table rendered under one setting must not be published under another."""
    project = _project_with_table(tmp_path)
    render_project(project)
    _dashboard_with(project, "best_months")

    with pytest.raises(DashboardGenerationError, match="shows table 'best_months'"):
        generate_dashboards(project, replace(GlyfConfig(), export=ExportConfig(row_data="exclude")))


# --- the dashboard, the bundle and the site --------------------------------


def test_the_dashboard_inlines_the_table_and_sorts_it_once(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path)
    render_project(project)
    _dashboard_with(project, "revenue", "best_months")

    generate_dashboards(project)

    html = (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(
        encoding="utf-8"
    )
    assert 'class="glyf-card glyf-table-card"' in html
    assert "Best months" in html
    assert "Revenue (USD)" in html
    assert 'data-glyf-table="best_months"' in html
    assert html.count("[data-glyf-table]") == 1, "one sort script for every table"
    assert '<img src="../charts/revenue.png"' in html or "<svg" in html


def test_a_dashboard_without_a_table_carries_no_sort_script(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)

    generate_dashboards(project)

    html = (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(
        encoding="utf-8"
    )
    assert "[data-glyf-table]" not in html


def test_the_loaded_artifact_carries_the_fragment(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path)
    render_project(project)

    artifact = load_chart_artifact(project, "best_months")

    assert artifact.metadata.is_table
    assert artifact.metadata.columns == ("month", "revenue")
    assert artifact.metadata.png_path is None
    assert artifact.svg is None
    assert artifact.table_html is not None and "<table>" in artifact.table_html

    (project / "target" / "glyf" / "charts" / "best_months.table.html").unlink()
    with pytest.raises(ChartArtifactError, match="missing table artifact"):
        load_chart_artifact(project, "best_months")


def test_the_bundle_lists_a_tables_columns_and_no_picture(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path)
    render_project(project)
    _dashboard_with(project, "revenue", "best_months")
    generate_dashboards(project)

    bundle = json.loads(
        (project / "target" / "glyf" / "bundle.json").read_text(encoding="utf-8")
    )

    table = bundle["charts"]["best_months"]
    assert table["chart_type"] == "table"
    assert table["fields"] == {"columns": ["month", "revenue"]}
    assert table["artifacts"]["png"] is None
    assert table["artifacts"]["svg"] is None
    assert table["artifacts"]["table"] == "charts/best_months.table.html"
    assert table["artifacts"]["data"] == "data/normalized/best_months.data.json"
    # A drawn chart's entry is unchanged.
    assert bundle["charts"]["revenue"]["fields"] == {"x": "month", "y": "revenue"}
    assert "table" not in bundle["charts"]["revenue"]["artifacts"]


def test_the_site_publishes_the_fragment_beside_the_metadata(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path)
    render_project(project)
    _dashboard_with(project, "revenue", "best_months")
    generate_dashboards(project)

    export_site(project)

    site = project / "target" / "glyf" / "site"
    assert (site / "charts" / "best_months.table.html").exists()
    assert not (site / "charts" / "best_months.png").exists()
    metadata = json.loads((site / "charts" / "best_months.json").read_text(encoding="utf-8"))
    assert metadata["table_html_path"] == "charts/best_months.table.html"
    assert "png_path" not in metadata
    bundle = json.loads((site / "bundle.json").read_text(encoding="utf-8"))
    assert bundle["charts"]["best_months"]["artifacts"]["table"] == (
        "charts/best_months.table.html"
    )


def test_render_says_it_wrote_a_table(tmp_path: Path) -> None:
    project = _project_with_table(tmp_path)

    result = runner.invoke(app, ["render", "--project", str(project)])

    assert result.exit_code == 0, result.output
    assert "✓ rendered PNG/SVG" in result.output
    assert "✓ wrote table HTML (1)" in result.output


# --- helpers ----------------------------------------------------------------


def _project_with_table(tmp_path: Path, text: str = TABLE, name: str = "best_months") -> Path:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / f"{name}.ggsql").write_text(text, encoding="utf-8")
    return project


def _dashboard_with(project: Path, *charts: str) -> None:
    listed = "\n".join(f"  - {chart}" for chart in charts)
    (project / "dashboards" / "executive.yml").write_text(
        f"name: executive\ntitle: Executive\ncharts:\n{listed}\n", encoding="utf-8"
    )


def _table_html(project: Path, name: str) -> str:
    return (project / "target" / "glyf" / "charts" / f"{name}.table.html").read_text(
        encoding="utf-8"
    )


def _render(**render: object) -> GlyfConfig:
    return GlyfConfig(render=replace(RenderConfig(), **render))
