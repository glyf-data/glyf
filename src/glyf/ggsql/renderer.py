import html
import json
import re
from pathlib import Path

import altair as alt

from glyf.config import RenderConfig
from glyf.execution.result import ArrowStreamExportable, QueryResult
from glyf.ggsql.models import GgsqlChart
from glyf.ggsql.parser import SUPPORTED_CHART_TYPES
from glyf.renderers import chart_renderer, get_chart_renderer


class ChartRenderError(ValueError):
    """Raised when a chart cannot be rendered."""


def render_chart(
    chart: GgsqlChart,
    data: QueryResult | ArrowStreamExportable,
    png_path: Path,
    svg_path: Path,
    config: RenderConfig | None = None,
    *,
    vega_json_path: Path | None = None,
) -> None:
    config = config or RenderConfig()
    query_result = _coerce_query_result(data)
    try:
        renderer = get_chart_renderer(config.renderer)
    except ValueError as exc:
        raise ChartRenderError(str(exc)) from exc
    renderer(chart, query_result, png_path, svg_path, config, vega_json_path)


@chart_renderer("altair")
def _render_altair_chart(
    chart: GgsqlChart,
    data: QueryResult,
    png_path: Path,
    svg_path: Path,
    config: RenderConfig,
    vega_json_path: Path | None,
) -> None:
    chart_spec = build_chart(chart, data, config=config)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if "svg" in config.formats:
            chart_spec.save(svg_path)
            _patch_svg_fonts(svg_path)
        if "png" in config.formats:
            chart_spec.save(png_path)
        if chart.is_interactive and vega_json_path is not None:
            vega_json_path.parent.mkdir(parents=True, exist_ok=True)
            chart_spec.save(vega_json_path)
            _patch_vega_json_fonts(vega_json_path)
    except Exception as exc:
        raise ChartRenderError(str(exc)) from exc


def required_columns(chart: GgsqlChart) -> tuple[str, ...]:
    """The columns a chart's VISUALISE clause binds, in encoding order."""
    roles = ("x", "y", "color")
    fields = [chart.field_for_role(role) for role in roles]
    return tuple(dict.fromkeys(field for field in fields if field is not None))


def prune_to_encoded_columns(chart: GgsqlChart, data: QueryResult) -> QueryResult:
    """The result reduced to the columns the chart encodes.

    A chart built from this carries nothing the picture does not show: an
    inlined Vega `datasets` block lists only these columns, and so do the
    tooltips. Values are untouched -- the chart must agree with the warehouse.
    A column the chart binds but the result lacks is left for `build_chart`
    to report.
    """
    available = set(data.columns)
    keep = [field for field in required_columns(chart) if field in available]
    if len(keep) == len(data.columns):
        return data
    return QueryResult.from_arrow(data.to_arrow().select(keep))


def missing_columns(chart: GgsqlChart, columns: tuple[str, ...]) -> tuple[str, ...]:
    """Which of the chart's bound columns a result does not provide.

    Shared with validate mode, which checks the same binding against a
    zero-row result rather than against data it never fetched.
    """
    available = set(columns)
    return tuple(
        field for field in required_columns(chart) if field not in available
    )


def build_chart(
    chart: GgsqlChart,
    data: QueryResult | ArrowStreamExportable,
    config: RenderConfig | None = None,
) -> alt.Chart:
    config = config or RenderConfig()
    frame = _coerce_query_result(data).to_arrow()
    x_field = chart.field_for_role("x")
    y_field = chart.field_for_role("y")
    if x_field is None or y_field is None:
        raise ChartRenderError("VISUALISE requires x and y mappings")

    if chart.draw_type not in SUPPORTED_CHART_TYPES:
        raise ChartRenderError(f"unsupported chart type '{chart.draw_type}'")

    color_field = chart.field_for_role("color")
    required_fields = list(required_columns(chart))

    missing = missing_columns(chart, tuple(frame.column_names))
    if missing:
        joined = ", ".join(f"'{field}'" for field in missing)
        raise ChartRenderError(f"query result missing chart column {joined}")

    width = chart.width or config.default_width
    height = chart.height or config.default_height
    title: str | alt.TitleParams | None = chart.title
    if chart.title and chart.subtitle:
        title = alt.TitleParams(text=chart.title, subtitle=chart.subtitle)

    encoding: dict[str, object]
    if chart.draw_type == "pie":
        encoding = {
            "theta": alt.Theta(y_field, title=chart.y_title),
            "color": alt.Color(
                color_field or x_field,
                title=chart.x_title if color_field is None else color_field,
            ),
        }
    else:
        encoding = {
            "x": alt.X(x_field, axis=alt.Axis(labelAngle=0), title=chart.x_title),
            "y": alt.Y(y_field, title=chart.y_title),
        }
        if color_field is not None:
            encoding["color"] = alt.Color(color_field)
    if "tooltip" in chart.interactions:
        tooltip_fields = list(dict.fromkeys(required_fields))
        encoding["tooltip"] = [alt.Tooltip(field) for field in tooltip_fields]

    properties: dict[str, object] = {
        "width": width,
        "height": height,
    }
    if title is not None:
        properties["title"] = title

    base = (
        alt.Chart(frame)
        .encode(**encoding)
        .properties(**properties)
        .configure_view(stroke="#d9e2ec")
        .configure_axis(
            labelAngle=0,
            labelFontSize=11,
            titleFontSize=12,
            titleFontWeight=600,
        )
        .configure_legend(
            labelFontSize=11,
            titleFontSize=12,
            titleFontWeight=600,
        )
        .configure_title(
            fontSize=15,
            fontWeight=600,
            subtitleFontSize=12,
            subtitleFontWeight=400,
        )
    )
    if chart.draw_type == "line":
        rendered = base.mark_line(point=True)
    elif chart.draw_type == "bar":
        rendered = base.mark_bar()
    elif chart.draw_type == "scatter":
        rendered = base.mark_circle(size=80)
    elif chart.draw_type == "area":
        rendered = base.mark_area(opacity=0.7)
    else:
        rendered = base.mark_arc()

    if "legend_filter" in chart.interactions:
        if color_field is None:
            raise ChartRenderError("legend_filter interaction requires a color mapping")
        legend_selection = alt.selection_point(fields=[color_field], bind="legend")
        rendered = rendered.add_params(legend_selection).encode(
            opacity=alt.condition(legend_selection, alt.value(1), alt.value(0.2))
        )
    if "zoom" in chart.interactions:
        rendered = rendered.interactive()
    return rendered


