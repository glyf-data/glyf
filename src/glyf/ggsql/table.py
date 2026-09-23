"""A table chart: the rows, laid out to be read.

A table is the one draw type glyf does not draw. The picture of a table is
its rows, so the artifact is an HTML fragment -- a `<table>` with the listed
columns in order, labels applied to the headers -- that the dashboard inlines
where a chart card would hold an SVG. It carries no script: sorting is the
dashboard page's, once, for every table on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
from jinja2 import Environment, FileSystemLoader, select_autoescape

from glyf.execution.result import QueryResult
from glyf.ggsql.models import GgsqlChart
from glyf.ggsql.renderer import ChartRenderError, missing_columns, table_columns

_TEMPLATES = Path(__file__).parent / "templates"


@dataclass(frozen=True)
class _Column:
    name: str
    label: str
    # `number` or `text`: how the page sorts the column and which way it
    # aligns. Numbers read best right-aligned with the digits lined up.
    type: str


@dataclass(frozen=True)
class _Cell:
    text: str
    numeric: bool
    empty: bool


def render_table(chart: GgsqlChart, data: QueryResult, path: Path) -> None:
    """Write the table's HTML fragment from its rows."""
    columns = table_columns(chart, data.columns)
    missing = missing_columns(chart, data.columns)
    if missing:
        joined = ", ".join(f"'{field}'" for field in missing)
        raise ChartRenderError(f"query result missing table column {joined}")
    if not columns:
        raise ChartRenderError("the query returned no columns to list")

    frame = data.to_arrow()
    specs = [
        _Column(
            name=name,
            label=chart.column_label(name),
            type="number" if _is_numeric(frame.schema.field(name).type) else "text",
        )
        for name in columns
    ]
    rows = [
        [_cell(row.get(spec.name), spec.type == "number") for spec in specs]
        for row in frame.select(list(columns)).to_pylist()
    ]
    html = _environment().get_template("table.html.j2").render(
        name=chart.name,
        columns=specs,
        rows=rows,
        width=chart.width,
        height=chart.height,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html.rstrip() + "\n", encoding="utf-8")


def _cell(value: object, numeric: bool) -> _Cell:
    if value is None:
        return _Cell(text="", numeric=numeric, empty=True)
    if isinstance(value, bool):
        return _Cell(text="true" if value else "false", numeric=False, empty=False)
    # The value as the warehouse returned it. Rounding and formatting are the
    # query's to do: a table that reformatted its numbers would disagree with
    # the rows it was built from.
    return _Cell(text=str(value), numeric=numeric, empty=False)


def _is_numeric(column_type: pa.DataType) -> bool:
    return (
        pa.types.is_integer(column_type)
        or pa.types.is_floating(column_type)
        or pa.types.is_decimal(column_type)
    )


def _environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(_TEMPLATES),
        autoescape=select_autoescape(("html", "xml", "j2")),
    )
