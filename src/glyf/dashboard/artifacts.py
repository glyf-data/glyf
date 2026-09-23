import json
from dataclasses import dataclass
from pathlib import Path

from glyf.config import GlyfConfig
from glyf.output.paths import artifact_paths


class ChartArtifactError(ValueError):
    """Raised when chart artifact metadata is missing or invalid."""


@dataclass(frozen=True)
class ChartMetadata:
    name: str
    title: str | None
    chart_type: str
    # None for a table, which has no axes.
    x: str | None
    y: str | None
    compiled_sql_path: Path
    data_json_path: Path
    # None for a table, which is not drawn.
    png_path: Path | None
    svg_path: Path | None
    interactions: tuple[str, ...] = ()
    vega_json_path: Path | None = None
    # A table's columns, in the order it lists them, and its HTML fragment.
    columns: tuple[str, ...] = ()
    table_html_path: Path | None = None
    # A kpi's value and comparison columns, and its HTML fragment.
    value: str | None = None
    compare: str | None = None
    kpi_html_path: Path | None = None
    # `{"models": {name: {"parents": [...], "path": ...}}, "sources": [...]}`;
    # empty for metadata written before lineage was recorded.
    lineage: dict[str, object] | None = None

    @property
    def is_table(self) -> bool:
        return self.chart_type == "table"

    @property
    def is_kpi(self) -> bool:
        return self.chart_type == "kpi"


@dataclass(frozen=True)
class ChartDataArtifact:
    fields: tuple[str, ...]
    rows: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class ChartArtifact:
    metadata: ChartMetadata
    svg: str | None
    compiled_sql: str | None
    data: ChartDataArtifact
    vega_spec: object | None = None
    # The `<table>` fragment a table chart is shown as.
    table_html: str | None = None
    # The tile fragment a kpi chart is shown as.
    kpi_html: str | None = None


