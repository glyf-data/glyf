import html
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import altair as alt
import pyarrow as pa
import pyarrow.compute as pc

from glyf.config import RenderConfig
from glyf.execution.result import ArrowStreamExportable, QueryResult
from glyf.ggsql.geo import MapShapesError, Shapes, load_shapes, match_regions
from glyf.ggsql.models import GgsqlChart
from glyf.ggsql.sankey import LABEL_GAP, Layout, SankeyError, layout_sankey
from glyf.ggsql.treemap import Tile, TreemapError, layout_treemap
from glyf.renderers import chart_renderer, get_chart_renderer

_Styleable = TypeVar("_Styleable", alt.Chart, alt.LayerChart)


HISTOGRAM_MAX_BINS = 30
_HISTOGRAM_BINS = alt.Bin(maxbins=HISTOGRAM_MAX_BINS)
BOXPLOT_MIN_SIZE = 6
BOXPLOT_MAX_SIZE = 80
# Small multiples: at most this many panels to a row unless CONFIG columns
# says otherwise, this much room between them, and a panel's height as a
# share of its width when CONFIG height leaves it open.
FACET_COLUMNS = 3
FACET_GAP = 16
FACET_ASPECT = 0.6
FACET_MIN_HEIGHT = 120
# Pixels of room past the outermost point, on both axes of a scatter.
SCATTER_PADDING = 12
# A map's land, under the regions and points the query draws: present enough
# to place them, quiet enough that it never reads as data. Translucent, so the
# same spec reads on a light card and a dark one.
MAP_LAND = "#94a3b8"
MAP_LAND_OPACITY = 0.28
MAP_BORDER = "#ffffff"
MAP_DEFAULT_PROJECTION = "equalEarth"
# The roles a map binds, in encoding order.
MAP_ROLES = ("region", "latitude", "longitude", "size", "color")
SANKEY_ROLES = ("source", "target", "value")
COMBO_ROLES = ("x", "y", "y2")
TREEMAP_ROLES = ("label", "value", "group")
# A tile shows its name when it is at least this big, and its value under the
# name when it has room for a second line.
TREEMAP_NAME_SIZE = (36, 18)
TREEMAP_VALUE_HEIGHT = 34
TREEMAP_TEXT_INSET = 6
# A combo's bars and line: the first two colours of the default palette, so
# each axis title can say which mark it measures.
COMBO_BAR = "#4c78a8"
COMBO_LINE = "#f58518"
# Roughly how many pixels a funnel label's character and its margins take:
# a label goes inside its bar when it fits there, and beside it otherwise.
FUNNEL_LABEL_CHAR = 7
FUNNEL_LABEL_MARGIN = 20
FUNNEL_PADDING = {"left": 24, "right": 5, "top": 5, "bottom": 5}
# A waterfall's bars: up, down, and the amounts it starts and ends at.
WATERFALL_KINDS = ("Increase", "Decrease", "Total")
WATERFALL_COLORS = ("#54a24b", "#e45756", "#4c78a8")
WATERFALL_TOTAL = "Total"
# A link's band, behind its nodes: see-through, so crossing bands both read.
SANKEY_LINK_OPACITY = 0.38


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
        if vega_json_path is not None:
            # Every drawn chart keeps its spec: an interactive card embeds it,
            # and a dashboard filter redraws any chart from it in the browser.
            vega_json_path.parent.mkdir(parents=True, exist_ok=True)
            chart_spec.save(vega_json_path)
            _patch_vega_json_fonts(vega_json_path)
    except Exception as exc:
        raise ChartRenderError(str(exc)) from exc


def required_columns(chart: GgsqlChart) -> tuple[str, ...]:
    """The columns a chart's VISUALISE clause binds, in encoding order.

    For a table, the columns it lists; `VISUALISE *` binds nothing by name,
    so it requires nothing and `table_columns` resolves it against the rows.
    """
    if chart.is_table:
        return chart.table_columns
    if chart.is_map:
        roles: tuple[str, ...] = MAP_ROLES
    elif chart.is_sankey:
        roles = SANKEY_ROLES
    elif chart.is_combo:
        roles = COMBO_ROLES
    elif chart.is_treemap:
        roles = TREEMAP_ROLES
    elif chart.is_kpi:
        roles = ("value", "compare")
    else:
        roles = ("x", "y", "color", "facet")
    fields = [chart.field_for_role(role) for role in roles]
    return tuple(dict.fromkeys(field for field in fields if field is not None))


def table_columns(chart: GgsqlChart, columns: tuple[str, ...]) -> tuple[str, ...]:
    """The columns a table shows, resolved against a result's columns."""
    if chart.lists_every_column:
        return tuple(columns)
    return chart.table_columns


def prune_to_encoded_columns(chart: GgsqlChart, data: QueryResult) -> QueryResult:
    """The result reduced to the columns the chart encodes.

    A chart built from this carries nothing the picture does not show: an
    inlined Vega `datasets` block lists only these columns, and so do the
    tooltips. Values are untouched -- the chart must agree with the warehouse.
    A column the chart binds but the result lacks is left for `build_chart`
    to report. A table under `VISUALISE *` shows every column, so there is
    nothing to prune.
    """
    if chart.lists_every_column:
        return data
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


