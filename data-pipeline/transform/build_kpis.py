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
from common import PROCESSED, PROVENANCE, SITE_DATA, banner, expect, write_processed  # noqa: E402

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
    """Geographic gap, measured rather than inferred.

    This used to carry an `intensity_index` of volume_share / value_share. That
    index is algebraically identical to national_ticket / state_ticket, so it
    restated average ticket size and could say nothing independent about merchant
    behaviour. It is gone. `ticket_vs_national` below is the same quantity stated
    honestly, and the merchant shares are the real measure: what fraction of a
    state's OWN transactions are merchant payments - the leg zero-MDR applies to.
    """
    df = read("pulse_txn_state")
    latest = df[df.period == df.period.max()].copy()
    period = latest.period.max()

    latest["volume_share"] = latest["count"] / latest["count"].sum()
    latest["value_share"] = latest["amount_inr"] / latest["amount_inr"].sum()
    national_ticket = latest["amount_inr"].sum() / latest["count"].sum()
    latest["ticket_vs_national"] = latest["avg_ticket_inr"] / national_ticket

    mix = read("pulse_txn_state_mix")
    mix = mix[mix.period == period]
    expect(len(mix) > 0, f"pulse_txn_state_mix has no rows for {period}")

    # Category shares WITHIN each state, so a big state and a small one compare.
    totals = mix.groupby("state")[["count", "amount_inr"]].sum()
    wide = mix.pivot_table(index="state", columns="category",
                           values=["count", "amount_inr"], aggfunc="sum").fillna(0.0)
    for cat, label in ((MERCHANT, "merchant"), ("P2P", "p2p"), ("Utility", "utility")):
        expect(("count", cat) in wide.columns, f"state mix is missing category {cat!r}")
        latest[f"{label}_volume_share"] = latest.state.map(
            wide[("count", cat)] / totals["count"])
        latest[f"{label}_value_share"] = latest.state.map(
            wide[("amount_inr", cat)] / totals["amount_inr"])
    latest["merchant_avg_ticket_inr"] = latest.state.map(
        wide[("amount_inr", MERCHANT)] / wide[("count", MERCHANT)])

    missing = latest[latest.merchant_volume_share.isna()].state.tolist()
    expect(not missing, f"states present in totals but absent from the mix: {missing}")
    shares = latest[["merchant_volume_share", "p2p_volume_share", "utility_volume_share"]].sum(axis=1)
    expect(bool(((shares - 1.0).abs() < 1e-6).all()),
           "per-state category shares do not sum to 1 - a category is missing")

    return latest.sort_values("volume_share", ascending=False).reset_index(drop=True)


def pipeline_meta() -> dict:
    """Counts the site prose used to hardcode.

    The footer said "six public sources, five analysis modules" while run.py
    listed seven modules. Anything a human retypes eventually drifts, so these
    are counted from the tree and the provenance ledger instead (CLAUDE.md rule 1).
    """
    root = PROCESSED.parents[2]
    fetchers = sorted((root / "data-pipeline" / "fetch").glob("fetch_*.py"))
    modules = sorted(p for p in (root / "analysis").glob("*.py") if p.stem[0].isdigit())
    publishers: set[str] = set()
    if PROVENANCE.exists():
        ledger = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        publishers = {v["publisher"] for v in ledger.values() if v.get("publisher")}
    expect(bool(fetchers) and bool(modules), "pipeline_meta counted nothing - wrong root?")
    return {
        "fetchers": len(fetchers),
        "analysis_modules": len(modules),
        "publishers": len(publishers),
        "publisher_names": sorted(publishers),
        "datasets": len(list(PROCESSED.glob("*.csv"))),
    }


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
    material = states[states.volume_share >= 0.01]
    lead = material.nlargest(1, "merchant_volume_share").iloc[0]
    print(f"   state gap: {len(states)} states; most merchant-heavy material state = "
          f"{lead.state.title()} at {lead.merchant_volume_share:.1%} of its own transactions")

    for name in ["kpi_upi_trend", "kpi_bank_nim", "kpi_state_gap"]:
        frame = pd.read_csv(PROCESSED / f"{name}.csv")
        (SITE_DATA / f"{name}.json").write_text(
            frame.to_json(orient="records", double_precision=4), encoding="utf-8"
        )
    (SITE_DATA / "pipeline_meta.json").write_text(
        json.dumps(pipeline_meta(), indent=2), encoding="utf-8")
    print(f"   site data written to {SITE_DATA.relative_to(SITE_DATA.parents[3])}")


if __name__ == "__main__":
    main()
