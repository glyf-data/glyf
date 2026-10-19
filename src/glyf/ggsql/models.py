from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path

# A table's columns carry this role: `VISUALISE region, revenue` is a list
# of columns, not a set of axes. Mirrors `COLUMN_ROLE` in the Rust core.
COLUMN_ROLE = "column"
# `VISUALISE *`: every column the query returns. Mirrors `EVERY_COLUMN`.
EVERY_COLUMN = "*"


@dataclass(frozen=True)
class OrderTiebreak:
    """What glyf can do about the ties a query's ORDER BY leaves.

    Worked out by the Rust core from the compiled SQL; see `order_tiebreak`.
    """

    # The query with the other output columns appended to its ORDER BY, when
    # glyf could add them.
    sql: str | None = None
    # Those columns, by name (`column 3` for an unnamed one).
    added: tuple[str, ...] = ()
    # The author's keys as result column names, when every key is one.
    keys: tuple[str, ...] = ()
    # Why the SQL could not be given a tiebreak.
    reason: str | None = None
    # A LIMIT or FETCH: ties then decide which rows come back.
    limited: bool = False


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
    # Text CONFIG values: a map's `shapes` file and `projection`.
    options: dict[str, str] = dataclass_field(default_factory=dict)
    interactions: tuple[str, ...] = ()
    has_order_by: bool = False
    # Set when the SQL did not parse for the chosen dialect. A warning, never
    # an error: the warehouse is the judge of the SQL.
    sql_warning: str | None = None
    # Every column name the SQL mentions, lower-cased, wherever it appears;
    # empty when the SQL did not parse. What `glyf impact` reads.
    sql_columns: tuple[str, ...] = ()
    # Whether any SELECT uses `*`, reading columns the query never names.
    sql_selects_star: bool = False

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
    def y2_title(self) -> str | None:
        """A combo's right axis: the line's title."""
        return self.labels.get("y2_title")

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
    def is_map(self) -> bool:
        return self.draw_type == "map"

    @property
    def is_sankey(self) -> bool:
        return self.draw_type == "sankey"

    @property
    def is_combo(self) -> bool:
        """Bars of `y` and a line of `y2`, each on its own axis."""
        return self.draw_type == "combo"

    @property
    def is_funnel(self) -> bool:
        return self.draw_type == "funnel"

    @property
    def is_treemap(self) -> bool:
        return self.draw_type == "treemap"

    @property
    def is_point_map(self) -> bool:
        """A map of places at a latitude and longitude, rather than regions."""
        return self.is_map and self.field_for_role("region") is None

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
