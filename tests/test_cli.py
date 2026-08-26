from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from glyf.cli import app
from tests.helpers import copy_basic_project, copy_simple_dbt_project


runner = CliRunner()


def test_init_command_creates_starter_files(tmp_path: Path) -> None:
    project = tmp_path / "my_dbt_project"
    project.mkdir()
    (project / "dbt_project.yml").write_text("name: my_dbt_project\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "init",
            "--project",
            str(project),
            "--chart-name",
            "monthly_revenue",
            "--dashboard-name",
            "executive",
            "--model-name",
            "fct_orders",
            "--chart-title",
            "Monthly Revenue",
            "--chart-type",
            "line",
        ],
    )

    assert result.exit_code == 0
    assert "Initialized glyf" in result.output
    assert "✓ wrote glyf.yml" in result.output
    assert "✓ wrote visualisations/monthly_revenue.ggsql" in result.output
    assert "✓ wrote dashboards/executive.yml" in result.output
    assert "glyf build" in result.output
    assert "glyf serve" in result.output
    assert (project / "glyf.yml").exists()
    assert (project / "visualisations" / "monthly_revenue.ggsql").exists()
    assert (project / "dashboards" / "executive.yml").exists()
    assert "{{ ref('fct_orders') }}" in (
        project / "visualisations" / "monthly_revenue.ggsql"
    ).read_text(encoding="utf-8")
    assert "monthly_revenue" in (project / "dashboards" / "executive.yml").read_text(
        encoding="utf-8"
    )


def test_init_command_prompts_for_starter_values(tmp_path: Path) -> None:
    project = tmp_path / "my_dbt_project"
    project.mkdir()
    (project / "dbt_project.yml").write_text("name: my_dbt_project\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["init", "--project", str(project)],
        input="weekly_signups\nproduct\nfct_signups\nWeekly Signups\nbar\n",
    )

    assert result.exit_code == 0
    assert "Starter chart name" in result.output
    assert (project / "visualisations" / "weekly_signups.ggsql").exists()
    assert (project / "dashboards" / "product.yml").exists()
    assert "DRAW bar" in (project / "visualisations" / "weekly_signups.ggsql").read_text(
        encoding="utf-8"
    )


def test_init_command_requires_clean_before_replacing_starter_files(
    tmp_path: Path,
) -> None:
    project = tmp_path / "my_dbt_project"
    project.mkdir()
    (project / "dbt_project.yml").write_text("name: my_dbt_project\n", encoding="utf-8")

    first_result = runner.invoke(
        app,
        [
            "init",
            "--project",
            str(project),
            "--chart-name",
            "monthly_revenue",
            "--dashboard-name",
            "executive",
            "--model-name",
            "fct_orders",
            "--chart-title",
            "Monthly Revenue",
            "--chart-type",
            "line",
        ],
    )
    assert first_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "init",
            "--project",
            str(project),
            "--chart-name",
            "monthly_revenue",
            "--dashboard-name",
            "executive",
            "--model-name",
            "fct_orders",
            "--chart-title",
            "Monthly Revenue",
            "--chart-type",
            "line",
        ],
    )

    assert result.exit_code == 1
    assert "Init skipped" in result.output
    assert "Re-run with --clean" in result.output


def test_init_command_clean_replaces_starter_files(tmp_path: Path) -> None:
    project = tmp_path / "my_dbt_project"
    project.mkdir()
    (project / "dbt_project.yml").write_text("name: my_dbt_project\n", encoding="utf-8")

    first_result = runner.invoke(
        app,
        [
            "init",
            "--project",
            str(project),
            "--chart-name",
            "monthly_revenue",
            "--dashboard-name",
            "executive",
            "--model-name",
            "fct_orders",
            "--chart-title",
            "Monthly Revenue",
            "--chart-type",
            "line",
        ],
    )
    assert first_result.exit_code == 0
    chart_file = project / "visualisations" / "monthly_revenue.ggsql"
    chart_file.write_text("custom content\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "init",
            "--project",
            str(project),
            "--clean",
            "--chart-name",
            "monthly_revenue",
            "--dashboard-name",
            "executive",
            "--model-name",
            "fct_revenue",
            "--chart-title",
            "Monthly Revenue",
            "--chart-type",
            "bar",
        ],
    )

    assert result.exit_code == 0
    assert "✓ kept glyf.yml" in result.output
    assert "DRAW bar" in chart_file.read_text(encoding="utf-8")
    assert "{{ ref('fct_revenue') }}" in chart_file.read_text(encoding="utf-8")


