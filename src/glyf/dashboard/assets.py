from dataclasses import dataclass
from pathlib import Path
import shutil

from glyf.dashboard.theme import DEFAULT_THEME, Theme


@dataclass(frozen=True)
class DashboardAssets:
    css_href: str
    css_path: Path
    inline_css: str | None = None


class AssetManager:
    def __init__(self, package_root: Path | None = None) -> None:
        self.package_root = package_root or Path(__file__).parent

    def prepare(
        self,
        output_root: Path,
        *,
        theme: Theme = DEFAULT_THEME,
        single_file: bool = False,
    ) -> DashboardAssets:
        source = self.package_root / "assets" / theme.css_file
        if not source.exists():
            raise FileNotFoundError(f"Dashboard CSS asset does not exist: {source}")

        if single_file:
            return DashboardAssets(
                css_href="",
                css_path=source,
                inline_css=source.read_text(encoding="utf-8"),
            )

        assets_dir = output_root / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        destination = assets_dir / theme.css_file
        shutil.copy2(source, destination)
        return DashboardAssets(
            css_href=f"assets/{theme.css_file}",
            css_path=destination,
        )


def copy_dashboard_assets(source_root: Path, destination_root: Path) -> None:
    source = source_root / "assets"
    if source.exists():
        shutil.copytree(source, destination_root / "assets", dirs_exist_ok=True)