def _coerce_query_result(data: QueryResult | ArrowStreamExportable) -> QueryResult:
    if isinstance(data, QueryResult):
        return data
    if hasattr(data, "__arrow_c_stream__"):
        return QueryResult.from_dataframe(data)
    raise ChartRenderError(
        "chart renderer expected a QueryResult or an Arrow-exportable dataframe "
        "(pyarrow, polars, pandas >= 2.2, or a DuckDB relation)"
    )


_SVG_ARIA_LABEL = re.compile(r'aria-label="([^"]*)"')


def strip_svg_row_values(svg_path: Path, chart: GgsqlChart) -> None:
    """Replace each mark's `field: value; ...` label with the field names alone.

    Vega labels a data mark with the values it was drawn from, one
    `field: value` per encoded channel, and gives axes, legends and titles
    prose labels of their own. Only the former carry the rows; the latter
    describe text the page already shows. A mark still announces which columns
    it came from, so a screen reader can tell a bar from a legend, but a reader
    gets what the pixels show and nothing more precise.
    """
    fields = required_columns(chart)
    row_label = tuple(f"{html.escape(field, quote=True)}: " for field in fields)
    field_names = html.escape("; ".join(fields), quote=True)

    def relabel(match: re.Match[str]) -> str:
        if match.group(1).startswith(row_label):
            return f'aria-label="{field_names}"'
        return match.group(0)

    svg = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(_SVG_ARIA_LABEL.sub(relabel, svg), encoding="utf-8")


def _patch_svg_fonts(svg_path: Path) -> None:
    svg = svg_path.read_text(encoding="utf-8")
    if 'font-family="Hanken Grotesk"' in svg:
        return

    style_block = (
        "<style>"
        "@font-face{font-family:'Hanken Grotesk';src:url('../assets/fonts/HankenGrotesk-Regular.ttf') format('truetype');font-weight:400;font-style:normal;}"
        "@font-face{font-family:'Hanken Grotesk';src:url('../assets/fonts/HankenGrotesk-Medium.ttf') format('truetype');font-weight:500;font-style:normal;}"
        "@font-face{font-family:'Hanken Grotesk';src:url('../assets/fonts/HankenGrotesk-SemiBold.ttf') format('truetype');font-weight:600;font-style:normal;}"
        "@font-face{font-family:'Hanken Grotesk';src:url('../assets/fonts/HankenGrotesk-Bold.ttf') format('truetype');font-weight:700;font-style:normal;}"
        "</style>"
    )
    svg = svg.replace("><rect ", f">{style_block}<rect ", 1)
    svg = svg.replace('font-family="sans-serif"', 'font-family="Hanken Grotesk"')
    svg_path.write_text(svg, encoding="utf-8")


def _patch_vega_json_fonts(vega_json_path: Path) -> None:
    spec = json.loads(vega_json_path.read_text(encoding="utf-8"))
    config = spec.setdefault("config", {})
    axis = config.setdefault("axis", {})
    axis.update(
        {
            "labelFont": "Hanken Grotesk",
            "titleFont": "Hanken Grotesk",
        }
    )
    legend = config.setdefault("legend", {})
    legend.update(
        {
            "labelFont": "Hanken Grotesk",
            "titleFont": "Hanken Grotesk",
        }
    )
    title = config.setdefault("title", {})
    title.update(
        {
            "font": "Hanken Grotesk",
            "subtitleFont": "Hanken Grotesk",
        }
    )
    vega_json_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
