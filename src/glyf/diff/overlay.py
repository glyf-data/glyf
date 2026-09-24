"""Draw what moved in a chart's own terms.

The pixel comparison says which pixels differ and cannot say why: a bar that
shrank lights up at its old height and its new one, a line that re-spread
across the axis lights up twice. This module draws the comparison the way a
reviewer thinks about it: the new marks in colour, the old marks in grey
behind them, and a box around every category whose value moved. It also says
it in words: `bars: 6 gone (Partners), 5 lower`.

It needs the rows both builds published, and the chart's roles, so a build
under `export.row_data: exclude` gets the pixel picture only.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import altair as alt
import pyarrow as pa

from glyf.config import RenderConfig

# The same colour the pixel diff marks with: absent from every chart palette.
MARK = "#e11d74"
GHOST = "#94a3b8"

# What the overlay can draw: charts with a category on x and a value on y.
# A scatter's x is a number, so there is no category to box; a histogram
# computes its own bins, a boxplot its own quartiles; a heatmap has no
# height to compare and a pie no axis. Those keep the pixel picture.
SUPPORTED = frozenset({"bar", "line", "area"})

MAX_NAMED = 4

# How far an end of the y axis must move, as a share of the larger range,
# before the sentence says so. Less than this and the redraw barely shows.
AXIS_SHIFT = 0.10

Row = dict[str, object]
Key = tuple[str, str | None]


@dataclass(frozen=True)
class MarkChange:
    """How the chart's marks moved between the two builds."""

    draw_type: str
    gone: int = 0
    new: int = 0
    higher: int = 0
    lower: int = 0
    gone_series: tuple[str, ...] = ()
    new_series: tuple[str, ...] = ()
    # The x values whose marks moved, in the chart's own order.
    changed_x: tuple[str, ...] = ()
    # The span the y axis has to cover in each build, zero included, as the
    # renderer draws it: stacked totals for a stacked chart.
    y_before: tuple[float, float] | None = None
    y_after: tuple[float, float] | None = None
    # x categories only one build has, in the chart's own order.
    x_gone: tuple[str, ...] = ()
    x_new: tuple[str, ...] = ()

    @property
    def any(self) -> bool:
        return bool(self.gone or self.new or self.higher or self.lower)

    def describe(self) -> str:
        """One sentence in the chart's terms: `bars: 6 gone (Partners), 5 lower`."""
        noun = "bars" if self.draw_type == "bar" else "points"
        parts = []
        if self.gone:
            parts.append(f"{self.gone} gone" + _named(self.gone_series))
        if self.new:
            parts.append(f"{self.new} new" + _named(self.new_series))
        if self.higher:
            parts.append(f"{self.higher} higher")
        if self.lower:
            parts.append(f"{self.lower} lower")
        return f"{noun}: " + ", ".join(parts) if parts else f"{noun}: unchanged"

    @property
    def y_rescaled(self) -> bool:
        """Whether an end of the y axis moved enough to redraw every mark."""
        if self.y_before is None or self.y_after is None:
            return False
        span = max(
            self.y_before[1] - self.y_before[0], self.y_after[1] - self.y_after[0]
        )
        if span <= 0:
            return False
        return any(
            abs(after - before) / span >= AXIS_SHIFT
            for before, after in zip(self.y_before, self.y_after)
        )

    def describe_axes(self) -> str | None:
        """The axes' own change: `y axis 0–60k → 0–400k; x axis: 2026-04 added`.

        A rescaled y axis moves every mark on the page, so a reviewer sees
        boxes and shifts everywhere; this says which part of that is scale.
        """
        parts = []
        if self.y_rescaled and self.y_before and self.y_after:
            parts.append(f"y axis {_span(self.y_before)} → {_span(self.y_after)}")
        x_parts = []
        if self.x_new:
            x_parts.append(_listed_x(self.x_new) + " added")
        if self.x_gone:
            x_parts.append(_listed_x(self.x_gone) + " dropped")
        if x_parts:
            parts.append("x axis: " + ", ".join(x_parts))
        return "; ".join(parts) if parts else None


def _span(bounds: tuple[float, float]) -> str:
    return f"{compact(bounds[0])}–{compact(bounds[1])}"


def compact(value: float) -> str:
    """A number as an axis would label it: 400000 is 400k, 1250000 is 1.25M."""
    for size, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if abs(value) >= size:
            return f"{value / size:.3g}{suffix}"
    if value == int(value):
        return str(int(value))
    return f"{value:.3g}"


def _listed_x(values: tuple[str, ...]) -> str:
    shown = ", ".join(values[:MAX_NAMED])
    if len(values) > MAX_NAMED:
        shown += f" and {len(values) - MAX_NAMED} more"
    return shown


