import re
from dataclasses import dataclass

from dbt_ggsql.manifest.loader import DbtManifest

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
    missing: list[str] = []
    refs: list[str] = []
    missing_sources: list[tuple[str, str]] = []
    sources: list[tuple[str, str]] = []

    def replace_ref(match: re.Match[str]) -> str:
        name = match.group(1)
        refs.append(name)
        relation = manifest.relation_for_ref(name)
        if relation is None:
            missing.append(name)
            return match.group(0)
        return relation

    def replace_source(match: re.Match[str]) -> str:
        source_name = match.group(1)
        table_name = match.group(2)
        sources.append((source_name, table_name))
        relation = manifest.relation_for_source(source_name, table_name)
        if relation is None:
            missing_sources.append((source_name, table_name))
            return match.group(0)
        return relation

    resolved_sql = REF_PATTERN.sub(replace_ref, sql)
    resolved_sql = SOURCE_PATTERN.sub(replace_source, resolved_sql)
    return RefResolution(
        sql=resolved_sql,
        refs=tuple(refs),
        missing_refs=tuple(dict.fromkeys(missing)),
        sources=tuple(sources),
        missing_sources=tuple(dict.fromkeys(missing_sources)),
    )
