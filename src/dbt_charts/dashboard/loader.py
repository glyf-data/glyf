from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class DashboardLayout:
    kind: str = "grid"
    columns: int | None = None


@dataclass(frozen=True)
class DashboardItem:
    kind: str
    chart: str | None = None
    title: str | None = None
    text: str | None = None
    label: str | None = None
    value: str | None = None
    note: str | None = None
    width: int | None = None


@dataclass(frozen=True)
class DashboardSection:
    title: str | None
    description: str | None
    columns: int | None
    items: tuple[DashboardItem, ...]


@dataclass(frozen=True)
class Dashboard:
    path: Path
    name: str
    title: str
    charts: tuple[str, ...]
    description: str | None = None
    layout: str | None = None
    layout_config: DashboardLayout = DashboardLayout()
    sections: tuple[DashboardSection, ...] = ()

    @property
    def chart_names(self) -> tuple[str, ...]:
        names = list(self.charts)
        for section in self.sections:
            names.extend(item.chart for item in section.items if item.chart is not None)
        return tuple(dict.fromkeys(names))


def load_dashboard(path: Path) -> Dashboard:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError("invalid YAML") from exc

    if not isinstance(raw, dict):
        raise ValueError("expected a YAML mapping")

    name = raw.get("name")
    title = raw.get("title", name)
    description = raw.get("description")
    layout_raw = raw.get("layout")
    charts = raw.get("charts", [])
    sections_raw = raw.get("sections", raw.get("groups", []))

    if not isinstance(name, str) or not name:
        raise ValueError("expected non-empty 'name'")
    if not isinstance(title, str) or not title:
        raise ValueError("expected non-empty 'title'")
    if description is not None and not isinstance(description, str):
        raise ValueError("expected 'description' to be a string")
    if not isinstance(charts, list) or not all(isinstance(item, str) for item in charts):
        raise ValueError("expected 'charts' to be a list of chart names")

    layout_config = _parse_layout(layout_raw)
    sections = _parse_sections(sections_raw)

    return Dashboard(
        path=path,
        name=name,
        title=title,
        description=description,
        layout=layout_config.kind if layout_raw is not None else None,
        layout_config=layout_config,
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
    return DashboardLayout(
        kind=kind,
        columns=_optional_positive_int(raw.get("columns"), "layout.columns"),
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
        columns = _optional_positive_int(item.get("columns"), f"sections[{index}].columns")
        items = _parse_section_items(item, index)
        sections.append(
            DashboardSection(
                title=title,
                description=description,
                columns=columns,
                items=items,
            )
        )
    return tuple(sections)


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
    if "markdown" in raw:
        return _parse_markdown_item(raw, label)
    if "metric" in raw:
        return _parse_metric_item(raw, label)
    raise ValueError(f"expected {label} to define chart, markdown, or metric")


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
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"expected '{label}' to be a positive integer")
    return value
