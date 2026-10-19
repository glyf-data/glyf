"""How a `DRAW treemap` is laid out: a rectangle per row, its area its value.

Vega-Lite has no treemap mark, so glyf computes the rectangles here and draws
them as rects on pixel scales, as it does a sankey. The layout is the
squarified one (Bruls, Huizing and van Wijk): tiles are placed largest first,
a row at a time, adding a tile to the row while that keeps the row's tiles
closer to square. With a `group`, the groups are laid out first and each
group's tiles inside it, so a group reads as one block.

Ties in value keep the order the query first names them in, so the same rows
lay out the same way on every build.
"""

from dataclasses import dataclass
from decimal import Decimal
from numbers import Real

# Room between two groups, and between two tiles of one group.
GROUP_GAP = 4
TILE_GAP = 1


class TreemapError(ValueError):
    """Raised when a treemap's rows cannot be laid out."""


@dataclass(frozen=True)
class Tile:
    label: str
    group: str | None
    value: float
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class _Box:
    x: float
    y: float
    width: float
    height: float


def layout_treemap(
    rows: list[tuple[object, object, object]], width: float, height: float
) -> tuple[Tile, ...]:
    """Tiles in pixels for `(label, group, value)` rows, in a `width` by `height` box.

    Rows naming the same label in the same group are one tile, their values
    summed. A row with a missing label or value is skipped, and so is a zero.
    """
    totals = _totals(rows)
    by_group: dict[str | None, dict[str, float]] = {}
    for (group, label), value in totals.items():
        by_group.setdefault(group, {})[label] = value

    tiles: list[Tile] = []
    if list(by_group) == [None]:
        tiles.extend(_place(by_group[None], None, _Box(0, 0, width, height), TILE_GAP))
        return tuple(tiles)
    group_totals = {group: sum(labels.values()) for group, labels in by_group.items()}
    for group, box in _squarify(group_totals, _Box(0, 0, width, height)):
        tiles.extend(_place(by_group[group], group, _inset(box, GROUP_GAP / 2), TILE_GAP))
    return tuple(tiles)


def _totals(
    rows: list[tuple[object, object, object]],
) -> dict[tuple[str | None, str], float]:
    totals: dict[tuple[str | None, str], float] = {}
    for label, group, amount in rows:
        if label is None or amount is None:
            continue
        # A warehouse's SUM of a NUMERIC column comes back as a Decimal.
        if isinstance(amount, bool) or not isinstance(amount, (Real, Decimal)):
            raise TreemapError(f"treemap needs a numeric value and got {amount!r}")
        if amount < 0:
            raise TreemapError(
                f"treemap value for '{label}' is negative ({amount}); a tile's area cannot be"
            )
        if amount == 0:
            continue
        key = (None if group is None else str(group), str(label))
        totals[key] = totals.get(key, 0.0) + float(amount)
    if not totals:
        raise TreemapError("treemap has nothing to draw: every value is zero or missing")
    return totals


def _place(
    values: dict[str, float], group: str | None, box: _Box, gap: float
) -> list[Tile]:
    tiles = []
    for label, cell in _squarify(values, box):
        inner = _inset(cell, gap / 2)
        tiles.append(
            Tile(
                label=label,
                group=group,
                value=values[label],
                x0=inner.x,
                y0=inner.y,
                x1=inner.x + inner.width,
                y1=inner.y + inner.height,
            )
        )
    return tiles


def _inset(box: _Box, by: float) -> _Box:
    """The box shrunk on every side, unless that would leave nothing."""
    if box.width <= 2 * by or box.height <= 2 * by:
        return box
    return _Box(box.x + by, box.y + by, box.width - 2 * by, box.height - 2 * by)


def _squarify(values: dict[str, float], box: _Box) -> list[tuple[str, _Box]]:
    """Each key's box, its area in proportion to its value, largest first."""
    # `sorted` is stable, so equal values keep the order they were first seen.
    ordered = sorted(values.items(), key=lambda item: -item[1])
    total = sum(value for _, value in ordered)
    scale = box.width * box.height / total
    pending = [(key, value * scale) for key, value in ordered]
    placed: list[tuple[str, _Box]] = []
    x, y, width, height = box.x, box.y, box.width, box.height
    while pending:
        side = min(width, height)
        row = [pending[0]]
        for item in pending[1:]:
            if _worst([area for _, area in row + [item]], side) > _worst(
                [area for _, area in row], side
            ):
                break
            row.append(item)
        pending = pending[len(row) :]
        row_area = sum(area for _, area in row)
        if width >= height:
            # A column down the left side of what is left.
            column = row_area / height if height else 0.0
            top = y
            for key, area in row:
                tall = area / column if column else 0.0
                placed.append((key, _Box(x, top, column, tall)))
                top += tall
            x, width = x + column, width - column
        else:
            # A row along the top of what is left.
            band = row_area / width if width else 0.0
            left = x
            for key, area in row:
                wide = area / band if band else 0.0
                placed.append((key, _Box(left, y, wide, band)))
                left += wide
            y, height = y + band, height - band
    return placed


def _worst(areas: list[float], side: float) -> float:
    """The worst aspect ratio in a row of these areas along a side this long."""
    total = sum(areas)
    if total == 0 or side == 0:
        return float("inf")
    return max(
        max(side * side * area / (total * total), (total * total) / (side * side * area))
        for area in areas
    )
