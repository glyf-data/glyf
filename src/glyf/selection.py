"""Choosing which dashboards a build produces.

A build normally renders every chart and every dashboard in the project. When
one project serves several audiences -- each built under its own warehouse
identity, each published behind its own access group -- a build needs to
produce that audience's dashboards and nothing else. A dashboard left out is
not merely tidier: a chart whose table the audience's role cannot read fails
the build, so the audience that should not see it must not build it.

Selection is by dashboard, and the charts follow: a selected build renders
exactly the charts its selected dashboards reference, including the ones a
`source()` filter reads.
"""

from dataclasses import dataclass
from pathlib import Path

from glyf.dashboard.loader import load_dashboard
from glyf.project.scanner import ProjectScan


class SelectionError(ValueError):
    """Raised when a selector is malformed or matches no dashboard."""


TAG_PREFIX = "tag:"
NAME_PREFIX = "name:"


@dataclass(frozen=True)
class Selection:
    """The dashboards a run builds, and the charts they need."""

    selectors: tuple[str, ...]
    dashboard_files: tuple[Path, ...]
    chart_names: frozenset[str]

    def describe(self) -> str:
        return ", ".join(self.selectors)


def resolve_selection(
    scan: ProjectScan, selectors: tuple[str, ...] | None
) -> Selection | None:
    """The dashboards matching `selectors`, or None when nothing was asked for.

    A selector is `tag:NAME`, `name:NAME`, or a bare dashboard name. Several
    are a union. Matching is case-insensitive, and a selector that matches
    nothing is an error -- silently building an empty site would look like a
    successful build of the wrong thing.
    """
    if not selectors:
        return None

    wanted_tags: set[str] = set()
    wanted_names: set[str] = set()
    for selector in selectors:
        text = selector.strip()
        if not text:
            raise SelectionError("--select needs a value, e.g. --select tag:finance")
        if text.startswith(TAG_PREFIX):
            value = text[len(TAG_PREFIX) :].strip()
            if not value:
                raise SelectionError(f"'{selector}' names no tag")
            wanted_tags.add(value.lower())
        elif text.startswith(NAME_PREFIX):
            value = text[len(NAME_PREFIX) :].strip()
            if not value:
                raise SelectionError(f"'{selector}' names no dashboard")
            wanted_names.add(value.lower())
        else:
            wanted_names.add(text.lower())

    matched: list[Path] = []
    chart_names: set[str] = set()
    for path in scan.dashboard_files:
        try:
            dashboard = load_dashboard(path)
        except ValueError as exc:
            rel_path = path.relative_to(scan.root).as_posix()
            raise SelectionError(f"{rel_path}: {exc}") from exc
        tags = {tag.lower() for tag in dashboard.tags}
        if dashboard.name.lower() in wanted_names or tags & wanted_tags:
            matched.append(path)
            chart_names.update(dashboard.artifact_chart_names)

    if not matched:
        joined = ", ".join(selectors)
        raise SelectionError(
            f"no dashboard matches {joined}. Check the dashboard's name, or its "
            "tags: list."
        )

    return Selection(
        selectors=tuple(selectors),
        dashboard_files=tuple(matched),
        chart_names=frozenset(chart_names),
    )
