import re
from pathlib import Path

import typer
import yaml

from dbt_charts.config import (
    ConfigError,
    DbtChartsConfig,
    load_config,
    resolve_project_path,
)
from dbt_charts.ggsql.parser import SUPPORTED_CHART_TYPES

DEFAULT_CONFIG = """visualisations_path: visualisations
dashboards_path: dashboards
output_path: target/ggsql
compiled_path: target/ggsql/compiled
charts_path: target/ggsql/charts
dashboards_output_path: target/ggsql/dashboards
site_path: target/ggsql/site

render:
  renderer: altair
  formats:
    - svg
    - png
  default_width: 800
  default_height: 400

dashboard:
  theme: light
  embed_charts: true
  show_compiled_sql: true
"""

NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def run_init(
    project: Path,
    *,
    config_path: Path | None = None,
    clean: bool = False,
    chart_name: str,
    dashboard_name: str,
    model_name: str,
    chart_title: str,
    chart_type: str,
) -> None:
    root = project.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        typer.echo("Init failed")
        typer.echo(f"  - Project directory does not exist: {root}")
        raise typer.Exit(1)

    if not (root / "dbt_project.yml").exists():
        typer.echo("Init failed")
        typer.echo(
            "  - Missing dbt_project.yml. Run from a dbt project root or pass --project-dir."
        )
        raise typer.Exit(1)

    chart_name = _normalize_name(chart_name, "chart name")
    dashboard_name = _normalize_name(dashboard_name, "dashboard name")
    model_name = _normalize_name(model_name, "model name")
    chart_title = chart_title.strip() or _title_from_name(chart_name)
    chart_type = chart_type.strip().lower()
    if chart_type not in SUPPORTED_CHART_TYPES:
        supported = ", ".join(sorted(SUPPORTED_CHART_TYPES))
        typer.echo("Init failed")
        typer.echo(f"  - Unsupported chart type '{chart_type}'. Supported: {supported}")
        raise typer.Exit(1)

    config_file = _config_file(root, config_path)
    config, config_exists = _load_or_default_config(root, config_file)
    visualisations_dir = resolve_project_path(root, config.visualisations_path)
    dashboards_dir = resolve_project_path(root, config.dashboards_path)
    chart_file = visualisations_dir / f"{chart_name}.ggsql"
    dashboard_file = dashboards_dir / f"{dashboard_name}.yml"

    existing = [path for path in (chart_file, dashboard_file) if path.exists()]
    if existing and not clean:
        typer.echo("Init skipped")
        typer.echo("  - Starter files already exist:")
        for path in existing:
            typer.echo(f"    - {_rel(path, root)}")
        typer.echo("  - Re-run with --clean to replace starter chart/dashboard files.")
        raise typer.Exit(1)

    visualisations_dir.mkdir(parents=True, exist_ok=True)
    dashboards_dir.mkdir(parents=True, exist_ok=True)

    wrote_config = False
    if not config_exists:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(DEFAULT_CONFIG, encoding="utf-8")
        wrote_config = True

    chart_file.write_text(
        _starter_ggsql(
            model_name=model_name,
            chart_title=chart_title,
            chart_type=chart_type,
        ),
        encoding="utf-8",
    )
    dashboard_file.write_text(
        _starter_dashboard_yaml(
            dashboard_name=dashboard_name,
            chart_name=chart_name,
        ),
        encoding="utf-8",
    )

    typer.echo(f"Initialized dbt-charts in {_rel(root, Path.cwd())}")
    typer.echo(f"✓ {'wrote' if wrote_config else 'kept'} {_rel(config_file, root)}")
    typer.echo(f"✓ ensured {_rel(visualisations_dir, root)}/")
    typer.echo(f"✓ wrote {_rel(chart_file, root)}")
    typer.echo(f"✓ ensured {_rel(dashboards_dir, root)}/")
    typer.echo(f"✓ wrote {_rel(dashboard_file, root)}")
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo("  dbt build")
    typer.echo("  dbt-charts doctor")
    typer.echo("  dbt-charts validate")
    typer.echo("  dbt-charts render")
    typer.echo("  dbt-charts dashboard")
    typer.echo("  dbt-charts export --clean")


def _normalize_name(value: str, label: str) -> str:
    normalized = value.strip()
    if not NAME_PATTERN.match(normalized):
        typer.echo("Init failed")
        typer.echo(
            f"  - Invalid {label} '{value}'. Use letters, numbers, and underscores."
        )
        raise typer.Exit(1)
    return normalized


def _config_file(root: Path, config_path: Path | None) -> Path:
    if config_path is None:
        return root / "dbt_charts.yml"
    expanded = config_path.expanduser()
    return expanded if expanded.is_absolute() else root / expanded


def _load_or_default_config(root: Path, config_file: Path) -> tuple[DbtChartsConfig, bool]:
    if not config_file.exists():
        return DbtChartsConfig(), False

    try:
        return load_config(root, config_file), True
    except ConfigError as exc:
        typer.echo("Config error")
        typer.echo(f"  - {exc}")
        raise typer.Exit(1) from exc


def _starter_ggsql(*, model_name: str, chart_title: str, chart_type: str) -> str:
    return (
        "SELECT\n"
        "  date_day,\n"
        "  metric_value\n"
        f"FROM {{{{ ref('{model_name}') }}}}\n"
        "\n"
        "VISUALISE date_day AS x, metric_value AS y\n"
        f"DRAW {chart_type}\n"
        f'LABEL title => "{_ggsql_label(chart_title)}"\n'
        'LABEL subtitle => "Starter chart generated by dbt-charts init"\n'
        'LABEL x_title => "Date"\n'
        'LABEL y_title => "Value"\n'
        "CONFIG width => 900\n"
        "CONFIG height => 500\n"
    )


def _starter_dashboard_yaml(*, dashboard_name: str, chart_name: str) -> str:
    body = {
        "name": dashboard_name,
        "title": _title_from_name(dashboard_name),
        "description": "Starter dashboard generated by dbt-charts init.",
        "charts": [chart_name],
    }
    return yaml.safe_dump(body, sort_keys=False)


def _title_from_name(value: str) -> str:
    return value.replace("_", " ").title()


def _ggsql_label(value: str) -> str:
    return value.replace('"', "'")


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
