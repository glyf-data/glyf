"""Resolving a dbt project's connection profile.

Phase 1 of executing chart SQL where dbt built the models: work out which
profile and target a project uses, and read the target's settings. Nothing here
opens a connection.
"""

from pathlib import Path

import pytest

from glyf.execution.dbt_profile import (
    DbtProfileError,
    load_dbt_profile,
    profiles_search_path,
)

PROFILES = """\
warehouse:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: target/dev.duckdb
    prod:
      type: postgres
      host: db.example.com
      port: "{{ env_var('PGPORT', '5432') }}"
      user: reporting
      password: "{{ env_var('PGPASSWORD') }}"
"""


@pytest.fixture(autouse=True)
def _clean_dbt_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """dbt's own environment variables must not leak into these tests."""
    monkeypatch.delenv("DBT_PROFILES_DIR", raising=False)
    monkeypatch.delenv("DBT_TARGET", raising=False)
    monkeypatch.delenv("PGPASSWORD", raising=False)
    monkeypatch.delenv("PGPORT", raising=False)


def test_resolves_the_profile_of_a_shipped_example() -> None:
    profile = load_dbt_profile(Path("examples/simple_dbt"))

    assert (profile.name, profile.target, profile.type) == (
        "simple_dbt",
        "dev",
        "duckdb",
    )
    assert profile.config["path"] == "target/simple_dbt.duckdb"
    assert profile.profiles_path == Path("examples/simple_dbt/profiles.yml")


def test_target_can_be_overridden(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    monkeypatch.setenv("PGPASSWORD", "hunter2")

    assert load_dbt_profile(project).target == "dev"
    assert load_dbt_profile(project, target="prod").type == "postgres"


def test_dbt_target_environment_variable_selects_the_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    monkeypatch.setenv("PGPASSWORD", "hunter2")
    monkeypatch.setenv("DBT_TARGET", "prod")

    assert load_dbt_profile(project).target == "prod"
    # An explicit target beats the environment.
    assert load_dbt_profile(project, target="dev").target == "dev"


def test_profiles_are_searched_in_dbt_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setenv("DBT_PROFILES_DIR", str(tmp_path / "from_env"))

    assert profiles_search_path(project) == (
        tmp_path / "from_env" / "profiles.yml",
        project / "profiles.yml",
        home / ".dbt" / "profiles.yml",
    )
    # An explicit directory replaces the search entirely.
    assert profiles_search_path(project, tmp_path / "explicit") == (
        tmp_path / "explicit" / "profiles.yml",
    )


def test_profiles_directory_environment_variable_is_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path, with_profiles=False)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "profiles.yml").write_text(PROFILES, encoding="utf-8")
    monkeypatch.setenv("DBT_PROFILES_DIR", str(elsewhere))

    assert load_dbt_profile(project).profiles_path == elsewhere / "profiles.yml"


def test_env_var_is_expanded_with_and_without_a_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    monkeypatch.setenv("PGPASSWORD", "hunter2")

    profile = load_dbt_profile(project, target="prod")

    assert profile.config["password"] == "hunter2"
    assert profile.config["port"] == 5432, "a numeric default should not stay a string"


def test_a_missing_env_var_without_a_default_fails_loudly(tmp_path: Path) -> None:
    project = _project(tmp_path)

    with pytest.raises(DbtProfileError, match="PGPASSWORD"):
        load_dbt_profile(project, target="prod")


def test_unsupported_templating_names_env_var(tmp_path: Path) -> None:
    project = _project(
        tmp_path,
        profiles="""\
warehouse:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "{{ var('somewhere') }}"
""",
    )

    with pytest.raises(DbtProfileError, match="Only env_var"):
        load_dbt_profile(project)


def test_unquoted_jinja_still_parses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """dbt renders before parsing, so a profile may hold YAML-invalid Jinja."""
    monkeypatch.setenv("DB_PATH", "target/from_env.duckdb")
    project = _project(
        tmp_path,
        profiles="""\
warehouse:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: {{ env_var('DB_PATH') }}
""",
    )

    assert load_dbt_profile(project).config["path"] == "target/from_env.duckdb"


