"""Rebuild the world-countries shapes a `DRAW map` uses when it names none.

The source is world-atlas 2.0.2 (`countries-110m.json`, ISC, Mike Bostock,
from Natural Earth's public-domain data). Each country is keyed by its ISO
3166 numeric code there; this adds the keys a query is likely to hold --
`iso_a3`, `iso_a2` and an English `name` -- and drops the `land` object glyf
never draws.

Run: uv run --no-project --with pycountry python scripts/build_world_shapes.py \
       path/to/countries-110m.json
"""
import json
import sys
from pathlib import Path

import pycountry

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/glyf/ggsql/geo/world-countries.topojson"
# Natural Earth draws these without an ISO 3166 code.
UNCODED = {
    "Kosovo": ("XK", "XKX", "Kosovo"),
    "N. Cyprus": (None, None, "Northern Cyprus"),
    "Somaliland": (None, None, "Somaliland"),
}


def keys(geometry: dict) -> dict[str, str]:
    source_name = geometry["properties"]["name"]
    if "id" not in geometry:
        alpha2, alpha3, name = UNCODED[source_name]
    else:
        country = pycountry.countries.get(numeric=geometry["id"])
        if country is None:
            raise SystemExit(f"no ISO 3166 entry for {source_name} ({geometry['id']})")
        alpha2, alpha3 = country.alpha_2, country.alpha_3
        name = getattr(country, "common_name", None) or country.name
    properties = {"name": name}
    if alpha2 is not None:
        properties["iso_a2"] = alpha2
        properties["iso_a3"] = alpha3
    return properties


def main(source: Path) -> None:
    topology = json.loads(source.read_text(encoding="utf-8"))
    countries = topology["objects"]["countries"]
    for geometry in countries["geometries"]:
        geometry["properties"] = keys(geometry)
        geometry.pop("id", None)
    topology["objects"] = {"countries": countries}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(topology, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
