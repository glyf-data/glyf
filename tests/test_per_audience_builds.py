"""Building one artifact per audience.

A static artifact is one materialised view of the data, so per-viewer
filtering inside it is impossible. The static-native answer is to build once
per audience: `--target` runs the queries as that audience's warehouse
identity, so its role decides what the artifacts can contain; `--select`
decides which dashboards the build produces; `--output-dir` keeps the results
apart.

Only the first of those is a privacy control, and it is the warehouse that
enforces it. These tests cover what glyf is responsible for: running as the
identity it was told to, building what it was told to, and leaving nothing
from another audience's build behind.
"""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from glyf.cli import app
from glyf.config import ConfigError, ExecutionConfig, GlyfConfig, apply_run_overrides
from glyf.dashboard.generator import generate_dashboards
from glyf.exporter import export_site
from glyf.pipeline import RenderError, render_project
from glyf.selection import SelectionError, resolve_selection
from glyf.project.scanner import scan_project
from tests.helpers import copy_basic_project

runner = CliRunner()


# --- selecting the dashboards -------------------------------------------------


def test_a_tag_builds_only_that_audiences_dashboards(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)

    _build(project, select=("tag:hr",))

    site = project / "target" / "glyf" / "site"
    assert (site / "dashboards" / "people.html").exists()
    assert not (site / "dashboards" / "executive.html").exists()
    # ...and only the charts that dashboard uses.
    assert (site / "charts" / "headcount.png").exists()
    assert not (site / "charts" / "revenue.png").exists()
    assert not (site / "compiled" / "revenue.sql").exists()


def test_a_dashboard_can_be_selected_by_name(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)

    for selector in ("people", "name:people"):
        result = render_project(project, select=(selector,))
        assert [chart.chart.name for chart in result.charts] == ["headcount"]


def test_selectors_are_a_union(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)

    result = render_project(project, select=("tag:hr", "executive"))

    assert sorted(chart.chart.name for chart in result.charts) == [
        "headcount",
        "revenue",
    ]


def test_matching_ignores_case(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)

    result = render_project(project, select=("tag:HR",))

    assert [chart.chart.name for chart in result.charts] == ["headcount"]


def test_a_selector_matching_nothing_is_an_error(tmp_path: Path) -> None:
    """An empty site is a successful build of the wrong thing."""
    project = _two_audience_project(tmp_path)

    with pytest.raises(SelectionError, match="no dashboard matches tag:legal"):
        render_project(project, select=("tag:legal",))


def test_an_empty_selector_says_what_one_looks_like(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)
    scan = scan_project(project)

    with pytest.raises(SelectionError, match="--select tag:finance"):
        resolve_selection(scan, ("  ",))


def test_a_selected_dashboard_missing_its_chart_fails(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)
    (project / "visualisations" / "headcount.ggsql").unlink()

    with pytest.raises(RenderError, match="unknown chart 'headcount'"):
        render_project(project, select=("tag:hr",))


def test_no_selector_builds_everything(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)

    result = render_project(project)

    assert result.selection is None
    assert len(result.charts) == 2


# --- keeping one audience's build out of another's ----------------------------


def test_an_earlier_build_does_not_ride_along(tmp_path: Path) -> None:
    """Export copies the artifact directory, not a list of what was just built."""
    project = _two_audience_project(tmp_path)
    _build(project)  # everything, as a full build would leave it
    assert (project / "target" / "glyf" / "charts" / "revenue.png").exists()

    _build(project, select=("tag:hr",))

    charts = project / "target" / "glyf" / "charts"
    assert not list(charts.glob("revenue.*")), "the finance chart is still on disk"
    assert (charts / "headcount.png").exists()
    site = project / "target" / "glyf" / "site"
    assert not list(site.rglob("revenue.*"))
    assert not (site / "dashboards" / "executive.html").exists()
    assert not (
        project / "target" / "glyf" / "dashboards" / "executive.html"
    ).exists()
    bundle = json.loads((site / "bundle.json").read_text(encoding="utf-8"))
    assert list(bundle["charts"]) == ["headcount"]
    assert list(bundle["dashboards"]) == ["people"]


def test_output_dir_keeps_two_audiences_apart(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)

    for audience, selector in (("finance", "tag:finance"), ("hr", "tag:hr")):
        result = runner.invoke(
            app,
            [
                "build",
                "--project",
                str(project),
                "--select",
                selector,
                "--output-dir",
                str(project / "artifacts" / audience),
            ],
        )
        assert result.exit_code == 0, result.output

    finance = project / "artifacts" / "finance" / "site"
    hr = project / "artifacts" / "hr" / "site"
    assert (finance / "dashboards" / "executive.html").exists()
    assert not (finance / "dashboards" / "people.html").exists()
    assert (hr / "dashboards" / "people.html").exists()
    assert not (hr / "dashboards" / "executive.html").exists()
    assert not (project / "target" / "glyf" / "site").exists()


def test_output_dir_moves_every_derived_directory(tmp_path: Path) -> None:
    config = GlyfConfig().with_output_dir(Path("artifacts/exec"))

    assert config.output_path == Path("artifacts/exec")
    assert config.compiled_path == Path("artifacts/exec/compiled")
    assert config.charts_path == Path("artifacts/exec/charts")
    assert config.dashboards_output_path == Path("artifacts/exec/dashboards")
    assert config.site_path == Path("artifacts/exec/site")


# --- running as an audience's identity ----------------------------------------


def test_target_selects_the_dbt_profile_target() -> None:
    config = replace(GlyfConfig(), execution=ExecutionConfig(backend="dbt"))

    applied = apply_run_overrides(config, target="exec")

    assert applied.execution.target == "exec"


def test_target_without_the_dbt_backend_is_refused() -> None:
    """A target the backend ignores would be a false sense of security."""
    with pytest.raises(ConfigError, match="needs execution.backend: dbt"):
        apply_run_overrides(GlyfConfig(), target="exec")


def test_the_cli_refuses_a_target_it_would_ignore(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)

    result = runner.invoke(
        app, ["build", "--project", str(project), "--target", "exec"]
    )

    assert result.exit_code == 1
    assert "execution.backend: dbt" in result.output


def test_the_build_says_which_dashboards_it_selected(tmp_path: Path) -> None:
    project = _two_audience_project(tmp_path)

    result = runner.invoke(
        app, ["build", "--project", str(project), "--select", "tag:hr", "--verbose"]
    )

    assert result.exit_code == 0, result.output
    assert "selected dashboards (tag:hr)" in result.output


# --- helpers ------------------------------------------------------------------


def _two_audience_project(tmp_path: Path) -> Path:
    """The basic project plus a second dashboard for a second audience."""
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "headcount.ggsql").write_text(
        "SELECT month, revenue\n"
        "FROM {{ ref('fct_orders') }}\n"
        "\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW bar\n"
        "LABEL title => 'Headcount'\n",
        encoding="utf-8",
    )
    (project / "dashboards" / "people.yml").write_text(
        "name: people\n"
        "title: People\n"
        "tags:\n"
        "  - hr\n"
        "\n"
        "charts:\n"
        "  - headcount\n",
        encoding="utf-8",
    )
    return project


def _build(project: Path, *, select: tuple[str, ...] | None = None) -> None:
    config = GlyfConfig()
    render_project(project, config, select=select)
    generate_dashboards(project, config, select=select)
    export_site(project, config=config)