def _named(series: tuple[str, ...]) -> str:
    if not series:
        return ""
    shown = ", ".join(series[:MAX_NAMED])
    if len(series) > MAX_NAMED:
        shown += f" and {len(series) - MAX_NAMED} more"
    return f" ({shown})"


@dataclass(frozen=True)
class Overlay:
    png: bytes
    marks: MarkChange


def build_overlay(
    metadata: dict[str, object],
    before_rows: list[Row],
    after_rows: list[Row],
    config: RenderConfig,
) -> Overlay | None:
    """The overlay for one chart, or nothing when it cannot be drawn.

    `metadata` is the chart's `charts/<name>.json` from the current build,
    which names the draw type and the columns bound to x, y and color.
    """
    draw_type = metadata.get("chart_type")
    x, y, color = metadata.get("x"), metadata.get("y"), metadata.get("color")
    if draw_type not in SUPPORTED or not isinstance(x, str) or not isinstance(y, str):
        return None
    if color is not None and not isinstance(color, str):
        return None
    if not _has_columns(before_rows, x, y, color) or not _has_columns(after_rows, x, y, color):
        return None

    before = _values(before_rows, x, y, color)
    after = _values(after_rows, x, y, color)
    if not before or not after:
        return None
    x_order = _x_order(before_rows, after_rows, x)
    marks = _mark_change(
        draw_type, before, after, x_order=x_order, stacked=color is not None and draw_type != "line"
    )
    chart = _draw(draw_type, metadata, x, y, color, before, after, marks, x_order, config)
    buffer = io.BytesIO()
    chart.save(buffer, format="png")
    return Overlay(png=buffer.getvalue(), marks=marks)


def _has_columns(rows: list[Row], *columns: str | None) -> bool:
    return bool(rows) and all(column is None or column in rows[0] for column in columns)


def _values(rows: list[Row], x: str, y: str, color: str | None) -> dict[Key, float]:
    """y per (x, series), summed the way a stacked bar sums repeated keys."""
    values: dict[Key, float] = {}
    for row in rows:
        value = row.get(y)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        key = (str(row.get(x)), str(row.get(color)) if color is not None else None)
        values[key] = values.get(key, 0.0) + float(value)
    return values


def _x_order(before_rows: list[Row], after_rows: list[Row], x: str) -> list[str]:
    """Every x value either build has, in the order the baseline drew them.

    The baseline's order is the chart's own (its ORDER BY, or glyf's), so a
    category the new build dropped stays where it was; a category the new
    build added goes after the ones they share.
    """
    order: list[str] = []
    for row in [*before_rows, *after_rows]:
        value = str(row.get(x))
        if value not in order:
            order.append(value)
    return order


def _mark_change(
    draw_type: str,
    before: dict[Key, float],
    after: dict[Key, float],
    *,
    x_order: list[str],
    stacked: bool = False,
) -> MarkChange:
    gone = [key for key in before if key not in after]
    new = [key for key in after if key not in before]
    higher = [key for key in after if key in before and after[key] > before[key]]
    lower = [key for key in after if key in before and after[key] < before[key]]

    before_series = {series for _, series in before if series is not None}
    after_series = {series for _, series in after if series is not None}
    changed_x = {x for x, _ in [*gone, *new, *higher, *lower]}
    before_x = {x for x, _ in before}
    after_x = {x for x, _ in after}
    return MarkChange(
        draw_type=draw_type,
        gone=len(gone),
        new=len(new),
        higher=len(higher),
        lower=len(lower),
        gone_series=tuple(sorted(before_series - after_series)),
        new_series=tuple(sorted(after_series - before_series)),
        changed_x=tuple(x for x in x_order if x in changed_x),
        y_before=_y_span(before, stacked=stacked),
        y_after=_y_span(after, stacked=stacked),
        x_gone=tuple(x for x in x_order if x in before_x and x not in after_x),
        x_new=tuple(x for x in x_order if x in after_x and x not in before_x),
    )


def _y_span(values: dict[Key, float], *, stacked: bool) -> tuple[float, float] | None:
    """The y range the chart has to show, zero included as the renderer does.

    Stacked marks reach their total at each x, positives up and negatives down;
    unstacked ones reach their own value.
    """
    if not values:
        return None
    if stacked:
        ups: dict[str, float] = {}
        downs: dict[str, float] = {}
        for (x, _), value in values.items():
            if value >= 0:
                ups[x] = ups.get(x, 0.0) + value
            else:
                downs[x] = downs.get(x, 0.0) + value
        ends = [*ups.values(), *downs.values()]
    else:
        ends = list(values.values())
    return (min(0.0, *ends), max(0.0, *ends))


