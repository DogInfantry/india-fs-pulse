"""AMFI daily NAV file -> Indian mutual-fund scheme master.

Wealth and asset management is one of the JD's named FS sectors. AMFI publishes
the full scheme universe daily as a semicolon-delimited text file with no auth.

Structure of NAVAll.txt:
    "Open Ended Schemes(Equity Scheme - Large Cap Fund)"   <- category header
    "SBI Mutual Fund"                                      <- fund house
    "119598;INF...;INF...;SBI Large Cap Fund...;...;NAV;Date"   <- scheme rows
Blank lines separate blocks. Anything with >=5 semicolons is a data row; any
other non-empty line is a header (category if it contains a bracket, else house).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import banner, expect, expect_nonempty, get_text, record_source, write_processed  # noqa: E402

URL = "https://www.amfiindia.com/spages/NAVAll.txt"

# Category headers always name a scheme structure first; anything else that
# happens to contain brackets is a fund house.
CATEGORY_RE = re.compile(r"^(Open Ended|Close Ended|Interval Fund)\s+Schemes?\s*\(", re.I)

# Legacy AMFI labels ("Income", "Growth") predate the 2018 category scheme.
ASSET_RULES = [
    (r"equity|elss|growth$", "Equity"),
    (r"debt|income|liquid|money market|gilt", "Debt"),
    (r"hybrid|balanced", "Hybrid"),
    (r"solution oriented|retirement|children", "Solution oriented"),
    (r"fof|fund of fund", "Fund of funds"),
    (r"etf", "ETF"),
    (r"index", "Index"),
]


def parse(text: str) -> pd.DataFrame:
    rows, category, house = [], None, None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.count(";") >= 5:
            parts = line.split(";")
            if parts[0].strip().lower() == "scheme code":
                continue
            # AMFI added Plan and Option columns: the current file is 8 fields
            # (code;isin;isin;name;plan;option;nav;date), older dumps were 6.
            nav_idx, date_idx = (6, 7) if len(parts) >= 8 else (4, 5)
            rows.append({
                "scheme_code": parts[0].strip(),
                "scheme_name": parts[3].strip(),
                "plan": parts[4].strip() if len(parts) >= 8 else None,
                "option": parts[5].strip() if len(parts) >= 8 else None,
                "nav": pd.to_numeric(parts[nav_idx], errors="coerce"),
                "nav_date": parts[date_idx].strip() if len(parts) > date_idx else None,
                "fund_house": house,
                "category": category,
            })
        elif CATEGORY_RE.match(line):
            category = line
        else:
            # Fund house names can contain brackets too ("IL&FS Mutual Fund (IDF)"),
            # so a bracket alone is not enough to call a line a category header.
            house = line
    df = pd.DataFrame(rows)
    expect_nonempty(df, "AMFI NAVAll", minimum=5000)
    expect(df.fund_house.notna().mean() > 0.95, "AMFI: fund house missing on >5% of schemes")
    expect(df.nav.notna().mean() > 0.8, "AMFI: NAV parsed as null on >20% of rows - column layout changed")
    expect(df.nav_date.notna().mean() > 0.8, "AMFI: NAV date missing on >20% of rows")
    return df


def main() -> None:
    banner("AMFI: daily NAV scheme master")
    df = parse(get_text(URL))
    inner = df.category.str.extract(r"\((.*)\)", expand=False).fillna("")

    def classify(text: str) -> str:
        low = text.lower()
        for pattern, label in ASSET_RULES:
            if re.search(pattern, low):
                return label
        return "Other"

    df["asset_class"] = inner.map(classify)
    expect(
        (df.asset_class == "Other").mean() < 0.10,
        f"{(df.asset_class == 'Other').mean():.1%} of schemes unclassified - AMFI labels changed",
    )
    print(f"   {len(df):,} schemes across {df.fund_house.nunique()} fund houses")
    print(f"   NAV date: {df.nav_date.dropna().mode().iloc[0]}")

    house = (
        df.groupby("fund_house")
        .agg(schemes=("scheme_code", "count"), asset_classes=("asset_class", "nunique"))
        .sort_values("schemes", ascending=False)
        .reset_index()
    )
    print("   top 5 by scheme count: " + ", ".join(house.fund_house.head(5)))

    write_processed(df, "amfi_schemes")
    write_processed(house, "amfi_fund_houses")
    for name, frame in [("amfi_schemes", df), ("amfi_fund_houses", house)]:
        record_source(
            name,
            url=URL,
            publisher="Association of Mutual Funds in India (AMFI)",
            coverage=str(df.nav_date.dropna().mode().iloc[0]),
            rows=len(frame),
            licence="AMFI terms; publicly published daily NAV file",
            note="Scheme universe snapshot; scheme counts are not AUM.",
        )


if __name__ == "__main__":
    main()
