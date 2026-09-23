"""Where a chart's data comes from: the models and sources behind it.

A chart names the models and sources it reads with `ref()` and `source()`.
dbt records what each of those reads in turn, in the manifest's
`depends_on`, all the way back to the raw tables. This module follows that
chain for one chart and writes the result into the chart's metadata, so a
dashboard can draw the whole graph from artifacts alone, with no manifest
and no chart files: the exported site carries everything it shows.
"""

from __future__ import annotations

from typing import Any

from glyf.manifest.loader import DbtManifest, ManifestRelation
from glyf.manifest.resolver import RefResolution


def chart_lineage(resolution: RefResolution, manifest: DbtManifest) -> dict[str, Any]:
    """The models and sources upstream of one chart.

    Returns `{"models": {name: {"parents": [...], "path": ...}}, "sources": [...]}`.
    A model's parents are model names or `source:<source>.<table>`; sources
    are listed as `<source>.<table>`. Unknown refs are left out: `glyf
    validate` reports those.
    """
    models: dict[str, dict[str, Any]] = {}
    sources: list[str] = []
    queue: list[ManifestRelation] = []
    for ref in dict.fromkeys(resolution.refs):
        node = manifest.node_for_ref(ref)
        if node is not None:
            queue.append(node)
    for source_name, table_name in dict.fromkeys(resolution.sources):
        label = f"{source_name}.{table_name}"
        if label not in sources:
            sources.append(label)
    while queue:
        node = queue.pop(0)
        if node.name in models:
            continue
        parents: list[str] = []
        for unique_id in node.parents:
            parent = manifest.node_by_id(unique_id)
            if parent is None:
                continue
            if parent.resource_type == "source":
                label = f"{parent.source_name}.{parent.name}"
                parents.append(f"source:{label}")
                if label not in sources:
                    sources.append(label)
            else:
                parents.append(parent.name)
                queue.append(parent)
        models[node.name] = {"parents": parents, "path": node.path}
    return {"models": models, "sources": sources}
