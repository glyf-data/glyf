import json
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pytest

from glyf.config import load_config
from glyf.execution import QueryResult, execute_sql, get_sql_executor
from tests.helpers import copy_basic_project


def test_query_result_round_trips_to_pandas() -> None:
    result = QueryResult.from_records(
        columns=("month", "revenue"),
        rows=(
            {"month": "2026-01", "revenue": 1200},
            {"month": "2026-02", "revenue": 1800},
        ),
    )

    arrow_table = result.to_arrow()
    polars_frame = result.to_polars()
    frame = result.to_pandas()

    assert arrow_table.column_names == ["month", "revenue"]
    assert polars_frame.columns == ["month", "revenue"]
    assert list(frame.columns) == ["month", "revenue"]
    assert frame.to_dict(orient="records") == list(result.rows)


def test_get_sql_executor_returns_duckdb_by_default() -> None:
    executor = get_sql_executor()

    assert executor.__class__.__name__ == "AdbcDuckDbExecutor"


def test_unknown_sql_executor_reports_available_options() -> None:
    with pytest.raises(ValueError, match="Unknown SQL executor 'missing'"):
        get_sql_executor("missing")


def test_execute_sql_accepts_named_executor(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = execute_sql(
        project,
        "select month, revenue from main.fct_orders order by month",
        executor="duckdb",
    )

    assert result.columns == ("month", "revenue")
    assert list(result.rows) == [
        {"month": "2026-01", "revenue": 1200},
        {"month": "2026-02", "revenue": 1800},
        {"month": "2026-03", "revenue": 2100},
        {"month": "2026-04", "revenue": 2400},
    ]


def test_execute_sql_supports_duckdb_dbapi_fallback(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = execute_sql(
        project,
        "select month, revenue from main.fct_orders order by month",
        executor="duckdb_dbapi",
    )

    assert result.columns == ("month", "revenue")
    assert len(result) == 4


def test_config_loads_execution_backend(tmp_path: Path) -> None:
    config_path = tmp_path / "glyf.yml"
    config_path.write_text(
        "execution:\n"
        "  backend: duckdb\n",
        encoding="utf-8",
    )

    config = load_config(tmp_path, config_path)

    assert config.execution.backend == "duckdb"


def test_decimal_columns_are_normalized_to_native_numbers() -> None:
    table = pa.table(
        {
            "revenue": pa.array(
                [Decimal("1200"), Decimal("1800")], pa.decimal128(38, 0)
            ),
            "margin": pa.array([Decimal("1.25"), Decimal("2.50")], pa.decimal128(10, 2)),
        }
    )

    result = QueryResult.from_arrow(table)

    assert result.table.schema.field("revenue").type == pa.int64()
    assert result.table.schema.field("margin").type == pa.float64()
    assert list(result.rows) == [
        {"revenue": 1200, "margin": 1.25},
        {"revenue": 1800, "margin": 2.5},
    ]
    assert json.loads(json.dumps(list(result.rows)))[0]["revenue"] == 1200


def test_aggregated_hugeint_results_are_json_serializable(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    result = execute_sql(
        project,
        "select month, sum(revenue) as revenue from main.fct_orders group by 1",
    )

    assert result.table.schema.field("revenue").type == pa.int64()
    json.dumps(list(result.rows))


def test_backends_agree_on_result_types(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)
    sql = "select month, sum(revenue) as revenue from main.fct_orders group by 1"

    adbc_result = execute_sql(project, sql, executor="duckdb_adbc")
    dbapi_result = execute_sql(project, sql, executor="duckdb_dbapi")

    assert adbc_result.table.schema == dbapi_result.table.schema
    assert sorted(adbc_result.rows, key=lambda row: row["month"]) == sorted(
        dbapi_result.rows, key=lambda row: row["month"]
    )
