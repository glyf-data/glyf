from pathlib import Path

from typer.testing import CliRunner

from glyf.cli import app
from glyf.doctor import run_doctor_checks
from tests.helpers import copy_basic_project


runner = CliRunner()


def test_doctor_checks_pass_for_basic_project(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = run_doctor_checks(project)

    assert result.has_errors is False
    statuses = {check.name: check.status for check in result.checks}
    assert statuses["dbt_project.yml"] == "ok"
    assert statuses["manifest.json"] == "ok"
    assert statuses["visualisation files"] == "ok"
    assert statuses["dashboard files"] == "ok"


def test_doctor_checks_report_missing_required_files(tmp_path: Path) -> None:
    project = tmp_path / "empty"
    project.mkdir()

    result = run_doctor_checks(project)

    assert result.has_errors is True
    errors = [check.message for check in result.checks if check.status == "error"]
    assert any("missing dbt_project.yml" in message for message in errors)
    assert any("missing target/manifest.json" in message for message in errors)


def test_doctor_command_outputs_checks(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = runner.invoke(app, ["doctor", "--project-dir", str(project)])

    assert result.exit_code == 0
    assert "[OK] dbt_project.yml" in result.output
    assert "[OK] manifest.json" in result.output


def test_doctor_command_exits_nonzero_for_broken_project(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path, "broken")
    (project / "target" / "manifest.json").unlink()

    result = runner.invoke(app, ["doctor", "--project-dir", str(project)])

    assert result.exit_code == 1
    assert "[ERROR] manifest.json" in result.output


def test_doctor_probes_execution_on_the_default_backend(tmp_path: Path) -> None:
    """A misconfigured backend should surface here rather than mid-render."""
    project = copy_basic_project(tmp_path)

    result = run_doctor_checks(project)

    statuses = {check.name: check.status for check in result.checks}
    assert statuses["execution backend"] == "ok"
    assert statuses["execution probe"] == "ok"


def test_doctor_reports_the_dbt_profile_it_resolved(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "dbt_project.yml").write_text(
        "name: basic\nprofile: basic\n", encoding="utf-8"
    )
    (project / "profiles.yml").write_text(
        "basic:\n"
        "  target: dev\n"
        "  outputs:\n"
        "    dev:\n"
        "      type: duckdb\n"
        '      path: ":memory:"\n',
        encoding="utf-8",
    )
    (project / "glyf.yml").write_text(
        "execution:\n  backend: dbt\n", encoding="utf-8"
    )

    result = run_doctor_checks(project)

    checks = {check.name: check for check in result.checks}
    assert checks["dbt profile"].status == "ok"
    assert "profile 'basic' target 'dev' (type: duckdb)" in checks["dbt profile"].message
    assert checks["execution probe"].status == "ok"


def test_doctor_reports_a_profile_that_cannot_resolve(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "glyf.yml").write_text(
        "execution:\n  backend: dbt\n", encoding="utf-8"
    )

    result = run_doctor_checks(project)

    assert result.has_errors is True
    checks = {check.name: check for check in result.checks}
    assert checks["dbt profile"].status == "error"
    assert "execution probe" not in checks, "no probe without a profile"


def test_doctor_reports_a_missing_warehouse_driver(
    tmp_path: Path, monkeypatch
) -> None:
    """The trino target is fine; the driver extra is not installed."""
    import glyf.doctor as doctor_module

    monkeypatch.setattr(
        doctor_module,
        "_DRIVER_EXTRAS",
        {"trino": ("glyf_no_such_driver", "glyf-core[trino]")},
    )
    project = copy_basic_project(tmp_path)
    (project / "dbt_project.yml").write_text(
        "name: basic\nprofile: basic\n", encoding="utf-8"
    )
    (project / "profiles.yml").write_text(
        "basic:\n"
        "  target: prod\n"
        "  outputs:\n"
        "    prod:\n"
        "      type: trino\n"
        "      host: trino.example.com\n"
        "      port: 8080\n"
        "      user: analyst\n",
        encoding="utf-8",
    )
    (project / "glyf.yml").write_text(
        "execution:\n  backend: dbt\n", encoding="utf-8"
    )

    result = run_doctor_checks(project)

    checks = {check.name: check for check in result.checks}
    assert checks["warehouse driver"].status == "error"
    assert "glyf-core[trino]" in checks["warehouse driver"].message
    assert "execution probe" not in checks, "no probe without the driver"
