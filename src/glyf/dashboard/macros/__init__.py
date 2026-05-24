"""Built-in dashboard macro namespaces."""

from glyf.dashboard.macros.registry import (
    DashboardMacroError,
    DashboardMacroRegistry,
    resolve_dashboard_components,
)

__all__ = [
    "DashboardMacroError",
    "DashboardMacroRegistry",
    "resolve_dashboard_components",
]