def load_chart_artifact(
    project_root: Path,
    chart_name: str,
    config: GlyfConfig | None = None,
) -> ChartArtifact:
    paths = artifact_paths(project_root, config)
    metadata_path = paths.charts_dir / f"{chart_name}.json"
    if not metadata_path.exists():
        raise ChartArtifactError(f"missing chart metadata for '{chart_name}'")

    try:
        raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ChartArtifactError(f"invalid chart metadata for '{chart_name}'") from exc

    metadata = _parse_metadata(project_root, chart_name, raw)
    svg = (
        metadata.svg_path.read_text(encoding="utf-8")
        if metadata.svg_path is not None and metadata.svg_path.exists()
        else None
    )
    compiled_sql = (
        metadata.compiled_sql_path.read_text(encoding="utf-8")
        if metadata.compiled_sql_path.exists()
        else None
    )
    data_artifact = _load_data_artifact(metadata, chart_name)
    vega_spec = None
    if metadata.vega_json_path is not None and metadata.vega_json_path.exists():
        try:
            vega_spec = json.loads(metadata.vega_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ChartArtifactError(f"invalid Vega-Lite JSON for '{chart_name}'") from exc

    table_html = None
    kpi_html = None
    if metadata.is_table:
        if metadata.table_html_path is None or not metadata.table_html_path.exists():
            raise ChartArtifactError(f"missing table artifact for '{chart_name}'")
        table_html = metadata.table_html_path.read_text(encoding="utf-8")
    elif metadata.is_kpi:
        if metadata.kpi_html_path is None or not metadata.kpi_html_path.exists():
            raise ChartArtifactError(f"missing kpi artifact for '{chart_name}'")
        kpi_html = metadata.kpi_html_path.read_text(encoding="utf-8")
    elif svg is None and (metadata.png_path is None or not metadata.png_path.exists()):
        raise ChartArtifactError(f"missing SVG or PNG artifact for '{chart_name}'")

    return ChartArtifact(
        metadata=metadata,
        svg=svg,
        compiled_sql=compiled_sql,
        data=data_artifact,
        vega_spec=vega_spec,
        table_html=table_html,
        kpi_html=kpi_html,
    )


def _parse_metadata(project_root: Path, chart_name: str, raw: object) -> ChartMetadata:
    if not isinstance(raw, dict):
        raise ChartArtifactError(f"invalid chart metadata for '{chart_name}'")

    is_table = raw.get("chart_type") == "table"
    is_kpi = raw.get("chart_type") == "kpi"
    required = {"name", "chart_type", "compiled_sql_path", "data_json_path"}
    if is_table:
        # A table has no axes and no picture: it records its columns and the
        # fragment that lays them out.
        required |= {"table_html_path"}
    elif is_kpi:
        required |= {"value", "kpi_html_path"}
    else:
        required |= {"x", "png_path", "svg_path"}
    missing = sorted(key for key in required if not isinstance(raw.get(key), str))
    if missing:
        joined = ", ".join(missing)
        raise ChartArtifactError(f"chart metadata for '{chart_name}' missing {joined}")

    title = raw.get("title")
    if title is not None and not isinstance(title, str):
        raise ChartArtifactError(f"chart metadata for '{chart_name}' has invalid title")

    columns = raw.get("columns", [])
    if is_table and (
        not isinstance(columns, list)
        or not columns
        or not all(isinstance(item, str) for item in columns)
    ):
        raise ChartArtifactError(f"chart metadata for '{chart_name}' has invalid columns")

    # A histogram counts rows per bin of x and binds no y column.
    y = raw.get("y")
    if y is not None and not isinstance(y, str):
        raise ChartArtifactError(f"chart metadata for '{chart_name}' has invalid y")
    if y is None and raw["chart_type"] not in {"histogram", "table", "kpi"}:
        raise ChartArtifactError(f"chart metadata for '{chart_name}' missing y")

    compare = raw.get("compare")
    if compare is not None and not isinstance(compare, str):
        raise ChartArtifactError(f"chart metadata for '{chart_name}' has invalid compare")

    interactions = raw.get("interactions", [])
    if not isinstance(interactions, list) or not all(
        isinstance(item, str) for item in interactions
    ):
        raise ChartArtifactError(
            f"chart metadata for '{chart_name}' has invalid interactions"
        )

    vega_json_path = raw.get("vega_json_path")
    if vega_json_path is not None and not isinstance(vega_json_path, str):
        raise ChartArtifactError(
            f"chart metadata for '{chart_name}' has invalid vega_json_path"
        )

    return ChartMetadata(
        name=raw["name"],
        title=title,
        chart_type=raw["chart_type"],
        x=None if is_table or is_kpi else raw["x"],
        y=y,
        compiled_sql_path=project_root / raw["compiled_sql_path"],
        data_json_path=project_root / raw["data_json_path"],
        png_path=None if is_table or is_kpi else project_root / raw["png_path"],
        svg_path=None if is_table or is_kpi else project_root / raw["svg_path"],
        interactions=tuple(interactions),
        vega_json_path=project_root / vega_json_path
        if vega_json_path is not None
        else None,
        columns=tuple(columns) if is_table else (),
        table_html_path=project_root / raw["table_html_path"] if is_table else None,
        value=raw["value"] if is_kpi else None,
        compare=compare if is_kpi else None,
        kpi_html_path=project_root / raw["kpi_html_path"] if is_kpi else None,
        lineage=raw["lineage"] if isinstance(raw.get("lineage"), dict) else None,
    )


def _load_data_artifact(metadata: ChartMetadata, chart_name: str) -> ChartDataArtifact:
    if not metadata.data_json_path.exists():
        raise ChartArtifactError(f"missing chart data for '{chart_name}'")
    try:
        raw = json.loads(metadata.data_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ChartArtifactError(f"invalid chart data for '{chart_name}'") from exc

    if not isinstance(raw, dict):
        raise ChartArtifactError(f"invalid chart data for '{chart_name}'")
    fields = raw.get("fields")
    rows = raw.get("rows")
    if not isinstance(fields, list) or not all(isinstance(item, str) for item in fields):
        raise ChartArtifactError(f"chart data for '{chart_name}' has invalid fields")
    if not isinstance(rows, list) or not all(isinstance(item, dict) for item in rows):
        raise ChartArtifactError(f"chart data for '{chart_name}' has invalid rows")
    return ChartDataArtifact(
        fields=tuple(fields),
        rows=tuple(dict(item) for item in rows),
    )
