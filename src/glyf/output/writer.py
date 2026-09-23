import json
from dataclasses import dataclass
from pathlib import Path

from glyf.config import GlyfConfig
from glyf.execution.result import QueryResult
from glyf.ggsql.models import GgsqlChart
from glyf.output.paths import artifact_paths


@dataclass(frozen=True)
class ChartArtifacts:
    compiled_sql: Path
    metadata_json: Path
    data_json: Path
    png: Path
    svg: Path
    vega_json: Path
    # A table's rendering: an HTML fragment instead of a picture.
    table_html: Path
    # A kpi's rendering, likewise.
    kpi_html: Path


def chart_artifact_paths(
    project_root: Path,
    chart: GgsqlChart,
    config: GlyfConfig | None = None,
) -> ChartArtifacts:
    paths = artifact_paths(project_root, config)
    paths.compiled_dir.mkdir(parents=True, exist_ok=True)
    paths.charts_dir.mkdir(parents=True, exist_ok=True)
    paths.normalized_data_dir.mkdir(parents=True, exist_ok=True)
    paths.vega_data_dir.mkdir(parents=True, exist_ok=True)

    return ChartArtifacts(
        compiled_sql=paths.compiled_dir / f"{chart.name}.sql",
        metadata_json=paths.charts_dir / f"{chart.name}.json",
        data_json=paths.normalized_data_dir / f"{chart.name}.data.json",
        png=paths.charts_dir / f"{chart.name}.png",
        svg=paths.charts_dir / f"{chart.name}.svg",
        vega_json=paths.vega_data_dir / f"{chart.name}.vega.json",
        table_html=paths.charts_dir / f"{chart.name}.table.html",
        kpi_html=paths.charts_dir / f"{chart.name}.kpi.html",
    )


def write_compiled_sql(compiled_path: Path, compiled_sql: str) -> None:
    compiled_path.parent.mkdir(parents=True, exist_ok=True)
    compiled_path.write_text(compiled_sql.strip() + "\n", encoding="utf-8")


def write_chart_metadata(
    project_root: Path,
    chart: GgsqlChart,
    artifacts: ChartArtifacts,
    *,
    columns: tuple[str, ...] = (),
    lineage: dict[str, object] | None = None,
    vega: bool = False,
) -> None:
    """Write `charts/<name>.json`.

    A table records the columns it lists (`VISUALISE *` resolved against the
    rows) and its HTML fragment, in place of the axes and the PNG and SVG a
    drawn chart has.
    """
    metadata: dict[str, object] = {
        "name": chart.name,
        "title": chart.title,
        "chart_type": chart.draw_type,
        "compiled_sql_path": artifacts.compiled_sql.relative_to(project_root).as_posix(),
        "data_json_path": artifacts.data_json.relative_to(project_root).as_posix(),
        "metadata_path": artifacts.metadata_json.relative_to(project_root).as_posix(),
    }
    if chart.is_table:
        metadata["columns"] = list(columns)
        metadata["table_html_path"] = artifacts.table_html.relative_to(
            project_root
        ).as_posix()
    elif chart.is_kpi:
        metadata["value"] = chart.field_for_role("value")
        metadata["compare"] = chart.field_for_role("compare")
        metadata["kpi_html_path"] = artifacts.kpi_html.relative_to(project_root).as_posix()
    else:
        metadata["x"] = chart.field_for_role("x")
        metadata["y"] = chart.field_for_role("y")
        metadata["png_path"] = artifacts.png.relative_to(project_root).as_posix()
        metadata["svg_path"] = artifacts.svg.relative_to(project_root).as_posix()
    # What `glyf diff` needs to draw the chart over its old self; only when set.
    for key, value in (
        ("color", chart.field_for_role("color")),
        ("x_title", chart.x_title),
        ("y_title", chart.y_title),
        ("width", chart.width),
        ("height", chart.height),
    ):
        if value is not None:
            metadata[key] = value
    if lineage is not None:
        # The models and sources behind the chart, so a dashboard can draw
        # lineage from artifacts alone.
        metadata["lineage"] = lineage
    if chart.is_interactive:
        metadata["interactions"] = list(chart.interactions)
    if vega:
        metadata["vega_json_path"] = artifacts.vega_json.relative_to(
            project_root
        ).as_posix()
    artifacts.metadata_json.parent.mkdir(parents=True, exist_ok=True)
    artifacts.metadata_json.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_chart_data(
    project_root: Path,
    chart: GgsqlChart,
    artifacts: ChartArtifacts,
    data: QueryResult,
) -> None:
    payload = {
        "name": chart.name,
        "fields": list(data.columns),
        "rows": list(data.rows),
    }
    artifacts.data_json.parent.mkdir(parents=True, exist_ok=True)
    artifacts.data_json.write_text(
        json.dumps(payload, indent=2, default=str, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def cleanup_legacy_chart_artifacts(project_root: Path, chart: GgsqlChart, config: GlyfConfig | None = None) -> None:
    paths = artifact_paths(project_root, config)
    legacy_paths = (
        paths.charts_dir / f"{chart.name}.data.json",
        paths.charts_dir / f"{chart.name}.vega.json",
    )
    for legacy_path in legacy_paths:
        if legacy_path.exists():
            legacy_path.unlink()
