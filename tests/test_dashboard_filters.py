"""Filters that filter: redraw what carries the column, dim what does not.

The page holds the rows a chart was drawn from, so a filter can redraw the
chart in the browser from its Vega spec, hide a table's rows, and say on
every other card that it does not apply. These tests check the plan the page
is built from and the markup the script drives; the script itself runs in a
browser, not here.
"""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from glyf.config import ExportConfig, GlyfConfig
from glyf.dashboard.artifacts import load_chart_artifact
from glyf.dashboard.filters import plan_filters
from glyf.dashboard.generator import generate_dashboards
from glyf.dashboard.loader import load_dashboard
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

TABLE = (
    "SELECT month, revenue FROM {{ ref('fct_orders') }} ORDER BY month\n\n"
    "VISUALISE month, revenue\nDRAW table\n"
)
KPI = (
    "SELECT sum(revenue) AS revenue FROM {{ ref('fct_orders') }}\n\n"
    "VISUALISE revenue AS value\nDRAW kpi\n"
)


def _project(tmp_path: Path, *, filters: str, row_data: str = "include") -> tuple[Path, GlyfConfig]:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "months.ggsql").write_text(TABLE, encoding="utf-8")
    (project / "visualisations" / "total.ggsql").write_text(KPI, encoding="utf-8")
    (project / "dashboards" / "executive.yml").write_text(
        f"name: executive\ntitle: Executive\n{filters}charts:\n  - revenue\n  - months\n  - total\n",
        encoding="utf-8",
    )
    config = replace(GlyfConfig(), export=ExportConfig(row_data=row_data))
    render_project(project, config)
    return project, config


def test_every_drawn_chart_keeps_its_vega_spec_now(tmp_path: Path) -> None:
    """A filter redraws from the spec, so a chart without INTERACT has one too."""
    project = copy_basic_project(tmp_path)
    render_project(project)

    metadata = json.loads((project / "target" / "glyf" / "charts" / "revenue.json").read_text(encoding="utf-8"))
    assert metadata["vega_json_path"] == "target/glyf/data/vega/revenue.vega.json"
    assert "interactions" not in metadata
    assert (project / metadata["vega_json_path"]).exists()


def test_the_plan_says_how_each_card_takes_a_filter(tmp_path: Path) -> None:
    project, config = _project(tmp_path, filters="filters:\n  - field: month\n    values: source(revenue, month)\n  - field: region\n    values: [north]\n")
    dashboard = load_dashboard(project / "dashboards" / "executive.yml")
    charts = {name: load_chart_artifact(project, name, config) for name in ("revenue", "months", "total")}

    plan = plan_filters(dashboard, charts)

    assert plan.live
    assert plan.modes("revenue") == "month:vega region:none"
    assert plan.modes("months") == "month:table region:none"
    assert plan.modes("total") == "month:none region:none", "a kpi is one number"
    assert plan.vega_charts == frozenset({"revenue"})


def test_the_page_carries_selects_specs_and_card_hooks(tmp_path: Path) -> None:
    project, config = _project(tmp_path, filters="filters:\n  - field: month\n    values: source(revenue, month)\n")

    generate_dashboards(project, config)

    html = (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(encoding="utf-8")
    assert 'data-glyf-filter-select="month"' in html
    assert '<option value="">All</option>' in html and '<option value="2026-03">2026-03</option>' in html
    assert 'data-glyf-chart="revenue" data-glyf-filters="month:vega"' in html
    assert 'data-glyf-chart="months" data-glyf-filters="month:table"' in html
    assert 'data-glyf-chart="total" data-glyf-filters="month:none"' in html
    # The static chart keeps its picture and gains a hidden spec to redraw from.
    assert 'data-glyf-still' in html and 'data-glyf-filter-chart' in html
    assert 'id="chart-revenue-spec"' in html
    assert "https://cdn.jsdelivr.net/npm/vega@6" in html, "the runtime is needed to redraw"
    assert 'toString(datum[' in html


def test_a_filter_can_be_narrowed_to_named_charts(tmp_path: Path) -> None:
    project, config = _project(tmp_path, filters="filters:\n  - field: month\n    values: [2026-01]\n    charts: [months]\n")
    dashboard = load_dashboard(project / "dashboards" / "executive.yml")
    assert dashboard.filters[0].charts == ("months",)

    generate_dashboards(project, config)

    html = (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(encoding="utf-8")
    assert 'data-glyf-chart="months" data-glyf-filters="month:table"' in html
    assert 'data-glyf-chart="revenue" data-glyf-filters=' not in html
    assert "vega@6" not in html, "no chart is redrawn, so no runtime"


def test_a_page_without_filters_carries_no_runtime_or_specs(tmp_path: Path) -> None:
    project, config = _project(tmp_path, filters="")

    generate_dashboards(project, config)

    html = (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(encoding="utf-8")
    assert "vega@6" not in html and "vegaEmbed" not in html
    assert 'id="chart-revenue-spec"' not in html
    assert "data-glyf-filter-select" not in html


def test_exclude_keeps_the_filters_as_labels(tmp_path: Path) -> None:
    """No rows are published, so nothing can be redrawn; the filters stay labels."""
    project = copy_basic_project(tmp_path)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive\nfilters:\n  - field: month\n    values: [2026-01]\ncharts:\n  - revenue\n",
        encoding="utf-8",
    )
    config = replace(GlyfConfig(), export=ExportConfig(row_data="exclude"))
    render_project(project, config)

    generate_dashboards(project, config)

    html = (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(encoding="utf-8")
    assert "data-glyf-filter-select" not in html
    assert "no chart on this page publishes these columns" in html
    assert "vega@6" not in html


def test_minimal_filters_only_the_encoded_columns(tmp_path: Path) -> None:
    (tmp_path / "x").mkdir()
    project = copy_basic_project(tmp_path / "x")
    (project / "visualisations" / "revenue.ggsql").write_text(
        "SELECT month, revenue, 'x' AS region FROM {{ ref('fct_orders') }}\n\nVISUALISE month AS x, revenue AS y\nDRAW line\n",
        encoding="utf-8",
    )
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive\nfilters:\n  - field: region\n    values: [x]\n  - field: month\n    values: [2026-01]\ncharts:\n  - revenue\n",
        encoding="utf-8",
    )
    config = replace(GlyfConfig(), export=ExportConfig(row_data="minimal"))
    render_project(project, config)
    dashboard = load_dashboard(project / "dashboards" / "executive.yml")

    plan = plan_filters(dashboard, {"revenue": load_chart_artifact(project, "revenue", config)})

    assert plan.modes("revenue") == "region:none month:vega"


def test_a_bad_charts_list_is_rejected(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive\nfilters:\n  - field: month\n    values: [a]\n    charts: revenue\ncharts:\n  - revenue\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="filters\\[1\\].charts"):
        load_dashboard(project / "dashboards" / "executive.yml")
