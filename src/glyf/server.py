from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from glyf.config import GlyfConfig
from glyf.output.paths import artifact_paths


class ServeError(ValueError):
    """Raised when the static dashboard site cannot be served."""


@dataclass(frozen=True)
class ServeTarget:
    site_dir: Path
    host: str
    port: int
    url: str


@dataclass(frozen=True)
class ServeServer:
    server: ThreadingHTTPServer
    target: ServeTarget


def resolve_serve_target(
    project_root: Path,
    config: GlyfConfig | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> ServeTarget:
    root = project_root.expanduser().resolve()
    paths = artifact_paths(root, config)
    site_dir = paths.site_dir
    index_path = site_dir / "index.html"

    if not site_dir.exists():
        rel_path = _display_path(root, site_dir)
        raise ServeError(
            f"{rel_path} does not exist; run `glyf build` or `glyf export` first"
        )
    if not site_dir.is_dir():
        rel_path = _display_path(root, site_dir)
        raise ServeError(f"{rel_path} is not a directory")
    if not index_path.exists():
        rel_path = _display_path(root, index_path)
        raise ServeError(
            f"{rel_path} does not exist; run `glyf build` or `glyf export` first"
        )

    return ServeTarget(
        site_dir=site_dir,
        host=host,
        port=port,
        url=f"http://{host}:{port}/",
    )


def create_server(target: ServeTarget) -> ServeServer:
    handler = partial(
        SimpleHTTPRequestHandler,
        directory=target.site_dir.as_posix(),
    )
    server = ThreadingHTTPServer((target.host, target.port), handler)
    actual_port = int(server.server_address[1])
    if actual_port != target.port:
        target = ServeTarget(
            site_dir=target.site_dir,
            host=target.host,
            port=actual_port,
            url=f"http://{target.host}:{actual_port}/",
        )
    return ServeServer(server=server, target=target)


def _display_path(root: Path, path: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path