@dataclass(frozen=True)
class _Drawing:
    """What a chart type draws from: the chart, its rows and its bound columns."""

    chart: GgsqlChart
    frame: pa.Table
    x: str
    # None only for a histogram, which counts rows instead of binding a column.
    y: str | None
    color: str | None
    width: int


@dataclass(frozen=True)
class _ChartType:
    """Everything that makes one `DRAW` type different from the others.

    A chart type is defined here and nowhere else in this module: adding one is
    adding an entry to `CHART_TYPES`, not another branch in `build_chart`.
    """

    encode: Callable[[_Drawing], dict[str, object]]
    mark: Callable[[alt.Chart, _Drawing], alt.Chart]
    # The role whose column the type computes from rather than plots. The
    # renderer answers a text column there with an empty chart, not an error.
    numeric_role: str | None = None
    # What a tooltip lists; by default, the columns the chart binds.
    tooltips: Callable[[_Drawing], list[alt.Tooltip]] | None = None
    # A boxplot keeps the renderer's own tooltip -- the quartiles of the box
    # under the pointer -- which a list of row fields would replace.
    keeps_own_tooltip: bool = False


def _encode_xy(drawing: _Drawing) -> dict[str, object]:
    chart = drawing.chart
    encoding: dict[str, object] = {
        "x": alt.X(drawing.x, axis=alt.Axis(labelAngle=0), title=chart.x_title),
        "y": alt.Y(drawing.y, title=chart.y_title),
    }
    if drawing.color is not None:
        encoding["color"] = alt.Color(drawing.color)
    return encoding


def _encode_scatter(drawing: _Drawing) -> dict[str, object]:
    # Clipped marks cut a point on the domain's edge in half, and a chart
    # that zooms clips; the padding keeps the outermost points whole. A nice
    # domain would round the padding out to a whole tick, below zero.
    encoding = _encode_xy(drawing)
    for channel in ("x", "y"):
        encoding[channel] = encoding[channel].scale(padding=SCATTER_PADDING, nice=False)
    return encoding


def _encode_pie(drawing: _Drawing) -> dict[str, object]:
    chart = drawing.chart
    return {
        "theta": alt.Theta(drawing.y, title=chart.y_title),
        "color": alt.Color(
            drawing.color or drawing.x,
            title=chart.x_title if drawing.color is None else drawing.color,
        ),
    }


def _encode_histogram(drawing: _Drawing) -> dict[str, object]:
    # The rows are binned and counted by the renderer, so the y axis describes
    # a bin rather than any column of the query.
    chart = drawing.chart
    encoding: dict[str, object] = {
        "x": alt.X(drawing.x, bin=_HISTOGRAM_BINS, title=chart.x_title),
        "y": alt.Y("count()", title=chart.y_title),
    }
    if drawing.color is not None:
        encoding["color"] = alt.Color(drawing.color)
    return encoding


def _histogram_tooltips(drawing: _Drawing) -> list[alt.Tooltip]:
    """A bar of a histogram is a bin and its count, not a row."""
    tooltips = [alt.Tooltip(drawing.x, bin=_HISTOGRAM_BINS), alt.Tooltip("count()")]
    if drawing.color is not None:
        tooltips.append(alt.Tooltip(drawing.color))
    return tooltips


def _encode_heatmap(drawing: _Drawing) -> dict[str, object]:
    # Both axes are discrete cells, and `sort=None` keeps the order the query
    # returned them in: an ORDER BY is how a heatmap puts Monday before Tuesday.
    chart = drawing.chart
    if drawing.color is None:
        raise ChartRenderError("heatmap requires x, y and color mappings")
    return {
        "x": alt.X(drawing.x, type="ordinal", sort=None, title=chart.x_title),
        "y": alt.Y(drawing.y, type="ordinal", sort=None, title=chart.y_title),
        "color": alt.Color(drawing.color, type="quantitative"),
    }


def _encode_boxplot(drawing: _Drawing) -> dict[str, object]:
    # The mark names its tooltip rows after the y title -- "Median of revenue"
    # -- so an absent title falls back to the column rather than to None, which
    # it would print as "Median of null".
    chart = drawing.chart
    encoding: dict[str, object] = {
        "x": alt.X(drawing.x, axis=alt.Axis(labelAngle=0), title=chart.x_title),
        "y": alt.Y(drawing.y, title=chart.y_title or drawing.y),
    }
    if drawing.color is not None:
        encoding["color"] = alt.Color(drawing.color)
    return encoding


CHART_TYPES: dict[str, _ChartType] = {
    "line": _ChartType(_encode_xy, lambda base, _: base.mark_line(point=True)),
    "bar": _ChartType(_encode_xy, lambda base, _: base.mark_bar()),
    "scatter": _ChartType(_encode_scatter, lambda base, _: base.mark_circle(size=80)),
    "area": _ChartType(_encode_xy, lambda base, _: base.mark_area(opacity=0.7)),
    "pie": _ChartType(_encode_pie, lambda base, _: base.mark_arc()),
    "histogram": _ChartType(
        _encode_histogram,
        lambda base, _: base.mark_bar(),
        numeric_role="x",
        tooltips=_histogram_tooltips,
    ),
    "boxplot": _ChartType(
        _encode_boxplot,
        lambda base, drawing: base.mark_boxplot(
            size=_boxplot_size(drawing.frame, drawing.x, drawing.width)
        ),
        numeric_role="y",
        keeps_own_tooltip=True,
    ),
    "heatmap": _ChartType(
        _encode_heatmap, lambda base, _: base.mark_rect(), numeric_role="color"
    ),
}


