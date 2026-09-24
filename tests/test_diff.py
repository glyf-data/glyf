"""`glyf diff`: which charts changed between two builds, how much, and why."""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyf.cli import app
from glyf.diff import DiffError, compare_builds, write_report
from glyf.diff.compare import resolve_build_dir
from glyf.diff.report import describe_change
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

runner = CliRunner()

SEEDS = "month,revenue\n2026-01,1200\n2026-02,1800\n2026-03,2400\n"


def _build(project: Path) -> Path:
    render_project(project)
    return project / "target" / "glyf"


def _baseline_and_project(tmp_path: Path) -> tuple[Path, Path]:
    """A built project, and a copy of that build to compare later ones with."""
    project = copy_basic_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(SEEDS, encoding="utf-8")
    baseline = tmp_path / "baseline"
    shutil.copytree(_build(project), baseline)
    return baseline, project


def test_a_rebuild_of_unchanged_data_changes_nothing(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)

    diff = compare_builds(baseline, _build(project))

    assert not diff.has_changes
    assert [chart.status for chart in diff.charts] == ["unchanged"]


def test_changed_rows_are_reported_with_what_moved(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "3000"), encoding="utf-8"
    )

    diff = compare_builds(baseline, _build(project))

    (chart,) = diff.with_status("changed")
    assert chart.name == "revenue"
    assert chart.title == "Monthly Revenue"
    assert 0 < chart.changed_pixels < chart.total_pixels
    assert chart.reasons == ("the rows changed",)
    assert chart.data is not None
    (revenue,) = chart.data.fields
    assert (revenue.name, revenue.before_sum, revenue.after_sum) == ("revenue", 5400.0, 6000.0)
    assert revenue.percent == pytest.approx(11.11, abs=0.01)


def test_a_changed_query_is_named_as_the_reason(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    chart_file = project / "visualisations" / "revenue.ggsql"
    chart_file.write_text(
        chart_file.read_text(encoding="utf-8").replace(
            "SELECT month, revenue", "SELECT month, revenue * 2 AS revenue"
        ),
        encoding="utf-8",
    )

    (chart,) = compare_builds(baseline, _build(project)).with_status("changed")

    assert chart.reasons == ("the query changed", "the rows changed")


def test_a_changed_label_is_the_chart_definition(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    chart_file = project / "visualisations" / "revenue.ggsql"
    chart_file.write_text(
        chart_file.read_text(encoding="utf-8").replace("Monthly Revenue", "Revenue"),
        encoding="utf-8",
    )

    (chart,) = compare_builds(baseline, _build(project)).with_status("changed")

    # Same query, same rows, same glyf: only the chart block is left.
    assert chart.reasons == ("the chart definition changed",)


def test_new_and_missing_categories_are_listed(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2026-01,1200\n", "") + "2026-04,2600\n", encoding="utf-8"
    )

    (chart,) = compare_builds(baseline, _build(project)).with_status("changed")

    assert chart.data is not None
    month = next(change for change in chart.data.fields if change.name == "month")
    assert month.new_values == ("2026-04",)
    assert month.gone_values == ("2026-01",)


def test_added_and_removed_charts(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    visualisations = project / "visualisations"
    original = (visualisations / "revenue.ggsql").read_text(encoding="utf-8")
    (visualisations / "revenue.ggsql").unlink()
    (visualisations / "revenue_bars.ggsql").write_text(
        original.replace("DRAW line", "DRAW bar"), encoding="utf-8"
    )
    shutil.rmtree(project / "target" / "glyf")
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive\ncharts:\n  - revenue_bars\n", encoding="utf-8"
    )

    diff = compare_builds(baseline, _build(project))

    assert [chart.name for chart in diff.with_status("added")] == ["revenue_bars"]
    assert [chart.name for chart in diff.with_status("removed")] == ["revenue"]
    assert diff.has_changes


def test_threshold_forgives_a_small_change(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "3000"), encoding="utf-8"
    )
    current = _build(project)

    assert compare_builds(baseline, current).has_changes
    assert not compare_builds(baseline, current, threshold=100.0).has_changes


def test_report_is_self_contained(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "3000"), encoding="utf-8"
    )
    diff = compare_builds(baseline, _build(project))

    page = write_report(diff, tmp_path / "report")

    report = page.parent
    for view in ("before", "after", "diff", "overlay"):
        assert (report / "images" / f"revenue.{view}.png").read_bytes().startswith(b"\x89PNG")
    document = json.loads((report / "diff.json").read_text(encoding="utf-8"))
    assert document["diff_version"] == "1"
    assert document["counts"] == {"added": 0, "changed": 1, "removed": 0, "unchanged": 0}
    assert document["charts"]["revenue"]["reasons"] == ["the rows changed"]
    assert document["charts"]["revenue"]["marks"]["summary"] == "points: 1 higher"
    summary = (report / "summary.md").read_text(encoding="utf-8")
    assert "**1 changed, 0 unchanged**" in summary
    assert "points: 1 higher<br>sum of revenue 5,400 → 6,000 (+11.1%)" in summary
    html = page.read_text(encoding="utf-8")
    # A chart the overlay can draw shows itself over its old self; the pixel
    # picture is still written for anything that wants it.
    assert "images/revenue.overlay.png" in html
    assert "images/revenue.diff.png" not in html
    # A shared report does not publish the layout of the machine that built it.
    assert str(tmp_path) not in html


def test_build_dir_is_found_from_a_project_root(tmp_path: Path) -> None:
    _, project = _baseline_and_project(tmp_path)

    assert resolve_build_dir(project) == project / "target" / "glyf"
    with pytest.raises(DiffError, match="does not hold a glyf build"):
        resolve_build_dir(tmp_path / "nowhere")


