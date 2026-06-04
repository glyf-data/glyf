import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from glyf import _core
from glyf.dashboard.components import ComponentSpec


_COLUMN_TRACK_RE = re.compile(
    r"^(?P<number>\d+(?:\.\d+)?)(?P<unit>%|fr|px|rem|em|ch|vw|vh)$"
)
_FILTER_SOURCE_RE = re.compile(
    r"""^source\(\s*['"]?(?P<chart>[A-Za-z0-9_.-]+)['"]?\s*,\s*['"]?(?P<field>[A-Za-z0-9_.-]+)['"]?\s*\)$"""
)
_TOOLBAR_ACTIONS = {"share", "visibility"}
_TOOLBAR_VISIBILITIES = {"public", "private"}
_DASHBOARD_THEMES = {"light", "dark"}
_CHART_THEMES = {"auto", "light", "dark"}


@dataclass(frozen=True)
class DashboardLayout:
    kind: str = "grid"
    columns: int | None = None
    column_widths: tuple[str, ...] = ()

    @property
    def column_template(self) -> str | None:
        if not self.column_widths:
            return None
        return " ".join(f"minmax(0, {width})" for width in self.column_widths)


@dataclass(frozen=True)
class DashboardToolbar:
    enabled: bool = True
    visibility: str = "private"
    actions: tuple[str, ...] = ("share", "visibility")


@dataclass(frozen=True)
class DashboardItem:
    kind: str
    chart: str | None = None
    component: str | None = None
    component_spec: ComponentSpec | None = None
    title: str | None = None
    text: str | None = None
    label: str | None = None
    value: str | None = None
    note: str | None = None
    width: int | None = None


@dataclass(frozen=True)
class DashboardFilter:
    field: str
    values: tuple[str, ...] = ()
    source_chart: str | None = None
    source_field: str | None = None

    @property
    def is_sourced(self) -> bool:
        return self.source_chart is not None and self.source_field is not None


@dataclass(frozen=True)
class DashboardSection:
    title: str | None
    description: str | None
    columns: int | None
    column_widths: tuple[str, ...]
    items: tuple[DashboardItem, ...]

    @property
    def column_template(self) -> str | None:
        if not self.column_widths:
            return None
        return " ".join(f"minmax(0, {width})" for width in self.column_widths)


@dataclass(frozen=True)
class Dashboard:
    path: Path
    name: str
    title: str
    charts: tuple[str, ...]
    tags: tuple[str, ...] = ()
    theme: str | None = None
    chart_theme: str | None = None
    description: str | None = None
    layout: str | None = None
    layout_config: DashboardLayout = DashboardLayout()
    toolbar: DashboardToolbar = DashboardToolbar()
    summary: tuple[str, ...] = ()
    summary_components: tuple[ComponentSpec, ...] = ()
    filters: tuple[DashboardFilter, ...] = ()
    sections: tuple[DashboardSection, ...] = ()

    @property
    def chart_names(self) -> tuple[str, ...]:
        names = list(self.charts)
        for section in self.sections:
            names.extend(item.chart for item in section.items if item.chart is not None)
        return tuple(dict.fromkeys(names))

    @property
    def artifact_chart_names(self) -> tuple[str, ...]:
        names = list(self.chart_names)
        names.extend(
            filter_spec.source_chart
            for filter_spec in self.filters
            if filter_spec.source_chart is not None
        )
        return tuple(dict.fromkeys(name for name in names if name is not None))


