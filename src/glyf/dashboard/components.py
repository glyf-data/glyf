from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


ALLOWED_COMPONENT_KINDS = {"alert", "badge", "label_value", "link", "list", "text"}
ALLOWED_TONES = {"neutral", "info", "success", "warning", "error"}


class ComponentError(ValueError):
    """Raised when a dashboard macro returns an invalid component."""


@dataclass(frozen=True)
class ComponentSpec:
    kind: str
    title: str | None = None
    label: str | None = None
    value: str | None = None
    text: str | None = None
    note: str | None = None
    tone: str = "neutral"
    items: tuple[str, ...] = ()
    href: str | None = None
    width: int | None = None


def label_value(
    label: object,
    value: object,
    *,
    note: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return ComponentSpec(
        kind="label_value",
        label=_required_text(label, "label"),
        value=_required_text(value, "value"),
        note=_optional_text(note, "note"),
        width=_optional_positive_int(width, "width"),
    )


def text(
    value: object,
    *,
    title: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return ComponentSpec(
        kind="text",
        title=_optional_text(title, "title"),
        text=_required_text(value, "text"),
        width=_optional_positive_int(width, "width"),
    )


def alert(
    value: object,
    *,
    title: object | None = None,
    tone: str = "info",
    width: int | None = None,
) -> ComponentSpec:
    return ComponentSpec(
        kind="alert",
        title=_optional_text(title, "title"),
        text=_required_text(value, "text"),
        tone=_tone(tone),
        width=_optional_positive_int(width, "width"),
    )


def values_list(
    values: object,
    *,
    title: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    if not isinstance(values, (list, tuple)):
        raise ComponentError("expected 'values' to be a list or tuple")
    if not values:
        raise ComponentError("expected 'values' to contain at least one item")
    return ComponentSpec(
        kind="list",
        title=_optional_text(title, "title"),
        items=tuple(_required_text(item, "values[]") for item in values),
        width=_optional_positive_int(width, "width"),
    )


def badge(
    label: object,
    *,
    tone: str = "neutral",
    width: int | None = None,
) -> ComponentSpec:
    return ComponentSpec(
        kind="badge",
        label=_required_text(label, "label"),
        tone=_tone(tone),
        width=_optional_positive_int(width, "width"),
    )


def link(
    label: object,
    href: object,
    *,
    title: object | None = None,
    width: int | None = None,
) -> ComponentSpec:
    return ComponentSpec(
        kind="link",
        title=_optional_text(title, "title"),
        label=_required_text(label, "label"),
        href=_required_text(href, "href"),
        width=_optional_positive_int(width, "width"),
    )


def ensure_component(value: object, label: str) -> ComponentSpec:
    if isinstance(value, ComponentSpec):
        return _validate_component(value, label)
    if isinstance(value, str):
        return text(value)
    if isinstance(value, Mapping):
        return _validate_component(_component_from_mapping(value, label), label)
    raise ComponentError(f"expected {label} to return a dashboard component")


def _validate_component(component: ComponentSpec, label: str) -> ComponentSpec:
    if component.kind not in ALLOWED_COMPONENT_KINDS:
        allowed = ", ".join(sorted(ALLOWED_COMPONENT_KINDS))
        raise ComponentError(f"expected {label}.kind to be one of: {allowed}")
    _tone(component.tone)
    if component.width is not None:
        _optional_positive_int(component.width, f"{label}.width")
    if component.kind == "label_value":
        _required_text(component.label, f"{label}.label")
        _required_text(component.value, f"{label}.value")
    elif component.kind in {"alert", "text"}:
        _required_text(component.text, f"{label}.text")
    elif component.kind == "list" and not component.items:
        raise ComponentError(f"expected {label}.items to contain at least one item")
    elif component.kind == "badge":
        _required_text(component.label, f"{label}.label")
    elif component.kind == "link":
        _required_text(component.label, f"{label}.label")
        _required_text(component.href, f"{label}.href")
    return component


def _component_from_mapping(value: Mapping[object, object], label: str) -> ComponentSpec:
    kind = value.get("kind")
    if not isinstance(kind, str) or not kind:
        raise ComponentError(f"expected {label}.kind to be a non-empty string")
    raw_items = value.get("items", ())
    if raw_items is None:
        items: tuple[str, ...] = ()
    elif isinstance(raw_items, (list, tuple)):
        items = tuple(_required_text(item, f"{label}.items[]") for item in raw_items)
    else:
        raise ComponentError(f"expected {label}.items to be a list")

    return ComponentSpec(
        kind=kind,
        title=_optional_text(value.get("title"), f"{label}.title"),
        label=_optional_text(value.get("label"), f"{label}.label"),
        value=_optional_text(value.get("value"), f"{label}.value"),
        text=_optional_text(value.get("text"), f"{label}.text"),
        note=_optional_text(value.get("note"), f"{label}.note"),
        tone=_tone(value.get("tone", "neutral")),
        items=items,
        href=_optional_text(value.get("href"), f"{label}.href"),
        width=_optional_positive_int(value.get("width"), f"{label}.width"),
    )


def _required_text(value: object, label: str) -> str:
    if value is None:
        raise ComponentError(f"expected '{label}' to be provided")
    text_value = str(value)
    if not text_value:
        raise ComponentError(f"expected '{label}' to be non-empty")
    return text_value


def _optional_text(value: object | None, label: str) -> str | None:
    if value is None:
        return None
    text_value = str(value)
    if not text_value:
        raise ComponentError(f"expected '{label}' to be non-empty")
    return text_value


def _tone(value: object) -> str:
    if not isinstance(value, str) or value not in ALLOWED_TONES:
        allowed = ", ".join(sorted(ALLOWED_TONES))
        raise ComponentError(f"expected 'tone' to be one of: {allowed}")
    return value


def _optional_positive_int(value: object | None, label: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ComponentError(f"expected '{label}' to be a positive integer")
    return value
