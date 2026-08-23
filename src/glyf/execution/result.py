from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import polars as pl
import pyarrow as pa


@dataclass(frozen=True)
class QueryResult:
    table: pa.Table

    def __post_init__(self) -> None:
        object.__setattr__(self, "table", _normalize_table(self.table))

    def __len__(self) -> int:
        return self.table.num_rows

    @property
    def columns(self) -> tuple[str, ...]:
        return tuple(self.table.column_names)

    @property
    def rows(self) -> tuple[dict[str, object], ...]:
        return tuple(self.table.to_pylist())

    @classmethod
    def from_arrow(cls, table: pa.Table) -> "QueryResult":
        return cls(table=table)

    @classmethod
    def from_records(
        cls,
        columns: tuple[str, ...],
        rows: tuple[dict[str, object], ...],
    ) -> "QueryResult":
        ordered_rows = [{column: row.get(column) for column in columns} for row in rows]
        return cls(table=pa.Table.from_pylist(ordered_rows))

    @classmethod
    def from_pandas(cls, frame: pd.DataFrame) -> "QueryResult":
        return cls(table=pa.Table.from_pandas(frame, preserve_index=False))

    @classmethod
    def from_polars(cls, frame: pl.DataFrame) -> "QueryResult":
        return cls(table=frame.to_arrow())

    def to_arrow(self) -> pa.Table:
        return self.table

    def to_polars(self) -> pl.DataFrame:
        return pl.from_arrow(self.table)

    def to_pandas(self) -> pd.DataFrame:
        return self.table.to_pandas()


def _normalize_table(table: pa.Table) -> pa.Table:
    """Cast Arrow decimal columns to native numeric types.

    DuckDB exports HUGEINT (for example ``sum()`` over integers) as
    ``decimal128(38, 0)``, which reaches Python as ``decimal.Decimal``.
    Neither ``json`` nor vl-convert can serialise that, so charts and
    ``*.data.json`` artifacts fail on otherwise valid queries.
    """
    normalized = table
    for index, field in enumerate(table.schema):
        if not pa.types.is_decimal(field.type):
            continue
        column = _cast_decimal(table.column(index), field.type)
        normalized = normalized.set_column(
            index, field.with_type(column.type), column
        )
    return normalized


def _cast_decimal(column: pa.ChunkedArray, decimal_type: pa.DataType) -> pa.ChunkedArray:
    if decimal_type.scale == 0:
        try:
            return column.cast(pa.int64())
        except (pa.ArrowInvalid, pa.ArrowNotImplementedError):
            pass
    return column.cast(pa.float64())