def load_dashboard(path: Path) -> Dashboard:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError("invalid YAML") from exc

    if not isinstance(raw, dict):
        raise ValueError("expected a YAML mapping")
    _validate_dashboard_schema(raw, path)

    name = raw.get("name")
    title = raw.get("title", name)
    description = raw.get("description")
    theme = raw.get("theme")
    chart_theme = raw.get("chart_theme")
    layout_raw = raw.get("layout")
    toolbar_raw = raw.get("toolbar")
    summary_raw = raw.get("summary", [])
    filters_raw = raw.get("filters", [])
    tags_raw = raw.get("tags", [])
    charts = raw.get("charts", [])
    sections_raw = raw.get("sections", raw.get("groups", []))

    if not isinstance(name, str) or not name:
        raise ValueError("expected non-empty 'name'")
    if not isinstance(title, str) or not title:
        raise ValueError("expected non-empty 'title'")
    if description is not None and not isinstance(description, str):
        raise ValueError("expected 'description' to be a string")
    if theme is not None:
        if not isinstance(theme, str) or theme not in _DASHBOARD_THEMES:
            joined = ", ".join(sorted(_DASHBOARD_THEMES))
            raise ValueError(f"expected 'theme' to be one of: {joined}")
    if chart_theme is not None:
        if not isinstance(chart_theme, str) or chart_theme not in _CHART_THEMES:
            joined = ", ".join(sorted(_CHART_THEMES))
            raise ValueError(f"expected 'chart_theme' to be one of: {joined}")
    if not isinstance(charts, list) or not all(isinstance(item, str) for item in charts):
        raise ValueError("expected 'charts' to be a list of chart names")

    layout_config = _parse_layout(layout_raw)
    toolbar = _parse_toolbar(toolbar_raw)
    summary = _parse_summary(summary_raw)
    filters = _parse_filters(filters_raw)
    tags = _parse_tags(tags_raw)
    sections = _parse_sections(sections_raw)

    return Dashboard(
        path=path,
        name=name,
        title=title,
        tags=tags,
        theme=theme,
        chart_theme=chart_theme,
        description=description,
        layout=layout_config.kind if layout_raw is not None else None,
        layout_config=layout_config,
        toolbar=toolbar,
        summary=summary,
        filters=filters,
        charts=tuple(charts),
        sections=sections,
    )


def _parse_layout(raw: object) -> DashboardLayout:
    if raw is None:
        return DashboardLayout()
    if isinstance(raw, str):
        if not raw:
            raise ValueError("expected 'layout' to be a non-empty string")
        return DashboardLayout(kind=raw)
    if not isinstance(raw, dict):
        raise ValueError("expected 'layout' to be a string or mapping")

    kind = raw.get("type", raw.get("kind", "grid"))
    if not isinstance(kind, str) or not kind:
        raise ValueError("expected 'layout.type' to be a non-empty string")
    columns, column_widths = _parse_columns(raw.get("columns"), "layout.columns")
    return DashboardLayout(
        kind=kind,
        columns=columns,
        column_widths=column_widths,
    )


def _parse_sections(raw: object) -> tuple[DashboardSection, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("expected 'sections' to be a list")

    sections = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"expected section {index} to be a mapping")

        title = _optional_string(item.get("title"), f"sections[{index}].title")
        description = _optional_string(
            item.get("description"),
            f"sections[{index}].description",
        )
        columns, column_widths = _parse_columns(
            item.get("columns"),
            f"sections[{index}].columns",
        )
        items = _parse_section_items(item, index)
        sections.append(
            DashboardSection(
                title=title,
                description=description,
                columns=columns,
                column_widths=column_widths,
                items=items,
            )
        )
    return tuple(sections)


def _parse_toolbar(raw: object) -> DashboardToolbar:
    if raw is None:
        return DashboardToolbar()
    if isinstance(raw, bool):
        return DashboardToolbar(enabled=raw)
    if not isinstance(raw, dict):
        raise ValueError("expected 'toolbar' to be a boolean or mapping")

    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("expected 'toolbar.enabled' to be true or false")

    visibility = raw.get("visibility", "private")
    if not isinstance(visibility, str) or visibility not in _TOOLBAR_VISIBILITIES:
        joined = ", ".join(sorted(_TOOLBAR_VISIBILITIES))
        raise ValueError(f"expected 'toolbar.visibility' to be one of: {joined}")

    actions_raw = raw.get("actions", ("share", "visibility"))
    if not isinstance(actions_raw, (list, tuple)):
        raise ValueError("expected 'toolbar.actions' to be a list")
    actions: list[str] = []
    for index, action in enumerate(actions_raw, start=1):
        if not isinstance(action, str) or action not in _TOOLBAR_ACTIONS:
            joined = ", ".join(sorted(_TOOLBAR_ACTIONS))
            raise ValueError(
                f"expected 'toolbar.actions[{index}]' to be one of: {joined}"
            )
        actions.append(action)

    return DashboardToolbar(
        enabled=enabled,
        visibility=visibility,
        actions=tuple(dict.fromkeys(actions)),
    )


def _parse_summary(raw: object) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("expected 'summary' to be a list")

    items: list[str] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, str) or not item:
            raise ValueError(
                f"expected 'summary[{index}]' to be a non-empty macro expression"
            )
        items.append(item)
    return tuple(items)


