"""The trino executor: profile fields to a connection, rows to a QueryResult.

No Trino server here. `trino.dbapi.connect` is monkeypatched to a fake that
records what it was given and serves canned rows, so these tests pin the
mapping from a dbt-trino target to connection arguments. The real-server path
runs in test_trino_integration.py behind GLYF_TRINO_HOST.
"""

from pathlib import Path
from typing import Any

import pytest
import trino.auth
import trino.dbapi

from glyf.config import ExecutionConfig
from glyf.execution import SqlExecutionError, execute_sql

QUERY = "select month, revenue from analytics.marts.fct_orders"

PROFILES = """\
warehouse:
  target: trino
  outputs:
    trino:
      type: trino
      host: trino.example.com
      port: 8080
      user: analyst
      database: analytics
      schema: marts
    ldap:
      type: trino
      method: ldap
      host: trino.example.com
      port: 443
      user: analyst
      password: s3cret
    jwt:
      type: trino
      method: jwt
      host: trino.example.com
      port: 443
      user: analyst
      jwt_token: such-token
    oauth:
      type: trino
      method: oauth
      host: trino.example.com
      port: 443
      user: analyst
    portless:
      type: trino
      host: trino.example.com
      user: analyst
    passwordless:
      type: trino
      method: ldap
      host: trino.example.com
      port: 443
      user: analyst
"""


class FakeCursor:
    def __init__(self, description: Any, rows: Any) -> None:
        self.description = description
        self.rows = rows
        self.executed: list[str] = []

    def execute(self, sql: str) -> None:
        self.executed.append(sql)

    def fetchall(self) -> Any:
        return self.rows

    def close(self) -> None:
        pass


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
def connect_kwargs(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace trino.dbapi.connect; the dict fills with what it was given."""
    recorded: dict[str, Any] = {}
    cursor = FakeCursor(
        description=[("month",), ("revenue",)],
        rows=[("2026-01", 1200), ("2026-02", 1350)],
    )

    def fake_connect(**kwargs: Any) -> FakeConnection:
        recorded.update(kwargs)
        recorded["_cursor"] = cursor
        return FakeConnection(cursor)

    monkeypatch.setattr(trino.dbapi, "connect", fake_connect)
    return recorded


def _execute(project: Path, target: str | None = None) -> Any:
    return execute_sql(
        project,
        QUERY,
        executor="dbt",
        config=ExecutionConfig(backend="dbt", target=target),
    )


def test_a_trino_profile_executes_and_returns_rows(
    tmp_path: Path, connect_kwargs: dict[str, Any]
) -> None:
    result = _execute(_project(tmp_path))

    assert connect_kwargs["_cursor"].executed == [QUERY]
    assert list(result.rows) == [
        {"month": "2026-01", "revenue": 1200},
        {"month": "2026-02", "revenue": 1350},
    ]


def test_the_profile_fields_reach_the_connection(
    tmp_path: Path, connect_kwargs: dict[str, Any]
) -> None:
    """dbt-trino's `database` is the catalog; no auth defaults to plain http."""
    _execute(_project(tmp_path))

    assert connect_kwargs["host"] == "trino.example.com"
    assert connect_kwargs["port"] == 8080
    assert connect_kwargs["user"] == "analyst"
    assert connect_kwargs["catalog"] == "analytics"
    assert connect_kwargs["schema"] == "marts"
    assert connect_kwargs["http_scheme"] == "http"
    assert "auth" not in connect_kwargs


def test_ldap_authenticates_with_the_password_over_https(
    tmp_path: Path, connect_kwargs: dict[str, Any]
) -> None:
    _execute(_project(tmp_path), target="ldap")

    assert isinstance(connect_kwargs["auth"], trino.auth.BasicAuthentication)
    assert connect_kwargs["http_scheme"] == "https"


def test_jwt_authenticates_with_the_token(
    tmp_path: Path, connect_kwargs: dict[str, Any]
) -> None:
    _execute(_project(tmp_path), target="jwt")

    assert isinstance(connect_kwargs["auth"], trino.auth.JWTAuthentication)
    assert connect_kwargs["http_scheme"] == "https"


def test_an_unsupported_auth_method_names_itself(tmp_path: Path) -> None:
    """Falling back to no auth would connect as somebody unauthenticated."""
    with pytest.raises(SqlExecutionError, match="auth method 'oauth'"):
        _execute(_project(tmp_path), target="oauth")


def test_a_missing_port_is_reported_with_its_target(tmp_path: Path) -> None:
    with pytest.raises(SqlExecutionError, match="target 'portless'.*integer 'port'"):
        _execute(_project(tmp_path), target="portless")


def test_ldap_without_a_password_fails_loudly(tmp_path: Path) -> None:
    with pytest.raises(SqlExecutionError, match="uses 'ldap' but has no 'password'"):
        _execute(_project(tmp_path), target="passwordless")


def test_a_missing_driver_says_how_to_install_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("trino", "trino.dbapi", "trino.auth"):
        monkeypatch.setitem(__import__("sys").modules, name, None)

    with pytest.raises(SqlExecutionError, match=r"glyf-core\[trino\]"):
        _execute(_project(tmp_path))


def test_a_connection_failure_surfaces_as_an_execution_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(**kwargs: Any) -> None:
        raise ConnectionError("connection refused")

    monkeypatch.setattr(trino.dbapi, "connect", refuse)

    with pytest.raises(SqlExecutionError, match="connection refused"):
        _execute(_project(tmp_path))


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    (project / "dbt_project.yml").write_text(
        "name: warehouse\nprofile: warehouse\n", encoding="utf-8"
    )
    (project / "profiles.yml").write_text(PROFILES, encoding="utf-8")
    return project
