"""The Snowflake executor: profile fields to ADBC options, Arrow to QueryResult.

No warehouse here. `adbc_driver_snowflake.dbapi.connect` is monkeypatched to a
fake that records the `db_kwargs` it was given and serves a canned Arrow
table, so these tests pin the mapping from a dbt-snowflake target onto the
driver's own option keys. The real-warehouse path is manual:
tests/test_warehouse_manual.py.
"""

from pathlib import Path
from typing import Any

import adbc_driver_snowflake.dbapi
import pyarrow as pa
import pytest

from glyf.config import ExecutionConfig
from glyf.execution import SqlExecutionError, execute_sql

OPTIONS = adbc_driver_snowflake.DatabaseOptions
AUTH = adbc_driver_snowflake.AuthType

QUERY = "select month, revenue from analytics.marts.fct_orders"

PROFILES = """\
warehouse:
  target: password
  outputs:
    password:
      type: snowflake
      account: acme-analytics
      user: analyst
      password: s3cret
      database: analytics
      warehouse: transforming
      schema: marts
      role: reporter
    keypair:
      type: snowflake
      account: acme-analytics
      user: analyst
      private_key_path: /keys/snowflake.p8
      private_key_passphrase: opensesame
      database: analytics
    browser:
      type: snowflake
      account: acme-analytics
      user: analyst
      authenticator: externalbrowser
    oauth:
      type: snowflake
      account: acme-analytics
      user: analyst
      authenticator: oauth
      token: such-token
    okta:
      type: snowflake
      account: acme-analytics
      user: analyst
      authenticator: https://acme.okta.com
    credentialless:
      type: snowflake
      account: acme-analytics
      user: analyst
    accountless:
      type: snowflake
      user: analyst
      password: s3cret
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
    """Replace the driver's connect; the dict fills with what it was given."""
    recorded: dict[str, Any] = {}
    cursor = FakeCursor()

    def fake_connect(db_kwargs: dict[str, str] | None = None, **_: Any) -> FakeConnection:
        recorded.update(db_kwargs or {})
        recorded["_cursor"] = cursor
        return FakeConnection(cursor)

    monkeypatch.setattr(adbc_driver_snowflake.dbapi, "connect", fake_connect)
    return recorded


def _execute(project: Path, target: str | None = None) -> Any:
    return execute_sql(
        project,
        QUERY,
        executor="dbt",
        config=ExecutionConfig(backend="dbt", target=target),
    )


def test_a_snowflake_profile_executes_and_returns_rows(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    result = _execute(_project(tmp_path))

    assert db_kwargs["_cursor"].executed == [QUERY]
    assert list(result.rows) == [{"month": "2026-01", "revenue": 1200}]


def test_password_auth_maps_onto_the_drivers_own_option_keys(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    _execute(_project(tmp_path))

    assert db_kwargs[OPTIONS.ACCOUNT.value] == "acme-analytics"
    assert db_kwargs["username"] == "analyst"
    assert db_kwargs["password"] == "s3cret"
    assert db_kwargs[OPTIONS.DATABASE.value] == "analytics"
    assert db_kwargs[OPTIONS.WAREHOUSE.value] == "transforming"
    assert db_kwargs[OPTIONS.SCHEMA.value] == "marts"
    assert db_kwargs[OPTIONS.ROLE.value] == "reporter"
    assert OPTIONS.AUTH_TYPE.value not in db_kwargs, "password is the default"


def test_a_key_pair_selects_jwt_auth(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    _execute(_project(tmp_path), target="keypair")

    assert db_kwargs[OPTIONS.AUTH_TYPE.value] == AUTH.JWT.value
    assert db_kwargs[OPTIONS.JWT_PRIVATE_KEY.value] == "/keys/snowflake.p8"
    assert db_kwargs[OPTIONS.JWT_PRIVATE_KEY_PASSWORD.value] == "opensesame"
    assert "password" not in db_kwargs


def test_externalbrowser_selects_browser_auth(
    tmp_path: Path, db_kwargs: dict[str, Any]
) -> None:
    _execute(_project(tmp_path), target="browser")

    assert db_kwargs[OPTIONS.AUTH_TYPE.value] == AUTH.EXTERNAL_BROWSER.value


def test_oauth_carries_the_token(tmp_path: Path, db_kwargs: dict[str, Any]) -> None:
    _execute(_project(tmp_path), target="oauth")

    assert db_kwargs[OPTIONS.AUTH_TYPE.value] == AUTH.OAUTH.value
    assert db_kwargs[OPTIONS.AUTH_TOKEN.value] == "such-token"


def test_an_unsupported_authenticator_names_itself(tmp_path: Path) -> None:
    with pytest.raises(SqlExecutionError, match="authenticator 'https://acme.okta.com'"):
        _execute(_project(tmp_path), target="okta")


def test_no_credentials_at_all_fails_loudly(tmp_path: Path) -> None:
    with pytest.raises(SqlExecutionError, match="has no 'password'"):
        _execute(_project(tmp_path), target="credentialless")


def test_a_missing_account_is_reported_with_its_target(tmp_path: Path) -> None:
    with pytest.raises(SqlExecutionError, match="target 'accountless'.*no 'account'"):
        _execute(_project(tmp_path), target="accountless")


def test_a_missing_driver_says_how_to_install_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    for name in ("adbc_driver_snowflake", "adbc_driver_snowflake.dbapi"):
        monkeypatch.setitem(sys.modules, name, None)

    with pytest.raises(SqlExecutionError, match=r"glyf-core\[snowflake\]"):
        _execute(_project(tmp_path))


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    (project / "dbt_project.yml").write_text(
        "name: warehouse\nprofile: warehouse\n", encoding="utf-8"
    )
    (project / "profiles.yml").write_text(PROFILES, encoding="utf-8")
    return project
