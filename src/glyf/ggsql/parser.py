from pathlib import Path

from glyf import _core
from glyf.ggsql.models import GgsqlChart, OrderTiebreak, VisualiseMapping


class GgsqlParseError(ValueError):
    """Raised when a ggsql file cannot be parsed."""


SUPPORTED_CHART_TYPES = {
    "line",
    "bar",
    "scatter",
    "area",
    "pie",
    "histogram",
    "boxplot",
    "heatmap",
    "table",
    "kpi",
}
SUPPORTED_CONFIG_KEYS = {"width", "height"}
SUPPORTED_INTERACTIONS = {"tooltip", "zoom", "legend_filter"}


def parse_ggsql_file(path: Path, *, dialect: str = "generic") -> GgsqlChart:
    text = path.read_text(encoding="utf-8")
    return parse_ggsql(text, path=path, name=path.stem, dialect=dialect)


def parse_ggsql(
    text: str, *, path: Path | None = None, name: str = "chart", dialect: str = "generic"
) -> GgsqlChart:
    """Parse a chart file.

    `dialect` names the warehouse the SQL is written for (`duckdb`, `snowflake`,
    `bigquery`; anything else reads as generic SQL). It only affects how the SQL
    is read for the ORDER BY rule and the syntax warning; the chart block is
    validated the same way whatever the dialect.
    """
    try:
        raw = _core.parse_ggsql(text, name, path.as_posix() if path else None, dialect)
    except ValueError as exc:
        raise GgsqlParseError(str(exc)) from exc
    return _chart_from_core(raw)


def order_tiebreak(sql: str, *, dialect: str = "generic") -> OrderTiebreak:
    """How to settle the ties a compiled query's outer ORDER BY leaves.

    The Rust core appends the query's other output columns to that ORDER BY,
    after the author's keys, so the order asked for holds and rows it calls
    equal come back the same way every build. A query without an ORDER BY
    gets an empty answer: glyf orders those rows itself.
    """
    raw = _core.order_tiebreak(sql, dialect)
    return OrderTiebreak(
        sql=_optional_str(raw, "sql"),
        added=tuple(str(value) for value in _required_list(raw, "added")),
        keys=tuple(str(value) for value in _required_list(raw, "keys")),
        reason=_optional_str(raw, "reason"),
        limited=bool(raw.get("limited", False)),
    )


def _chart_from_core(raw: dict[str, object]) -> GgsqlChart:
    return GgsqlChart(
        path=Path(_required_str(raw, "path")),
        name=_required_str(raw, "name"),
        sql=_required_str(raw, "sql"),
        visualise=tuple(
            VisualiseMapping(
                field=_required_str(mapping, "field"),
                role=_required_str(mapping, "role"),
            )
            for mapping in _required_list(raw, "visualise")
            if isinstance(mapping, dict)
        ),
        draw_type=_required_str(raw, "draw_type"),
        labels={
            str(key): str(value)
            for key, value in _required_dict(raw, "labels").items()
        },
        config={
            str(key): int(value)
            for key, value in _required_dict(raw, "config").items()
        },
        interactions=tuple(str(value) for value in _required_list(raw, "interactions")),
        has_order_by=bool(raw.get("has_order_by", False)),
        sql_warning=_optional_str(raw, "sql_warning"),
        sql_columns=tuple(str(value) for value in _required_list(raw, "sql_columns")),
        sql_selects_star=bool(raw.get("sql_selects_star", False)),
    )


def _required_str(raw: dict[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise GgsqlParseError(f"Rust core returned invalid chart field '{key}'")
    return value


def _required_list(raw: dict[str, object], key: str) -> list[object]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise GgsqlParseError(f"Rust core returned invalid chart field '{key}'")
    return value


def _required_dict(raw: dict[str, object], key: str) -> dict[object, object]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise GgsqlParseError(f"Rust core returned invalid chart field '{key}'")
    return value


def _optional_str(raw: dict[str, object], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise GgsqlParseError(f"core returned a non-string {key}")
    return value
