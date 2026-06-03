from copy import deepcopy
from dataclasses import replace
import re

from glyf.dashboard.artifacts import ChartArtifact


LIGHT_CHART_THEME = "light"
DARK_CHART_THEME = "dark"
AUTO_CHART_THEME = "auto"


def resolve_chart_theme(dashboard_theme: str, chart_theme: str | None) -> str:
    if chart_theme in {LIGHT_CHART_THEME, DARK_CHART_THEME}:
        return chart_theme
    if dashboard_theme == DARK_CHART_THEME:
        return DARK_CHART_THEME
    return LIGHT_CHART_THEME


def apply_chart_theme(chart: ChartArtifact, theme: str) -> ChartArtifact:
    if theme != DARK_CHART_THEME:
        return chart

    return replace(
        chart,
        svg=_apply_dark_svg_theme(chart.svg),
        vega_spec=_apply_dark_vega_theme(chart.vega_spec),
    )


def _apply_dark_svg_theme(svg: str | None) -> str | None:
    if svg is None:
        return None

    themed = svg
    themed = _ROOT_RECT_RE.sub(
        lambda match: match.group(0).replace('fill="white"', 'fill="#09090b"', 1),
        themed,
        count=1,
    )
    themed = themed.replace('stroke="#d9e2ec"', 'stroke="#3f3f46"')
    themed = themed.replace('stroke="#ddd"', 'stroke="#27272a"')
    themed = themed.replace('stroke="#888"', 'stroke="#a1a1aa"')
    themed = themed.replace('fill="#000"', 'fill="#f4f4f5"')
    themed = themed.replace('fill="black"', 'fill="#f4f4f5"')
    return themed


def _apply_dark_vega_theme(spec: object | None) -> object | None:
    if spec is None:
        return None
    if not isinstance(spec, dict):
        return spec

    themed = deepcopy(spec)
    themed["background"] = "#09090b"

    config = themed.setdefault("config", {})
    view = config.setdefault("view", {})
    view.update(
        {
            "stroke": "#3f3f46",
            "fill": "#09090b",
        }
    )

    axis = config.setdefault("axis", {})
    axis.update(
        {
            "labelColor": "#f4f4f5",
            "titleColor": "#f4f4f5",
            "domainColor": "#a1a1aa",
            "tickColor": "#a1a1aa",
            "gridColor": "#27272a",
        }
    )

    legend = config.setdefault("legend", {})
    legend.update(
        {
            "labelColor": "#f4f4f5",
            "titleColor": "#f4f4f5",
        }
    )

    title = config.setdefault("title", {})
    title.update(
        {
            "color": "#f4f4f5",
            "subtitleColor": "#d4d4d8",
        }
    )

    return themed


_ROOT_RECT_RE = re.compile(r'<rect[^>]+fill="white"[^>]*/>')
