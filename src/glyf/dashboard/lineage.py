"""The lineage view: every source, model and chart behind one dashboard.

Built from the charts' metadata alone, which records each chart's upstream
models and sources at build time, so the view exists in an exported site
with no manifest and no chart files. Laid out here, in three columns with a
fixed geometry, and drawn as a static SVG by the template; the page adds
tracing, pan and zoom with a few lines of script.
"""

from __future__ import annotations

from dataclasses import dataclass

from glyf.dashboard.artifacts import ChartArtifact

NODE_WIDTH = 240
NODE_HEIGHT = 44
NODE_GAP = 14
COLUMN_GAP = 150
MARGIN = 24


@dataclass(frozen=True)
class LineageNode:
    # `source`, `model` or `chart`.
    kind: str
    # What the tracing script keys on: `kind:name`.
    id: str
    title: str
    subtitle: str
    # What the tooltip says: a model's file, a chart's bindings.
    tip: str
    x: float
    y: float


@dataclass(frozen=True)
class LineageEdge:
    source: str
    target: str
    # Cubic curve control, from the right edge of one node to the left of the next.
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class LineageGraph:
    nodes: tuple[LineageNode, ...]
    edges: tuple[LineageEdge, ...]
    width: float
    height: float
    source_count: int
    model_count: int
    chart_count: int

    @property
    def is_empty(self) -> bool:
        return not self.nodes


def build_lineage(charts: tuple[ChartArtifact, ...]) -> LineageGraph:
    """The graph for a dashboard's charts, in display order."""
    models: dict[str, dict[str, object]] = {}
    sources: list[str] = []
    chart_models: dict[str, list[str]] = {}
    chart_sources: dict[str, list[str]] = {}
    for chart in charts:
        lineage = chart.metadata.lineage or {}
        raw_models = lineage.get("models")
        raw_sources = lineage.get("sources")
        chart_models[chart.metadata.name] = []
        chart_sources[chart.metadata.name] = []
        if isinstance(raw_models, dict):
            for name, info in raw_models.items():
                if isinstance(info, dict) and name not in models:
                    models[name] = info
            # The chart reads the models that no other model in its lineage
            # reads: its direct refs. Everything else is reached through them.
            read_by_models = {
                parent
                for info in raw_models.values()
                if isinstance(info, dict)
                for parent in info.get("parents", [])
                if isinstance(parent, str)
            }
            chart_models[chart.metadata.name] = [
                name for name in raw_models if name not in read_by_models
            ]
        if isinstance(raw_sources, list):
            for label in raw_sources:
                if isinstance(label, str) and label not in sources:
                    sources.append(label)
            model_sources = {
                parent[len("source:"):]
                for info in (raw_models or {}).values()
                if isinstance(info, dict)
                for parent in info.get("parents", [])
                if isinstance(parent, str) and parent.startswith("source:")
            }
            chart_sources[chart.metadata.name] = [
                label for label in raw_sources if isinstance(label, str) and label not in model_sources
            ]

    columns = {
        "source": list(sources),
        "model": list(models),
        "chart": [chart.metadata.name for chart in charts],
    }
    tallest = max((len(names) for names in columns.values()), default=0)
    height = tallest * NODE_HEIGHT + max(tallest - 1, 0) * NODE_GAP + 2 * MARGIN
    x_of = {
        "source": MARGIN,
        "model": MARGIN + NODE_WIDTH + COLUMN_GAP,
        "chart": MARGIN + 2 * (NODE_WIDTH + COLUMN_GAP),
    }
    positions: dict[str, tuple[float, float]] = {}
    nodes: list[LineageNode] = []
    for kind, names in columns.items():
        block = len(names) * NODE_HEIGHT + max(len(names) - 1, 0) * NODE_GAP
        top = (height - block) / 2
        for index, name in enumerate(names):
            x, y = x_of[kind], top + index * (NODE_HEIGHT + NODE_GAP)
            node_id = f"{kind}:{name}"
            positions[node_id] = (x, y)
            if kind == "chart":
                chart = next(c for c in charts if c.metadata.name == name)
                title = chart.metadata.title or name
                subtitle = chart.metadata.chart_type
                tip = _bindings(chart)
            elif kind == "model":
                title, subtitle = name, "model"
                path = models[name].get("path")
                tip = str(path) if isinstance(path, str) else "dbt model"
            else:
                title, subtitle, tip = name, "source", "raw table, read through source()"
            nodes.append(LineageNode(kind, node_id, title, subtitle, tip, x, y))

    edges: list[LineageEdge] = []
    seen: set[tuple[str, str]] = set()

    def connect(source: str, target: str) -> None:
        if (source, target) in seen or source not in positions or target not in positions:
            return
        seen.add((source, target))
        (x1, y1), (x2, y2) = positions[source], positions[target]
        edges.append(
            LineageEdge(source, target, x1 + NODE_WIDTH, y1 + NODE_HEIGHT / 2, x2, y2 + NODE_HEIGHT / 2)
        )

    for name, info in models.items():
        for parent in info.get("parents", []):
            if not isinstance(parent, str):
                continue
            if parent.startswith("source:"):
                connect(f"source:{parent[len('source:'):]}", f"model:{name}")
            else:
                connect(f"model:{parent}", f"model:{name}")
    for chart_name, names in chart_models.items():
        for name in names:
            connect(f"model:{name}", f"chart:{chart_name}")
    for chart_name, labels in chart_sources.items():
        for label in labels:
            connect(f"source:{label}", f"chart:{chart_name}")

    return LineageGraph(
        nodes=tuple(nodes),
        edges=tuple(edges),
        width=x_of["chart"] + NODE_WIDTH + MARGIN,
        height=height,
        source_count=len(sources),
        model_count=len(models),
        chart_count=len(charts),
    )


def _bindings(chart: ChartArtifact) -> str:
    metadata = chart.metadata
    if metadata.is_table:
        return "lists " + ", ".join(metadata.columns)
    if metadata.is_kpi:
        parts = [f"{metadata.value} AS value"]
        if metadata.compare:
            parts.append(f"{metadata.compare} AS compare")
        return "binds " + ", ".join(parts)
    parts = [f"{metadata.x} AS x"]
    if metadata.y:
        parts.append(f"{metadata.y} AS y")
    return "binds " + ", ".join(parts)
