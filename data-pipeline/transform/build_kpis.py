"""Processed data -> the KPI layer the analysis scripts and the site both read.

One rule: every number the site renders is computed HERE, from a committed
processed file. Nothing downstream invents a figure (CLAUDE.md rule 1).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import PROCESSED, SITE_DATA, banner, expect, write_processed  # noqa: E402

MERCHANT = "Retail"  # PhonePe's label for merchant payments


def read(name: str) -> pd.DataFrame:
    path = PROCESSED / f"{name}.csv"
    expect(path.exists(), f"missing {path.name} - run the fetchers first")
    return pd.read_csv(path)


def upi_monetisation() -> dict:
    """The hero: merchant payments dominate volume, P2P dominates value, and the
    merchant leg - the only monetisable one - earns zero under zero-MDR."""
    national = read("pulse_txn_national")
    base = read("pulse_base_national")
    latest = national[national.period == national.period.max()]
    total_count = float(latest["count"].sum())
    total_amount = float(latest["amount_inr"].sum())

    categories = []
    for cat, row in latest.groupby("category")[["count", "amount_inr"]].sum().iterrows():
        categories.append({
            "category": cat,
            "count": int(row["count"]),
            "count_bn": round(row["count"] / 1e9, 2),
            "amount_lakh_cr": round(row["amount_inr"] / 1e12, 2),
            "volume_share": round(row["count"] / total_count, 4),
            "value_share": round(row["amount_inr"] / total_amount, 4),
            "avg_ticket_inr": round(row["amount_inr"] / row["count"], 0),
        })

    merchant = next(c for c in categories if c["category"] == MERCHANT)
    latest_base = base[base.period == base.period.max()].iloc[0]
    merchants = latest_base.get("registered_merchants")
    expect(pd.notna(merchants), "registered merchant count missing for the latest quarter")

    merchant_gmv = merchant["amount_lakh_cr"] * 1e12
    return {
        "period": str(latest.period.iloc[0]),
        "source": "PhonePe Pulse (PhonePe's own transactions, not all of UPI)",
        "categories": categories,
        "merchant_volume_share": merchant["volume_share"],
        "merchant_value_share": merchant["value_share"],
        "merchant_avg_ticket_inr": merchant["avg_ticket_inr"],
        "registered_merchants": int(merchants),
        "registered_users": int(latest_base["registered_users"]),
        # Zero MDR: this is the revenue that would exist at each hypothetical rate.
        "mdr_scenarios_cr": {
            f"{bps}bps": round(merchant_gmv * bps / 10000 / 1e7, 0) for bps in (0, 10, 30, 50)
        },
        "gmv_per_merchant_inr": round(merchant_gmv / float(merchants), 0),
        "txns_per_merchant": round(merchant["count"] / float(merchants), 1),
    }


def upi_trend() -> pd.DataFrame:
    df = read("upi_monthly").sort_values("month").copy()
    df["volume_yoy"] = df["volume_mn"].pct_change(12)
    df["value_yoy"] = df["value_cr"].pct_change(12)
    return df


def bank_nim() -> pd.DataFrame:
    df = read("bank_fundamentals")
    banks = df[df.cohort.isin(["Public", "Private"])].dropna(subset=["nim_proxy_pct"]).copy()
    banks["fy"] = pd.to_datetime(banks.fy_end).dt.year
    cohort = (
        banks.groupby(["fy", "cohort"])
        .agg(nim_proxy_pct=("nim_proxy_pct", "mean"), banks=("ticker", "nunique"))
        .reset_index()
    )
    wide = cohort.pivot(index="fy", columns="cohort", values="nim_proxy_pct")
    if {"Private", "Public"}.issubset(wide.columns):
        wide["gap_bps"] = (wide["Private"] - wide["Public"]) * 100
    return wide.reset_index()


def state_gap() -> pd.DataFrame:
    """Geographic gap without inventing a population denominator: compare each
    state's share of transactions with its share of value. States that transact
    far more often than their rupee share implies are merchant-heavy - i.e. the
    states carrying the zero-MDR burden."""
    df = read("pulse_txn_state")
    latest = df[df.period == df.period.max()].copy()
    latest["volume_share"] = latest["count"] / latest["count"].sum()
    latest["value_share"] = latest["amount_inr"] / latest["amount_inr"].sum()
    latest["intensity_index"] = latest["volume_share"] / latest["value_share"]
    national_ticket = latest["amount_inr"].sum() / latest["count"].sum()
    latest["ticket_vs_national"] = latest["avg_ticket_inr"] / national_ticket
    return latest.sort_values("volume_share", ascending=False).reset_index(drop=True)


def main() -> None:
    banner("Building KPI layer")
    SITE_DATA.mkdir(parents=True, exist_ok=True)

    hero = upi_monetisation()
    (SITE_DATA / "upi_monetisation.json").write_text(json.dumps(hero, indent=2), encoding="utf-8")
    print(f"   hero {hero['period']}: merchant {hero['merchant_volume_share']:.1%} of volume, "
          f"{hero['merchant_value_share']:.1%} of value, avg Rs {hero['merchant_avg_ticket_inr']:,.0f}")
    print(f"   {hero['registered_merchants']:,} merchants -> Rs {hero['gmv_per_merchant_inr']:,.0f} "
          f"GMV each per quarter, {hero['txns_per_merchant']:,.0f} txns each, Rs 0 MDR revenue")

    trend = upi_trend()
    write_processed(trend, "kpi_upi_trend")

    nim = bank_nim()
    write_processed(nim, "kpi_bank_nim")
    if "gap_bps" in nim.columns:
        last = nim.dropna(subset=["gap_bps"]).iloc[-1]
        print(f"   NIM gap FY{int(last.fy)}: private {last.Private:.2f}% vs public "
              f"{last.Public:.2f}%  =  {last.gap_bps:.0f}bps")

    states = state_gap()
    write_processed(states, "kpi_state_gap")
    print(f"   state gap: {len(states)} states, most merchant-intense = "
          f"{states.sort_values('intensity_index', ascending=False).state.iloc[0]}")

    for name in ["kpi_upi_trend", "kpi_bank_nim", "kpi_state_gap"]:
        frame = pd.read_csv(PROCESSED / f"{name}.csv")
        (SITE_DATA / f"{name}.json").write_text(
            frame.to_json(orient="records", double_precision=4), encoding="utf-8"
        )
    print(f"   site data written to {SITE_DATA.relative_to(SITE_DATA.parents[3])}")


if __name__ == "__main__":
    main()
