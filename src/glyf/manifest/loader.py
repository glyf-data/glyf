from dataclasses import dataclass
from pathlib import Path

from glyf import _core


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
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(f"Could not read manifest: {path}") from exc

    try:
        raw = _core.load_manifest_json(text, path.as_posix())
    except ValueError as exc:
        raise ManifestError(str(exc)) from exc

    return _manifest_from_core(raw)


def _manifest_from_core(raw: dict[str, object]) -> DbtManifest:
    return DbtManifest(
        path=Path(_required_str(raw, "path")),
        nodes=tuple(_relation_from_core(item) for item in _required_list(raw, "nodes")),
        sources=tuple(
            _relation_from_core(item) for item in _required_list(raw, "sources")
        ),
    )


def _relation_from_core(raw: object) -> ManifestRelation:
    if not isinstance(raw, dict):
        raise ManifestError("Rust core returned invalid manifest relation")
    return ManifestRelation(
        unique_id=_required_str(raw, "unique_id"),
        name=_required_str(raw, "name"),
        relation_name=_required_str(raw, "relation_name"),
        resource_type=_required_str(raw, "resource_type"),
        package_name=_optional_str(raw, "package_name"),
        source_name=_optional_str(raw, "source_name"),
    )


def _required_str(raw: dict[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise ManifestError(f"Rust core returned invalid manifest field '{key}'")
    return value


def _optional_str(raw: dict[str, object], key: str) -> str | None:
    value = raw.get(key)
    if value is None or isinstance(value, str):
        return value
    raise ManifestError(f"Rust core returned invalid manifest field '{key}'")


def _required_list(raw: dict[str, object], key: str) -> list[object]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise ManifestError(f"Rust core returned invalid manifest field '{key}'")
    return value
