"""`glyf diff` on a table: judged by its fragment, explained by its rows.

A table has no picture, so there are no pixels to count and no overlay to
draw. Its HTML fragment is written from the rows and nothing else, so it is
byte-stable the way a PNG is, and a fragment that differs is a table that
changed. The report then says what moved in the rows' terms and shows the
two fragments side by side.
"""

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from glyf.cli import app
from glyf.diff import compare_builds, write_report
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

runner = CliRunner()

SEEDS = "month,revenue\n2026-01,1200\n2026-02,1800\n2026-03,2400\n"
TABLE = (
    "SELECT month, revenue\nFROM {{ ref('fct_orders') }}\nORDER BY month\n\n"
    "VISUALISE month, revenue\nDRAW table\nLABEL title => 'Months'\n"
)


def _build(project: Path) -> Path:
    render_project(project)
    return project / "target" / "glyf"


def _baseline_and_project(tmp_path: Path) -> tuple[Path, Path]:
    project = copy_basic_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(SEEDS, encoding="utf-8")
    (project / "visualisations" / "months.ggsql").write_text(TABLE, encoding="utf-8")
    baseline = tmp_path / "baseline"
    shutil.copytree(_build(project), baseline)
    return baseline, project


def test_a_rebuild_of_the_same_rows_is_the_same_table(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)

    diff = compare_builds(baseline, _build(project))

    assert not diff.has_changes
    months = next(chart for chart in diff.charts if chart.name == "months")
    assert months.status == "unchanged"
    assert months.table


def test_changed_rows_change_the_table_and_are_said_in_the_rows_terms(
    tmp_path: Path,
) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "3000"), encoding="utf-8"
    )

    diff = compare_builds(baseline, _build(project))

    months = next(chart for chart in diff.with_status("changed") if chart.name == "months")
    assert months.table
    assert months.title == "Months"
    assert months.reasons == ("the rows changed",)
    assert months.changed_pixels == 0 and months.overlay_png is None and months.marks is None
    assert months.data is not None
    (revenue,) = months.data.fields
    assert (revenue.before_sum, revenue.after_sum) == (5400.0, 6000.0)
    assert months.before_fragment is not None and "2400" in months.before_fragment
    assert months.after_fragment is not None and "3000" in months.after_fragment


def test_a_changed_label_changes_the_table_as_a_definition_change(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "visualisations" / "months.ggsql").write_text(
        TABLE + "LABEL revenue => 'Revenue (USD)'\n", encoding="utf-8"
    )

    diff = compare_builds(baseline, _build(project))

    months = next(chart for chart in diff.with_status("changed") if chart.name == "months")
    assert months.reasons == ("the chart definition changed",)
    assert months.data is not None and months.data.is_empty


def test_the_report_shows_both_fragments_and_no_picture(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "3000"), encoding="utf-8"
    )
    diff = compare_builds(baseline, _build(project))

    page = write_report(diff, tmp_path / "report")

    report = page.parent
    assert (report / "fragments" / "months.before.html").exists()
    assert (report / "fragments" / "months.after.html").exists()
    assert not list((report / "images").glob("months.*"))

    document = json.loads((report / "diff.json").read_text(encoding="utf-8"))
    months = document["charts"]["months"]
    assert months["table"] is True
    assert months["status"] == "changed"
    assert months["reasons"] == ["the rows changed"]
    assert months["fragments"] == {
        "before": "fragments/months.before.html",
        "after": "fragments/months.after.html",
    }
    assert "changed_pixels" not in months and "images" not in months
    assert months["data"]["fields"][0]["name"] == "revenue"
    # A drawn chart's entry is what it was.
    assert "changed_pixels" in document["charts"]["revenue"]
    assert "table" not in document["charts"]["revenue"]

    summary = (report / "summary.md").read_text(encoding="utf-8")
    assert "| **Months** `months` | table rows | the rows changed | sum of revenue 5,400 → 6,000 (+11.1%) |" in summary

    html = page.read_text(encoding="utf-8")
    assert "the rows changed</span>" in html
    assert html.count('data-glyf-table="months"') == 2, "before and after, inlined"
    assert "images/months" not in html


def test_an_added_table_is_shown_as_new(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    baseline = tmp_path / "baseline"
    shutil.copytree(_build(project), baseline)
    (project / "visualisations" / "months.ggsql").write_text(TABLE, encoding="utf-8")

    diff = compare_builds(baseline, _build(project))
    page = write_report(diff, tmp_path / "report")

    (months,) = diff.with_status("added")
    assert months.table and months.after_fragment is not None
    document = json.loads((page.parent / "diff.json").read_text(encoding="utf-8"))
    assert document["charts"]["months"] == {
        "status": "added",
        "title": "Months",
        "table": True,
        "fragments": {"after": "fragments/months.after.html"},
    }
    assert "New in this build" in page.read_text(encoding="utf-8")


def test_diff_command_says_the_table_changed(tmp_path: Path) -> None:
    baseline, project = _baseline_and_project(tmp_path)
    (project / "seeds" / "fct_orders.csv").write_text(
        SEEDS.replace("2400", "3000"), encoding="utf-8"
    )
    _build(project)

    result = runner.invoke(
        app, ["diff", "--project-dir", str(project), "--baseline", str(baseline)]
    )

    assert result.exit_code == 0, result.output
    assert "~ months: the table changed (the rows changed)" in result.output
    assert "sum of revenue 5,400 → 6,000 (+11.1%)" in result.output
