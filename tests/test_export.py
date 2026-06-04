import json
import zipfile
from pathlib import Path

from glyf.dashboard.generator import generate_dashboards
from glyf.exporter import export_site
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project


def test_export_site_creates_publish_ready_folder(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)

    result = export_site(project)

    site = project / "target" / "glyf" / "site"
    assert result.site_dir == site
    assert (site / "index.html").exists()
    assert (site / "dashboards" / "executive.html").exists()
    assert (site / "charts" / "revenue.json").exists()
    assert (site / "charts" / "revenue.svg").exists()
    assert (site / "charts" / "revenue.png").exists()
    assert not (site / "charts" / "revenue.data.json").exists()
    assert (site / "compiled" / "revenue.sql").exists()
    assert (site / "assets" / "dashboard.css").exists()
    chart_metadata = json.loads(
        (site / "charts" / "revenue.json").read_text(encoding="utf-8")
    )
    assert "data_json_path" not in chart_metadata
    assert "vega_json_path" not in chart_metadata
    assert chart_metadata["metadata_path"] == "charts/revenue.json"
    assert chart_metadata["png_path"] == "charts/revenue.png"
    assert chart_metadata["svg_path"] == "charts/revenue.svg"
    assert chart_metadata["compiled_sql_path"] == "compiled/revenue.sql"
    bundle = json.loads((site / "bundle.json").read_text(encoding="utf-8"))
    assert bundle["mode"] == "public_site"
    assert bundle["security"]["internal_artifacts_included"] is False
    assert bundle["charts"]["revenue"]["artifacts"]["data"] is None
    assert bundle["charts"]["revenue"]["artifacts"]["vega"] is None


def test_export_site_preserves_relative_links(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)

    export_site(project)

    site = project / "target" / "glyf" / "site"
    index_html = (site / "index.html").read_text(encoding="utf-8")
    dashboard_html = (site / "dashboards" / "executive.html").read_text(
        encoding="utf-8"
    )

    assert 'href="dashboards/executive.html"' in index_html
    assert "https://" not in index_html
    assert "https://" not in dashboard_html


def test_export_site_clean_removes_previous_files(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)
    export_site(project)
    stale_file = project / "target" / "glyf" / "site" / "stale.txt"
    stale_file.write_text("old", encoding="utf-8")

    export_site(project, clean=True)

    assert not stale_file.exists()
    assert (project / "target" / "glyf" / "site" / "index.html").exists()


def test_export_site_zip_writes_archive(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)

    result = export_site(project, zip_site=True)

    zip_path = project / "target" / "glyf" / "glyf-site.zip"
    assert result.zip_path == zip_path
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    assert "index.html" in names
    assert "dashboards/executive.html" in names
    assert "charts/revenue.svg" in names
    assert "charts/revenue.png" in names
    assert "charts/revenue.json" in names
    assert "charts/revenue.data.json" not in names
    assert "compiled/revenue.sql" in names
    assert "assets/dashboard.css" in names
    assert "bundle.json" in names


def test_export_site_skips_internal_vega_specs(tmp_path: Path) -> None:
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

    export_site(project)

    site = project / "target" / "glyf" / "site"
    assert not (site / "charts" / "revenue.vega.json").exists()
    assert (project / "target" / "glyf" / "data" / "vega" / "revenue.vega.json").exists()


def _rendered_project(tmp_path: Path) -> Path:
    project = copy_basic_project(tmp_path)
    render_project(project)
    generate_dashboards(project)
    return project
