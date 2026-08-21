"""Build the India state boundary file the choropleth renders.

Run once, commit the output. This is a static boundary file, not a refreshing
dataset, so it deliberately stays OUT of `run.py data`: re-fetching 1 MB of
district geometry on every pipeline run would buy nothing.

Two things were checked before this source was chosen, and both matter.

1. ADMINISTRATIVE CURRENCY. The obvious candidate, geohacker/india, is derived
   from a pre-2014 GADM extract: no Telangana, no Ladakh, "Orissa", "Uttaranchal",
   and Dadra & Nagar Haveli still separate from Daman & Diu. Telangana alone is
   10% of the transaction volume in this project, so a map missing it is not
   merely dated, it is wrong. This source carries all 36 current states and UTs
   and they map one-to-one onto the Pulse state list.

2. BOUNDARY DEPICTION. Verified numerically at build time below: the northern
   extent must reach ~37.1N / ~80.3E, which is India's official depiction
   including Aksai Chin and Gilgit-Baltistan. A map of India drawn to the Line of
   Control instead is a live legal and political problem in India, and this
   project is aimed at an Indian employer. The assertion fails the build rather
   than shipping the wrong boundary quietly.

Output: site/public/india_states.geojson, fetched by the browser on demand rather
than imported into the page, so it costs nothing until the map is actually shown.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

SRC = "https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/india.geojson"
OUT = Path(__file__).resolve().parent.parent / "public" / "india_states.geojson"
PULSE_STATES = Path(__file__).resolve().parents[2] / "data-pipeline" / "data" / "processed" / "pulse_txn_state.csv"

SIMPLIFY_TOLERANCE = 0.02   # degrees; 69.5 KB out, visually indistinguishable at page size
COORD_DECIMALS = 3          # ~110 m, far finer than a state-level choropleth can show
EXPECTED_STATES = 36

# India's official northern and eastern extent. Anything materially short of this
# is the Line of Control depiction, which must not ship.
MIN_NORTH_LAT = 36.5
MIN_EAST_LON = 80.0


def pulse_names() -> set[str]:
    """The state names the site's data actually uses, title-cased as the analysis emits them."""
    if not PULSE_STATES.exists():
        sys.exit(f"missing {PULSE_STATES.name}. Run: python run.py data")
    rows = PULSE_STATES.read_text(encoding="utf-8").splitlines()
    idx = rows[0].split(",").index("state")
    return {r.split(",")[idx].title() for r in rows[1:] if r.strip()}


def normalise(name: str) -> str:
    """GeoJSON spells out 'and'; Pulse uses '&'. One rule covers all three cases."""
    return name.replace(" and ", " & ").title()


def main() -> None:
    print(f"-- fetching district geometry\n   {SRC}")
    payload = requests.get(SRC, timeout=180, headers={"User-Agent": "india-fs-pulse/1.0"}).json()
    districts = payload["features"]
    print(f"   {len(districts)} district features")

    by_state: dict[str, list] = {}
    for f in districts:
        by_state.setdefault(f["properties"]["st_nm"], []).append(shape(f["geometry"]))
    print(f"   dissolving into {len(by_state)} states and union territories")
    assert len(by_state) == EXPECTED_STATES, f"expected {EXPECTED_STATES} states, got {len(by_state)}"

    merged = {normalise(k): unary_union(v).buffer(0) for k, v in by_state.items()}

    # Guard 1: names must line up with the data, or states silently vanish from the map.
    ours, theirs = pulse_names(), set(merged)
    missing, extra = ours - theirs, theirs - ours
    assert not missing and not extra, (
        f"name mismatch\n  in data, not map: {sorted(missing)}\n  in map, not data: {sorted(extra)}")
    print(f"   all {len(ours)} names reconcile with pulse_txn_state.csv")

    # Guard 2: the boundary must be India's own depiction.
    north = max(g.bounds[3] for g in merged.values())
    east = max(g.bounds[2] for g in merged.values())
    assert north >= MIN_NORTH_LAT and east >= MIN_EAST_LON, (
        f"boundary reaches only {north:.2f}N / {east:.2f}E. India's official depiction extends to "
        f"~37.1N / ~80.3E; this looks like a Line of Control map and must not ship.")
    print(f"   boundary extent {north:.2f}N / {east:.2f}E - India's official depiction, Aksai Chin included")

    features = [
        {"type": "Feature", "properties": {"name": name},
         "geometry": mapping(geom.simplify(SIMPLIFY_TOLERANCE, preserve_topology=True))}
        for name, geom in sorted(merged.items())
    ]
    raw = json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":"))
    trimmed = re.sub(r"-?\d+\.\d{4,}", lambda m: f"{float(m.group()):.{COORD_DECIMALS}f}", raw)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(trimmed, encoding="utf-8")
    print(f"\n   wrote public/{OUT.name}  ({len(trimmed) / 1024:.1f} KB, {len(features)} features, "
          f"tolerance {SIMPLIFY_TOLERANCE}, {COORD_DECIMALS} dp)")


if __name__ == "__main__":
    main()
