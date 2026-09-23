"""Which charts a dashboard filter can redraw, and how.

A filter names a column. A chart the filter applies to is one whose published
rows carry that column: a drawn chart is redrawn in the browser from its
Vega spec with the filter as a transform, a table hides the rows that do not
match, and a kpi, which is one aggregated number, cannot be recomputed and
is dimmed instead. A chart the filter cannot touch is dimmed too, and says
so, rather than staying still and looking filtered.
"""

from __future__ import annotations

from dataclasses import dataclass

from glyf.dashboard.artifacts import ChartArtifact
from glyf.dashboard.loader import Dashboard


@dataclass(frozen=True)
class FilterTarget:
    field: str
    # `vega` (redraw from the spec), `table` (hide rows) or `none` (dim).
    mode: str


@dataclass(frozen=True)
class FilterPlan:
    # Chart name -> the filters that apply to it, in dashboard order.
    targets: dict[str, tuple[FilterTarget, ...]]
    # Charts whose spec the page must carry so a filter can redraw them.
    vega_charts: frozenset[str]

    @property
    def live(self) -> bool:
        return any(target.mode != "none" for targets in self.targets.values() for target in targets)

    def modes(self, chart: str) -> str:
        """`plan:vega week:vega` for a card's data attribute."""
        return " ".join(f"{t.field}:{t.mode}" for t in self.targets.get(chart, ()))


def plan_filters(dashboard: Dashboard, charts: dict[str, ChartArtifact]) -> FilterPlan:
    targets: dict[str, list[FilterTarget]] = {name: [] for name in charts}
    vega_charts: set[str] = set()
    for spec in dashboard.filters:
        for name, artifact in charts.items():
            if spec.charts and name not in spec.charts:
                continue
            mode = _mode(artifact, spec.field)
            if mode == "vega":
                vega_charts.add(name)
            targets[name].append(FilterTarget(field=spec.field, mode=mode))
    return FilterPlan(
        targets={name: tuple(items) for name, items in targets.items()},
        vega_charts=frozenset(vega_charts),
    )


def _mode(artifact: ChartArtifact, field: str) -> str:
    metadata = artifact.metadata
    if metadata.is_kpi:
        return "none"
    if metadata.is_table:
        return "table" if field in metadata.columns else "none"
    if artifact.vega_spec is None or field not in _spec_columns(artifact):
        return "none"
    return "vega"


def _spec_columns(artifact: ChartArtifact) -> frozenset[str]:
    """The columns the chart's inlined data carries: what a transform can see.

    Under `export.row_data: minimal` that is the encoded columns only, so a
    filter on any other column cannot apply, which is the point of the mode.
    """
    spec = artifact.vega_spec
    if isinstance(spec, dict):
        datasets = spec.get("datasets")
        if isinstance(datasets, dict):
            for rows in datasets.values():
                if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                    return frozenset(str(key) for key in rows[0])
    return frozenset(artifact.data.fields)
