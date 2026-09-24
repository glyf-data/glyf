from __future__ import annotations

from glyf.dashboard import components
from glyf.dashboard.components import ComponentSpec


def message(
    value: object,
    *,
    title: object | None = None,
    tone: str = "info",
    metric: object | None = None,
    note: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return components.alert(
        value, title=title, tone=tone, metric=metric, note=note, width=width
    )


def info(
    value: object,
    title: object | None = None,
    *,
    metric: object | None = None,
    note: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return message(
        value, title=title, tone="info", metric=metric, note=note, width=width
    )


def success(
    value: object,
    title: object | None = None,
    *,
    metric: object | None = None,
    note: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return message(
        value, title=title, tone="success", metric=metric, note=note, width=width
    )


def warning(
    value: object,
    title: object | None = None,
    *,
    metric: object | None = None,
    note: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return message(
        value, title=title, tone="warning", metric=metric, note=note, width=width
    )


def error(
    value: object,
    title: object | None = None,
    *,
    metric: object | None = None,
    note: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return message(
        value, title=title, tone="error", metric=metric, note=note, width=width
    )
