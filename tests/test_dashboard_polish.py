"""The reader's switch and the little colour: what the page carries for them."""

from pathlib import Path

from glyf.dashboard.generator import generate_dashboards
from glyf.dashboard.renderer import tag_tone
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project


def _html(project: Path, page: str = "dashboards/executive.html") -> str:
    return (project / "target" / "glyf" / page).read_text(encoding="utf-8")


def test_every_page_carries_the_theme_switch(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_project(project)

    generate_dashboards(project)

    for page in ("dashboards/executive.html", "index.html"):
        html = _html(project, page)
        assert "data-glyf-theme-toggle" in html, page
        assert 'localStorage.getItem("glyf-theme")' in html, page
        assert "glyf-theme-icon--dark" in html and "glyf-theme-icon--light" in html, page


def test_a_static_page_re_themes_svgs_and_never_names_vega(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "SELECT month, revenue FROM {{ ref('fct_orders') }}\n\nVISUALISE month AS x, revenue AS y\nDRAW line\n",
        encoding="utf-8",
    )
    render_project(project)
    generate_dashboards(project)

    html = _html(project)
    assert '["stroke", "#d9e2ec", "#3f3f46"]' in html
    assert "vegaEmbed" not in html


def test_the_pill_and_tags_carry_a_tint(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive\ntags:\n  - finance\n  - demo\ntoolbar:\n  visibility: private\ncharts:\n  - revenue\n",
        encoding="utf-8",
    )
    render_project(project)
    generate_dashboards(project)

    html = _html(project)
    assert "glyf-badge glyf-badge-amber" in html, "private is amber"
    assert f'glyf-tag glyf-tag--{tag_tone("finance")}">finance<' in html
    assert f'glyf-tag glyf-tag--{tag_tone("demo")}">demo<' in html
    assert "glyf-icon-btn glyf-icon-btn--accent" in html
    # The same word gets the same tint on the index page.
    assert f'glyf-tag--{tag_tone("finance")}">finance<' in _html(project, "index.html")


def test_tag_tones_are_stable_and_bounded() -> None:
    assert tag_tone("finance") == tag_tone("finance")
    assert all(0 <= tag_tone(word) < 6 for word in ("a", "finance", "executive", "usage"))


def test_the_stylesheet_link_carries_a_content_hash(tmp_path: Path) -> None:
    """A browser that cached an older stylesheet must not pair it with a new page."""
    import hashlib
    from glyf.dashboard.assets import AssetManager

    project = copy_basic_project(tmp_path)
    render_project(project)
    generate_dashboards(project)

    source = AssetManager().package_root / "assets" / "dashboard.css"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:10]
    assert f'href="../assets/dashboard.css?v={digest}"' in _html(project)
    assert f'href="assets/dashboard.css?v={digest}"' in _html(project, "index.html")


def test_the_star_count_comes_from_the_toolbar(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive\ntoolbar:\n  stars: 24\ncharts:\n  - revenue\n", encoding="utf-8"
    )
    render_project(project)
    generate_dashboards(project)

    assert '<span class="glyf-star-count">24</span>' in _html(project)


def test_a_negative_star_count_is_rejected(tmp_path: Path) -> None:
    import pytest
    from glyf.dashboard.loader import load_dashboard

    project = copy_basic_project(tmp_path)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive\ntoolbar:\n  stars: -1\ncharts:\n  - revenue\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="toolbar.stars"):
        load_dashboard(project / "dashboards" / "executive.yml")


def test_every_card_can_carry_a_watermark(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive\nfilters:\n  - field: month\n    values: [2026-01]\ncharts:\n  - revenue\n",
        encoding="utf-8",
    )
    render_project(project)
    generate_dashboards(project)

    html = _html(project)
    assert 'data-glyf-watermark' in html
    assert '"Not filtered"' in html and '"No data"' in html
