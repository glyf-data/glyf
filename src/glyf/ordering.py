"""Row order for a chart whose query does not choose one.

A chart is drawn from the rows its query returned, in the order it returned
them, and for several chart types that order is part of the picture: it sets a
stacked bar's segment order, a pie's slice order, which points a scatter draws
on top, and a heatmap's axes. SQL only promises an order when the query asks
for one, so the same project can draw a different chart on every build.

Where the query asks, glyf keeps that order exactly. Where it does not, glyf
picks one: there is no intent to override, and an arbitrary order that holds
still is worth more than an arbitrary order that does not.
"""

from dataclasses import dataclass

import pyarrow as pa
import pyarrow.compute as pc

from glyf.execution.result import QueryResult
from glyf.ggsql.models import GgsqlChart
from glyf.ggsql.renderer import required_columns

# Chart types whose picture changes with the order of the rows, so the order
# glyf picked is worth reporting. A line or an area is drawn along its x axis
# whatever order the rows arrive in. A table's picture is the order.
_STACKS = frozenset({"bar", "area", "histogram"})
_ALWAYS_ORDER_SENSITIVE = frozenset({"pie", "heatmap", "table"})


@dataclass(frozen=True)
class RowOrder:
    """What glyf did about the order of a chart's rows."""

    applied: bool
    columns: tuple[str, ...] = ()
    reason: str = ""

    def describe(self, rel_path: str) -> str:
        if self.applied:
            return (
                f"{rel_path}: the query has no ORDER BY, so glyf ordered the rows "
                f"by {', '.join(self.columns)} to keep the chart reproducible. "
                "Add an ORDER BY to choose the order yourself."
            )
        return f"{rel_path}: {self.reason}"


def order_rows(chart: GgsqlChart, data: QueryResult) -> tuple[QueryResult, RowOrder]:
    """The chart's rows in a defined order, and what to say about it.

    Returns the rows untouched when the query orders itself. Ordering by the
    encoded columns first puts the chart's own axes and series in a sensible
    order; the remaining columns follow only to break ties, so that two rows
    the picture cannot tell apart still land the same way round every build.
    """
    if chart.has_order_by:
        return data, RowOrder(applied=False)

    table = data.to_arrow()
    encoded = [field for field in required_columns(chart) if field in table.column_names]
    rest = [name for name in table.column_names if name not in encoded]
    keys = [name for name in [*encoded, *rest] if _is_sortable(table.schema.field(name).type)]

    if not keys:
        return data, RowOrder(
            applied=False,
            reason=(
                "the query has no ORDER BY and none of its columns can be ordered, "
                "so the rendered chart may differ between builds"
            ),
        )

    ordered = table.take(
        pc.sort_indices(table, sort_keys=[(name, "ascending") for name in keys])
    )
    reported = tuple(encoded) or tuple(keys[:1])
    return QueryResult.from_arrow(ordered), RowOrder(applied=True, columns=reported)


def is_order_sensitive(chart: GgsqlChart) -> bool:
    """Whether the order of the rows shows up in this chart's picture.

    Every chart is ordered, because any of them can feed an artifact a build
    compares against the last one. Only these are worth a line of output: the
    order glyf chose is visible, so it is the author's to disagree with.
    """
    if chart.draw_type in _ALWAYS_ORDER_SENSITIVE:
        return True
    has_color = chart.field_for_role("color") is not None
    if chart.draw_type in _STACKS:
        # Stacked marks are laid down in the order the rows arrive.
        return has_color
    if chart.draw_type == "scatter":
        # Points of one colour hide each other invisibly; two colours do not.
        return has_color
    return False


def _is_sortable(field_type: pa.DataType) -> bool:
    """Whether Arrow can order a column of this type.

    Numbers, text, times and booleans order; a list or a struct does not, and
    asking would raise rather than return an order.
    """
    return not (
        pa.types.is_nested(field_type)
        or pa.types.is_dictionary(field_type)
        or pa.types.is_null(field_type)
    )
