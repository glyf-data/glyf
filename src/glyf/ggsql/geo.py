"""What a `DRAW map` is drawn on: region shapes, and how a row finds its own.

A map without `CONFIG shapes` draws on the world's countries, which ship with
glyf (`geo/world-countries.topojson`, from world-atlas and Natural Earth). A
project can name its own TopoJSON instead, for states, sales territories or
anything else with a boundary.

A row finds its shape by a key. Rather than make the author say which
property holds it, glyf counts how many of the query's regions each property
of the shapes would match and takes the best: a column of `US`, `GB` matches
`iso_a2`, one of `USA`, `GBR` matches `iso_a3`.
"""

import json
from collections import Counter
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

WORLD_SHAPES = "world-countries.topojson"
# Which key wins a tie: codes before names, because names drift.
_PREFERRED_KEYS = ("iso_a3", "iso_a2", "id", "name")


class MapShapesError(ValueError):
    """Raised when a map's shapes cannot be loaded or matched to its rows."""


@dataclass(frozen=True)
class Shapes:
    """A TopoJSON topology, the object in it that holds the regions, and where
    it came from, for error messages."""

    topology: dict[str, object]
    feature: str
    source: str

    def keys(self) -> dict[str, set[str]]:
        """Every value each candidate key takes, as text: `id` and each property."""
        objects = self.topology["objects"]
        assert isinstance(objects, dict)
        found: dict[str, set[str]] = {}
        for geometry in objects[self.feature].get("geometries", []):
            if not isinstance(geometry, dict):
                continue
            if geometry.get("id") is not None:
                found.setdefault("id", set()).add(str(geometry["id"]))
            properties = geometry.get("properties") or {}
            if isinstance(properties, dict):
                for name, value in properties.items():
                    if value is not None and not isinstance(value, (dict, list)):
                        found.setdefault(str(name), set()).add(str(value))
        return found


@dataclass(frozen=True)
class RegionMatch:
    """The key a map's rows are joined to its shapes on, and what it missed."""

    # A field path Vega reads off a shape: `id` or `properties.<name>`.
    lookup_key: str
    unmatched: tuple[str, ...]


def resolve_shapes_path(shapes: str, project_root: Path) -> Path:
    """Where a chart's `CONFIG shapes` file is: relative to the project.

    It must stay inside the project. A chart is built by everyone who builds
    the project, and it should not be able to inline a file from outside it
    into a page that gets published.
    """
    root = project_root.resolve()
    path = (root / shapes).resolve()
    if not path.is_relative_to(root):
        raise MapShapesError(f"CONFIG shapes '{shapes}' is outside the project")
    if not path.is_file():
        raise MapShapesError(f"CONFIG shapes '{shapes}' does not exist")
    return path


def load_shapes(shapes: str | None) -> Shapes:
    """The bundled world, or the TopoJSON file a chart names.

    The pipeline has already resolved a named file against the project with
    `resolve_shapes_path`; anything relative left here reads from the
    working directory.
    """
    if shapes is None:
        text = resources.files("glyf.ggsql").joinpath("geo", WORLD_SHAPES).read_text(
            encoding="utf-8"
        )
        return _shapes_from_text(text, "the bundled world countries")
    path = Path(shapes)
    if not path.is_file():
        raise MapShapesError(f"CONFIG shapes '{shapes}' does not exist")
    return _shapes_from_text(path.read_text(encoding="utf-8"), path.name)


def match_regions(shapes: Shapes, regions: list[object]) -> RegionMatch:
    """Pick the shapes' key that matches the most of a query's regions."""
    wanted = {str(value) for value in regions if value is not None}
    if not wanted:
        raise MapShapesError("the region column holds no values to draw")
    candidates = shapes.keys()
    scores = Counter({key: len(wanted & values) for key, values in candidates.items()})
    best = max(
        scores,
        key=lambda key: (
            scores[key],
            -_PREFERRED_KEYS.index(key) if key in _PREFERRED_KEYS else -len(_PREFERRED_KEYS),
        ),
        default=None,
    )
    if best is None or scores[best] == 0:
        example = ", ".join(sorted(wanted)[:3])
        hint = (
            "ISO 3166 codes such as 'USA' or 'US', or English names such as 'United States'"
            if shapes.source == "the bundled world countries"
            else f"one of its keys: {', '.join(sorted(candidates)) or 'none found'}"
        )
        raise MapShapesError(
            f"none of the regions ({example}) match {shapes.source}; use {hint}"
        )
    return RegionMatch(
        lookup_key="id" if best == "id" else f"properties.{best}",
        unmatched=tuple(sorted(wanted - candidates[best])),
    )


def _shapes_from_text(text: str, source: str) -> Shapes:
    try:
        topology = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MapShapesError(f"{source} is not valid JSON: {exc}") from exc
    if not isinstance(topology, dict) or topology.get("type") != "Topology":
        raise MapShapesError(f"{source} is not a TopoJSON topology")
    objects = topology.get("objects")
    if not isinstance(objects, dict) or not objects:
        raise MapShapesError(f"{source} has no objects to draw")
    # A topology may hold several layers (countries and land, states and
    # nation); the first is the one it is named for.
    return Shapes(topology=topology, feature=next(iter(objects)), source=source)
