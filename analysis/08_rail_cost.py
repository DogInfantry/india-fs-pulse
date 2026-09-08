"""Sub-module H: what the zero-MDR rail costs, and who pays for it.

Sub-module A prices the merchant leg at zero. That is true of the discount rate
and false of the system: merchants pay nothing because the state pays instead.
This module measures how much, against what base, and which way it is moving.

Everything here divides one published figure by another. The blended rate is
incentive actually paid over ALL national merchant value, which needs no
assumption about how much of that value sits inside the eligibility band.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import banner, inr, load, load_json, pct, write_json, write_memo  # noqa: E402

MEMO = "pov-rail-cost"
# NPCI permits an MDR of up to 0.30% on UPI P2M. It has been set to zero by
# statute since January 2020. Source: PIB release 2114335.
NPCI_PERMITTED_MDR_BPS = 30.0


def main() -> None:
    banner("Sub-module H: the cost of the rail")
    df = load("upi_incentive")
    hero = load_json("upi_monetisation")

    actual = df[df.effective_bps.notna()].copy()
    first, last = actual.iloc[0], actual.iloc[-1]
    budget = df[df.effective_bps.isna()]
    statutory_bps = float(df.rate_pct.iloc[0]) * 100
    ceiling = int(df.ceiling_inr.iloc[0])

    paid_growth = float(last.payout_cr) / float(first.payout_cr)
    base_growth = float(last.p2m_lakh_cr) / float(first.p2m_lakh_cr)
    rate_fall = 1 - float(last.effective_bps) / float(first.effective_bps)

    # The blended rate over the statutory rate is the share of merchant value the
    # incentive actually reached. It is a FLOOR, not a point: 20% of every claim
    # is conditional on the acquirer's technical decline and uptime, so unclaimed
    # entitlement pushes the true eligible share up, never down.
    eligible_floor = float(last.effective_bps) / statutory_bps
    funded_share = float(last.effective_bps) / NPCI_PERMITTED_MDR_BPS

    write_json("chart_rail_cost", {
        "note": "Incentive actually paid by the government, over all national merchant "
                "value. Not the statutory rate: that applies only to transactions at or "
                f"under Rs {ceiling:,} to small merchants.",
        "statutory_rate_bps": statutory_bps,
        "npci_permitted_mdr_bps": NPCI_PERMITTED_MDR_BPS,
        "years": [
            {"fy": r.fy,
             "payout_cr": int(r.payout_cr),
             "status": r.status,
             "p2m_lakh_cr": float(r.p2m_lakh_cr),
             "effective_bps": None if pd.isna(r.effective_bps) else float(r.effective_bps),
             "basis": r.rate_basis}
            for r in df.itertuples()
        ],
    })

    budget_note = ""
    if len(budget):
        b = budget.iloc[0]
        cut = 1 - float(b.payout_cr) / float(last.payout_cr)
        budget_note = (
            f"\n\n**The appropriation is now falling in absolute terms, not only per rupee.** "
            f"FY{b.fy} was approved at **{inr(float(b.payout_cr) * 1e7)}**, {pct(cut)} below "
            f"the {inr(float(last.payout_cr) * 1e7)} actually paid in FY{last.fy}, against a "
            f"merchant base that was still growing. No rate is computed for that year here: "
            f"the outlay covers twelve months and the published value base covers "
            f"{int(b.months)}, and a ratio across mismatched periods is not a rate."
        )

    body = f"""
## The answer

Zero MDR is not zero cost. It is **{last.effective_bps:.1f} basis points, paid by the
taxpayer**, and it is falling. In FY{last.fy} the government paid acquiring banks
{inr(float(last.payout_cr) * 1e7)} in incentive against
Rs {last.p2m_lakh_cr:.1f} lakh crore of national merchant volume. Set beside the
{NPCI_PERMITTED_MDR_BPS:.0f} basis points NPCI permits on merchant UPI and that statute
has held at zero since January 2020, the state is funding roughly {pct(funded_share)} of
the discount rate the market is not allowed to charge.{budget_note}

