from pathlib import Path

from glyf.commands.dashboard_cmd import run_dashboard
from glyf.commands.export_cmd import run_export
from glyf.commands.render_cmd import run_render
from glyf.commands.validate_cmd import run_validate


def run_build(
    project: Path,
    *,
    clean: bool = True,
    zip_site: bool = False,
    config_path: Path | None = None,
) -> None:
    run_validate(project, config_path)
    run_render(project, config_path)
    run_dashboard(project, config_path)
    run_export(project, clean=clean, zip_site=zip_site, config_path=config_path)
