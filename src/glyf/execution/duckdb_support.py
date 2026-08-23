"""Helpers shared by the DuckDB-backed SQL executors."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class _SupportsExecute(Protocol):
    def execute(self, operation: str) -> object:
        ...


def duckdb_database(project_root: Path) -> str:
    """Return the DuckDB database for a project, or ``:memory:`` if it has none."""
    database_name = f"{project_root.name}.duckdb"
    for database_path in (
        project_root / "target" / database_name,
        project_root / database_name,
    ):
        if database_path.exists():
            return database_path.as_posix()
    return ":memory:"


def load_seed_tables(connection: _SupportsExecute, seeds_dir: Path) -> None:
    """Expose a project's seed CSVs as views on an in-memory database."""
    if not seeds_dir.exists():
        return

    for csv_path in sorted(seeds_dir.glob("*.csv")):
        table_name = quote_identifier(csv_path.stem)
        csv_literal = quote_literal(csv_path.as_posix())
        connection.execute(
            f"CREATE OR REPLACE VIEW {table_name} AS "
            f"SELECT * FROM read_csv_auto({csv_literal}, header = true)"
        )


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
