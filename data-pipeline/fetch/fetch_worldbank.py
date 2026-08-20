"""World Bank indicators for India - the financial-inclusion denominator.

Account ownership is what turns raw payment volume into a penetration story:
transactions per banked adult, and which states over- or under-index.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import banner, expect, get_json, record_source, write_processed  # noqa: E402

API = "https://api.worldbank.org/v2/country/IND/indicator/{code}?format=json&per_page=200"
INDICATORS = {
    "FX.OWN.TOTL.ZS": "account_ownership_pct",
    "FX.OWN.TOTL.FE.ZS": "account_ownership_female_pct",
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "SP.POP.TOTL": "population",
    # 0-14 lets us derive the 15+ base that account ownership is measured against,
    # rather than assuming an adult share.
    "SP.POP.0014.TO": "population_0_14",
}


def fetch(code: str, label: str) -> pd.DataFrame:
    payload = get_json(API.format(code=code))
    expect(isinstance(payload, list) and len(payload) == 2, f"world bank {code}: unexpected envelope")
    rows = [
        {"year": int(r["date"]), label: float(r["value"])}
        for r in payload[1]
        if r.get("value") is not None
    ]
    expect(bool(rows), f"world bank {code}: no non-null observations")
    print(f"   {label:<28} {len(rows):>3} obs, latest {max(r['year'] for r in rows)}")
    return pd.DataFrame(rows)


def main() -> None:
    banner("World Bank: India indicators")
    merged: pd.DataFrame | None = None
    for code, label in INDICATORS.items():
        df = fetch(code, label)
        merged = df if merged is None else merged.merge(df, on="year", how="outer")
    assert merged is not None
    merged = merged.sort_values("year").reset_index(drop=True)
    write_processed(merged, "worldbank_india")
    record_source(
        "worldbank_india",
        url="https://api.worldbank.org/v2/country/IND/indicator/",
        publisher="World Bank Open Data",
        coverage=f"{merged.year.min()} - {merged.year.max()}",
        rows=len(merged),
        licence="CC BY 4.0",
        note="Indicators: " + ", ".join(INDICATORS),
    )


if __name__ == "__main__":
    main()
