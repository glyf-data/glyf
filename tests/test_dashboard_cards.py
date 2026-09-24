"""Cards that say more: owners, metric deltas, status cards, notes, chart tools."""

import json
from pathlib import Path

import pytest

from glyf.dashboard import components as c
from glyf.dashboard.generator import generate_dashboards
from glyf.dashboard.loader import load_dashboard
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _html(project: Path) -> str:
    return (project / "target" / "glyf" / "dashboards" / "executive.html").read_text(
        encoding="utf-8"
    )


def test_owner_and_metric_delta_parse(tmp_path: Path) -> None:
    dashboard = load_dashboard(
        _write(
            tmp_path / "product.yml",
            "name: product\ntitle: Product\nowner: Growth team\n"
            "sections:\n  - items:\n      - metric:\n          label: Activation rate\n"
            "          value: '28.5%'\n          delta: '-1.7 pts'\n          trend: down\n",
        )
    )

    assert dashboard.owner == "Growth team"
    item = dashboard.sections[0].items[0]
    assert (item.delta, item.trend) == ("-1.7 pts", "down")


@pytest.mark.parametrize(
    ("metric", "message"),
    [
        ("delta: '-1'\n          trend: sideways", "metric.trend' to be one of"),
        ("trend: down", "to come with a"),
    ],
)
def test_metric_trend_is_checked(tmp_path: Path, metric: str, message: str) -> None:
    path = _write(
        tmp_path / "product.yml",
        "name: product\ntitle: Product\nsections:\n  - items:\n      - metric:\n"
        f"          label: Rate\n          value: '1'\n          {metric}\n",
    )
    with pytest.raises(ValueError, match=message):
        load_dashboard(path)


def test_owner_must_be_a_string(tmp_path: Path) -> None:
    path = _write(tmp_path / "product.yml", "name: product\ntitle: Product\nowner: 7\n")
    with pytest.raises(ValueError, match="'owner' to be a string"):
        load_dashboard(path)


def test_alert_and_list_carry_a_metric_and_a_note() -> None:
    alert = c.alert("Below target.", tone="warning", metric="37.4%", note="Worked out at build.")
    notes = c.values_list(["W06: shipped."], title="Notes", note="Written by hand.")

    assert (alert.value, alert.note) == ("37.4%", "Worked out at build.")
    assert notes.note == "Written by hand."
    assert c.ensure_component(
        {"kind": "alert", "text": "Below", "value": "37.4%", "note": "n"}, "macro"
    ).value == "37.4%"


def test_dashboard_renders_owner_delta_status_card_and_notes(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    _write(
        project / "dashboards" / "executive.yml",
        "name: executive\ntitle: Executive\nowner: Growth team\n"
        "sections:\n  - items:\n"
        "      - metric:\n          label: Activation rate\n          value: '28.5%'\n"
        "          delta: '-1.7 pts vs last week'\n          trend: down\n"
        "      - component: \"{{ alert.warning('Below target.', 'Health', metric='37.4%', note='Worked out at build.') }}\"\n"
        "      - component: \"{{ ui.list(['W06: shipped.'], title='Notes', note='Written by hand.') }}\"\n"
        "      - chart: revenue\n",
    )

    generate_dashboards(project)
    html = _html(project)

    assert "Owner <strong>Growth team</strong>" in html
    assert "glyf-kpi-compare glyf-kpi-compare--down" in html
    assert "-1.7 pts vs last week" in html
    assert "glyf-status-card glyf-status--warning" in html
    assert '<div class="glyf-status-value">37.4%</div>' in html
    assert html.count("glyf-component-footnote") == 2
    assert "Written by hand." in html


def test_owner_defaults_to_the_data_team(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    generate_dashboards(project)

    assert "Owner <strong>data team</strong>" in _html(project)


def test_every_chart_gets_download_and_full_screen(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)
    generate_dashboards(project)
    html = _html(project)

    assert "data-glyf-chart-download" in html
    assert "data-glyf-chart-expand" in html
    # Only a chart that zooms has a zoom lock to offer.
    assert "data-glyf-zoom-lock aria-pressed" not in html


def test_a_zooming_chart_starts_with_its_zoom_locked(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    _write(
        project / "visualisations" / "revenue.ggsql",
        "select month, revenue from {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\nDRAW scatter\nINTERACT tooltip, zoom\n",
    )
    render_project(project)
    generate_dashboards(project)
    html = _html(project)

    assert 'class="glyf-card glyf-chart-card" data-glyf-zoom-locked' in html
    assert 'data-glyf-zoom-lock aria-pressed="true"' in html
    assert "data-glyf-zoom-reset" in html

    spec = json.loads(
        (project / "target" / "glyf" / "data" / "vega" / "revenue.vega.json").read_text()
    )
    # The outermost points stay whole when the zooming chart clips its marks.
    for channel in ("x", "y"):
        assert spec["encoding"][channel]["scale"] == {"padding": 12, "nice": False}
