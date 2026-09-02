from dataclasses import dataclass, replace
from pathlib import Path

import yaml


class ConfigError(ValueError):
    """Raised when glyf.yml cannot be loaded."""


EXECUTION_MODES = frozenset({"full", "validate"})

ROW_DATA_MODES = frozenset({"include", "minimal", "exclude"})

PII_POLICIES = frozenset({"deny", "redact"})

REDACTION_METHODS = frozenset({"mask", "hash"})


@dataclass(frozen=True)
class RenderConfig:
    formats: tuple[str, ...] = ("svg", "png")
    default_width: int = 800
    default_height: int = 400
    renderer: str = "altair"


@dataclass(frozen=True)
class ExecutionConfig:
    backend: str = "duckdb"
    # Used by the `dbt` backend, which reads the project's profiles.yml.
    target: str | None = None
    profiles_dir: Path | None = None
    # `validate` runs each query with `limit 0` and draws nothing: enough to
    # prove the SQL still runs and binds its columns, which is what CI needs.
    mode: str = "full"
    # A guardrail against an unbounded chart query. Unset means no limit.
    max_rows: int | None = None


@dataclass(frozen=True)
class DashboardConfig:
    theme: str = "light"
    embed_charts: bool = True
    show_compiled_sql: bool = True


@dataclass(frozen=True)
class ExportConfig:
    # `minimal` publishes only the columns each chart encodes: Vega specs are
    # pruned to them and SVG accessibility labels keep field names, not values.
    # `exclude` publishes pictures instead of data: PNG only, no Vega specs, no
    # compiled SQL, no values resolved out of a chart's rows.
    row_data: str = "include"

    @property
    def excludes_row_data(self) -> bool:
        return self.row_data == "exclude"

    @property
    def prunes_row_data(self) -> bool:
        return self.row_data == "minimal"


@dataclass(frozen=True)
class PrivacyConfig:
    # Columns to treat as PII on top of what the dbt manifest tags: aliases
    # and expressions dbt does not model.
    pii_columns: tuple[str, ...] = ()
    # What a build does when a chart's result carries a PII column. `deny`
    # fails it; `redact` rewrites the column's values before anything reads
    # them.
    on_pii: str = "deny"
    # `mask` keeps a hint of the value (`j***@acme.com`); `hash` keeps only
    # its distinctness, for grouping by a sensitive key.
    redaction: str = "mask"
    # Look at the values of unclassified columns for things that read like
    # emails, phone numbers, card numbers or SSNs. Fuzzy, so it warns.
    scan: bool = True
    # ...unless strict, when a warning fails the build instead.
    strict: bool = False


@dataclass(frozen=True)
class GlyfConfig:
    visualisations_path: Path = Path("visualisations")
    dashboards_path: Path = Path("dashboards")
    output_path: Path = Path("target/glyf")
    compiled_path: Path = Path("target/glyf/compiled")
    charts_path: Path = Path("target/glyf/charts")
    dashboards_output_path: Path = Path("target/glyf/dashboards")
    site_path: Path = Path("target/glyf/site")
    execution: ExecutionConfig = ExecutionConfig()
    render: RenderConfig = RenderConfig()
    dashboard: DashboardConfig = DashboardConfig()
    export: ExportConfig = ExportConfig()
    privacy: PrivacyConfig = PrivacyConfig()

    def with_output_dir(self, output_dir: Path) -> "GlyfConfig":
        """The same config writing everything under `output_dir`.

        The derived directories move with it, overriding `compiled_path`,
        `charts_path`, `dashboards_output_path` and `site_path` whatever
        `glyf.yml` set them to: a run told where to write should not scatter
        half its output somewhere else.
        """
        root = Path(output_dir)
        return replace(
            self,
            output_path=root,
            compiled_path=root / "compiled",
            charts_path=root / "charts",
            dashboards_output_path=root / "dashboards",
            site_path=root / "site",
        )


def load_config(project_root: Path, config_path: Path | None = None) -> GlyfConfig:
    root = project_root.expanduser().resolve()
    path = _resolve_config_path(root, config_path)
    if path is None:
        return GlyfConfig()

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

    return GlyfConfig(
        visualisations_path=_path_value(raw, "visualisations_path", "visualisations"),
        dashboards_path=_path_value(raw, "dashboards_path", "dashboards"),
        output_path=_path_value(raw, "output_path", "target/glyf"),
        compiled_path=_path_value(raw, "compiled_path", "target/glyf/compiled"),
        charts_path=_path_value(raw, "charts_path", "target/glyf/charts"),
        dashboards_output_path=_path_value(
            raw,
            "dashboards_output_path",
            "target/glyf/dashboards",
        ),
        site_path=_path_value(raw, "site_path", "target/glyf/site"),
        execution=_execution_config(raw.get("execution", {})),
        render=_render_config(raw.get("render", {})),
        dashboard=_dashboard_config(raw.get("dashboard", {})),
        export=_export_config(raw.get("export", {})),
        privacy=_privacy_config(raw.get("privacy", {})),
    )


