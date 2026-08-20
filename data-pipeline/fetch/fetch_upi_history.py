"""NPCI UPI monthly headline series - the long history.

Two sources, deliberately, because neither alone is sufficient:

1. India Data Portal CKAN mirror of NPCI product statistics. Open, no auth,
   but the series STOPS AT 2023-08 (verified 2026-08-20). History only.
   Its date column is YYYY-DD-MM, NOT ISO - 2023-01-08 means 1 August 2023.
2. data/manual/npci_upi_monthly.csv - hand-seeded rows for 2023-09 onward,
   because npci.org.in returns HTTP 403 to every scripted request (WAF).
   Each manual row carries its own source URL and access date. See docs/REFRESH.md.

The output marks every row with `provenance` so charts can label the seam.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    MANUAL,
    banner,
    expect_columns,
    expect_nonempty,
    get_text,
    read_seeded_csv,
    record_source,
    write_processed,
)

CKAN_URL = (
    "https://ckandev.indiadataportal.com/dataset/"
    "150fe363-f61f-41f2-9215-15f61358f427/resource/"
    "8b176063-658a-41d7-9401-7461808d87a2/download/upi-product-statistics.csv"
)


def load_ckan() -> pd.DataFrame:
    raw = pd.read_csv(io.StringIO(get_text(CKAN_URL)))
    expect_columns(raw, ["date", "num_of_banks_live_on_upi", "volume", "value"], "CKAN UPI")
    expect_nonempty(raw, "CKAN UPI", minimum=50)
    df = pd.DataFrame({
        # YYYY-DD-MM in the source: the middle field is the day, always 01.
        "month": pd.to_datetime(raw["date"], format="%Y-%d-%m").dt.to_period("M").astype(str),
        "banks_live": raw["num_of_banks_live_on_upi"].astype("Int64"),
        "volume_mn": raw["volume"].astype(float),
        "value_cr": raw["value"].astype(float),
        "provenance": "npci_ckan_mirror",
    })
    return df[df.volume_mn > 0]


def load_manual() -> pd.DataFrame:
    path = MANUAL / "npci_upi_monthly.csv"
    if not path.exists():
        print("   note: no manual NPCI seed file; series ends at the CKAN cut-off")
        return pd.DataFrame()
    df = read_seeded_csv(path)
    expect_columns(df, ["month", "volume_mn", "value_cr", "source_url", "accessed"], "manual NPCI")
    df["provenance"] = "npci_manual"
    if "banks_live" not in df.columns:
        df["banks_live"] = pd.NA
    return df


def main() -> None:
    banner("NPCI UPI monthly: CKAN mirror (history)")
    ckan = load_ckan()
    print(f"   CKAN covers {ckan.month.min()} to {ckan.month.max()}  ({len(ckan)} months)")

    banner("NPCI UPI monthly: manual seed (recent)")
    manual = load_manual()
    if len(manual):
        print(f"   manual covers {manual.month.min()} to {manual.month.max()}  ({len(manual)} months)")

    cols = ["month", "banks_live", "volume_mn", "value_cr", "provenance"]
    combined = pd.concat([ckan[cols], manual[cols]] if len(manual) else [ckan[cols]])
    combined = combined.drop_duplicates("month", keep="last").sort_values("month")
    combined["avg_ticket_inr"] = (combined.value_cr * 1e7) / (combined.volume_mn * 1e6)
    combined["value_lakh_cr"] = combined.value_cr / 1e5

    write_processed(combined.reset_index(drop=True), "upi_monthly")
    record_source(
        "upi_monthly",
        url=CKAN_URL,
        publisher="NPCI via India Data Portal (CKAN mirror)",
        coverage=f"{combined.month.min()} - {combined.month.max()}",
        rows=len(combined),
        licence="NPCI terms apply to the underlying data",
        note=(
            "CKAN mirror STOPS AT 2023-08. Rows after that are hand-seeded from "
            "npci.org.in, which returns HTTP 403 to scripted access. "
            "The `provenance` column marks which is which."
        ),
    )


if __name__ == "__main__":
    main()
