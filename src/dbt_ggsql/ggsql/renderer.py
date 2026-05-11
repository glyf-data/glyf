from pathlib import Path

import altair as alt
import pandas as pd

from dbt_ggsql.ggsql.models import GgsqlChart


class ChartRenderError(ValueError):
    """Raised when a chart cannot be rendered."""


SUPPORTED_CHART_TYPES = {"line", "bar", "scatter"}


def render_chart(chart: GgsqlChart, data: pd.DataFrame, png_path: Path, svg_path: Path) -> None:
    chart_spec = build_chart(chart, data)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        chart_spec.save(svg_path)
        chart_spec.save(png_path)
    except Exception as exc:
        raise ChartRenderError(str(exc)) from exc


def build_chart(chart: GgsqlChart, data: pd.DataFrame) -> alt.Chart:
    x_field = chart.field_for_role("x")
    y_field = chart.field_for_role("y")
    if x_field is None or y_field is None:
        raise ChartRenderError("VISUALISE requires x and y mappings")

    if chart.draw_type not in SUPPORTED_CHART_TYPES:
        raise ChartRenderError(f"unsupported chart type '{chart.draw_type}'")

    missing_columns = [field for field in (x_field, y_field) if field not in data.columns]
    if missing_columns:
        joined = ", ".join(f"'{field}'" for field in missing_columns)
        raise ChartRenderError(f"query result missing chart column {joined}")

    base = alt.Chart(data).encode(x=x_field, y=y_field).properties(title=chart.title)
    if chart.draw_type == "line":
        return base.mark_line(point=True)
    if chart.draw_type == "bar":
        return base.mark_bar()
    return base.mark_circle(size=80)
