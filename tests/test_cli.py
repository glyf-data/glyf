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
