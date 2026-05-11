import shutil
from pathlib import Path

from typer.testing import CliRunner

from dbt_ggsql.cli import app


runner = CliRunner()


def test_list_command_outputs_discovered_assets() -> None:
    result = runner.invoke(app, ["list", "--project", "examples/basic"])

    assert result.exit_code == 0
    assert "visualisations/revenue.ggsql" in result.output
    assert "dashboards/executive.yml" in result.output
    assert "fct_orders -> main.fct_orders" in result.output


def test_validate_command_passes_basic_example() -> None:
    result = runner.invoke(app, ["validate", "--project", "examples/basic"])

    assert result.exit_code == 0
    assert "Validation passed" in result.output


def test_project_dir_option_validates_simple_dbt_example() -> None:
    result = runner.invoke(app, ["validate", "--project-dir", "examples/simple_dbt"])

    assert result.exit_code == 0
    assert "Validation passed" in result.output


def test_render_command_outputs_pipeline_steps(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)

    result = runner.invoke(app, ["render", "--project", str(project)])

    assert result.exit_code == 0
    assert "✓ discovered charts (1)" in result.output
    assert "✓ compiled SQL" in result.output
    assert "✓ executed SQL" in result.output
    assert "✓ rendered PNG/SVG" in result.output
    assert "✓ wrote metadata" in result.output
    assert (project / "target" / "ggsql" / "compiled" / "revenue.sql").exists()


def test_dashboard_command_outputs_pipeline_steps(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    render_result = runner.invoke(app, ["render", "--project", str(project)])
    assert render_result.exit_code == 0

    result = runner.invoke(app, ["dashboard", "--project", str(project)])

    assert result.exit_code == 0
    assert "✓ discovered dashboard configs" in result.output
    assert "✓ loaded chart artifacts" in result.output
    assert "✓ generated dashboard HTML" in result.output
    assert "✓ generated index page" in result.output
    assert (project / "target" / "ggsql" / "dashboards" / "executive.html").exists()
    assert (project / "target" / "ggsql" / "index.html").exists()


def test_export_command_outputs_pipeline_steps(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    render_result = runner.invoke(app, ["render", "--project", str(project)])
    assert render_result.exit_code == 0
    dashboard_result = runner.invoke(app, ["dashboard", "--project", str(project)])
    assert dashboard_result.exit_code == 0

    result = runner.invoke(app, ["export", "--project", str(project), "--zip"])

    assert result.exit_code == 0
    assert "✓ copied dashboard HTML" in result.output
    assert "✓ copied chart artifacts" in result.output
    assert "✓ wrote site assets" in result.output
    assert (project / "target" / "ggsql" / "site" / "index.html").exists()
    assert (project / "target" / "ggsql" / "dbt-ggsql-site.zip").exists()


def test_validate_command_reports_malformed_ggsql(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select 1\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "Validation failed" in result.output
    assert "missing VISUALISE section" in result.output


def test_validate_command_reports_unresolved_ref(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select * from {{ ref('missing_model') }}\n\nVISUALISE one AS x\nDRAW line\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "unknown model 'missing_model'" in result.output


def test_validate_command_reports_unresolved_source(tmp_path: Path) -> None:
    project = tmp_path / "simple_dbt"
    shutil.copytree(Path("examples/simple_dbt"), project)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select * from {{ source('raw', 'missing') }}\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW line\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--project-dir", str(project)])

    assert result.exit_code == 1
    assert "unknown source 'raw.missing'" in result.output


def test_validate_command_reports_invalid_dashboard_reference(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive Dashboard\ncharts:\n  - missing_chart\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "unknown chart 'missing_chart'" in result.output


def test_validate_command_reports_missing_manifest(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    (project / "target" / "manifest.json").unlink()

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "Missing target/manifest.json" in result.output


def test_validate_command_reports_missing_dbt_project(tmp_path: Path) -> None:
    project = tmp_path / "basic"
    shutil.copytree(Path("examples/basic"), project)
    (project / "dbt_project.yml").unlink()

    result = runner.invoke(app, ["validate", "--project-dir", str(project)])

    assert result.exit_code == 1
    assert "Missing dbt_project.yml" in result.output
