"""DuckDB executor using the native Python DB-API driver."""

from __future__ import annotations

from pathlib import Path

import duckdb

from glyf.config import ExecutionConfig
from glyf.execution.base import SqlExecutionError, sql_executor
from glyf.execution.duckdb_support import duckdb_database, load_seed_tables
from glyf.execution.result import QueryResult


class DuckDbExecutor:
    def __init__(self, database: str | None = None) -> None:
        # None means "find the project's database"; the dbt backend passes the
        # path the profile names instead of guessing.
        self._database = database

    def execute(self, project_root: Path, sql: str) -> QueryResult:
        database = self._database or duckdb_database(project_root)
        try:
            with duckdb.connect(database=database) as connection:
                if database == ":memory:":
                    load_seed_tables(connection, project_root / "seeds")
                return QueryResult.from_arrow(connection.execute(sql).to_arrow_table())
        except duckdb.Error as exc:
            raise SqlExecutionError(str(exc)) from exc


@sql_executor("duckdb_dbapi")
def _duckdb_dbapi_executor(config: ExecutionConfig) -> DuckDbExecutor:
    return DuckDbExecutor()
