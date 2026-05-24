from pathlib import Path

from glyf.project.scanner import scan_project
from tests.helpers import copy_basic_project


def test_scan_project_discovers_expected_files(tmp_path: Path) -> None:
    project = copy_basic_project(tmp_path)

    scan = scan_project(project)

    assert [path.relative_to(scan.root).as_posix() for path in scan.ggsql_files] == [
        "visualisations/revenue.ggsql"
    ]
    assert [path.relative_to(scan.root).as_posix() for path in scan.dashboard_files] == [
        "dashboards/executive.yml"
    ]
    assert scan.manifest_path == scan.root / "target" / "manifest.json"
    assert scan.dbt_project_path == scan.root / "dbt_project.yml"
    assert scan.visualisations_dir == scan.root / "visualisations"
    assert scan.dashboards_dir == scan.root / "dashboards"
