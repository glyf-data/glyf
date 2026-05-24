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
