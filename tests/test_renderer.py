from pathlib import Path
import re

import pandas as pd
import pytest

from dbt_ggsql.ggsql.parser import GgsqlParseError, parse_ggsql
from dbt_ggsql.ggsql.renderer import ChartRenderError, render_chart


def test_render_chart_writes_png_and_svg(tmp_path: Path) -> None:
    chart = parse_ggsql(
        "select month, revenue from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW bar\n"
        "LABEL title => 'Monthly Revenue'\n",
        name="revenue",
    )
    data = pd.DataFrame(
        {
            "month": ["2026-01", "2026-02"],
            "revenue": [1200, 1800],
        }
    )
    png_path = tmp_path / "revenue.png"
    svg_path = tmp_path / "revenue.svg"

    render_chart(chart, data, png_path, svg_path)

    assert png_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    svg = svg_path.read_text(encoding="utf-8")
    assert "<svg" in svg
    width = int(re.search(r'width="(\d+)"', svg).group(1))
    height = int(re.search(r'height="(\d+)"', svg).group(1))
    assert width >= 800
    assert height >= 400


def test_render_chart_rejects_unsupported_chart_type(tmp_path: Path) -> None:
    with pytest.raises(GgsqlParseError, match="unsupported chart type 'heatmap'"):
        parse_ggsql(
            "select month, revenue from fct_orders\n\n"
            "VISUALISE month AS x, revenue AS y\n"
            "DRAW heatmap\n",
            name="revenue",
        )


def test_render_chart_supports_area_pie_scatter_and_color(tmp_path: Path) -> None:
    data = pd.DataFrame(
        {
            "month": ["2026-01", "2026-02"],
            "region": ["North", "South"],
            "revenue": [1200, 1800],
        }
    )
    chart_types = ["area", "pie", "scatter"]

    for chart_type in chart_types:
        chart = parse_ggsql(
            "select month, region, revenue from fct_orders\n\n"
            "VISUALISE month AS x, revenue AS y, region AS color\n"
            f"DRAW {chart_type}\n"
            "LABEL title => 'Revenue'\n"
            "LABEL subtitle => 'By region'\n"
            "LABEL x_title => 'Month'\n"
            "LABEL y_title => 'Revenue'\n"
            "CONFIG width => 500\n"
            "CONFIG height => 300\n",
            name=f"revenue_{chart_type}",
        )
        png_path = tmp_path / f"{chart_type}.png"
        svg_path = tmp_path / f"{chart_type}.svg"

        render_chart(chart, data, png_path, svg_path)

        assert png_path.exists()
        assert svg_path.exists()
        assert "Revenue" in svg_path.read_text(encoding="utf-8")


def test_render_chart_reports_missing_color_column(tmp_path: Path) -> None:
    chart = parse_ggsql(
        "select month, revenue from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y, region AS color\n"
        "DRAW bar\n",
        name="revenue",
    )
    data = pd.DataFrame({"month": ["2026-01"], "revenue": [1200]})

    with pytest.raises(ChartRenderError, match="query result missing chart column 'region'"):
        render_chart(chart, data, tmp_path / "revenue.png", tmp_path / "revenue.svg")
