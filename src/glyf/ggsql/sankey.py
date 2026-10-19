"""How a `DRAW sankey` is laid out: stages as columns, flows as bands.

Vega-Lite has no sankey mark, so glyf computes the picture's geometry here
and draws it from marks every renderer has: a rect per node, a thick line per
link and a text per label. The layout is plain arithmetic on the query's
rows, so the same rows lay out the same way on every build.

A node's column is the longest path to it from a node nothing flows into;
a node nothing flows out of goes to the last column, so every flow ends at
the right edge. A loop has no such order and is an error.
"""

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from numbers import Real

NODE_WIDTH = 14
# Vertical room between two nodes in one column.
NODE_GAP = 12
# Room between a node and its label.
LABEL_GAP = 6
# Points sampled along each link's curve.
CURVE_STEPS = 16


class SankeyError(ValueError):
    """Raised when a sankey's rows cannot be laid out."""


@dataclass(frozen=True)
class Node:
    name: str
    column: int
    x0: float
    x1: float
    y0: float
    y1: float
    value: float


@dataclass(frozen=True)
class Link:
    source: str
    target: str
    value: float
    # The band's thickness, and where its centre meets each node.
    width: float
    y_source: float
    y_target: float
    x_source: float
    x_target: float

    def curve(self) -> list[tuple[float, float]]:
        """The band's centre line: a cubic curve leaving and arriving level."""
        middle = (self.x_source + self.x_target) / 2
        points = (
            (self.x_source, self.y_source),
            (middle, self.y_source),
            (middle, self.y_target),
            (self.x_target, self.y_target),
        )
        return [_bezier(points, step / CURVE_STEPS) for step in range(CURVE_STEPS + 1)]


@dataclass(frozen=True)
class Layout:
    nodes: tuple[Node, ...]
    links: tuple[Link, ...]
    columns: int


def layout_sankey(
    rows: list[tuple[object, object, object]], width: float, height: float
) -> Layout:
    """Nodes and links in pixels, for a picture `width` by `height`.

    Rows linking the same two nodes are one flow, their values summed. A row
    with a missing end or value is skipped, and so is a zero.
    """
    flows, first_seen = _flows(rows)
    names = sorted(first_seen, key=first_seen.__getitem__)
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    for source, target in flows:
        outgoing[source].append(target)
        incoming[target].append(source)

    column = _columns(names, outgoing, incoming)
    columns = max(column.values()) + 1
    value = {
        name: max(
            sum(flows[(source, name)] for source in incoming[name]),
            sum(flows[(name, target)] for target in outgoing[name]),
        )
        for name in names
    }
    stacks: list[list[str]] = [[] for _ in range(columns)]
    for name in names:
        stacks[column[name]].append(name)

    scale = min(
        (height - NODE_GAP * (len(stack) - 1)) / sum(value[name] for name in stack)
        for stack in stacks
    )
    if scale <= 0:
        raise SankeyError(
            f"sankey has too many nodes in one column for a height of {height:g}; "
            "set CONFIG height higher or group the smaller flows in SQL"
        )
    step = (width - NODE_WIDTH) / (columns - 1)
    top: dict[str, float] = {}
    for index, stack in enumerate(stacks):
        if index > 0:
            # Nodes fed from higher up sit higher: fewer bands cross.
            stack.sort(key=lambda name: _feeding_height(name, incoming, flows, top, value, scale))
        top.update(_stack(stack, value, scale, height))

    nodes = {
        name: Node(
            name=name,
            column=column[name],
            x0=column[name] * step,
            x1=column[name] * step + NODE_WIDTH,
            y0=top[name],
            y1=top[name] + value[name] * scale,
            value=value[name],
        )
        for name in names
    }
    return Layout(
        nodes=tuple(nodes[name] for stack in stacks for name in stack),
        links=_links(flows, nodes, scale),
        columns=columns,
    )


