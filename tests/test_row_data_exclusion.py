"""Publishing pictures instead of data.

Everything a normal build publishes carries the rows: an interactive chart
inlines its whole Vega spec, a static SVG carries each row in a per-mark
accessibility label, and `site/compiled/*.sql` names the warehouse tables.
`export.row_data: exclude` publishes rendered PNGs and nothing else.

These tests read the exported bytes rather than trusting the configuration.
That distinction matters: `tests/test_export.py` has long asserted no `https://`
appears in a dashboard, and it passes only because its fixture has no
interactive chart to pull in a CDN.
"""

from dataclasses import replace
from pathlib import Path

import json

import pytest

from glyf.config import ExportConfig, GlyfConfig
from glyf.dashboard.generator import generate_dashboards
from glyf.exporter import export_site
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

# Values that exist nowhere else, so finding them in the output means they came
# from the rows.
SECRET_REVENUE = "987654321"
SECRET_REGION = "Acme Holdings"


def test_exported_site_contains_no_row_values(tmp_path: Path) -> None:
    project = _built_project(tmp_path, row_data="exclude")

    published = _published_text(project)

    assert SECRET_REVENUE not in published
    assert SECRET_REGION not in published
    assert "datasets" not in published, "a Vega spec carries the rows outright"
    # The values above are what an SVG's per-mark accessibility labels would
    # carry, so their absence is the real check; this pins the mechanism.
    dashboard = (
        project / "target" / "glyf" / "site" / "dashboards" / "executive.html"
    ).read_text(encoding="utf-8")
    assert '<img src="../charts/revenue.png"' in dashboard
    assert "glyf-source-sql" not in dashboard, "the drawer prints the compiled SQL"


def test_the_same_values_are_published_by_default(tmp_path: Path) -> None:
    """The guard above is only meaningful if the default really does publish."""
    project = _built_project(tmp_path, row_data="include")

    published = _published_text(project)

    assert SECRET_REVENUE in published
    assert SECRET_REGION in published


def test_charts_are_published_as_png_only(tmp_path: Path) -> None:
    project = _built_project(tmp_path, row_data="exclude")
    site = project / "target" / "glyf" / "site"

    assert (site / "charts" / "revenue.png").exists()
    assert not list(site.rglob("*.svg"))
    assert not list(site.rglob("*.vega.json"))
    assert not list(site.rglob("*.data.json"))


def test_compiled_sql_is_not_published(tmp_path: Path) -> None:
    """It names the warehouse tables the dashboard was built from."""
    project = _built_project(tmp_path, row_data="exclude")
    site = project / "target" / "glyf" / "site"

    assert not (site / "compiled").exists()
    assert "fct_orders" not in _published_text(project)
    # ...while the local artifact keeps it, for the person who ran the build.
    assert (project / "target" / "glyf" / "compiled" / "revenue.sql").exists()


def test_the_public_manifest_does_not_advertise_withheld_artifacts(
    tmp_path: Path,
) -> None:
    project = _built_project(tmp_path, row_data="exclude")
    site = project / "target" / "glyf" / "site"

    bundle = json.loads((site / "bundle.json").read_text(encoding="utf-8"))
    artifacts = bundle["charts"]["revenue"]["artifacts"]

    assert artifacts["png"] == "charts/revenue.png"
    assert artifacts["svg"] is None
    assert artifacts["compiled_sql"] is None
    assert bundle["security"]["row_data"] == "excluded"


def test_an_interactive_chart_degrades_visibly(tmp_path: Path) -> None:
    """Silently dropping the interactivity someone asked for would be worse."""
    project = _project(tmp_path)
    _write_chart(project, interactive=True)

    result = render_project(project, _config("exclude"))

    assert len(result.warnings) == 1
    assert "static PNG" in result.warnings[0]
    assert "revenue.ggsql" in result.warnings[0]
    assert not (project / "target" / "glyf" / "data" / "vega" / "revenue.vega.json").exists()


def test_a_stale_artifact_from_an_earlier_build_is_cleared(tmp_path: Path) -> None:
    """A full build leaves an SVG behind; the next excluded build must not ship it."""
    project = _project(tmp_path)
    _write_chart(project, interactive=True)
    render_project(project, _config("include"))
    assert (project / "target" / "glyf" / "charts" / "revenue.svg").exists()

    render_project(project, _config("exclude"))

    assert not (project / "target" / "glyf" / "charts" / "revenue.svg").exists()
    assert not (project / "target" / "glyf" / "data" / "vega" / "revenue.vega.json").exists()


def test_sourced_filter_values_are_withheld(tmp_path: Path) -> None:
    """`source(chart, field)` is a SELECT DISTINCT, so it is data."""
    project = _project(tmp_path)
    _write_chart(project, color=True)
    _write_dashboard(
        project,
        "filters:\n"
        "  - field: region\n"
        "    values: source(revenue, region)\n"
        "  - field: focus\n"
        "    values: [revenue, margin]\n",
    )

    project = _build(project, row_data="exclude")

    published = _published_text(project)
    assert SECRET_REGION not in published
    assert "margin" in published, "a hand-written list is configuration, not data"


def _config(row_data: str) -> GlyfConfig:
    return replace(GlyfConfig(), export=ExportConfig(row_data=row_data))


def _project(tmp_path: Path) -> Path:
    project = copy_basic_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        f"month,region,revenue\n2026-01,{SECRET_REGION},{SECRET_REVENUE}\n",
        encoding="utf-8",
    )
    return project


def _write_chart(project: Path, *, interactive: bool = False, color: bool = False) -> None:
    visualise = "month AS x, revenue AS y"
    if color:
        visualise += ", region AS color"
    lines = [
        "SELECT month, region, revenue",
        "FROM {{ ref('fct_orders') }}",
        "",
        f"VISUALISE {visualise}",
        "DRAW line",
        "LABEL title => 'Monthly Revenue'",
    ]
    if interactive:
        lines.append("INTERACT tooltip, zoom")
    (project / "visualisations" / "revenue.ggsql").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_dashboard(project: Path, extra: str) -> None:
    path = project / "dashboards" / "executive.yml"
    path.write_text(path.read_text(encoding="utf-8") + "\n" + extra, encoding="utf-8")


def _build(project: Path, *, row_data: str) -> Path:
    config = _config(row_data)
    render_project(project, config)
    generate_dashboards(project, config)
    export_site(project, config=config)
    return project


def _built_project(tmp_path: Path, *, row_data: str) -> Path:
    project = _project(tmp_path)
    _write_chart(project, interactive=True, color=True)
    return _build(project, row_data=row_data)


def _published_text(project: Path) -> str:
    """Everything under site/ that a browser or a curl could read as text."""
    site = project / "target" / "glyf" / "site"
    chunks = []
    for path in sorted(site.rglob("*")):
        if path.is_file() and path.suffix not in {".png", ".ttf", ".zip"}:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)
