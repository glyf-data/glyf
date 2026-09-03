"""Reducing a chart to the marks its pixels can show.

`render.downsample` is opt-in, and deliberately so: a downsampled chart's
artifacts carry fewer rows than the query returned, which is the author's
decision rather than a build's. When it is on, it applies M4 -- the first,
last, highest and lowest row of each pixel column -- to line and area charts
over `render.downsample_over` rows.

The property that matters is not the size of the output but that the picture
does not change. M4 keeps rows the warehouse returned rather than values
computed from them, so an outlier narrower than a bin survives; averaging each
bin would report its neighbourhood instead. `bench/downsampling.py fidelity`
measures that at scale, and the spike test below pins it.
"""

from dataclasses import replace
from pathlib import Path

import duckdb
import pytest

from glyf.config import ConfigError, GlyfConfig, RenderConfig, load_config
from glyf.downsample import Downsampling, downsample_m4, plan_downsampling
from glyf.execution.result import QueryResult
from glyf.ggsql.models import GgsqlChart, VisualiseMapping
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

WIDTH = 800


def _chart(draw: str = "line", *, color: bool = False, width: int | None = None) -> GgsqlChart:
    mappings = [VisualiseMapping("x", "x"), VisualiseMapping("y", "y")]
    if color:
        mappings.append(VisualiseMapping("series", "color"))
    return GgsqlChart(
        path=Path("chart.ggsql"),
        name="chart",
        sql="select 1",
        visualise=tuple(mappings),
        draw_type=draw,
        labels={},
        config={} if width is None else {"width": width},
    )


def _series(rows: int = 50_000, *, series: int = 1, spike_at: int | None = None) -> QueryResult:
    spike = (
        f"+ case when i between {spike_at} and {spike_at + 40} then 45 else 0 end"
        if spike_at is not None
        else ""
    )
    return QueryResult.from_arrow(
        duckdb.sql(f"""
            select
                i                                          as x,
                sin(i / 500.0) * 30 + 50 {spike}           as y,
                chr((97 + (i % {series}))::int)            as series
            from range({rows}) t(i)
        """).to_arrow_table()
    )


def _plan(chart: GgsqlChart, data: QueryResult, **overrides: object) -> Downsampling:
    settings: dict[str, object] = {"enabled": True, "over_rows": 25_000, "width": WIDTH}
    settings.update(overrides)
    return plan_downsampling(chart, data, **settings)  # type: ignore[arg-type]


# --------------------------------------------------------------- the reduction

def test_m4_reduces_a_line_to_the_marks_its_pixels_can_show() -> None:
    data = _series()

    reduced, marks = downsample_m4(_chart(), data, WIDTH)

    assert marks < len(data) / 10
    assert marks <= 4 * WIDTH, "at most four rows per pixel column"
    assert len(reduced) == marks


def test_m4_keeps_whole_rows_not_just_the_axes() -> None:
    """A tooltip or a colour reads columns the reduction never looked at."""
    data = _series(series=3)

    reduced, _ = downsample_m4(_chart(color=True), data, WIDTH)

    assert reduced.columns == data.columns
    assert {row["series"] for row in reduced.rows} == {"a", "b", "c"}


def test_m4_keeps_the_exact_peak_of_a_spike_narrower_than_a_bin() -> None:
    """The case that separates M4 from averaging each bin.

    A 40-row spike in 50,000 rows at 800 bins sits inside a single bin: its
    bin's maximum is the spike, its bin's mean is barely the neighbourhood.
    """
    data = _series(spike_at=30_000)
    peak = max(row["y"] for row in data.rows)

    reduced, _ = downsample_m4(_chart(), data, WIDTH)

    assert max(row["y"] for row in reduced.rows) == peak


def test_m4_preserves_the_vertical_extent_of_every_pixel_column() -> None:
    """The invariant the whole approach rests on.

    A line renderer's output in a pixel column is decided by how high and how
    low the series goes inside it. If those two agree for every column, the
    drawn line agrees -- which is a stronger claim than any single peak.
    """
    data = _series(rows=120_000)
    arrow_full = data.to_arrow()
    arrow_m4 = downsample_m4(_chart(), data, WIDTH)[0].to_arrow()

    differing = duckdb.sql(f"""
        with bounds as (select min(x) as lo, max(x) as hi from arrow_full),
        columns_full as (
            select least(floor((x - lo) / nullif(hi - lo, 0) * {WIDTH}), {WIDTH} - 1)
                       as bin,
                   min(y) as low, max(y) as high
            from arrow_full, bounds group by 1
        ),
        columns_m4 as (
            select least(floor((x - lo) / nullif(hi - lo, 0) * {WIDTH}), {WIDTH} - 1)
                       as bin,
                   min(y) as low, max(y) as high
            from arrow_m4, bounds group by 1
        )
        select count(*) from columns_full join columns_m4 using (bin)
        where abs(columns_full.low - columns_m4.low) > 1e-12
           or abs(columns_full.high - columns_m4.high) > 1e-12
    """).fetchone()[0]

    assert differing == 0


