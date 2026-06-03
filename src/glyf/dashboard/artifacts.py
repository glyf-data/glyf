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
    x: str
    y: str
    compiled_sql_path: Path
    data_json_path: Path
    png_path: Path
    svg_path: Path
    interactions: tuple[str, ...] = ()
    vega_json_path: Path | None = None


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
    svg = metadata.svg_path.read_text(encoding="utf-8") if metadata.svg_path.exists() else None
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

    if svg is None and not metadata.png_path.exists():
        raise ChartArtifactError(f"missing SVG or PNG artifact for '{chart_name}'")

    return ChartArtifact(
        metadata=metadata,
        svg=svg,
        compiled_sql=compiled_sql,
        data=data_artifact,
        vega_spec=vega_spec,
    )


def _parse_metadata(project_root: Path, chart_name: str, raw: object) -> ChartMetadata:
    if not isinstance(raw, dict):
        raise ChartArtifactError(f"invalid chart metadata for '{chart_name}'")

    required = {
        "name",
        "chart_type",
        "x",
        "y",
        "compiled_sql_path",
        "data_json_path",
        "png_path",
        "svg_path",
    }
    missing = sorted(key for key in required if not isinstance(raw.get(key), str))
    if missing:
        joined = ", ".join(missing)
        raise ChartArtifactError(f"chart metadata for '{chart_name}' missing {joined}")

    title = raw.get("title")
    if title is not None and not isinstance(title, str):
        raise ChartArtifactError(f"chart metadata for '{chart_name}' has invalid title")

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
        x=raw["x"],
        y=raw["y"],
        compiled_sql_path=project_root / raw["compiled_sql_path"],
        data_json_path=project_root / raw["data_json_path"],
        png_path=project_root / raw["png_path"],
        svg_path=project_root / raw["svg_path"],
        interactions=tuple(interactions),
        vega_json_path=project_root / vega_json_path
        if vega_json_path is not None
        else None,
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