def _draw(
    draw_type: str,
    metadata: dict[str, object],
    x: str,
    y: str,
    color: str | None,
    before: dict[Key, float],
    after: dict[Key, float],
    marks: MarkChange,
    x_order: list[str],
    config: RenderConfig,
) -> alt.LayerChart:
    before_table = _table(before, x, y, color)
    after_table = _table(after, x, y, color)
    # A nominal x keeps the chart's own order and gives a bar its band; a
    # temporal-looking x would drop categories one build no longer has.
    x_axis = alt.X(x, type="nominal", sort=x_order, axis=alt.Axis(labelAngle=0), title=_label(metadata, "x_title", x))
    y_axis = alt.Y(y, type="quantitative", title=_label(metadata, "y_title", y))

    layers: list[alt.Chart] = []
    if draw_type == "bar":
        ghost = alt.Chart(before_table).mark_bar(
            fillOpacity=0, stroke=GHOST, strokeWidth=1.5, strokeDash=[4, 3]
        )
        current = alt.Chart(after_table).mark_bar()
    elif draw_type == "area":
        ghost = alt.Chart(before_table).mark_line(
            color=GHOST, strokeDash=[4, 3], strokeWidth=1.5
        )
        current = alt.Chart(after_table).mark_area(opacity=0.7)
    else:
        ghost = alt.Chart(before_table).mark_line(
            color=GHOST, strokeDash=[4, 3], strokeWidth=1.5, point={"color": GHOST}
        )
        current = alt.Chart(after_table).mark_line(point=True)

    ghost_encoding: dict[str, object] = {"x": x_axis, "y": y_axis}
    current_encoding: dict[str, object] = {"x": x_axis, "y": y_axis}
    if color is not None:
        # The ghost stacks (or splits into series) the way the chart does,
        # but stays grey; the legend comes from the current marks.
        if draw_type == "bar":
            # The ghost carries the legend, so a series the new build dropped
            # is still listed, with no bars under it.
            ghost_encoding["color"] = alt.Color(color, type="nominal")
        else:
            ghost_encoding["detail"] = alt.Detail(color, type="nominal")
        current_encoding["color"] = alt.Color(color, type="nominal")
    layers.append(ghost.encode(**ghost_encoding))
    layers.append(current.encode(**current_encoding))

    if marks.changed_x:
        layers.append(_boxes(x, y, color, before, after, marks.changed_x, x_axis))

    title = metadata.get("title")
    title_text = title if isinstance(title, str) else str(metadata.get("name", ""))
    chart = alt.layer(*layers).properties(
        width=_size(metadata, "width", config.default_width),
        height=_size(metadata, "height", config.default_height),
        title=alt.TitleParams(
            text=title_text, subtitle="before in grey, what moved boxed"
        ),
    )
    return chart.resolve_scale(color="shared")


def _boxes(
    x: str,
    y: str,
    color: str | None,
    before: dict[Key, float],
    after: dict[Key, float],
    changed_x: tuple[str, ...],
    x_axis: alt.X,
) -> alt.Chart:
    """One box per x value that moved, from the axis to just above the taller mark."""
    tops = []
    for value in changed_x:
        before_top = _top(before, value, color)
        after_top = _top(after, value, color)
        top = max(before_top, after_top)
        tops.append({x: value, "y0": min(0.0, min(before_top, after_top)), "y1": top * 1.04})
    table = pa.Table.from_pylist(tops)
    return (
        alt.Chart(table)
        .mark_rect(fill=None, stroke=MARK, strokeWidth=2)
        .encode(x=x_axis, y=alt.Y("y0", type="quantitative", title=None), y2=alt.Y2("y1", title=None))
    )


def _label(metadata: dict[str, object], key: str, default: str) -> str:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else default


def _top(values: dict[Key, float], x: str, color: str | None) -> float:
    """A bar's stacked total, or a line's value, at one x."""
    at_x = [v for (vx, _), v in values.items() if vx == x]
    if not at_x:
        return 0.0
    return sum(at_x) if color is not None else max(at_x)


def _table(values: dict[Key, float], x: str, y: str, color: str | None) -> pa.Table:
    rows = []
    for (vx, series), value in values.items():
        row: Row = {x: vx, y: value}
        if color is not None:
            row[color] = series
        rows.append(row)
    return pa.Table.from_pylist(rows)


def _size(metadata: dict[str, object], key: str, default: int) -> int:
    value = metadata.get(key)
    return value if isinstance(value, int) and value > 0 else default
