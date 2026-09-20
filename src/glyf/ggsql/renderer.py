import html
import json
import re
from pathlib import Path

import altair as alt
import pyarrow as pa
import pyarrow.compute as pc

from glyf.config import RenderConfig
from glyf.execution.result import ArrowStreamExportable, QueryResult
from glyf.ggsql.models import GgsqlChart
from glyf.ggsql.parser import SUPPORTED_CHART_TYPES
from glyf.renderers import chart_renderer, get_chart_renderer


HISTOGRAM_MAX_BINS = 30
BOXPLOT_MIN_SIZE = 6
BOXPLOT_MAX_SIZE = 80


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
    if chart.draw_type not in SUPPORTED_CHART_TYPES:
        raise ChartRenderError(f"unsupported chart type '{chart.draw_type}'")

    x_field = chart.field_for_role("x")
    y_field = chart.field_for_role("y")
    if x_field is None:
        raise ChartRenderError(f"{chart.draw_type} requires an x mapping")
    if y_field is None and chart.draw_type != "histogram":
        raise ChartRenderError("VISUALISE requires x and y mappings")

    color_field = chart.field_for_role("color")
    required_fields = list(required_columns(chart))

    missing = missing_columns(chart, tuple(frame.column_names))
    if missing:
        joined = ", ".join(f"'{field}'" for field in missing)
        raise ChartRenderError(f"query result missing chart column {joined}")

    # These three compute from the column rather than plot it, and the renderer
    # answers a text column with an empty chart instead of an error.
    numeric_role = {"histogram": "x", "boxplot": "y", "heatmap": "color"}.get(
        chart.draw_type
    )
    if numeric_role is not None:
        numeric_field = chart.field_for_role(numeric_role)
        if numeric_field is not None:
            _require_numeric(frame, numeric_field, numeric_role, chart.draw_type)

    width = chart.width or config.default_width
    height = chart.height or config.default_height
    title: str | alt.TitleParams | None = chart.title
    if chart.title and chart.subtitle:
        title = alt.TitleParams(text=chart.title, subtitle=chart.subtitle)

    encoding: dict[str, object]
    tooltips = [alt.Tooltip(field) for field in dict.fromkeys(required_fields)]
    if chart.draw_type == "pie":
        encoding = {
            "theta": alt.Theta(y_field, title=chart.y_title),
            "color": alt.Color(
                color_field or x_field,
                title=chart.x_title if color_field is None else color_field,
            ),
        }
    elif chart.draw_type == "histogram":
        # The rows are binned and counted by the renderer, so the y axis and
        # the tooltip describe a bin rather than any column of the query.
        bins = alt.Bin(maxbins=HISTOGRAM_MAX_BINS)
        encoding = {
            "x": alt.X(x_field, bin=bins, title=chart.x_title),
            "y": alt.Y("count()", title=chart.y_title),
        }
        tooltips = [alt.Tooltip(x_field, bin=bins), alt.Tooltip("count()")]
        if color_field is not None:
            encoding["color"] = alt.Color(color_field)
            tooltips.append(alt.Tooltip(color_field))
    elif chart.draw_type == "heatmap":
        # Both axes are discrete cells, and `sort=None` keeps the order the
        # query returned them in: an ORDER BY is how a heatmap puts Monday
        # before Tuesday.
        if color_field is None:
            raise ChartRenderError("heatmap requires x, y and color mappings")
        encoding = {
            "x": alt.X(x_field, type="ordinal", sort=None, title=chart.x_title),
            "y": alt.Y(y_field, type="ordinal", sort=None, title=chart.y_title),
            "color": alt.Color(color_field, type="quantitative"),
        }
    elif chart.draw_type == "boxplot":
        # The mark names its tooltip rows after the y title -- "Median of
        # revenue" -- so an absent title falls back to the column rather than
        # to None, which it would print as "Median of null".
        encoding = {
            "x": alt.X(x_field, axis=alt.Axis(labelAngle=0), title=chart.x_title),
            "y": alt.Y(y_field, title=chart.y_title or y_field),
        }
        if color_field is not None:
            encoding["color"] = alt.Color(color_field)
    else:
        encoding = {
            "x": alt.X(x_field, axis=alt.Axis(labelAngle=0), title=chart.x_title),
            "y": alt.Y(y_field, title=chart.y_title),
        }
        if color_field is not None:
            encoding["color"] = alt.Color(color_field)
    # A boxplot keeps the renderer's own tooltip -- the quartiles of the box
    # under the pointer -- which a list of row fields would replace.
    if "tooltip" in chart.interactions and chart.draw_type != "boxplot":
        encoding["tooltip"] = tooltips

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
    elif chart.draw_type == "histogram":
        rendered = base.mark_bar()
    elif chart.draw_type == "boxplot":
        rendered = base.mark_boxplot(size=_boxplot_size(frame, x_field, width))
    elif chart.draw_type == "heatmap":
        rendered = base.mark_rect()
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