def test_credentials_are_redacted_for_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PGPASSWORD", "hunter2")
    project = _project(tmp_path)

    redacted = load_dbt_profile(project, target="prod").redacted()

    assert redacted["password"] == "***"
    assert redacted["host"] == "db.example.com"
    assert redacted["user"] == "reporting"


def test_an_inline_credential_document_is_masked_whole(tmp_path: Path) -> None:
    """BigQuery keyfile_json holds the private key inline; walking into it and
    publishing the parts that individually look harmless is not good enough."""
    project = _project(
        tmp_path,
        profiles="""\
warehouse:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account-json
      authenticator: oauth
      keyfile_json:
        client_email: bot@example.iam.gserviceaccount.com
        private_key: "-----BEGIN PRIVATE KEY-----"
""",
    )

    redacted = load_dbt_profile(project).redacted()

    assert redacted["keyfile_json"] == "***"
    assert redacted["method"] == "service-account-json"
    assert redacted["authenticator"] == "oauth", "not a secret; doctor should show it"


def test_a_render_error_does_not_quote_a_long_value(tmp_path: Path) -> None:
    """An error about a template must not become a way to print a secret."""
    project = _project(
        tmp_path,
        profiles="""\
warehouse:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "s3://bucket/very/long/path/that/might/be/sensitive/{{ nope() }}"
""",
    )

    with pytest.raises(DbtProfileError) as error:
        load_dbt_profile(project)

    assert "a templated value" in str(error.value)
    assert "s3://bucket" not in str(error.value)


@pytest.mark.parametrize(
    "profiles,message",
    [
        ("other:\n  target: dev\n  outputs:\n    dev:\n      type: duckdb\n",
         "no profile named 'warehouse'"),
        ("warehouse:\n  target: dev\n  outputs: {}\n", "defines no outputs"),
        ("warehouse:\n  outputs:\n    dev:\n      type: duckdb\n", "has no target"),
        ("warehouse:\n  target: missing\n  outputs:\n    dev:\n      type: duckdb\n",
         "has no target 'missing'"),
        ("warehouse:\n  target: dev\n  outputs:\n    dev:\n      path: x\n",
         "has no 'type'"),
    ],
)
def test_profile_errors_say_what_is_wrong(
    tmp_path: Path, profiles: str, message: str
) -> None:
    project = _project(tmp_path, profiles=profiles)

    with pytest.raises(DbtProfileError, match=message):
        load_dbt_profile(project)


def test_a_missing_dbt_project_is_reported(tmp_path: Path) -> None:
    with pytest.raises(DbtProfileError, match="is this a dbt project"):
        load_dbt_profile(tmp_path)


def test_a_dbt_project_without_a_profile_key_is_reported(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "dbt_project.yml").write_text("name: thing\n", encoding="utf-8")

    with pytest.raises(DbtProfileError, match="no 'profile' key"):
        load_dbt_profile(project)


def test_an_empty_dbt_project_file_says_so(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "dbt_project.yml").write_text("", encoding="utf-8")

    with pytest.raises(DbtProfileError, match="is empty"):
        load_dbt_profile(project)


def test_missing_profiles_yml_lists_where_it_looked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home"))
    project = _project(tmp_path, with_profiles=False)

    with pytest.raises(DbtProfileError) as error:
        load_dbt_profile(project)

    assert "Looked in:" in str(error.value)
    assert str(project / "profiles.yml") in str(error.value)


def _project(
    tmp_path: Path,
    *,
    profiles: str = PROFILES,
    with_profiles: bool = True,
) -> Path:
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    (project / "dbt_project.yml").write_text(
        "name: warehouse\nprofile: warehouse\n", encoding="utf-8"
    )
    if with_profiles:
        (project / "profiles.yml").write_text(profiles, encoding="utf-8")
    return project
