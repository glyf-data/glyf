import re
from pathlib import Path

from dbt_ggsql.ggsql.models import GgsqlChart, VisualiseMapping


class GgsqlParseError(ValueError):
    """Raised when a ggsql file cannot be parsed."""


SUPPORTED_CHART_TYPES = {"line", "bar", "scatter", "area", "pie"}
SUPPORTED_CONFIG_KEYS = {"width", "height"}
VISUALISE_PATTERN = re.compile(r"^VISUALISE\s+(.+)$", re.IGNORECASE)
MAPPING_PATTERN = re.compile(
    r"^\s*([A-Za-z_][\w.]*)\s+AS\s+([A-Za-z_][\w]*)\s*$",
    re.IGNORECASE,
)
DRAW_PATTERN = re.compile(r"^DRAW\s+([A-Za-z_][\w-]*)\s*$", re.IGNORECASE)
LABEL_PATTERN = re.compile(
    r"^LABEL\s+([A-Za-z_][\w-]*)\s*=>\s*(?:'([^']*)'|\"([^\"]*)\"|(.+?))\s*$",
    re.IGNORECASE,
)
CONFIG_PATTERN = re.compile(r"^CONFIG\s+([A-Za-z_][\w-]*)\s*=>\s*(.+?)\s*$", re.IGNORECASE)


def parse_ggsql_file(path: Path) -> GgsqlChart:
    text = path.read_text(encoding="utf-8")
    return parse_ggsql(text, path=path, name=path.stem)


def parse_ggsql(text: str, *, path: Path | None = None, name: str = "chart") -> GgsqlChart:
    lines = text.splitlines()
    visualise_index = _find_visualise_index(lines)
    if visualise_index is None:
        raise GgsqlParseError("missing VISUALISE section")

    sql = "\n".join(lines[:visualise_index]).strip()
    if not sql:
        raise GgsqlParseError("missing SQL query section")

    config_lines = [line.strip() for line in lines[visualise_index:] if line.strip()]
    visualise = _parse_visualise(config_lines[0])
    _validate_required_roles(visualise)
    draw_type: str | None = None
    labels: dict[str, str] = {}
    config: dict[str, int] = {}

    for line in config_lines[1:]:
        draw_match = DRAW_PATTERN.match(line)
        if draw_match:
            draw_type = draw_match.group(1).lower()
            if draw_type not in SUPPORTED_CHART_TYPES:
                raise GgsqlParseError(f"unsupported chart type '{draw_type}'")
            continue

        label_match = LABEL_PATTERN.match(line)
        if label_match:
            labels[label_match.group(1)] = _first_group(label_match, 2, 3, 4).strip()
            continue

        config_match = CONFIG_PATTERN.match(line)
        if config_match:
            key = config_match.group(1).lower()
            if key not in SUPPORTED_CONFIG_KEYS:
                raise GgsqlParseError(f"unsupported CONFIG key '{key}'")
            config[key] = _parse_positive_int_config(key, config_match.group(2))
            continue

        raise GgsqlParseError(f"unrecognised ggsql directive: {line}")

    if draw_type is None:
        raise GgsqlParseError("missing DRAW directive")

    return GgsqlChart(
        path=path or Path(name),
        name=name,
        sql=sql,
        visualise=visualise,
        draw_type=draw_type,
        labels=labels,
        config=config,
    )


def _find_visualise_index(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if VISUALISE_PATTERN.match(line.strip()):
            return index
    return None


def _parse_visualise(line: str) -> tuple[VisualiseMapping, ...]:
    match = VISUALISE_PATTERN.match(line)
    if match is None:
        raise GgsqlParseError("missing VISUALISE section")

    mappings: list[VisualiseMapping] = []
    for raw_mapping in match.group(1).split(","):
        mapping_match = MAPPING_PATTERN.match(raw_mapping)
        if mapping_match is None:
            raise GgsqlParseError(f"invalid VISUALISE mapping: {raw_mapping.strip()}")
        mappings.append(
            VisualiseMapping(
                field=mapping_match.group(1),
                role=mapping_match.group(2),
            )
        )

    if not mappings:
        raise GgsqlParseError("VISUALISE requires at least one mapping")
    return tuple(mappings)


def _validate_required_roles(visualise: tuple[VisualiseMapping, ...]) -> None:
    roles = {mapping.role for mapping in visualise}
    if "x" not in roles or "y" not in roles:
        raise GgsqlParseError("VISUALISE requires x and y mappings")


def _first_group(match: re.Match[str], *groups: int) -> str:
    for group in groups:
        value = match.group(group)
        if value is not None:
            return value
    return ""


def _parse_positive_int_config(key: str, raw_value: str) -> int:
    value = raw_value.strip()
    if not value.isdigit():
        raise GgsqlParseError(f"invalid CONFIG {key}: expected a positive integer")
    parsed = int(value)
    if parsed <= 0:
        raise GgsqlParseError(f"invalid CONFIG {key}: expected a positive integer")
    return parsed