def build_chart(
    chart: GgsqlChart,
    data: QueryResult | ArrowStreamExportable,
    config: RenderConfig | None = None,
) -> alt.Chart | alt.LayerChart:
    config = config or RenderConfig()
    frame = _coerce_query_result(data).to_arrow()
    if not chart.has_picture:
        raise ChartRenderError(
            f"a {chart.draw_type} is not drawn; glyf.ggsql.{chart.draw_type} writes it from its rows"
        )
    if chart.is_map:
        return _build_map(chart, frame, config)
    if chart.is_sankey:
        return _build_sankey(chart, frame, config)
    if chart.is_combo:
        return _build_combo(chart, frame, config)
    if chart.is_funnel:
        return _build_funnel(chart, frame, config)
    if chart.is_treemap:
        return _build_treemap(chart, frame, config)
    if chart.is_waterfall:
        return _build_waterfall(chart, frame, config)
    chart_type = CHART_TYPES.get(chart.draw_type)
    if chart_type is None:
        raise ChartRenderError(f"unsupported chart type '{chart.draw_type}'")

    drawing = _drawing(chart, frame, config)
    encoding = chart_type.encode(drawing)
    if "tooltip" in chart.interactions and not chart_type.keeps_own_tooltip:
        encoding["tooltip"] = (
            chart_type.tooltips(drawing)
            if chart_type.tooltips is not None
            else [alt.Tooltip(field) for field in required_columns(chart)]
        )

    if chart.facet is not None:
        return _faceted(chart_type, drawing, encoding, config)
    base = _styled(alt.Chart(frame).encode(**encoding), chart, config)
    return _with_interactions(chart_type.mark(base, drawing), drawing)


def _faceted(
    chart_type: _ChartType,
    drawing: _Drawing,
    encoding: dict[str, object],
    config: RenderConfig,
) -> alt.FacetChart:
    """The chart drawn once per value of its facet column, in a grid.

    Every panel shares its axes and colours, so panels compare at a glance.
    `CONFIG width` and `CONFIG height` are the whole grid's; each panel takes
    its share, a fixed proportion of its width tall when the height is open.
    """
    chart, frame = drawing.chart, drawing.frame
    facet = chart.facet
    assert facet is not None
    panels = max(pc.count_distinct(frame.column(facet)).as_py(), 1)
    columns = min(chart.columns or FACET_COLUMNS, panels)
    rows = -(-panels // columns)
    width = chart.width or config.default_width
    panel_width = max(int((width - FACET_GAP * (columns - 1)) / columns), 60)
    if chart.height is not None:
        panel_height = max(int((chart.height - FACET_GAP * (rows - 1)) / rows), 60)
    else:
        panel_height = max(int(panel_width * FACET_ASPECT), FACET_MIN_HEIGHT)
    # A panel is a fraction of the width: labels that would collide are
    # dropped, every other one first.
    encoding = {**encoding, "x": encoding["x"].axis(labelAngle=0, labelOverlap="parity")}
    panel = chart_type.mark(alt.Chart(frame).encode(**encoding), drawing).properties(
        width=panel_width, height=panel_height
    )
    grid = _with_interactions(panel, drawing).facet(
        facet=alt.Facet(
            facet,
            title=None,
            header=alt.Header(labelFontSize=12, labelFontWeight=600, labelPadding=6),
        ),
        columns=columns,
        spacing=FACET_GAP,
    )
    # A grid's title starts at its left edge by default; centre it as a
    # single chart's is.
    return _configured(grid.properties(**_title(chart, anchor="middle")))


def _build_combo(chart: GgsqlChart, frame: pa.Table, config: RenderConfig) -> alt.LayerChart:
    """Bars of `y` on the left axis and a line of `y2` on the right.

    The two measures rarely share a unit, so each has its own scale. Each
    axis title takes its mark's colour, and a legend names both, so nobody
    reads the line against the bars' axis. Both layers draw from the layered
    chart's data, so a dashboard filter narrows them together.
    """
    _require_columns(chart, frame)
    x, y, y2 = (chart.field_for_role(role) for role in COMBO_ROLES)
    assert x is not None and y is not None and y2 is not None
    _require_numeric(frame, y, "y", "combo")
    _require_numeric(frame, y2, "y2", "combo")
    bar_title = chart.y_title or y
    line_title = chart.y2_title or y2
    # One colour scale over both marks: the legend's two entries.
    legend = alt.Scale(domain=[bar_title, line_title], range=[COMBO_BAR, COMBO_LINE])
    encoding: dict[str, object] = {"x": _band_x(frame, x, chart.x_title)}
    if "tooltip" in chart.interactions:
        encoding["tooltip"] = [alt.Tooltip(field) for field in required_columns(chart)]
    series = alt.Color(f"{_COMBO_SERIES}:N", scale=legend, legend=_COMBO_LEGEND)
    bars = (
        alt.Chart()
        .transform_calculate(**{_COMBO_SERIES: json.dumps(bar_title)})
        .mark_bar()
        .encode(
            y=alt.Y(y, title=bar_title, axis=alt.Axis(titleColor=COMBO_BAR)),
            color=series,
            **encoding,
        )
    )
    line = (
        alt.Chart()
        .transform_calculate(**{_COMBO_SERIES: json.dumps(line_title)})
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            y=alt.Y(y2, title=line_title, axis=alt.Axis(titleColor=COMBO_LINE, orient="right", grid=False)),
            color=series,
            **encoding,
        )
    )
    layered = alt.layer(bars, line, data=frame).resolve_scale(y="independent")
    return _styled(layered, chart, config)


