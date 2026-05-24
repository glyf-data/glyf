from __future__ import annotations

from glyf.dashboard import components
from glyf.dashboard.components import ComponentSpec


def label_value(
    label: object,
    value: object,
    *,
    note: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return components.label_value(label, value, note=note, width=width)


def text(
    value: object,
    *,
    title: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return components.text(value, title=title, width=width)


def list(
    values: object,
    *,
    title: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return components.values_list(values, title=title, width=width)


def listofvalues(
    values: object,
    *,
    title: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return components.values_list(values, title=title, width=width)


def badge(
    label: object,
    *,
    tone: str = "neutral",
    width: int | None = None,
) -> ComponentSpec:
    return components.badge(label, tone=tone, width=width)


def link(
    label: object,
    href: object,
    *,
    title: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return components.link(label, href, title=title, width=width)