def _require_numeric(frame: pa.Table, field: str, role: str, draw_type: str) -> None:
    column_type = frame.schema.field(field).type
    if pa.types.is_integer(column_type) or pa.types.is_floating(column_type):
        return
    raise ChartRenderError(
        f"{draw_type} needs a numeric {role} column and '{field}' is {column_type}"
    )


def _boxplot_size(frame: pa.Table, x_field: str, width: int) -> int:
    """Box width in pixels: half of each category's share of the plot.

    The renderer's default is a fixed 14 pixels, which reads as a hairline on
    a two-category chart the width glyf draws.
    """
    categories = max(pc.count_distinct(frame.column(x_field)).as_py(), 1)
    return max(BOXPLOT_MIN_SIZE, min(BOXPLOT_MAX_SIZE, width // (categories * 2)))


def _coerce_query_result(data: QueryResult | ArrowStreamExportable) -> QueryResult:
    if isinstance(data, QueryResult):
        return data
    if hasattr(data, "__arrow_c_stream__"):
        return QueryResult.from_dataframe(data)
    raise ChartRenderError(
        "chart renderer expected a QueryResult or an Arrow-exportable dataframe "
        "(pyarrow, polars, pandas >= 2.2, or a DuckDB relation)"
    )


_SVG_LABELLED_TAG = re.compile(r'<[^<>]*\baria-label="[^"]*"[^<>]*>')
_SVG_ARIA_LABEL = re.compile(r'aria-label="[^"]*"')
_SVG_ROLE_DESCRIPTION = re.compile(r'aria-roledescription="([^"]*)"')
# What Vega calls the elements whose label repeats text the page already shows.
# Anything else it labels is a data mark.
_SVG_GUIDE_ROLES = frozenset({"axis", "legend", "title", "subtitle"})


def strip_svg_row_values(svg_path: Path, chart: GgsqlChart) -> None:
    """Replace each mark's `field: value; ...` label with the field names alone.

    Vega labels a data mark with the values it was drawn from, one
    `name: value` per encoded channel, and gives axes, legends and titles
    prose labels of their own. Only the former carry the rows; the latter
    describe text the page already shows. A mark still announces which columns
    it came from, so a screen reader can tell a bar from a legend, but a reader
    gets what the pixels show and nothing more precise.

    A mark is told from a guide by the role Vega gives the element, not by how
    its label reads: the name in `name: value` is the axis title when the chart
    sets one, so a label cannot be recognised by the column it starts with.
    """
    field_names = html.escape("; ".join(required_columns(chart)), quote=True)

    def relabel(match: re.Match[str]) -> str:
        tag = match.group(0)
        role = _SVG_ROLE_DESCRIPTION.search(tag)
        if role is not None and role.group(1) in _SVG_GUIDE_ROLES:
            return tag
        return _SVG_ARIA_LABEL.sub(f'aria-label="{field_names}"', tag, count=1)

    svg = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(_SVG_LABELLED_TAG.sub(relabel, svg), encoding="utf-8")


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
