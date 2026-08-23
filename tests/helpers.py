import json
import shutil
from pathlib import Path

# Output directories glyf writes under a project's target/. They are absent in a
# fresh clone but present as soon as anyone runs `glyf build` on an example, so
# copying them into a fixture makes tests depend on whatever was built last.
_GENERATED_OUTPUT_DIRS = frozenset({"glyf", "ggsql"})


def _ignore_generated_output(directory: str, names: list[str]) -> set[str]:
    if Path(directory).name != "target":
        return set()
    return {name for name in names if name in _GENERATED_OUTPUT_DIRS}


def copy_basic_project(tmp_path: Path, name: str = "basic") -> Path:
    project = tmp_path / name
    shutil.copytree(Path("examples/basic"), project, ignore=_ignore_generated_output)
    write_basic_manifest(project)
    return project


def copy_simple_dbt_project(tmp_path: Path, name: str = "simple_dbt") -> Path:
    project = tmp_path / name
    shutil.copytree(
        Path("examples/simple_dbt"), project, ignore=_ignore_generated_output
    )
    write_simple_dbt_manifest(project)
    return project


def write_basic_manifest(project: Path) -> Path:
    return _write_manifest(
        project,
        {
            "nodes": {
                "model.basic.fct_orders": {
                    "name": "fct_orders",
                    "relation_name": "main.fct_orders",
                }
            }
        },
    )


def write_simple_dbt_manifest(project: Path) -> Path:
    return _write_manifest(
        project,
        {
            "nodes": {
                "model.simple_dbt.fct_orders": {
                    "resource_type": "model",
                    "package_name": "simple_dbt",
                    "name": "fct_orders",
                    "relation_name": "main.fct_orders",
                }
            },
            "sources": {
                "source.simple_dbt.raw.orders": {
                    "resource_type": "source",
                    "package_name": "simple_dbt",
                    "source_name": "raw",
                    "name": "orders",
                    "relation_name": "main.raw_orders",
                }
            },
        },
    )


def _write_manifest(project: Path, manifest: dict[str, object]) -> Path:
    path = project / "target" / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path