def test_list_command_outputs_discovered_assets(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = runner.invoke(app, ["list", "--project", str(project)])

    assert result.exit_code == 0
    assert "visualisations/revenue.ggsql" in result.output
    assert "dashboards/executive.yml" in result.output
    assert "fct_orders -> main.fct_orders" in result.output


def test_validate_command_passes_basic_example(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 0
    assert "Validation passed" in result.output
    assert "✓ validated dashboard specs (1)" in result.output


def test_project_dir_option_validates_simple_dbt_example(tmp_path: Path) -> None:
    project = copy_simple_dbt_project(tmp_path)

    result = runner.invoke(app, ["validate", "--project-dir", str(project)])

    assert result.exit_code == 0
    assert "Validation passed" in result.output


def test_render_command_outputs_pipeline_steps(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = runner.invoke(app, ["render", "--project", str(project)])

    assert result.exit_code == 0
    assert "✓ discovered charts (1)" in result.output
    assert "✓ compiled SQL" in result.output
    assert "✓ executed SQL" in result.output
    assert "✓ rendered PNG/SVG" in result.output
    assert "✓ wrote metadata" in result.output
    assert (project / "target" / "glyf" / "compiled" / "revenue.sql").exists()


def test_build_command_runs_full_pipeline(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = runner.invoke(app, ["build", "--project", str(project), "--zip"])

    assert result.exit_code == 0
    assert "✓ validated project" in result.output
    assert "✓ rendered chart artifacts" in result.output
    assert "✓ generated dashboard HTML" in result.output
    assert "✓ exported static site" in result.output
    assert "✓ compiled SQL" not in result.output
    assert (project / "target" / "glyf" / "site" / "index.html").exists()
    assert (project / "target" / "glyf" / "glyf-site.zip").exists()


def test_build_verbose_outputs_low_level_pipeline_steps(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = runner.invoke(app, ["build", "--project", str(project), "--verbose"])

    assert result.exit_code == 0
    assert "Running validate" in result.output
    assert "Validation passed" in result.output
    assert "✓ validated dashboard specs (1)" in result.output
    assert "Running render" in result.output
    assert "✓ compiled SQL" in result.output
    assert "Running dashboard" in result.output
    assert "✓ generated dashboard HTML" in result.output
    assert "✓ wrote bundle manifest" in result.output
    assert "Running export" in result.output
    assert "✓ wrote public bundle manifest" in result.output
    assert "✓ exported site to target/glyf/site" in result.output


def test_dashboard_command_outputs_pipeline_steps(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_result = runner.invoke(app, ["render", "--project", str(project)])
    assert render_result.exit_code == 0

    result = runner.invoke(app, ["dashboard", "--project", str(project)])

    assert result.exit_code == 0
    assert "✓ discovered dashboard configs" in result.output
    assert "✓ loaded chart artifacts" in result.output
    assert "✓ generated dashboard HTML" in result.output
    assert "✓ generated index page" in result.output
    assert "✓ wrote bundle manifest" in result.output
    assert (project / "target" / "glyf" / "dashboards" / "executive.html").exists()
    assert (project / "target" / "glyf" / "index.html").exists()
    assert (project / "target" / "glyf" / "bundle.json").exists()


def test_export_command_outputs_pipeline_steps(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    render_result = runner.invoke(app, ["render", "--project", str(project)])
    assert render_result.exit_code == 0
    dashboard_result = runner.invoke(app, ["dashboard", "--project", str(project)])
    assert dashboard_result.exit_code == 0

    result = runner.invoke(app, ["export", "--project", str(project), "--zip"])

    assert result.exit_code == 0
    assert "✓ copied dashboard HTML" in result.output
    assert "✓ copied chart artifacts" in result.output
    assert "✓ wrote site assets" in result.output
    assert "✓ wrote public bundle manifest" in result.output
    assert (project / "target" / "glyf" / "site" / "index.html").exists()
    assert (project / "target" / "glyf" / "site" / "bundle.json").exists()
    assert (project / "target" / "glyf" / "glyf-site.zip").exists()


@pytest.mark.parametrize(
    "command",
    ["list", "validate", "render", "build", "dashboard", "export", "serve"],
)
def test_commands_report_config_errors(tmp_path: Path, command: str) -> None:
    project = copy_basic_project(tmp_path)
    config = project / "bad_config.yml"
    config.write_text("[]\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [command, "--project", str(project), "--config", str(config)],
    )

    assert result.exit_code == 1
    assert "Config error" in result.output
    assert "Invalid config: expected a YAML mapping" in result.output


def test_render_command_reports_pipeline_errors(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select month, revenue from {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW heatmap\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["render", "--project", str(project)])

    assert result.exit_code == 1
    assert "Render failed" in result.output
    assert "unsupported chart type 'heatmap'" in result.output


def test_dashboard_command_reports_missing_chart_artifacts(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    chart_artifact = project / "target" / "glyf" / "charts" / "revenue.json"
    chart_artifact.parent.mkdir(parents=True, exist_ok=True)
    chart_artifact.write_text('{"test": "data"}', encoding="utf-8")
    chart_artifact.unlink()

    result = runner.invoke(app, ["dashboard", "--project", str(project)])

    assert result.exit_code == 1
    assert "Dashboard generation failed" in result.output
    assert "missing chart metadata" in result.output


def test_export_command_reports_missing_generated_outputs(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    index_file = project / "target" / "glyf" / "index.html"
    index_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text("<html></html>", encoding="utf-8")
    index_file.unlink()

    result = runner.invoke(app, ["export", "--project", str(project)])

    assert result.exit_code == 1
    assert "Export failed" in result.output
    assert "Missing generated outputs" in result.output


def test_serve_command_reports_missing_site(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = runner.invoke(app, ["serve", "--project", str(project)])

    assert result.exit_code == 1
    assert "Serve failed" in result.output
    assert "run `glyf build` or `glyf export` first" in result.output


def test_serve_command_serves_generated_site(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = copy_basic_project(tmp_path)
    site_dir = project / "target" / "glyf" / "site"
    site_dir.mkdir(parents=True)
    (site_dir / "index.html").write_text("<h1>glyf</h1>", encoding="utf-8")

    class FakeHttpServer:
        def __init__(self) -> None:
            self.served = False
            self.closed = False

        def serve_forever(self) -> None:
            self.served = True

        def server_close(self) -> None:
            self.closed = True

    captured: dict[str, FakeHttpServer] = {}

    def fake_create_server(target: object) -> SimpleNamespace:
        server = FakeHttpServer()
        captured["server"] = server
        return SimpleNamespace(target=target, server=server)

    monkeypatch.setattr("glyf.commands.serve_cmd.create_server", fake_create_server)

    result = runner.invoke(
        app,
        ["serve", "--project", str(project), "--port", "8123"],
    )

    assert result.exit_code == 0
    assert "Serving target/glyf/site" in result.output
    assert "Open http://127.0.0.1:8123/" in result.output
    assert "Press Ctrl+C to stop." in result.output
    assert captured["server"].served
    assert captured["server"].closed


def test_validate_command_reports_malformed_ggsql(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select 1\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "Validation failed" in result.output
    assert "missing VISUALISE section" in result.output


def test_validate_command_reports_unsupported_interaction(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select month, revenue from {{ ref('fct_orders') }}\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW line\n"
        "INTERACT brush\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "unsupported interaction 'brush'" in result.output


def test_validate_command_reports_unresolved_ref(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "visualisations" / "revenue.ggsql").write_text(
        "select * from {{ ref('missing_model') }}\n\n"
        "VISUALISE month AS x, revenue AS y\n"
        "DRAW line\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "unknown model 'missing_model'" in result.output


def test_validate_command_reports_unresolved_source(tmp_path: Path) -> None:
    project = copy_simple_dbt_project(tmp_path)
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
    project = copy_basic_project(tmp_path)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\ntitle: Executive Dashboard\ncharts:\n  - missing_chart\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "unknown chart 'missing_chart'" in result.output


def test_validate_command_reports_invalid_section_chart_reference(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "dashboards" / "executive.yml").write_text(
        "name: executive\n"
        "title: Executive Dashboard\n"
        "sections:\n"
        "  - title: Missing chart section\n"
        "    items:\n"
        "      - chart: missing_chart\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "unknown chart 'missing_chart'" in result.output


def test_validate_command_reports_missing_manifest(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "target" / "manifest.json").unlink()

    result = runner.invoke(app, ["validate", "--project", str(project)])

    assert result.exit_code == 1
    assert "Missing target/manifest.json" in result.output


def test_validate_command_reports_missing_dbt_project(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "dbt_project.yml").unlink()

    result = runner.invoke(app, ["validate", "--project-dir", str(project)])

    assert result.exit_code == 1
    assert "Missing dbt_project.yml" in result.output


def test_version_flag_prints_package_version() -> None:
    from glyf import __version__

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == f"glyf {__version__}"