def _flows(
    rows: list[tuple[object, object, object]],
) -> tuple[dict[tuple[str, str], float], dict[str, int]]:
    flows: dict[tuple[str, str], float] = {}
    first_seen: dict[str, int] = {}
    for source, target, amount in rows:
        if source is None or target is None or amount is None:
            continue
        # A warehouse's SUM of a NUMERIC column comes back as a Decimal.
        if isinstance(amount, bool) or not isinstance(amount, (Real, Decimal)):
            raise SankeyError(f"sankey needs a numeric value and got {amount!r}")
        if amount < 0:
            raise SankeyError(
                f"sankey flow from '{source}' to '{target}' is negative ({amount}); "
                "a flow's width cannot be"
            )
        if amount == 0:
            continue
        start, end = str(source), str(target)
        if start == end:
            raise SankeyError(f"sankey flow from '{start}' to itself has nowhere to go")
        first_seen.setdefault(start, len(first_seen))
        first_seen.setdefault(end, len(first_seen))
        flows[(start, end)] = flows.get((start, end), 0.0) + float(amount)
    if not flows:
        raise SankeyError("sankey has no flows to draw: every value is zero or missing")
    return flows, first_seen


def _columns(
    names: list[str],
    outgoing: dict[str, list[str]],
    incoming: dict[str, list[str]],
) -> dict[str, int]:
    """Each node's column: its longest path from a start, ends pushed right."""
    waiting = {name: len(incoming[name]) for name in names}
    ready = [name for name in names if waiting[name] == 0]
    column = {name: 0 for name in names}
    placed = 0
    while ready:
        name = ready.pop(0)
        placed += 1
        for target in outgoing[name]:
            column[target] = max(column[target], column[name] + 1)
            waiting[target] -= 1
            if waiting[target] == 0:
                ready.append(target)
    if placed < len(names):
        looped = [name for name in names if waiting[name] > 0]
        raise SankeyError(
            f"sankey flows loop back through {', '.join(repr(n) for n in looped[:3])}; "
            "every flow has to move forward to a later stage"
        )
    last = max(column.values())
    for name in names:
        if not outgoing[name]:
            column[name] = last
    return column


def _feeding_height(
    name: str,
    incoming: dict[str, list[str]],
    flows: dict[tuple[str, str], float],
    top: dict[str, float],
    value: dict[str, float],
    scale: float,
) -> float:
    """The flow-weighted middle of the nodes that feed this one."""
    weights = [(flows[(source, name)], top[source] + value[source] * scale / 2) for source in incoming[name] if source in top]
    total = sum(weight for weight, _ in weights)
    if total == 0:
        return float("inf")
    return sum(weight * middle for weight, middle in weights) / total


def _stack(
    stack: list[str], value: dict[str, float], scale: float, height: float
) -> dict[str, float]:
    """Tops for one column's nodes, the column centred in the height."""
    used = sum(value[name] * scale for name in stack) + NODE_GAP * (len(stack) - 1)
    y = (height - used) / 2
    tops = {}
    for name in stack:
        tops[name] = y
        y += value[name] * scale + NODE_GAP
    return tops


def _links(
    flows: dict[tuple[str, str], float], nodes: dict[str, Node], scale: float
) -> tuple[Link, ...]:
    """Each flow as a band, stacked at both ends so bands never overlap."""
    leaving: dict[str, list[tuple[str, str]]] = defaultdict(list)
    arriving: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for pair in flows:
        leaving[pair[0]].append(pair)
        arriving[pair[1]].append(pair)
    starts: dict[tuple[str, str], float] = {}
    ends: dict[tuple[str, str], float] = {}
    for name, node in nodes.items():
        y = node.y0
        for pair in sorted(leaving[name], key=lambda pair: nodes[pair[1]].y0):
            width = flows[pair] * scale
            starts[pair] = y + width / 2
            y += width
        y = node.y0
        for pair in sorted(arriving[name], key=lambda pair: nodes[pair[0]].y0):
            width = flows[pair] * scale
            ends[pair] = y + width / 2
            y += width
    return tuple(
        Link(
            source=source,
            target=target,
            value=amount,
            width=amount * scale,
            y_source=starts[(source, target)],
            y_target=ends[(source, target)],
            x_source=nodes[source].x1,
            x_target=nodes[target].x0,
        )
        for (source, target), amount in flows.items()
    )


def _bezier(
    points: tuple[tuple[float, float], ...], t: float
) -> tuple[float, float]:
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = points
    u = 1 - t
    a, b, c, d = u**3, 3 * u * u * t, 3 * u * t * t, t**3
    return (
        a * x0 + b * x1 + c * x2 + d * x3,
        a * y0 + b * y1 + c * y2 + d * y3,
    )
