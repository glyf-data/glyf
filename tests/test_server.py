from pathlib import Path

import pytest

from glyf.server import ServeError, create_server, resolve_serve_target


def test_resolve_serve_target_reports_missing_site(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(ServeError, match="run `glyf build` or `glyf export` first"):
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
    (site_dir / "index.html").write_text("<h1>glyf</h1>", encoding="utf-8")

    target = resolve_serve_target(project, port=0)

    class FakeThreadingHTTPServer:
        def __init__(self, address: tuple[str, int], handler: object) -> None:
            self.server_address = (address[0], 43123)

        def server_close(self) -> None:
            return None

    import glyf.server as server_module

    original = server_module.ThreadingHTTPServer
    server_module.ThreadingHTTPServer = FakeThreadingHTTPServer
    try:
        serve_server = create_server(target)
        actual_target = serve_server.target
        assert actual_target.site_dir == site_dir
        assert actual_target.host == "127.0.0.1"
        assert actual_target.port == 43123
        assert actual_target.url == "http://127.0.0.1:43123/"
    finally:
        server_module.ThreadingHTTPServer = original
