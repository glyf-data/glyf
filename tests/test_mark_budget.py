"""The bound that keeps an oversized chart from killing the build.

`execution.max_rows` bounds what a query is allowed to return, and it is unset
by default. `render.max_marks` bounds what the renderer is asked to draw, and
it is not: past roughly half a million marks vl-convert stops failing and
starts aborting. It inlines every mark into a JavaScript heap, and when that
heap runs out the process dies -- exit 133, a V8 C stack trace instead of a
traceback, and in a multi-chart build no indication of which chart caused it.

The budget exists so that becomes a normal `RenderError` naming the chart.
Nothing here renders a chart that large: the cost of proving the crash is
minutes and a 138 MB artifact, which is what `bench/downsampling.py ceiling`
is for. These tests prove the guard fires, and that it fires before the
renderer is reached.
"""

from dataclasses import replace
from pathlib import Path

import pytest

from glyf.config import ConfigError, GlyfConfig, RenderConfig, load_config
from glyf.pipeline import RenderError, render_project
from tests.helpers import copy_basic_project


def _config(**render: object) -> GlyfConfig:
    return GlyfConfig(render=replace(RenderConfig(), **render))


def test_a_chart_over_the_budget_fails_the_build(tmp_path: Path) -> None:
    """The fixture draws four marks; a budget of three is one too few."""
    project = copy_basic_project(tmp_path)

    with pytest.raises(RenderError, match="would draw 4 marks"):
        render_project(project, _config(max_marks=3))


def test_the_error_names_the_chart_and_what_to_do(tmp_path: Path) -> None:
    """What the V8 abort cannot do: say which chart, and say what to change."""
    project = copy_basic_project(tmp_path)

    with pytest.raises(RenderError) as error:
        render_project(project, _config(max_marks=1))

    message = str(error.value)
    assert "revenue.ggsql" in message
    assert "render.max_marks" in message
    assert "Aggregate the query" in message


def test_the_budget_fires_before_anything_is_rendered(tmp_path: Path) -> None:
    """The guard is worthless if it runs after the renderer has already died."""
    project = copy_basic_project(tmp_path)

    with pytest.raises(RenderError):
        render_project(project, _config(max_marks=1))

    charts = project / "target" / "glyf" / "charts"
    assert not list(charts.glob("*.png"))
    assert not list(charts.glob("*.svg"))


def test_a_chart_that_exactly_fills_the_budget_renders(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = render_project(project, _config(max_marks=4))

    assert len(result.charts[0].data) == 4
    assert (project / "target" / "glyf" / "charts" / "revenue.png").exists()


def test_the_budget_applies_with_no_configuration(tmp_path: Path) -> None:
    """Unlike max_rows, this one defends a project that never set anything."""
    assert RenderConfig().max_marks == 500_000

    project = copy_basic_project(tmp_path)
    result = render_project(project, GlyfConfig())

    assert (project / "target" / "glyf" / "charts" / "revenue.png").exists()
    assert len(result.charts[0].data) == 4


def test_validate_mode_never_trips_the_budget(tmp_path: Path) -> None:
    """A validate run fetches no rows, so it has nothing to bound."""
    project = copy_basic_project(tmp_path)
    config = replace(
        _config(max_marks=1), execution=replace(GlyfConfig().execution, mode="validate")
    )

    result = render_project(project, config)

    assert result.validated_only is True


def test_max_marks_defaults_when_the_key_is_absent(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text("render:\n  default_width: 640\n", encoding="utf-8")

    config = load_config(tmp_path)

    assert config.render.max_marks == 500_000
    assert config.render.default_width == 640


def test_max_marks_can_be_turned_off_explicitly(tmp_path: Path) -> None:
    """`null` is not the same as absent: it removes the guard on purpose."""
    (tmp_path / "glyf.yml").write_text("render:\n  max_marks: null\n", encoding="utf-8")

    assert load_config(tmp_path).render.max_marks is None


def test_max_marks_can_be_raised(tmp_path: Path) -> None:
    (tmp_path / "glyf.yml").write_text("render:\n  max_marks: 750000\n", encoding="utf-8")

    assert load_config(tmp_path).render.max_marks == 750_000


@pytest.mark.parametrize("value", ["0", "-1", "'lots'", "true"])
def test_max_marks_rejects_a_value_that_is_not_a_positive_integer(
    tmp_path: Path, value: str
) -> None:
    (tmp_path / "glyf.yml").write_text(f"render:\n  max_marks: {value}\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="max_marks"):
        load_config(tmp_path)
