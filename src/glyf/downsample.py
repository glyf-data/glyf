"""Reduce a chart's marks to what its pixels can show.

An 800-pixel-wide chart cannot draw more than 800 distinguishable positions
across its x axis, but glyf hands the renderer a mark per row regardless: at
100,000 rows that is a 27 MB SVG spending a DOM node on marks that land on a
pixel another mark already covers.

M4 is the reduction that does not change the picture. For each pixel column it
keeps four rows -- the leftmost, the rightmost, the highest and the lowest --
which are exactly the ones a line renderer's output depends on in that column.
Everything dropped would have been painted over. The rows kept are rows the
warehouse returned, not values computed from them, which is the difference
between this and averaging each column: an average redraws the series, so a
noisy one loses its envelope and an outlier narrower than a column disappears
into the mean of its neighbours. Measured on a 40-row spike in 100,000 rows,
M4 keeps the peak at 102.3 and the mean reports 72.1.

Only line and area charts qualify. A scatter binned this way snaps its marks to
a lattice and loses the density that a scatter exists to show, which is a
different chart rather than a smaller one, and bar and pie draw a mark per
category rather than per pixel column.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import pyarrow as pa

from glyf.execution.result import QueryResult
from glyf.ggsql.models import GgsqlChart

# Chart types whose marks are bounded by the pixel columns they are drawn
# across, and so can be reduced without changing what the chart shows.
DOWNSAMPLEABLE_DRAW_TYPES = frozenset({"line", "area"})

# A bin per horizontal pixel. Not configurable: fewer bins is where
# downsampling starts moving the line, and more cannot be told apart on screen.
BINS_PER_PIXEL = 1


@dataclass(frozen=True)
class Downsampling:
    """What downsampling did to one chart, or why it did nothing."""

    applied: bool
    reason: str
    rows: int
    marks: int
    bins: int = 0

    def describe(self, rel_path: str) -> str:
        if self.applied:
            return (
                f"{rel_path}: {self.rows} rows downsampled to {self.marks} marks "
                f"(M4, {self.bins} bins)"
            )
        return f"{rel_path}: {self.rows} rows, {self.reason}"


def plan_downsampling(
    chart: GgsqlChart,
    data: QueryResult,
    *,
    enabled: bool,
    over_rows: int,
    width: int,
) -> Downsampling:
    """Whether this chart is downsampled, and what to say about it either way.

    The decision is separate from the work so that a chart which cannot be
    reduced can still be reported: a build that quietly rendered 400,000 marks
    because downsampling was on but did not apply would be the worst of both.
    """
    rows = len(data)
    unchanged = Downsampling(applied=False, reason="", rows=rows, marks=rows)
    if not enabled or rows <= over_rows:
        return unchanged

    if chart.draw_type not in DOWNSAMPLEABLE_DRAW_TYPES:
        return Downsampling(
            applied=False,
            reason=(
                "downsampling applies to line and area charts only; "
                f"rendering all {rows} marks"
            ),
            rows=rows,
            marks=rows,
        )

    x_field = chart.field_for_role("x")
    y_field = chart.field_for_role("y")
    if x_field is None or y_field is None:
        return unchanged

    table = data.to_arrow()
    for role, field in (("x", x_field), ("y", y_field)):
        if field not in table.column_names:
            return unchanged
        if not _is_orderable(table.schema.field(field).type):
            return Downsampling(
                applied=False,
                reason=(
                    f"downsampling needs a numeric or temporal {role} axis and "
                    f"'{field}' is {table.schema.field(field).type}; "
                    f"rendering all {rows} marks"
                ),
                rows=rows,
                marks=rows,
            )

    return Downsampling(
        applied=True,
        reason="",
        rows=rows,
        marks=0,  # not known until the rows are picked
        bins=max(1, width * BINS_PER_PIXEL),
    )


def downsample_m4(
    chart: GgsqlChart, data: QueryResult, bins: int
) -> tuple[QueryResult, int]:
    """The result reduced to at most four rows per x bin, and the mark count.

    Whole rows are kept, not the extreme values alone, so every column a chart
    encodes or a tooltip shows still lines up with the row it came from. A
    chart coloured by a series bins each series separately; sharing bins across
    them would let a busy series' extremes stand in for a quiet one's.
    """
    x_field = chart.field_for_role("x")
    y_field = chart.field_for_role("y")
    color_field = chart.field_for_role("color")
    if x_field is None or y_field is None:
        raise ValueError("downsampling needs a chart with x and y mappings")

    table = data.to_arrow()
    if color_field is not None and color_field not in table.column_names:
        color_field = None

    # An in-memory transform over a result already in hand, not execution: the
    # rows have been fetched, whichever warehouse they came from. duckdb reads
    # `arrow_table` out of this frame by name.
    arrow_table = table
    group = f", {_quote(color_field)}" if color_field else ""
    reduced = duckdb.sql(f"""
        with source as (
            select *, row_number() over () as glyf_row from arrow_table
        ),
        bounds as (
            select min({_quote(x_field)}) as lo, max({_quote(x_field)}) as hi
            from source
        ),
        binned as (
            select
                source.*,
                least(
                    floor(
                        (source.{_quote(x_field)} - bounds.lo)
                        / nullif(bounds.hi - bounds.lo, 0) * {bins}
                    ),
                    {bins} - 1
                ) as glyf_bin
            from source, bounds
        ),
        picked as (
            select
                arg_min(glyf_row, {_quote(x_field)}) as first_row,
                arg_max(glyf_row, {_quote(x_field)}) as last_row,
                arg_min(glyf_row, {_quote(y_field)}) as lowest_row,
                arg_max(glyf_row, {_quote(y_field)}) as highest_row
            from binned
            group by glyf_bin{group}
        ),
        keep as (
            select first_row as glyf_row from picked
            union select last_row from picked
            union select lowest_row from picked
            union select highest_row from picked
        )
        select source.* exclude (glyf_row)
        from source join keep on source.glyf_row = keep.glyf_row
        order by source.{_quote(x_field)}
    """).to_arrow_table()

    return QueryResult.from_arrow(reduced), reduced.num_rows


def _is_orderable(field_type: pa.DataType) -> bool:
    """Can this column be cut into evenly spaced bins along an axis?

    A string x axis is a category, not a position: bins over it would be bins
    over whatever order the warehouse happened to return.
    """
    return bool(
        pa.types.is_integer(field_type)
        or pa.types.is_floating(field_type)
        or pa.types.is_decimal(field_type)
        or pa.types.is_temporal(field_type)
    )


def _quote(identifier: str) -> str:
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'
