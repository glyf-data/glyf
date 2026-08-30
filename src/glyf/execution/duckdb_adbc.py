"""DuckDB executor using ADBC, fetching results as Arrow without a copy."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import adbc_driver_manager.dbapi

from glyf.config import ExecutionConfig
from glyf.execution.base import SqlExecutionError, sql_executor
from glyf.execution.duckdb_support import duckdb_database, load_seed_tables
from glyf.execution.result import QueryResult


class AdbcDuckDbExecutor:
    def __init__(self, database: str | None = None) -> None:
        # None means "find the project's database"; the dbt backend passes the
        # path the profile names instead of guessing.
        self._database = database

    def execute(self, project_root: Path, sql: str) -> QueryResult:
        database = self._database or duckdb_database(project_root)
        try:
            with adbc_driver_manager.dbapi.connect(
                driver=_duckdb_driver_path(),
                entrypoint="duckdb_adbc_init",
                db_kwargs=_duckdb_connection_kwargs(database),
            ) as connection:
                if database == ":memory:":
                    load_seed_tables(connection, project_root / "seeds")
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    return QueryResult.from_arrow(cursor.fetch_arrow_table())
        except Exception as exc:
            raise SqlExecutionError(str(exc)) from exc


@sql_executor("duckdb")
@sql_executor("duckdb_adbc")
def _duckdb_adbc_executor(config: ExecutionConfig) -> AdbcDuckDbExecutor:
    return AdbcDuckDbExecutor()


def _duckdb_driver_path() -> str:
    duckdb_module_spec = importlib.util.find_spec("_duckdb")
    if duckdb_module_spec is None or duckdb_module_spec.origin is None:
        raise SqlExecutionError(
            "Could not find DuckDB shared library for the ADBC executor"
        )
    return duckdb_module_spec.origin


def _duckdb_connection_kwargs(database: str) -> dict[str, str]:
    if database == ":memory:":
        return {}
    return {"path": database}
