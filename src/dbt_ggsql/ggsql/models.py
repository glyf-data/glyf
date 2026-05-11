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

    @property
    def title(self) -> str | None:
        return self.labels.get("title")
