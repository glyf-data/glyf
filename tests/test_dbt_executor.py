"""Executing chart SQL through the project's dbt profile.

Phase 2: the `dbt` backend resolves `profiles.yml` and connects where the
profile points, instead of guessing at a database beside the project. Only
`type: duckdb` is dispatched today, which is enough to exercise the whole chain
-- profile discovery, target selection, dispatch -- with no warehouse.
"""

from pathlib import Path

import duckdb
import pytest

from dataclasses import replace

from glyf.config import ExecutionConfig, GlyfConfig
from glyf.execution import SqlExecutionError, execute_sql, get_sql_executor
from glyf.pipeline import render_project
from tests.helpers import copy_basic_project

QUERY = "select month, revenue from main.fct_orders order by month"

PROFILES = """\
warehouse:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: target/dev.duckdb
    other:
      type: duckdb
      path: target/other.duckdb
    memory:
      type: duckdb
      path: ":memory:"
    redshift:
      type: redshift
      host: acme.example.com
"""


@pytest.fixture(autouse=True)
def _clean_dbt_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DBT_PROFILES_DIR", raising=False)
    monkeypatch.delenv("DBT_TARGET", raising=False)


def test_executes_against_the_database_the_profile_names(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _database(project / "target" / "dev.duckdb", revenue=1200)

    result = execute_sql(project, QUERY, executor="dbt")

    assert list(result.rows) == [{"month": "2026-01", "revenue": 1200}]


def test_the_configured_target_selects_the_database(tmp_path: Path) -> None:
    """The whole point of the backend: two targets, two databases."""
    project = _project(tmp_path)
    _database(project / "target" / "dev.duckdb", revenue=1200)
    _database(project / "target" / "other.duckdb", revenue=9999)

    result = execute_sql(
        project,
        QUERY,
        executor="dbt",
        config=ExecutionConfig(backend="dbt", target="other"),
    )

    assert list(result.rows) == [{"month": "2026-01", "revenue": 9999}]


def test_an_in_memory_profile_reads_the_seeds(tmp_path: Path) -> None:
    project = _project(tmp_path)
    seeds = project / "seeds"
    seeds.mkdir()
    (seeds / "fct_orders.csv").write_text(
        "month,revenue\n2026-01,1200\n", encoding="utf-8"
    )

    result = execute_sql(
        project,
        QUERY,
        executor="dbt",
        config=ExecutionConfig(backend="dbt", target="memory"),
    )

    assert list(result.rows) == [{"month": "2026-01", "revenue": 1200}]


def test_a_missing_database_says_to_run_dbt(tmp_path: Path) -> None:
    """Connecting anyway would create an empty database and fail confusingly."""
    project = _project(tmp_path)

    with pytest.raises(SqlExecutionError, match="does not exist. Run dbt build first"):
        execute_sql(project, QUERY, executor="dbt")


def test_an_unsupported_warehouse_names_the_type(tmp_path: Path) -> None:
    project = _project(tmp_path)

    with pytest.raises(SqlExecutionError, match="uses 'redshift'"):
        execute_sql(
            project,
            QUERY,
            executor="dbt",
            config=ExecutionConfig(backend="dbt", target="redshift"),
        )


def test_a_profile_problem_surfaces_as_an_execution_error(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(SqlExecutionError, match="is this a dbt project"):
        execute_sql(project, QUERY, executor="dbt")


def test_the_profiles_directory_can_be_configured(tmp_path: Path) -> None:
    project = _project(tmp_path, with_profiles=False)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "profiles.yml").write_text(PROFILES, encoding="utf-8")
    _database(project / "target" / "dev.duckdb", revenue=1200)

    result = execute_sql(
        project,
        QUERY,
        executor="dbt",
        config=ExecutionConfig(backend="dbt", profiles_dir=elsewhere),
    )

    assert list(result.rows) == [{"month": "2026-01", "revenue": 1200}]


def test_the_backend_is_registered_and_configurable() -> None:
    executor = get_sql_executor("dbt", ExecutionConfig(backend="dbt", target="prod"))

    assert executor.__class__.__name__ == "DbtExecutor"


def test_render_project_executes_through_the_dbt_backend(tmp_path: Path) -> None:
    """End to end: `execution.backend: dbt` in glyf.yml renders a chart from the
    database profiles.yml names, with no DuckDB path guessed anywhere."""
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
        "      path: target/basic.duckdb\n",
        encoding="utf-8",
    )
    _database(project / "target" / "basic.duckdb", revenue=4242)
    config = replace(GlyfConfig(), execution=ExecutionConfig(backend="dbt"))

    result = render_project(project, config)

    revenue = [row["revenue"] for row in result.charts[0].data.rows]
    assert revenue == [4242], "the chart must come from the profile's database"


def _project(tmp_path: Path, *, with_profiles: bool = True) -> Path:
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    (project / "target").mkdir(exist_ok=True)
    (project / "dbt_project.yml").write_text(
        "name: warehouse\nprofile: warehouse\n", encoding="utf-8"
    )
    if with_profiles:
        (project / "profiles.yml").write_text(PROFILES, encoding="utf-8")
    return project


def _database(path: Path, *, revenue: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(database=path.as_posix()) as connection:
        connection.execute(
            "create table main.fct_orders as "
            f"select '2026-01' as month, {revenue} as revenue"
        )
