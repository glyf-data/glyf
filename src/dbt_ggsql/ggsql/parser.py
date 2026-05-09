from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GgsqlFile:
    path: Path
    name: str
    sql: str
    visualisation: str


def parse_ggsql_file(path: Path) -> GgsqlFile:
    text = path.read_text(encoding="utf-8")
    marker = "\nVISUALISE "
    if marker in text:
        sql, visualisation = text.split(marker, 1)
        visualisation = "VISUALISE " + visualisation
    else:
        sql = text
        visualisation = ""

    return GgsqlFile(
        path=path,
        name=path.stem,
        sql=sql.strip(),
        visualisation=visualisation.strip(),
    )
