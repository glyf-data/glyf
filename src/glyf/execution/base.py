from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from glyf.config import ExecutionConfig
from glyf.execution.result import QueryResult


class SqlExecutionError(ValueError):
    """Raised when compiled SQL cannot be executed."""


class SqlExecutor(Protocol):
    def execute(self, project_root: Path, sql: str) -> QueryResult:
        ...


# Factories take the execution config because a backend may need more than a
# name to build itself: the `dbt` backend has a target and a profiles directory
# to honour. Backends that need nothing ignore it.
SqlExecutorFactory = Callable[[ExecutionConfig], SqlExecutor]

_EXECUTORS: dict[str, SqlExecutorFactory] = {}


def sql_executor(name: str) -> Callable[[SqlExecutorFactory], SqlExecutorFactory]:
    normalized = _normalize_name(name)

    def decorator(factory: SqlExecutorFactory) -> SqlExecutorFactory:
        _EXECUTORS[normalized] = factory
        return factory

    return decorator


def get_sql_executor(
    name: str = "duckdb",
    config: ExecutionConfig | None = None,
) -> SqlExecutor:
    normalized = _normalize_name(name)
    try:
        factory = _EXECUTORS[normalized]
    except KeyError as exc:
        available = ", ".join(sorted(_EXECUTORS)) or "none"
        raise ValueError(
            f"Unknown SQL executor '{name}'. Available: {available}"
        ) from exc
    return factory(config or ExecutionConfig())


def execute_sql(
    project_root: Path,
    sql: str,
    executor: str = "duckdb",
    config: ExecutionConfig | None = None,
) -> QueryResult:
    return get_sql_executor(executor, config).execute(project_root, sql)


def _normalize_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_")
    if not normalized:
        raise ValueError("SQL executor name must not be empty")
    return normalized
