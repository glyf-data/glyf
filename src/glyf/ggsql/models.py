from dataclasses import dataclass
from pathlib import Path

# A table's columns carry this role: `VISUALISE region, revenue` is a list
# of columns, not a set of axes. Mirrors `COLUMN_ROLE` in the Rust core.
COLUMN_ROLE = "column"
# `VISUALISE *`: every column the query returns. Mirrors `EVERY_COLUMN`.
EVERY_COLUMN = "*"


@dataclass(frozen=True)
class VisualiseMapping:
    field: str
    role: str


@dataclass(frozen=True)
class GgsqlChart:
    path: Path
    name: str
    sql: str
    visualise: tuple[VisualiseMapping, ...]
    draw_type: str
    labels: dict[str, str]
    config: dict[str, int]
    interactions: tuple[str, ...] = ()
    has_order_by: bool = False
    # Set when the SQL did not parse for the chosen dialect. A warning, never
    # an error: the warehouse is the judge of the SQL.
    sql_warning: str | None = None

    @property
    def title(self) -> str | None:
        return self.labels.get("title")

    def field_for_role(self, role: str) -> str | None:
        for mapping in self.visualise:
            if mapping.role == role:
                return mapping.field
        return None

    @property
    def subtitle(self) -> str | None:
        return self.labels.get("subtitle")

    @property
    def x_title(self) -> str | None:
        return self.labels.get("x_title")

    @property
    def y_title(self) -> str | None:
        return self.labels.get("y_title")

    @property
    def width(self) -> int | None:
        return self.config.get("width")

    @property
    def height(self) -> int | None:
        return self.config.get("height")

    @property
    def is_interactive(self) -> bool:
        return bool(self.interactions)

    @property
    def is_table(self) -> bool:
        """A table is its rows: no picture is drawn, and no PNG or SVG exists."""
        return self.draw_type == "table"

    @property
    def is_kpi(self) -> bool:
        """A kpi is one number, shown as an HTML tile rather than drawn."""
        return self.draw_type == "kpi"

    @property
    def has_picture(self) -> bool:
        """Whether the renderer draws this chart to a PNG and SVG."""
        return not (self.is_table or self.is_kpi)

    @property
    def lists_every_column(self) -> bool:
        """`VISUALISE *`: the columns are whatever the query returns."""
        return self.is_table and any(
            mapping.field == EVERY_COLUMN for mapping in self.visualise
        )

    @property
    def table_columns(self) -> tuple[str, ...]:
        """The columns a table names, in order; empty under `VISUALISE *`."""
        if not self.is_table or self.lists_every_column:
            return ()
        return tuple(
            mapping.field for mapping in self.visualise if mapping.role == COLUMN_ROLE
        )

    def column_label(self, column: str) -> str:
        """What a table's header says for a column: its LABEL, or its name."""
        return self.labels.get(column, column)
