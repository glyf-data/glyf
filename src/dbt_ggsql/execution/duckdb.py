from pathlib import Path

import duckdb
import pandas as pd


class SqlExecutionError(ValueError):
    """Raised when compiled SQL cannot be executed."""


def execute_sql(project_root: Path, sql: str) -> pd.DataFrame:
    try:
        with duckdb.connect(database=":memory:") as connection:
            _load_seed_tables(connection, project_root / "seeds")
            return connection.execute(sql).fetchdf()
    except duckdb.Error as exc:
        raise SqlExecutionError(str(exc)) from exc


def _load_seed_tables(connection: duckdb.DuckDBPyConnection, seeds_dir: Path) -> None:
    if not seeds_dir.exists():
        return

    for csv_path in sorted(seeds_dir.glob("*.csv")):
        table_name = _quote_identifier(csv_path.stem)
        csv_literal = _quote_literal(csv_path.as_posix())
        connection.execute(
            f"CREATE OR REPLACE VIEW {table_name} AS "
            f"SELECT * FROM read_csv_auto({csv_literal}, header = true)"
        )


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
