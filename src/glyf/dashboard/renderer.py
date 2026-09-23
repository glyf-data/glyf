from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from glyf.config import GlyfConfig
from glyf.dashboard.artifacts import ChartArtifact
from glyf.dashboard.assets import AssetManager, DashboardAssets
from glyf.dashboard.chart_theme import apply_chart_theme, resolve_chart_theme
from glyf.dashboard.filters import plan_filters
from glyf.dashboard.lineage import build_lineage
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
        resolved_theme = dashboard.theme or config.dashboard.theme or DEFAULT_THEME.name
        resolved_chart_theme = resolve_chart_theme(
            resolved_theme,
            dashboard.chart_theme,
        )
        themed_chart_artifacts = {
            name: apply_chart_theme(chart_artifact, resolved_chart_theme)
            for name, chart_artifact in chart_artifacts.items()
        }
        themed_charts = tuple(
            themed_chart_artifacts[chart.metadata.name] for chart in charts
        )
        template = self._environment().get_template("dashboard.html.j2")
        filters = plan_filters(dashboard, themed_chart_artifacts)
        interactive = any(chart.metadata.interactions for chart in themed_charts)
        html = template.render(
            dashboard=dashboard,
            chart_artifacts=themed_chart_artifacts,
            charts=themed_charts,
            has_interactive_charts=interactive,
            # The Vega runtime is loaded for an interactive chart, and for a
            # filter that redraws a static one; a page with neither stays free
            # of it.
            needs_vega=interactive or bool(filters.vega_charts),
            filters=filters,
            has_tables=any(chart.metadata.is_table for chart in themed_charts),
            lineage=build_lineage(charts) if config.dashboard.show_lineage else None,
            dashboard_config=config.dashboard,
            dashboard_theme=resolved_theme,
            chart_theme=resolved_chart_theme,
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
        environment = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(("html", "xml")),
        )
        environment.filters["tag_tone"] = tag_tone
        return environment


TAG_TONES = 6


def tag_tone(tag: str) -> int:
    """Which of the tag tints a tag gets: the same one on every page it appears."""
    return sum(ord(char) for char in str(tag)) % TAG_TONES


def _strip_trailing_whitespace(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.splitlines()) + "\n"
