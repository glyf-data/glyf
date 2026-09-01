"""The BigQuery executor: profile fields to ADBC options, Arrow to QueryResult.

Mirror of test_snowflake_executor.py: the driver's connect is monkeypatched,
the tests pin the mapping from a dbt-bigquery target onto the driver's own
option keys. The real-warehouse path is manual: tests/test_warehouse_manual.py.
"""

import json
from pathlib import Path
from typing import Any

import adbc_driver_bigquery.dbapi
import pyarrow as pa
import pytest

from glyf.config import ExecutionConfig
from glyf.execution import SqlExecutionError, execute_sql

OPTIONS = adbc_driver_bigquery.DatabaseOptions

QUERY = "select month, revenue from `acme-analytics`.marts.fct_orders"

PROFILES = """\
warehouse:
  target: adc
  outputs:
    adc:
      type: bigquery
      method: oauth
      project: acme-analytics
      dataset: marts
      location: EU
    aliased:
      type: bigquery
      method: oauth
      database: acme-analytics
      schema: marts
    keyfile:
      type: bigquery
      method: service-account
      project: acme-analytics
      dataset: marts
      keyfile: /keys/bigquery.json
    inline:
      type: bigquery
      method: service-account-json
      project: acme-analytics
      dataset: marts
      keyfile_json:
        type: service_account
        project_id: acme-analytics
        private_key: not-a-real-key
    secrets:
      type: bigquery
      method: oauth-secrets
      project: acme-analytics
      client_id: the-id
      client_secret: the-secret
      refresh_token: the-refresh
    impersonated:
      type: bigquery
      method: oauth-secrets-and-mirrors
      project: acme-analytics
    projectless:
      type: bigquery
      method: oauth
      dataset: marts
    keyfileless:
      type: bigquery
      method: service-account
      project: acme-analytics
"""


class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def execute(self, sql: str) -> None:
        self.executed.append(sql)

    def fetch_arrow_table(self) -> pa.Table:
        return pa.table({"month": ["2026-01"], "revenue": [1200]})


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def cursor(self) -> FakeCursor:
        return self._cursor


@pytest.fixture(autouse=True)
def _clean_dbt_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DBT_PROFILES_DIR", raising=False)
    monkeypatch.delenv("DBT_TARGET", raising=False)


@pytest.fixture()
def db_kwargs(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    recorded: dict[str, Any] = {}
    cursor = FakeCursor()

    def fake_connect(db_kwargs: dict[str, str] | None = None, **_: Any) -> FakeConnection:
        recorded.update(db_kwargs or {})
        recorded["_cursor"] = cursor
        return FakeConnection(cursor)

    monkeypatch.setattr(adbc_driver_bigquery.dbapi, "connect", fake_connect)
    return recorded


def _execute(project: Path, target: str | None = None) -> Any:
    return execute_sql(
        project,
        QUERY,
        executor="dbt",
        config=ExecutionConfig(backend="dbt", target=target),
    )


def test_a_bigquery_profile_executes_and_returns_rows(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    result = _execute(_project(tmp_path))

    assert db_kwargs["_cursor"].executed == [QUERY]
    assert list(result.rows) == [{"month": "2026-01", "revenue": 1200}]


def test_oauth_uses_application_default_credentials(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    _execute(_project(tmp_path))

    assert db_kwargs[OPTIONS.PROJECT_ID.value] == "acme-analytics"
    assert db_kwargs[OPTIONS.DATASET_ID.value] == "marts"
    assert db_kwargs[OPTIONS.LOCATION.value] == "EU"
    assert db_kwargs[OPTIONS.AUTH_TYPE.value] == OPTIONS.AUTH_VALUE_BIGQUERY.value


def test_dbts_database_and_schema_aliases_are_honoured(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    """dbt-bigquery accepts database/schema for project/dataset; so does glyf."""
    _execute(_project(tmp_path), target="aliased")

    assert db_kwargs[OPTIONS.PROJECT_ID.value] == "acme-analytics"
    assert db_kwargs[OPTIONS.DATASET_ID.value] == "marts"


def test_a_service_account_keyfile_is_passed_as_a_file(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    _execute(_project(tmp_path), target="keyfile")

    assert (
        db_kwargs[OPTIONS.AUTH_TYPE.value]
        == OPTIONS.AUTH_VALUE_JSON_CREDENTIAL_FILE.value
    )
    assert db_kwargs[OPTIONS.AUTH_CREDENTIALS.value] == "/keys/bigquery.json"


def test_an_inline_keyfile_is_passed_as_json(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    _execute(_project(tmp_path), target="inline")

    assert (
        db_kwargs[OPTIONS.AUTH_TYPE.value]
        == OPTIONS.AUTH_VALUE_JSON_CREDENTIAL_STRING.value
    )
    credentials = json.loads(db_kwargs[OPTIONS.AUTH_CREDENTIALS.value])
    assert credentials["project_id"] == "acme-analytics"


def test_oauth_secrets_carry_all_three_fields(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    _execute(_project(tmp_path), target="secrets")

    assert (
        db_kwargs[OPTIONS.AUTH_TYPE.value]
        == OPTIONS.AUTH_VALUE_USER_AUTHENTICATION.value
    )
    assert db_kwargs[OPTIONS.AUTH_CLIENT_ID.value] == "the-id"
    assert db_kwargs[OPTIONS.AUTH_CLIENT_SECRET.value] == "the-secret"
    assert db_kwargs[OPTIONS.AUTH_REFRESH_TOKEN.value] == "the-refresh"


def test_an_unsupported_method_names_itself(tmp_path: Path) -> None:
    with pytest.raises(
        SqlExecutionError, match="auth method 'oauth-secrets-and-mirrors'"
    ):
        _execute(_project(tmp_path), target="impersonated")


def test_a_missing_project_is_reported_with_its_target(tmp_path: Path) -> None:
    with pytest.raises(SqlExecutionError, match="target 'projectless'.*no 'project'"):
        _execute(_project(tmp_path), target="projectless")


def test_a_service_account_without_a_keyfile_fails_loudly(tmp_path: Path) -> None:
    with pytest.raises(SqlExecutionError, match="no 'keyfile'"):
        _execute(_project(tmp_path), target="keyfileless")


def test_a_missing_driver_says_how_to_install_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    for name in ("adbc_driver_bigquery", "adbc_driver_bigquery.dbapi"):
        monkeypatch.setitem(sys.modules, name, None)

    with pytest.raises(SqlExecutionError, match=r"glyf-core\[bigquery\]"):
        _execute(_project(tmp_path))


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    (project / "dbt_project.yml").write_text(
        "name: warehouse\nprofile: warehouse\n", encoding="utf-8"
    )
    (project / "profiles.yml").write_text(PROFILES, encoding="utf-8")
    return project