def _build_funnel(chart: GgsqlChart, frame: pa.Table, config: RenderConfig) -> alt.LayerChart:
    """One centred bar per step, as wide as its value, top to bottom.

    The steps run in the query's order when it has an ORDER BY, and largest
    first when it does not: a funnel narrows. Each bar says its value and its
    share of the first step; the tooltip adds the share of the step before.
    The shares are worked out here, from all the rows, so the spec carries
    the picture rather than rows a filter could narrow.
    """
    _require_columns(chart, frame)
    step, value = chart.field_for_role("x"), chart.field_for_role("y")
    assert step is not None and value is not None
    _require_numeric(frame, value, "y", "funnel")
    rows = [
        (name, amount)
        for name, amount in zip(frame.column(step).to_pylist(), frame.column(value).to_pylist())
        if name is not None and amount is not None
    ]
    if not rows:
        raise ChartRenderError("funnel has no steps to draw: every step or value is missing")
    if any(amount < 0 for _, amount in rows):
        raise ChartRenderError(f"funnel needs values of zero or more, and '{value}' has a negative one")
    if not chart.has_order_by:
        rows.sort(key=lambda row: -row[1])
    widest = max(amount for _, amount in rows) or 1
    first = rows[0][1]
    # The step names take part of the width; most of it is the bars'.
    bar_room = (chart.width or config.default_width) * 0.8
    steps = []
    for index, (name, amount) in enumerate(rows):
        previous = rows[index - 1][1] if index else amount
        share = amount / first if first else 0.0
        label = f"{_number(amount)} · {share:.0%}"
        fits = bar_room * amount / widest >= len(label) * FUNNEL_LABEL_CHAR + FUNNEL_LABEL_MARGIN
        steps.append(
            {
                "step": str(name),
                "value": amount,
                "start": (widest - amount) / 2,
                "end": (widest + amount) / 2,
                "share": share,
                "from_previous": amount / previous if previous else 0.0,
                "label": label,
                "inside": fits,
            }
        )

    x_scale = alt.Scale(domain=[0, widest], nice=False, zero=False)
    x = alt.X("start:Q", scale=x_scale, axis=None)
    y = alt.Y(
        "step:N",
        sort=None,
        title=chart.x_title,
        axis=alt.Axis(labelFontSize=11, ticks=False, domain=False, labelPadding=8),
    )
    encoding: dict[str, object] = {}
    if "tooltip" in chart.interactions:
        encoding["tooltip"] = [
            alt.Tooltip("step:N", title=step),
            alt.Tooltip("value:Q", title=value, format=","),
            alt.Tooltip("share:Q", title="of the first step", format=".1%"),
            alt.Tooltip("from_previous:Q", title="of the step before", format=".1%"),
        ]
    base = alt.Chart(pa.Table.from_pylist(steps))
    bars = base.mark_bar(color=COMBO_BAR, cornerRadius=2).encode(x=x, x2="end:Q", y=y, **encoding)
    inside = (
        base.transform_filter("datum.inside")
        .mark_text(color="#ffffff", fontSize=11, fontWeight=600)
        .encode(x=alt.X("middle:Q", scale=x_scale, axis=None), y=y, text="label:N", **encoding)
        .transform_calculate(middle=f"{widest} / 2")
    )
    beside = (
        base.transform_filter("!datum.inside")
        .mark_text(align="left", dx=6, fontSize=11, fontWeight=600)
        .encode(x=alt.X("end:Q", scale=x_scale, axis=None), y=y, text="label:N", **encoding)
    )
    # Vega sizes the step names by measuring them in a stand-in font, a few
    # pixels short of the dashboard's; the room keeps a long name whole.
    layered = alt.layer(bars, inside, beside).properties(padding=FUNNEL_PADDING)
    return _styled(layered, chart, config).configure_view(stroke=None)


