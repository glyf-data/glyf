"""Executing against a real Trino server.

Skipped unless GLYF_TRINO_HOST is set. Locally:

    docker run --rm -p 8080:8080 trinodb/trino
    GLYF_TRINO_HOST=localhost uv run pytest tests/test_trino_integration.py

CI runs this against a Trino service container; the queries use the `tpch`
catalog every stock Trino ships, so no data needs loading.
"""

import os
from pathlib import Path

import pytest

from glyf.config import ExecutionConfig
from glyf.execution import execute_sql
from glyf.execution.limits import wrap_row_limit

TRINO_HOST = os.environ.get("GLYF_TRINO_HOST")
TRINO_PORT = int(os.environ.get("GLYF_TRINO_PORT", "8080"))

pytestmark = pytest.mark.skipif(
    TRINO_HOST is None,
    reason="set GLYF_TRINO_HOST to run the Trino integration tests",
)

REGIONS = ["AFRICA", "AMERICA", "ASIA", "EUROPE", "MIDDLE EAST"]


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    (project / "dbt_project.yml").write_text(
        "name: warehouse\nprofile: warehouse\n", encoding="utf-8"
    )
    (project / "profiles.yml").write_text(
        "warehouse:\n"
        "  target: trino\n"
        "  outputs:\n"
        "    trino:\n"
        "      type: trino\n"
        f"      host: {TRINO_HOST}\n"
        f"      port: {TRINO_PORT}\n"
        "      user: glyf\n"
        "      database: tpch\n"
        "      schema: tiny\n",
        encoding="utf-8",
    )
    return project


def _execute(project: Path, sql: str):
    return execute_sql(
        project, sql, executor="dbt", config=ExecutionConfig(backend="dbt")
    )


def test_the_catalog_and_schema_come_from_the_profile(tmp_path: Path) -> None:
    """`region` is unqualified, so it resolves through the session defaults."""
    result = _execute(_project(tmp_path), "select name from region order by name")

    assert [row["name"] for row in result.rows] == REGIONS


def test_qualified_sql_executes_as_ref_resolution_emits_it(tmp_path: Path) -> None:
    result = _execute(
        _project(tmp_path),
        "select name from tpch.tiny.region order by name",
    )

    assert [row["name"] for row in result.rows] == REGIONS


def test_the_row_limit_wrap_holds_on_trino(tmp_path: Path) -> None:
    """The SQL `limits.py` emits must be dialect-clean on Trino, not just DuckDB."""
    sql = wrap_row_limit("select name from region order by name", 2)

    result = _execute(_project(tmp_path), sql)

    assert [row["name"] for row in result.rows] == REGIONS[:2]


def test_a_limit_zero_probe_binds_columns_without_rows(tmp_path: Path) -> None:
    """What validate mode sends: prove the query runs, fetch nothing."""
    sql = wrap_row_limit("select name, regionkey from region", 0)

    result = _execute(_project(tmp_path), sql)

    assert len(result) == 0
    assert result.columns == ("name", "regionkey")
