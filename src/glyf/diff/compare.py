"""Compare two glyf builds chart by chart.

A build renders the same data to the same bytes, so a chart whose PNG differs
from the last build's is a chart that changed. This module says which charts
those are, how much of each picture moved, and as far as the builds record it,
why: a different query, different rows, or a different renderer.

A table or a kpi has no picture: the rows are the chart, laid out as an HTML
fragment that is byte-stable in the same way. One whose fragment differs is a
chart that changed, and what changed is said in the rows' terms alone.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from glyf import _core
from glyf.config import RenderConfig
from glyf.diff.overlay import MarkChange, build_overlay

Status = Literal["added", "removed", "changed", "unchanged"]

# How many category values a report lists before it says "and N more".
MAX_LISTED_VALUES = 5


class DiffError(ValueError):
    """Raised when two builds cannot be compared."""


@dataclass(frozen=True)
class FieldChange:
    """How one column of a chart's rows moved between the builds."""

    name: str
    # For a numeric column: its sum on each side.
    before_sum: float | None = None
    after_sum: float | None = None
    # For any other column: values that appeared and values that went away.
    new_values: tuple[str, ...] = ()
    gone_values: tuple[str, ...] = ()

    @property
    def percent(self) -> float | None:
        if self.before_sum in (None, 0) or self.after_sum is None:
            return None
        return (self.after_sum - self.before_sum) / abs(self.before_sum) * 100


@dataclass(frozen=True)
class DataChange:
    before_rows: int
    after_rows: int
    added_fields: tuple[str, ...] = ()
    removed_fields: tuple[str, ...] = ()
    fields: tuple[FieldChange, ...] = ()
    # The same rows, returned in a different order.
    reordered: bool = False

    @property
    def is_empty(self) -> bool:
        return (
            self.before_rows == self.after_rows
            and not self.added_fields
            and not self.removed_fields
            and not self.fields
        )


@dataclass(frozen=True)
class ChartDiff:
    name: str
    status: Status
    title: str | None = None
    # A table or a kpi: no picture, no pixels, no overlay; the rows are the
    # change. At most one of these is set.
    table: bool = False
    kpi: bool = False
    changed_pixels: int = 0
    total_pixels: int = 0
    before_size: tuple[int, int] | None = None
    after_size: tuple[int, int] | None = None
    # Why the chart changed, as far as the two builds record it.
    reasons: tuple[str, ...] = ()
    data: DataChange | None = None
    # The marked-up comparison; only a changed chart has one.
    diff_png: bytes | None = field(default=None, repr=False, compare=False)
    # The chart's own account of the change: new marks over the old ones in
    # grey, what moved boxed. Needs both builds' rows and a chart type the
    # overlay can draw; otherwise the pixel picture is all there is.
    overlay_png: bytes | None = field(default=None, repr=False, compare=False)
    marks: MarkChange | None = None
    # A table's or a kpi's fragment on each side, for the report to show it
    # as it was shown.
    before_fragment: str | None = field(default=None, repr=False, compare=False)
    after_fragment: str | None = field(default=None, repr=False, compare=False)

    @property
    def is_fragment(self) -> bool:
        return self.table or self.kpi

    @property
    def changed_percent(self) -> float:
        if not self.total_pixels:
            return 0.0
        return self.changed_pixels / self.total_pixels * 100


@dataclass(frozen=True)
class BuildDiff:
    baseline: Path
    current: Path
    charts: tuple[ChartDiff, ...]
    baseline_version: str | None = None
    current_version: str | None = None

    def with_status(self, status: Status) -> tuple[ChartDiff, ...]:
        return tuple(chart for chart in self.charts if chart.status == status)

    @property
    def has_changes(self) -> bool:
        return any(chart.status != "unchanged" for chart in self.charts)


def resolve_build_dir(path: Path) -> Path:
    """The directory holding a build's `charts/`, given a path near it.

    Accepts the output directory itself, an exported `site/`, or a project
    root, because a baseline is whichever of those CI happened to keep.
    """
    for candidate in (path, path / "target" / "glyf"):
        if (candidate / "charts").is_dir():
            return candidate
    raise DiffError(
        f"{path} does not hold a glyf build: expected a charts/ directory in it "
        "or in its target/glyf/. Run glyf build there first."
    )