def test_m4_covers_every_pixel_column_the_result_reached() -> None:
    """A column the series entered must still have a mark in it."""
    data = _series(rows=120_000)
    arrow_full = data.to_arrow()
    arrow_m4 = downsample_m4(_chart(), data, WIDTH)[0].to_arrow()
    low, high = duckdb.sql("select min(x), max(x) from arrow_full").fetchone()

    def columns_reached(arrow_table: object) -> int:
        return duckdb.sql(f"""
            select count(distinct least(
                floor((x - {low}) / {high - low} * {WIDTH}), {WIDTH} - 1
            )) from arrow_table
        """).fetchone()[0]

    assert columns_reached(arrow_m4) == columns_reached(arrow_full) == WIDTH


def test_m4_bins_each_series_separately() -> None:
    """Shared bins would let a busy series' extremes stand in for a quiet one."""
    data = _series(rows=10_000, series=4)

    reduced, _ = downsample_m4(_chart(color=True), data, WIDTH)

    counts = {name: 0 for name in "abcd"}
    for row in reduced.rows:
        counts[str(row["series"])] += 1
    assert all(count > 0 for count in counts.values())


def test_m4_returns_rows_in_x_order() -> None:
    data = _series()

    reduced, _ = downsample_m4(_chart(), data, WIDTH)

    xs = [row["x"] for row in reduced.rows]
    assert xs == sorted(xs)


def test_m4_keeps_only_rows_that_were_in_the_result() -> None:
    """Nothing is computed: every mark drawn is a row the warehouse returned."""
    data = _series(rows=5_000)
    original = {(row["x"], row["y"]) for row in data.rows}

    reduced, _ = downsample_m4(_chart(), data, WIDTH)

    assert {(row["x"], row["y"]) for row in reduced.rows} <= original


# ------------------------------------------------------------------ the plan

def test_nothing_is_downsampled_unless_it_is_turned_on() -> None:
    assert _plan(_chart(), _series(), enabled=False).applied is False


def test_a_result_under_the_threshold_is_left_alone() -> None:
    assert _plan(_chart(), _series(rows=1_000)).applied is False


def test_a_line_over_the_threshold_is_downsampled_at_one_bin_per_pixel() -> None:
    plan = _plan(_chart(), _series())

    assert plan.applied is True
    assert plan.bins == WIDTH


def test_the_chart_decides_the_bin_count_when_it_sets_a_width() -> None:
    plan = _plan(_chart(width=320), _series(), width=320)

    assert plan.bins == 320


def test_an_area_chart_qualifies() -> None:
    assert _plan(_chart("area"), _series()).applied is True


@pytest.mark.parametrize("draw", ["scatter", "bar", "pie"])
def test_only_line_and_area_are_downsampled(draw: str) -> None:
    plan = _plan(_chart(draw), _series())

    assert plan.applied is False
    assert "line and area charts only" in plan.reason
    assert "rendering all 50000 marks" in plan.reason


def test_a_categorical_x_axis_cannot_be_binned() -> None:
    """Bins over a string axis would be bins over the warehouse's row order."""
    data = QueryResult.from_arrow(
        duckdb.sql(
            "select chr((97 + (i % 26))::int) as x, i * 1.0 as y from range(50000) t(i)"
        ).to_arrow_table()
    )

    plan = _plan(_chart(), data)

    assert plan.applied is False
    assert "numeric or temporal x axis" in plan.reason


def test_a_string_x_axis_says_what_would_fix_it(tmp_path: Path) -> None:
    """The shipped example charts a month name, which is a category.

    Worth pinning: a line chart over a string axis is ordinary, so the message
    has to name the column and the reason rather than just declining.
    """
    project = copy_basic_project(tmp_path)

    result = render_project(project, _config(downsample=True, downsample_over=1))

    assert len(result.warnings) == 1
    assert "'month' is string" in result.warnings[0]
    assert "numeric or temporal x axis" in result.warnings[0]


