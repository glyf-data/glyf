from pathlib import Path

from glyf.config import ExecutionConfig
from glyf.execution.dialect import sql_dialect
from tests.helpers import copy_basic_project


def test_duckdb_backends_read_duckdb_sql(tmp_path: Path) -> None:
    for backend in ("duckdb", "duckdb_adbc", "duckdb_dbapi"):
        assert sql_dialect(tmp_path, ExecutionConfig(backend=backend)) == "duckdb"


def test_dbt_backend_follows_the_profile_target_type(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    (project / "dbt_project.yml").write_text("name: basic\nprofile: basic\n", encoding="utf-8")
    (project / "profiles.yml").write_text(
        "basic:\n  target: dev\n  outputs:\n"
        "    dev:\n      type: snowflake\n      account: a\n"
        "    warehouse:\n      type: bigquery\n      project: p\n"
        "    lake:\n      type: trino\n      host: h\n",
        encoding="utf-8",
    )
    dbt = ExecutionConfig(backend="dbt")
    assert sql_dialect(project, dbt) == "snowflake"
    assert sql_dialect(project, ExecutionConfig(backend="dbt", target="warehouse")) == "bigquery"
    assert sql_dialect(project, ExecutionConfig(backend="dbt", target="lake")) == "generic"


def test_an_unreadable_profile_is_generic_not_an_error(tmp_path: Path) -> None:
    assert sql_dialect(tmp_path, ExecutionConfig(backend="dbt")) == "generic"
