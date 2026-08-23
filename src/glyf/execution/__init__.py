"""SQL execution helpers.

Executors register themselves under a name via ``@sql_executor``. Importing the
concrete modules here is what populates the registry, so they are imported for
their side effects.
"""

from glyf.execution.base import (
    SqlExecutionError,
    SqlExecutor,
    execute_sql,
    get_sql_executor,
    sql_executor,
)
from glyf.execution.result import QueryResult

from . import duckdb_adbc as _duckdb_adbc  # noqa: F401
from . import duckdb_dbapi as _duckdb_dbapi  # noqa: F401

__all__ = [
    "QueryResult",
    "SqlExecutionError",
    "SqlExecutor",
    "execute_sql",
    "get_sql_executor",
    "sql_executor",
]
