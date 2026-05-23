from __future__ import annotations

from dbt_charts.dashboard import components
from dbt_charts.dashboard.components import ComponentSpec


def message(
    value: object,
    *,
    title: object | None = None,
    tone: str = "info",
    width: int | None = None,
) -> ComponentSpec:
    return components.alert(value, title=title, tone=tone, width=width)


def info(
    value: object,
    title: object | None = None,
    *,
    width: int | None = None,
) -> ComponentSpec:
    return message(value, title=title, tone="info", width=width)


def success(
    value: object,
    title: object | None = None,
    *,
    width: int | None = None,
) -> ComponentSpec:
    return message(value, title=title, tone="success", width=width)


def warning(
    value: object,
    title: object | None = None,
    *,
    width: int | None = None,
) -> ComponentSpec:
    return message(value, title=title, tone="warning", width=width)


def error(
    value: object,
    title: object | None = None,
    *,
    width: int | None = None,
) -> ComponentSpec:
    return message(value, title=title, tone="error", width=width)