def compare_builds(
    baseline: Path,
    current: Path,
    *,
    threshold: float = 0.0,
    tolerance: int = 0,
    render_config: RenderConfig | None = None,
) -> BuildDiff:
    """Compare every chart of two builds.

    `threshold` is the percentage of a chart's pixels that may differ before
    it counts as changed. It is zero by default because glyf's renders are
    byte-stable; raise it when the two builds were rendered on different
    machines, where font rasterisation moves a few pixels by itself.
    """
    baseline = resolve_build_dir(baseline)
    current = resolve_build_dir(current)
    before_record = _load_json(baseline / "build.json")
    after_record = _load_json(current / "build.json")

    before_charts = _chart_images(baseline)
    after_charts = _chart_images(current)
    before_fragments = _chart_fragments(baseline)
    after_fragments = _chart_fragments(current)
    charts = []
    for name in sorted(
        before_charts.keys()
        | after_charts.keys()
        | before_fragments.keys()
        | after_fragments.keys()
    ):
        if name in before_fragments or name in after_fragments:
            kind, _ = after_fragments.get(name) or before_fragments[name]
            charts.append(
                _compare_fragment(
                    name,
                    _title(current if name in after_fragments else baseline, name),
                    kind,
                    before_fragments.get(name),
                    after_fragments.get(name),
                    baseline=baseline,
                    current=current,
                    before_record=before_record,
                    after_record=after_record,
                )
            )
            continue
        old, new = before_charts.get(name), after_charts.get(name)
        title = _title(current if new else baseline, name)
        if old is None:
            charts.append(ChartDiff(name=name, status="added", title=title))
        elif new is None:
            charts.append(ChartDiff(name=name, status="removed", title=title))
        else:
            charts.append(
                _compare_chart(
                    name,
                    title,
                    old,
                    new,
                    baseline=baseline,
                    current=current,
                    before_record=before_record,
                    after_record=after_record,
                    threshold=threshold,
                    tolerance=tolerance,
                    render_config=render_config or RenderConfig(),
                )
            )

    return BuildDiff(
        baseline=baseline,
        current=current,
        charts=tuple(charts),
        baseline_version=_version(before_record),
        current_version=_version(after_record),
    )


def _compare_chart(
    name: str,
    title: str | None,
    old: Path,
    new: Path,
    *,
    baseline: Path,
    current: Path,
    before_record: dict[str, object],
    after_record: dict[str, object],
    threshold: float,
    tolerance: int,
    render_config: RenderConfig,
) -> ChartDiff:
    before_bytes, after_bytes = old.read_bytes(), new.read_bytes()
    if before_bytes == after_bytes:
        return ChartDiff(name=name, status="unchanged", title=title)

    try:
        raw = _core.diff_png(before_bytes, after_bytes, tolerance)
    except ValueError as exc:
        raise DiffError(f"chart '{name}': {exc}") from exc

    changed, total = int(raw["changed_pixels"]), int(raw["total_pixels"])
    if total and changed / total * 100 <= threshold:
        return ChartDiff(name=name, status="unchanged", title=title)

    data = _data_change(baseline, current, name)
    overlay = _overlay(baseline, current, name, render_config)
    return ChartDiff(
        name=name,
        status="changed",
        title=title,
        changed_pixels=changed,
        total_pixels=total,
        before_size=tuple(raw["before_size"]),
        after_size=tuple(raw["after_size"]),
        reasons=_reasons(name, before_record, after_record, data),
        data=data,
        diff_png=bytes(raw["diff_png"]),
        overlay_png=overlay.png if overlay else None,
        marks=overlay.marks if overlay else None,
    )


def _compare_fragment(
    name: str,
    title: str | None,
    kind: str,
    old: tuple[str, Path] | None,
    new: tuple[str, Path] | None,
    *,
    baseline: Path,
    current: Path,
    before_record: dict[str, object],
    after_record: dict[str, object],
) -> ChartDiff:
    """A table or a kpi judged by its fragment, explained by its rows.

    The fragment is written from the rows and nothing else, so two builds with
    the same rows write the same bytes, and a byte that differs is a row, a
    column or a label that did. There is no threshold: there are no pixels to
    forgive, and a cell that changed is a change.
    """
    kinds = {"table": kind == "table", "kpi": kind == "kpi"}
    before_text = old[1].read_text(encoding="utf-8") if old is not None else None
    after_text = new[1].read_text(encoding="utf-8") if new is not None else None
    if before_text is None:
        return ChartDiff(
            name=name, status="added", title=title, after_fragment=after_text, **kinds
        )
    if after_text is None:
        return ChartDiff(
            name=name, status="removed", title=title, before_fragment=before_text, **kinds
        )
    if before_text == after_text:
        return ChartDiff(name=name, status="unchanged", title=title, **kinds)

    data = _data_change(baseline, current, name)
    return ChartDiff(
        name=name,
        status="changed",
        title=title,
        reasons=_reasons(name, before_record, after_record, data),
        data=data,
        before_fragment=before_text,
        after_fragment=after_text,
        **kinds,
    )


def _overlay(baseline: Path, current: Path, name: str, render_config: RenderConfig):
    """The chart drawn over its old self, when both builds published rows."""
    rel = Path("data") / "normalized" / f"{name}.data.json"
    before, after = _load_json(baseline / rel), _load_json(current / rel)
    if not before or not after:
        return None
    metadata = _load_json(current / "charts" / f"{name}.json")
    try:
        return build_overlay(metadata, _rows(before), _rows(after), render_config)
    except Exception:  # noqa: BLE001 - the overlay is an extra; the diff stands without it
        return None


