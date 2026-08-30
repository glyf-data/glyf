"""Execute chart SQL where dbt built the models.

The `dbt` backend reads the project's `profiles.yml` and connects the way dbt
would, rather than guessing at a local DuckDB file. Today it dispatches only
`type: duckdb`; warehouse types arrive behind optional ADBC drivers, and the
reasoning for that route is in ARCHITECTURE.md.

The difference from the default `duckdb` backend is exactness. That one looks
for a database beside the project and falls back to reading the seed CSVs, which
is what makes the examples work before dbt has run. This one uses the path the
profile names, and says so when it is not there.
"""

from __future__ import annotations

from pathlib import Path

from glyf.config import ExecutionConfig
from glyf.execution.base import SqlExecutionError, SqlExecutor, sql_executor
from glyf.execution.dbt_profile import DbtProfile, DbtProfileError, load_dbt_profile
from glyf.execution.duckdb_adbc import AdbcDuckDbExecutor
from glyf.execution.result import QueryResult

IN_MEMORY = ":memory:"


class DbtExecutor:
    def __init__(
        self,
        *,
        target: str | None = None,
        profiles_dir: Path | None = None,
    ) -> None:
        self._target = target
        self._profiles_dir = profiles_dir

    def execute(self, project_root: Path, sql: str) -> QueryResult:
        try:
            profile = load_dbt_profile(
                project_root,
                profiles_dir=self._profiles_dir,
                target=self._target,
            )
        except DbtProfileError as exc:
            raise SqlExecutionError(str(exc)) from exc

        return _delegate(profile, project_root).execute(project_root, sql)


def _delegate(profile: DbtProfile, project_root: Path) -> SqlExecutor:
    if profile.type == "duckdb":
        return _duckdb_from_profile(profile, project_root)

    raise SqlExecutionError(
        f"{profile.profiles_path}: target '{profile.target}' of profile "
        f"'{profile.name}' uses '{profile.type}', which glyf cannot execute "
        "against yet. Supported: duckdb."
    )


def _duckdb_from_profile(profile: DbtProfile, project_root: Path) -> SqlExecutor:
    path = profile.config.get("path")
    if not isinstance(path, str) or not path:
        raise SqlExecutionError(
            f"{profile.profiles_path}: target '{profile.target}' of profile "
            f"'{profile.name}' has no 'path'"
        )

    if path == IN_MEMORY:
        return AdbcDuckDbExecutor(database=IN_MEMORY)

    database = Path(path)
    if not database.is_absolute():
        database = project_root / database
    if not database.exists():
        raise SqlExecutionError(
            f"{profile.profiles_path}: target '{profile.target}' points at "
            f"{database}, which does not exist. Run dbt build first."
        )
    return AdbcDuckDbExecutor(database=database.as_posix())


@sql_executor("dbt")
def _dbt_executor(config: ExecutionConfig) -> DbtExecutor:
    return DbtExecutor(target=config.target, profiles_dir=config.profiles_dir)
