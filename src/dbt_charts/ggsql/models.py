from dataclasses import dataclass
from pathlib import Path


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