def _parse_tags(raw: object) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("expected 'tags' to be a list of non-empty strings")

    tags: list[str] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"expected 'tags[{index}]' to be a non-empty string")
        tags.append(item.strip())
    return tuple(dict.fromkeys(tags))


def _parse_filters(raw: object) -> tuple[DashboardFilter, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("expected 'filters' to be a list")

    filters: list[DashboardFilter] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"expected filters[{index}] to be a mapping")
        field = item.get("field")
        if not isinstance(field, str) or not field.strip():
            raise ValueError(f"expected 'filters[{index}].field' to be a non-empty string")
        values = item.get("values")
        if isinstance(values, list):
            parsed_values = tuple(
                str(value).strip() for value in values if str(value).strip()
            )
            if len(parsed_values) != len(values):
                raise ValueError(
                    f"expected 'filters[{index}].values' to contain only non-empty values"
                )
            filters.append(
                DashboardFilter(
                    field=field.strip(),
                    values=tuple(dict.fromkeys(parsed_values)),
                )
            )
            continue
        if isinstance(values, str):
            source_match = _FILTER_SOURCE_RE.match(values.strip())
            if source_match is None:
                raise ValueError(
                    f"expected 'filters[{index}].values' to be a list or source(chart, field)"
                )
            filters.append(
                DashboardFilter(
                    field=field.strip(),
                    source_chart=source_match.group("chart"),
                    source_field=source_match.group("field"),
                )
            )
            continue
        raise ValueError(
            f"expected 'filters[{index}].values' to be a list or source(chart, field)"
        )
    return tuple(filters)


def _parse_section_items(raw: dict[object, object], section_index: int) -> tuple[DashboardItem, ...]:
    items: list[DashboardItem] = []

    section_items = raw.get("items")
    if section_items is not None:
        if not isinstance(section_items, list):
            raise ValueError(f"expected sections[{section_index}].items to be a list")
        items.extend(
            _parse_dashboard_item(item, f"sections[{section_index}].items[{item_index}]")
            for item_index, item in enumerate(section_items, start=1)
        )

    charts = raw.get("charts")
    if charts is not None:
        if not isinstance(charts, list):
            raise ValueError(f"expected sections[{section_index}].charts to be a list")
        items.extend(
            _parse_chart_item(chart, f"sections[{section_index}].charts[{chart_index}]")
            for chart_index, chart in enumerate(charts, start=1)
        )

    if not items:
        raise ValueError(f"expected section {section_index} to contain items or charts")
    return tuple(items)


def _parse_dashboard_item(raw: object, label: str) -> DashboardItem:
    if isinstance(raw, str):
        return DashboardItem(kind="chart", chart=raw)
    if not isinstance(raw, dict):
        raise ValueError(f"expected {label} to be a chart name or mapping")

    if "chart" in raw:
        return _parse_chart_item(raw, label)
    if "component" in raw:
        return _parse_component_item(raw, label)
    if "markdown" in raw:
        return _parse_markdown_item(raw, label)
    if "metric" in raw:
        return _parse_metric_item(raw, label)
    raise ValueError(
        f"expected {label} to define chart, component, markdown, or metric"
    )


def _parse_chart_item(raw: object, label: str) -> DashboardItem:
    if isinstance(raw, str):
        if not raw:
            raise ValueError(f"expected {label} to be a non-empty chart name")
        return DashboardItem(kind="chart", chart=raw)
    if not isinstance(raw, dict):
        raise ValueError(f"expected {label} to be a chart name or mapping")

    chart = raw.get("chart")
    if isinstance(chart, dict):
        name = chart.get("name")
        title = _optional_string(chart.get("title"), f"{label}.chart.title")
        width = _optional_positive_int(chart.get("width"), f"{label}.chart.width")
    else:
        name = chart
        title = _optional_string(raw.get("title"), f"{label}.title")
        width = _optional_positive_int(raw.get("width"), f"{label}.width")
    if not isinstance(name, str) or not name:
        raise ValueError(f"expected {label}.chart to be a non-empty chart name")
    return DashboardItem(kind="chart", chart=name, title=title, width=width)


