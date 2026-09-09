"""Every exhibit's underlying numbers, as a CSV the reader can download.

This project's strongest claim is that nothing on the page is asserted: each figure
is computed from a committed dataset. Until now a reader had to clone the repository
to check that. These files close the gap at the point of the claim, next to the chart
the number came from.

Generated from `site/src/data/chart_*.json`, which the analysis layer writes, so a CSV
cannot disagree with the exhibit above it. Nothing is recomputed here and no figure is
formatted differently: this is a transcription of the chart's own input.

The chart JSONs come in three shapes, all three handled rather than special-cased one
file at a time:

  records   one key holding a list of objects            -> those objects, as rows
  parallel  an axis list plus numeric lists beside it    -> axis joined to each list
  series    an axis list plus objects each holding one   -> axis down, one column per
            `values` list of the same length                series, nulls preserved

A null stays null. Rule 1 forbids filling a gap, and a zero in a downloaded CSV would
be read as a measurement rather than as an absence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site" / "src" / "data"
OUT = ROOT / "site" / "public" / "data"

# Keys that describe the exhibit rather than carrying its data.
META_KEYS = {"note", "caveat", "unit", "highlight", "synthetic", "label", "seed"}


def axis_key(payload: dict) -> str | None:
    for key in ("months", "years", "periods", "episodes", "window"):
        if isinstance(payload.get(key), list) and payload[key]:
            return key
    return None


def series_frame(payload: dict, axis: str) -> pd.DataFrame | None:
    """An axis plus objects that each carry a `values` list of the same length."""
    for key, value in payload.items():
        if key == axis or not isinstance(value, list) or not value:
            continue
        if not isinstance(value[0], dict) or "values" not in value[0]:
            continue
        index = payload[axis]
        out = pd.DataFrame({axis: index})
        for entry in value:
            if len(entry["values"]) != len(index):
                return None
            name = next((str(v) for k, v in entry.items()
                         if k != "values" and isinstance(v, str)), key)
            out[name] = entry["values"]
        return out
    return None


def parallel_frame(payload: dict, axis: str) -> pd.DataFrame | None:
    """An axis plus plain numeric lists of the same length beside it."""
    index = payload[axis]
    cols = {
        key: value for key, value in payload.items()
        if key != axis and isinstance(value, list) and len(value) == len(index)
        and value and isinstance(value[0], (int, float))
    }
    return pd.DataFrame({axis: index, **cols}) if cols else None


def record_frames(payload: dict) -> list[tuple[str, pd.DataFrame]]:
    out = []
    for key, value in payload.items():
        if key in META_KEYS or not isinstance(value, list) or not value:
            continue
        if isinstance(value[0], dict):
            out.append((key, pd.json_normalize(value)))
    return out


def frames_for(name: str, payload: dict) -> list[tuple[str, pd.DataFrame]]:
    axis = axis_key(payload)
    if axis:
        for builder in (series_frame, parallel_frame):
            frame = builder(payload, axis)
            if frame is not None and len(frame.columns) > 1:
                return [(name, frame)]
    records = record_frames(payload)
    if len(records) == 1:
        return [(name, records[0][1])]
    # More than one record list means genuinely separate tables, so they are kept
    # separate rather than merged into something the exhibit never showed.
    return [(f"{name}_{key}", frame) for key, frame in records]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = []
    # kpi_upi_trend is the one exhibit input the transform layer writes rather than
    # the analysis layer, and it is a bare array rather than an object.
    trend = SRC / "kpi_upi_trend.json"
    if trend.exists():
        rows = json.loads(trend.read_text(encoding="utf-8"))
        if isinstance(rows, list) and rows:
            pd.json_normalize(rows).to_csv(OUT / "kpi_upi_trend.csv", index=False)
            written += 1

    for path in sorted(SRC.glob("chart_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            skipped.append(path.stem)
            continue
        made = frames_for(path.stem, payload)
        if not made:
            skipped.append(path.stem)
            continue
        for name, frame in made:
            # na_rep left empty on purpose: an absent observation reads as blank,
            # never as a zero someone could mistake for a measurement.
            frame.to_csv(OUT / f"{name}.csv", index=False)
            written += 1
    stale = {p.stem for p in OUT.glob("*.csv")} - {"kpi_upi_trend"} - {
        n for p in SRC.glob("chart_*.json")
        for n, _ in frames_for(p.stem, json.loads(p.read_text(encoding="utf-8")))
    }
    for name in sorted(stale):
        (OUT / f"{name}.csv").unlink()
        print(f"   removed stale {name}.csv")
    print(f"   wrote {written} exhibit CSVs to site/public/data/")
    if skipped:
        print(f"   note: no table shape recognised for {', '.join(skipped)}")
        # A silent skip would let an exhibit ship a download link to nothing.
        sys.exit(f"unhandled chart shape: {skipped}")


if __name__ == "__main__":
    main()
