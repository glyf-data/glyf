"""Snowflake executor over ADBC, fetching results as Arrow without a copy.

The route ARCHITECTURE.md records: `adbc-driver-manager` is already a runtime
dependency and `QueryResult` holds Arrow, so a Snowflake executor is the same
shape as the DuckDB one with a different `connect()`. The driver itself is an
optional extra (`glyf-core[snowflake]`) so other installs pay nothing for it.

Connection settings come from the project's resolved dbt profile and follow
dbt-snowflake's field names. The auth methods glyf honours are password (the
default), key-pair (`private_key_path`, with an optional passphrase),
`authenticator: externalbrowser`, and `authenticator: oauth` with a `token`;
anything else fails loudly rather than connecting as somebody unauthenticated.
`QueryResult` already casts Snowflake's NUMBER decimals to native types.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

from glyf.execution.base import SqlExecutionError
from glyf.execution.result import QueryResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from glyf.execution.dbt_profile import DbtProfile


class AdbcSnowflakeExecutor:
    def __init__(self, db_kwargs: Mapping[str, str]) -> None:
        # Built by `snowflake_from_profile`; holds credentials, so it must
        # never appear in an error.
        self._db_kwargs = dict(db_kwargs)

    def execute(self, project_root: Path, sql: str) -> QueryResult:
        driver = _import_driver()
        try:
            with driver.dbapi.connect(db_kwargs=self._db_kwargs) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    return QueryResult.from_arrow(cursor.fetch_arrow_table())
        except Exception as exc:
            raise SqlExecutionError(str(exc)) from exc


def snowflake_from_profile(profile: "DbtProfile") -> AdbcSnowflakeExecutor:
    """Build a Snowflake executor from a resolved dbt-snowflake target."""
    driver = _import_driver()
    options = driver.DatabaseOptions
    auth_types = driver.AuthType
    where = (
        f"{profile.profiles_path}: target '{profile.target}' of profile "
        f"'{profile.name}'"
    )

    db_kwargs: dict[str, str] = {
        options.ACCOUNT.value: _required_str(profile, "account", where),
        "username": _required_str(profile, "user", where),
    }

    for field, option in (
        ("database", options.DATABASE),
        ("warehouse", options.WAREHOUSE),
        ("schema", options.SCHEMA),
        ("role", options.ROLE),
    ):
        value = profile.config.get(field)
        if isinstance(value, str) and value:
            db_kwargs[option.value] = value

    authenticator = profile.config.get("authenticator")
    private_key_path = profile.config.get("private_key_path")
    password = profile.config.get("password")

    if isinstance(private_key_path, str) and private_key_path:
        db_kwargs[options.AUTH_TYPE.value] = auth_types.JWT.value
        db_kwargs[options.JWT_PRIVATE_KEY.value] = private_key_path
        passphrase = profile.config.get("private_key_passphrase")
        if isinstance(passphrase, str) and passphrase:
            db_kwargs[options.JWT_PRIVATE_KEY_PASSWORD.value] = passphrase
    elif authenticator == "externalbrowser":
        db_kwargs[options.AUTH_TYPE.value] = auth_types.EXTERNAL_BROWSER.value
    elif authenticator == "oauth":
        token = profile.config.get("token")
        if not isinstance(token, str) or not token:
            raise SqlExecutionError(f"{where} uses 'oauth' but has no 'token'")
        db_kwargs[options.AUTH_TYPE.value] = auth_types.OAUTH.value
        db_kwargs[options.AUTH_TOKEN.value] = token
    elif authenticator is not None:
        raise SqlExecutionError(
            f"{where} uses authenticator '{authenticator}', which glyf cannot "
            "honour yet. Supported: password, key-pair (private_key_path), "
            "externalbrowser, oauth."
        )
    else:
        if not isinstance(password, str) or not password:
            raise SqlExecutionError(
                f"{where} has no 'password' (or 'private_key_path' or "
                "'authenticator') to connect with"
            )
        db_kwargs["password"] = password

    return AdbcSnowflakeExecutor(db_kwargs)


def _required_str(profile: "DbtProfile", key: str, where: str) -> str:
    value = profile.config.get(key)
    if not isinstance(value, str) or not value:
        raise SqlExecutionError(f"{where} has no '{key}'")
    return value


def _import_driver() -> Any:
    try:
        import adbc_driver_snowflake.dbapi  # noqa: F401
    except ImportError as exc:
        raise SqlExecutionError(
            "The Snowflake ADBC driver is not installed. "
            "Install it with: pip install 'glyf-core[snowflake]'"
        ) from exc
    return adbc_driver_snowflake
