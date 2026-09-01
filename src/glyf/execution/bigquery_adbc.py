"""BigQuery executor over ADBC, fetching results as Arrow without a copy.

Same shape as the Snowflake executor and the same reasoning from
ARCHITECTURE.md; the driver is an optional extra (`glyf-core[bigquery]`).

Connection settings follow dbt-bigquery's field names, aliases included:
`project` (or `database`) is the billing project, `dataset` (or `schema`) the
default dataset. The auth methods glyf honours map one-to-one onto the
driver's: `oauth` (application default credentials, dbt-bigquery's default),
`service-account` (a keyfile path), `service-account-json` (the key inline),
and `oauth-secrets` (client id, secret and refresh token). Anything else
fails loudly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

from glyf.execution.base import SqlExecutionError
from glyf.execution.result import QueryResult

if TYPE_CHECKING:  # pragma: no cover - typing only
    from glyf.execution.dbt_profile import DbtProfile


class AdbcBigQueryExecutor:
    def __init__(self, db_kwargs: Mapping[str, str]) -> None:
        # Built by `bigquery_from_profile`; holds credentials, so it must
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


def bigquery_from_profile(profile: "DbtProfile") -> AdbcBigQueryExecutor:
    """Build a BigQuery executor from a resolved dbt-bigquery target."""
    driver = _import_driver()
    options = driver.DatabaseOptions
    where = (
        f"{profile.profiles_path}: target '{profile.target}' of profile "
        f"'{profile.name}'"
    )

    project = _first_str(profile, "project", "database")
    if project is None:
        raise SqlExecutionError(f"{where} has no 'project'")
    db_kwargs: dict[str, str] = {options.PROJECT_ID.value: project}

    dataset = _first_str(profile, "dataset", "schema")
    if dataset is not None:
        db_kwargs[options.DATASET_ID.value] = dataset
    location = profile.config.get("location")
    if isinstance(location, str) and location:
        db_kwargs[options.LOCATION.value] = location

    method = profile.config.get("method", "oauth")
    if method == "oauth":
        db_kwargs[options.AUTH_TYPE.value] = options.AUTH_VALUE_BIGQUERY.value
    elif method == "service-account":
        keyfile = profile.config.get("keyfile")
        if not isinstance(keyfile, str) or not keyfile:
            raise SqlExecutionError(
                f"{where} uses 'service-account' but has no 'keyfile'"
            )
        db_kwargs[options.AUTH_TYPE.value] = (
            options.AUTH_VALUE_JSON_CREDENTIAL_FILE.value
        )
        db_kwargs[options.AUTH_CREDENTIALS.value] = keyfile
    elif method == "service-account-json":
        keyfile_json = profile.config.get("keyfile_json")
        if not isinstance(keyfile_json, Mapping) or not keyfile_json:
            raise SqlExecutionError(
                f"{where} uses 'service-account-json' but has no 'keyfile_json'"
            )
        db_kwargs[options.AUTH_TYPE.value] = (
            options.AUTH_VALUE_JSON_CREDENTIAL_STRING.value
        )
        db_kwargs[options.AUTH_CREDENTIALS.value] = json.dumps(dict(keyfile_json))
    elif method == "oauth-secrets":
        db_kwargs[options.AUTH_TYPE.value] = (
            options.AUTH_VALUE_USER_AUTHENTICATION.value
        )
        for field, option in (
            ("client_id", options.AUTH_CLIENT_ID),
            ("client_secret", options.AUTH_CLIENT_SECRET),
            ("refresh_token", options.AUTH_REFRESH_TOKEN),
        ):
            value = profile.config.get(field)
            if not isinstance(value, str) or not value:
                raise SqlExecutionError(
                    f"{where} uses 'oauth-secrets' but has no '{field}'"
                )
            db_kwargs[option.value] = value
    else:
        raise SqlExecutionError(
            f"{where} uses auth method '{method}', which glyf cannot honour "
            "yet. Supported: oauth, service-account, service-account-json, "
            "oauth-secrets."
        )

    return AdbcBigQueryExecutor(db_kwargs)


def _first_str(profile: "DbtProfile", *keys: str) -> str | None:
    for key in keys:
        value = profile.config.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _import_driver() -> Any:
    try:
        import adbc_driver_bigquery.dbapi  # noqa: F401
    except ImportError as exc:
        raise SqlExecutionError(
            "The BigQuery ADBC driver is not installed. "
            "Install it with: pip install 'glyf-core[bigquery]'"
        ) from exc
    return adbc_driver_bigquery
