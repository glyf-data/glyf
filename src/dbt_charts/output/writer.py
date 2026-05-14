import json
from dataclasses import dataclass
from pathlib import Path

from dbt_charts.config import DbtChartsConfig
from dbt_charts.ggsql.models import GgsqlChart
from dbt_charts.output.paths import artifact_paths


@dataclass(frozen=True)
class ChartArtifacts:
    compiled_sql: Path
    metadata_json: Path
    png: Path
    svg: Path


def chart_artifact_paths(
    project_root: Path,
    chart: GgsqlChart,
    config: DbtChartsConfig | None = None,
) -> ChartArtifacts:
    paths = artifact_paths(project_root, config)
    paths.compiled_dir.mkdir(parents=True, exist_ok=True)
    paths.charts_dir.mkdir(parents=True, exist_ok=True)

    return ChartArtifacts(
        compiled_sql=paths.compiled_dir / f"{chart.name}.sql",
        metadata_json=paths.charts_dir / f"{chart.name}.json",
        png=paths.charts_dir / f"{chart.name}.png",
        svg=paths.charts_dir / f"{chart.name}.svg",
    )


def write_compiled_sql(compiled_path: Path, compiled_sql: str) -> None:
    compiled_path.parent.mkdir(parents=True, exist_ok=True)
    compiled_path.write_text(compiled_sql.strip() + "\n", encoding="utf-8")


def write_chart_metadata(project_root: Path, chart: GgsqlChart, artifacts: ChartArtifacts) -> None:
    metadata = {
        "name": chart.name,
        "title": chart.title,
        "chart_type": chart.draw_type,
        "x": chart.field_for_role("x"),
        "y": chart.field_for_role("y"),
        "compiled_sql_path": artifacts.compiled_sql.relative_to(project_root).as_posix(),
        "png_path": artifacts.png.relative_to(project_root).as_posix(),
        "svg_path": artifacts.svg.relative_to(project_root).as_posix(),
    }
    artifacts.metadata_json.parent.mkdir(parents=True, exist_ok=True)
    artifacts.metadata_json.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
