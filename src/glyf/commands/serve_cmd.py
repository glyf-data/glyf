from pathlib import Path

import typer

from glyf.config import ConfigError, load_config
from glyf.server import ServeError, create_server, resolve_serve_target


def run_serve(
    project: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    config_path: Path | None = None,
) -> None:
    try:
        config = load_config(project, config_path)
        target = resolve_serve_target(project.resolve(), config, host=host, port=port)
        serve_server = create_server(target)
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc
    except OSError as exc:
        typer.echo("Serve failed")
        typer.echo(f"  - could not start server on {host}:{port}: {exc}")
        raise typer.Exit(1) from exc
    except ServeError as exc:
        typer.echo("Serve failed")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc

    actual_target = serve_server.target
    typer.echo(f"Serving {_display_path(project.resolve(), actual_target.site_dir)}")
    typer.echo(f"Open {actual_target.url}")
    typer.echo("Press Ctrl+C to stop.")

    try:
        serve_server.server.serve_forever()
    except KeyboardInterrupt:
        typer.echo("\nStopped.")
    finally:
        serve_server.server.server_close()


def _display_path(root: Path, path: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path
