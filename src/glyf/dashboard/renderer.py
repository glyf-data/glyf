from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from glyf.config import GlyfConfig
from glyf.dashboard.artifacts import ChartArtifact
from glyf.dashboard.assets import AssetManager, DashboardAssets
from glyf.dashboard.loader import Dashboard
from glyf.dashboard.theme import DEFAULT_THEME, Theme


@dataclass(frozen=True)
class RenderedDashboard:
    html: str


@dataclass(frozen=True)
class DashboardBuildMeta:
    generated_at: datetime
    generated_at_display: str
    generated_at_iso: str

    @classmethod
    def now(cls) -> "DashboardBuildMeta":
        generated_at = datetime.now(timezone.utc).replace(microsecond=0)
        return cls.from_datetime(generated_at)

    @classmethod
    def from_datetime(cls, generated_at: datetime) -> "DashboardBuildMeta":
        normalized = generated_at.astimezone(timezone.utc).replace(microsecond=0)
        return cls(
            generated_at=normalized,
            generated_at_display=normalized.strftime("%d %b %Y, %H:%M UTC"),
            generated_at_iso=normalized.isoformat().replace("+00:00", "Z"),
        )


class DashboardRenderer:
    def __init__(
        self,
        *,
        templates_dir: Path | None = None,
        asset_manager: AssetManager | None = None,
    ) -> None:
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"
        self.asset_manager = asset_manager or AssetManager()

    def prepare_assets(
        self,
        output_root: Path,
        *,
        theme: Theme = DEFAULT_THEME,
        single_file: bool = False,
    ) -> DashboardAssets:
        return self.asset_manager.prepare(
            output_root,
            theme=theme,
            single_file=single_file,
        )

    def render_dashboard(
        self,
        dashboard: Dashboard,
        chart_artifacts: dict[str, ChartArtifact],
        charts: tuple[ChartArtifact, ...],
        config: GlyfConfig,
        assets: DashboardAssets,
        build_meta: DashboardBuildMeta | None = None,
    ) -> RenderedDashboard:
        build_meta = build_meta or DashboardBuildMeta.now()
        template = self._environment().get_template("dashboard.html.j2")
        html = template.render(
            dashboard=dashboard,
            chart_artifacts=chart_artifacts,
            charts=charts,
            has_interactive_charts=any(chart.vega_spec is not None for chart in charts),
            dashboard_config=config.dashboard,
            assets=assets,
            build_meta=build_meta,
        )
        return RenderedDashboard(html=_strip_trailing_whitespace(html))

    def render_index(
        self,
        dashboards: tuple[object, ...],
        assets: DashboardAssets,
    ) -> str:
        template = self._environment().get_template("index.html.j2")
        return _strip_trailing_whitespace(
            template.render(dashboards=dashboards, assets=assets)
        )

    def _environment(self) -> Environment:
        return Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(("html", "xml")),
        )


def _strip_trailing_whitespace(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.splitlines()) + "\n"
