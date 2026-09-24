"""A kpi tile: one number, and how it compares.

The second draw type glyf does not draw. A kpi is the single row its query
returns: the `value` column as a headline, and when a `compare` column is
mapped, the difference and its direction. The artifact is an HTML fragment
the dashboard shows as a tile, beside the data JSON that holds the row.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from glyf.execution.result import QueryResult
from glyf.ggsql.models import GgsqlChart
from glyf.ggsql.renderer import ChartRenderError, missing_columns

_TEMPLATES = Path(__file__).parent / "templates"


@dataclass(frozen=True)
class Comparison:
    """How the value stands against the one it is compared with."""

    compare_text: str
    # `up`, `down` or `flat`; None when the two cannot be subtracted.
    direction: str | None
    delta_text: str | None
    percent_text: str | None


@dataclass(frozen=True)
class KpiTile:
    value_text: str
    comparison: Comparison | None


def render_kpi(chart: GgsqlChart, data: QueryResult, path: Path) -> None:
    """Write the tile's HTML fragment from its one row."""
    missing = missing_columns(chart, data.columns)
    if missing:
        joined = ", ".join(f"'{field}'" for field in missing)
        raise ChartRenderError(f"query result missing kpi column {joined}")
    if len(data) != 1:
        raise ChartRenderError(
            f"the query returned {len(data)} rows and a kpi shows one; "
            "aggregate the query so it returns exactly one row"
        )
    tile = build_tile(chart, data.rows[0])
    html = _environment().get_template("kpi.html.j2").render(
        name=chart.name,
        tile=tile,
        compare_label=chart.labels.get("compare", "vs previous"),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html.rstrip() + "\n", encoding="utf-8")


def build_tile(chart: GgsqlChart, row: dict[str, object]) -> KpiTile:
    value_field = chart.field_for_role("value")
    compare_field = chart.field_for_role("compare")
    assert value_field is not None
    value = row.get(value_field)
    if compare_field is None:
        return KpiTile(value_text=format_number(value), comparison=None)
    compare = row.get(compare_field)
    return KpiTile(value_text=format_number(value), comparison=_compare(value, compare))


def _compare(value: object, compare: object) -> Comparison | None:
    if compare is None:
        return None
    compare_text = format_number(compare)
    if not (_is_number(value) and _is_number(compare)):
        return Comparison(compare_text, None, None, None)
    delta = value - compare  # type: ignore[operator]
    places = _shared_places(value, compare)
    if places is not None:
        # 89.9 - 92.3 is -2.3999999999999915 in binary floating point; the
        # difference of two numbers is as precise as they are, no more.
        delta = round(delta, places)
    direction = "up" if delta > 0 else "down" if delta < 0 else "flat"
    delta_text = (
        f"{delta:+,.{places}f}"
        if places is not None and isinstance(delta, float)
        else format_number(delta, signed=True)
    )
    # A share of nothing is not a number; the delta alone says what moved.
    percent_text = f"{delta / abs(compare):+.1%}" if compare else None  # type: ignore[operator]
    return Comparison(compare_text, direction, delta_text, percent_text)


def format_number(value: object, *, signed: bool = False) -> str:
    """A headline number reads with thousands separators; anything else as is.

    The table shows values exactly as the warehouse returned them, because a
    row is read against other rows. A kpi is one number read on its own, and
    `2,314,900` is what a person can take in. Precision is untouched.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if _is_number(value):
        return f"{value:+,}" if signed else f"{value:,}"
    return str(value)


def _shared_places(value: object, compare: object) -> int | None:
    """The decimal places the two numbers were written with, the more of the two.

    `None` when either is written in exponent form, which says nothing about
    its places; the delta is then left as it is.
    """
    places = [_places(value), _places(compare)]
    if any(place is None for place in places):
        return None
    return max(place for place in places if place is not None)


def _places(number: object) -> int | None:
    if isinstance(number, int):
        return 0
    text = repr(number)
    if "e" in text or "E" in text or "n" in text:
        return None
    return len(text.split(".", 1)[1]) if "." in text else 0


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(_TEMPLATES),
        autoescape=select_autoescape(("html", "xml", "j2")),
    )
