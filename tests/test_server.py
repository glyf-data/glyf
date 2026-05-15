from pathlib import Path

import pytest

from dbt_charts.server import ServeError, create_server, resolve_serve_target


def test_resolve_serve_target_reports_missing_site(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(ServeError, match="run `dbt-charts dashboard` first"):
        resolve_serve_target(project)


def test_resolve_serve_target_reports_missing_index(tmp_path: Path) -> None:
    project = tmp_path / "project"
    site_dir = project / "target" / "ggsql" / "site"
    site_dir.mkdir(parents=True)

    with pytest.raises(ServeError, match="target/ggsql/site/index.html"):
        resolve_serve_target(project)


def test_create_server_uses_site_directory_and_ephemeral_port(tmp_path: Path) -> None:
    project = tmp_path / "project"
    site_dir = project / "target" / "ggsql" / "site"
    site_dir.mkdir(parents=True)
    (site_dir / "index.html").write_text("<h1>dbt-charts</h1>", encoding="utf-8")

    target = resolve_serve_target(project, port=0)
    serve_server = create_server(target)

    try:
        actual_target = serve_server.target
        assert actual_target.site_dir == site_dir
        assert actual_target.host == "127.0.0.1"
        assert actual_target.port > 0
        assert actual_target.url == f"http://127.0.0.1:{actual_target.port}/"
    finally:
        serve_server.server.server_close()