def _build_treemap(chart: GgsqlChart, frame: pa.Table, config: RenderConfig) -> alt.LayerChart:
    """A rectangle per tile, coloured by group, with its name and value on it.

    The tiles are laid out in pixels by `glyf.ggsql.treemap`, so both axes are
    pixel scales with no axis drawn. A tile shows its name and value when it
    has room for them; the tooltip has them for every tile.
    """
    _require_columns(chart, frame)
    label, value, group = (chart.field_for_role(role) for role in TREEMAP_ROLES)
    assert label is not None and value is not None
    _require_numeric(frame, value, "value", "treemap")
    width = chart.width or config.default_width
    height = chart.height or config.default_height
    groups = frame.column(group).to_pylist() if group is not None else [None] * frame.num_rows
    try:
        tiles = layout_treemap(
            list(zip(frame.column(label).to_pylist(), groups, frame.column(value).to_pylist())),
            width,
            height,
        )
    except TreemapError as exc:
        raise ChartRenderError(str(exc)) from exc

    total = sum(tile.value for tile in tiles)
    rows = [
        {
            "label": tile.label,
            "group": tile.group,
            "value": tile.value,
            "share": tile.value / total,
            "x": tile.x0,
            "x2": tile.x1,
            "y": tile.y0,
            "y2": tile.y1,
            "name": _fit_text(tile.label, tile.width),
            "amount": _fit_text(_number(tile.value), tile.width),
            "named": tile.width >= TREEMAP_NAME_SIZE[0] and tile.height >= TREEMAP_NAME_SIZE[1],
            "valued": tile.width >= TREEMAP_NAME_SIZE[0] and tile.height >= TREEMAP_VALUE_HEIGHT,
        }
        for tile in tiles
    ]
    x_scale = alt.Scale(domain=[0, width], nice=False, zero=False)
    y_scale = alt.Scale(domain=[0, height], nice=False, zero=False, reverse=True)
    position = {
        "x": alt.X("x:Q", scale=x_scale, axis=None),
        "y": alt.Y("y:Q", scale=y_scale, axis=None),
    }
    color: alt.Color | alt.ColorValue = alt.value(COMBO_BAR)
    if group is not None:
        # Groups in layout order, largest first, so the legend reads like the picture.
        order = list(dict.fromkeys(tile.group for tile in tiles))
        color = alt.Color(
            "group:N", scale=alt.Scale(domain=order), legend=alt.Legend(orient="top", title=group)
        )
    encoding: dict[str, object] = {}
    if "tooltip" in chart.interactions:
        encoding["tooltip"] = [
            alt.Tooltip("label:N", title=label),
            *([alt.Tooltip("group:N", title=group)] if group is not None else []),
            alt.Tooltip("value:Q", title=value, format=","),
            alt.Tooltip("share:Q", title="share of the total", format=".1%"),
        ]
    base = alt.Chart(pa.Table.from_pylist(rows))
    rects = base.mark_rect().encode(x2="x2:Q", y2="y2:Q", color=color, **position, **encoding)
    names = (
        base.transform_filter("datum.named")
        .mark_text(
            align="left", baseline="top", dx=TREEMAP_TEXT_INSET, dy=TREEMAP_TEXT_INSET,
            color="#ffffff", fontSize=11, fontWeight=600,
        )
        .encode(text="name:N", **position, **encoding)
    )
    amounts = (
        base.transform_filter("datum.valued")
        .mark_text(
            align="left", baseline="top", dx=TREEMAP_TEXT_INSET, dy=TREEMAP_TEXT_INSET + 14,
            color="#ffffff", fontSize=11, opacity=0.85,
        )
        .encode(text="amount:N", **position, **encoding)
    )
    return _styled(alt.layer(rects, names, amounts), chart, config).configure_view(stroke=None)


def _build_waterfall(chart: GgsqlChart, frame: pa.Table, config: RenderConfig) -> alt.LayerChart:
    """A bar per change from where the running total stood, then the total.

    The first row is where the total starts, drawn up from zero like the
    closing total; every row after it rises or falls from where the one
    before ended. The steps keep the query's order: a waterfall reads as a
    story, and only the query knows its order. A dashed line carries each
    bar's end across to the next bar.
    """
    _require_columns(chart, frame)
    step, change = chart.field_for_role("x"), chart.field_for_role("y")
    assert step is not None and change is not None
    _require_numeric(frame, change, "y", "waterfall")
    rows = [
        (str(name), float(amount))
        for name, amount in zip(frame.column(step).to_pylist(), frame.column(change).to_pylist())
        if name is not None and amount is not None
    ]
    if not rows:
        raise ChartRenderError("waterfall has no steps to draw: every step or change is missing")
    total_label = chart.labels.get("total", WATERFALL_TOTAL)
    if total_label in {name for name, _ in rows}:
        raise ChartRenderError(
            f"waterfall adds a closing bar named '{total_label}', and a step already has "
            "that name; set LABEL total to another name"
        )

    bars = []
    running = 0.0
    for index, (name, amount) in enumerate(rows):
        start, running = running, running + amount
        kind = "Total" if index == 0 else ("Increase" if amount >= 0 else "Decrease")
        bars.append(_waterfall_bar(name, kind, start, running, amount))
    bars.append(_waterfall_bar(total_label, "Total", 0.0, running, running))
    for bar, following in zip(bars, bars[1:]):
        bar["next"] = following["step"]

    # The connectors share this scale; set its padding, or bars touch.
    x_scale = alt.Scale(type="band", paddingInner=0.3, paddingOuter=0.15)
    x = alt.X("step:N", sort=None, scale=x_scale, title=chart.x_title, axis=alt.Axis(labelAngle=0))
    y = alt.Y("start:Q", title=chart.y_title or change)
    encoding: dict[str, object] = {}
    if "tooltip" in chart.interactions:
        encoding["tooltip"] = [
            alt.Tooltip("step:N", title=step),
            alt.Tooltip("change:Q", title=change, format=","),
            alt.Tooltip("end:Q", title="running total", format=","),
        ]
    base = alt.Chart(pa.Table.from_pylist(bars))
    # The legend names only the kinds of bar the chart has.
    present = {bar["kind"] for bar in bars}
    color = alt.Color(
        "kind:N",
        scale=alt.Scale(
            domain=[kind for kind in WATERFALL_KINDS if kind in present],
            range=[c for kind, c in zip(WATERFALL_KINDS, WATERFALL_COLORS) if kind in present],
        ),
        legend=alt.Legend(orient="top", title=None),
    )
    # Under the bars, so only the stretch between two bars shows.
    connectors = (
        base.transform_filter("isValid(datum.next)")
        .mark_rule(strokeDash=[3, 3], color="#888888")
        .encode(
            x=alt.X("step:N", sort=None, scale=x_scale, bandPosition=0.5),
            x2=alt.X2("next:N", bandPosition=0.5),
            y=alt.Y("end:Q"),
        )
    )
    columns = base.mark_bar().encode(x=x, y=y, y2="end:Q", color=color, **encoding)
    labels = base.mark_text(dy=-6, fontSize=11, fontWeight=600).encode(
        x=x, y=alt.Y("top:Q"), text="label:N", **encoding
    )
    layered = alt.layer(connectors, columns, labels)
    return _styled(layered, chart, config)


