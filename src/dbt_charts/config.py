from dataclasses import dataclass
from pathlib import Path

import yaml


class ConfigError(ValueError):
    """Raised when dbt_charts.yml cannot be loaded."""


@dataclass(frozen=True)
class RenderConfig:
    formats: tuple[str, ...] = ("svg", "png")
    default_width: int = 800
    default_height: int = 400


@dataclass(frozen=True)
class DashboardConfig:
    theme: str = "light"
    embed_charts: bool = True
    show_compiled_sql: bool = True


@dataclass(frozen=True)
class DbtChartsConfig:
    visualisations_path: Path = Path("visualisations")
    dashboards_path: Path = Path("dashboards")
    output_path: Path = Path("target/ggsql")
    compiled_path: Path = Path("target/ggsql/compiled")
    charts_path: Path = Path("target/ggsql/charts")
    dashboards_output_path: Path = Path("target/ggsql/dashboards")
    site_path: Path = Path("target/ggsql/site")
    render: RenderConfig = RenderConfig()
    dashboard: DashboardConfig = DashboardConfig()


def load_config(project_root: Path, config_path: Path | None = None) -> DbtChartsConfig:
    root = project_root.expanduser().resolve()
    path = _resolve_config_path(root, config_path)
    if path is None:
        return DbtChartsConfig()

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in config file: {path}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read config file: {path}") from exc

    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError("Invalid config: expected a YAML mapping")

    return DbtChartsConfig(
        visualisations_path=_path_value(raw, "visualisations_path", "visualisations"),
        dashboards_path=_path_value(raw, "dashboards_path", "dashboards"),
        output_path=_path_value(raw, "output_path", "target/ggsql"),
        compiled_path=_path_value(raw, "compiled_path", "target/ggsql/compiled"),
        charts_path=_path_value(raw, "charts_path", "target/ggsql/charts"),
        dashboards_output_path=_path_value(
            raw,
            "dashboards_output_path",
            "target/ggsql/dashboards",
        ),
        site_path=_path_value(raw, "site_path", "target/ggsql/site"),
        render=_render_config(raw.get("render", {})),
        dashboard=_dashboard_config(raw.get("dashboard", {})),
    )


def resolve_project_path(project_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else project_root / path


def _resolve_config_path(root: Path, config_path: Path | None) -> Path | None:
    if config_path is None:
        default_path = root / "dbt_charts.yml"
        return default_path if default_path.exists() else None

    expanded = config_path.expanduser()
    candidates = [expanded]
    if not expanded.is_absolute():
        candidates.append(root / expanded)
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    raise ConfigError(f"Config file does not exist: {config_path}")


def _path_value(raw: dict[object, object], key: str, default: str) -> Path:
    value = raw.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Invalid config: '{key}' must be a non-empty path string")
    return Path(value)


def _render_config(raw: object) -> RenderConfig:
    if not isinstance(raw, dict):
        raise ConfigError("Invalid config: 'render' must be a mapping")

    formats = raw.get("formats", ["svg", "png"])
    if (
        not isinstance(formats, list)
        or not formats
        or not all(isinstance(item, str) for item in formats)
    ):
        raise ConfigError("Invalid config: 'render.formats' must be a list of strings")

    normalized_formats = tuple(item.lower() for item in formats)
    unsupported = sorted(set(normalized_formats) - {"svg", "png"})
    if unsupported:
        joined = ", ".join(unsupported)
        raise ConfigError(f"Invalid config: unsupported render format(s): {joined}")

    return RenderConfig(
        formats=normalized_formats,
        default_width=_positive_int(raw, "default_width", 800),
        default_height=_positive_int(raw, "default_height", 400),
    )


def _dashboard_config(raw: object) -> DashboardConfig:
    if not isinstance(raw, dict):
        raise ConfigError("Invalid config: 'dashboard' must be a mapping")

    theme = raw.get("theme", "light")
    if not isinstance(theme, str) or not theme:
        raise ConfigError("Invalid config: 'dashboard.theme' must be a string")

    return DashboardConfig(
        theme=theme,
        embed_charts=_bool_value(raw, "embed_charts", True),
        show_compiled_sql=_bool_value(raw, "show_compiled_sql", True),
    )


def _positive_int(raw: dict[object, object], key: str, default: int) -> int:
    value = raw.get(key, default)
    if not isinstance(value, int) or value <= 0:
        raise ConfigError(f"Invalid config: 'render.{key}' must be a positive integer")
    return value


def _bool_value(raw: dict[object, object], key: str, default: bool) -> bool:
    value = raw.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"Invalid config: 'dashboard.{key}' must be true or false")
    return value
