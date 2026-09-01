"""Manual verification against a real warehouse.

Snowflake and BigQuery get no CI service container, so this is the by-hand
half of their testing: point the variables at a real dbt profile and the same
execution chain a build uses runs `select 1` and a validate-style probe
against the warehouse it names.

    export GLYF_WAREHOUSE_PROFILES_DIR=~/.dbt
    export GLYF_WAREHOUSE_PROFILE=my_profile     # a profile in profiles.yml
    export GLYF_WAREHOUSE_TARGET=prod            # optional
    uv run pytest tests/test_warehouse_manual.py -v

Works for any type the dbt backend dispatches (trino included), with real
credentials and real auth flows -- exactly what the fakes cannot cover.
"""

import os
from pathlib import Path

import pytest

from glyf.config import ExecutionConfig
from glyf.execution import execute_sql
from glyf.execution.limits import wrap_row_limit

PROFILES_DIR = os.environ.get("GLYF_WAREHOUSE_PROFILES_DIR")
PROFILE = os.environ.get("GLYF_WAREHOUSE_PROFILE")
TARGET = os.environ.get("GLYF_WAREHOUSE_TARGET")

pytestmark = pytest.mark.skipif(
    PROFILES_DIR is None or PROFILE is None,
    reason=(
        "set GLYF_WAREHOUSE_PROFILES_DIR and GLYF_WAREHOUSE_PROFILE "
        "to verify against a real warehouse"
    ),
)


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    (project / "dbt_project.yml").write_text(
        f"name: manual_check\nprofile: {PROFILE}\n", encoding="utf-8"
    )
    return project


def _execute(project: Path, sql: str):
    config = ExecutionConfig(
        backend="dbt",
        target=TARGET,
        profiles_dir=Path(PROFILES_DIR).expanduser(),
    )
    return execute_sql(project, sql, executor="dbt", config=config)


def test_select_one_reaches_the_warehouse(tmp_path: Path) -> None:
    result = _execute(_project(tmp_path), "select 1 as answer")

    assert [row["answer"] for row in result.rows] == [1]


def test_a_limit_zero_probe_binds_columns_without_rows(tmp_path: Path) -> None:
    """What validate mode sends."""
    sql = wrap_row_limit("select 1 as answer, 2 as another", 0)

    result = _execute(_project(tmp_path), sql)

    assert len(result) == 0
    assert result.columns == ("answer", "another")
