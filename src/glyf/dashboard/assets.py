import base64
from dataclasses import dataclass
from pathlib import Path
import re
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
                inline_css=self._inline_font_assets(source),
            )

        assets_dir = output_root / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        destination = assets_dir / theme.css_file
        shutil.copy2(source, destination)
        self._copy_font_assets(source.parent, assets_dir)
        return DashboardAssets(
            css_href=f"assets/{theme.css_file}",
            css_path=destination,
        )

    def _copy_font_assets(self, source_assets_dir: Path, destination_assets_dir: Path) -> None:
        source_fonts = source_assets_dir / "fonts"
        if source_fonts.exists():
            shutil.copytree(
                source_fonts,
                destination_assets_dir / "fonts",
                dirs_exist_ok=True,
            )

    def _inline_font_assets(self, css_path: Path) -> str:
        css_text = css_path.read_text(encoding="utf-8")
        assets_dir = css_path.parent

        def replace(match: re.Match[str]) -> str:
            relative_path = match.group("path")
            font_path = assets_dir / relative_path
            if not font_path.exists():
                return match.group(0)
            mime_type = _font_mime_type(font_path)
            encoded = base64.b64encode(font_path.read_bytes()).decode("ascii")
            return f'url("data:{mime_type};base64,{encoded}")'

        return _FONT_URL_RE.sub(replace, css_text)


def copy_dashboard_assets(source_root: Path, destination_root: Path) -> None:
    source = source_root / "assets"
    if source.exists():
        shutil.copytree(source, destination_root / "assets", dirs_exist_ok=True)


_FONT_URL_RE = re.compile(r'url\("(?P<path>fonts/[^"]+)"\)')


def _font_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".woff2":
        return "font/woff2"
    if suffix == ".woff":
        return "font/woff"
    if suffix == ".ttf":
        return "font/ttf"
    if suffix == ".otf":
        return "font/otf"
    return "application/octet-stream"
