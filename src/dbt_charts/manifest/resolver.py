import re
from dataclasses import dataclass

from dbt_charts import _core
from dbt_charts.manifest.loader import DbtManifest

REF_PATTERN = re.compile(r"\{\{\s*ref\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}")
SOURCE_PATTERN = re.compile(
    r"\{\{\s*source\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}"
)


@dataclass(frozen=True)
class RefResolution:
    sql: str
    refs: tuple[str, ...]
    missing_refs: tuple[str, ...]
    sources: tuple[tuple[str, str], ...] = ()
    missing_sources: tuple[tuple[str, str], ...] = ()


def find_refs(sql: str) -> tuple[str, ...]:
    return tuple(match.group(1) for match in REF_PATTERN.finditer(sql))


def find_sources(sql: str) -> tuple[tuple[str, str], ...]:
    return tuple((match.group(1), match.group(2)) for match in SOURCE_PATTERN.finditer(sql))


def resolve_refs(sql: str, manifest: DbtManifest) -> RefResolution:
    raw = _core.resolve_refs(sql, _manifest_to_core(manifest))
    return RefResolution(
        sql=_required_str(raw, "sql"),
        refs=tuple(str(item) for item in _required_list(raw, "refs")),
        missing_refs=tuple(str(item) for item in _required_list(raw, "missing_refs")),
        sources=tuple(_tuple_pair(item) for item in _required_list(raw, "sources")),
        missing_sources=tuple(
            _tuple_pair(item) for item in _required_list(raw, "missing_sources")
        ),
    )


def _manifest_to_core(manifest: DbtManifest) -> dict[str, object]:
    return {
        "path": manifest.path.as_posix(),
        "nodes": [_relation_to_core(item) for item in manifest.nodes],
        "sources": [_relation_to_core(item) for item in manifest.sources],
    }


def _relation_to_core(relation: object) -> dict[str, object]:
    return {
        "unique_id": relation.unique_id,
        "name": relation.name,
        "relation_name": relation.relation_name,
        "resource_type": relation.resource_type,
        "package_name": relation.package_name,
        "source_name": relation.source_name,
    }


def _tuple_pair(raw: object) -> tuple[str, str]:
    if not isinstance(raw, (tuple, list)) or len(raw) != 2:
        raise ValueError("Rust core returned invalid ref/source tuple")
    return (str(raw[0]), str(raw[1]))


def _required_str(raw: dict[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Rust core returned invalid resolution field '{key}'")
    return value


def _required_list(raw: dict[str, object], key: str) -> list[object]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Rust core returned invalid resolution field '{key}'")
    return value