def _waterfall_bar(
    name: str, kind: str, start: float, end: float, change: float
) -> dict[str, object]:
    sign = "" if kind == "Total" else ("+" if change >= 0 else "−")
    return {
        "step": name,
        "kind": kind,
        "start": start,
        "end": end,
        "top": max(start, end),
        "change": change,
        "label": f"{sign}{_number(abs(change) if sign else change)}",
        "next": None,
    }


def _fit_text(text: str, room: float) -> str:
    """The text cut to fit a tile this wide, with an ellipsis when it was cut."""
    fits = int((room - 2 * TREEMAP_TEXT_INSET) // FUNNEL_LABEL_CHAR)
    if len(text) <= fits:
        return text
    return text[: max(fits - 1, 1)] + "…"


def _number(value: float) -> str:
    """A value as a label: whole numbers without decimals, others with two."""
    if float(value).is_integer():
        return f"{value:,.0f}"
    return f"{value:,.2f}"


def _band_x(frame: pa.Table, field: str, title: str | None) -> alt.X:
    """An x of whole bands, so a bar is a bar wide even on a date axis.

    A temporal scale gives a bar a few pixels and cuts the first and last in
    half. Dates become bands at the grain they are at: a month when every
    date is the first of one, otherwise a day.
    """
    axis = alt.Axis(labelAngle=0)
    column_type = frame.schema.field(field).type
    if not (pa.types.is_date(column_type) or pa.types.is_timestamp(column_type)):
        return alt.X(field, type="ordinal", sort=None, axis=axis, title=title)
    days = [value for value in frame.column(field).to_pylist() if value is not None]
    monthly = all(value.day == 1 for value in days)
    return alt.X(
        field,
        type="ordinal",
        timeUnit="yearmonth" if monthly else "yearmonthdate",
        axis=axis,
        title=title,
    )


_COMBO_LEGEND = alt.Legend(orient="top", title=None)
# The field each combo layer names itself in, for the legend.
_COMBO_SERIES = "glyf_series"


def _require_columns(chart: GgsqlChart, frame: pa.Table) -> None:
    missing = missing_columns(chart, tuple(frame.column_names))
    if missing:
        joined = ", ".join(f"'{field}'" for field in missing)
        raise ChartRenderError(f"query result missing chart column {joined}")


def _build_map(chart: GgsqlChart, frame: pa.Table, config: RenderConfig) -> alt.LayerChart:
    """Land from the shapes, then the query's regions or points over it.

    The rows are the layered chart's own data and the land brings its own, so
    a dashboard filter -- a transform at the top of the spec -- narrows the
    regions or points and leaves the land whole.
    """
    missing = missing_columns(chart, tuple(frame.column_names))
    if missing:
        joined = ", ".join(f"'{field}'" for field in missing)
        raise ChartRenderError(f"query result missing chart column {joined}")
    try:
        shapes = load_shapes(chart.options.get("shapes"))
    except MapShapesError as exc:
        raise ChartRenderError(str(exc)) from exc

    land_data = _shape_data(shapes)
    land = alt.Chart(land_data).mark_geoshape(
        fill=MAP_LAND,
        fillOpacity=MAP_LAND_OPACITY,
        stroke=MAP_LAND,
        strokeOpacity=0.5,
        strokeWidth=0.5,
    )
    encoding: dict[str, object] = {}
    color = chart.field_for_role("color")
    if color is not None:
        encoding["color"] = alt.Color(
            color, type="quantitative" if _is_numeric(frame, color) else "nominal"
        )
    if "tooltip" in chart.interactions:
        encoding["tooltip"] = [alt.Tooltip(field) for field in required_columns(chart)]

    if chart.is_point_map:
        latitude = chart.field_for_role("latitude")
        longitude = chart.field_for_role("longitude")
        assert latitude is not None and longitude is not None
        _require_numeric(frame, latitude, "latitude", "map")
        _require_numeric(frame, longitude, "longitude", "map")
        encoding["latitude"] = alt.Latitude(latitude, type="quantitative")
        encoding["longitude"] = alt.Longitude(longitude, type="quantitative")
        size = chart.field_for_role("size")
        if size is not None:
            _require_numeric(frame, size, "size", "map")
            encoding["size"] = alt.Size(size, type="quantitative")
        marks = alt.Chart().mark_circle(
            opacity=0.8, stroke=MAP_BORDER, strokeWidth=0.5
        )
    else:
        region = chart.field_for_role("region")
        assert region is not None
        try:
            match = match_regions(shapes, frame.column(region).to_pylist())
        except MapShapesError as exc:
            raise ChartRenderError(str(exc)) from exc
        marks = (
            alt.Chart()
            .transform_lookup(
                lookup=region,
                from_=alt.LookupData(
                    data=land_data, key=match.lookup_key, fields=["type", "geometry"]
                ),
            )
            # A region the shapes do not have has nothing to fill.
            .transform_filter("isValid(datum.geometry)")
            .mark_geoshape(stroke=MAP_BORDER, strokeOpacity=0.6, strokeWidth=0.5)
        )

    layered = alt.layer(land, marks.encode(**encoding), data=frame).project(
        type=chart.options.get("projection", MAP_DEFAULT_PROJECTION)
    )
    # A map is not a plot area: the frame around the view would box the sea.
    return _styled(layered, chart, config).configure_view(stroke=None)


def _build_sankey(chart: GgsqlChart, frame: pa.Table, config: RenderConfig) -> alt.LayerChart:
    """Bands for the flows, a bar per node over them, and the nodes' names.

    The geometry is laid out in pixels by `glyf.ggsql.sankey`, so both axes
    are pixel scales with no axis drawn.
    """
    missing = missing_columns(chart, tuple(frame.column_names))
    if missing:
        joined = ", ".join(f"'{field}'" for field in missing)
        raise ChartRenderError(f"query result missing chart column {joined}")
    source, target, value = (chart.field_for_role(role) for role in SANKEY_ROLES)
    assert source is not None and target is not None and value is not None
    width = chart.width or config.default_width
    height = chart.height or config.default_height
    try:
        layout = layout_sankey(
            list(
                zip(
                    frame.column(source).to_pylist(),
                    frame.column(target).to_pylist(),
                    frame.column(value).to_pylist(),
                )
            ),
            width,
            height,
        )
    except SankeyError as exc:
        raise ChartRenderError(str(exc)) from exc

    x = alt.X("x:Q", scale=alt.Scale(domain=[0, width], nice=False, zero=False), axis=None)
    y_scale = alt.Scale(domain=[0, height], nice=False, zero=False, reverse=True)
    y = alt.Y("y:Q", scale=y_scale, axis=None)
    # One colour per node, in the order the query first names them, so a
    # band takes the colour of the node it leaves.
    colors = alt.Scale(domain=[node.name for node in _first_seen_nodes(layout)])
    tooltip = "tooltip" in chart.interactions

    # A band is an area between its top and bottom edges, not a thick line:
    # a line's bounds grow by half its stroke, which would pad the picture.
    links = alt.Chart(pa.Table.from_pylist(_link_points(layout))).mark_area(
        interpolate="monotone", opacity=SANKEY_LINK_OPACITY
    ).encode(
        x=x,
        y=alt.Y("y:Q", scale=y_scale, axis=None, stack=None),
        y2="y2:Q",
        # An area runs along x, and a band's points rise in x; an `order`
        # channel would split it into one area per point.
        detail="link:N",
        color=alt.Color("source:N", scale=colors, legend=None),
        **(
            {
                "tooltip": [
                    alt.Tooltip("source:N", title=source),
                    alt.Tooltip("target:N", title=target),
                    alt.Tooltip("value:Q", title=value),
                ]
            }
            if tooltip
            else {}
        ),
    )
    node_rows = [
        {"node": node.name, "x": node.x0, "x2": node.x1, "y": node.y0, "y2": node.y1, "value": node.value}
        for node in layout.nodes
    ]
    nodes = alt.Chart(pa.Table.from_pylist(node_rows)).mark_rect().encode(
        x=x,
        x2="x2:Q",
        y=y,
        y2="y2:Q",
        color=alt.Color("node:N", scale=colors, legend=None),
        **(
            {"tooltip": [alt.Tooltip("node:N", title="node"), alt.Tooltip("value:Q", title=value)]}
            if tooltip
            else {}
        ),
    )
    layers = [links, nodes]
    # The last column's names sit to the left of their bars, inside the
    # picture; every other column's to the right.
    for align, last in (("left", False), ("right", True)):
        rows = [
            {
                "label": node.name,
                "x": node.x0 - LABEL_GAP if last else node.x1 + LABEL_GAP,
                "y": (node.y0 + node.y1) / 2,
            }
            for node in layout.nodes
            if (node.column == layout.columns - 1) == last
        ]
        if rows:
            layers.append(
                alt.Chart(pa.Table.from_pylist(rows))
                .mark_text(align=align, baseline="middle", fontSize=11, fontWeight=500)
                .encode(x=x, y=y, text="label:N")
            )
    return _styled(alt.layer(*layers), chart, config).configure_view(stroke=None)


def _first_seen_nodes(layout: Layout) -> list:
    """Nodes in column order, top to bottom: a stable order for the colours."""
    return sorted(layout.nodes, key=lambda node: (node.column, node.y0))


def _link_points(layout: Layout) -> list[dict[str, object]]:
    return [
        {
            "link": index,
            "step": step,
            "x": point[0],
            "y": point[1] - link.width / 2,
            "y2": point[1] + link.width / 2,
            "source": link.source,
            "target": link.target,
            "value": link.value,
        }
        for index, link in enumerate(layout.links)
        for step, point in enumerate(link.curve())
    ]


def unmatched_regions(chart: GgsqlChart, data: QueryResult) -> tuple[str, ...]:
    """The regions a map's query returned that its shapes have no shape for.

    They are left off the map, which is easy to miss, so the build says so.
    """
    region = chart.field_for_role("region")
    if not chart.is_map or region is None or region not in data.columns:
        return ()
    try:
        shapes = load_shapes(chart.options.get("shapes"))
        return match_regions(shapes, data.to_arrow().column(region).to_pylist()).unmatched
    except MapShapesError:
        # The render reports it, with the same message.
        return ()


def _shape_data(shapes: Shapes) -> alt.InlineData:
    return alt.InlineData(
        values=shapes.topology,
        format=alt.DataFormat(type="topojson", feature=shapes.feature),
    )


def _is_numeric(frame: pa.Table, field: str) -> bool:
    column_type = frame.schema.field(field).type
    return pa.types.is_integer(column_type) or pa.types.is_floating(column_type)


def _drawing(chart: GgsqlChart, frame: pa.Table, config: RenderConfig) -> _Drawing:
    """Check the chart's bindings against its rows, and gather them."""
    x_field = chart.field_for_role("x")
    y_field = chart.field_for_role("y")
    if x_field is None:
        raise ChartRenderError(f"{chart.draw_type} requires an x mapping")
    if y_field is None and chart.draw_type != "histogram":
        raise ChartRenderError("VISUALISE requires x and y mappings")

    missing = missing_columns(chart, tuple(frame.column_names))
    if missing:
        joined = ", ".join(f"'{field}'" for field in missing)
        raise ChartRenderError(f"query result missing chart column {joined}")

    numeric_role = CHART_TYPES[chart.draw_type].numeric_role
    if numeric_role is not None:
        numeric_field = chart.field_for_role(numeric_role)
        if numeric_field is not None:
            _require_numeric(frame, numeric_field, numeric_role, chart.draw_type)

    return _Drawing(
        chart=chart,
        frame=frame,
        x=x_field,
        y=y_field,
        color=chart.field_for_role("color"),
        width=chart.width or config.default_width,
    )


def _styled(base: _Styleable, chart: GgsqlChart, config: RenderConfig) -> _Styleable:
    """Size, title and the type treatment every glyf chart shares."""
    return _configured(
        base.properties(
            width=chart.width or config.default_width,
            height=chart.height or config.default_height,
            **_title(chart),
        )
    )


def _title(chart: GgsqlChart, **params: object) -> dict[str, object]:
    if chart.title and chart.subtitle:
        return {"title": alt.TitleParams(text=chart.title, subtitle=chart.subtitle, **params)}
    if chart.title:
        return {"title": alt.TitleParams(text=chart.title, **params) if params else chart.title}
    return {}


_Configurable = TypeVar("_Configurable", alt.Chart, alt.LayerChart, alt.FacetChart)


def _configured(base: _Configurable) -> _Configurable:
    """The type treatment every glyf chart shares."""
    return (
        base.configure_view(stroke="#d9e2ec")
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


def _with_interactions(rendered: alt.Chart, drawing: _Drawing) -> alt.Chart:
    """Legend filtering and zoom, on one chart or on each panel of a grid."""
    interactions = drawing.chart.interactions
    if "legend_filter" in interactions:
        if drawing.color is None:
            raise ChartRenderError("legend_filter interaction requires a color mapping")
        legend_selection = alt.selection_point(fields=[drawing.color], bind="legend")
        rendered = rendered.add_params(legend_selection).encode(
            opacity=alt.condition(legend_selection, alt.value(1), alt.value(0.2))
        )
    if "zoom" in interactions:
        rendered = rendered.interactive()
    return rendered


def _require_numeric(frame: pa.Table, field: str, role: str, draw_type: str) -> None:
    if _is_numeric(frame, field):
        return
    raise ChartRenderError(
        f"{draw_type} needs a numeric {role} column and '{field}' is "
        f"{frame.schema.field(field).type}"
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
