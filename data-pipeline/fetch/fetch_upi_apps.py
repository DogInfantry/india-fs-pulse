"""NPCI per-application UPI statistics -> market structure.

This is the only open source that attributes UPI activity to a PLAYER. PhonePe
Pulse is PhonePe-only; the NPCI headline series is market-total. Without this,
the project's central question - who captures the value - has no data behind it.

Shares are computed against the NPCI NATIONAL total for the same month rather
than against the sum of the ten listed apps. NPCI caps the table at ten rows, so
summing them and calling it 100% would overstate every share. Using the national
denominator also produces an honest "all other apps" residual.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    MANUAL,
    PROCESSED,
    read_seeded_csv,
    banner,
    expect,
    expect_columns,
    expect_nonempty,
    record_source,
    write_processed,
)

URL = "https://www.npci.org.in/product/ecosystem-statistics/upi"
RESIDUAL = "All other apps"

# NPCI's own spelling drifts between months. Longest patterns first.
CANON = [
    (r"^phone\s*pe", "PhonePe"),
    (r"^google\s*pay", "Google Pay"),
    (r"^paytm", "Paytm"),
    (r"^navi", "Navi"),
    (r"^super\.?money", "super.money"),
    (r"^bhim$", "BHIM"),
    (r"^(famapp|fampay)", "FamApp"),
    (r"^whats\s*app", "WhatsApp"),
    (r"^cred", "CRED"),
    (r"^amazon\s*pay", "Amazon Pay"),
    (r"^axis bank", "Axis Bank apps"),
    (r"^icici bank", "ICICI Bank apps"),
    (r"^kotak", "Kotak Mahindra Bank apps"),
    (r"^yes bank", "Yes Bank apps"),
]


def canonical(raw: str) -> str:
    name = re.sub(r"\s*#\s*$", "", str(raw)).strip()          # strip NPCI's TPAP marker
    low = name.lower()
    for pattern, clean in CANON:
        if re.match(pattern, low):
            return clean
    return name


def load_apps() -> pd.DataFrame:
    path = MANUAL / "npci_upi_apps.csv"
    expect(path.exists(), f"missing {path.name}; see docs/REFRESH.md")
    df = read_seeded_csv(path)
    expect_columns(df, ["month", "app_raw", "volume_mn", "value_cr"], "npci apps")
    expect_nonempty(df, "npci apps", minimum=50)
    df["app"] = df.app_raw.map(canonical)
    expect(
        df.groupby(["month", "app"]).size().max() == 1,
        "name normalisation collapsed two different apps into one in the same month",
    )
    return df


def main() -> None:
    banner("NPCI UPI per-application statistics")
    apps = load_apps()

    national = pd.read_csv(PROCESSED / "upi_monthly.csv")[["month", "volume_mn", "value_cr"]]
    national = national.rename(columns={"volume_mn": "nat_volume_mn", "value_cr": "nat_value_cr"})
    df = apps.merge(national, on="month", how="left")
    expect(
        df.nat_volume_mn.notna().all(),
        f"no national total for: {sorted(df[df.nat_volume_mn.isna()].month.unique())}",
    )

    df["volume_share"] = df.volume_mn / df.nat_volume_mn
    df["value_share"] = df.value_cr / df.nat_value_cr
    df["avg_ticket_inr"] = (df.value_cr * 1e7) / (df.volume_mn * 1e6)

    # Cross-source reconciliation: ten apps cannot exceed the market, and if they
    # covered far less than most of it the table would not be the top ten.
    covered = df.groupby("month")["volume_share"].sum()
    expect(
        bool((covered <= 1.001).all()),
        f"listed apps exceed the national total in {covered[covered > 1.001].to_dict()}",
    )
    expect(
        bool((covered > 0.90).all()),
        f"top-ten coverage implausibly low: {covered[covered <= 0.90].round(3).to_dict()}",
    )
    print(f"   reconciliation ok - top ten cover {covered.min():.1%} to {covered.max():.1%} of national volume")

    # Honest residual so the shares add to the whole market.
    residual = []
    for month, grp in df.groupby("month"):
        nat_v, nat_c = grp.nat_volume_mn.iloc[0], grp.nat_value_cr.iloc[0]
        vol, val = nat_v - grp.volume_mn.sum(), nat_c - grp.value_cr.sum()
        residual.append({
            "month": month, "app": RESIDUAL, "app_raw": RESIDUAL,
            "volume_mn": vol, "value_cr": val,
            "nat_volume_mn": nat_v, "nat_value_cr": nat_c,
            "volume_share": vol / nat_v, "value_share": val / nat_c,
            "avg_ticket_inr": (val * 1e7) / (vol * 1e6) if vol > 0 else float("nan"),
        })
    out = pd.concat([df.drop(columns=["source_url", "accessed"]), pd.DataFrame(residual)])
    out = out.sort_values(["month", "volume_share"], ascending=[True, False]).reset_index(drop=True)

    # Concentration. HHI on the 0-10,000 scale, computed on true market shares.
    hhi = out.groupby("month").apply(
        lambda g: (g.volume_share.mul(100) ** 2).sum(), include_groups=False
    ).rename("hhi").reset_index()

    write_processed(out, "upi_apps")
    write_processed(hhi, "upi_apps_hhi")

    latest = out[out.month == out.month.max()]
    print(f"\n   {out.month.max()} market structure:")
    for r in latest.head(4).itertuples():
        print(f"     {r.app:<14} {r.volume_share:6.1%} of volume  {r.value_share:6.1%} of value"
              f"   avg Rs {r.avg_ticket_inr:,.0f}")
    print(f"   HHI {hhi.hhi.iloc[-1]:,.0f} (was {hhi.hhi.iloc[0]:,.0f} in {hhi.month.iloc[0]})")

    for name, frame in [("upi_apps", out), ("upi_apps_hhi", hhi)]:
        record_source(
            name, url=URL, publisher="NPCI (UPI Ecosystem Statistics)",
            coverage=f"{out.month.min()} to {out.month.max()}", rows=len(frame),
            licence="NPCI terms apply to the underlying data",
            note=("Top ten apps by volume, transcribed from a browser session because NPCI "
                  "returns HTTP 403 to scripted access. Shares are computed against the NPCI "
                  "national monthly total, so they are true market shares and the residual is real."),
        )


if __name__ == "__main__":
    main()
