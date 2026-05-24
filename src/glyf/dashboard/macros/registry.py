from __future__ import annotations

import hashlib
import inspect
import importlib.util
import re
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Callable

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

from glyf.dashboard import components
from glyf.dashboard.components import ComponentError, ComponentSpec
from glyf.dashboard.loader import Dashboard, DashboardItem, DashboardSection
from glyf.dashboard.macros import alert, time, ui


_EXPRESSION_RE = re.compile(r"^\s*\{\{\s*(?P<expression>.*?)\s*\}\}\s*$", re.S)
_RESERVED_NAMES = {"ui", "alert", "time"}


class DashboardMacroError(ValueError):
    """Raised when dashboard macro loading or evaluation fails."""


class DashboardMacroRegistry:
    def __init__(self, context: dict[str, object]) -> None:
        self._context = context
        self._environment = SandboxedEnvironment(undefined=StrictUndefined)

    @classmethod
    def from_project(cls, dashboards_dir: Path | None) -> "DashboardMacroRegistry":
        context = _builtin_context()
        if dashboards_dir is not None:
            macros_path = dashboards_dir / "macros.py"
            if macros_path.exists():
                context.update(_load_project_macros(macros_path))
        return cls(context)

    def evaluate_component(self, raw_expression: str, label: str) -> ComponentSpec:
        result = self.evaluate(raw_expression, label)
        try:
            return components.ensure_component(result, label)
        except ComponentError as exc:
            raise DashboardMacroError(f"{label}: {exc}") from exc

    def evaluate(self, raw_expression: str, label: str) -> object:
        match = _EXPRESSION_RE.match(raw_expression)
        if match is None:
            raise DashboardMacroError(
                f"{label}: expected a Jinja expression like "
                "'{{ ui.label_value(...) }}'"
            )

        expression = match.group("expression").strip()
        if not expression:
            raise DashboardMacroError(f"{label}: expected a non-empty expression")

        try:
            compiled = self._environment.compile_expression(
                expression,
                undefined_to_none=False,
            )
            return compiled(**self._context)
        except Exception as exc:
            raise DashboardMacroError(f"{label}: {exc}") from exc


def resolve_dashboard_components(
    dashboard: Dashboard,
    registry: DashboardMacroRegistry,
) -> Dashboard:
    summary_components = tuple(
        registry.evaluate_component(expression, f"summary[{index}]")
        for index, expression in enumerate(dashboard.summary, start=1)
    )
    sections = tuple(
        _resolve_section(section, section_index, registry)
        for section_index, section in enumerate(dashboard.sections, start=1)
    )
    return replace(
        dashboard,
        summary_components=summary_components,
        sections=sections,
    )


def _resolve_section(
    section: DashboardSection,
    section_index: int,
    registry: DashboardMacroRegistry,
) -> DashboardSection:
    items = tuple(
        _resolve_item(item, f"sections[{section_index}].items[{item_index}]", registry)
        for item_index, item in enumerate(section.items, start=1)
    )
    return replace(section, items=items)


def _resolve_item(
    item: DashboardItem,
    label: str,
    registry: DashboardMacroRegistry,
) -> DashboardItem:
    if item.kind != "component" or item.component is None:
        return item

    component = registry.evaluate_component(item.component, f"{label}.component")
    if item.width is not None and component.width is None:
        component = replace(component, width=item.width)
    return replace(item, component_spec=component)


def _builtin_context() -> dict[str, object]:
    ui_namespace = {
        "badge": ui.badge,
        "label_value": ui.label_value,
        "link": ui.link,
        "list": ui.list,
        "listofvalues": ui.listofvalues,
        "text": ui.text,
    }
    alert_namespace = {
        "error": alert.error,
        "info": alert.info,
        "message": alert.message,
        "success": alert.success,
        "warning": alert.warning,
    }
    time_namespace = {"now": time.now}

    return {
        "ui": ui_namespace,
        "alert": alert_namespace,
        "time": time_namespace,
        "badge": ui.badge,
        "echo": alert.info,
        "label_value": ui.label_value,
        "link": ui.link,
        "listofvalues": ui.listofvalues,
        "now": time.now,
        "text": ui.text,
    }


def _load_project_macros(macros_path: Path) -> dict[str, Callable[..., object]]:
    module = _load_module(macros_path)
    macros = {
        name: value
        for name, value in vars(module).items()
        if not name.startswith("_")
        and inspect.isfunction(value)
        and value.__module__ == module.__name__
    }
    reserved = sorted(set(macros) & _RESERVED_NAMES)
    if reserved:
        joined = ", ".join(reserved)
        raise DashboardMacroError(
            f"{macros_path}: custom macros cannot replace reserved namespace(s): "
            f"{joined}"
        )
    return macros


def _load_module(macros_path: Path) -> ModuleType:
    module_name = "glyf_project_macros_" + hashlib.sha1(
        str(macros_path.resolve()).encode("utf-8")
    ).hexdigest()
    spec = importlib.util.spec_from_file_location(module_name, macros_path)
    if spec is None or spec.loader is None:
        raise DashboardMacroError(f"{macros_path}: could not load project macros")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise DashboardMacroError(f"{macros_path}: {exc}") from exc
    return module