def test_a_temporal_x_axis_qualifies() -> None:
    data = QueryResult.from_arrow(
        duckdb.sql(
            "select timestamp '2020-01-01' + interval (i) second as x, "
            "i * 1.0 as y from range(50000) t(i)"
        ).to_arrow_table()
    )

    assert _plan(_chart(), data).applied is True


# ------------------------------------------------------------- through a build

def _project(tmp_path: Path, rows: int, draw: str = "line") -> Path:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        f"SELECT i AS month, sin(i / 50.0) * 100 AS revenue FROM range({rows}) t(i)\n\n"
        f"VISUALISE month AS x, revenue AS y\nDRAW {draw}\n"
        "LABEL title => 'Monthly Revenue'\nCONFIG width => 40\n",
        encoding="utf-8",
    )
    return project


def _config(**render: object) -> GlyfConfig:
    return GlyfConfig(render=replace(RenderConfig(), **render))


def test_a_build_downsamples_nothing_by_default(tmp_path: Path) -> None:
    project = _project(tmp_path, rows=2_000)

    result = render_project(project, _config(downsample_over=100))

    assert result.warnings == ()
    assert result.build is not None
    assert result.build.charts[0].downsampled_to is None
    assert result.build.charts[0].row_count == 2_000


def test_a_build_downsamples_a_large_line_when_asked(tmp_path: Path) -> None:
    project = _project(tmp_path, rows=2_000)

    result = render_project(project, _config(downsample=True, downsample_over=100))

    record = result.build.charts[0] if result.build else None
    assert record is not None
    assert record.row_count == 2_000, "the record keeps what the query returned"
    assert record.downsampled_to is not None
    assert record.downsampled_to < 2_000
    assert (project / "target" / "glyf" / "charts" / "revenue.png").exists()


def test_the_build_says_which_chart_it_downsampled(tmp_path: Path) -> None:
    project = _project(tmp_path, rows=2_000)

    result = render_project(project, _config(downsample=True, downsample_over=100))

    assert len(result.warnings) == 1
    warning = result.warnings[0]
    assert "revenue.ggsql" in warning
    assert "2000 rows downsampled to" in warning
    assert "M4, 40 bins" in warning, "the chart's own width sets the bins"


def test_a_chart_that_cannot_be_downsampled_says_so(tmp_path: Path) -> None:
    """Silence here would be the worst case: every mark drawn, nobody told."""
    project = _project(tmp_path, rows=2_000, draw="scatter")

    result = render_project(project, _config(downsample=True, downsample_over=100))

    assert len(result.warnings) == 1
    assert "line and area charts only" in result.warnings[0]
    assert result.build is not None
    assert result.build.charts[0].downsampled_to is None


def test_a_downsample_that_removes_nothing_is_not_reported(tmp_path: Path) -> None:
    """Twenty rows across forty bins are already one mark each."""
    project = _project(tmp_path, rows=20)

    result = render_project(project, _config(downsample=True, downsample_over=1))

    assert result.warnings == ()
    assert result.build is not None
    assert result.build.charts[0].downsampled_to is None


def test_downsampling_is_bounded_by_the_mark_budget_after_it_runs(
    tmp_path: Path,
) -> None:
    """The budget bounds what is drawn, so downsampling is what it sees."""
    project = _project(tmp_path, rows=2_000)

    result = render_project(
        project, _config(downsample=True, downsample_over=100, max_marks=200)
    )

    assert result.build is not None
    assert (result.build.charts[0].downsampled_to or 0) <= 200


# ------------------------------------------------------------------- config

def test_downsampling_is_off_by_default() -> None:
    assert RenderConfig().downsample is False
    assert RenderConfig().downsample_over == 25_000


def test_the_config_reads_both_settings(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text(
        "render:\n  downsample: true\n  downsample_over: 5000\n", encoding="utf-8"
    )

    config = load_config(tmp_path)

    assert config.render.downsample is True
    assert config.render.downsample_over == 5_000


def test_downsample_rejects_a_value_that_is_not_a_boolean(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text("render:\n  downsample: yes please\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="'render.downsample' must be true or false"):
        load_config(tmp_path)


def test_downsample_over_rejects_a_value_that_is_not_a_positive_integer(
    tmp_path: Path,
) -> None:
    (tmp_path / "glyf.yml").write_text("render:\n  downsample_over: 0\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="downsample_over"):
        load_config(tmp_path)
