import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from glyf.config import ConfigError, GlyfConfig, load_config, resolve_project_path
from glyf.output.paths import artifact_paths
from glyf.project.scanner import ProjectScan, scan_project


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class DoctorResult:
    project_root: Path
    checks: tuple[DoctorCheck, ...]

    @property
    def has_errors(self) -> bool:
        return any(check.status == "error" for check in self.checks)


def run_doctor_checks(
    project: Path,
    config_path: Path | None = None,
) -> DoctorResult:
    root = project.expanduser().resolve()
    checks: list[DoctorCheck] = [_uv_environment_check()]

    config = GlyfConfig()
    config_loaded = False
    try:
        config = load_config(root, config_path)
        config_loaded = True
    except ConfigError as exc:
        checks.append(DoctorCheck("config", "error", str(exc)))

    if config_loaded:
        checks.append(_config_check(root, config_path))

    try:
        scan = scan_project(root, config)
    except ValueError as exc:
        checks.append(DoctorCheck("project", "error", str(exc)))
        return DoctorResult(project_root=root, checks=tuple(checks))

    checks.extend(_project_checks(scan))
    checks.extend(_output_checks(scan.root, config))
    return DoctorResult(project_root=root, checks=tuple(checks))


def _uv_environment_check() -> DoctorCheck:
    if shutil.which("uv") is not None:
        return DoctorCheck("uv", "ok", "uv executable found")
    if os.environ.get("VIRTUAL_ENV"):
        return DoctorCheck("uv", "warn", "uv executable not found, but a virtualenv is active")
    return DoctorCheck("uv", "warn", "uv executable not found on PATH")


def _config_check(root: Path, config_path: Path | None) -> DoctorCheck:
    if config_path is not None:
        return DoctorCheck("config", "ok", f"loaded {config_path}")
    default_path = root / "glyf.yml"
    if default_path.exists():
        return DoctorCheck("config", "ok", "loaded glyf.yml")
    return DoctorCheck("config", "ok", "no config file found, using defaults")


def _project_checks(scan: ProjectScan) -> list[DoctorCheck]:
    checks = [
        _exists_check(
            "dbt_project.yml",
            scan.dbt_project_path,
            "found dbt_project.yml",
            "missing dbt_project.yml; run from a dbt project root or pass --project-dir",
        ),
        _exists_check(
            "manifest.json",
            scan.manifest_path,
            "found target/manifest.json",
            "missing target/manifest.json; run dbt compile or dbt build",
        ),
        _exists_check(
            "visualisations",
            scan.visualisations_dir,
            f"found {len(scan.ggsql_files)} .ggsql file(s)",
            "missing visualisations directory or no configured visualisations_path",
        ),
        _exists_check(
            "dashboards",
            scan.dashboards_dir,
            f"found {len(scan.dashboard_files)} dashboard YAML file(s)",
            "missing dashboards directory or no configured dashboards_path",
        ),
    ]

    if scan.visualisations_dir is not None and not scan.ggsql_files:
        checks.append(
            DoctorCheck("visualisation files", "error", "no .ggsql files discovered")
        )
    else:
        checks.append(
            DoctorCheck(
                "visualisation files",
                "ok",
                f"{len(scan.ggsql_files)} .ggsql file(s) discovered",
            )
        )

    if scan.dashboards_dir is not None and not scan.dashboard_files:
        checks.append(
            DoctorCheck("dashboard files", "error", "no dashboard YAML files discovered")
        )
    else:
        checks.append(
            DoctorCheck(
                "dashboard files",
                "ok",
                f"{len(scan.dashboard_files)} dashboard YAML file(s) discovered",
            )
        )

    return checks


def _output_checks(root: Path, config: GlyfConfig) -> list[DoctorCheck]:
    paths = artifact_paths(root, config)
    output_paths = {
        "output directory": paths.root,
        "compiled directory": paths.compiled_dir,
        "charts directory": paths.charts_dir,
        "dashboards output directory": paths.dashboards_dir,
        "site directory": paths.site_dir,
    }
    checks = []
    for name, path in output_paths.items():
        if path.exists():
            checks.append(DoctorCheck(name, "ok", f"found {path.relative_to(root)}"))
        else:
            checks.append(
                DoctorCheck(
                    name,
                    "warn",
                    f"{path.relative_to(root)} does not exist yet; generate outputs first",
                )
            )
    return checks


def _exists_check(
    name: str,
    path: Path | None,
    ok_message: str,
    error_message: str,
) -> DoctorCheck:
    if path is not None:
        return DoctorCheck(name, "ok", ok_message)
    return DoctorCheck(name, "error", error_message)