def _reasons(
    name: str,
    before_record: dict[str, object],
    after_record: dict[str, object],
    data: DataChange | None,
) -> tuple[str, ...]:
    """Why the picture moved, in the order a reviewer would ask."""
    reasons = []
    before_chart = _chart_record(before_record, name)
    after_chart = _chart_record(after_record, name)
    before_sql = before_chart.get("compiled_sql_sha256")
    after_sql = after_chart.get("compiled_sql_sha256")
    if before_sql and after_sql and before_sql != after_sql:
        reasons.append("the query changed")
    if data is not None and not data.is_empty:
        reasons.append("the rows changed")
    elif data is not None and data.reordered:
        # Nothing about the data moved except which row came first. A query
        # whose ORDER BY leaves ties may return them either way round, and a
        # scatter then draws one point over the other differently.
        reasons.append("the same rows came back in a different order")
    elif (
        data is None
        and before_chart.get("row_count") is not None
        and before_chart.get("row_count") != after_chart.get("row_count")
    ):
        reasons.append("the rows changed")
    before_version, after_version = _version(before_record), _version(after_record)
    if before_version and after_version and before_version != after_version:
        reasons.append(f"glyf {before_version} -> {after_version}")
    if not reasons:
        # Same query, same rows, same glyf: what is left is the chart block
        # itself -- its DRAW type, labels, size or interactions.
        reasons.append("the chart definition changed")
    return tuple(reasons)


def _data_change(baseline: Path, current: Path, name: str) -> DataChange | None:
    """How the chart's rows moved, when both builds published them.

    A build under `export.row_data: exclude` publishes no rows, and then there
    is nothing to compare: the picture is the only evidence.
    """
    rel = Path("data") / "normalized" / f"{name}.data.json"
    before, after = _load_json(baseline / rel), _load_json(current / rel)
    if not before or not after:
        return None
    before_rows, after_rows = _rows(before), _rows(after)
    before_fields, after_fields = _fields(before), _fields(after)

    changes = []
    for field_name in (f for f in after_fields if f in before_fields):
        old = [row.get(field_name) for row in before_rows]
        new = [row.get(field_name) for row in after_rows]
        change = _field_change(field_name, old, new)
        if change is not None:
            changes.append(change)

    return DataChange(
        before_rows=len(before_rows),
        after_rows=len(after_rows),
        added_fields=tuple(f for f in after_fields if f not in before_fields),
        removed_fields=tuple(f for f in before_fields if f not in after_fields),
        fields=tuple(changes),
        reordered=before_rows != after_rows
        and _canonical(before_rows) == _canonical(after_rows),
    )


def _field_change(name: str, old: list[object], new: list[object]) -> FieldChange | None:
    if _all_numbers(old) and _all_numbers(new):
        before_sum = float(sum(v for v in old if v is not None))  # type: ignore[misc]
        after_sum = float(sum(v for v in new if v is not None))  # type: ignore[misc]
        if before_sum == after_sum:
            return None
        return FieldChange(name=name, before_sum=before_sum, after_sum=after_sum)

    old_values = {str(v) for v in old if v is not None}
    new_values = {str(v) for v in new if v is not None}
    if old_values == new_values:
        return None
    return FieldChange(
        name=name,
        new_values=tuple(sorted(new_values - old_values)),
        gone_values=tuple(sorted(old_values - new_values)),
    )


def _canonical(rows: list[dict[str, object]]) -> list[str]:
    """The rows as a bag: equal for two results that differ only in order."""
    return sorted(json.dumps(row, sort_keys=True, default=str) for row in rows)


def _all_numbers(values: list[object]) -> bool:
    present = [v for v in values if v is not None]
    return bool(present) and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in present
    )


def _chart_images(build_dir: Path) -> dict[str, Path]:
    return {path.stem: path for path in sorted((build_dir / "charts").glob("*.png"))}


# The charts a build writes as HTML rather than draws, by their file suffix.
FRAGMENT_KINDS = ("table", "kpi")


def _chart_fragments(build_dir: Path) -> dict[str, tuple[str, Path]]:
    """The tables and kpis a build wrote, by chart name, with their kind."""
    fragments = {}
    for kind in FRAGMENT_KINDS:
        suffix = f".{kind}.html"
        for path in sorted((build_dir / "charts").glob(f"*{suffix}")):
            fragments[path.name[: -len(suffix)]] = (kind, path)
    return fragments


def _title(build_dir: Path, name: str) -> str | None:
    title = _load_json(build_dir / "charts" / f"{name}.json").get("title")
    return title if isinstance(title, str) else None


def _chart_record(record: dict[str, object], name: str) -> dict[str, object]:
    charts = record.get("charts")
    chart = charts.get(name) if isinstance(charts, dict) else None
    return chart if isinstance(chart, dict) else {}


def _version(record: dict[str, object]) -> str | None:
    version = record.get("glyf_version")
    return version if isinstance(version, str) else None


def _rows(document: dict[str, object]) -> list[dict[str, object]]:
    rows = document.get("rows")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _fields(document: dict[str, object]) -> list[str]:
    fields = document.get("fields")
    return [str(f) for f in fields] if isinstance(fields, list) else []


def _load_json(path: Path) -> dict[str, object]:
    """The JSON object at `path`, or nothing: every one of these is optional.

    An exported site carries no build.json, and a build under
    `export.row_data: exclude` carries no rows. A diff of pictures alone is
    still a diff.
    """
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return document if isinstance(document, dict) else {}
