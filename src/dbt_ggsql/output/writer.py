import json
from dataclasses import dataclass
from pathlib import Path

from dbt_ggsql.ggsql.models import GgsqlChart
from dbt_ggsql.output.paths import artifact_paths


@dataclass(frozen=True)
class ChartArtifacts:
    compiled_sql: Path
    metadata_json: Path
    png: Path
    svg: Path


def write_chart_artifacts(project_root: Path, chart: GgsqlChart, compiled_sql: str) -> ChartArtifacts:
    paths = artifact_paths(project_root)
    paths.compiled_dir.mkdir(parents=True, exist_ok=True)
    paths.charts_dir.mkdir(parents=True, exist_ok=True)

    compiled_path = paths.compiled_dir / f"{chart.name}.sql"
    metadata_path = paths.charts_dir / f"{chart.name}.json"
    png_path = paths.charts_dir / f"{chart.name}.png"
    svg_path = paths.charts_dir / f"{chart.name}.svg"

    compiled_path.write_text(compiled_sql.strip() + "\n", encoding="utf-8")

    metadata = {
        "chart": chart.name,
        "type": chart.draw_type,
        "title": chart.title,
        "compiled_sql": compiled_path.relative_to(project_root).as_posix(),
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    png_path.write_text(f"Placeholder PNG for {chart.name}\n", encoding="utf-8")
    svg_path.write_text(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" '
            'viewBox="0 0 640 360">\n'
            '  <rect width="640" height="360" fill="#f5f5f5"/>\n'
            f'  <text x="32" y="64" font-family="sans-serif" font-size="24">'
            f"Placeholder chart: {chart.name}</text>\n"
            "</svg>\n"
        ),
        encoding="utf-8",
    )

    return ChartArtifacts(
        compiled_sql=compiled_path,
        metadata_json=metadata_path,
        png=png_path,
        svg=svg_path,
    )
