from pathlib import Path

import altair as alt
import pandas as pd

from dbt_charts.config import RenderConfig
from dbt_charts.ggsql.models import GgsqlChart
from dbt_charts.ggsql.parser import SUPPORTED_CHART_TYPES


class ChartRenderError(ValueError):
    """Raised when a chart cannot be rendered."""


def render_chart(
    chart: GgsqlChart,
    data: pd.DataFrame,
    png_path: Path,
    svg_path: Path,
    config: RenderConfig | None = None,
) -> None:
    config = config or RenderConfig()
    chart_spec = build_chart(chart, data, config=config)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if "svg" in config.formats:
            chart_spec.save(svg_path)
        if "png" in config.formats:
            chart_spec.save(png_path)
    except Exception as exc:
        raise ChartRenderError(str(exc)) from exc


def build_chart(
    chart: GgsqlChart,
    data: pd.DataFrame,
    config: RenderConfig | None = None,
) -> alt.Chart:
    config = config or RenderConfig()
    x_field = chart.field_for_role("x")
    y_field = chart.field_for_role("y")
    if x_field is None or y_field is None:
        raise ChartRenderError("VISUALISE requires x and y mappings")

    if chart.draw_type not in SUPPORTED_CHART_TYPES:
        raise ChartRenderError(f"unsupported chart type '{chart.draw_type}'")

    color_field = chart.field_for_role("color")
    required_fields = [x_field, y_field]
    if color_field is not None:
        required_fields.append(color_field)

    missing_columns = [field for field in required_fields if field not in data.columns]
    if missing_columns:
        joined = ", ".join(f"'{field}'" for field in missing_columns)
        raise ChartRenderError(f"query result missing chart column {joined}")

    width = chart.width or config.default_width
    height = chart.height or config.default_height
    title: str | alt.TitleParams | None = chart.title
    if chart.title and chart.subtitle:
        title = alt.TitleParams(text=chart.title, subtitle=chart.subtitle)

    encoding: dict[str, object]
    if chart.draw_type == "pie":
        encoding = {
            "theta": alt.Theta(y_field, title=chart.y_title),
            "color": alt.Color(
                color_field or x_field,
                title=chart.x_title if color_field is None else color_field,
            ),
        }
    else:
        encoding = {
            "x": alt.X(x_field, axis=alt.Axis(labelAngle=0), title=chart.x_title),
            "y": alt.Y(y_field, title=chart.y_title),
        }
        if color_field is not None:
            encoding["color"] = alt.Color(color_field)

    base = (
        alt.Chart(data)
        .encode(**encoding)
        .properties(
            title=title,
            width=width,
            height=height,
        )
        .configure_view(stroke="#d9e2ec")
    )
    if chart.draw_type == "line":
        return base.mark_line(point=True)
    if chart.draw_type == "bar":
        return base.mark_bar()
    if chart.draw_type == "scatter":
        return base.mark_circle(size=80)
    if chart.draw_type == "area":
        return base.mark_area(opacity=0.7)
    return base.mark_arc()
