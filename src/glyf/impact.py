"""Which charts and dashboards a model or column change touches.

A reviewer reading a pull request that changes a dbt model wants to know what
it does to the dashboards before the diff tells them what moved. glyf has the
raw material: every chart's `ref()` and `source()` calls, resolved against
the manifest, and every column name its SQL mentions. This module joins them.

The model answer is exact. The column answer is honest rather than exact: a
query that names the column reads it, one that selects `*` may read it, and
one whose SQL did not parse may read it too. A column renamed inside a CTE
reaches the chart under another name, and the report says nothing about
that, which is why every line carries how sure it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path

from glyf.config import GlyfConfig
from glyf.dashboard.loader import load_dashboard
from glyf.execution.dialect import sql_dialect
from glyf.ggsql.parser import GgsqlParseError, parse_ggsql_file
from glyf.manifest.loader import DbtManifest, ManifestError, load_manifest
from glyf.manifest.resolver import resolve_refs
from glyf.project.scanner import scan_project


class ImpactError(ValueError):
    """Raised when the target cannot be resolved or the project cannot be read."""


@dataclass(frozen=True)
class ImpactTarget:
    # `model`, `source` or `column`.
    kind: str
    # The model name, or `source_name.table_name`.
    relation: str
    column: str | None = None

    @property
    def label(self) -> str:
        return f"{self.relation}.{self.column}" if self.column else self.relation


@dataclass(frozen=True)
class ChartImpact:
    name: str
    path: str
    # `reads` or `may read`.
    certainty: str
    # Why: `ref(\'fct_orders\')`, `revenue AS y`, `SELECT *`, ...
    detail: str
    dashboards: tuple[str, ...]


@dataclass(frozen=True)
class ImpactReport:
    target: ImpactTarget
    charts: tuple[ChartImpact, ...]

    @property
    def dashboards(self) -> tuple[str, ...]:
        names: list[str] = []
        for chart in self.charts:
            names.extend(chart.dashboards)
        return tuple(dict.fromkeys(names))

    @property
    def uncertain(self) -> int:
        return sum(1 for chart in self.charts if chart.certainty == "may read")

    def headline(self) -> str:
        charts = f"{len(self.charts)} chart{'' if len(self.charts) == 1 else 's'}"
        boards = f"{len(self.dashboards)} dashboard{'' if len(self.dashboards) == 1 else 's'}"
        if not self.charts:
            return f"{self.target.label} is read by no chart"
        line = f"{self.target.label} is read by {charts} on {boards}"
        if self.uncertain:
            line += f" ({self.uncertain} may read it)"
        return line

    def as_document(self) -> dict[str, object]:
        return {
            "target": {
                "kind": self.target.kind,
                "relation": self.target.relation,
                "column": self.target.column,
            },
            "charts": [
                {
                    "name": chart.name,
                    "path": chart.path,
                    "certainty": chart.certainty,
                    "detail": chart.detail,
                    "dashboards": list(chart.dashboards),
                }
                for chart in self.charts
            ],
            "dashboards": list(self.dashboards),
        }


def compute_impact(project: Path, config: GlyfConfig, target: str) -> ImpactReport:
    scan = scan_project(project, config)
    if scan.manifest_path is None:
        raise ImpactError(
            "Missing target/manifest.json. Run dbt compile or dbt build before glyf impact."
        )
    try:
        manifest = load_manifest(scan.manifest_path)
    except ManifestError as exc:
        raise ImpactError(str(exc)) from exc
    resolved = _resolve_target(target, manifest)

    dashboards_by_chart: dict[str, list[str]] = {}
    for path in scan.dashboard_files:
        try:
            dashboard = load_dashboard(path)
        except ValueError:
            # A dashboard `glyf validate` would reject is not this command's
            # to report; the charts still are.
            continue
        for chart in dashboard.chart_names:
            dashboards_by_chart.setdefault(chart, []).append(dashboard.name)

    dialect = sql_dialect(scan.root, config.execution)
    charts = []
    for path in scan.ggsql_files:
        rel_path = path.relative_to(scan.root).as_posix()
        try:
            chart = parse_ggsql_file(path, dialect=dialect)
        except GgsqlParseError as exc:
            raise ImpactError(f"{rel_path}: {exc}") from exc
        resolution = resolve_refs(chart.sql, manifest)
        if "." in resolved.relation:
            reads_relation = tuple(resolved.relation.split(".", 1)) in resolution.sources
        else:
            reads_relation = resolved.relation in resolution.refs
        if not reads_relation:
            continue
        how = _how_read(resolved, chart)
        if how is None:
            continue
        certainty, detail = how
        charts.append(
            ChartImpact(
                name=chart.name,
                path=rel_path,
                certainty=certainty,
                detail=detail,
                dashboards=tuple(dashboards_by_chart.get(chart.name, ())),
            )
        )
    return ImpactReport(target=resolved, charts=tuple(charts))


def _how_read(target: ImpactTarget, chart) -> tuple[str, str] | None:
    """How sure the report is that this chart reads the target, and why."""
    if target.kind == "model":
        return "reads", f"ref('{target.relation}')"
    if target.kind == "source":
        source_name, table_name = target.relation.split(".", 1)
        return "reads", f"source('{source_name}', '{table_name}')"
    column = (target.column or "").lower()
    if column in chart.sql_columns:
        for mapping in chart.visualise:
            if mapping.field.lower() == column:
                return "reads", f"{mapping.field} AS {mapping.role}"
        return "reads", "in the SQL"
    if chart.sql_selects_star:
        return "may read", "SELECT *"
    if chart.sql_warning:
        return "may read", "SQL did not parse"
    return None


def _resolve_target(target: str, manifest: DbtManifest) -> ImpactTarget:
    """`fct_orders`, `raw.orders`, `fct_orders.revenue` or `raw.orders.id`."""
    name = target.strip()
    if not name:
        raise ImpactError("impact needs a model, a source or a column to look for")
    if manifest.node_for_ref(name) is not None:
        return ImpactTarget(kind="model", relation=name)
    if _source(manifest, name) is not None:
        return ImpactTarget(kind="source", relation=name)
    if "." in name:
        relation, column = name.rsplit(".", 1)
        if manifest.node_for_ref(relation) is not None or _source(manifest, relation) is not None:
            return ImpactTarget(kind="column", relation=relation, column=column)
    known = [node.name for node in manifest.models] + [
        f"{source.source_name}.{source.name}" for source in manifest.sources
    ]
    hint = ""
    close = get_close_matches(name.split(".")[0], known, n=3)
    if close:
        hint = " Did you mean " + ", ".join(close) + "?"
    raise ImpactError(
        f"'{name}' is not a model, a source or a column of one in the manifest. "
        f"Name a model (fct_orders), a source (raw.orders) or a column "
        f"(fct_orders.revenue).{hint}"
    )


def _source(manifest: DbtManifest, name: str):
    if "." not in name:
        return None
    source_name, table_name = name.split(".", 1)
    return manifest.node_for_source(source_name, table_name)
