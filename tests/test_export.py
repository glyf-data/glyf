import shutil
import zipfile
from pathlib import Path

from dbt_charts.dashboard.generator import generate_dashboards
from dbt_charts.exporter import export_site
from dbt_charts.pipeline import render_project


def test_export_site_creates_publish_ready_folder(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)

    result = export_site(project)

    site = project / "target" / "ggsql" / "site"
    assert result.site_dir == site
    assert (site / "index.html").exists()
    assert (site / "dashboards" / "executive.html").exists()
    assert (site / "charts" / "revenue.json").exists()
    assert (site / "charts" / "revenue.svg").exists()
    assert (site / "charts" / "revenue.png").exists()
    assert (site / "compiled" / "revenue.sql").exists()
    assert (site / "assets" / "style.css").exists()


def test_export_site_preserves_relative_links(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)

    export_site(project)

    site = project / "target" / "ggsql" / "site"
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
    stale_file = project / "target" / "ggsql" / "site" / "stale.txt"
    stale_file.write_text("old", encoding="utf-8")

    export_site(project, clean=True)

    assert not stale_file.exists()
    assert (project / "target" / "ggsql" / "site" / "index.html").exists()


def test_export_site_zip_writes_archive(tmp_path: Path) -> None:
    project = _rendered_project(tmp_path)

    result = export_site(project, zip_site=True)

    zip_path = project / "target" / "ggsql" / "dbt-charts-site.zip"
    assert result.zip_path == zip_path
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    assert "index.html" in names
    assert "dashboards/executive.html" in names
    assert "charts/revenue.svg" in names
    assert "charts/revenue.png" in names
    assert "charts/revenue.json" in names
    assert "compiled/revenue.sql" in names
    assert "assets/style.css" in names


def _rendered_project(tmp_path: Path) -> Path:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    render_project(project)
    generate_dashboards(project)
    return project
