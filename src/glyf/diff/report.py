"""Write a build comparison where a reviewer and a machine can each read it.

Three views of one result, in one directory that can be uploaded as it is:

- `diff.json` for a script deciding whether to fail a pipeline
- `summary.md` for a pull request comment
- `index.html` with each changed chart before, after, and marked up
"""

import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from glyf.diff.compare import (
    MAX_LISTED_VALUES,
    BuildDiff,
    ChartDiff,
    DataChange,
    FieldChange,
)

DIFF_VERSION = "1"
TEMPLATES_DIR = Path(__file__).parent / "templates"


def write_report(diff: BuildDiff, output_dir: Path) -> Path:
    """Write all three views into `output_dir` and return the HTML page."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    images = output_dir / "images"
    images.mkdir(parents=True)

    for chart in diff.charts:
        if chart.status in ("changed", "removed"):
            shutil.copyfile(
                diff.baseline / "charts" / f"{chart.name}.png",
                images / f"{chart.name}.before.png",
            )
        if chart.status in ("changed", "added"):
            shutil.copyfile(
                diff.current / "charts" / f"{chart.name}.png",
                images / f"{chart.name}.after.png",
            )
        if chart.diff_png is not None:
            (images / f"{chart.name}.diff.png").write_bytes(chart.diff_png)
        if chart.overlay_png is not None:
            (images / f"{chart.name}.overlay.png").write_bytes(chart.overlay_png)

    (output_dir / "diff.json").write_text(
        json.dumps(as_document(diff), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "summary.md").write_text(as_markdown(diff), encoding="utf-8")
    page = output_dir / "index.html"
    page.write_text(_render_html(diff), encoding="utf-8")
    return page


def as_document(diff: BuildDiff) -> dict[str, object]:
    return {
        "diff_version": DIFF_VERSION,
        "baseline_glyf_version": diff.baseline_version,
        "current_glyf_version": diff.current_version,
        "has_changes": diff.has_changes,
        "counts": {
            status: len(diff.with_status(status))  # type: ignore[arg-type]
            for status in ("changed", "added", "removed", "unchanged")
        },
        "charts": {chart.name: _chart_document(chart) for chart in diff.charts},
    }


def _chart_document(chart: ChartDiff) -> dict[str, object]:
    document: dict[str, object] = {"status": chart.status, "title": chart.title}
    if chart.status != "changed":
        return document
    document.update(
        {
            "changed_pixels": chart.changed_pixels,
            "total_pixels": chart.total_pixels,
            "changed_percent": round(chart.changed_percent, 3),
            "marks": _marks_document(chart),
            "before_size": list(chart.before_size or ()),
            "after_size": list(chart.after_size or ()),
            "reasons": list(chart.reasons),
            "images": {
                "before": f"images/{chart.name}.before.png",
                "after": f"images/{chart.name}.after.png",
                "diff": f"images/{chart.name}.diff.png",
            },
        }
    )
    if chart.data is not None:
        document["data"] = {
            "before_rows": chart.data.before_rows,
            "after_rows": chart.data.after_rows,
            "added_fields": list(chart.data.added_fields),
            "removed_fields": list(chart.data.removed_fields),
            "reordered": chart.data.reordered,
            "fields": [
                {
                    "name": change.name,
                    "before_sum": change.before_sum,
                    "after_sum": change.after_sum,
                    "new_values": list(change.new_values),
                    "gone_values": list(change.gone_values),
                }
                for change in chart.data.fields
            ],
        }
    return document


def headline(diff: BuildDiff) -> str:
    """One line a reviewer can act on: '2 changed, 1 added, 14 unchanged'."""
    parts = [
        f"{len(diff.with_status(status))} {status}"  # type: ignore[arg-type]
        for status in ("changed", "added", "removed")
        if diff.with_status(status)  # type: ignore[arg-type]
    ]
    unchanged = len(diff.with_status("unchanged"))
    if not parts:
        return f"No chart changed ({unchanged} compared)"
    return ", ".join([*parts, f"{unchanged} unchanged"])


def as_markdown(diff: BuildDiff) -> str:
    lines = ["### glyf visual diff", "", f"**{headline(diff)}**", ""]
    changed = diff.with_status("changed")
    if changed:
        lines += ["| Chart | Picture | Why | Data |", "| --- | --- | --- | --- |"]
        for chart in changed:
            lines.append(
                f"| {_label(chart)} | {format_percent(chart.changed_percent)} of pixels "
                f"| {'; '.join(chart.reasons)} "
                f"| {'<br>'.join(describe_change(chart)) or 'n/a'} |"
            )
        lines.append("")
    for status, heading in (("added", "Added"), ("removed", "Removed")):
        charts = diff.with_status(status)  # type: ignore[arg-type]
        if charts:
            lines.append(f"**{heading}:** " + ", ".join(_label(chart) for chart in charts))
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def describe_change(chart: ChartDiff) -> list[str]:
    """What moved, in the chart's terms first and then in the rows'."""
    lines = []
    if chart.marks is not None and chart.marks.any:
        lines.append(chart.marks.describe())
    lines.extend(describe_data(chart.data))
    return lines


def describe_data(data: DataChange | None) -> list[str]:
    """The changes to a chart's rows, one plain sentence each."""
    if data is None:
        return []
    if data.is_empty:
        if data.reordered:
            return [
                "no value changed; the query's ORDER BY leaves ties, so add "
                "columns to it until no two rows tie"
            ]
        return []
    lines = []
    if data.before_rows != data.after_rows:
        lines.append(f"rows {data.before_rows:,} → {data.after_rows:,}")
    if data.added_fields:
        lines.append("new columns: " + ", ".join(data.added_fields))
    if data.removed_fields:
        lines.append("removed columns: " + ", ".join(data.removed_fields))
    lines.extend(_describe_field(change) for change in data.fields)
    return lines


