"""World Bank indicators: the financial-inclusion denominator, for India and for Brazil.

Account ownership is what turns raw payment volume into a penetration story:
transactions per banked adult, and which states over- or under-index. The
non-performing-loan and private-credit series carry the banking module's asset
quality and headroom, neither of which is derivable from filed statements alone.

Brazil carries only the three series the Pix comparator needs. Brazil runs roughly a
third of India's monthly instant-payment volume on about a seventh of its population,
so a raw volume comparison flatters India and says nothing about maturity. Per banked
adult is the honest measure, and it is computed for Brazil exactly as it already is
for India in analysis/02: total population, less ages 0 to 14, times account
ownership. Nothing here needs an exchange rate, and none is introduced.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import banner, expect, get_json, record_source, write_processed  # noqa: E402

API = "https://api.worldbank.org/v2/country/{iso3}/indicator/{code}?format=json&per_page=200"
INDICATORS = {
    "FX.OWN.TOTL.ZS": "account_ownership_pct",
    "FX.OWN.TOTL.FE.ZS": "account_ownership_female_pct",
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "SP.POP.TOTL": "population",
    # 0-14 lets us derive the 15+ base that account ownership is measured against,
    # rather than assuming an adult share.
    "SP.POP.0014.TO": "population_0_14",
    # Asset quality and credit penetration. The banking module had margins and
    # price returns but no answer to "what happened to credit costs", which is
    # most of why the public-bank cohort re-rated.
    "FB.AST.NPER.ZS": "npl_pct_gross_loans",
    "FS.AST.PRVT.GD.ZS": "domestic_credit_private_pct_gdp",
}
# Only what the Pix comparator reads. Fetching Brazil's full India-shaped set would
# land five columns nothing computes against.
BRAZIL_INDICATORS = {
    "FX.OWN.TOTL.ZS": "account_ownership_pct",
    "SP.POP.TOTL": "population",
    "SP.POP.0014.TO": "population_0_14",
}
COUNTRIES = [
    ("IND", "India", "worldbank_india", INDICATORS,
     "Inclusion denominators, asset quality and private credit for the banking and "
     "payments modules."),
    ("BRA", "Brazil", "worldbank_brazil", BRAZIL_INDICATORS,
     "The denominator for the Pix comparator only: transactions per banked adult, "
     "computed on the same 15+ base as India's."),
]


def fetch(iso3: str, code: str, label: str) -> pd.DataFrame:
    payload = get_json(API.format(iso3=iso3, code=code))
    expect(isinstance(payload, list) and len(payload) == 2,
           f"world bank {iso3} {code}: unexpected envelope")
    rows = [
        {"year": int(r["date"]), label: float(r["value"])}
        for r in payload[1]
        if r.get("value") is not None
    ]
    expect(bool(rows), f"world bank {iso3} {code}: no non-null observations")
    print(f"   {label:<28} {len(rows):>3} obs, latest {max(r['year'] for r in rows)}")
    return pd.DataFrame(rows)


def main() -> None:
    for iso3, name, dataset, indicators, note in COUNTRIES:
        banner(f"World Bank: {name} indicators")
        merged: pd.DataFrame | None = None
        for code, label in indicators.items():
            df = fetch(iso3, code, label)
            merged = df if merged is None else merged.merge(df, on="year", how="outer")
        assert merged is not None
        merged = merged.sort_values("year").reset_index(drop=True)
        write_processed(merged, dataset)
        record_source(
            dataset,
            url=f"https://api.worldbank.org/v2/country/{iso3}/indicator/",
            publisher="World Bank Open Data",
            coverage=f"{merged.year.min()} to {merged.year.max()}",
            rows=len(merged),
            licence="CC BY 4.0",
            note=f"{note} Indicators: " + ", ".join(indicators),
        )


if __name__ == "__main__":
    main()