def _parse_markdown_item(raw: dict[object, object], label: str) -> DashboardItem:
    markdown = raw.get("markdown")
    if isinstance(markdown, str):
        title = _optional_string(raw.get("title"), f"{label}.title")
        text = markdown
    elif isinstance(markdown, dict):
        title = _optional_string(markdown.get("title"), f"{label}.markdown.title")
        text = markdown.get("text")
    else:
        raise ValueError(f"expected {label}.markdown to be a string or mapping")
    if not isinstance(text, str) or not text:
        raise ValueError(f"expected {label}.markdown.text to be a non-empty string")
    return DashboardItem(kind="markdown", title=title, text=text)


def _parse_component_item(raw: dict[object, object], label: str) -> DashboardItem:
    component = raw.get("component")
    if not isinstance(component, str) or not component:
        raise ValueError(f"expected {label}.component to be a non-empty expression")
    return DashboardItem(
        kind="component",
        component=component,
        width=_optional_positive_int(raw.get("width"), f"{label}.width"),
    )


def _parse_metric_item(raw: dict[object, object], label: str) -> DashboardItem:
    metric = raw.get("metric")
    if not isinstance(metric, dict):
        raise ValueError(f"expected {label}.metric to be a mapping")
    label_value = metric.get("label")
    value = metric.get("value")
    if not isinstance(label_value, str) or not label_value:
        raise ValueError(f"expected {label}.metric.label to be a non-empty string")
    if not isinstance(value, str) or not value:
        raise ValueError(f"expected {label}.metric.value to be a non-empty string")
    return DashboardItem(
        kind="metric",
        label=label_value,
        value=value,
        note=_optional_string(metric.get("note"), f"{label}.metric.note"),
        width=_optional_positive_int(metric.get("width"), f"{label}.metric.width"),
    )


def _optional_string(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"expected '{label}' to be a string")
    return value


def _optional_positive_int(value: object, label: str) -> int | None:
    if value is None:
        return None
    if not _is_positive_int(value):
        raise ValueError(f"expected '{label}' to be a positive integer")
    return value


def _parse_columns(value: object, label: str) -> tuple[int | None, tuple[str, ...]]:
    if value is None:
        return None, ()
    if isinstance(value, int):
        if not _is_positive_int(value):
            raise ValueError(f"expected '{label}' to be a positive integer")
        return value, ()

    tracks = _parse_column_tracks(value, label)
    if not tracks:
        raise ValueError(f"expected '{label}' to define at least one column")
    return len(tracks), tuple(tracks)


def _parse_column_tracks(value: object, label: str) -> list[str]:
    if isinstance(value, str):
        raw_tracks = _split_column_tracks(value)
    elif isinstance(value, list):
        raw_tracks = value
    else:
        raise ValueError(
            f"expected '{label}' to be a positive integer, string, or list"
        )

    tracks: list[str] = []
    for index, raw_track in enumerate(raw_tracks, start=1):
        tracks.append(_normalise_column_track(raw_track, f"{label}[{index}]"))
    return tracks


def _split_column_tracks(value: str) -> list[str]:
    if not value.strip():
        return []
    separator = "," if "," in value else None
    return [track.strip() for track in value.split(separator) if track.strip()]


def _normalise_column_track(value: object, label: str) -> str:
    if isinstance(value, int):
        if not _is_positive_int(value):
            raise ValueError(f"expected '{label}' to be a positive column weight")
        return f"{value}fr"
    if not isinstance(value, str):
        raise ValueError(f"expected '{label}' to be a column width string")

    track = value.strip()
    if track == "auto":
        return track

    match = _COLUMN_TRACK_RE.match(track)
    if match is None:
        raise ValueError(
            f"expected '{label}' to use %, fr, px, rem, em, ch, vw, vh, or auto"
        )

    number = float(match.group("number"))
    if number <= 0:
        raise ValueError(f"expected '{label}' to be greater than zero")

    normalized_number = _normalise_number_text(match.group("number"))
    unit = match.group("unit")
    if unit == "%":
        return f"{normalized_number}fr"
    return f"{normalized_number}{unit}"


def _normalise_number_text(value: str) -> str:
    if "." not in value:
        return value
    return value.rstrip("0").rstrip(".")


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _validate_dashboard_schema(raw: dict[object, object], path: Path) -> None:
    try:
        json_text = json.dumps(raw)
    except TypeError as exc:
        raise ValueError("dashboard YAML contains unsupported values") from exc

    try:
        _core.validate_dashboard_json(json_text, path.as_posix())
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
