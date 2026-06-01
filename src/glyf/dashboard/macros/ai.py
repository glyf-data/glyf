from __future__ import annotations

from glyf.dashboard import components
from glyf.dashboard.components import ComponentSpec


def summary(
    value: object,
    *,
    title: object | None = "Overview",
    width: int | None = None,
) -> ComponentSpec:
    return components.text(value, title=title, width=width)


def insight(
    value: object,
    *,
    title: object | None = None,
    tone: str = "info",
    width: int | None = None,
) -> ComponentSpec:
    return components.alert(value, title=title, tone=tone, width=width)


def signal(
    value: object,
    *,
    title: object | None = None,
    tone: str = "info",
    width: int | None = None,
) -> ComponentSpec:
    return insight(value, title=title, tone=tone, width=width)
