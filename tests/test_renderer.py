from pathlib import Path

import pandas as pd
import pytest

from dbt_ggsql.ggsql.parser import parse_ggsql
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
    assert 'width="778"' in svg
    assert 'height="484"' in svg


def test_render_chart_rejects_unsupported_chart_type(tmp_path: Path) -> None:
    chart = parse_ggsql(
        "select month, revenue from fct_orders\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW pie\n",
        name="revenue",
    )
    data = pd.DataFrame({"month": ["2026-01"], "revenue": [1200]})

    with pytest.raises(ChartRenderError, match="unsupported chart type 'pie'"):
        render_chart(chart, data, tmp_path / "revenue.png", tmp_path / "revenue.svg")