def test_diff_command_reports_and_can_fail_the_run(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "3000"), encoding="utf-8"
    )
    _build(project)
    arguments = ["diff", "--baseline", str(baseline), "--project", str(project)]

    reported = runner.invoke(app, arguments)
    failed = runner.invoke(app, [*arguments, "--fail-on-change"])

    assert reported.exit_code == 0
    assert "~ revenue:" in reported.output
    # The row changes sit under the chart they belong to.
    assert "    sum of revenue 5,400 → 6,000 (+11.1%)" in reported.output
    assert "✓ 1 changed, 0 unchanged" in reported.output
    assert "✓ wrote target/glyf/diff/index.html" in reported.output
    assert failed.exit_code == 1


def test_diff_command_explains_a_missing_baseline(tmp_path: Path) -> None:
    _, project = _baseline_and_project(tmp_path)

    result = runner.invoke(
        app, ["diff", "--baseline", str(tmp_path / "nowhere"), "--project", str(project)]
    )

    assert result.exit_code == 1
    assert "Diff failed" in result.output
    assert "Run glyf build there first." in result.output


def test_the_same_rows_in_a_different_order_are_named_as_such(tmp_path: Path) -> None:
    """An ORDER BY that leaves ties: no value moved, but the picture can."""
    baseline, project = _baseline_and_project(tmp_path)
    current = _build(project)
    rows_file = current / "data" / "normalized" / "revenue.data.json"
    document = json.loads(rows_file.read_text(encoding="utf-8"))
    document["rows"].reverse()
    rows_file.write_text(json.dumps(document), encoding="utf-8")
    # Stand-ins for a picture that moved; the rows are what is under test.
    (baseline / "charts" / "revenue.png").write_bytes(_png(4, 4, (255, 255, 255, 255)))
    (current / "charts" / "revenue.png").write_bytes(_png(4, 4, (0, 0, 0, 255)))

    diff = compare_builds(baseline, current)

    (chart,) = diff.with_status("changed")
    assert chart.data is not None and chart.data.reordered
    assert chart.reasons == ("the same rows came back in a different order",)
    summary = write_report(diff, tmp_path / "report").parent / "summary.md"
    assert "ORDER BY leaves ties" in summary.read_text(encoding="utf-8")


def _png(width: int, height: int, colour: tuple[int, int, int, int]) -> bytes:
    """A solid PNG, written by hand so the tests need no image library."""
    import struct
    import zlib

    row = b"\x00" + bytes(colour) * width
    body = zlib.compress(row * height)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data))
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", body) + chunk(b"IEND", b"")


def test_a_dropped_category_is_drawn_and_said_in_the_charts_terms(tmp_path: Path) -> None:
    """A stacked bar with one series gone: the overlay lists it, the boxes name the months."""
    project = copy_basic_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        "month,region,revenue\n"
        "2026-01,east,100\n2026-01,west,50\n"
        "2026-02,east,120\n2026-02,west,60\n"
        "2026-03,east,140\n2026-03,west,70\n",
        encoding="utf-8",
    )
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select month, region, sum(revenue) as revenue from {{ ref('fct_orders') }}\n"
        "group by 1, 2 order by 1, 2\n\n"
        "VISUALISE month AS x, revenue AS y, region AS color\nDRAW bar\n"
        "LABEL title => 'Revenue'\n",
        encoding="utf-8",
    )
    baseline = tmp_path / "baseline"
    shutil.copytree(_build(project), baseline)
    (project / "seeds" / "fct_orders.csv").write_text(
        "month,region,revenue\n2026-01,east,100\n2026-02,east,120\n2026-03,east,150\n",
        encoding="utf-8",
    )

    diff = compare_builds(baseline, _build(project))

    (chart,) = diff.with_status("changed")
    assert chart.overlay_png is not None and chart.overlay_png.startswith(b"\x89PNG")
    assert chart.marks is not None
    assert chart.marks.describe() == "bars: 3 gone (west), 1 higher"
    assert chart.marks.changed_x == ("2026-01", "2026-02", "2026-03")


def test_a_spike_that_rescales_the_axis_is_named_as_scale(tmp_path: Path) -> None:
    """One month jumps; the rest shrink on the page but did not change."""
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "24000"), encoding="utf-8"
    )

    diff = compare_builds(baseline, _build(project))

    (chart,) = diff.with_status("changed")
    lines = describe_change(chart)
    assert lines[0].startswith("y axis 0–") and "→ 0–24k" in lines[0], lines
    assert lines[1] == "points: 1 higher"


def test_a_chart_the_overlay_cannot_draw_keeps_the_pixel_picture(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select month, revenue from {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\nDRAW pie\nLABEL title => 'Share'\n",
        encoding="utf-8",
    )
    shutil.rmtree(baseline)
    shutil.copytree(_build(project), baseline)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "3000"), encoding="utf-8"
    )

    diff = compare_builds(baseline, _build(project))
    page = write_report(diff, tmp_path / "report")

    (chart,) = diff.with_status("changed")
    assert chart.overlay_png is None and chart.marks is None
    assert "images/revenue.diff.png" in page.read_text(encoding="utf-8")
    assert not (page.parent / "images" / "revenue.overlay.png").exists()


def test_the_overlay_is_byte_stable(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "3000"), encoding="utf-8"
    )
    current = _build(project)

    first = compare_builds(baseline, current).with_status("changed")[0].overlay_png
    second = compare_builds(baseline, current).with_status("changed")[0].overlay_png

    assert first == second