def apply_run_overrides(
    config: GlyfConfig,
    *,
    target: str | None = None,
    output_dir: Path | None = None,
) -> GlyfConfig:
    """Config with a run's command-line overrides applied."""
    if output_dir is not None:
        config = config.with_output_dir(output_dir)
    if target is not None:
        if config.execution.backend != "dbt":
            raise ConfigError(
                "Invalid config: --target names a dbt profile target, which needs "
                f"execution.backend: dbt; this project uses "
                f"'{config.execution.backend}'. Without it the target would be "
                "ignored and the build would run as the same identity."
            )
        config = replace(config, execution=replace(config.execution, target=target))
    return config


def resolve_project_path(project_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else project_root / path


def _resolve_config_path(root: Path, config_path: Path | None) -> Path | None:
    if config_path is None:
        default_path = root / "glyf.yml"
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
        renderer=_string_value(raw, "renderer", "altair"),
    )


def _execution_config(raw: object) -> ExecutionConfig:
    if not isinstance(raw, dict):
        raise ConfigError("Invalid config: 'execution' must be a mapping")

    mode = _string_value(raw, "mode", "full")
    if mode not in EXECUTION_MODES:
        allowed = ", ".join(sorted(EXECUTION_MODES))
        raise ConfigError(f"Invalid config: 'execution.mode' must be one of {allowed}")

    return ExecutionConfig(
        backend=_string_value(raw, "backend", "duckdb"),
        target=_optional_string(raw, "target"),
        profiles_dir=_optional_path(raw, "profiles_dir"),
        mode=mode,
        max_rows=_optional_positive_int(raw, "max_rows"),
    )


def _export_config(raw: object) -> ExportConfig:
    if not isinstance(raw, dict):
        raise ConfigError("Invalid config: 'export' must be a mapping")

    row_data = _string_value(raw, "row_data", "include")
    if row_data not in ROW_DATA_MODES:
        allowed = ", ".join(sorted(ROW_DATA_MODES))
        raise ConfigError(
            f"Invalid config: 'export.row_data' must be one of {allowed}"
        )
    return ExportConfig(row_data=row_data)


def _privacy_config(raw: object) -> PrivacyConfig:
    if not isinstance(raw, dict):
        raise ConfigError("Invalid config: 'privacy' must be a mapping")

    columns = raw.get("pii_columns", [])
    if columns is None:
        columns = []
    if not isinstance(columns, list) or not all(
        isinstance(item, str) and item.strip() for item in columns
    ):
        raise ConfigError(
            "Invalid config: 'privacy.pii_columns' must be a list of column names"
        )
    on_pii = _string_value(raw, "on_pii", "deny")
    if on_pii not in PII_POLICIES:
        allowed = ", ".join(sorted(PII_POLICIES))
        raise ConfigError(f"Invalid config: 'privacy.on_pii' must be one of {allowed}")
    redaction = _string_value(raw, "redaction", "mask")
    if redaction not in REDACTION_METHODS:
        allowed = ", ".join(sorted(REDACTION_METHODS))
        raise ConfigError(
            f"Invalid config: 'privacy.redaction' must be one of {allowed}"
        )
    return PrivacyConfig(
        pii_columns=tuple(dict.fromkeys(item.strip() for item in columns)),
        on_pii=on_pii,
        redaction=redaction,
        scan=_bool_value(raw, "scan", True),
        strict=_bool_value(raw, "strict", False),
    )


def _optional_positive_int(raw: dict[object, object], key: str) -> int | None:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ConfigError(f"Invalid config: '{key}' must be a positive integer")
    return value


def _optional_string(raw: dict[object, object], key: str) -> str | None:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Invalid config: '{key}' must be a non-empty string")
    return value


def _optional_path(raw: dict[object, object], key: str) -> Path | None:
    value = _optional_string(raw, key)
    return Path(value).expanduser() if value is not None else None


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


def _string_value(raw: dict[object, object], key: str, default: str) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Invalid config: 'render.{key}' must be a non-empty string")
    return value.strip()
