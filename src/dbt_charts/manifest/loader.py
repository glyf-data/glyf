import json
from dataclasses import dataclass
from pathlib import Path


class ManifestError(ValueError):
    """Raised when a dbt manifest cannot be loaded."""


@dataclass(frozen=True)
class ManifestRelation:
    unique_id: str
    name: str
    relation_name: str
    resource_type: str
    package_name: str | None = None
    source_name: str | None = None


@dataclass(frozen=True)
class DbtManifest:
    path: Path
    nodes: tuple[ManifestRelation, ...]
    sources: tuple[ManifestRelation, ...]

    @property
    def models(self) -> tuple[ManifestRelation, ...]:
        return tuple(node for node in self.nodes if node.resource_type == "model")

    @property
    def refable_nodes(self) -> tuple[ManifestRelation, ...]:
        return tuple(
            node
            for node in self.nodes
            if node.resource_type in {"model", "seed", "snapshot"}
        )

    def relation_for_ref(self, name: str) -> str | None:
        for node in self.refable_nodes:
            if node.name == name:
                return node.relation_name
        return None

    def relation_for_source(self, source_name: str, table_name: str) -> str | None:
        for source in self.sources:
            if source.source_name == source_name and source.name == table_name:
                return source.relation_name
        return None


def load_manifest(path: Path) -> DbtManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestError(f"Could not read manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Invalid manifest JSON: {path}") from exc

    nodes = raw.get("nodes")
    if not isinstance(nodes, dict):
        raise ManifestError("Invalid manifest: expected top-level 'nodes' object")

    nodes_list: list[ManifestRelation] = []
    for unique_id, node in nodes.items():
        if not isinstance(node, dict):
            continue

        relation = _manifest_relation(str(unique_id), node)
        if relation is not None and relation.resource_type in {
            "model",
            "seed",
            "snapshot",
        }:
            nodes_list.append(relation)

    sources = raw.get("sources", {})
    if not isinstance(sources, dict):
        raise ManifestError("Invalid manifest: expected top-level 'sources' object")

    source_list: list[ManifestRelation] = []
    for unique_id, source in sources.items():
        if not isinstance(source, dict):
            continue
        relation = _manifest_relation(str(unique_id), source)
        if relation is not None and relation.resource_type == "source":
            source_list.append(relation)

    return DbtManifest(
        path=path,
        nodes=tuple(sorted(nodes_list, key=lambda item: item.unique_id)),
        sources=tuple(sorted(source_list, key=lambda item: item.unique_id)),
    )


def _manifest_relation(unique_id: str, raw: dict[str, object]) -> ManifestRelation | None:
    name = raw.get("name")
    if not isinstance(name, str) or not name:
        return None

    resource_type = raw.get("resource_type", _resource_type_from_unique_id(unique_id))
    if not isinstance(resource_type, str) or not resource_type:
        return None

    relation_name = raw.get("relation_name")
    if not isinstance(relation_name, str) or not relation_name:
        relation_name = _relation_from_parts(raw)
    if relation_name is None:
        return None

    package_name = raw.get("package_name")
    source_name = raw.get("source_name")
    return ManifestRelation(
        unique_id=unique_id,
        name=name,
        relation_name=relation_name,
        resource_type=resource_type,
        package_name=package_name if isinstance(package_name, str) else None,
        source_name=source_name if isinstance(source_name, str) else None,
    )


def _resource_type_from_unique_id(unique_id: str) -> str:
    return unique_id.split(".", 1)[0] if "." in unique_id else ""


def _relation_from_parts(raw: dict[str, object]) -> str | None:
    identifier = raw.get("alias") or raw.get("identifier") or raw.get("name")
    schema = raw.get("schema")
    database = raw.get("database")

    parts = [
        part
        for part in (database, schema, identifier)
        if isinstance(part, str) and part
    ]
    if not parts:
        return None
    return ".".join(parts)
