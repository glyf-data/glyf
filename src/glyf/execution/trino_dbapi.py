"""Trino executor using the official DBAPI client.

Trino is the first warehouse the `dbt` backend reaches beyond DuckDB. The
route differs from the one ARCHITECTURE.md records for Snowflake and BigQuery:
there is no ADBC driver for Trino, because Trino speaks its own HTTP protocol,
so this executor uses the `trino` package -- the same client dbt-trino
connects with. It is an optional extra (`glyf-core[trino]`) so DuckDB-only
installs pay nothing for it.

Connection settings come from the project's resolved dbt profile and follow
dbt-trino's field names: `database` is the catalog, `method` is the auth
method. Only the methods glyf can honour are accepted -- `none`, `ldap`
(user and password) and `jwt` -- and anything else fails loudly rather than
connecting as somebody unauthenticated.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

import pyarrow as pa

from glyf.execution.base import SqlExecutionError
from glyf.execution.result import QueryResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from glyf.execution.dbt_profile import DbtProfile

_SUPPORTED_METHODS = ("none", "ldap", "jwt")


class TrinoExecutor:
    def __init__(self, connection_kwargs: Mapping[str, Any]) -> None:
        # Built by `trino_from_profile`; holds everything `trino.dbapi.connect`
        # needs, credentials included, so it must never appear in an error.
        self._connection_kwargs = dict(connection_kwargs)

    def execute(self, project_root: Path, sql: str) -> QueryResult:
        trino = _import_trino()
        try:
            with trino.dbapi.connect(**self._connection_kwargs) as connection:
                cursor = connection.cursor()
                try:
                    cursor.execute(sql)
                    if cursor.description is None:
                        raise SqlExecutionError(
                            "The query returned no result set; charts need a select"
                        )
                    columns = tuple(entry[0] for entry in cursor.description)
                    rows = tuple(
                        dict(zip(columns, row)) for row in cursor.fetchall()
                    )
                finally:
                    cursor.close()
        except SqlExecutionError:
            raise
        except Exception as exc:
            raise SqlExecutionError(str(exc)) from exc
        if rows:
            return QueryResult.from_records(columns, rows)
        # Zero rows still binds columns: validate mode checks a chart's fields
        # against `result.columns`, so the names must survive an empty fetch.
        return QueryResult.from_arrow(
            pa.table({column: pa.array([], type=pa.null()) for column in columns})
        )


def trino_from_profile(profile: "DbtProfile") -> TrinoExecutor:
    """Build a Trino executor from a resolved dbt-trino target."""
    trino = _import_trino()
    where = (
        f"{profile.profiles_path}: target '{profile.target}' of profile "
        f"'{profile.name}'"
    )

    host = _required_str(profile, "host", where)
    port = profile.config.get("port")
    if not isinstance(port, int):
        raise SqlExecutionError(f"{where} needs an integer 'port'")
    user = _required_str(profile, "user", where)

    method = profile.config.get("method", "none")
    if method not in _SUPPORTED_METHODS:
        supported = ", ".join(_SUPPORTED_METHODS)
        raise SqlExecutionError(
            f"{where} uses auth method '{method}', which glyf cannot honour "
            f"yet. Supported: {supported}."
        )

    kwargs: dict[str, Any] = {
        "host": host,
        "port": port,
        "user": user,
        "http_scheme": profile.config.get(
            "http_scheme", "http" if method == "none" else "https"
        ),
    }

    # dbt-trino calls the catalog `database`. Both are optional here: compiled
    # chart SQL is already warehouse-qualified by ref() resolution, but session
    # defaults keep hand-written table names working.
    catalog = profile.config.get("database")
    if isinstance(catalog, str) and catalog:
        kwargs["catalog"] = catalog
    schema = profile.config.get("schema")
    if isinstance(schema, str) and schema:
        kwargs["schema"] = schema
    session_properties = profile.config.get("session_properties")
    if isinstance(session_properties, Mapping) and session_properties:
        kwargs["session_properties"] = dict(session_properties)

    if method == "ldap":
        password = profile.config.get("password")
        if not isinstance(password, str) or not password:
            raise SqlExecutionError(f"{where} uses 'ldap' but has no 'password'")
        kwargs["auth"] = trino.auth.BasicAuthentication(user, password)
    elif method == "jwt":
        token = profile.config.get("jwt_token")
        if not isinstance(token, str) or not token:
            raise SqlExecutionError(f"{where} uses 'jwt' but has no 'jwt_token'")
        kwargs["auth"] = trino.auth.JWTAuthentication(token)

    return TrinoExecutor(kwargs)


def _required_str(profile: "DbtProfile", key: str, where: str) -> str:
    value = profile.config.get(key)
    if not isinstance(value, str) or not value:
        raise SqlExecutionError(f"{where} has no '{key}'")
    return value


def _import_trino() -> Any:
    try:
        import trino.auth  # noqa: F401
        import trino.dbapi  # noqa: F401
    except ImportError as exc:
        raise SqlExecutionError(
            "The 'trino' driver is not installed. "
            "Install it with: pip install 'glyf-core[trino]'"
        ) from exc
    return trino