## Three supporting arguments

**1. The subsidy per rupee has fallen in every year measured.** The blended rate went
from **{first.effective_bps:.2f}bps in FY{first.fy} to {last.effective_bps:.2f}bps in
FY{last.fy}**, a {pct(rate_fall)} decline. Nobody legislated that. The payout grew
{paid_growth:.1f} times while the merchant base it covers grew {base_growth:.1f} times,
and the distance between those two multiples is the whole mechanism: the appropriation
is set in rupees and the base compounds in percent.

**2. The statutory rate and the effective rate are different numbers, and only one of
them is money.** The scheme pays {statutory_bps:.2f}bps, but only on merchant
transactions at or under Rs {ceiling:,} to small merchants. Blended across all merchant
value the state pays {last.effective_bps:.2f}bps, which implies that **at least
{pct(eligible_floor)} of national merchant value sits inside that band**. That is a floor
rather than an estimate: 20% of every claim is withheld unless the acquiring bank holds
technical declines below 0.75% and uptime above 99.5%, so any entitlement left unclaimed
pushes the true eligible share up rather than down.

**3. It reframes the question from "why is the rail free" to "for how long".** The
merchant leg carries {pct(hero["merchant_volume_share"])} of transactions and
{pct(hero["merchant_value_share"])} of value at an average ticket of
Rs {hero["merchant_avg_ticket_inr"]:,.0f}. Those economics are not zero-revenue. They are
revenue of last resort, appropriated one year at a time, at an effective rate nobody has
committed to holding. A business model resting on it is underwriting a budget line, not
a price.

## So what

- **For a payments operator:** the incentive is the floor under acquirer economics and it
  is thinning without an announcement. Model the rail at zero and treat the subsidy as
  upside, never as base case.
- **For a policymaker:** a fixed rupee appropriation against a compounding base is a rate
  cut delivered by arithmetic rather than by decision. If holding the effective rate is
  the intent, the outlay has to be indexed to merchant volume.
- **For an investor:** this is the strongest support yet for the conclusion in the
  diligence memo. The payment will not be repriced, and the subsidy is not a growth
  business. Whatever is investable here sits in the products the relationship carries,
  not in the transaction.

## Method and its limits

Both tables come from one PIB release, transcribed in a browser because PIB serves HTTP
403 to scripted requests and publishes these figures as chart images with printed data
labels rather than as text. The blended rate divides incentive actually paid by all
national merchant value, so both sides are measured and neither is modelled. The national
merchant share it implies, {pct(float(last.p2m_lakh_cr) / float(last.total_lakh_cr))} of
UPI value, is cross-checked in the fetcher against PhonePe Pulse's own merchant share of
value, which is the one independent read available on the same quantity.

What is not known: how merchant value splits above and below the Rs {ceiling:,} ceiling,
what share of it belongs to small merchants as the scheme defines them, and how much
entitlement went unclaimed on the performance conditions. Those three unknowns are
precisely why the eligible share above is published as a floor and not as a figure. The
series ends at FY{df.fy.iloc[-1]} and is not extended by interpolation.
"""

    write_memo(
        MEMO,
        "Zero MDR is not zero cost: the state pays about seven basis points, and it is falling",
        body,
        sources=[
            "PIB, Ministry of Finance, Advancing Cashless India, 24 March 2025: "
            "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2114335",
            "PhonePe Pulse, for the merchant-share cross-check",
        ],
    )
    print(f"   blended rate FY{first.fy} {first.effective_bps:.2f}bps to "
          f"FY{last.fy} {last.effective_bps:.2f}bps ({pct(rate_fall)} fall)")
    print(f"   eligible share of merchant value: at least {pct(eligible_floor)}")


if __name__ == "__main__":
    main()