def _describe_field(change: FieldChange) -> str:
    if change.before_sum is not None and change.after_sum is not None:
        percent = change.percent
        shift = f" ({percent:+.1f}%)" if percent is not None else ""
        return (
            f"sum of {change.name} {_number(change.before_sum)} → "
            f"{_number(change.after_sum)}{shift}"
        )
    parts = []
    if change.new_values:
        parts.append(f"new in {change.name}: {_listed(change.new_values)}")
    if change.gone_values:
        parts.append(f"gone from {change.name}: {_listed(change.gone_values)}")
    return "; ".join(parts)


def _listed(values: tuple[str, ...]) -> str:
    shown = ", ".join(values[:MAX_LISTED_VALUES])
    rest = len(values) - MAX_LISTED_VALUES
    return f"{shown} and {rest} more" if rest > 0 else shown


def _marks_document(chart: ChartDiff) -> dict[str, object] | None:
    marks = chart.marks
    if marks is None:
        return None
    return {
        "gone": marks.gone,
        "new": marks.new,
        "higher": marks.higher,
        "lower": marks.lower,
        "gone_series": list(marks.gone_series),
        "new_series": list(marks.new_series),
        "changed_x": list(marks.changed_x),
        "summary": marks.describe(),
    }


def _label(chart: ChartDiff) -> str:
    return f"**{chart.title}** `{chart.name}`" if chart.title else f"`{chart.name}`"


def _number(value: float) -> str:
    return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"


def format_percent(value: float) -> str:
    """A share of the picture; a change too small to round up still shows."""
    return "<0.1%" if 0 < value < 0.1 else f"{value:.1f}%"


def _display_path(path: Path) -> str:
    """The path as someone in the working directory would type it.

    A report is uploaded and shared, and an absolute path would publish the
    layout of whichever machine built it.
    """
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return "/".join(path.parts[-2:])


def _render_html(diff: BuildDiff) -> str:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["percent"] = format_percent
    return environment.get_template("diff.html.j2").render(
        diff=diff,
        baseline_label=_display_path(diff.baseline),
        current_label=_display_path(diff.current),
        headline=headline(diff),
        changed=diff.with_status("changed"),
        added=diff.with_status("added"),
        removed=diff.with_status("removed"),
        unchanged=diff.with_status("unchanged"),
        describe_change=describe_change,
    )
