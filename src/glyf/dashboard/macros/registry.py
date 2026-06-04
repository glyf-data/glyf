from __future__ import annotations

import hashlib
import inspect
import importlib.util
from functools import wraps
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
from glyf.dashboard.macros.context import MacroContext
from glyf.dashboard.macros import ai, alert, time, ui


_EXPRESSION_RE = re.compile(r"^\s*\{\{\s*(?P<expression>.*?)\s*\}\}\s*$", re.S)
_RESERVED_NAMES = {
    "ai",
    "alert",
    "alert_threshold",
    "distinct_values",
    "latest_value",
    "source",
    "time",
    "ui",
}


class DashboardMacroError(ValueError):
    """Raised when dashboard macro loading or evaluation fails."""


class DashboardMacroRegistry:
    def __init__(self, context: dict[str, object]) -> None:
        self._context = context
        self._environment = SandboxedEnvironment(undefined=StrictUndefined)

    @classmethod
    def from_project(
        cls,
        dashboards_dir: Path | None,
        macro_context: MacroContext | None = None,
    ) -> "DashboardMacroRegistry":
        context = _builtin_context(macro_context)
        if dashboards_dir is not None:
            macros_path = dashboards_dir / "macros.py"
            if macros_path.exists():
                context.update(_load_project_macros(macros_path, macro_context))
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


def _builtin_context(macro_context: MacroContext | None) -> dict[str, object]:
    source = _bind_context_method(macro_context, "source")
    distinct_values = _bind_context_method(macro_context, "distinct_values")
    latest_value = _bind_context_method(macro_context, "latest_value")
    alert_threshold = _alert_threshold_factory(macro_context)

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
        "threshold": alert_threshold,
        "warning": alert.warning,
    }
    time_namespace = {"now": time.now}
    ai_namespace = {
        "insight": ai.insight,
        "signal": ai.signal,
        "summary": ai.summary,
    }

    return {
        "ai": ai_namespace,
        "ui": ui_namespace,
        "alert": alert_namespace,
        "time": time_namespace,
        "badge": ui.badge,
        "echo": alert.info,
        "label_value": ui.label_value,
        "link": ui.link,
        "alert_threshold": alert_threshold,
        "distinct_values": distinct_values,
        "latest_value": latest_value,
        "listofvalues": ui.listofvalues,
        "now": time.now,
        "source": source,
        "text": ui.text,
    }


def _load_project_macros(
    macros_path: Path,
    macro_context: MacroContext | None,
) -> dict[str, Callable[..., object]]:
    module = _load_module(macros_path)
    macros = {
        name: _bind_project_macro_context(value, macro_context)
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


def _bind_project_macro_context(
    function: Callable[..., object],
    macro_context: MacroContext | None,
) -> Callable[..., object]:
    if macro_context is None:
        return function
    parameters = tuple(inspect.signature(function).parameters.values())
    if not parameters or parameters[0].name != "ctx":
        return function

    @wraps(function)
    def wrapped(*args: object, **kwargs: object) -> object:
        return function(macro_context, *args, **kwargs)

    return wrapped


def _bind_context_method(
    macro_context: MacroContext | None,
    method_name: str,
) -> Callable[..., object]:
    if macro_context is None:
        def unavailable(*_: object, **__: object) -> object:
            raise DashboardMacroError(
                f"'{method_name}' is only available while rendering dashboards"
            )

        return unavailable
    return getattr(macro_context, method_name)


def _alert_threshold_factory(
    macro_context: MacroContext | None,
) -> Callable[..., ComponentSpec]:
    def alert_threshold(
        chart: str,
        field: str,
        value: object,
        *,
        op: str = "lt",
        title: str | None = None,
        success_text: str | None = None,
        alert_text: str | None = None,
        width: int | None = None,
    ) -> ComponentSpec:
        if macro_context is None:
            raise DashboardMacroError(
                "'alert.threshold' is only available while rendering dashboards"
            )
        operator = _normalise_operator(op)
        actual_value = macro_context.latest_value(chart, field)
        actual_number = _coerce_number(actual_value, f"{chart}.{field}")
        threshold_number = _coerce_number(value, "threshold")
        passed = _compare(actual_number, threshold_number, operator)
        title_value = title or f"{field.replace('_', ' ').title()} threshold"
        rendered_value = _format_number(actual_number)
        rendered_threshold = _format_number(threshold_number)
        if passed:
            message = success_text or (
                f"{field.replace('_', ' ').title()} is {rendered_value}. "
                f"Threshold satisfied ({operator} {rendered_threshold})."
            )
            return alert.success(message, title_value, width=width)
        message = alert_text or (
            f"{field.replace('_', ' ').title()} is {rendered_value}. "
            f"Threshold breached ({operator} {rendered_threshold})."
        )
        return alert.warning(message, title_value, width=width)

    return alert_threshold


def _normalise_operator(value: str) -> str:
    operators = {"lt", "lte", "gt", "gte", "eq", "neq"}
    operator = str(value).strip().lower()
    if operator not in operators:
        joined = ", ".join(sorted(operators))
        raise DashboardMacroError(f"expected 'op' to be one of: {joined}")
    return operator


def _coerce_number(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise DashboardMacroError(f"expected {label} to be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise DashboardMacroError(f"expected {label} to be numeric") from exc


def _compare(actual: float, threshold: float, operator: str) -> bool:
    if operator == "lt":
        return actual < threshold
    if operator == "lte":
        return actual <= threshold
    if operator == "gt":
        return actual > threshold
    if operator == "gte":
        return actual >= threshold
    if operator == "eq":
        return actual == threshold
    return actual != threshold


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")
